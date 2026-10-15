"""
run_quantum_advantage.py
========================
Top-level runner for Empirical Quantum Advantage benchmarking.
Compares QAOA vs BPSO across problem scales N in [4, 6, 8, 10, 12, 14] qubits
on frustrated, highly non-convex traffic network instances.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from strict_qaoa.quantum_advantage_benchmark import run_quantum_advantage_study

if __name__ == "__main__":
    output_dir = os.path.join(current_dir, "charts")
    results = run_quantum_advantage_study(
        scale_range=[4, 6, 8, 10, 12],
        n_trials=4,
        output_dir=output_dir,
    )
    print("\n[SUCCESS] Quantum Advantage Benchmark complete.")
    print(f"Results and publication figures saved in: {output_dir}")
