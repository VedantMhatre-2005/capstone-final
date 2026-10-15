# Yash's traffic scenario deliverables

Start with [REPORT.md](REPORT.md), then [CASE_STUDIES.md](CASE_STUDIES.md). Tables are in `tables/`; figures have both PNG and vector PDF formats in `figures/`. The Excel workbook is a measurement snapshot with recalculating peak-relief formulas; it does not rerun quantum or swarm solvers when edited. Manuscript text and a draft reviewer response are provided separately. Existing manuscript and prior result files are unchanged.

## Reproduce from repository root (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r reviewers_changes\traffic_scenarios\requirements-lock.txt
.\.venv\Scripts\python.exe -m unittest reviewers_changes.traffic_scenarios.test_experiment -v
.\.venv\Scripts\python.exe -m reviewers_changes.traffic_scenarios.experiment --output reviewers_changes\yash_traffic_evaluation\new_run
.\.venv\Scripts\python.exe -m reviewers_changes.traffic_scenarios.diagnostics --output reviewers_changes\yash_traffic_evaluation\new_run
.\.venv\Scripts\python.exe -m reviewers_changes.traffic_scenarios.report --results reviewers_changes\yash_traffic_evaluation\new_run --output reviewers_changes\yash_traffic_evaluation\new_report
```

Use a fresh output directory for new runs. `--resume` resumes saved completed cases only when configuration, source hashes, dependencies and scenario inputs match. Solver seeds can be supplied using `--seeds 42 123 456 789 2026`; use the same five seeds to reproduce this package. Scripts checkpoint each case. QAOA exceptions are retained as failures, never silently replaced by a different solver or default bitstring. Timing varies by machine.

`results/run_metadata.json` identifies software, code and input provenance. `results/completion.json` identifies execution completion. `results/verification.json` records integrity checks. Raw CSVs are analytical measurements exported by the Python experiments. All scientific result numbers are derived from those records, not manually entered paper values.

Column definitions and units are in `DATA_DICTIONARY.md`. Document and implementation references are in `SOURCES.md`. The workbook builder is `reviewers_changes/traffic_scenarios/build_workbook.mjs` and uses the Codex bundled Artifact Tool; Python outputs and scientific plots can be regenerated independently of that optional Excel export.

The experiment is optimizer-only and synthetic, with the current two-detour model and at most 10 qubits in the primary suite. Extra exact diagnostics reach a 12-packet cap. IBM hardware, real STQGCN inference and traffic-seed generalization are separate team tasks.
