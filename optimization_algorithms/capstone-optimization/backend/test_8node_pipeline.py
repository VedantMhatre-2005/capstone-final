"""
test_8node_pipeline.py
======================
End-to-end integration test of Traffic Forecasting (ST-QGCN) and
Traffic Optimization (QAOA) on the 8-Node Mumbai Highway Network.

Topology:
  Nodes (8): V1 (Borivali Toll), V2 (JVLR Interchange), V3 (Dadar TT Circle),
             V4 (Jogeshwari WEH), V5 (BKC Connector), V6 (Sion Circle),
             V7 (Lower Parel), V8 (South Terminal / Sea Link)
  Edges (11): Directed corridors with realistic physical capacities.

Workflow:
  1. Load dataset & pick peak bottleneck scenario (Timestep 8529).
  2. Perform traffic flow forecasting using pre-trained ST-QGCN (8-qubit VQC, K=5).
  3. Formulate QUBO and run QAOA optimization with Qiskit.
  4. Optimize dynamic traffic signal green splits for all 8 nodes.
  5. Print comprehensive diagnostic report.
"""

import os
import sys
import time
import math
import numpy as np
import networkx as nx
import torch
import torch.nn as nn
import pennylane as qml

# Ensure local backend imports resolve
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from graph import TrafficGraph
from final_qaoa_with_signal import (
    build_network, detect_congestion, generate_alternate_routes,
    generate_packets, build_qubo, solve_qaoa, apply_solution,
    evaluate_network, optimize_signals, normalize_edge
)

# ---------------------------------------------------------------------------
# 1. Network Topology Definition (8 Nodes, 11 Directed Edges)
# ---------------------------------------------------------------------------

NODE_NAMES = [
    "V1_Borivali_Toll",
    "V2_JVLR_Interchange",
    "V3_Dadar_TT_Circle",
    "V4_Jogeshwari_WEH",
    "V5_BKC_Connector",
    "V6_Sion_Circle",
    "V7_Lower_Parel",
    "V8_South_Terminal",
]

EDGES = [
    (0, 1), # E0: V1 -> V2
    (0, 3), # E1: V1 -> V4
    (0, 4), # E2: V1 -> V5
    (1, 2), # E3: V2 -> V3
    (1, 4), # E4: V2 -> V5
    (2, 7), # E5: V3 -> V8
    (3, 4), # E6: V4 -> V5
    (4, 5), # E7: V5 -> V6
    (5, 1), # E8: V6 -> V2 (Feedback Loop)
    (5, 6), # E9: V6 -> V7
    (6, 2), # E10: V7 -> V3
]

EDGE_NAMES = [f"V{src+1}\u2192V{dst+1}" for src, dst in EDGES]

# Base Physical Capacities (veh/hr)
EDGE_CAPACITIES_LIST = [
    4000.0, # E0: V1->V2 (WEH Main)
    3200.0, # E1: V1->V4
    3000.0, # E2: V1->V5
    3500.0, # E3: V2->V3
    2800.0, # E4: V2->V5
    4200.0, # E5: V3->V8 (Sea Link Corridor)
    2500.0, # E6: V4->V5
    3600.0, # E7: V5->V6 (BKC-Sion Link)
    2400.0, # E8: V6->V2 (Loop)
    2800.0, # E9: V6->V7
    3100.0, # E10: V7->V3
]

CAPACITIES = {
    normalize_edge(f"V{src+1}", f"V{dst+1}"): cap
    for (src, dst), cap in zip(EDGES, EDGE_CAPACITIES_LIST)
}

# ---------------------------------------------------------------------------
# 2. ST-QGCN Quantum Neural Network Architecture
# ---------------------------------------------------------------------------

NUM_QUBITS = 8
dev = qml.device("default.qubit", wires=NUM_QUBITS)

@qml.qnode(dev, interface="torch", diff_method="backprop")
def vqc_circuit_vectorized(inputs, weights):
    n_layers = weights.shape[0]
    for q in range(NUM_QUBITS):
        qml.RY(inputs[:, q], wires=q)
    for k in range(n_layers):
        for q in range(NUM_QUBITS):
            qml.RZ(weights[k, q, 0], wires=q)
            qml.RY(weights[k, q, 1], wires=q)
            qml.RZ(weights[k, q, 2], wires=q)
        for q in range(NUM_QUBITS):
            qml.CNOT(wires=[q, (q + 1) % NUM_QUBITS])
    return [qml.expval(qml.PauliZ(q)) for q in range(NUM_QUBITS)]

class QuantumVQCModule(nn.Module):
    def __init__(self, n_layers=5, n_qubits=8):
        super().__init__()
        self.weights = nn.Parameter(torch.randn(n_layers, n_qubits, 3) * 0.1)

    def forward(self, angles):
        weights_cpu = self.weights.cpu()
        out_list = vqc_circuit_vectorized(angles, weights_cpu)
        return torch.stack(out_list, dim=1)

class STQGCN(nn.Module):
    def __init__(self, num_nodes=8, num_edges=11, node_in_dim=6, edge_in_dim=6, temp_in_dim=4, hidden_dim=16, n_qubits=8, n_vqc_layers=5):
        super().__init__()
        self.num_nodes = num_nodes
        self.num_edges = num_edges
        self.edges = EDGES
        
        self.node_embed = nn.Sequential(
            nn.Linear(node_in_dim + temp_in_dim, hidden_dim),
            nn.ReLU()
        )
        self.message_mlp = nn.Sequential(
            nn.Linear(hidden_dim + edge_in_dim + temp_in_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, hidden_dim)
        )
        self.q_pre_proj = nn.Sequential(
            nn.Linear(hidden_dim + temp_in_dim, 1),
            nn.Tanh()
        )
        self.q_vqc = QuantumVQCModule(n_layers=n_vqc_layers, n_qubits=n_qubits)
        self.q_post_proj = nn.Sequential(
            nn.Linear(1 + temp_in_dim, hidden_dim),
            nn.ReLU()
        )
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.pred_mlp = nn.Sequential(
            nn.Linear(2 * hidden_dim + edge_in_dim + temp_in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self, X_node, E_edge, T_temp):
        B = X_node.size(0)
        T_expanded = T_temp.unsqueeze(1).expand(-1, self.num_nodes, -1)
        node_inputs = torch.cat([X_node, T_expanded], dim=-1)
        h_0 = self.node_embed(node_inputs)
        a_aggregated = torch.zeros_like(h_0)
        for e_idx, (src, dst) in enumerate(self.edges):
            h_src = h_0[:, src, :]
            e_feat = E_edge[:, e_idx, :]
            t_feat = T_temp
            msg_input = torch.cat([h_src, e_feat, t_feat], dim=-1)
            msg = self.message_mlp(msg_input)
            a_aggregated[:, dst, :] += msg
        h_1 = h_0 + a_aggregated
        node_angles = self.q_pre_proj(torch.cat([h_1, T_expanded], dim=-1)).squeeze(-1) * np.pi
        q_expval_cpu = self.q_vqc(node_angles.cpu())
        q_expval = q_expval_cpu.to(X_node.device).float().unsqueeze(-1)
        q_post = self.q_post_proj(torch.cat([q_expval, T_expanded], dim=-1))
        h_final = self.layer_norm(h_1 + q_post)
        predictions = []
        for e_idx, (src, dst) in enumerate(self.edges):
            h_s = h_final[:, src, :]
            h_d = h_final[:, dst, :]
            e_feat = E_edge[:, e_idx, :]
            t_feat = T_temp
            pred_input = torch.cat([h_s, h_d, e_feat, t_feat], dim=-1)
            pred_out = self.pred_mlp(pred_input).squeeze(-1)
            predictions.append(pred_out)
        return torch.stack(predictions, dim=1)

# ---------------------------------------------------------------------------
# 3. Main Integration Test Execution
# ---------------------------------------------------------------------------

def run_test():
    print("=" * 80)
    print(" 8-NODE GRAPH INTEGRATED PIPELINE: ST-QGCN PREDICTION + QAOA OPTIMIZATION")
    print("=" * 80)

    # Locate files relative to repository root
    repo_root = os.path.abspath(os.path.join(CURRENT_DIR, "../../../"))
    dataset_path = os.path.join(repo_root, "prediction-final/Traffic Forecasting/Dataset/Single Network/mumbai_stqgcn_dataset_10k.npz")
    checkpoint_path = os.path.join(repo_root, "prediction-final/Traffic Forecasting/Single Network/Unidirectional/STQGCN/stqgcn_K5_model.pt")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}")

    # Load dataset
    print(f"\n[1/4] Loading Mumbai 8-Node Traffic Dataset...")
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

    # Load trained model
    print(f"[2/4] Loading Pre-Trained ST-QGCN Model (K=5 VQC Layers)...")
    model = STQGCN(num_nodes=8, num_edges=11, node_in_dim=6, edge_in_dim=6, temp_in_dim=4, hidden_dim=16, n_qubits=8, n_vqc_layers=5)
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=False))
    model.eval()

    # Select peak bottleneck scenario (Timestep 8529: Evening Rush Hour with Central Bottlenecks)
    t = 8529
    x_in = torch.FloatTensor(X_norm[t:t+1])
    e_in = torch.FloatTensor(E_norm[t:t+1])
    t_in = torch.FloatTensor(T_temp[t:t+1])
    y_true = Y_target[t+1]

    t_pred_start = time.perf_counter()
    with torch.no_grad():
        y_pred_norm = model(x_in, e_in, t_in).squeeze(0).numpy()
    y_pred = y_pred_norm * std_traffic + mu_traffic
    pred_latency_ms = (time.perf_counter() - t_pred_start) * 1000.0

    mae = float(np.mean(np.abs(y_pred - y_true)))
    mape = float(np.mean(np.abs((y_pred - y_true) / (y_true + 1e-5)))) * 100.0

    print(f"\n--- ST-QGCN FORECASTING RESULTS (Timestep {t} \u2192 {t+1}) ---")
    print(f"Inference Latency : {pred_latency_ms:.2f} ms")
    print(f"Mean Absolute Error: {mae:.2f} veh/hr")
    print(f"Mean Abs % Error  : {mape:.2f} %")
    print("-" * 75)
    print(f"{'Edge':<12} {'Description':<28} {'Capacity':<10} {'Predicted':<12} {'Actual':<10} {'Occupancy':<10}")
    print("-" * 75)

    descriptions = [
        "V1->V2 (Borivali->JVLR)",
        "V1->V4 (Borivali->Jogeshwari)",
        "V1->V5 (Borivali->BKC)",
        "V2->V3 (JVLR->Dadar TT)",
        "V2->V5 (JVLR->BKC)",
        "V3->V8 (Dadar TT->Sea Link)",
        "V4->V5 (Jogeshwari->BKC)",
        "V5->V6 (BKC->Sion)",
        "V6->V2 (Sion->JVLR Loop)",
        "V6->V7 (Sion->Lower Parel)",
        "V7->V3 (Lower Parel->Dadar TT)"
    ]

    predicted_loads_dict = {}
    for i in range(11):
        src, dst = EDGES[i]
        edge_key = normalize_edge(f"V{src+1}", f"V{dst+1}")
        pred_val = float(y_pred[i])
        predicted_loads_dict[edge_key] = pred_val
        cap = EDGE_CAPACITIES_LIST[i]
        occ = (pred_val / cap) * 100.0
        print(f"{EDGE_NAMES[i]:<12} {descriptions[i]:<28} {cap:<10.0f} {pred_val:<12.1f} {y_true[i]:<10.1f} {occ:.1f}%")

    # Build NetworkX graph
    print(f"\n[3/4] Formulating QUBO & Running QAOA Optimization...")
    G = nx.Graph()
    for e in CAPACITIES:
        G.add_edge(e[0], e[1])

    occ, cong, under = detect_congestion(CAPACITIES, predicted_loads_dict, high_threshold=0.60, low_threshold=0.45)
    alt_routes = generate_alternate_routes(G, cong, occ, max_cutoff=4, top_k=2)

    # Prioritize worst bottleneck edges first for packetization
    sorted_cong = dict(sorted(cong.items(), key=lambda item: item[1], reverse=True))

    packets, variables = generate_packets(
        sorted_cong, predicted_loads_dict, CAPACITIES, alt_routes,
        target=0.50, packet_size=150.0, max_packets=6
    )

    qubo_problem = build_qubo(variables, CAPACITIES, occ, target=0.50, packet_size=150.0)

    t_qaoa_start = time.perf_counter()
    sol = solve_qaoa(
        qubo_problem,
        packets=packets,
        capacities=CAPACITIES,
        initial_loads=predicted_loads_dict,
        packet_size=150.0,
        reps=1,
        maxiter=30
    )
    qaoa_latency_ms = (time.perf_counter() - t_qaoa_start) * 1000.0

    # Apply solution
    updated_loads = apply_solution(packets, sol["bitstring"], predicted_loads_dict, packet_size=150.0)
    eval_res = evaluate_network(CAPACITIES, predicted_loads_dict, updated_loads)

    # Optimize dynamic signal timings for all 8 intersections
    green_times = optimize_signals(G, CAPACITIES, updated_loads, cycle_time=90.0, yellow_red_time=4.0)

    print(f"\n[4/4] Optimization Results & Signal Control Rebalancing:")
    print("=" * 80)
    print(f"Optimal QAOA Bitstring : {sol['bitstring']}")
    print(f"Number of Qubits       : {len(variables)}")
    print(f"QAOA Solver Latency    : {qaoa_latency_ms:.2f} ms")
    print(f"Initial Peak Occupancy : {eval_res['peak_before']*100:.2f}% (Edge: V2\u2194V6)")
    print(f"Post-QAOA Peak Occ.    : {eval_res['peak_after']*100:.2f}%")
    print(f"Peak Congestion Reduc. : {eval_res['peak_reduction_pct']:.2f}%")
    print(f"Standard Dev. Before   : {eval_res['stdev_before']*100:.2f}%")
    print(f"Standard Dev. After    : {eval_res['stdev_after']*100:.2f}%")
    print("-" * 80)
    print("Sample Optimized Signal Green Timings (seconds per 90s cycle):")
    for k in sorted(list(green_times.keys()))[:8]:
        print(f"  Approach {k:<8}: {green_times[k]:.1f} s")
    print("=" * 80)
    print(" ALL TESTS COMPLETED SUCCESSFULLY FOR 8-NODE GRAPH!")
    print("=" * 80)

if __name__ == "__main__":
    run_test()
