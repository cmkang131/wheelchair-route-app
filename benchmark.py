"""Dijkstra vs A* (straight line) vs ALT (landmarks) on every pair of buildings.
python3 benchmark.py [--k 8]"""
import argparse, itertools, math, time
from cost_model import CostParams, build_g_prime
from data_loader import load
from pathfinding import a_star, alt, build_landmarks, dijkstra, heuristic_scale

ap = argparse.ArgumentParser(); ap.add_argument("--k", type=int, default=8); args = ap.parse_args()
data = load("data")
adj = build_g_prime(data.edges, CostParams())
alpha = heuristic_scale(data.coords, adj)
t0 = time.perf_counter(); lm = build_landmarks(adj, k=args.k); t_pre = time.perf_counter() - t0
rep = {}
for r in data.entrances:
    if r["wheelchair_accessible"].lower() == "yes":
        rep.setdefault(r["building_id"], r["node_id"])
pairs = list(itertools.combinations(sorted(rep.values()), 2))
tot = {"Dijkstra": [0, 0.0], "A*": [0, 0.0], "ALT": [0, 0.0]}
found = bad = 0
for s, t in pairs:
    res = {}
    for name, fn in [("Dijkstra", lambda: dijkstra(data.coords, adj, s, t)),
                     ("A*", lambda: a_star(data.coords, adj, s, t, alpha)),
                     ("ALT", lambda: alt(data.coords, adj, s, t, lm, alpha))]:
        t1 = time.perf_counter(); r = fn(); dt = time.perf_counter() - t1
        res[name] = r; tot[name][0] += r.expanded; tot[name][1] += dt
    if res["Dijkstra"].found:
        found += 1
        bad += any(not math.isclose(res[n].cost, res["Dijkstra"].cost, abs_tol=1e-6) for n in res)
    else:
        bad += any(res[n].found for n in res)
print(f"pairs {len(pairs)}, found {found}, cost mismatches {bad}")
print(f"landmarks k={len(lm.ids)}, precompute {t_pre*1000:.1f} ms (once per cost setting)")
base = tot["Dijkstra"][0]
for n, (e, s) in tot.items():
    print(f"{n:9s} expanded {e:6d} ({100*e/base:5.1f}%)  time {s*1000:7.1f} ms")
