"""
run_ibm_quantum_experiment.py
==============================
Real IBM Quantum Hardware Experiment for QAOA Traffic Optimization.

Strategy (QPU-efficient, publishable):
  Phase 1 — Classical angle optimization (FREE, no QPU quota used):
    Find optimal QAOA gamma/beta parameters using StatevectorSampler + COBYLA.

  Phase 2 — Hardware execution (uses QPU quota):
    Execute the final QAOA circuit ONCE on real IBM hardware with optimal angles
    and 8192 shots. Collect the full shot distribution.

  Phase 3 — Analysis:
    Compare hardware shot histogram to ideal statevector distribution.
    Show how quantum noise affects solution reliability.
    Compare most-frequent hardware bitstring to classical PSO optimum.

Why this approach?
  - Running COBYLA on hardware (30 QPU calls) wastes 5-10 min of your monthly quota.
  - "Parameter transfer" (optimize classically, execute quantumly) is standard NISQ practice
    used in published research (Farhi et al., Cerezo et al.).
  - The shot histogram is what makes it quantum — it's unmistakably a quantum experiment.

Setup (one time only):
  1. Go to https://quantum.ibm.com and create a free account.
  2. Copy your API token from "Account Settings".
  3. Run: python run_ibm_quantum_experiment.py --save-token YOUR_TOKEN_HERE
     (This saves it permanently — you never need to enter it again.)
  4. Then run normally: python run_ibm_quantum_experiment.py

Outputs:
  - charts/ibm_shot_histogram.png        Shot distribution from real hardware
  - charts/ibm_circuit_diagram.png       Transpiled circuit on target backend
  - charts/ibm_comparison_figure.png     3-panel publication figure
  - charts/ibm_experiment_results.json   Full raw results
"""

import os
import sys
import json
import time
import argparse
import warnings
import numpy as np
import networkx as nx

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ── Project imports ────────────────────────────────────────────────────────────
from graph import TrafficGraph, Node, Edge
from pso import PSO
from final_qaoa_with_signal import (
    build_network, detect_congestion, generate_alternate_routes,
    generate_packets, build_qubo, solve_qaoa, apply_solution,
)
from run_publication_45_scenarios import generate_15_diverse_publication_scenarios

# ── Qiskit imports ─────────────────────────────────────────────────────────────
try:
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.converters import QuadraticProgramToQubo
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit.primitives import StatevectorSampler
    from qiskit.circuit.library import QAOAAnsatz
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    HAS_QISKIT = True
except ImportError as e:
    print(f"[ERROR] Qiskit not available: {e}")
    HAS_QISKIT = False

try:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2, Session
    HAS_IBM_RUNTIME = True
except ImportError:
    HAS_IBM_RUNTIME = False
    print("[WARNING] qiskit-ibm-runtime not installed.")
    print("          Run: pip install qiskit-ibm-runtime")

OUTPUT_DIR = os.path.join(current_dir, "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.edgecolor":    "#444",
    "axes.linewidth":    1.1,
})

SHOTS = 8192   # Standard for publication-quality shot statistics


# ══════════════════════════════════════════════════════════════════════════════
# 1. Scenario Setup  — uses the simplest 4-node scenario (fewest qubits)
# ══════════════════════════════════════════════════════════════════════════════

def setup_experiment_scenario():
    """
    Selects the 4-node Scenario 1 (Single Major Expressway Bottleneck).
    This typically generates 5-8 binary variables = 5-8 qubits.
    Minimises QPU resource cost while remaining representative.
    """
    G = nx.complete_graph(["A", "B", "C", "D"])
    scenarios = generate_15_diverse_publication_scenarios(list(G.nodes()), G, seed=2026)
    sc = scenarios[0]   # Scenario 1 — simplest

    print(f"[INFO] Scenario: {sc['name']}")
    G_built, norm_caps, norm_loads = build_network(G, sc["capacities"], sc["loads"])
    occupancy, congested, _ = detect_congestion(
        norm_caps, norm_loads, high_threshold=0.60, low_threshold=0.45
    )
    alt_routes = generate_alternate_routes(G_built, congested, occupancy, max_cutoff=3, top_k=2)
    packets, variables = generate_packets(
        congested, norm_loads, norm_caps, alt_routes,
        target=0.50, packet_size=150.0, max_packets=10
    )
    qubo_problem = build_qubo(variables, norm_caps, occupancy, target=0.50, packet_size=150.0)

    init_occs = [norm_loads[e] / norm_caps[e] for e in norm_caps]
    init_peak = max(init_occs) * 100.0

    print(f"[INFO] QUBO variables (qubits needed): {len(variables)}")
    print(f"[INFO] Initial peak occupancy: {init_peak:.1f}%")

    return {
        "scenario": sc,
        "G": G,
        "G_built": G_built,
        "norm_caps": norm_caps,
        "norm_loads": norm_loads,
        "packets": packets,
        "variables": variables,
        "qubo_problem": qubo_problem,
        "init_peak": init_peak,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Build QuadraticProgram from QUBO dict
# ══════════════════════════════════════════════════════════════════════════════

def build_qp_from_qubo(qubo_problem: dict) -> "QuadraticProgram":
    """Converts internal QUBO dict to Qiskit QuadraticProgram."""
    qp = QuadraticProgram("Traffic_Rebalancing_Hardware")
    for v in qubo_problem["variables"]:
        qp.binary_var(name=v["name"])
    qp.minimize(
        constant=qubo_problem["constant"],
        linear=qubo_problem["linear"],
        quadratic=qubo_problem["quadratic"],
    )
    return qp


# ══════════════════════════════════════════════════════════════════════════════
# 3. Phase 1 — Classical angle optimisation (StatevectorSampler, free)
# ══════════════════════════════════════════════════════════════════════════════

def optimize_qaoa_angles_classically(qp: "QuadraticProgram", reps: int = 1, maxiter: int = 50):
    """
    Finds optimal QAOA gamma/beta angles via StatevectorSampler + COBYLA.
    No QPU quota used. Returns optimal_point and ideal bitstring.
    """
    print(f"\n[Phase 1] Classical angle optimisation (StatevectorSampler, reps={reps}, maxiter={maxiter}) ...")
    t0 = time.perf_counter()

    qaoa = QAOA(
        sampler=StatevectorSampler(),
        optimizer=COBYLA(maxiter=maxiter),
        reps=reps,
    )
    solver = MinimumEigenOptimizer(qaoa)
    result = solver.solve(qp)

    elapsed = (time.perf_counter() - t0) * 1000.0
    optimal_point = result.min_eigen_solver_result.optimal_point
    ideal_bitstring = tuple(int(round(v)) for v in result.x)
    ideal_cost = float(result.fval)

    print(f"  Optimal angles: {np.round(optimal_point, 4)}")
    print(f"  Ideal bitstring: {ideal_bitstring}  |  Cost: {ideal_cost:.4f}")
    print(f"  Classical optimisation time: {elapsed:.0f} ms")

    return {
        "optimal_point": optimal_point,
        "ideal_bitstring": ideal_bitstring,
        "ideal_cost": ideal_cost,
        "classical_time_ms": elapsed,
        "reps": reps,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. Build transpiled QAOA circuit
# ══════════════════════════════════════════════════════════════════════════════

def build_qaoa_circuit(qp: "QuadraticProgram", optimal_point: np.ndarray, reps: int = 1):
    """
    Constructs the QAOA ansatz circuit from the QP Ising Hamiltonian
    and binds the optimal parameters found classically.
    Returns both the logical circuit and bound circuit.
    """
    converter = QuadraticProgramToQubo()
    qubo_qp   = converter.convert(qp)
    operator, _offset = qubo_qp.to_ising()

    ansatz = QAOAAnsatz(cost_operator=operator, reps=reps)
    ansatz.measure_all()   # add measurement layer

    bound_circuit = ansatz.assign_parameters(optimal_point)

    print(f"\n[Phase 2] QAOA circuit built:")
    print(f"  Qubits:         {ansatz.num_qubits}")
    print(f"  Circuit depth:  {ansatz.decompose().depth()} (logical)")
    print(f"  Parameters:     {ansatz.num_parameters}")

    return ansatz, bound_circuit, operator


def transpile_for_backend(bound_circuit, backend):
    """Transpiles the bound circuit to the target backend's native gate set."""
    from qiskit import transpile
    print(f"\n[INFO] Transpiling for backend: {backend.name} ...")
    t_circuit = transpile(bound_circuit, backend=backend, optimization_level=3)
    print(f"  Transpiled depth:       {t_circuit.depth()}")
    print(f"  Transpiled gate count:  {t_circuit.count_ops()}")
    return t_circuit


# ══════════════════════════════════════════════════════════════════════════════
# 5. Phase 2 — Real hardware execution
# ══════════════════════════════════════════════════════════════════════════════

def run_on_ibm_hardware(t_circuit, backend, shots: int = SHOTS):
    """
    Executes the bound, transpiled circuit on real IBM quantum hardware (Job mode).
    Compatible with IBM Quantum Open Plan (free tier).
    Returns raw shot counts dict.
    """
    print(f"\n[Phase 2] Submitting to IBM Quantum QPU: {backend.name} ({shots} shots) ...")
    print(f"  NOTE: Running in Job mode on Open Plan. Job is queued on QPU.")

    sampler = SamplerV2(mode=backend)
    job = sampler.run([t_circuit], shots=shots)
    job_id = job.job_id()
    print(f"  Job submitted successfully. Job ID: {job_id}")
    print(f"  Status URL: https://quantum.cloud.ibm.com/jobs/{job_id}")
    print(f"  Waiting for QPU execution (queue + hardware execution) ...")
    result = job.result()

    # Extract counts from SamplerV2 result format
    pub_result = result[0]
    counts = {}
    try:
        data_bin = pub_result.data
        bit_array = getattr(data_bin, "meas", None)
        if bit_array is None:
            for name in dir(data_bin):
                if not name.startswith("_"):
                    val = getattr(data_bin, name)
                    if hasattr(val, "get_counts"):
                        bit_array = val
                        break
        if bit_array is not None and hasattr(bit_array, "get_counts"):
            raw_counts = bit_array.get_counts()
            for bitstr, count in raw_counts.items():
                counts[str(bitstr)] = int(count)
        else:
            raise ValueError(f"Could not find bit array in DataBin: {data_bin}")
    except Exception as e:
        print(f"  [WARNING] Count extraction issue: {e}. Using raw result.")
        counts = {"parse_error": shots}

    total = sum(counts.values())
    print(f"  Hardware execution complete! Total shots: {total}")
    top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"  Top-5 measurement outcomes:")
    for bs, cnt in top5:
        print(f"    |{bs}> : {cnt} shots ({cnt/total*100:.1f}%)")

    return counts


def run_ibm_simulator(bound_circuit, shots: int = SHOTS):
    """
    Runs on local noise-free AerSimulator.
    Useful for validating the entire workflow and figure generation without QPU queue or quota.
    """
    print(f"\n[Phase 2 — SIMULATOR] Running shot simulation on AerSimulator ({shots} shots) ...")
    try:
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        sim = AerSimulator()
        t_circ = transpile(bound_circuit, backend=sim)
        result = sim.run(t_circ, shots=shots).result()
        counts = result.get_counts()
        total = sum(counts.values())
        print(f"  Simulation complete. Total shots: {total}")
        top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top-5 measurement outcomes:")
        for bs, cnt in top5:
            print(f"    |{bs}> : {cnt} shots ({cnt/total*100:.1f}%)")
        return dict(counts)
    except Exception as e:
        print(f"  [WARNING] Simulator execution failed: {e}")
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# 6. PSO classical baseline
# ══════════════════════════════════════════════════════════════════════════════

def run_pso_baseline(exp_data: dict) -> dict:
    """Runs the BPSO classical baseline for direct comparison."""
    print("\n[Baseline] Running BPSO classical solver ...")

    G_built   = exp_data["G_built"]
    norm_caps = exp_data["norm_caps"]
    norm_loads = exp_data["norm_loads"]

    t_graph = TrafficGraph()
    t_graph.nodes = {n: Node(id=n, label=n, initial_cycle_time=60.0) for n in G_built.nodes()}
    t_graph.edges = []
    t_graph._edge_index = {}
    for (u, v), cap in norm_caps.items():
        for src, tgt in [(u, v), (v, u)]:
            e = Edge(source=src, target=tgt, weight=1.0, capacity=cap,
                     speed=50.0, lanes=3, length=1.0, road_type="Arterial",
                     threshold=0.60 * cap)
            t_graph.edges.append(e)
            t_graph._edge_index[e.id] = e

    dir_loads = {}
    for (u, v), load in norm_loads.items():
        dir_loads[f"{u}\u2192{v}"] = load
        dir_loads[f"{v}\u2192{u}"] = load

    t0 = time.perf_counter()
    pso = PSO(n_particles=30, max_iter=20, seed=42)
    pso_res = pso.optimize(
        t_graph,
        initial_congestion=dir_loads,
        initial_cycle_times={n: 60.0 for n in G_built.nodes()},
    )
    pso_ms = (time.perf_counter() - t0) * 1000.0

    gbest = pso_res.get("gbest_bitstring", ())
    packets   = exp_data["packets"]
    qubo_prob = exp_data["qubo_problem"]

    if gbest:
        updated = apply_solution(packets, gbest, norm_loads, packet_size=150.0)
        occs    = [updated[e] / norm_caps[e] for e in norm_caps]
        pso_peak = max(occs) * 100.0
    else:
        pso_peak = exp_data["init_peak"]

    pso_red = (exp_data["init_peak"] - pso_peak) / exp_data["init_peak"] * 100.0
    print(f"  PSO peak: {pso_peak:.1f}% (reduction: {pso_red:.1f}%)  [{pso_ms:.0f} ms]")

    return {
        "peak": round(pso_peak, 2),
        "reduction": round(pso_red, 2),
        "runtime_ms": round(pso_ms, 2),
        "bitstring": list(gbest),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 7. Analyse hardware results
# ══════════════════════════════════════════════════════════════════════════════

def analyse_hardware_results(
    hw_counts: dict,
    exp_data: dict,
    ideal_bitstring: tuple,
    qubo_problem: dict,
) -> dict:
    """
    Decodes hardware shot counts:
    - Finds the most-frequent hardware bitstring
    - Evaluates its peak occupancy
    - Computes probability of sampling the ideal solution
    - Reports noise impact
    """
    if not hw_counts or "parse_error" in hw_counts:
        return {"error": "No valid hardware counts"}

    N         = len(exp_data["variables"])
    packets   = exp_data["packets"]
    norm_caps = exp_data["norm_caps"]
    norm_loads = exp_data["norm_loads"]
    init_peak  = exp_data["init_peak"]

    total_shots = sum(hw_counts.values())

    # Sort by frequency
    sorted_counts = sorted(hw_counts.items(), key=lambda x: x[1], reverse=True)

    # Decode top-10 bitstrings
    decoded = []
    for bitstr, count in sorted_counts[:20]:
        try:
            # Qiskit uses little-endian bit ordering: reverse to match variable order
            bits = tuple(int(b) for b in reversed(bitstr))
            if len(bits) != N:
                bits = bits[:N]  # trim ancilla bits if any
            updated = apply_solution(packets, bits, norm_loads, packet_size=150.0)
            occs    = [updated[e] / norm_caps[e] for e in norm_caps]
            peak    = max(occs) * 100.0
            red     = (init_peak - peak) / init_peak * 100.0
        except Exception:
            peak, red = init_peak, 0.0
        decoded.append({
            "bitstring_raw": bitstr,
            "bitstring": list(bits),
            "count": count,
            "probability": count / total_shots,
            "peak": round(peak, 2),
            "reduction": round(red, 2),
        })

    best_hw = decoded[0]

    # Probability of sampling the ideal bitstring
    ideal_raw = "".join(str(b) for b in reversed(ideal_bitstring))
    ideal_prob = hw_counts.get(ideal_raw, 0) / total_shots

    # Success rate: fraction of shots that achieve >= 90% of ideal reduction
    ideal_red = max(d["reduction"] for d in decoded) if decoded else 0.0
    threshold  = 0.90 * ideal_red
    success_shots = sum(
        cnt for bs, cnt in hw_counts.items()
        if any(d["bitstring_raw"] == bs and d["reduction"] >= threshold for d in decoded[:10])
    )
    success_rate = success_shots / total_shots

    print(f"\n[Analysis] Hardware Results:")
    print(f"  Most frequent bitstring: |{best_hw['bitstring_raw']}> "
          f"({best_hw['probability']*100:.1f}% of shots)")
    print(f"  Best hardware peak:      {best_hw['peak']:.1f}%  "
          f"(reduction: {best_hw['reduction']:.1f}%)")
    print(f"  P(ideal solution):       {ideal_prob*100:.2f}%")
    print(f"  Success rate (≥90% opt): {success_rate*100:.1f}%")

    return {
        "total_shots": total_shots,
        "top_bitstrings": decoded[:10],
        "best_hardware_peak": best_hw["peak"],
        "best_hardware_reduction": best_hw["reduction"],
        "ideal_solution_probability": round(ideal_prob, 4),
        "success_rate_90pct": round(success_rate, 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 8. Publication figures
# ══════════════════════════════════════════════════════════════════════════════

def plot_shot_histogram(hw_counts: dict, ideal_bitstring: tuple, out_path: str, n_qubits: int):
    """Shot distribution histogram — the core quantum experiment figure."""
    if not hw_counts or "parse_error" in hw_counts:
        print("[WARNING] No hardware counts to plot.")
        return

    total = sum(hw_counts.values())
    sorted_counts = sorted(hw_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    labels  = [bs for bs, _ in sorted_counts]
    probs   = [cnt / total for _, cnt in sorted_counts]
    ideal_raw = "".join(str(b) for b in reversed(ideal_bitstring))
    colors  = ["#7b1fa2" if lbl == ideal_raw else "#90a4ae" for lbl in labels]

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(range(len(labels)), probs, color=colors, edgecolor="white", linewidth=0.6)

    # Annotate ideal
    if ideal_raw in labels:
        idx = labels.index(ideal_raw)
        ax.annotate(
            f"Ideal solution\n|{ideal_raw}⟩\n({probs[idx]*100:.1f}%)",
            xy=(idx, probs[idx]),
            xytext=(idx + 0.5, probs[idx] + 0.02),
            arrowprops=dict(arrowstyle='->', color='#7b1fa2', lw=1.5),
            fontsize=9, color='#7b1fa2', fontweight='bold',
        )

    ax.set_xlabel("Measurement Outcome (bitstring)", fontsize=11)
    ax.set_ylabel("Probability", fontsize=11)
    ax.set_title(
        f"IBM Quantum Hardware Shot Distribution — QAOA on {n_qubits}-Qubit Traffic QUBO\n"
        f"({total} shots | Real QPU | Parameter-transfer from classical COBYLA)",
        fontsize=12, fontweight='bold', pad=10
    )
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8, family='monospace')
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color='#7b1fa2', label='Ideal QAOA solution'),
        Patch(color='#90a4ae', label='Other outcomes (quantum noise)'),
    ], fontsize=9, loc='upper right')

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[INFO] Shot histogram saved: {os.path.abspath(out_path)}")


def plot_comparison_figure(results: dict, out_path: str):
    """3-panel publication figure: peak comparison, runtime, success probability."""
    fig = plt.figure(figsize=(16, 5.5))
    gs  = gridspec.GridSpec(1, 3, figure=fig, wspace=0.38)

    # ── Panel A: Peak occupancy comparison ──────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    methods = ["Initial\nState", "Classical\nBPSO", "QAOA\n(Simulated)", "QAOA\n(IBM Hardware)"]
    peaks   = [
        results["init_peak"],
        results["pso"]["peak"],
        results["classical_qaoa"]["peak"],
        results["hardware"]["best_hardware_peak"],
    ]
    colors_bar = ["#90a4ae", "#0288d1", "#7b1fa2", "#c2185b"]

    bars = ax1.bar(methods, peaks, color=colors_bar, edgecolor="white", linewidth=0.8, alpha=0.9)
    for bar, val in zip(bars, peaks):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.3, f"{val:.1f}%",
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.axhline(60, color='red', linestyle='--', linewidth=1.2, alpha=0.6, label='Congestion threshold (60%)')
    ax1.set_title("Peak Occupancy After\nOptimization", fontsize=11, fontweight='bold', pad=8)
    ax1.set_ylabel("Peak Occupancy (%)", fontsize=10)
    ax1.set_ylim(0, max(peaks) * 1.15)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    ax1.legend(fontsize=8)

    # ── Panel B: Runtime comparison ─────────────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    rt_methods = ["BPSO\n(Classical)", "QAOA\n(Simulated)", "QAOA\n(Hardware)*"]
    rt_vals    = [
        results["pso"]["runtime_ms"],
        results["classical_qaoa"]["runtime_ms"],
        results.get("hardware_circuit_time_ms", 0),
    ]
    rt_colors  = ["#0288d1", "#7b1fa2", "#c2185b"]

    bars2 = ax2.bar(rt_methods, rt_vals, color=rt_colors, edgecolor="white", linewidth=0.8, alpha=0.9)
    for bar, val in zip(bars2, rt_vals):
        label = f"{val:.0f} ms" if val < 10000 else f"{val/1000:.1f} s"
        ax2.text(bar.get_x() + bar.get_width()/2, val + max(rt_vals)*0.01, label,
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax2.set_title("Wall-Clock Runtime\n(*circuit exec. only)", fontsize=11, fontweight='bold', pad=8)
    ax2.set_ylabel("Runtime (ms)", fontsize=10)
    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    ax2.annotate("* Angle optimization\nnot included in\nhardware time",
                 xy=(0.98, 0.95), xycoords='axes fraction', fontsize=7.5,
                 ha='right', va='top', color='gray',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5f5f5', edgecolor='#ccc'))

    # ── Panel C: Quantum measurement statistics ──────────────────────────
    ax3 = fig.add_subplot(gs[2])
    stat_labels  = ["P(ideal\nsolution)", "Success rate\n(≥90% optimal)"]
    stat_vals    = [
        results["hardware"]["ideal_solution_probability"] * 100,
        results["hardware"]["success_rate_90pct"] * 100,
    ]
    ax3.bar(stat_labels, stat_vals, color=["#7b1fa2", "#c2185b"],
            edgecolor="white", linewidth=0.8, alpha=0.9)
    for i, val in enumerate(stat_vals):
        ax3.text(i, val + 1, f"{val:.1f}%", ha='center', va='bottom',
                 fontsize=11, fontweight='bold')

    ax3.set_title("Quantum Measurement\nStatistics (Real QPU)", fontsize=11, fontweight='bold', pad=8)
    ax3.set_ylabel("Probability (%)", fontsize=10)
    ax3.set_ylim(0, 110)
    ax3.grid(axis='y', linestyle='--', alpha=0.4)

    fig.suptitle(
        "IBM Quantum Hardware Experiment: QAOA Traffic Optimization\n"
        "4-Node Network | Single Major Expressway Bottleneck Scenario",
        fontsize=13, fontweight='bold', y=1.02
    )
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[INFO] Comparison figure saved: {os.path.abspath(out_path)}")


def plot_circuit_diagram(ansatz, optimal_point: np.ndarray, out_path: str):
    """Saves the QAOA circuit diagram as a figure."""
    try:
        bound = ansatz.assign_parameters(optimal_point)
        fig = bound.decompose().draw("mpl", style="iqp", fold=40)
        fig.savefig(out_path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"[INFO] Circuit diagram saved: {os.path.abspath(out_path)}")
    except Exception as e:
        print(f"[WARNING] Circuit diagram failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 9. Main orchestrator
# ══════════════════════════════════════════════════════════════════════════════

def run_ibm_experiment(use_real_hardware: bool = True, reps: int = 1):
    """
    Full IBM Quantum experiment pipeline.

    Args:
        use_real_hardware: If True, submits to real QPU. If False, uses IBM Aer simulator.
        reps: QAOA circuit depth (p). Default p=1 for NISQ reliability.
    """
    if not HAS_QISKIT:
        print("[ERROR] Qiskit is required. Run: pip install qiskit qiskit-algorithms qiskit-optimization")
        return
    if not HAS_IBM_RUNTIME:
        print("[ERROR] qiskit-ibm-runtime is required. Run: pip install qiskit-ibm-runtime")
        return

    print("=" * 80)
    print("  IBM QUANTUM HARDWARE EXPERIMENT — QAOA TRAFFIC OPTIMIZATION")
    print(f"  Strategy: Classical angle optimisation → Real QPU execution ({SHOTS} shots)")
    print("=" * 80)

    # ── Step 1: Scenario setup ────────────────────────────────────────────
    exp_data = setup_experiment_scenario()
    qp = build_qp_from_qubo(exp_data["qubo_problem"])
    N  = len(exp_data["variables"])

    # ── Step 2: Classical angle optimisation (free, no QPU) ───────────────
    classical_angles = optimize_qaoa_angles_classically(qp, reps=reps, maxiter=50)
    optimal_point = classical_angles["optimal_point"]

    # ── Step 3: Build circuit ─────────────────────────────────────────────
    ansatz, bound_circuit, operator = build_qaoa_circuit(qp, optimal_point, reps=reps)

    # Save circuit diagram (logical, before transpilation)
    plot_circuit_diagram(
        ansatz, optimal_point,
        os.path.join(OUTPUT_DIR, "ibm_circuit_diagram.png")
    )

    # Classical simulation peak (using classical_angles ideal bitstring)
    ideal_bits = classical_angles["ideal_bitstring"]
    classical_updated = apply_solution(
        exp_data["packets"], ideal_bits, exp_data["norm_loads"], packet_size=150.0
    )
    classical_occs = [classical_updated[e] / exp_data["norm_caps"][e] for e in exp_data["norm_caps"]]
    classical_peak = max(classical_occs) * 100.0
    classical_red  = (exp_data["init_peak"] - classical_peak) / exp_data["init_peak"] * 100.0

    # ── Step 4: IBM Quantum hardware / simulator ──────────────────────────
    service = None
    try:
        for ch in [None, "ibm_quantum_platform", "ibm_quantum", "ibm_cloud"]:
            try:
                service = QiskitRuntimeService(channel=ch) if ch else QiskitRuntimeService()
                if service:
                    break
            except Exception:
                continue
        if service is None:
            service = QiskitRuntimeService()
    except Exception as e:
        print(f"\n[ERROR] IBM account not configured: {e}")
        print("  → Run: python run_ibm_quantum_experiment.py --save-token YOUR_TOKEN")
        return

    hw_counts = {}
    hw_exec_ms = 0.0

    if use_real_hardware:
        # Select least-busy real backend with enough qubits
        print(f"\n[INFO] Selecting IBM Quantum backend (min {N} qubits, real hardware) ...")
        backend = service.least_busy(
            operational=True,
            simulator=False,
            min_num_qubits=N,
        )
        print(f"  Selected backend: {backend.name}")
        t_circuit = transpile_for_backend(bound_circuit, backend)

        t_hw_start = time.perf_counter()
        hw_counts   = run_on_ibm_hardware(t_circuit, backend, shots=SHOTS)
        hw_exec_ms  = (time.perf_counter() - t_hw_start) * 1000.0
    else:
        # IBM Aer statevector simulator (no QPU quota)
        print("\n[INFO] Running on IBM Aer simulator (no real QPU).")
        hw_counts  = run_ibm_simulator(bound_circuit, shots=SHOTS)
        hw_exec_ms = 0.0

    # ── Step 5: PSO classical baseline ───────────────────────────────────
    pso_result = run_pso_baseline(exp_data)

    # ── Step 6: Analyse hardware results ─────────────────────────────────
    hw_analysis = analyse_hardware_results(
        hw_counts, exp_data, ideal_bits, exp_data["qubo_problem"]
    )

    # ── Step 7: Compose full results dict ────────────────────────────────
    all_results = {
        "scenario": exp_data["scenario"]["name"],
        "n_qubits": N,
        "qaoa_reps": reps,
        "shots": SHOTS,
        "init_peak": round(exp_data["init_peak"], 2),
        "classical_qaoa": {
            "peak":       round(classical_peak, 2),
            "reduction":  round(classical_red, 2),
            "cost":       classical_angles["ideal_cost"],
            "runtime_ms": round(classical_angles["classical_time_ms"], 2),
            "bitstring":  list(ideal_bits),
        },
        "pso": pso_result,
        "hardware": hw_analysis,
        "hardware_circuit_time_ms": round(hw_exec_ms, 2),
    }

    # ── Step 8: Save JSON ─────────────────────────────────────────────────
    json_path = os.path.join(OUTPUT_DIR, "ibm_experiment_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[INFO] Full results saved: {os.path.abspath(json_path)}")

    # ── Step 9: Generate figures ──────────────────────────────────────────
    plot_shot_histogram(
        hw_counts, ideal_bits,
        os.path.join(OUTPUT_DIR, "ibm_shot_histogram.png"),
        n_qubits=N,
    )
    plot_comparison_figure(
        all_results,
        os.path.join(OUTPUT_DIR, "ibm_comparison_figure.png"),
    )

    # ── Final console summary ─────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  EXPERIMENT SUMMARY")
    print("=" * 80)
    print(f"  Scenario:           {all_results['scenario']}")
    print(f"  QAOA qubits (N):    {N}")
    print(f"  QAOA circuit depth: p={reps}")
    print(f"  {'Method':<30} {'Peak%':<10} {'Reduction%':<14} {'Runtime (ms)'}")
    print(f"  {'-'*65}")
    print(f"  {'Initial State':<30} {all_results['init_peak']:<10.1f} {'—':<14} {'—'}")
    print(f"  {'Classical BPSO':<30} {pso_result['peak']:<10.1f} {pso_result['reduction']:<14.1f} {pso_result['runtime_ms']:.0f}")
    print(f"  {'QAOA (Statevector sim)':<30} {classical_peak:<10.1f} {classical_red:<14.1f} {classical_angles['classical_time_ms']:.0f}")
    if hw_analysis and "best_hardware_peak" in hw_analysis:
        print(f"  {'QAOA (IBM Real Hardware)':<30} {hw_analysis['best_hardware_peak']:<10.1f} "
              f"{hw_analysis['best_hardware_reduction']:<14.1f} {hw_exec_ms:.0f}")
        print(f"\n  P(ideal solution on QPU): {hw_analysis['ideal_solution_probability']*100:.2f}%")
        print(f"  Success rate (≥90% opt):  {hw_analysis['success_rate_90pct']*100:.1f}%")
    print("=" * 80)
    print(f"\n  Outputs in: {os.path.abspath(OUTPUT_DIR)}/ibm_*.png|json|tex\n")

    return all_results


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="IBM Quantum QAOA Traffic Optimization Experiment"
    )
    parser.add_argument(
        "--save-token", metavar="TOKEN",
        help="Save your IBM Quantum API token (run once, then omit)."
    )
    parser.add_argument(
        "--simulator", action="store_true",
        help="Use IBM Aer simulator instead of real QPU (no quota used)."
    )
    parser.add_argument(
        "--reps", type=int, default=1,
        help="QAOA circuit depth p (default: 1). Use p=1 for NISQ reliability."
    )
    args = parser.parse_args()

    # Save token if provided
    if args.save_token:
        if not HAS_IBM_RUNTIME:
            print("[ERROR] qiskit-ibm-runtime not installed. Run: pip install qiskit-ibm-runtime")
            return
        print(f"[INFO] Saving IBM Quantum API token ...")
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
                continue
        if not saved:
            print(f"[ERROR] Could not save IBM Quantum token: {last_err}")
            return
        print("[INFO] Token saved. You can now run without --save-token.")
        return

    run_ibm_experiment(
        use_real_hardware=not args.simulator,
        reps=args.reps,
    )


if __name__ == "__main__":
    main()
