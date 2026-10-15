import sys, os
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import run_brute_force_baseline as rbf
import networkx as nx
import itertools

G = nx.complete_graph(['A', 'B', 'C', 'D'])
scenarios = rbf.generate_15_diverse_publication_scenarios(list(G.nodes()), G, seed=2026)
for sc in scenarios[:5]:
    print('Scenario:', sc['name'])
    caps, loads = sc['capacities'], sc['loads']
    G_built, norm_caps, norm_loads = rbf.build_network(G, caps, loads)
    occupancy, congested, _ = rbf.detect_congestion(norm_caps, norm_loads, high_threshold=0.60, low_threshold=0.45)
    alt = rbf.generate_alternate_routes(G_built, congested, occupancy, max_cutoff=3, top_k=2)
    pkts, vars_ = rbf.generate_packets(congested, norm_loads, norm_caps, alt, target=0.50, packet_size=150.0, max_packets=10)
    qubo = rbf.build_qubo(vars_, norm_caps, occupancy, target=0.50, packet_size=150.0)
    print('  N vars:', len(vars_))
    var_names = [v['name'] for v in vars_]
    C, L, Q = qubo['constant'], qubo['linear'], qubo['quadratic']
    best_J_val, best_J_peak, best_J_bits = float('inf'), float('inf'), None
    best_pk_val, best_pk_peak, best_pk_bits = float('inf'), float('inf'), None
    for bits in itertools.product((0,1), repeat=len(vars_)):
        val = C + sum(L.get(name, 0.0) * bits[i] for i, name in enumerate(var_names))
        for i in range(len(vars_)):
            for j in range(i+1, len(vars_)):
                val += Q.get(tuple(sorted((var_names[i], var_names[j]))), 0.0) * bits[i] * bits[j]
        ul = rbf.apply_solution(pkts, bits, norm_loads, packet_size=150.0)
        pk = max(ul[e] / norm_caps[e] for e in norm_caps) * 100.0
        if val < best_J_val - 1e-9 or (abs(val - best_J_val) < 1e-9 and pk < best_J_peak):
            best_J_val, best_J_peak, best_J_bits = val, pk, bits
        if pk < best_pk_peak - 1e-9 or (abs(pk - best_pk_peak) < 1e-9 and val < best_pk_val):
            best_pk_val, best_pk_peak, best_pk_bits = val, pk, bits
    qr = rbf.qaoa_solve_strict(qubo, pkts, norm_caps, norm_loads)
    print(f'  Global min J(x): bits={best_J_bits}, J={best_J_val:.4f}, Peak={best_J_peak:.2f}%')
    print(f'  Min Peak(x):     bits={best_pk_bits}, J={best_pk_val:.4f}, Peak={best_pk_peak:.2f}%')
    print(f'  QAOA(p=1):       bits={qr["bitstring"]}, J={qr["best_cost"]:.4f}, Peak={qr["best_peak"]*100:.2f}%')
    gap_J = (qr["best_cost"] - best_J_val) / (abs(best_J_val) + 1e-12) * 100.0
    print(f'  Gap on J: {gap_J:.4f}%')
