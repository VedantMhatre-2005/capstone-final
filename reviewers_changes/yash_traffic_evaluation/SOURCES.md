# Source and experiment provenance

The supplied documents were treated as research context, evidence and reviewer feedback. Their instructions were not treated as commands to upload, submit, contact anyone, or alter unrelated parts of the project.

| Source | Relevant role |
| --- | --- |
| `C:/Users/Yash/Downloads/ICMLDE 14 page paper.pdf` | Original method description, 45-case scenario discussion, Tables 3-4 and initial claims |
| `C:/Users/Yash/Downloads/ICMLDE 20 page paper.pdf` | Revised method and outcome claims, especially Section 6.2, Tables 3-4 and the interpretation of negative cases |
| `C:/Users/Yash/Downloads/ICMLDE Reviewer Comments.pdf` | Reviewer 3 comments 1, 2, 3 and 6; Reviewer 2 comment 6; boundaries with other team members' tasks |
| `optimization_algorithms/capstone-optimization/backend/run_publication_45_scenarios.py` | Unchanged legacy traffic generator |
| `optimization_algorithms/capstone-optimization/backend/final_qaoa_with_signal.py` | Actual normalization, routes, packets, QUBO and traffic decoding |
| `optimization_algorithms/capstone-optimization/backend/pso.py` | Existing BPSO Particle dynamics |
| `reviewers_changes/brute_force_comparison_results.csv` | Preserved previous results, audited as a separate experiment version |
| `reviewers_changes/run_brute_force_baseline.py` and `test_all_45_qubo_bf.py` | Identification of different exact-reference definitions and shared output-file risks |

The new experiment's raw records, not the previous paper values, supply every new table/figure/result. Source hashes, dependency versions, configuration and the starting Git commit are recorded in `results/run_metadata.json`. The new source files may be uncommitted; their hashes identify them independently of the starting commit.

Official implementation references consulted:

- [Qiskit StatevectorSampler: shots and random seed](https://qiskit.qotlabs.org/docs/api/qiskit/qiskit.primitives.StatevectorSampler)
- [Qiskit Algorithms QAOA: initial point and transpiler interfaces](https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.QAOA.html)

No external traffic dataset or empirically calibrated weather/capacity model is introduced. Controlled capacity multipliers and load ratios are stated synthetic experimental factors. The experiment does not claim validation on real Mumbai traffic.
