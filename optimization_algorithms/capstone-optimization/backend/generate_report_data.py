import os, sys, time, json
import numpy as np
import networkx as nx
import torch
import pennylane as qml

CURRENT_DIR = "/Users/adityaupasani/capstone-final/optimization_algorithms/capstone-optimization/backend"
sys.path.insert(0, CURRENT_DIR)

from test_8node_pipeline import (
    STQGCN, EDGES, EDGE_NAMES, EDGE_CAPACITIES_LIST, CAPACITIES,
    NODE_NAMES, vqc_circuit_vectorized
)
from final_qaoa_with_signal import (
    detect_congestion, generate_alternate_routes,
    generate_packets, build_qubo, solve_qaoa, apply_solution,
    evaluate_network, optimize_signals, normalize_edge
)

repo_root = "/Users/adityaupasani/capstone-final"
dataset_path = os.path.join(repo_root, "prediction-final/Traffic Forecasting/Dataset/Single Network/mumbai_stqgcn_dataset_10k.npz")
checkpoint_path = os.path.join(repo_root, "prediction-final/Traffic Forecasting/Single Network/Unidirectional/STQGCN/stqgcn_K5_model.pt")

data = np.load(dataset_path)
X_node = data["node_features"]
E_edge = data["edge_features"]
T_temp = data["temporal_features"]
Y_target = data["target_flow"]
Y_speed = data["target_speed"]

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
s_true = Y_speed[t+1]

t_pred_start = time.perf_counter()
with torch.no_grad():
    T_expanded = t_in.unsqueeze(1).expand(-1, 8, -1)
    node_inputs = torch.cat([x_in, T_expanded], dim=-1)
    h_0 = model.node_embed(node_inputs)
    a_aggregated = torch.zeros_like(h_0)
    for e_idx, (src, dst) in enumerate(model.edges):
        h_src = h_0[:, src, :]
        e_feat = e_in[:, e_idx, :]
        msg_input = torch.cat([h_src, e_feat, t_in], dim=-1)
        msg = model.message_mlp(msg_input)
        a_aggregated[:, dst, :] += msg
    h_1 = h_0 + a_aggregated
    node_angles = model.q_pre_proj(torch.cat([h_1, T_expanded], dim=-1)).squeeze(-1) * np.pi
    q_expval_cpu = model.q_vqc(node_angles.cpu())
    
    y_pred_norm = model(x_in, e_in, t_in).squeeze(0).numpy()

pred_latency = (time.perf_counter() - t_pred_start) * 1000.0
y_pred = y_pred_norm * std_traffic + mu_traffic

# Prediction metrics
mae = float(np.mean(np.abs(y_pred - y_true)))
mape = float(np.mean(np.abs((y_pred - y_true) / (y_true + 1e-5)))) * 100.0
rmse = float(np.sqrt(np.mean((y_pred - y_true)**2)))
mse = float(np.mean((y_pred - y_true)**2))
ss_tot = np.sum((y_true - np.mean(y_true))**2)
ss_res = np.sum((y_true - y_pred)**2)
r2 = float(1.0 - (ss_res / (ss_tot + 1e-6)))

predicted_loads_dict = {}
for i in range(11):
    src, dst = EDGES[i]
    edge_key = normalize_edge(f"V{src+1}", f"V{dst+1}")
    predicted_loads_dict[edge_key] = float(y_pred[i])

G = nx.Graph()
for e in CAPACITIES:
    G.add_edge(e[0], e[1])

occ, cong, under = detect_congestion(CAPACITIES, predicted_loads_dict, high_threshold=0.60, low_threshold=0.45)
alt_routes = generate_alternate_routes(G, cong, occ, max_cutoff=4, top_k=2)
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
qaoa_latency = (time.perf_counter() - t_qaoa_start) * 1000.0

updated_loads = apply_solution(packets, sol["bitstring"], predicted_loads_dict, packet_size=150.0)
eval_res = evaluate_network(CAPACITIES, predicted_loads_dict, updated_loads)
green_times = optimize_signals(G, CAPACITIES, updated_loads, cycle_time=90.0, yellow_red_time=4.0)

lengths = [3.5, 2.8, 4.5, 4.0, 1.8, 2.5, 1.5, 2.0, 2.2, 3.0, 2.1]
spd_limits = [70, 60, 60, 60, 50, 80, 50, 50, 50, 50, 50]

bpr_delay_before = 0.0
bpr_delay_after = 0.0
for i in range(11):
    src, dst = EDGES[i]
    e_key = normalize_edge(f"V{src+1}", f"V{dst+1}")
    cap = EDGE_CAPACITIES_LIST[i]
    t0 = lengths[i] / spd_limits[i]
    flow_b = predicted_loads_dict[e_key]
    flow_a = updated_loads[e_key]
    d_b = flow_b * t0 * (1.0 + 0.15 * ((flow_b / cap)**4))
    d_a = flow_a * t0 * (1.0 + 0.15 * ((flow_a / cap)**4))
    bpr_delay_before += d_b
    bpr_delay_after += d_a

packet_list = []
for p in packets:
    u, v = p["origin"]
    packet_list.append({
        "id": p["id"],
        "origin": f"{u}-{v}",
        "r0": p["routes"][0],
        "r1": p["routes"][1]
    })

report = {
    "scenario_timestep": t,
    "pred_metrics": {
        "mae": mae,
        "mape": mape,
        "rmse": rmse,
        "mse": mse,
        "r2": r2,
        "latency_ms": pred_latency,
        "qubit_expvals": q_expval_cpu.squeeze(0).tolist(),
        "node_angles": node_angles.squeeze(0).tolist(),
    },
    "edge_table": [],
    "qubo_details": {
        "num_variables": len(variables),
        "constant": qubo_problem["constant"],
        "linear_terms": qubo_problem["linear"],
        "quadratic_terms": {f"{k[0]}:{k[1]}": v for k, v in qubo_problem["quadratic"].items()},
    },
    "packets": packet_list,
    "qaoa_solution": {
        "bitstring": sol["bitstring"],
        "best_cost": sol["best_cost"],
        "latency_ms": qaoa_latency
    },
    "network_eval": eval_res,
    "bpr_delay": {
        "before_veh_hrs": bpr_delay_before,
        "after_veh_hrs": bpr_delay_after,
        "reduction_pct": (bpr_delay_before - bpr_delay_after) / bpr_delay_before * 100.0
    },
    "green_times": green_times
}

for i in range(11):
    src, dst = EDGES[i]
    e_key = normalize_edge(f"V{src+1}", f"V{dst+1}")
    cap = EDGE_CAPACITIES_LIST[i]
    pred = float(y_pred[i])
    act = float(y_true[i])
    post_flow = float(updated_loads[e_key])
    report["edge_table"].append({
        "edge_id": f"E{i}",
        "name": EDGE_NAMES[i],
        "endpoints": f"V{src+1} -> V{dst+1}",
        "capacity": cap,
        "actual_flow": act,
        "predicted_flow": pred,
        "pred_error": abs(pred - act),
        "pred_err_pct": abs(pred - act) / (act + 1e-5) * 100.0,
        "occ_before_pct": (pred / cap) * 100.0,
        "flow_after": post_flow,
        "occ_after_pct": (post_flow / cap) * 100.0,
        "flow_change": post_flow - pred
    })

with open("report_data.json", "w") as f:
    json.dump(report, f, indent=2)

print("Report generated successfully and saved to report_data.json")
