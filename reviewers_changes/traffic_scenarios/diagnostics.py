"""Exact-only packet-budget and allocation-order diagnostics on fixed traffic."""
import argparse
import json
from pathlib import Path

from .experiment import (DEFAULT_CONFIG, ROOT, dump, enumerate_exact, prepare,
                         scenarios, serialize_scenario, write_csv)


def run(output):
    chosen = {"legacy_n4_05", "legacy_n4_11", "legacy_n4_14", "legacy_n6_11"}
    records, details = [], []
    for sc in scenarios():
        if sc["id"] not in chosen:
            continue
        initial = 100 * max(sc["loads"][e]/c for e, c in sc["capacities"].items())
        for cap in (6, 10, 12):
            for order in ("original", "reversed"):
                variant = {**sc, "capacities": dict(list(sc["capacities"].items())[
                           ::-1 if order == "reversed" else 1])}
                problem = prepare(variant, DEFAULT_CONFIG, packet_cap=cap)
                exact = enumerate_exact(problem, DEFAULT_CONFIG)
                row = dict(scenario_id=sc["id"], n_nodes=sc["n_nodes"], packet_cap=cap,
                    allocation_order=order, initial_peak_pct=initial, n_qubits=len(problem["packets"]),
                    requested_packets=sum(a["requested_packets"] for a in problem["allocation"]),
                    omitted_packets=sum(a["unallocated_packets"] for a in problem["allocation"]),
                    min_j_peak_pct=exact["min_j_peak_pct"], min_peak_pct=exact["min_peak_pct"],
                    min_j_cost=exact["min_j_cost"], n_states=exact["n_states"],
                    all_candidates_worsen=exact["min_peak_pct"] > initial + 1e-8,
                    instance_hash=problem["instance_hash"],
                    max_qubo_physical_error=exact["max_qubo_physical_error"])
                records.append(row)
                details.append(dict(**row, allocation=problem["allocation"],
                                    edge_order=problem["edge_order"], exact=exact))
        print(f"Exact cap/order diagnostics complete: {sc['id']}", flush=True)
    write_csv(output / "budget_order_diagnostics.csv", records)
    dump(output / "budget_order_diagnostics.json", details)
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reviewers_changes/yash_traffic_evaluation/results")
    run(parser.parse_args().output)
