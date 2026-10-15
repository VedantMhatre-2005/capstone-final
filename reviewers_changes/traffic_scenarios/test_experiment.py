"""Checks for the shared decision problem, physics, boundaries, and solver adapters."""
import unittest

import numpy as np

from .experiment import (DEFAULT_CONFIG, apply_solution, cost, enumerate_exact,
                         metrics, prepare, scenarios, solve_bpso, solve_qiskit)


class ScenarioEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {s["id"]: s for s in scenarios()}
        cls.config = DEFAULT_CONFIG

    def test_suite_size_and_unique_cases(self):
        self.assertEqual(len(self.cases), 119)
        self.assertEqual(sum(s["suite"] == "legacy" for s in self.cases.values()), 45)
        self.assertEqual(sum(s["suite"] == "controlled" for s in self.cases.values()), 72)

    def test_threshold_and_off_peak_do_not_trigger(self):
        for name in ("controlled_n4_off_peak_3", "controlled_n4_threshold_1", "controlled_n4_threshold_2"):
            p = prepare(self.cases[name], self.config)
            self.assertEqual(p["status"], "no_congestion")
            self.assertEqual(len(p["packets"]), 0)
        self.assertEqual(prepare(self.cases["controlled_n4_threshold_3"], self.config)["status"], "ready")

    def test_capacity_sweeps_hold_demand_fixed(self):
        for family in ("lane_closure", "weather_capacity_loss"):
            ss = [self.cases[f"controlled_n4_{family}_{i}"] for i in (1, 2, 3)]
            self.assertEqual(ss[0]["loads"], ss[1]["loads"])
            self.assertEqual(ss[0]["loads"], ss[2]["loads"])
            self.assertLess(ss[2]["capacities"][("A", "B")], ss[0]["capacities"][("A", "B")])

    def test_unavailable_routes_are_explicit(self):
        for name, expected in (("one_detour", 1), ("no_detour", 0)):
            p = prepare(self.cases[f"diagnostic_{name}"], self.config)
            self.assertEqual(p["status"], "no_eligible_routes")
            self.assertEqual(p["allocation"][0]["candidate_detours"], expected)
            self.assertGreater(p["allocation"][0]["requested_packets"], 0)

    def test_all_zero_is_a_detour_not_unmanaged(self):
        p = prepare(self.cases["legacy_n4_01"], self.config)
        updated = apply_solution(p["packets"], (0,) * len(p["packets"]), p["loads"])
        self.assertNotEqual(updated, p["loads"])
        self.assertGreater(sum(updated.values()), sum(p["loads"].values()))

    def test_exact_reference_checks_all_physical_states(self):
        p = prepare(self.cases["legacy_n4_02"], self.config)
        exact = enumerate_exact(p, self.config)
        self.assertEqual(exact["n_states"], 2 ** len(p["packets"]))
        self.assertLess(exact["max_qubo_physical_error"], 1e-8)
        self.assertLessEqual(exact["min_peak_pct"], exact["min_j_peak_pct"] + 1e-8)
        self.assertAlmostEqual(cost(p["qubo"], exact["min_j_bits"]), exact["min_j_cost"])

    def test_bpso_is_reproducible_and_not_better_than_exact(self):
        p = prepare(self.cases["legacy_n4_01"], self.config)
        a, b = solve_bpso(p, 42, self.config), solve_bpso(p, 42, self.config)
        self.assertEqual(a["bits"], b["bits"])
        self.assertEqual(a["evaluations"], 630)
        self.assertGreaterEqual(a["cost"] + 1e-8, enumerate_exact(p, self.config)["min_j_cost"])

    def test_bpso_adapter_matches_original_production_engine(self):
        # The full engine rebuilds a graph; verify the frozen adapter preserves its result.
        from graph import Edge, Node, TrafficGraph
        from pso import PSO
        p = prepare(self.cases["legacy_n4_01"], self.config)
        graph = TrafficGraph()
        graph.nodes = {n: Node(n, n, 60.0) for n in p["graph"]}
        graph.edges, graph._edge_index = [], {}
        initial = {}
        for (u, v), c in p["capacities"].items():
            for src, dst in ((u, v), (v, u)):
                edge = Edge(src, dst, 1.0, c, 50.0, 3, 1.0, "Arterial", .60*c)
                graph.edges.append(edge)
                graph._edge_index[edge.id] = edge
                initial[edge.id] = p["loads"][(u, v)]
        production = PSO(seed=42).optimize(graph, initial, {n: 60.0 for n in graph.nodes})
        adapter = solve_bpso(p, 42, self.config)
        self.assertEqual(adapter["bits"], production["gbest_bitstring"])
        self.assertAlmostEqual(adapter["cost"], production["final_fitness"], places=10)

    def test_qiskit_bit_order_cost_and_seed_reproducibility(self):
        p = prepare(self.cases["controlled_n4_threshold_3"], self.config)
        config = {**self.config, "qaoa_maxiter": 12, "qaoa_shots": 128}
        a, b = solve_qiskit(p, 42, config), solve_qiskit(p, 42, config)
        self.assertEqual(a["bits"], b["bits"])
        self.assertAlmostEqual(a["cost"], cost(p["qubo"], a["bits"]), places=10)

    def test_compiled_qaoa_preserves_state_probabilities(self):
        from qiskit.circuit.library import QAOAAnsatz
        from qiskit.quantum_info import Statevector
        from qiskit.transpiler import generate_preset_pass_manager
        from qiskit_optimization import QuadraticProgram
        p = prepare(self.cases["legacy_n4_01"], self.config)
        qp = QuadraticProgram()
        for v in p["qubo"]["variables"]:
            qp.binary_var(v["name"])
        qp.minimize(constant=p["qubo"]["constant"], linear=p["qubo"]["linear"],
                    quadratic=p["qubo"]["quadratic"])
        operator, _ = qp.to_ising()
        circuit = QAOAAnsatz(operator, reps=1).assign_parameters([.37, .81])
        compiled = generate_preset_pass_manager(optimization_level=0,
            basis_gates=["h", "rx", "rz", "cx"], seed_transpiler=42).run(circuit)
        np.testing.assert_allclose(Statevector(circuit).probabilities(),
                                   Statevector(compiled).probabilities(), atol=1e-12)

    def test_zero_peak_metric_does_not_divide_by_zero(self):
        p = prepare(self.cases["controlled_n4_off_peak_1"], self.config)
        p["loads"] = {e: 0.0 for e in p["loads"]}
        self.assertIsNone(metrics(p, p["loads"])["peak_reduction_relative_pct"])


if __name__ == "__main__":
    unittest.main()
