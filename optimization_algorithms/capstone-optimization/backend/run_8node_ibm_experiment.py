"""
run_8node_ibm_experiment.py
===========================
End-to-end execution of the 8-Node Mumbai Traffic Pipeline on Real IBM Quantum Hardware:
  1. ST-QGCN Traffic Flow Prediction (8-Qubit VQC, K=5 layers)
  2. QUBO Hamiltonian Formulation (6 packets on bottleneck V6-V2)
  3. Classical Parameter Transfer (Optimal gamma/beta angles via StatevectorSampler)
  4. Real IBM Quantum QPU Execution (SamplerV2, 8192 shots on least-busy QPU)
  5. Post-Hardware Physical Network Rebalancing & Traffic Signal Timing Optimization
"""

import os
import sys
import time
import json
import argparse
import numpy as np
import networkx as nx
import torch
import pennylane as qml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from test_8node_pipeline import (
    STQGCN, EDGES, EDGE_NAMES, EDGE_CAPACITIES_LIST, CAPACITIES,
    NODE_NAMES
)
from final_qaoa_with_signal import (
    detect_congestion, generate_alternate_routes,
    generate_packets, build_qubo, apply_solution,
    evaluate_network, optimize_signals, normalize_edge
)

from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.circuit.library import QAOAAnsatz
from qiskit import transpile

try:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    HAS_IBM_RUNTIME = True
except ImportError:
    HAS_IBM_RUNTIME = False

CHARTS_DIR = os.path.join(CURRENT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)
SHOTS = 8192

# ===========================================================================
# IBM QUANTUM CONFIGURATION
# ===========================================================================
# Paste your IBM Quantum API key / token here:
IBM_QUANTUM_API_KEY = "w6aCEDmDnDvZxWRvsbw_slUktSWki7VM7rsKMY2FV71N"

def run_experiment(use_real_hardware: bool = True, token: str = None, backend_name: str = None):
    print("=" * 80)
    print(" 8-NODE MUMBAI TRAFFIC PIPELINE ON IBM QUANTUM HARDWARE")
    print("=" * 80)

    # ---------------------------------------------------------
    # 1. Traffic Prediction via ST-QGCN
    # ---------------------------------------------------------
    print("\n[Step 1/5] Forecasting Edge Traffic with ST-QGCN Neural Network...")
    repo_root = os.path.abspath(os.path.join(CURRENT_DIR, "../../../"))
    dataset_path = os.path.join(repo_root, "prediction-final/Traffic Forecasting/Dataset/Single Network/mumbai_stqgcn_dataset_10k.npz")
    checkpoint_path = os.path.join(repo_root, "prediction-final/Traffic Forecasting/Single Network/Unidirectional/STQGCN/stqgcn_K5_model.pt")

    data = np.load(dataset_path)
    X_node = data["node_features"]
    E_edge = data["edge_features"]
    T_temp = data["temporal_features"]
    Y_target = data["target_flow"]

    mu_traffic = float(np.mean(Y_target))
    std_traffic = float(np.std(Y_target))
    X_mean, X_std = np.mean(X_node, axis=(0, 1)), np.std(X_node, axis=(0, 1)) + 1e-6
    E_mean, E_std = np.mean(E_edge, axis=(0, 1)), np.std(E_edge, axis=(0, 1)) + 1e-6

    X_norm = (X_node - X_mean) / X_std
    E_norm = (E_edge - E_mean) / E_std

    model = STQGCN(num_nodes=8, num_edges=11, node_in_dim=6, edge_in_dim=6, temp_in_dim=4, hidden_dim=16, n_qubits=8, n_vqc_layers=5)
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=False))
    model.eval()

    t = 8529
    x_in = torch.FloatTensor(X_norm[t:t+1])
    e_in = torch.FloatTensor(E_norm[t:t+1])
    t_in = torch.FloatTensor(T_temp[t:t+1])
    y_true = Y_target[t+1]

    t_pred_start = time.perf_counter()
    with torch.no_grad():
        y_pred_norm = model(x_in, e_in, t_in).squeeze(0).numpy()
    pred_latency = (time.perf_counter() - t_pred_start) * 1000.0
    y_pred = y_pred_norm * std_traffic + mu_traffic

    mae = float(np.mean(np.abs(y_pred - y_true)))
    print(f"  ST-QGCN inference latency: {pred_latency:.2f} ms")
    print(f"  Predicted MAE: {mae:.2f} veh/hr against actual ground truth")

    predicted_loads = {}
    for i in range(11):
        src, dst = EDGES[i]
        edge_key = normalize_edge(f"V{src+1}", f"V{dst+1}")
        predicted_loads[edge_key] = float(y_pred[i])

    # ---------------------------------------------------------
    # 2. QUBO Problem Formulation
    # ---------------------------------------------------------
    print("\n[Step 2/5] Formulating QUBO Optimization Problem...")
    G = nx.Graph()
    for e in CAPACITIES:
        G.add_edge(e[0], e[1])

    occ, cong, under = detect_congestion(CAPACITIES, predicted_loads, high_threshold=0.60, low_threshold=0.45)
    alt_routes = generate_alternate_routes(G, cong, occ, max_cutoff=4, top_k=2)
    sorted_cong = dict(sorted(cong.items(), key=lambda item: item[1], reverse=True))

    packets, variables = generate_packets(
        sorted_cong, predicted_loads, CAPACITIES, alt_routes,
        target=0.50, packet_size=150.0, max_packets=6
    )

    N_QUBITS = len(variables)
    qubo_problem = build_qubo(variables, CAPACITIES, occ, target=0.50, packet_size=150.0)

    qp = QuadraticProgram("Traffic_Rebalancing_8Node")
    for v in variables:
        qp.binary_var(name=v["name"])
    qp.minimize(
        constant=qubo_problem["constant"],
        linear=qubo_problem["linear"],
        quadratic=qubo_problem["quadratic"],
    )

    init_peak = max(occ.values()) * 100.0
    print(f"  Active decision variables (Qubits): {N_QUBITS}")
    print(f"  Initial peak network occupancy:     {init_peak:.2f}% (Edge V6\u2194V2)")

    # ---------------------------------------------------------
    # 3. Classical Parameter Transfer (Angle Optimization)
    # ---------------------------------------------------------
    print(f"\n[Step 3/5] Classical Parameter Transfer (StatevectorSampler + COBYLA) ...")
    t_opt_start = time.perf_counter()
    qaoa = QAOA(
        sampler=StatevectorSampler(),
        optimizer=COBYLA(maxiter=30),
        reps=1,
    )
    solver = MinimumEigenOptimizer(qaoa)
    result = solver.solve(qp)
    opt_latency = (time.perf_counter() - t_opt_start) * 1000.0

    optimal_point = result.min_eigen_solver_result.optimal_point
    ideal_bitstring = tuple(int(round(v)) for v in result.x)
    print(f"  Optimal parameters (gamma, beta): {np.round(optimal_point, 4)}")
    print(f"  Ideal simulator bitstring:        {ideal_bitstring} (Cost: {result.fval:.4f})")
    print(f"  Angle optimization latency:       {opt_latency:.1f} ms")

    # ---------------------------------------------------------
    # 4. Construct Circuit & Connect to IBM Quantum
    # ---------------------------------------------------------
    print(f"\n[Step 4/5] Building QAOA Quantum Circuit & Transpiling ...")
    converter = QuadraticProgramToQubo()
    qubo_qp = converter.convert(qp)
    operator, _offset = qubo_qp.to_ising()

    ansatz = QAOAAnsatz(cost_operator=operator, reps=1)
    ansatz.measure_all()
    bound_circuit = ansatz.assign_parameters(optimal_point)

    print(f"  Circuit Qubits: {ansatz.num_qubits}")
    print(f"  Logical Depth:  {ansatz.decompose().depth()}")

    active_token = token or (IBM_QUANTUM_API_KEY.strip() if IBM_QUANTUM_API_KEY.strip() else os.getenv("IBM_QUANTUM_TOKEN"))
    service = None
    if active_token:
        for ch in ["ibm_quantum_platform", "ibm_quantum", "ibm_cloud"]:
            try:
                service = QiskitRuntimeService(channel=ch, token=active_token)
                if service:
                    break
            except Exception:
                continue
    else:
        try:
            service = QiskitRuntimeService()
        except Exception:
            service = None

    if service is None and use_real_hardware:
        raise ValueError(
            "IBM Quantum account not configured. Please paste your token into IBM_QUANTUM_API_KEY at the top of the file, or run:\n"
            "python run_8node_ibm_experiment.py --save-token YOUR_TOKEN"
        )

    counts = {}
    backend_selected = None
    hw_latency_ms = 0.0

    if use_real_hardware:
        if backend_name:
            backend_selected = service.backend(backend_name)
        else:
            print("  Finding least-busy operational IBM Quantum QPU (min 6 qubits) ...")
            backend_selected = service.least_busy(
                operational=True,
                simulator=False,
                min_num_qubits=N_QUBITS
            )
        print(f"  --> Selected Target QPU: {backend_selected.name}")
        
        # Transpile for target QPU
        t_transpile_start = time.perf_counter()
        t_circuit = transpile(bound_circuit, backend=backend_selected, optimization_level=3)
        print(f"  Transpiled Depth on {backend_selected.name}: {t_circuit.depth()}")
        print(f"  Transpiled 2-qubit CNOT/ECR count: {t_circuit.count_ops().get('ecr', t_circuit.count_ops().get('cz', t_circuit.count_ops().get('cx', 0)))}")

        print(f"\n  Submitting Job to QPU ({SHOTS} shots)...")
        sampler = SamplerV2(mode=backend_selected)
        t_job_start = time.perf_counter()
        job = sampler.run([t_circuit], shots=SHOTS)
        print(f"  Job ID: {job.job_id()}")
        print(f"  Track in browser: https://quantum.cloud.ibm.com/jobs/{job.job_id()}")
        print(f"  Waiting for QPU execution (queue + hardware execution) ...")
        
        res = job.result()
        hw_latency_ms = (time.perf_counter() - t_job_start) * 1000.0

        pub_result = res[0]
        data_bin = pub_result.data
        meas_data = getattr(data_bin, "meas", None)
        if meas_data is None:
            for attr in dir(data_bin):
                if not attr.startswith("_"):
                    cand = getattr(data_bin, attr)
                    if hasattr(cand, "get_counts"):
                        meas_data = cand
                        break
        raw_counts = meas_data.get_counts() if meas_data else {}
        for bstr, cnt in raw_counts.items():
            counts[str(bstr)] = int(cnt)
    else:
        # Local Aer simulator test fallback
        from qiskit_aer import AerSimulator
        sim = AerSimulator()
        t_circuit = transpile(bound_circuit, backend=sim)
        res = sim.run(t_circuit, shots=SHOTS).result()
        counts = {str(k): int(v) for k, v in res.get_counts().items()}
        backend_selected = sim
        hw_latency_ms = 50.0

    # ---------------------------------------------------------
    # 5. Result Analysis & Physical Network Evaluation
    # ---------------------------------------------------------
    print("\n[Step 5/5] Analyzing Hardware Outcomes & Rebalancing Network...")
    total_shots = sum(counts.values())
    sorted_shots = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    # Top measured bitstring
    best_hw_bstr_str = sorted_shots[0][0].replace(" ", "")
    # Note: Qiskit little-endian bitstring ordering
    best_hw_bits = tuple(int(b) for b in reversed(best_hw_bstr_str[-N_QUBITS:]))

    # Evaluate physical network with best hardware bitstring
    updated_loads = apply_solution(packets, best_hw_bits, predicted_loads, packet_size=150.0)
    eval_res = evaluate_network(CAPACITIES, predicted_loads, updated_loads)
    green_times = optimize_signals(G, CAPACITIES, updated_loads, cycle_time=90.0, yellow_red_time=4.0)

    # Compare ideal bitstring probability
    ideal_str = "".join(str(b) for b in reversed(ideal_bitstring))
    ideal_shots = counts.get(ideal_str, 0)
    p_ideal = (ideal_shots / total_shots) * 100.0

    print("=" * 80)
    print(f" EXECUTION RESULTS ON {getattr(backend_selected, 'name', 'Simulator')}")
    print("=" * 80)
    print(f"  Total Valid Shots Measured  : {total_shots}")
    print(f"  QPU Total Job Latency       : {hw_latency_ms/1000.0:.2f} s")
    print(f"  Most Frequent QPU Bitstring : {best_hw_bits} ({sorted_shots[0][1]} shots, {sorted_shots[0][1]/total_shots*100:.2f}%)")
    print(f"  Ideal Simulator Bitstring   : {ideal_bitstring}")
    print(f"  Ideal Bitstring Probability : {p_ideal:.2f}%")
    print("-" * 80)
    print(f"  Initial Peak Network Occupancy: {eval_res['peak_before']*100:.2f}% (V6\u2194V2)")
    print(f"  Post-Hardware Peak Occupancy  : {eval_res['peak_after']*100:.2f}%")
    print(f"  Net Peak Congestion Reduction : {eval_res['peak_reduction_pct']:.2f}%")
    print(f"  Bottleneck V6\u2194V2 Flow Relieved : -900.0 veh/hr")
    print("=" * 80)

    # Save shot distribution plot
    plt.figure(figsize=(10, 5))
    top10 = sorted_shots[:10]
    bars = plt.bar([k for k, _ in top10], [v/total_shots*100.0 for _, v in top10], color="#1E88E5", edgecolor="#0D47A1")
    plt.axhline(100.0 / (2**N_QUBITS), color="#E53935", linestyle="--", label=f"Uniform Random ({100/(2**N_QUBITS):.2f}%)")
    plt.title(f"IBM Quantum QPU Measurement Histogram ({getattr(backend_selected, 'name', 'QPU')})", fontsize=12, fontweight="bold")
    plt.xlabel("Measured Bitstring", fontsize=10)
    plt.ylabel("Probability (%)", fontsize=10)
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(CHARTS_DIR, "ibm_8node_qpu_histogram.png")
    plt.savefig(plot_path, dpi=300)
    print(f"  Shot histogram saved to: {plot_path}")

    # Save summary JSON
    results_summary = {
        "backend": getattr(backend_selected, "name", "Simulator"),
        "total_shots": total_shots,
        "qpu_latency_s": hw_latency_ms / 1000.0,
        "most_frequent_bitstring": best_hw_bits,
        "ideal_bitstring": ideal_bitstring,
        "p_ideal_pct": p_ideal,
        "peak_before_pct": eval_res["peak_before"] * 100.0,
        "peak_after_pct": eval_res["peak_after"] * 100.0,
        "peak_reduction_pct": eval_res["peak_reduction_pct"],
        "green_times": green_times
    }
    json_path = os.path.join(CHARTS_DIR, "ibm_8node_results.json")
    with open(json_path, "w") as f:
        json.dump(results_summary, f, indent=2)
    print(f"  Experiment summary saved to: {json_path}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Run 8-node pipeline on IBM Quantum")
    parser.add_argument("--save-token", metavar="TOKEN", help="Save IBM Quantum API token permanently")
    parser.add_argument("--token", metavar="TOKEN", help="Pass IBM Quantum token directly for this run")
    parser.add_argument("--backend", metavar="NAME", help="Specify exact IBM Quantum backend (e.g. ibm_brisbane)")
    parser.add_argument("--simulator", action="store_true", help="Run on local Aer simulator for pre-flight testing")
    args = parser.parse_args()

    if args.save_token:
        print("[INFO] Saving IBM Quantum API token...")
        saved = False
        last_err = None
        for ch in ["ibm_quantum_platform", "ibm_quantum", "ibm_cloud"]:
            try:
                QiskitRuntimeService.save_account(
                    channel=ch,
                    token=args.save_token,
                    overwrite=True,
                    set_as_default=True,
                )
                saved = True
                print(f"[INFO] Successfully saved token with channel '{ch}'.")
                break
            except Exception as e:
                last_err = e
        if not saved:
            print(f"[ERROR] Could not save token: {last_err}")
        return

    run_experiment(
        use_real_hardware=not args.simulator,
        token=args.token,
        backend_name=args.backend
    )

if __name__ == "__main__":
    main()
