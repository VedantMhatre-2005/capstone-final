"""
run_brute_force_baseline.py
============================
Adds exhaustive-search (brute-force, BF) as a THIRD comparison baseline
alongside QAOA (depth p=1) and BPSO across all 45 publication scenarios.

Addresses Reviewer #2, Comment 6:
    "A depth-one QAOA on <=10 variables is exactly solvable by brute force
     in microseconds (2^10=1024 states); the reported exact optimality gap
     of 0.0000 therefore demonstrates problem triviality rather than
     algorithmic strength. An exhaustive-search baseline must be added."

KEY DESIGN DECISIONS
--------------------
1. BF finds the GLOBAL OPTIMUM by enumerating all 2^N bitstrings.
   For N<=10, this is at most 1024 evaluations -- sub-millisecond.
2. QAOA is run via Qiskit (StatevectorSampler + COBYLA, p=1, maxiter=50).
   NO FALLBACK: if the Qiskit solver raises an exception, it propagates.
   No silent all-zeros fallback is allowed.
3. BPSO: 30 particles x 20 iterations, fixed seed=42.
4. Optimality gap (relative, %) = |cost_QAOA - cost_BF| / (|cost_BF| + eps)

Outputs (all written to reviewers_changes/):
    brute_force_comparison_results.csv
    fig_three_way_bf_qaoa_pso.png
    fig_qaoa_optimality_gap.png
    bf_three_way_table.tex

Random seeds: scenario generation = 2026, BPSO = 42.
"""

import os, sys, time, itertools, csv, warnings
warnings.filterwarnings("ignore")
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Dict, List, Any

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.normpath(
    os.path.join(THIS_DIR, "..", "optimization_algorithms",
                 "capstone-optimization", "backend")
)
sys.path.insert(0, BACKEND_DIR)

from graph import TrafficGraph, Node, Edge
from pso import PSO
from final_qaoa_with_signal import (
    build_network, detect_congestion, generate_alternate_routes,
    generate_packets, build_qubo, apply_solution,
)
from run_publication_45_scenarios import generate_15_diverse_publication_scenarios

try:
    from qiskit_optimization import QuadraticProgram
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit.primitives import StatevectorSampler
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
except ImportError as _qe:
    raise ImportError(
        f"Qiskit required but not found: {_qe}\n"
        "pip install qiskit qiskit-algorithms qiskit-optimization"
    ) from _qe

OUTPUT_DIR = THIS_DIR


# ---------------------------------------------------------------------------
# Solver 1 -- Exhaustive Brute Force (global optimum, O(2^N * N^2))
# ---------------------------------------------------------------------------

def brute_force_qubo(qubo_problem, packets, capacities, initial_loads, packet_size=150.0):
    """
    Enumerate all 2^N binary assignments; select the global optimum.
    Criterion: minimise peak occupancy; break ties by QUBO cost.
    N <= 10 => at most 1024 evaluations, runtime < 1 ms.
    This is a COMPARISON BASELINE, not a fallback for QAOA.
    """
    variables = qubo_problem["variables"]
    N = len(variables)
    if N == 0:
        return {
            "bitstring": (),
            "best_cost": qubo_problem["constant"],
            "best_peak": max(initial_loads[e] / capacities[e] for e in capacities),
            "latency_ms": 0.0,
            "n_states": 0,
        }
    assert N <= 10, f"BF requires N <= 10; got N={N}. Confirm max_packets=10."
    var_names = [v["name"] for v in variables]
    C, L, Q = qubo_problem["constant"], qubo_problem["linear"], qubo_problem["quadratic"]
    best_bits, best_qubo, best_peak = None, float("inf"), float("inf")
    n_states = 0
    t0 = time.perf_counter()
    for bits in itertools.product((0, 1), repeat=N):
        n_states += 1
        val = C
        for i, name in enumerate(var_names):
            val += L.get(name, 0.0) * bits[i]
        for i in range(N):
            for j in range(i + 1, N):
                pair = tuple(sorted((var_names[i], var_names[j])))
                val += Q.get(pair, 0.0) * bits[i] * bits[j]
        ul = apply_solution(packets, bits, initial_loads, packet_size=packet_size)
        pk = max(ul[e] / capacities[e] for e in capacities)
        if pk < best_peak - 1e-9 or (abs(pk - best_peak) < 1e-9 and val < best_qubo):
            best_peak, best_qubo, best_bits = pk, val, bits
    return {
        "bitstring": best_bits,
        "best_cost": best_qubo,
        "best_peak": best_peak,
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
        "n_states": n_states,
    }


# ---------------------------------------------------------------------------
# Solver 2 -- QAOA (Qiskit) -- NO FALLBACK
# ---------------------------------------------------------------------------

def qaoa_solve_strict(qubo_problem, packets, capacities, initial_loads,
                      reps=1, maxiter=50, packet_size=150.0):
    """
    Qiskit QAOA with COBYLA. NO FALLBACK -- exceptions propagate.
    The caller decides how to handle failure; no silent all-zeros return.
    """
    variables = qubo_problem["variables"]
    if not variables:
        raise ValueError(
            "QAOA called with empty QUBO. Check that congestion exists before calling."
        )
    qp = QuadraticProgram("Traffic_Rebalancing")
    for v in variables:
        qp.binary_var(name=v["name"])
    qp.minimize(
        constant=qubo_problem["constant"],
        linear=qubo_problem["linear"],
        quadratic=qubo_problem["quadratic"],
    )
    t0 = time.perf_counter()
    solver = MinimumEigenOptimizer(
        QAOA(sampler=StatevectorSampler(), optimizer=COBYLA(maxiter=maxiter), reps=reps)
    )
    result = solver.solve(qp)   # raises on failure -- no try/except here
    latency_ms = (time.perf_counter() - t0) * 1000.0
    best_bits = tuple(int(round(x)) for x in result.x)
    ul = apply_solution(packets, best_bits, initial_loads, packet_size=packet_size)
    peak = max(ul[e] / capacities[e] for e in capacities)
    return {
        "bitstring": best_bits,
        "best_cost": float(result.fval),
        "best_peak": peak,
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Solver 3 -- BPSO
# ---------------------------------------------------------------------------

def run_bpso(G_built, norm_caps, norm_loads, pso_seed=42):
    dir_init = {}
    for (u, v), load in norm_loads.items():
        dir_init[f"{u}->{v}"] = load
        dir_init[f"{v}->{u}"] = load
    t_graph = TrafficGraph()
    t_graph.nodes = {n: Node(id=n, label=n, initial_cycle_time=60.0) for n in G_built.nodes()}
    t_graph.edges, t_graph._edge_index = [], {}
    for (u, v), cap in norm_caps.items():
        for src, tgt in [(u, v), (v, u)]:
            e = Edge(source=src, target=tgt, weight=1.0, capacity=cap,
                     speed=50.0, lanes=3, length=1.0,
                     road_type="Arterial", threshold=0.60 * cap)
            t_graph.edges.append(e)
            t_graph._edge_index[e.id] = e
    pso = PSO(n_particles=30, max_iter=20, seed=pso_seed)
    t0 = time.perf_counter()
    res = pso.optimize(t_graph, initial_congestion=dir_init,
                       initial_cycle_times={n: 60.0 for n in G_built.nodes()})
    latency_ms = (time.perf_counter() - t0) * 1000.0
    flows = res["optimized_congestion"]
    occs  = [flows.get(e.id, 0.0) / e.capacity for e in t_graph.edges if e.capacity > 0]
    return {
        "peak": max(occs) if occs else float("nan"),
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Per-scenario evaluation
# ---------------------------------------------------------------------------

def evaluate_scenario(topology_name, G, scenario):
    caps, loads = scenario["capacities"], scenario["loads"]
    G_built, norm_caps, norm_loads = build_network(G, caps, loads)
    occupancy, congested, _ = detect_congestion(norm_caps, norm_loads,
                                                high_threshold=0.60, low_threshold=0.45)
    alt_routes = generate_alternate_routes(G_built, congested, occupancy, max_cutoff=3, top_k=2)
    packets, variables = generate_packets(congested, norm_loads, norm_caps, alt_routes,
                                          target=0.50, packet_size=150.0, max_packets=10)
    qubo = build_qubo(variables, norm_caps, occupancy, target=0.50, packet_size=150.0)
    N = len(variables)
    init_peak = max(norm_loads[e] / norm_caps[e] for e in norm_caps) * 100.0

    # BF
    bf = brute_force_qubo(qubo, packets, norm_caps, norm_loads)
    bf_peak_pct = bf["best_peak"] * 100.0

    # QAOA
    qaoa_failed, qaoa_peak, qaoa_cost, qaoa_lat, opt_gap = False, None, None, None, None
    if N == 0:
        qaoa_peak, qaoa_lat, opt_gap = init_peak, 0.0, 0.0
        bf_peak_pct = init_peak
    else:
        try:
            qr = qaoa_solve_strict(qubo, packets, norm_caps, norm_loads)
            qaoa_peak = qr["best_peak"] * 100.0
            qaoa_cost = qr["best_cost"]
            qaoa_lat  = qr["latency_ms"]
            opt_gap   = abs(qaoa_cost - bf["best_cost"]) / (abs(bf["best_cost"]) + 1e-12) * 100.0
        except Exception as exc:
            qaoa_failed = True
            print(f"  [QAOA FAILED] {scenario['name']}: {exc}")

    # BPSO
    bpso = run_bpso(G_built, norm_caps, norm_loads)
    pso_peak = bpso["peak"] * 100.0

    return {
        "topology": topology_name,
        "scenario": scenario["name"],
        "N_qubits": N,
        "n_states": bf.get("n_states", 2 ** N),
        "init_peak": round(init_peak,   2),
        "bf_peak":   round(bf_peak_pct, 2),
        "bf_lat_ms": round(bf["latency_ms"], 4),
        "qaoa_peak": round(qaoa_peak, 2)   if qaoa_peak is not None else None,
        "qaoa_lat_ms": round(qaoa_lat, 2)  if qaoa_lat  is not None else None,
        "opt_gap_pct": round(opt_gap, 4)   if opt_gap   is not None else None,
        "pso_peak":  round(pso_peak,  2),
        "pso_lat_ms": round(bpso["latency_ms"], 2),
        "qaoa_failed": qaoa_failed,
    }


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_three_way(results):
    tops  = list(dict.fromkeys(r["topology"] for r in results))
    fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))
    for ax_i, top in enumerate(tops):
        top_r  = [r for r in results if r["topology"] == top]
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
        x, w   = np.arange(len(labels)), 0.25
        ax     = axes[ax_i]
        ax.bar(x - w, [r["bf_peak"]                                       for r in top_r], w,
               label="BF (Global Opt.)", color="#2ca02c", alpha=0.85)
        ax.bar(x,     [r["qaoa_peak"] if r["qaoa_peak"] is not None else float("nan")
                       for r in top_r], w, label="QAOA (p=1)", color="#1f77b4", alpha=0.85)
        ax.bar(x + w, [r["pso_peak"]                                       for r in top_r], w,
               label="BPSO", color="#ff7f0e", alpha=0.85)
        ax.set_title(top, fontsize=10, fontweight="bold")
        ax.set_ylabel("Peak Occupancy (%)" if ax_i == 0 else "")
        ax.set_xticks(x); ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=6.5)
        ax.legend(fontsize=8); ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_ylim(0, 110)
    plt.suptitle("BF (Global Opt.) vs QAOA (p=1) vs BPSO across 45 Scenarios",
                 fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_three_way_bf_qaoa_pso.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("[INFO] Saved fig_three_way_bf_qaoa_pso.png")


def plot_opt_gap(results):
    valid = [r for r in results if not r["qaoa_failed"] and r["opt_gap_pct"] is not None]
    if not valid:
        return
    tops   = list(dict.fromkeys(r["topology"] for r in valid))
    colors = ["#7b1fa2", "#c2185b", "#0288d1"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax, gidx = axes[0], 0
    for ci, top in enumerate(tops):
        top_v = [r for r in valid if r["topology"] == top]
        xs = list(range(gidx, gidx + len(top_v)))
        ax.scatter(xs, [r["opt_gap_pct"] for r in top_v], label=top,
                   color=colors[ci % 3], s=55, zorder=3)
        gidx += len(top_v)
    ax.axhline(0, color="red", linestyle="--", linewidth=1.2, label="Optimal (gap=0)")
    ax.set(xlabel="Scenario Index (1-45)", ylabel="Relative Optimality Gap (%)",
           title="QAOA (p=1) Optimality Gap vs BF Global Optimum")
    ax.legend(fontsize=9); ax.grid(linestyle="--", alpha=0.4)

    gaps_all = [r["opt_gap_pct"] for r in valid]
    axes[1].hist(gaps_all, bins=12, color="#7b1fa2", alpha=0.8, edgecolor="white")
    axes[1].axvline(np.mean(gaps_all), color="red", linestyle="--",
                    linewidth=1.5, label=f"Mean={np.mean(gaps_all):.3f}%")
    axes[1].set(xlabel="Relative Optimality Gap (%)", ylabel="Frequency",
                title="Distribution of QAOA Optimality Gaps (45 Scenarios)")
    axes[1].legend(fontsize=9); axes[1].grid(linestyle="--", alpha=0.4)
    plt.suptitle("QAOA Solution Quality Relative to Provably Optimal (BF) Solution",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_qaoa_optimality_gap.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("[INFO] Saved fig_qaoa_optimality_gap.png")


def plot_latency(results):
    valid = [r for r in results if r["qaoa_peak"] is not None]
    if not valid:
        return
    bf_lats = [r["bf_lat_ms"]    for r in results]
    qa_lats = [r["qaoa_lat_ms"]  for r in valid]
    ps_lats = [r["pso_lat_ms"]   for r in results]
    fig, ax = plt.subplots(figsize=(9, 5))
    ms = [np.mean(bf_lats), np.mean(qa_lats), np.mean(ps_lats)]
    se = [np.std(bf_lats),  np.std(qa_lats),  np.std(ps_lats)]
    bars = ax.bar(np.arange(3), ms, color=["#2ca02c", "#1f77b4", "#ff7f0e"], alpha=0.85, width=0.5)
    ax.errorbar(np.arange(3), ms, yerr=se, fmt="none", color="black", capsize=6, linewidth=2)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(["BF\n(Global Opt.)", "QAOA\n(p=1, Qiskit)", "BPSO\n(30 particles)"], fontsize=11)
    ax.set_ylabel("Mean Solve Latency (ms)", fontsize=11)
    ax.set_title("Solver Latency (wall-clock, excl. Qiskit circuit compilation)\nMean +/- 1 Std Dev",
                 fontsize=11, fontweight="bold")
    for bar, val, err in zip(bars, ms, se):
        ax.text(bar.get_x() + bar.get_width() / 2, val + err + 0.2,
                f"{val:.2f} ms", ha="center", va="bottom", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_ylim(0, max(ms) * 1.35)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_solver_latency.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("[INFO] Saved fig_solver_latency.png")


# ---------------------------------------------------------------------------
# CSV + LaTeX
# ---------------------------------------------------------------------------

def save_csv(results):
    out = os.path.join(OUTPUT_DIR, "brute_force_comparison_results.csv")
    fields = ["topology", "scenario", "N_qubits", "n_states", "init_peak",
              "bf_peak", "bf_lat_ms", "qaoa_peak", "qaoa_lat_ms",
              "opt_gap_pct", "pso_peak", "pso_lat_ms", "qaoa_failed"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"[INFO] CSV saved: {out}")


def save_latex(results):
    out  = os.path.join(OUTPUT_DIR, "bf_three_way_table.tex")
    tops = list(dict.fromkeys(r["topology"] for r in results))
    with open(out, "w", encoding="utf-8") as f:
        f.write("% Three-way comparison: BF vs QAOA vs BPSO\n")
        f.write("% Addresses R2-C6 (exhaustive baseline) and R3-C3 (BPSO column)\n\n")
        for top in tops:
            top_r = [r for r in results if r["topology"] == top]
            lbl   = top.lower().replace(" ", "_").replace("-", "")
            f.write("\\begin{table}[h!]\n\\centering\n")
            f.write(f"\\caption{{Three-way solver comparison on {top} (15 scenarios, seed=2026). "
                    f"BF = exhaustive brute force (global optimum, $\\leq$1024 states). "
                    f"Gap = $|J_{{\\text{{QAOA}}}}-J_{{\\text{{BF}}}}|/|J_{{\\text{{BF}}}}|\\times100\\%$.}}\n")
            f.write(f"\\label{{tab:threeway_{lbl}}}\n")
            f.write("\\begin{tabular}{p{5.0cm} c c c c c c}\n\\toprule\n")
            f.write("\\textbf{Scenario} & $N$ & \\textbf{Init.\\%} & "
                    "\\textbf{BF\\%} & \\textbf{QAOA\\%} & \\textbf{Gap\\%} & \\textbf{BPSO\\%} \\\\\n\\midrule\n")
            for r in top_r:
                sc = r["scenario"].split(". ", 1)[1]
                qs = f"{r['qaoa_peak']:.2f}" if r["qaoa_peak"] is not None else "FAIL"
                gs = f"{r['opt_gap_pct']:.4f}" if r["opt_gap_pct"] is not None else "FAIL"
                f.write(f"{sc} & {r['N_qubits']} & {r['init_peak']:.2f} & "
                        f"{r['bf_peak']:.2f} & {qs} & {gs} & {r['pso_peak']:.2f} \\\\\n")
            valid = [r for r in top_r if r["opt_gap_pct"] is not None]
            if valid:
                f.write("\\midrule\n")
                f.write(f"\\textbf{{Mean}} & {np.mean([r['N_qubits'] for r in valid]):.1f} & "
                        f"{np.mean([r['init_peak'] for r in valid]):.2f} & "
                        f"{np.mean([r['bf_peak'] for r in valid]):.2f} & "
                        f"{np.mean([r['qaoa_peak'] for r in valid]):.2f} & "
                        f"{np.mean([r['opt_gap_pct'] for r in valid]):.4f} & "
                        f"{np.mean([r['pso_peak'] for r in valid]):.2f} \\\\\n")
            f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n\n")
    print(f"[INFO] LaTeX table saved: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    topologies = [
        ("4-Node Complete Mesh",  nx.complete_graph(["A", "B", "C", "D"])),
        ("5-Node Connected Mesh", nx.complete_graph(["A", "B", "C", "D", "E"])),
        ("6-Node Complete Mesh",  nx.complete_graph(["A", "B", "C", "D", "E", "F"])),
    ]
    all_results = []
    for top_name, G in topologies:
        hdr = (
            f"{'Scenario':<42} | {'N':>3} | {'Init%':>6} | "
            f"{'BF%':>6} | {'BF(ms)':>8} | "
            f"{'QAOA%':>6} | {'QAOA(ms)':>9} | {'Gap%':>7} | "
            f"{'BPSO%':>6} | {'BPSO(ms)':>9}"
        )
        sep_len = max(len(hdr), 100)
        print(f"\n{'='*sep_len}\n  {top_name.upper()} -- BF vs QAOA (p=1, strict) vs BPSO\n{'='*sep_len}")
        scenarios = generate_15_diverse_publication_scenarios(list(G.nodes()), G, seed=2026)
        print(hdr); print("-" * len(hdr))
        for sc in scenarios:
            r = evaluate_scenario(top_name, G, sc)
            all_results.append(r)
            qs = f"{r['qaoa_peak']:>6.2f}" if r["qaoa_peak"] is not None else "  FAIL"
            ql = f"{r['qaoa_lat_ms']:>9.2f}" if r["qaoa_lat_ms"] is not None else "     FAIL"
            gs = f"{r['opt_gap_pct']:>7.4f}" if r["opt_gap_pct"] is not None else "   FAIL"
            bl = f"{r['bf_lat_ms']:>8.4f}"
            pl = f"{r['pso_lat_ms']:>9.2f}"
            print(
                f"{r['scenario']:<42} | {r['N_qubits']:>3} | {r['init_peak']:>6.2f} | "
                f"{r['bf_peak']:>6.2f} | {bl} | "
                f"{qs} | {ql} | {gs} | "
                f"{r['pso_peak']:>6.2f} | {pl}"
            )
    # Summary
    valid = [r for r in all_results if not r["qaoa_failed"] and r["opt_gap_pct"] is not None]
    if valid:
        gaps = [r["opt_gap_pct"] for r in valid]
        bf_l = [r["bf_lat_ms"]   for r in all_results]
        qa_l = [r["qaoa_lat_ms"] for r in valid]
        ps_l = [r["pso_lat_ms"]  for r in all_results]
        print(f"\n{'='*70}\n  SUMMARY  (n={len(valid)} valid QAOA / 45)\n{'='*70}")
        print(f"  QAOA Relative Optimality Gap:  Mean={np.mean(gaps):.4f}%  "
              f"Median={np.median(gaps):.4f}%  Max={np.max(gaps):.4f}%")
        print(f"  BF Latency (ms):               Mean={np.mean(bf_l):.4f}  "
              f"Max={np.max(bf_l):.4f}")
        print(f"  QAOA Latency (ms):             Mean={np.mean(qa_l):.2f}  "
              f"Max={np.max(qa_l):.2f}")
        print(f"  BPSO Latency (ms):             Mean={np.mean(ps_l):.2f}  "
              f"Max={np.max(ps_l):.2f}")
    save_csv(all_results)
    save_latex(all_results)
    plot_three_way(all_results)
    plot_opt_gap(all_results)
    plot_latency(all_results)
    print("\n[DONE] All outputs written to reviewers_changes/")

if __name__ == "__main__":
    main()
