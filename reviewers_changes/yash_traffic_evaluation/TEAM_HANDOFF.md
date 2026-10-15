# Team handoff

## Sanjay

Use `results/scenario_manifest.json` and `results/cases/` as fixed traffic inputs. The five seeds in this run vary QAOA initialization/sampling and BPSO initialization; they do not vary traffic. `results/paired_per_seed.csv` supplies paired peaks. Keep traffic-realization replication separate from solver replication. Compare QAOA with BPSO explicitly if making that claim. A test against the unmanaged input answers a different question. Prespecify inference, multiplicity correction and practical-equivalence margins where applicable. This package makes no p-value/equivalence claims.

## Vedant

Inspect `results/packet_allocation.csv`, `results/budget_order_diagnostics.csv`, and the full case QUBOs. Budgets 6/10/12 are exact-only diagnostic variants. Reaching the cap is distinct from omitting requested packets. Larger budgets force additional packets to detour in the current model, so peak reduction need not be monotonic. Allocation order can change covered origins. Use a separately named experiment for quantum circuit/resource scaling.

## Aditya

Representative easy, marginal and failing cases are identified in `results/team_representative_cases.json`. Each links to an exact input/QUBO/packet artifact. Use matching inputs for statevector/hardware comparisons. Measure actual inference, preprocessing, routing, QUBO construction, transpilation, execution and decoding under explicit timing boundaries. This package's solver-wrapper timings are not end-to-end latency or QPU timing.

## Team method corrections

The existing binary encoding chooses between two detours and cannot retain an allocated packet at its origin. The paper's stay-versus-reroute description must be revised or implemented and all solvers rerun under a separately versioned model. The current builder does not implement the advertised capacity penalty. The single-network generator/saved timestamps use five-minute steps despite five-second comments/manuscript claims. Existing integrated/horizon scripts use synthetic noise/assumed inference timing; those are not measured trained-model inference or measured longer-horizon forecast errors. Resolve these outside the scope of this traffic-only report before making those claims.
