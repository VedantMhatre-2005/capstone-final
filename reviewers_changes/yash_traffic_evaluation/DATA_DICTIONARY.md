# Data definitions

CSV files contain UTF-8 headers, one record per row, and numbers without display rounding. Empty fields represent not applicable/unavailable values, not a numerical zero. JSON stores ordered graph edges, routes, variables and complete solver details.

## Files and record units

| File | One row/object represents |
| --- | --- |
| `results/scenario_manifest.json` | One fully specified traffic input with graph, capacities, loads and parameter rules |
| `results/scenario_inputs.csv` | One undirected edge in one traffic input |
| `results/raw_results.csv` | One method on one scenario and, for stochastic methods, one solver seed |
| `results/edge_results.csv` | One edge after one method/seed evaluation |
| `results/paired_per_seed.csv` | A QAOA/BPSO pair on one fixed scenario and solver-seed index |
| `results/exact_references.csv` | Two exhaustive references for one fixed candidate set |
| `results/packet_allocation.csv` | One initially congested origin edge and its requested/allocated packets |
| `results/budget_order_diagnostics.csv` | One exact-only budget/allocation-order variant of a fixed legacy input |
| `tables/scenario_summary.csv` | One scenario, aggregating five fixed-traffic solver repetitions |
| `tables/topology_summary.csv` | One suite, topology size and method, aggregating scenario means |
| `results/existing_csv_audit.csv` | One unchanged historical CSV row plus recalculated comparison fields |
| `results/cases/<scenario_id>.json` | Complete input, frozen QUBO, routes, allocations, exact references, trial records and parameter-optimization traces |

`legacy_45_results.csv` and `controlled_72_results.csv` select the corresponding suites from scenario summaries. `negative_cases.csv` contains scenarios with a worsened QAOA mean initial-to-final peak. Individual deteriorating trials remain in the raw data even when a scenario mean is not worse.

## Identifiers and configuration

- `scenario_id`: stable case identifier. `legacy_n4_05` is legacy case 5 on four nodes. Controlled identifiers contain graph size, family and declared level index.
- `suite`: `legacy`, `controlled`, or `route_diagnostic`. These suites must not be silently pooled into the manuscript's original 45-case denominator.
- `n_nodes`: number of graph junctions. `n_qubits`/`allocated_packets`: number of represented binary decisions; these differ from graph size.
- `traffic_seed`: 2026 for legacy generation. Controlled cases use deterministic explicit rules; their traffic seed is empty.
- `solver_seed`: seed used independently for each method's randomness. Its equality across paired methods identifies repetitions, not identical random streams.
- `instance_hash`: SHA-256 of the complete prepared traffic problem including candidate order and configuration. `qubo_hash`: SHA-256 of variable definitions and QUBO coefficients.
- `backend`: actual solver implementation, `exhaustive_enumeration`, `unmanaged_input`, or `not_invoked`.
- `status`: `success`, `baseline`, `no_congestion`, `no_eligible_routes`, or `solver_failed`. A no-action record is not a quantum execution. Failure details must be retained rather than treated as zeros.

## Traffic quantities

Here 'occupancy' in the repository means flow divided by capacity; it is a load/capacity ratio, not a measured detector time-occupancy percentage.

| Field | Definition/unit |
| --- | --- |
| `capacity_veh_hr` | Edge flow capacity, vehicles/hour |
| `initial_load_veh_hr`, `before_load_veh_hr`, `after_load_veh_hr` | Synthetic edge flow, vehicles/hour |
| `initial_ratio`, `before_ratio`, `after_ratio`, `mean_ratio`, `std_ratio` | Dimensionless load/capacity ratio; 1 means 100% |
| `initial_peak_pct`, `final_peak_pct` | 100 times the highest edge load/capacity ratio |
| `peak_reduction_relative_pct` | 100 times (initial peak - final peak) / initial peak |
| `peak_relief_pp` | Initial peak minus final peak, percentage points |
| `bpso_minus_qaoa_pp` | BPSO final peak minus QAOA final peak, percentage points; positive favors QAOA |
| `n_congested_after` | Count of ratios above 0.60, with a 1e-12 numerical boundary tolerance |
| `n_over_capacity_after` | Count of ratios above 1, with the same numerical boundary tolerance |
| `requested_packets` | Sum of ceil((load - 0.50 * capacity)/150) over initially congested origins |
| `budget_omitted_packets` | Requested packets omitted on origins with two detours because the global budget was reached |
| `route_omitted_packets` | Requested packets omitted because fewer than two detours exist |
| `moved_packets` | Number of allocated packets sent onto detours, independent of the bit values |
| `bitstring` | Detour index per packet. 0 selects first detour and 1 selects second detour; neither selects staying on the original edge |

Global sums of edge flows can increase after detours because the same packet traverses multiple edges. That is additional edge traversal, not new vehicle demand. The decoder's traversal accounting is not a complete dynamic traffic-conservation simulation.

## Exact references and solver quality

- `qubo_cost`: weighted sum of squared deviations from target ratio 0.50, using the implementation's initial-load-dependent weights. This is dimensionless. No hard capacity penalty is added by the current builder.
- `exact_min_qubo_cost` / `min_j_cost`: minimum J among all represented bitstrings. This is the solver-optimality reference.
- `qubo_gap_absolute`: max(0, solver J - minimum J). Floating differences within 1e-8 are treated as an exact match for reporting.
- `qubo_gap_relative_pct`: 100 times the absolute gap / absolute minimum J. It is unavailable when the denominator magnitude is at most 1e-10.
- `exact_j_peak_pct` / `min_j_peak_pct`: lowest final peak among J minimizers within an absolute J tie tolerance of 1e-10. Maximum peak across tied J minimizers is also retained.
- `exact_min_peak_pct` / `min_peak_pct`: minimum final peak among all represented assignments, using J then lexicographic bits to break peak ties.
- `objective_peak_mismatch_pp`: minimum-J peak minus minimum attainable peak. Positive values identify different preferred traffic outcomes under the two objectives.
- `all_candidates_worsen`: even the minimum attainable peak exceeds the unmanaged peak by more than 1e-8 percentage points. The current candidate set then cannot preserve the unmanaged state.
- `n_states`: exactly 2 to the number of binary variables; one empty assignment when there are zero variables.
- `max_qubo_physical_error`: largest absolute difference between the algebraic QUBO and independently calculated decoded-load objective across all represented assignments.

## Aggregation and interpretation

`*_peak_mean_pct` is the arithmetic mean of final peaks over five solver seeds on fixed traffic. `*_peak_sd_pp` is sample SD with denominator n-1. `*_reduction_relative_pct` in a scenario summary is calculated from the fixed initial peak and mean final peak. Topology median reduction is the median of these scenario-level reductions.

Outcome counts compare unrounded peaks using a 1e-8 percentage-point tolerance. They are descriptive comparisons, not significance tests. The 72 controlled cases contain explicit control/no-action conditions; retain these denominators when reporting suite-wide counts and use family-level tables for interpretation.

`guarded_final_peak_pct` is a separate hypothetical reject-if-peak-worsens policy, taking the smaller of initial and raw final peak. `guard_rejected` identifies the rejected raw plan. Main tables and figures always use raw outcomes. No guarded result is relabeled as a raw QAOA improvement.

`solve_ms` is local wall-clock solver-wrapper time. BPSO timing excludes particle construction; QAOA timing includes algorithm solve/compilation but excludes QUBO construction. It is not a matched end-to-end latency benchmark. Exact enumeration timing includes decoding and independent physical validation. No speed comparison is inferred from these different boundaries.
