"""
run_rigorous_comparison.py
==========================
Statistically Rigorous QAOA vs BPSO Comparison Study.

Design:
  - Fixed set of 15 canonical scenarios per topology (seed=2026).
  - QAOA: run at circuit depth p=1 AND p=2 (reps=1, reps=2).
    Captures the effect of expressibility on solution quality.
  - PSO:  run N_PSO_TRIALS=5 independent trials with distinct random seeds.
    Captures classical solver variance across initializations.

No brute-force fallback. No artificial fallbacks. QAOA runs as-is via
Qiskit StatevectorSampler + COBYLA (same as production code).

Metrics (per scenario, per topology):
  1. Peak occupancy (%) after optimization  -- primary traffic metric
  2. QUBO objective cost achieved           -- solver quality metric
  3. Peak reduction (%) from initial state
  4. Load std-dev (%) -- traffic uniformity
  5. Wall-clock runtime (ms)
  6. Solver divergence: cases where QAOA and best-PSO differ >1%

Outputs:
  - Console table: per-scenario summary + aggregates
  - charts/rigorous_comparison_results.json
  - charts/rigorous_comparison_table.tex
  - charts/rigorous_comparison_peaks.png
  - charts/rigorous_comparison_qubo.png
  - charts/rigorous_comparison_runtime.png
"""

import os
import sys
import time
import json
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from graph import TrafficGraph, Node, Edge
from pso import PSO
from final_qaoa_with_signal import (
    build_network, detect_congestion, generate_alternate_routes,
    generate_packets, build_qubo, solve_qaoa, apply_solution,
)
from run_publication_45_scenarios import generate_15_diverse_publication_scenarios

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
SCENARIO_SEED  = 2026
N_PSO_TRIALS   = 5
PSO_SEEDS      = [42, 123, 456, 789, 2026]
QAOA_REPS_LIST = [1, 2]        # circuit depths to benchmark
QAOA_MAXITER   = 50
PSO_PARTICLES  = 30
PSO_MAXITER    = 20

OUTPUT_DIR = os.path.join(current_dir, "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family":          "DejaVu Sans",
    "axes.edgecolor":       "#444444",
    "axes.linewidth":       1.1,
    "axes.spines.top":      False,
    "axes.spines.right":    False,
})

PALETTE = {
    "qaoa_p1":  "#7b1fa2",
    "qaoa_p2":  "#c2185b",
    "pso_best": "#0288d1",
    "pso_mean": "#81d4fa",
}


# ─────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────

def eval_qubo_cost(qubo_problem: Dict, bitstring: Tuple) -> float:
    """Evaluates QUBO objective H_B(b) for a given bitstring."""
    var_names = [v["name"] for v in qubo_problem["variables"]]
    C = qubo_problem["constant"]
    L = qubo_problem["linear"]
    Q = qubo_problem["quadratic"]
    val = C
    for i, name in enumerate(var_names):
        val += L.get(name, 0.0) * bitstring[i]
    for i in range(len(var_names)):
        for j in range(i + 1, len(var_names)):
            pair = tuple(sorted((var_names[i], var_names[j])))
            val += Q.get(pair, 0.0) * bitstring[i] * bitstring[j]
    return float(val)


def peak_and_std(bitstring, packets, norm_caps, norm_loads) -> Tuple[float, float]:
    """Returns (peak_occupancy_pct, load_std_pct) after decoding a bitstring."""
    updated = apply_solution(packets, bitstring, norm_loads, packet_size=150.0)
    occs    = [updated[e] / norm_caps[e] for e in norm_caps]
    return max(occs) * 100.0, float(np.std(occs)) * 100.0


# ─────────────────────────────────────────────
# Per-Scenario Evaluation
# ─────────────────────────────────────────────

def evaluate_scenario(top_name: str, G: nx.Graph, scenario: Dict) -> Dict:
    """
    Runs QAOA at two circuit depths and PSO with N_PSO_TRIALS seeds on one scenario.
    """
    caps  = scenario["capacities"]
    loads = scenario["loads"]

    # Shared network setup
    G_built, norm_caps, norm_loads = build_network(G, caps, loads)
    occupancy, congested, _ = detect_congestion(
        norm_caps, norm_loads, high_threshold=0.60, low_threshold=0.45
    )
    alt_routes = generate_alternate_routes(
        G_built, congested, occupancy, max_cutoff=3, top_k=2
    )
    packets, variables = generate_packets(
        congested, norm_loads, norm_caps, alt_routes,
        target=0.50, packet_size=150.0, max_packets=10
    )
    qubo_problem = build_qubo(
        variables, norm_caps, occupancy, target=0.50, packet_size=150.0
    )

    init_occs = [norm_loads[e] / norm_caps[e] for e in norm_caps]
    init_peak = max(init_occs) * 100.0
    init_std  = float(np.std(init_occs)) * 100.0

    result = {
        "scenario_name": scenario["name"],
        "pattern_type":  scenario["pattern_type"],
        "n_variables":   len(variables),
        "init_peak":     round(init_peak, 2),
        "init_std":      round(init_std, 2),
        "qaoa": {},
        "pso":  {},
    }

    # ── QAOA: p=1 and p=2 ────────────────────────────────────────────
    for reps in QAOA_REPS_LIST:
        label = f"p{reps}"
        t0  = time.perf_counter()
        sol = solve_qaoa(
            qubo_problem,
            packets=packets,
            capacities=norm_caps,
            initial_loads=norm_loads,
            packet_size=150.0,
            reps=reps,
            maxiter=QAOA_MAXITER,
        )
        runtime_ms = (time.perf_counter() - t0) * 1000.0

        pk, sd = peak_and_std(sol["bitstring"], packets, norm_caps, norm_loads)
        red     = (init_peak - pk) / init_peak * 100.0 if init_peak > 0 else 0.0

        result["qaoa"][label] = {
            "peak":       round(pk, 2),
            "std":        round(sd, 2),
            "reduction":  round(red, 2),
            "qubo_cost":  round(sol["best_cost"], 4),
            "runtime_ms": round(runtime_ms, 2),
            "bitstring":  list(sol["bitstring"]),
        }

    # ── PSO: N_PSO_TRIALS independent seeds ──────────────────────────
    t_graph = TrafficGraph()
    t_graph.nodes      = {n: Node(id=n, label=n, initial_cycle_time=60.0) for n in G_built.nodes()}
    t_graph.edges      = []
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

    pso_peaks, pso_reds, pso_costs, pso_times = [], [], [], []

    for seed in PSO_SEEDS:
        pso = PSO(n_particles=PSO_PARTICLES, max_iter=PSO_MAXITER, seed=seed)
        t0      = time.perf_counter()
        pso_res = pso.optimize(
            t_graph,
            initial_congestion=dir_loads,
            initial_cycle_times={n: 60.0 for n in G_built.nodes()},
        )
        runtime_ms = (time.perf_counter() - t0) * 1000.0

        gbest = pso_res.get("gbest_bitstring", ())
        if gbest:
            pk, _ = peak_and_std(gbest, packets, norm_caps, norm_loads)
            cost  = eval_qubo_cost(qubo_problem, gbest)
        else:
            pk, cost = init_peak, qubo_problem["constant"]

        red = (init_peak - pk) / init_peak * 100.0 if init_peak > 0 else 0.0
        pso_peaks.append(pk)
        pso_reds.append(red)
        pso_costs.append(cost)
        pso_times.append(runtime_ms)

    std_peak_val = float(np.std(pso_peaks, ddof=1)) if len(pso_peaks) > 1 else 0.0
    std_rt_val   = float(np.std(pso_times, ddof=1)) if len(pso_times) > 1 else 0.0

    result["pso"] = {
        "peaks":        [round(x, 2) for x in pso_peaks],
        "mean_peak":    round(float(np.mean(pso_peaks)), 2),
        "std_peak":     round(std_peak_val, 2),
        "best_peak":    round(float(np.min(pso_peaks)), 2),
        "mean_red":     round(float(np.mean(pso_reds)), 2),
        "best_red":     round(float(np.max(pso_reds)), 2),
        "mean_qubo":    round(float(np.mean(pso_costs)), 4),
        "best_qubo":    round(float(np.min(pso_costs)), 4),
        "mean_runtime": round(float(np.mean(pso_times)), 2),
        "std_runtime":  round(std_rt_val, 2),
        "seeds":        PSO_SEEDS,
    }

    # Divergence: does QAOA p=1 significantly differ from PSO best?
    delta = abs(result["qaoa"]["p1"]["peak"] - result["pso"]["best_peak"])
    result["divergence"] = {
        "qaoa_p1_vs_pso_best_delta": round(delta, 2),
        "significant": delta > 1.0,
    }

    return result


# ─────────────────────────────────────────────
# Console Printing
# ─────────────────────────────────────────────

def print_table(top_name: str, results: List[Dict]):
    sep = "=" * 125
    print(f"\n{sep}")
    print(f"  {top_name.upper()}  |  QAOA p=1 & p=2 (maxiter={QAOA_MAXITER})  |  "
          f"PSO {N_PSO_TRIALS} seeds x {PSO_PARTICLES} particles x {PSO_MAXITER} iters")
    print(sep)
    print(f"{'#':<3} {'Scenario':<42} {'N':<3} {'Init%':<7} "
          f"{'QAOAp1%':<9} {'QAOAp2%':<9} {'PSO-Best%':<11} "
          f"{'PSO-Mean±σ':<15} {'Div?'}")
    print("-" * 125)

    for i, r in enumerate(results, 1):
        q1  = r["qaoa"]["p1"]["peak"]
        q2  = r["qaoa"]["p2"]["peak"]
        pb  = r["pso"]["best_peak"]
        pm  = r["pso"]["mean_peak"]
        ps  = r["pso"]["std_peak"]
        div = "YES!" if r["divergence"]["significant"] else "no"
        print(f"{i:<3} {r['scenario_name']:<42} {r['n_variables']:<3} "
              f"{r['init_peak']:<6.1f}% "
              f"{q1:<8.1f}% {q2:<8.1f}% {pb:<10.1f}% "
              f"{pm:.1f}±{ps:.1f}%        {div}")

    q1_pk = [r["qaoa"]["p1"]["peak"] for r in results]
    q2_pk = [r["qaoa"]["p2"]["peak"] for r in results]
    pb_pk = [r["pso"]["best_peak"]   for r in results]
    pm_pk = [r["pso"]["mean_peak"]   for r in results]
    q1_rt = [r["qaoa"]["p1"]["runtime_ms"] for r in results]
    q2_rt = [r["qaoa"]["p2"]["runtime_ms"] for r in results]
    ps_rt = [r["pso"]["mean_runtime"]      for r in results]
    ndiv  = sum(1 for r in results if r["divergence"]["significant"])

    print(f"\n{'─'*125}")
    print(f"  {'Metric':<38} {'QAOA p=1':<16} {'QAOA p=2':<16} {'PSO Best':<16} {'PSO Mean'}")
    print(f"  {'─'*90}")
    print(f"  {'Avg Peak Occupancy (%)':<38} {np.mean(q1_pk):<16.2f} {np.mean(q2_pk):<16.2f} "
          f"{np.mean(pb_pk):<16.2f} {np.mean(pm_pk):.2f}")
    print(f"  {'Avg Runtime (ms)':<38} {np.mean(q1_rt):<16.1f} {np.mean(q2_rt):<16.1f} "
          f"{np.mean(ps_rt):<16.1f} (same)")
    print(f"  Scenarios with >1% QAOA-p1 vs PSO-Best divergence: {ndiv}/{len(results)}")
    print()


# ─────────────────────────────────────────────
# Figures
# ─────────────────────────────────────────────

def plot_peak_comparison(top_results: Dict[str, List], out_path: str):
    fig, axes = plt.subplots(1, 3, figsize=(21, 6), sharey=False)
    fig.suptitle(
        "Peak Occupancy After Optimization: QAOA (p=1, p=2) vs PSO (5 Independent Seeds)\n"
        "Lower = Better",
        fontsize=14, fontweight='bold', y=1.01
    )
    for ax, (top_name, results) in zip(axes, top_results.items()):
        x       = np.arange(len(results))
        lbls    = [r["scenario_name"].split(".")[0] for r in results]
        q1_pk   = [r["qaoa"]["p1"]["peak"] for r in results]
        q2_pk   = [r["qaoa"]["p2"]["peak"] for r in results]
        pb_pk   = [r["pso"]["best_peak"]   for r in results]
        pm_pk   = [r["pso"]["mean_peak"]   for r in results]
        ps_std  = [r["pso"]["std_peak"]    for r in results]
        init_pk = [r["init_peak"]          for r in results]

        w = 0.2
        ax.bar(x - 1.5*w, q1_pk, w, label="QAOA p=1", color=PALETTE["qaoa_p1"], alpha=0.88, edgecolor="white")
        ax.bar(x - 0.5*w, q2_pk, w, label="QAOA p=2", color=PALETTE["qaoa_p2"], alpha=0.88, edgecolor="white")
        ax.bar(x + 0.5*w, pb_pk, w, label="PSO Best",  color=PALETTE["pso_best"], alpha=0.88, edgecolor="white")
        ax.errorbar(x + 1.5*w, pm_pk, yerr=ps_std, fmt='o',
                    color=PALETTE["pso_mean"], ecolor='#0277bd', capsize=3,
                    markersize=5, linewidth=1.3, label="PSO Mean±σ")
        ax.plot(x, init_pk, '--', color='#90a4ae', linewidth=1.2, label="Initial", alpha=0.7)

        ax.set_title(top_name, fontsize=11, fontweight='bold', pad=8)
        ax.set_xlabel("Scenario #", fontsize=10)
        ax.set_ylabel("Peak Occupancy (%)", fontsize=10)
        ax.set_xticks(x); ax.set_xticklabels(lbls, fontsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[INFO] Peak comparison saved: {os.path.abspath(out_path)}")


def plot_qubo_cost(top_results: Dict[str, List], out_path: str):
    fig, axes = plt.subplots(1, 3, figsize=(21, 6))
    fig.suptitle(
        "QUBO Objective Cost H_B(b) Achieved: QAOA vs PSO\n"
        "Lower = Better (Both Minimize the Same Quadratic Program)",
        fontsize=14, fontweight='bold', y=1.01
    )
    for ax, (top_name, results) in zip(axes, top_results.items()):
        active = [r for r in results if r["n_variables"] > 0]
        if not active:
            ax.text(0.5, 0.5, "No congestion detected", ha='center', va='center',
                    transform=ax.transAxes, color='gray')
            ax.set_title(top_name, fontsize=11, fontweight='bold')
            continue

        x       = np.arange(len(active))
        lbls    = [r["scenario_name"].split(".")[0] for r in active]
        q1_c    = [r["qaoa"]["p1"]["qubo_cost"] for r in active]
        q2_c    = [r["qaoa"]["p2"]["qubo_cost"] for r in active]
        pb_c    = [r["pso"]["best_qubo"]         for r in active]
        pm_c    = [r["pso"]["mean_qubo"]          for r in active]

        w = 0.22
        ax.bar(x - 1.5*w, q1_c, w, label="QAOA p=1", color=PALETTE["qaoa_p1"], alpha=0.88, edgecolor="white")
        ax.bar(x - 0.5*w, q2_c, w, label="QAOA p=2", color=PALETTE["qaoa_p2"], alpha=0.88, edgecolor="white")
        ax.bar(x + 0.5*w, pb_c, w, label="PSO Best",  color=PALETTE["pso_best"], alpha=0.88, edgecolor="white")
        ax.scatter(x + 1.5*w, pm_c, marker='D', color=PALETTE["pso_mean"], s=45, zorder=5, label="PSO Mean")

        ax.set_title(top_name, fontsize=11, fontweight='bold', pad=8)
        ax.set_xlabel("Scenario # (congested only)", fontsize=10)
        ax.set_ylabel("QUBO Cost H_B(b)", fontsize=10)
        ax.set_xticks(x); ax.set_xticklabels(lbls, fontsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[INFO] QUBO cost chart saved: {os.path.abspath(out_path)}")


def plot_runtime(top_results: Dict[str, List], out_path: str):
    names   = list(top_results.keys())
    q1_rt   = [np.mean([r["qaoa"]["p1"]["runtime_ms"] for r in v]) for v in top_results.values()]
    q2_rt   = [np.mean([r["qaoa"]["p2"]["runtime_ms"] for r in v]) for v in top_results.values()]
    ps_rt   = [np.mean([r["pso"]["mean_runtime"]       for r in v]) for v in top_results.values()]
    ps_std  = [np.mean([r["pso"]["std_runtime"]        for r in v]) for v in top_results.values()]

    x, w = np.arange(len(names)), 0.26
    fig, ax = plt.subplots(figsize=(10, 6))
    b1 = ax.bar(x - w,   q1_rt, w, label="QAOA p=1",  color=PALETTE["qaoa_p1"],  alpha=0.88, edgecolor="white")
    b2 = ax.bar(x,       q2_rt, w, label="QAOA p=2",  color=PALETTE["qaoa_p2"],  alpha=0.88, edgecolor="white")
    b3 = ax.bar(x + w,   ps_rt, w, label=f"PSO ({N_PSO_TRIALS} seeds avg)",
                color=PALETTE["pso_best"], alpha=0.88, edgecolor="white")
    ax.errorbar(x + w, ps_rt, yerr=ps_std, fmt='none', color='black', capsize=4, linewidth=1.2)

    for bar in [*b1, *b2, *b3]:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 3, f"{h:.0f}",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_title(f"Wall-Clock Runtime: QAOA (p=1 & p=2) vs PSO ({N_PSO_TRIALS} Seeds)\n"
                 f"Average across 15 scenarios per topology",
                 fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Network Topology", fontsize=11)
    ax.set_ylabel("Runtime (ms)", fontsize=11)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend(fontsize=10)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[INFO] Runtime chart saved: {os.path.abspath(out_path)}")


# ─────────────────────────────────────────────
# LaTeX Table
# ─────────────────────────────────────────────

def export_latex(top_results: Dict[str, List], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("% Rigorous QAOA vs PSO Comparison — Auto-generated by run_rigorous_comparison.py\n")
        f.write("\\begin{table*}[htbp]\n\\centering\n")
        f.write(
            f"\\caption{{Rigorous Comparison: QAOA ($p=1,2$, COBYLA maxiter={QAOA_MAXITER}) vs BPSO "
            f"({N_PSO_TRIALS} independent seeds, {PSO_PARTICLES} particles, {PSO_MAXITER} iters) "
            f"on 45 canonical traffic scenarios. "
            f"Peak occupancy (\\%) after optimization. $\\dagger$ = $>$1\\% QAOA--PSO divergence.}}\n"
        )
        f.write("\\label{tab:rigorous_comparison}\n")
        f.write("\\begin{tabular}{llrrrrrrr}\n\\hline\\hline\n")
        f.write(
            "Topology & Scenario & $N$ & Baseline & "
            "QAOA$_{p=1}$ & QAOA$_{p=2}$ & PSO Best & PSO Mean$\\pm\\sigma$ & $\\Delta$ \\\\\n"
        )
        f.write("& & & (\\%) & (\\%) & (\\%) & (\\%) & (\\%) & (pp) \\\\\n\\hline\n")

        for top_name, results in top_results.items():
            for i, r in enumerate(results):
                sc   = r["scenario_name"].replace("&", "\\&")
                tn   = top_name if i == 0 else ""
                dag  = "$^{\\dagger}$" if r["divergence"]["significant"] else ""
                f.write(
                    f"{tn} & {sc} & {r['n_variables']} & {r['init_peak']:.1f} & "
                    f"{r['qaoa']['p1']['peak']:.1f} & {r['qaoa']['p2']['peak']:.1f} & "
                    f"{r['pso']['best_peak']:.1f} & "
                    f"{r['pso']['mean_peak']:.1f}$\\pm${r['pso']['std_peak']:.1f} & "
                    f"{r['divergence']['qaoa_p1_vs_pso_best_delta']:.1f}{dag} \\\\\n"
                )
            f.write("\\hline\n")

        f.write("\\hline\n\\end{tabular}\n\\end{table*}\n")

    print(f"[INFO] LaTeX table saved: {os.path.abspath(out_path)}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def run_rigorous_comparison():
    topologies = [
        ("4-Node Mesh", nx.complete_graph(["A", "B", "C", "D"])),
        ("5-Node Mesh", nx.complete_graph(["A", "B", "C", "D", "E"])),
        ("6-Node Mesh", nx.complete_graph(["A", "B", "C", "D", "E", "F"])),
    ]

    all_results: Dict[str, List] = {}
    t0_total = time.time()

    for top_name, G in topologies:
        print(f"\n[INFO] {top_name} | generating {SCENARIO_SEED}-seed scenarios ...")
        scenarios = generate_15_diverse_publication_scenarios(
            list(G.nodes()), G, seed=SCENARIO_SEED
        )
        top_res: List[Dict] = []

        for i, sc in enumerate(scenarios, 1):
            print(f"  [{top_name}] Scenario {i:02d}/15: {sc['name']} ...", flush=True)
            res = evaluate_scenario(top_name, G, sc)
            top_res.append(res)

            q1 = res["qaoa"]["p1"]
            q2 = res["qaoa"]["p2"]
            print(
                f"           QAOA p1={q1['peak']:.1f}% ({q1['runtime_ms']:.0f}ms) | "
                f"QAOA p2={q2['peak']:.1f}% ({q2['runtime_ms']:.0f}ms) | "
                f"PSO best={res['pso']['best_peak']:.1f}% | "
                f"Div={res['divergence']['significant']}"
            )

        all_results[top_name] = top_res
        print_table(top_name, top_res)

    # Divergence summary
    total_div = sum(
        sum(1 for r in v if r["divergence"]["significant"])
        for v in all_results.values()
    )
    total_sc = sum(len(v) for v in all_results.values())
    print(f"\n{'='*80}")
    print(f"  FINAL: {total_div}/{total_sc} scenarios showed >1% QAOA-p1 vs PSO-Best divergence")
    print(f"{'='*80}\n")

    # Save JSON
    json_path = os.path.join(OUTPUT_DIR, "rigorous_comparison_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"[INFO] JSON saved: {os.path.abspath(json_path)}")

    # Charts
    plot_peak_comparison(all_results, os.path.join(OUTPUT_DIR, "rigorous_comparison_peaks.png"))
    plot_qubo_cost(all_results,       os.path.join(OUTPUT_DIR, "rigorous_comparison_qubo.png"))
    plot_runtime(all_results,         os.path.join(OUTPUT_DIR, "rigorous_comparison_runtime.png"))

    # LaTeX
    export_latex(all_results, os.path.join(OUTPUT_DIR, "rigorous_comparison_table.tex"))

    elapsed = time.time() - t0_total
    print(f"\n[SUCCESS] Complete in {elapsed:.1f}s ({elapsed/60:.1f} min).")
    return all_results


if __name__ == "__main__":
    run_rigorous_comparison()
