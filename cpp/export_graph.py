"""Export G' and query pairs for the C++ benchmark.
python3 cpp/export_graph.py  ->  cpp/graph.txt, cpp/pairs.txt"""
import itertools, math, random, sys
sys.path.insert(0, ".")
from cost_model import CostParams, build_g_prime
from data_loader import load

R = 6_371_008.8
data = load("data")
adj = build_g_prime(data.edges, CostParams())
nodes = sorted(set(adj) | {v for out in adj.values() for v, _, _ in out})
idx = {v: i for i, v in enumerate(nodes)}
lat0 = math.radians(sum(data.coords[v][0] for v in nodes) / len(nodes))
xy = {v: (R * math.radians(data.coords[v][1]) * math.cos(lat0), R * math.radians(data.coords[v][0])) for v in nodes}
edges = [(idx[u], idx[v], c) for u, out in adj.items() for v, _, c in out]
with open("cpp/graph.txt", "w") as f:
    f.write(f"{len(nodes)} {len(edges)}\n")
    for v in nodes:
        f.write(f"{xy[v][0]:.4f} {xy[v][1]:.4f}\n")
    for u, v, c in edges:
        f.write(f"{u} {v} {c:.9f}\n")
pairs = []
for seed in range(3):                       # same random pairs as benchmark_wide.py
    rng = random.Random(seed)
    pairs += [("random", idx[s], idx[t]) for s, t in (rng.sample(nodes, 2) for _ in range(10000))]
rep = {}
for r in data.entrances:
    if r["wheelchair_accessible"].lower() == "yes":
        rep.setdefault(r["building_id"], r["node_id"])
pairs += [("building", idx[s], idx[t]) for s, t in itertools.permutations(sorted(rep.values()), 2)]
with open("cpp/pairs.txt", "w") as f:
    f.write(f"{len(pairs)}\n")
    for g, s, t in pairs:
        f.write(f"{g} {s} {t}\n")
print(len(nodes), "nodes", len(edges), "edges", len(pairs), "pairs")
