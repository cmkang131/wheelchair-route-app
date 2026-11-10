"""Wider benchmark: random node pairs over all of G', several repeats, per-query stats.
python3 benchmark_wide.py [--pairs 10000] [--reps 3] [--seed 0]"""
import argparse, math, random, statistics as st, time
from cost_model import CostParams, build_g_prime
from data_loader import load
from pathfinding import _reverse, a_star, alt, bidirectional_dijkstra, build_landmarks, dijkstra, heuristic_scale

ap = argparse.ArgumentParser()
ap.add_argument("--pairs", type=int, default=10000)
ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
data = load("data")
adj = build_g_prime(data.edges, CostParams())
alpha = heuristic_scale(data.coords, adj)
lm = build_landmarks(adj, k=8)
rev = _reverse(adj)
nodes = sorted(set(adj) | {v for out in adj.values() for v, _, _ in out})
rng = random.Random(a.seed)
pairs = [tuple(rng.sample(nodes, 2)) for _ in range(a.pairs)]
algos = {"Dijkstra": lambda s, t: dijkstra(data.coords, adj, s, t),
         "Bidirectional": lambda s, t: bidirectional_dijkstra(adj, s, t, rev),
         "A*": lambda s, t: a_star(data.coords, adj, s, t, alpha),
         "ALT": lambda s, t: alt(data.coords, adj, s, t, lm, alpha)}
names = list(algos)
times = {n: [] for n in names}; exp = {n: 0 for n in names}
found = bad = 0; dcost = {}
for i, (s, t) in enumerate(pairs):
    best = {n: math.inf for n in names}; res = {}
    for r in range(a.reps):
        order = names[(i + r) % 4:] + names[:(i + r) % 4]      # rotate order
        for n in order:
            t1 = time.perf_counter(); res[n] = algos[n](s, t); dt = time.perf_counter() - t1
            best[n] = min(best[n], dt)
    for n in names:
        times[n].append(best[n] * 1e6); exp[n] += res[n].expanded
    if res["Dijkstra"].found:
        found += 1; dcost[i] = res["Dijkstra"].cost
        bad += any(not math.isclose(res[n].cost, res["Dijkstra"].cost, abs_tol=1e-6) for n in names)
    else:
        bad += any(res[n].found for n in names)
print(f"nodes {len(nodes)}, pairs {len(pairs)}, reachable {found}, cost mismatches {bad}, reps {a.reps} (min per query)")
base_t = sum(times["Dijkstra"]); base_e = exp["Dijkstra"]
for n in names:
    x = sorted(times[n])
    p = lambda q: x[int(q * (len(x) - 1))]
    wins = sum(b < d for b, d in zip(times[n], times["Dijkstra"]))
    print(f"{n:13s} nodes {100*exp[n]/base_e:5.1f}%  mean {st.mean(x):6.0f}us  median {p(.5):6.0f}  p90 {p(.9):6.0f}  p99 {p(.99):6.0f}  total {100*sum(x)/base_t:5.1f}%  faster-than-Dijkstra {100*wins/len(x):4.1f}%")
srt = sorted(dcost, key=dcost.get); k = len(srt)
groups = {"short (1/3)": srt[:k//3], "mid (1/3)": srt[k//3:2*k//3], "long (1/3)": srt[2*k//3:],
          "no path": [i for i in range(len(pairs)) if i not in dcost]}
print("mean time per query (us) by group")
print(f"{'group':12s} {'n':>5s} " + " ".join(f"{n:>13s}" for n in names))
for g, ids in groups.items():
    print(f"{g:12s} {len(ids):5d} " + " ".join(f"{st.mean(times[n][i] for i in ids):13.0f}" for n in names))
