# Yash: evaluating traffic scenarios

The evaluation has now been implemented and executed. Open [the completed report](yash_traffic_evaluation/REPORT.md) and [deliverables index](yash_traffic_evaluation/README.md). The plan below documents the initial audit and experimental design; the completed report contains the new measured results.

This guide is based on the current repository and the supplied 14-page paper, 20-page paper, and reviewer comments. It is an evaluation plan, not a report of newly executed QAOA experiments. Existing application and experiment code has not been changed.

Your research question is: **Under which traffic conditions does rerouting improve congestion, how does QAOA compare with BPSO on the same instances, and what explains weak or negative outcomes?**

## 1. Your scope and team interfaces

| Person | Main responsibility | Interface with your work |
| --- | --- | --- |
| Yash | Define traffic cases, measure paired outcomes, investigate failures, interpret results | Own scenario inputs, result schema, plots, case studies, and scenario discussion |
| Sanjay | Multi-seed reproducibility and statistical analysis | Give him fixed scenario manifests; distinguish traffic-generation seeds from solver seeds |
| Vedant | Qubit size and additional result columns | Give him requested versus allocated packets, omitted origins, and cases reaching the cap |
| Aditya | IBM hardware and measured end-to-end pipeline latency | Give him representative easy, hard, and negative cases with the same saved inputs |

You can start with optimizer-only experiments using known synthetic loads. Label them accordingly. Model inference and IBM execution are not prerequisites for that first stage.

Reviewer #3 comments 1, 2, 3, and 6 are especially relevant: reconcile outcome counts; show negative outcomes; include paired BPSO values; explain whether small reductions matter in practice. The exhaustive baseline requested by Reviewer #2 comment 6 is also necessary for interpreting solver quality.

## 2. What the implementation actually does

The forecasting scripts use graph features and a quantum update layer to predict edge flows. Forecasting datasets have 8-node and 24-node graphs. The publication rerouting experiment separately generates load snapshots on complete 4-, 5-, and 6-node graphs: 15 cases per size, giving 45 instances.

Read these files in order:

1. `optimization_algorithms/capstone-optimization/backend/run_publication_45_scenarios.py`: the 15 load-generation rules and the original comparison loop.
2. `optimization_algorithms/capstone-optimization/backend/final_qaoa_with_signal.py`: network normalization, congestion detection, detour generation, packets, QUBO, decoding.
3. `optimization_algorithms/capstone-optimization/backend/pso.py`: BPSO uses the same packet/QUBO helper functions, but rebuilds the instance internally.
4. `reviewers_changes/run_brute_force_baseline.py`: strict Qiskit solve wrapper and three-way comparison. Its exhaustive solver minimizes peak occupancy first.
5. `reviewers_changes/test_all_45_qubo_bf.py`: a different experiment that enumerates the minimum QUBO cost and uses a custom sampled statevector QAOA simulation. It executes at import/top level and overwrites the shared comparison CSV; inspect it before running it.

Current settings include congestion threshold 0.60, target load/capacity ratio 0.50, packet size 150 veh/hr, two detours, at most three hops, and a global cap of 10 packets/binary variables. BPSO defaults used in the benchmark are 30 particles and 20 iterations.

Important implementation details:

- `build_network()` merges opposite directions into an undirected edge using maximum directional capacity/load. It cannot establish inbound-versus-outbound behavior independently.
- `generate_packets()` uses `ceil`, requires exactly two detours, and allocates packets in congested-edge iteration order until the global budget is exhausted. A congested edge can be omitted because of the budget or insufficient detours.
- Each packet is removed from its origin regardless of its bit. Bit 0 chooses detour 1; bit 1 chooses detour 2. **The all-zero vector is not a no-rerouting action.** Both supplied papers describe a stay-versus-reroute encoding; the 20-page paper explicitly says all-zero means no rerouting. That does not match this implementation.
- `build_qubo()` minimizes weighted squared distance from target occupancy, not maximum occupancy. The `capacity_penalty_weight` argument is present but unused in coefficient construction. Do not describe it as an enforced hard capacity constraint.
- The production `solve_qaoa()` catches exceptions and returns all zeros. That changes traffic under this encoding and must not be counted as a successful QAOA solve. Use explicit solver status and the strict wrapper for research runs.
- Candidate routes are sorted by path length, then bottleneck occupancy; this differs from the weighted-sum score described in the papers.

Resolve the intended encoding with the team before the final benchmark: document the present two-detour formulation, or implement the intended stay/detour formulation consistently for all solvers and rerun. Keep those experiment versions separate.

## 3. First task: reconcile the existing evidence

The 20-page manuscript reports identical single-seed QAOA/BPSO peaks in all 45 cases, 40 improved initial states, one unchanged state, four worsened states, and 32 exact QUBO matches.

Recalculation from the currently saved `reviewers_changes/brute_force_comparison_results.csv` gives:

| Topology | Cases | QAOA improves initial peak | Unchanged | Worsens | QAOA beats BPSO | Ties BPSO | Loses to BPSO |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 nodes | 15 | 11 | 0 | 4 | 2 | 4 | 9 |
| 5 nodes | 15 | 11 | 0 | 4 | 1 | 5 | 9 |
| 6 nodes | 15 | 14 | 0 | 1 | 2 | 6 | 7 |
| Total | 45 | 36 | 0 | 9 | 5 | 15 | 25 |

The saved `opt_gap_pct` column is zero within 0.0001 percentage points in 11 rows. These are calculations from rounded saved values, not fresh solver runs or an independent verification of the gap calculation.

Example: the saved 5-node School Zone row has initial peak 84.45%, QAOA peak 92.88%, and BPSO peak 81.57%. The manuscript Table 4 shows 81.57% for both solvers. The CSV and manuscript therefore cannot be treated as a single verified experiment. This does not establish which version is correct.

Find the run/artifact that generated the final paper, or regenerate a new documented run. Preserve old results. Use unique run directories containing the commit identifier, configuration, inputs, raw outputs, software versions, and solver identity. Two scripts currently write to the same comparison CSV using different exhaustive objectives and QAOA implementations.

Also verify scenario semantics. The generated 4-node Off-Peak Nighttime case has an 81.78% initial peak. All named bottlenecks use roughly 72%-86% load/capacity, including the off-peak case. Most descriptive labels change selected bottleneck edges rather than implementing the claimed event physics. Bad weather does not explicitly reduce capacities in this generator. Treat existing cases as a legacy synthetic benchmark until their names or rules are corrected.

## 4. Define meaningful new traffic cases

Retain the 45 legacy cases for traceability. Add a separately named, controlled scenario suite. Start with these families on the same three graph sizes:

| Family | Concrete input rule | What it tests |
| --- | --- | --- |
| Off-peak control | Every edge at 20%-40% of capacity | No congestion and no unnecessary rerouting |
| Threshold boundary | One edge at 59%, 60%, and 61%; others at 30% | The strict `> 0.60` trigger |
| Single bottleneck | One edge at 65%, 80%, then 95%; background fixed at 30% | Increasing localized severity |
| Adjacent bottlenecks | Two overloaded edges sharing a junction | Detour competition and secondary congestion |
| Separated bottlenecks | Two overloaded edges without a shared endpoint | Spatially distributed demand |
| Distributed peak | Several overloaded edges; compare low versus high background load | Availability of spare detour capacity |
| Lane closure | Keep demand fixed and reduce one edge's original capacity, e.g. by 25% and 50% | Capacity-driven congestion, independent of demand |
| Weather capacity loss | Keep demand fixed and reduce capacities across selected/all edges by declared factors | Network-wide loss of spare capacity |

These numeric levels are proposed experimental settings, not empirically calibrated traffic laws. Save exact values and any random draws. Use identical base capacities and background loads within a controlled sweep; change only the intended factor. If you add directional morning/evening cases, first use an implementation that preserves directed flows. Static snapshots support claims about rerouting under a load state, not dynamic queue recovery or travel-time benefits.

Add two diagnostic edge cases after the main suite: a congested edge with only one available detour, and a bridge edge with no detour. The current implementation allocates no packets to either. Distinguish `no_congestion`, `no_eligible_routes`, and `solver_failed`; none should silently disappear from reporting.

## 5. Use a paired, traceable experiment procedure

For each topology/scenario realization:

1. Save the graph, ordered edge list, capacities, loads, scenario parameters, and traffic seed.
2. Detect congestion and generate candidate routes once. Save routes, requested packets per edge, allocated packets, omitted origins, and the QUBO with explicit variable order.
3. Validate positive capacities, nonnegative loads, valid detour endpoints/edges, packet/bitstring lengths, and matching inputs for every solver. Check resulting negative loads and overloads explicitly. The existing edge-flow accounting assertion is not a complete traffic-feasibility check.
4. Run the unmanaged baseline, BPSO, QAOA, and exhaustive search on the same decision problem. If BPSO still rebuilds it, compare its normalized edge/variable order, packets, routes, and QUBO coefficients against the saved problem.
5. Record solver identity, success/failure, bitstring, objective value, and decoded per-edge loads. Retain failed records and denominators. Do not substitute an exact solution or a default bitstring for a failed QAOA solve.
6. Give the frozen inputs to Sanjay for repetitions. Keep traffic-realization variation separate from solver randomness. A solver-reproducibility experiment fixes traffic and changes solver seeds; a scenario-generalization experiment changes traffic realizations and evaluates all methods on each realization.
7. Generate tables and paper numbers from the saved raw outputs. Round only for presentation.

For QAOA, save depth, shots, sampler seed, parameter initialization/seed, classical optimizer settings, and implementation. A custom NumPy statevector simulation, Qiskit execution, and IBM hardware execution must have distinct backend labels.

The existing `run_statistical_eval.py` changes scenario-generation seeds while BPSO is constructed with seed 42, and its recorded paired t-test compares QAOA with the unmanaged baseline. That test does not establish QAOA-versus-BPSO significance. Give this finding to Sanjay. Failure to reject a difference also does not, by itself, establish equivalence.

## 6. Metrics and result columns

The code calls load/capacity 'occupancy'. Define that convention explicitly; it is a flow-to-capacity ratio here.

Let `P_before = 100 * max(load[e]/capacity[e])` and define `P_after` similarly.

- Relative peak reduction: `100 * (P_before - P_after) / P_before`. Handle a zero initial peak explicitly. Negative values mean deterioration.
- Absolute peak relief in percentage points: `P_before - P_after`.
- Solver comparison: `P_BPSO - P_QAOA`, in percentage points. Positive means QAOA achieved a lower final peak.
- Also report mean ratio, ratio standard deviation, number of edges above 60%, number above 100%, moved packets, and QUBO objective cost.
- Keep measured solver runtime as contextual information under a declared boundary; Aditya owns detailed end-to-end/hardware latency comparisons.

Recommended raw row (one method, one case, one solver repetition):

```text
run_id, commit, scenario_id, topology, family, severity,
traffic_seed, solver_seed, method, backend, status,
n_congested_before, requested_packets, allocated_packets, omitted_origins,
n_qubits, qubo_hash, initial_peak_pct, final_peak_pct,
peak_reduction_relative_pct, peak_relief_pp, mean_ratio, std_ratio,
n_congested_after, n_over_capacity_after, moved_packets,
qubo_cost, exact_min_qubo_cost, qubo_gap_absolute, qubo_gap_relative_pct,
exact_min_peak_pct, bitstring, solve_ms
```

Save per-edge before/after loads in a separate linked artifact. Use a declared numerical tolerance for better/tie/worse counts, based on unrounded values. Do not combine those counts with statistical significance categories.

Small gains need context: the manuscript's 5-node School Zone result, 84.45% to 81.57%, is 2.88 percentage points, approximately 3.41% relative reduction using the displayed rounded numbers. It still exceeds the 60% congestion trigger. It is positive peak relief, but does not clear congestion under that trigger. The manuscript's 3.42% may reflect unrounded inputs; calculate from raw data.

## 7. Diagnose weak and negative scenarios

Investigate every negative case and at least one strong and one marginal case per topology. Produce an edge-by-edge before/after table and trace the packets that create the final bottleneck.

Compute two different exact references on the same packet/route set:

1. **Minimum J:** enumerate all bitstrings and minimize the QUBO cost. This is the reference for QAOA/BPSO objective optimality gaps. Use `J_solver - J_min` and, when the denominator is meaningful, `100*(J_solver-J_min)/abs(J_min)`.
2. **Minimum peak:** enumerate the same bitstrings and minimize final peak occupancy. This is a diagnostic for attainable traffic relief within that candidate set. It is not the QUBO ground state unless the objectives happen to agree.

`run_brute_force_baseline.py` currently uses minimum peak, with QUBO cost as a tie-breaker, then compares its cost with QAOA's cost. That does not provide a valid QUBO-optimality reference in general. `test_all_45_qubo_bf.py` instead minimizes J. Do not mix those definitions in a single gap claim.

Interpretation:

- QAOA has a worse J than exact minimum J: solver approximation/sampling error is present.
- Exact minimum J has poor peak, while minimum peak is better: the optimization objective and reported traffic metric favor different solutions.
- Every represented bitstring worsens the initial peak: the current candidate/mandatory-detour formulation cannot preserve the unmanaged state.
- Requested packets exceed allocated packets: the global cap truncates the instance. `N=10` alone does not prove truncation or explain deterioration.
- Repeat a few failing cases with a larger cap, using Vedant's settings, holding traffic and route rules fixed. Use exhaustive/reference results to separate changes to the decision space from additional QAOA solver difficulty. Check allocation order as another possible contributor.

A reject-if-peak-worsens rule is a possible separately evaluated policy. Report raw solver results and guarded policy results independently; rejected actions must not disappear from the raw deterioration counts.

## 8. What to deliver

1. A scenario manifest with formulas, graph definitions, capacities, loads, and seeds.
2. A reconciled 45-case legacy result table with unmanaged, QAOA, BPSO, minimum-J reference, and minimum-peak reference values.
3. A new controlled-scenario result table, with repeated-run summaries from Sanjay.
4. Three main plots: paired before/after peaks by scenario, peak reduction versus controlled severity, and a scenario-family-by-topology heatmap. Include negative values and uncertainty where available.
5. A few detailed case studies explaining strong, marginal, and negative outcomes from actual edge/packet evidence.
6. A revised scenario-results discussion and reviewer response for comments #3.1, #3.2, #3.3, and #3.6; coordinate the exact baseline explanation with #2.6.

Suggested order: reconcile one existing 4-node case; verify shared QUBO and exact references; audit all 45 saved cases; define/save the controlled suite; run all paired methods; hand the fixed inputs to Sanjay; investigate failures with Vedant; send representative cases to Aditya; regenerate the final tables and write the discussion.

Additional handoffs: the single-network generator and saved timestamps use five-minute intervals despite training comments/manuscripts saying five seconds. `run_integrated_pipeline.py` generates predictions by adding noise to fixed loads and inserts an assumed 0.5 ms inference time; `run_multi_horizon_evaluation.py` perturbs loads using assigned noise levels. Those scripts alone do not verify measured trained-model inference or measured multi-horizon forecasting accuracy. Aditya/the forecasting owner should reconcile these before integrated or horizon claims are reused.
