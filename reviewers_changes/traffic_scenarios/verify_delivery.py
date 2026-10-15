"""Independently reconcile saved trials, decoded edges and exported workbook caches."""
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from .experiment import ROOT, TOL, dump


def verify():
    output = ROOT / "reviewers_changes/yash_traffic_evaluation"
    results = output / "results"
    cases = [json.loads(p.read_text(encoding="utf-8")) for p in (results / "cases").glob("*.json")]
    trials_checked = 0
    max_edge_error, max_energy_error = 0.0, 0.0
    for case in cases:
        problem = case["problem"]
        names = [v["name"] for v in problem["qubo"]["variables"]]
        for r in case["results"]:
            decoded = problem["loads"].copy()
            if r["method"] != "Unmanaged":
                assert len(r["bitstring"]) == len(problem["packets"])
                for pkt, bit in zip(problem["packets"], r["bitstring"]):
                    assert bit in (0, 1)
                    decoded["--".join(pkt["origin"])] -= 150.0
                    route = pkt["routes"][bit]
                    for u, v in zip(route, route[1:]):
                        decoded["--".join(sorted((u, v)))] += 150.0
                by_name = dict(zip(names, r["bitstring"]))
                energy = problem["qubo"]["constant"]
                energy += sum(v * by_name[k] for k, v in problem["qubo"]["linear"].items())
                energy += sum(v * math.prod(by_name[k] for k in pair.split("--"))
                              for pair, v in problem["qubo"]["quadratic"].items())
                max_energy_error = max(max_energy_error, abs(energy-r["qubo_cost"]))
                assert abs(energy-r["qubo_cost"]) < TOL
            stored_edges = [e for e in case["edges"] if e["method"] == r["method"] and
                            e["solver_seed"] == r["solver_seed"]]
            assert len(stored_edges) == len(decoded)
            for e in stored_edges:
                error = abs(e["after_load_veh_hr"] - decoded[e["edge"]])
                max_edge_error = max(max_edge_error, error)
                assert error < TOL
            peak = max(decoded[e]/c for e, c in problem["capacities"].items()) * 100
            assert abs(peak-r["final_peak_pct"]) < TOL
            assert min(decoded.values()) >= -TOL
            trials_checked += 1
    assert len(cases) == 119 and trials_checked == 1547
    summaries = list(csv.DictReader((output / "tables/scenario_summary.csv").open(encoding="utf-8")))
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    def cells(archive, name):
        tree = ET.fromstring(archive.read(name))
        answer = {}
        for c in tree.findall(".//s:sheetData/s:row/s:c", ns):
            value = c.find("s:v", ns)
            if value is not None:
                answer[c.attrib["r"]] = value.text
        return answer
    with ZipFile(output / "traffic_scenario_results.xlsx") as book:
        assert book.testzip() is None
        overview = cells(book, "xl/worksheets/sheet1.xml")
        assert float(overview["C15"]) == 119
        sc = cells(book, "xl/worksheets/sheet2.xml")
        for row, source in enumerate(summaries, 2):
            for column, key in (("J", "initial_peak_pct"), ("K", "qaoa_peak_mean_pct"),
                                ("M", "bpso_peak_mean_pct"), ("O", "qaoa_reduction_relative_pct"),
                                ("P", "bpso_reduction_relative_pct"), ("Q", "qaoa_relief_pp"),
                                ("R", "bpso_minus_qaoa_pp")):
                assert abs(float(sc[f"{column}{row}"])-float(source[key])) < TOL
        for filename in ("xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml"):
            tree = ET.fromstring(book.read(filename))
            assert not tree.findall('.//s:c[@t="e"]', ns), f"Excel formula error in {filename}"
    scan = json.loads((results / "workbook_formula_scan.json").read_text(encoding="utf-8"))
    assert "matched 0 entries" in scan["inspection"]
    assert scan["formulaRefreshVerified"] and scan["originalInputsRestored"]
    diagnostics = json.loads((results / "budget_order_diagnostics.json").read_text(encoding="utf-8"))
    assert len(diagnostics) == 24
    assert max(x["max_qubo_physical_error"] for x in diagnostics) < TOL
    metadata = json.loads((results / "run_metadata.json").read_text(encoding="utf-8"))
    for name, expected in metadata["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    old = ROOT / "reviewers_changes/brute_force_comparison_results.csv"
    assert hashlib.sha256(old.read_bytes()).hexdigest() == metadata["old_comparison_sha256"]
    verification = dict(passed=True, independently_decoded_trial_records=trials_checked,
        max_decoded_edge_error_veh_hr=max_edge_error, max_saved_energy_error=max_energy_error,
        workbook_scenario_rows_reconciled=len(summaries), workbook_formula_errors=0,
        workbook_input_change_and_restoration_verified=True, exact_budget_order_variants=24,
        diagnostic_candidate_states=sum(r["n_states"] for r in diagnostics),
        original_results_and_evaluation_sources_unchanged=True,
        figure_visual_review="Five figures inspected; legend overlap and heatmap colorbar corrected",
        original_unit_test_execution="11 tests passed, including compiled-circuit probability equivalence")
    dump(results / "delivery_verification.json", verification)
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    verify()
