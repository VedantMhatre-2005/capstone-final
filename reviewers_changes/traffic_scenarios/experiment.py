r"""Paired scenario benchmark using the repository's existing two-detour model.

Run from repository root:
  .venv\Scripts\python.exe -m reviewers_changes.traffic_scenarios.experiment
Outputs are isolated from the manuscript's existing experiment artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "optimization_algorithms/capstone-optimization/backend"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv/matplotlib_cache"))
sys.path.insert(0, str(BACKEND))
from final_qaoa_with_signal import (  # noqa: E402
    apply_solution, build_network, build_qubo, detect_congestion,
    generate_alternate_routes, generate_packets, normalize_edge,
)
from pso import Particle  # noqa: E402
from run_publication_45_scenarios import generate_15_diverse_publication_scenarios  # noqa: E402

TOL = 1e-8
DEFAULT_CONFIG = {
    "encoding": "repository_two_detours_mandatory_rerouting",
    "threshold": 0.60, "target": 0.50, "packet_size_veh_hr": 150.0,
    "packet_cap": 10, "route_cutoff_hops": 3, "top_k_routes": 2,
    "scenario_seed": 2026, "solver_seeds": [42, 123, 456, 789, 2026],
    "qaoa_reps": 1, "qaoa_maxiter": 50, "qaoa_tol": 1e-4,
    "qaoa_shots": 1024, "qaoa_backend": "qiskit.primitives.StatevectorSampler",
    "qaoa_transpilation": "optimization_level=0; basis h,rx,rz,cx; seed_transpiler=42",
    "qaoa_initialization": "beta in [0,pi], gamma in [0,2*pi], independently seeded",
    "bpso_particles": 30, "bpso_iterations": 20, "bpso_w": 0.5,
    "bpso_c1": 1.5, "bpso_c2": 1.5,
    "exact_tie_break": "minimum J then minimum peak then lexicographic bits",
    "outcome_tolerance_pp": TOL,
}


def jsonable(value):
    if isinstance(value, dict):
        return {("--".join(k) if isinstance(k, tuple) else str(k)): jsonable(v)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(value), indent=2, allow_nan=False), encoding="utf-8")


def digest(value):
    return hashlib.sha256(json.dumps(jsonable(value), sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(jsonable(v), separators=(",", ":"))
                             if isinstance(v, (list, dict, tuple)) else v
                             for k, v in row.items()})


def scenarios():
    """45 unchanged legacy + 72 controlled + two route-availability diagnostics."""
    result = []
    for n in (4, 5, 6):
        graph = nx.complete_graph(list("ABCDEF"[:n]))
        for i, old in enumerate(generate_15_diverse_publication_scenarios(
                list(graph), graph, seed=2026), 1):
            result.append(dict(id=f"legacy_n{n}_{i:02}", suite="legacy", n_nodes=n,
                               graph=graph, family=old["pattern_type"], level=str(i),
                               name=old["name"], capacities=old["capacities"],
                               loads=old["loads"], parameters={"legacy_index": i,
                               "bottleneck_edges": old["bottleneck_edges"],
                               "scenario_seed": 2026}))
        edges = list(graph.edges())
        base_cap = {e: float((2400, 2000, 1800, 1600)[i % 4]) for i, e in enumerate(edges)}
        first, adjacent, separated = ("A", "B"), ("A", "C"), ("C", "D")
        for family, levels in (
            ("off_peak", (0.20, 0.30, 0.40)),
            ("threshold", (0.59, 0.60, 0.61)),
            ("single_bottleneck", (0.65, 0.80, 0.95)),
            ("adjacent_bottlenecks", (0.65, 0.80, 0.95)),
            ("separated_bottlenecks", (0.65, 0.80, 0.95)),
            ("distributed_peak", (0.30, 0.50, 0.70)),
            ("lane_closure", (1.0, 0.75, 0.50)),
            ("weather_capacity_loss", (1.0, 0.80, 0.60)),
        ):
            for li, level in enumerate(levels, 1):
                caps = base_cap.copy()
                loads = {e: 0.30 * c for e, c in base_cap.items()}
                params = {"base_capacities": base_cap, "background_ratio": 0.30,
                          "varied_parameter": "bottleneck_ratio", "value": level}
                hot = [first]
                if family == "off_peak":
                    loads = {e: level * c for e, c in base_cap.items()}
                    params["varied_parameter"] = "all_edge_ratio"
                elif family == "distributed_peak":
                    hot = [first, adjacent, ("A", "D")]
                    loads = {e: level * c for e, c in base_cap.items()}
                    for e in hot:
                        loads[e] = 0.85 * base_cap[e]
                    params.update(varied_parameter="background_ratio", background_ratio=level,
                                  fixed_bottleneck_ratio=0.85)
                elif family in ("lane_closure", "weather_capacity_loss"):
                    # Demand remains identical across the capacity-loss sweep.
                    loads = {e: 0.55 * c for e, c in base_cap.items()}
                    hot = [first] if family == "lane_closure" else edges
                    for e in hot:
                        caps[e] *= level
                    params.update(varied_parameter="capacity_multiplier", background_ratio=0.55,
                                  fixed_demand=True)
                else:
                    if family == "adjacent_bottlenecks":
                        hot.append(adjacent)
                    elif family == "separated_bottlenecks":
                        hot.append(separated)
                    for e in hot:
                        loads[e] = level * base_cap[e]
                params["affected_edges"] = hot
                result.append(dict(id=f"controlled_n{n}_{family}_{li}", suite="controlled",
                                   n_nodes=n, graph=graph, family=family, level=level,
                                   name=f"{family.replace('_', ' ')} ({level:g})",
                                   capacities=caps, loads=loads, parameters=params))
    for name, graph in (("one_detour", nx.cycle_graph(list("ABCD"))),
                        ("no_detour", nx.path_graph(list("ABCD")))):
        caps = {normalize_edge(*e): 2000.0 for e in graph.edges()}
        loads = {e: (1600.0 if e == ("A", "B") else 600.0) for e in caps}
        result.append(dict(id=f"diagnostic_{name}", suite="route_diagnostic", n_nodes=4,
                           graph=graph, family=name, level=1, name=name.replace('_', ' '),
                           capacities=caps, loads=loads, parameters={"overloaded_edge": ["A", "B"]}))
    return result


def serialize_scenario(sc):
    return {**{k: v for k, v in sc.items() if k != "graph"},
            "nodes": list(sc["graph"]), "edges": list(sc["graph"].edges())}


def prepare(sc, config, packet_cap=None):
    cap_limit = config["packet_cap"] if packet_cap is None else packet_cap
    graph, caps, loads = build_network(sc["graph"], sc["capacities"], sc["loads"])
    assert set(caps) == set(loads) == {normalize_edge(*e) for e in graph.edges()}
    assert all(c > 0 for c in caps.values()) and all(v >= 0 for v in loads.values())
    occ, congested, _ = detect_congestion(caps, loads, high_threshold=config["threshold"])
    routes = generate_alternate_routes(graph, congested, occ,
                                       max_cutoff=config["route_cutoff_hops"], top_k=2)
    packets, variables = generate_packets(congested, loads, caps, routes,
        target=config["target"], packet_size=config["packet_size_veh_hr"], max_packets=cap_limit)
    qubo = build_qubo(variables, caps, occ, target=config["target"],
                      packet_size=config["packet_size_veh_hr"])
    requested = {e: math.ceil((loads[e] - config["target"] * caps[e]) /
                              config["packet_size_veh_hr"]) for e in congested}
    allocated = Counter(p["origin"] for p in packets)
    audit = [{"origin": e, "requested_packets": requested[e],
              "allocated_packets": allocated[e], "candidate_detours": len(routes[e]),
              "unallocated_packets": requested[e] - allocated[e],
              "reason": ("insufficient_detours" if len(routes[e]) != 2 else
                         "packet_cap" if allocated[e] < requested[e] else "allocated")}
             for e in congested]
    for packet in packets:
        assert len(packet["routes"]) == 2
        for path in packet["routes"]:
            assert (path[0], path[-1]) == packet["origin"]
            assert len(path) - 1 <= config["route_cutoff_hops"]
            assert all(graph.has_edge(a, b) for a, b in zip(path, path[1:]))
            assert list(path) != list(packet["origin"])
    problem = dict(capacities=caps, loads=loads, packets=packets, qubo=qubo,
                   routes=routes, allocation=audit, packet_cap=cap_limit,
                   edge_order=list(caps), graph=graph,
                   status=("no_congestion" if not congested else
                           "no_eligible_routes" if not packets else "ready"))
    problem["qubo_hash"] = digest({"variables": variables, "qubo": qubo})
    problem["instance_hash"] = digest({k: v for k, v in problem.items() if k != "graph"})
    return problem


def cost(qubo, bits):
    names = [v["name"] for v in qubo["variables"]]
    return float(qubo["constant"] + sum(qubo["linear"].get(n, 0) * bits[i]
        for i, n in enumerate(names)) + sum(value * bits[names.index(a)] * bits[names.index(b)]
        for (a, b), value in qubo["quadratic"].items()))


def metrics(problem, loads):
    ratios = np.array([loads[e] / c for e, c in problem["capacities"].items()])
    initial = max(problem["loads"][e] / c for e, c in problem["capacities"].items()) * 100
    peak = float(ratios.max() * 100)
    return dict(initial_peak_pct=initial, final_peak_pct=peak,
        peak_reduction_relative_pct=100 * (initial - peak) / initial if initial > 0 else None,
        peak_relief_pp=initial - peak, mean_ratio=float(ratios.mean()),
        std_ratio=float(ratios.std()), n_congested_after=int(np.sum(ratios > .60 + 1e-12)),
        n_over_capacity_after=int(np.sum(ratios > 1 + 1e-12)),
        minimum_load_veh_hr=min(loads.values()))


def enumerate_exact(problem, config):
    """Independent physical-objective check over EVERY represented bitstring."""
    start = time.perf_counter()
    n = len(problem["packets"])
    states = list(itertools.product((0, 1), repeat=n))
    energies, peaks = [], []
    weights = {e: 1 + 2 * problem["loads"][e] / c +
               np.mean(list(problem["capacities"].values())) / c
               for e, c in problem["capacities"].items()}
    max_error = 0.0
    for bits in states:
        updated = apply_solution(problem["packets"], bits, problem["loads"],
                                 packet_size=config["packet_size_veh_hr"])
        assert min(updated.values()) >= -1e-8, "Negative load after route decoding"
        energy = cost(problem["qubo"], bits)
        physical = sum(weights[e] * (updated[e] / c - config["target"]) ** 2
                       for e, c in problem["capacities"].items())
        error = abs(energy - physical)
        max_error = max(max_error, error)
        assert error < 1e-8, f"QUBO/physical objective mismatch {error}"
        energies.append(energy)
        peaks.append(max(updated[e] / c for e, c in problem["capacities"].items()) * 100)
    minimum = min(energies)
    ground = [i for i, value in enumerate(energies) if abs(value - minimum) <= 1e-10]
    best_j = min(ground, key=lambda i: (peaks[i], states[i]))
    best_peak = min(range(len(states)), key=lambda i: (peaks[i], energies[i], states[i]))
    return dict(min_j_cost=minimum, min_j_bits=states[best_j],
                min_j_peak_pct=peaks[best_j], max_ground_state_peak_pct=max(peaks[i] for i in ground),
                min_peak_pct=peaks[best_peak], min_peak_bits=states[best_peak],
                min_peak_j_cost=energies[best_peak], n_ground_states=len(ground),
                n_states=len(states), max_qubo_physical_error=max_error,
                enumeration_and_validation_ms=(time.perf_counter() - start) * 1000)


def solve_bpso(problem, seed, config):
    """Repository Particle dynamics applied directly to the frozen shared QUBO."""
    rng = np.random.default_rng(seed)
    particles = [Particle(len(problem["packets"]), rng) for _ in range(config["bpso_particles"])]
    best_cost, best_bits, best_position = float("inf"), None, None
    evaluations = 0
    start = time.perf_counter()
    for particle in particles:
        bits = particle.to_bitstring()
        value = cost(problem["qubo"], bits)
        evaluations += 1
        particle.best_fitness = value
        particle.best_position = particle.position.copy()
        particle.best_bitstring = bits
        if value < best_cost:
            best_cost, best_bits, best_position = value, bits, particle.position.copy()
    for _ in range(config["bpso_iterations"]):
        for particle in particles:
            particle.update_velocity(best_position, config["bpso_w"], config["bpso_c1"],
                                     config["bpso_c2"], rng)
            particle.update_position()
            bits = particle.to_bitstring()
            value = cost(problem["qubo"], bits)
            evaluations += 1
            if value < particle.best_fitness:
                particle.best_fitness, particle.best_bitstring = value, bits
                particle.best_position = particle.position.copy()
            if value < best_cost:
                best_cost, best_bits, best_position = value, bits, particle.position.copy()
    return dict(bits=best_bits, cost=best_cost, evaluations=evaluations,
                solve_ms=(time.perf_counter() - start) * 1000,
                backend="repository_particle_dynamics_on_frozen_qubo")


def solve_qiskit(problem, seed, config):
    from qiskit.primitives import StatevectorSampler
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    qp = QuadraticProgram("yash_frozen_traffic_instance")
    for v in problem["qubo"]["variables"]:
        qp.binary_var(v["name"])
    qp.minimize(constant=problem["qubo"]["constant"], linear=problem["qubo"]["linear"],
                quadratic=problem["qubo"]["quadratic"])
    rng = np.random.default_rng(seed)
    initial_point = [float(rng.uniform(0, math.pi)), float(rng.uniform(0, 2 * math.pi))]
    history = []
    def callback(evaluation, parameters, mean, metadata):
        history.append({"evaluation": int(evaluation), "parameters": list(parameters),
                        "expectation": float(np.real(mean))})
    qaoa = QAOA(sampler=StatevectorSampler(default_shots=config["qaoa_shots"], seed=seed),
        optimizer=COBYLA(maxiter=config["qaoa_maxiter"], tol=config["qaoa_tol"]),
        reps=config["qaoa_reps"], initial_point=initial_point, callback=callback,
        transpiler=generate_preset_pass_manager(optimization_level=0,
            basis_gates=["h", "rx", "rz", "cx"], seed_transpiler=42))
    start = time.perf_counter()
    answer = MinimumEigenOptimizer(qaoa).solve(qp)
    elapsed = (time.perf_counter() - start) * 1000
    if answer.status.name != "SUCCESS":
        raise RuntimeError(f"Qiskit optimization status: {answer.status}")
    bits = tuple(int(round(x)) for x in answer.x)
    assert len(bits) == len(problem["packets"])
    assert abs(cost(problem["qubo"], bits) - float(answer.fval)) < 1e-8
    return dict(bits=bits, cost=float(answer.fval), solve_ms=elapsed,
                initial_point=initial_point, evaluations=len(history), history=history,
                backend=config["qaoa_backend"])


def evaluate(sc, problem, exact, method, seed, config):
    row = dict(scenario_id=sc["id"], suite=sc["suite"], n_nodes=sc["n_nodes"],
        family=sc["family"], level=sc["level"], scenario=sc["name"], method=method,
        solver_seed=seed, traffic_seed=2026 if sc["suite"] == "legacy" else None,
        instance_hash=problem["instance_hash"], qubo_hash=problem["qubo_hash"],
        packet_cap=problem["packet_cap"], n_qubits=len(problem["packets"]),
        requested_packets=sum(x["requested_packets"] for x in problem["allocation"]),
        allocated_packets=len(problem["packets"]),
        budget_omitted_packets=sum(x["unallocated_packets"] for x in problem["allocation"]
                                   if x["reason"] == "packet_cap"),
        route_omitted_packets=sum(x["unallocated_packets"] for x in problem["allocation"]
                                  if x["reason"] == "insufficient_detours"),
        exact_min_qubo_cost=exact["min_j_cost"], exact_min_peak_pct=exact["min_peak_pct"],
        exact_min_j_peak_pct=exact["min_j_peak_pct"], n_states=exact["n_states"])
    if method == "Unmanaged":
        row.update(status="baseline", backend="unmanaged_input", bitstring=None,
                   solve_ms=None, qubo_cost=None, moved_packets=0)
        updated = problem["loads"]
        details = {}
    else:
        try:
            if not problem["packets"]:
                solution = dict(bits=(), cost=problem["qubo"]["constant"], solve_ms=0.0,
                                backend="not_invoked", evaluations=0)
                status = problem["status"]
            elif method == "QAOA":
                solution, status = solve_qiskit(problem, seed, config), "success"
            elif method == "BPSO":
                solution, status = solve_bpso(problem, seed, config), "success"
            else:
                bits = exact["min_j_bits"] if method == "Exact J" else exact["min_peak_bits"]
                solution, status = dict(bits=bits, cost=cost(problem["qubo"], bits), solve_ms=None,
                                        backend="exhaustive_enumeration"), "success"
            updated = apply_solution(problem["packets"], solution["bits"], problem["loads"],
                                     packet_size=config["packet_size_veh_hr"])
            row.update(status=status, backend=solution["backend"], bitstring=solution["bits"],
                       qubo_cost=solution["cost"], solve_ms=solution["solve_ms"],
                       moved_packets=len(problem["packets"]), evaluations=solution.get("evaluations"),
                       initial_point=solution.get("initial_point"),
                       qubo_gap_absolute=max(0.0, solution["cost"] - exact["min_j_cost"]),
                       qubo_gap_relative_pct=(100 * max(0.0, solution["cost"] - exact["min_j_cost"]) /
                           abs(exact["min_j_cost"]) if abs(exact["min_j_cost"]) > 1e-10 else None))
            assert solution["cost"] >= exact["min_j_cost"] - 1e-8
            details = {k: v for k, v in solution.items() if k == "history"}
        except Exception as error:
            row.update(status="solver_failed", error_type=type(error).__name__, error=str(error))
            return row, [], {"error": str(error)}
    row.update(metrics(problem, updated))
    row["outcome_vs_initial"] = ("improved" if row["peak_relief_pp"] > TOL else
                                  "worsened" if row["peak_relief_pp"] < -TOL else "unchanged")
    if method != "Unmanaged":
        row["guarded_final_peak_pct"] = min(row["initial_peak_pct"], row["final_peak_pct"])
        row["guard_rejected"] = row["final_peak_pct"] > row["initial_peak_pct"] + TOL
    edge_rows = [dict(scenario_id=sc["id"], method=method, solver_seed=seed, edge="--".join(e),
        capacity_veh_hr=c, before_load_veh_hr=problem["loads"][e], after_load_veh_hr=updated[e],
        before_ratio=problem["loads"][e]/c, after_ratio=updated[e]/c,
        delta_load_veh_hr=updated[e]-problem["loads"][e]) for e, c in problem["capacities"].items()]
    return row, edge_rows, details


def audit_old_csv():
    source = ROOT / "reviewers_changes/brute_force_comparison_results.csv"
    rows = list(csv.DictReader(source.open(encoding="utf-8")))
    for row in rows:
        for key in ("init_peak", "qaoa_peak", "pso_peak", "bf_peak", "opt_gap_pct"):
            row[key] = float(row[key])
        row["qaoa_relief_pp"] = row["init_peak"] - row["qaoa_peak"]
        row["qaoa_minus_bpso_pp"] = row["qaoa_peak"] - row["pso_peak"]
    return rows


def provenance(config):
    tracked = [BACKEND / name for name in ("final_qaoa_with_signal.py", "pso.py", "graph.py",
               "predictions.py", "threshold.py", "run_publication_45_scenarios.py")]
    tracked += [Path(__file__), Path(__file__).parent / "__init__.py"]
    return dict(created_utc=datetime.now(timezone.utc).isoformat(),
                git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                python=sys.version, platform=platform.platform(), config=config,
                dependencies={p: importlib.metadata.version(p) for p in
                              ("numpy", "networkx", "scipy", "matplotlib", "qiskit",
                               "qiskit-algorithms", "qiskit-optimization")},
                source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in tracked},
                old_comparison_sha256=hashlib.sha256((ROOT / "reviewers_changes/brute_force_comparison_results.csv").read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reviewers_changes/yash_traffic_evaluation/results")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_CONFIG["solver_seeds"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--suite", choices=["legacy", "controlled", "route_diagnostic"])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = {**DEFAULT_CONFIG, "solver_seeds": args.seeds}
    selected = [sc for sc in scenarios() if not args.suite or sc["suite"] == args.suite]
    if args.limit:
        selected = selected[:args.limit]
    out = args.output.resolve()
    manifest = [serialize_scenario(sc) for sc in selected]
    if (out / "run_metadata.json").exists():
        if not args.resume:
            raise SystemExit("Output already exists. Choose a new --output or use --resume.")
        prior = json.loads((out / "run_metadata.json").read_text(encoding="utf-8"))
        assert prior["config"] == config, "Cannot resume with changed configuration"
        assert json.loads((out / "scenario_manifest.json").read_text(encoding="utf-8")) == jsonable(manifest)
        now = provenance(config)
        assert prior["source_sha256"] == now["source_sha256"], "Source changed since run began"
        assert prior["dependencies"] == now["dependencies"], "Dependencies changed since run began"
    else:
        dump(out / "run_metadata.json", provenance(config))
        dump(out / "scenario_manifest.json", manifest)
    raw, edges, exact_rows, allocation_rows = [], [], [], []
    started = time.perf_counter()
    for i, sc in enumerate(selected, 1):
        case_path = out / "cases" / f"{sc['id']}.json"
        if case_path.exists() and args.resume:
            case = json.loads(case_path.read_text(encoding="utf-8"))
        else:
            problem = prepare(sc, config)
            exact = enumerate_exact(problem, config)
            rows, edge_records, traces = [], [], {}
            for method, seed in [("Unmanaged", None), ("Exact J", None), ("Exact peak", None)] + [
                    (m, seed) for seed in args.seeds for m in ("BPSO", "QAOA")]:
                row, er, detail = evaluate(sc, problem, exact, method, seed, config)
                rows.append(row)
                edge_records.extend(er)
                if detail:
                    traces[f"{method}_{seed}"] = detail
                if row["status"] == "solver_failed":
                    print(f"FAILED {sc['id']} {method}/{seed}: {row['error']}", flush=True)
            case = dict(scenario=serialize_scenario(sc), problem={k: v for k, v in problem.items() if k != "graph"},
                        exact=exact, results=rows, edges=edge_records, solver_traces=traces)
            dump(case_path, case)
        raw.extend(case["results"])
        edges.extend(case["edges"])
        exact_rows.append(dict(scenario_id=sc["id"], suite=sc["suite"], n_nodes=sc["n_nodes"],
                               family=sc["family"], **case["exact"]))
        allocation_rows.extend(dict(scenario_id=sc["id"], **a) for a in case["problem"]["allocation"])
        print(f"[{i}/{len(selected)}] {sc['id']} N={len(case['problem']['packets'])} "
              f"elapsed={time.perf_counter()-started:.1f}s", flush=True)
        # Persist progress after every case; a failed process never loses completed cases.
        write_csv(out / "raw_results.csv", raw)
    write_csv(out / "edge_results.csv", edges)
    write_csv(out / "exact_references.csv", exact_rows)
    write_csv(out / "packet_allocation.csv", allocation_rows)
    write_csv(out / "existing_csv_audit.csv", audit_old_csv())
    dump(out / "completion.json", dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        scenario_count=len(selected), raw_rows=len(raw), edge_rows=len(edges),
        solver_failed=sum(r["status"] == "solver_failed" for r in raw),
        elapsed_seconds=time.perf_counter()-started))
    print(f"Complete: {out}", flush=True)


if __name__ == "__main__":
    main()
