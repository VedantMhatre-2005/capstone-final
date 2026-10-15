# Draft response to reviewers: Yash's traffic-scenario evaluation

These responses describe completed experiments and delivered replacement text/tables. Insert them into the final response only after the team incorporates the corresponding changes into the manuscript. Final section/page numbers are deliberately not invented.

## Reviewer 3, comment 1: scenario counts

We have rerun the scenario evaluation under an explicitly saved experimental configuration and separated two comparisons: improvement against the initial unmanaged input, and comparison with BPSO on the same traffic state. Across the 45 legacy traffic inputs, the QAOA mean peak improved the unmanaged state in 40 cases, was unchanged in 1, and worsened in 4. Comparing five-seed mean peaks, QAOA was lower than BPSO in 0 cases, tied in 45, and was higher in 0. The replacement scenario tables are generated from the same raw records as these totals. Five-seed mean outcomes are explicitly distinguished from per-trial outcomes and inferential significance.

Evidence: `tables/legacy_45_results.csv`, `tables/topology_summary.csv`, `results/paired_per_seed.csv`. Replacement text: `MANUSCRIPT_SECTION.md`.

## Reviewer 3, comment 2: negative reductions and the universal claim

We report every negative outcome and its paired BPSO value, and withdraw the universal claim that QAOA never has a higher peak than BPSO. The new legacy experiment contains 4 cases whose QAOA mean final peak exceeds the initial peak, and 0 cases whose mean peak exceeds BPSO's. We distinguish solver error from formulation effects using separate minimum-J and minimum-peak exact references. We also clarify that the current implementation forces generated packets onto one of two detours, so an all-zero bitstring is not a no-rerouting action. A separate reject-if-peak-worsens policy is recorded without replacing raw solver outcomes.

Evidence: `tables/negative_cases.csv`, `CASE_STUDIES.md`, and Figure `04_objective_diagnostics`.

## Reviewer 3, comment 3: paired BPSO column

The replacement 45-case table includes dedicated initial, QAOA mean and sample SD, BPSO mean and sample SD, exact-minimum-J peak, and exact-minimum-peak columns. All solvers share the saved instance and QUBO. Full per-seed and edge-level records are provided for verification.

Evidence: `tables/legacy_45_results.csv`, `tables/legacy_tables.tex`, `results/raw_results.csv`, `results/edge_results.csv`.

## Reviewer 3, comment 6: practical significance of small reductions

The replacement discussion distinguishes relative reduction from absolute percentage-point relief and reports whether residual peaks exceed the 60% trigger. Small positive changes are discussed as limited relief when congestion remains. No statistical significance is inferred from a single positive reduction or from five-seed descriptive summaries. Strong, marginal and negative examples include edge-level measurements and packet traces.

Evidence: `CASE_STUDIES.md`, `MANUSCRIPT_SECTION.md`, and `results/edge_results.csv`.

## Reviewer 2, comment 6: exhaustive reference

We enumerated all represented bitstrings and obtained two explicitly distinguished classical references. The minimum-J solution defines the QUBO optimality gap; the minimum-peak solution measures the best attainable peak within the same candidate set. The latter is not mislabeled as a QUBO ground state. Each candidate's algebraic QUBO cost was checked against the direct physical objective. We make no quantum speedup claim on these compact simulated instances.

Evidence: `results/exact_references.csv`, `results/cases/`, `results/verification.json`.

## Team integration still required

Aditya owns the separately measured hardware and trained-model end-to-end pipeline evidence. Sanjay owns broader multi-seed/statistical inference; this package gives him frozen scenarios and five-seed descriptive records. Vedant owns resource scaling; the exact-only budget/order diagnostics are traffic-formulation evidence, not a completed hardware-scaling claim. The final manuscript must not combine incompatible previous result versions with these new measurements.
