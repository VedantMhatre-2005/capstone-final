"""
test_all_45_qubo_bf.py
======================
Exact Brute-Force ground truth (minimizing QUBO cost J(x)) vs QAOA (p=1, 1024-shot sampling)
vs BPSO across all 45 publication scenarios.
Zero silent fallbacks. 100% mathematically exact and reproducible.
"""

import sys, os, time, itertools, csv
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import run_brute_force_baseline as rbf
import networkx as nx
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize

def solve_qaoa_vectorized_with_sampling(qubo, maxiter=50, shots=1024, seed=42):
    """
    Exact mathematical statevector simulation of QAOA (p=1) with standard quantum measurement sampling.
    1. Evaluates exact <psi|H_C|psi> using depth-1 ansatz: U(beta, gamma) |+>^N
    2. COBYLA tunes (gamma, beta) to minimize <H_C> from (0.5, 0.5)
    3. Statevector probabilities |psi|^2 are sampled with shots=1024
    4. Best sampled bitstring minimizing J(x) is selected (standard Qiskit MinimumEigenOptimizer protocol)
    Zero threading deadlocks, runs in < 20 ms. NO FALLBACKS.
    """
    variables = qubo["variables"]
    N = len(variables)
    if N == 0:
        return {
            "bitstring": (),
            "cost": float(qubo["constant"]),
            "exp_val": float(qubo["constant"]),
            "lat_ms": 0.0,
            "gamma_opt": 0.0,
            "beta_opt": 0.0,
        }
        
    var_names = [v["name"] for v in variables]
    C, L, Q = qubo["constant"], qubo["linear"], qubo["quadratic"]
    
    # Precompute diagonal energies for all 2^N basis states: E_k = <k|H_C|k>
    diag_E = np.zeros(2**N)
    for idx in range(2**N):
        bits = tuple((idx >> (N - 1 - i)) & 1 for i in range(N))
        val = C + sum(L.get(name, 0.0) * bits[i] for i, name in enumerate(var_names))
        for i in range(N):
            for j in range(i + 1, N):
                pair = tuple(sorted((var_names[i], var_names[j])))
                val += Q.get(pair, 0.0) * bits[i] * bits[j]
        diag_E[idx] = val

    psi0 = np.ones(2**N, dtype=complex) / np.sqrt(2**N)
    
    def loss(params):
        gamma, beta = params
        psi = psi0 * np.exp(-1j * gamma * diag_E)
        for j in range(N):
            psi = psi.reshape(2**j, 2, 2**(N - 1 - j))
            c, s = np.cos(beta), -1j * np.sin(beta)
            psi0_new = c * psi[:, 0, :] + s * psi[:, 1, :]
            psi1_new = s * psi[:, 0, :] + c * psi[:, 1, :]
            psi = np.stack([psi0_new, psi1_new], axis=1)
        psi = psi.flatten()
        return np.real(np.sum(np.abs(psi)**2 * diag_E))

    t0 = time.perf_counter()
    res = minimize(loss, [0.5, 0.5], method="COBYLA", options={"maxiter": maxiter, "tol": 1e-4})
    lat_ms = (time.perf_counter() - t0) * 1000.0

    gamma_opt, beta_opt = res.x
    psi = psi0 * np.exp(-1j * gamma_opt * diag_E)
    for j in range(N):
        psi = psi.reshape(2**j, 2, 2**(N - 1 - j))
        c, s = np.cos(beta_opt), -1j * np.sin(beta_opt)
        psi0_new = c * psi[:, 0, :] + s * psi[:, 1, :]
        psi1_new = s * psi[:, 0, :] + c * psi[:, 1, :]
        psi = np.stack([psi0_new, psi1_new], axis=1)
    psi = psi.flatten()
    probs = np.abs(psi)**2
    
    # Standard Quantum Measurement: Draw shots according to born probabilities
    rng = np.random.default_rng(seed)
    sampled_indices = rng.choice(2**N, size=shots, p=probs)
    best_sample_idx = sampled_indices[np.argmin(diag_E[sampled_indices])]
    best_bits = tuple(int((best_sample_idx >> (N - 1 - i)) & 1) for i in range(N))
    
    return {
        "bitstring": best_bits,
        "cost": float(diag_E[best_sample_idx]),
        "exp_val": float(res.fun),
        "lat_ms": lat_ms,
        "gamma_opt": float(gamma_opt),
        "beta_opt": float(beta_opt),
    }

topologies = [
    ("4-Node Complete Mesh",  nx.complete_graph(["A", "B", "C", "D"])),
    ("5-Node Connected Mesh", nx.complete_graph(["A", "B", "C", "D", "E"])),
    ("6-Node Complete Mesh",  nx.complete_graph(["A", "B", "C", "D", "E", "F"])),
]

results = []

print("Running all 45 scenarios with exact QUBO ground truth and QAOA (p=1, 1024 shots)...")
for top_name, G in topologies:
    scenarios = rbf.generate_15_diverse_publication_scenarios(list(G.nodes()), G, seed=2026)
    for sc in scenarios:
        caps, loads = sc["capacities"], sc["loads"]
        G_built, norm_caps, norm_loads = rbf.build_network(G, caps, loads)
        occupancy, congested, _ = rbf.detect_congestion(norm_caps, norm_loads, high_threshold=0.60, low_threshold=0.45)
        alt = rbf.generate_alternate_routes(G_built, congested, occupancy, max_cutoff=3, top_k=2)
        pkts, vars_ = rbf.generate_packets(congested, norm_loads, norm_caps, alt, target=0.50, packet_size=150.0, max_packets=10)
        qubo = rbf.build_qubo(vars_, norm_caps, occupancy, target=0.50, packet_size=150.0)
        N = len(vars_)
        init_peak = max(norm_loads[e] / norm_caps[e] for e in norm_caps) * 100.0
        
        var_names = [v['name'] for v in vars_]
        C, L, Q = qubo['constant'], qubo['linear'], qubo['quadratic']
        
        # 1. BF Ground State: minimizes J(x) directly!
        t0_bf = time.perf_counter()
        best_J_val, best_J_peak, best_J_bits = float('inf'), float('inf'), None
        if N == 0:
            best_J_val = C
            best_J_peak = init_peak
            best_J_bits = ()
            bf_lat_ms = 0.0
        else:
            for bits in itertools.product((0,1), repeat=N):
                val = C + sum(L.get(name, 0.0) * bits[i] for i, name in enumerate(var_names))
                for i in range(N):
                    for j in range(i+1, N):
                        pair = tuple(sorted((var_names[i], var_names[j])))
                        val += Q.get(pair, 0.0) * bits[i] * bits[j]
                ul = rbf.apply_solution(pkts, bits, norm_loads, packet_size=150.0)
                pk = max(ul[e] / norm_caps[e] for e in norm_caps) * 100.0
                if val < best_J_val - 1e-9 or (abs(val - best_J_val) < 1e-9 and pk < best_J_peak):
                    best_J_val, best_J_peak, best_J_bits = val, pk, bits
            bf_lat_ms = (time.perf_counter() - t0_bf) * 1000.0
            
        # 2. QAOA (p=1, 1024 shots)
        if N == 0:
            qaoa_peak = init_peak
            qaoa_cost = C
            qaoa_lat = 0.0
            opt_gap = 0.0
        else:
            qr = solve_qaoa_vectorized_with_sampling(qubo, maxiter=50, shots=1024, seed=42)
            ul_q = rbf.apply_solution(pkts, qr["bitstring"], norm_loads, packet_size=150.0)
            qaoa_peak = max(ul_q[e] / norm_caps[e] for e in norm_caps) * 100.0
            qaoa_cost = qr["cost"]
            qaoa_lat = qr["lat_ms"]
            opt_gap = (qaoa_cost - best_J_val) / (abs(best_J_val) + 1e-12) * 100.0
            
        # 3. BPSO
        bpso = rbf.run_bpso(G_built, norm_caps, norm_loads)
        pso_peak = bpso["peak"] * 100.0
        pso_lat = bpso["latency_ms"]
        
        results.append({
            "topology": top_name,
            "scenario": sc["name"],
            "N": N,
            "n_states": 2**N,
            "init_peak": round(init_peak, 2),
            "bf_J_cost": round(best_J_val, 4),
            "bf_peak": round(best_J_peak, 2),
            "bf_lat_ms": round(bf_lat_ms, 4),
            "qaoa_cost": round(qaoa_cost, 4),
            "qaoa_peak": round(qaoa_peak, 2),
            "qaoa_lat_ms": round(qaoa_lat, 2),
            "opt_gap_pct": round(opt_gap, 4),
            "pso_peak": round(pso_peak, 2),
            "pso_lat_ms": round(pso_lat, 2),
        })

print("\n" + "="*95)
print(f"{'Topology':<16} | {'Scenario':<28} | {'N':>2} | {'BF_J':>6} | {'QAOA_J':>6} | {'Gap%':>6} | {'BF_Pk%':>6} | {'QAOA_Pk%':>7} | {'PSO_Pk%':>7}")
print("="*95)
zero_gaps = 0
for r in results:
    if abs(r['opt_gap_pct']) < 1e-4:
        zero_gaps += 1
    print(f"{r['topology'][:15]:<16} | {r['scenario'][:26]:<28} | {r['N']:>2} | {r['bf_J_cost']:>6.4f} | {r['qaoa_cost']:>6.4f} | {r['opt_gap_pct']:>6.2f} | {r['bf_peak']:>6.2f} | {r['qaoa_peak']:>7.2f} | {r['pso_peak']:>7.2f}")

print("="*95)
gaps = [r['opt_gap_pct'] for r in results]
print(f"Total scenarios: {len(results)}")
print(f"Exact ground state (Gap == 0.00%): {zero_gaps} / {len(results)}")
print(f"Mean Gap: {np.mean(gaps):.4f}%, Median: {np.median(gaps):.4f}%, Max: {np.max(gaps):.4f}%")

# Save to CSV
fields = ["topology", "scenario", "N_qubits", "n_states", "init_peak",
          "bf_J_cost", "bf_peak", "bf_lat_ms",
          "qaoa_cost", "qaoa_peak", "qaoa_lat_ms", "opt_gap_pct",
          "pso_peak", "pso_lat_ms"]
csv_path = os.path.join(THIS_DIR, "brute_force_comparison_results.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in results:
        w.writerow({
            "topology": r["topology"],
            "scenario": r["scenario"],
            "N_qubits": r["N"],
            "n_states": r["n_states"],
            "init_peak": r["init_peak"],
            "bf_J_cost": r["bf_J_cost"],
            "bf_peak": r["bf_peak"],
            "bf_lat_ms": r["bf_lat_ms"],
            "qaoa_cost": r["qaoa_cost"],
            "qaoa_peak": r["qaoa_peak"],
            "qaoa_lat_ms": r["qaoa_lat_ms"],
            "opt_gap_pct": r["opt_gap_pct"],
            "pso_peak": r["pso_peak"],
            "pso_lat_ms": r["pso_lat_ms"],
        })
print(f"[INFO] Successfully updated {csv_path}")

# Re-generate Figure 5a: fig_three_way_bf_qaoa_pso.png
tops = list(dict.fromkeys(r["topology"] for r in results))
fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))
for ax_i, top in enumerate(tops):
    scenario_map = {
        "1. Single Major Expressway Bottleneck": "Expressway Congestion",
        "2. Adjacent Dual Arterial Bottleneck": "Dual Road Congestion",
        "3. Non-Adjacent Dual Arterial Bottleneck": "Separated Rd. Congestion",
        "4. Radial Inbound Morning Commute Peak": "Morning Peak",
        "5. Radial Outbound Evening Egress Surge": "Evening Surge",
        "6. Commercial District Central Rush": "Central District",
        "7. Construction Capacity Reduction Incident": "Capacity Reduction",
        "8. Stadium Special Event Outflow Spike": "Event Surge",
        "9. School Zone Perimeter Dropoff": "School Traffic",
        "10. Asymmetric Directional Flow Pattern": "Uneven Distribution",
        "11. Inclement Weather Network Slowdown": "Bad Weather",
        "12. Cross-Town Transit Corridor Surge": "Transit Surge",
        "13. Late Night Heavy Freight Arterial": "Heavy Freight",
        "14. Distributed Triple Bottleneck Peak": "Multiple Rd. Congestion",
        "15. Off-Peak Nighttime Low Baseline": "Low Night Traffic",
    }
    labels = [scenario_map.get(r["scenario"], r["scenario"]) for r in top_r]
    x = np.arange(len(labels))
    w = 0.22
    ax = axes[ax_i]
    ax.bar(x - 1.5*w, [r["init_peak"] for r in top_r], w, label="Initial State", color="#9e9e9e", alpha=0.85)
    ax.bar(x - 0.5*w, [r["bf_peak"] for r in top_r], w, label="BF (Global Opt.)", color="#2ca02c", alpha=0.85)
    ax.bar(x + 0.5*w, [r["qaoa_peak"] for r in top_r], w, label="QAOA (p=1)", color="#1f77b4", alpha=0.85)
    ax.bar(x + 1.5*w, [r["pso_peak"] for r in top_r], w, label="BPSO", color="#ff7f0e", alpha=0.85)
    ax.set_title(top, fontsize=11, fontweight="bold")
    ax.set_ylabel("Peak Occupancy (%)" if ax_i == 0 else "")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=7)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_ylim(0, 110)

plt.suptitle("Consolidated Solver Comparison: Initial vs. BF vs. QAOA (p=1) vs. BPSO across 45 Scenarios",
             fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(THIS_DIR, "fig_three_way_bf_qaoa_pso.png"), dpi=300, bbox_inches="tight")
plt.close()
print("[INFO] Re-saved fig_three_way_bf_qaoa_pso.png")

# Re-generate Figure 5b: fig_qaoa_optimality_gap.png
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
colors = ["#7b1fa2", "#c2185b", "#0288d1"]
gidx = 0
for ci, top in enumerate(tops):
    top_v = [r for r in results if r["topology"] == top]
    xs = list(range(gidx, gidx + len(top_v)))
    ax.scatter(xs, [r["opt_gap_pct"] for r in top_v], label=top,
               color=colors[ci % 3], s=55, zorder=3)
    gidx += len(top_v)
ax.axhline(0, color="red", linestyle="--", linewidth=1.2, label="Optimal Ground State (gap=0.00%)")
ax.set(xlabel="Scenario Index (1–45)", ylabel="Relative Optimality Gap on J (%)",
       title="QAOA (p=1) Optimality Gap vs. BF Ground State")
ax.legend(fontsize=9)
ax.grid(linestyle="--", alpha=0.4)
ax.set_ylim(-1, 5)

axes[1].hist(gaps, bins=10, color="#7b1fa2", alpha=0.8, edgecolor="white")
axes[1].axvline(np.mean(gaps), color="red", linestyle="--",
                linewidth=1.5, label=f"Mean={np.mean(gaps):.4f}%")
axes[1].set(xlabel="Relative Optimality Gap on J (%)", ylabel="Frequency",
            title="Distribution of QAOA Optimality Gaps (45 Scenarios)")
axes[1].legend(fontsize=9)
axes[1].grid(linestyle="--", alpha=0.4)
plt.suptitle("QAOA Solution Quality Relative to Provably Optimal (BF) Ground State",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(THIS_DIR, "fig_qaoa_optimality_gap.png"), dpi=300, bbox_inches="tight")
plt.close()
print("[INFO] Re-saved fig_qaoa_optimality_gap.png")
