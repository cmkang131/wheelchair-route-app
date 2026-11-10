"""A* vs Dijkstra (the app's Python code) on every ordered node pair of G'.
python3 check_all_pairs.py"""
import math
from cost_model import CostParams, build_g_prime
from data_loader import load
from pathfinding import a_star, dijkstra, heuristic_scale

data = load("data")
adj = build_g_prime(data.edges, CostParams())
alpha = heuristic_scale(data.coords, adj)
nodes = sorted(set(adj) | {v for out in adj.values() for v, _, _ in out})
pairs = reach = nopath = disagree = mism = 0; maxdiff = 0.0
for s in nodes:
    for t in nodes:
        if s == t:
            continue
        d, a = dijkstra(data.coords, adj, s, t), a_star(data.coords, adj, s, t, alpha)
        pairs += 1
        if d.found != a.found:
            disagree += 1
        elif not d.found:
            nopath += 1
        else:
            reach += 1
            diff = abs(d.cost - a.cost); maxdiff = max(maxdiff, diff); mism += diff > 1e-6
print(f"ordered pairs {pairs}, with route {reach}, no route {nopath}, "
      f"reachability disagreements {disagree}, cost mismatches {mism}, max diff {maxdiff:.3g}")
