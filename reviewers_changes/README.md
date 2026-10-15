# reviewers_changes/ -- ICMLDE 2026 Revision Package

All files in this folder address reviewer comments without modifying
the existing project source code.

## Files

### Python Scripts (run from this directory)
All scripts require the backend on sys.path (handled automatically):

| Script | Addresses | Outputs |
|--------|-----------|---------|
| `run_brute_force_baseline.py` | R2-C6, R3-C3 | `brute_force_comparison_results.csv`, `bf_three_way_table.tex`, 3 figures |
| `run_integrated_pipeline.py` | R3-C5 | `integrated_pipeline_results.csv`, `fig_integrated_pipeline.png` |
| `run_multi_horizon_evaluation.py` | R2-C5 | `multi_horizon_results.csv`, `multi_horizon_table.tex`, 1 figure |

### LaTeX File
`reviewer_revisions.tex` -- complete revision content with sections:
- **A** Abstract (revised): removes "never worse" claim and QA claims
- **B** Reproducibility: seeds, hyperparams, QAOA depth clarification
- **C** VQC ablation + total parameter count table
- **D** Notation correction (O* vs delta vs Delta_p)
- **E** Qubit budget reconciliation (N_max=10, averages<=10)
- **F** BF exhaustive search baseline (new Section 6.2.x)
- **G** Scenario count reconciliation (13+29+3=45)
- **H** Table 4 with BF and BPSO columns (use bf_three_way_table.tex)
- **I** Latency reporting clarification (wall-clock vs solve-only)
- **J** Integrated pipeline (new Section 6.3)
- **K** Multi-horizon forecasting justification
- **L** Marginal improvement discussion (3.42%, 3.50%)
- **M** List of quantum advantage phrases to DELETE from paper
- **N** Bibliography additions

### Running the Scripts

```powershell
cd reviewers_changes\
python run_brute_force_baseline.py       # ~30-60 min (45 QAOA runs)
python run_integrated_pipeline.py        # ~5 min
python run_multi_horizon_evaluation.py   # ~60-90 min (30x4 QAOA runs)
```

After running, replace [fill] placeholders in reviewer_revisions.tex
with actual values from the CSV outputs.

### Inserting into Paper

1. Replace abstract with Section A content
2. Insert Section B after Section 3.1 (STQGCN Architecture)
3. Insert Section C after Section 3.1.2 (VQC description)
4. Apply notation changes from Section D globally
5. Replace qubit budget paragraph with Section E
6. Insert Section F after Section 6.2 QAOA results
7. Replace scenario narrative with Section G
8. Use `\input{reviewers_changes/bf_three_way_table.tex}` for Table 4
9. Replace latency paragraph with Section I
10. Insert Section J as new Section 6.3
11. Insert Section K after Section 6.2.1
12. Add Section L after 5-node topology discussion
13. Delete all phrases listed in Section M
14. Add Section N entries to bibliography

### No Fallbacks Policy
All three scripts call QAOA via Qiskit with NO silent fallback:
- Solver exceptions propagate and are logged
- No all-zeros bitstring returned on failure
- Failed scenarios are marked in CSV with `qaoa_failed=True`
