"""Paired statistics on cpp/results.csv.  python3 cpp/analyze.py"""
import csv, numpy as np
from collections import defaultdict
from scipy.stats import wilcoxon

rows = defaultdict(dict)
for r in csv.DictReader(open("cpp/results.csv")):
    rows[(r["group"], r["s"], r["t"])][r["algo"]] = (float(r["cost"]), int(r["expanded"]), float(r["ns"]))
bad = sum(1 for v in rows.values() if max(x[0] for x in v.values()) - min(x[0] for x in v.values()) > 1e-3)
print(f"queries {len(rows)}, cost mismatches {bad}")
rng = np.random.default_rng(0)
A = ["Dijkstra", "A*", "Bidirectional"]
def report(name, keys):
    T = {a: np.array([rows[k][a][2] for k in keys]) / 1000 for a in A}      # us
    N = {a: np.array([rows[k][a][1] for k in keys]) for a in A}
    print(f"\n== {name}: {len(keys)} queries")
    for a in A:
        print(f"{a:13s} nodes {N[a].mean():6.1f} ({100*N[a].sum()/N['Dijkstra'].sum():5.1f}%)  "
              f"mean {T[a].mean():6.2f}us  median {np.median(T[a]):6.2f}  p99 {np.percentile(T[a],99):6.2f}")
    for a, b in [("A*", "Dijkstra"), ("Bidirectional", "Dijkstra"), ("A*", "Bidirectional")]:
        ratio = T[a] / T[b]
        boot = [np.exp(np.log(ratio[rng.integers(0, len(ratio), len(ratio))]).mean()) for _ in range(2000)]
        p = wilcoxon(T[a], T[b]).pvalue
        print(f"{a} vs {b}: faster on {100*(T[a]<T[b]).mean():5.1f}% of queries, "
              f"time ratio {np.exp(np.log(ratio).mean()):.3f} (95% CI {np.percentile(boot,2.5):.3f}-{np.percentile(boot,97.5):.3f}), "
              f"Wilcoxon p={p:.1e}")
    return T, N
out = {}
for g in ["random", "building"]:
    reach = [k for k in rows if k[0] == g and rows[k]["Dijkstra"][0] >= 0]
    nop = [k for k in rows if k[0] == g and rows[k]["Dijkstra"][0] < 0]
    out[g] = report(f"{g}, has route", reach)
    if nop: report(f"{g}, no route", nop)

# figure: mean time vs route cost (has route), and A*/Dijkstra ratio histogram
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
keys = [k for k in rows if k[0] == "random" and rows[k]["Dijkstra"][0] >= 0]
cost = np.array([rows[k]["Dijkstra"][0] for k in keys])
bins = np.linspace(0, np.percentile(cost, 99), 13); mid = (bins[1:] + bins[:-1]) / 2
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for a, c in zip(A, ["#888888", "#d1495b", "#00798c"]):
    t = np.array([rows[k][a][2] for k in keys]) / 1000
    ax[0].plot(mid, [t[(cost >= lo) & (cost < hi)].mean() for lo, hi in zip(bins[:-1], bins[1:])], "o-", color=c, label=a)
ax[0].set_xlabel("route cost"); ax[0].set_ylabel("mean time per query (μs)"); ax[0].legend(); ax[0].set_title("Time vs route length (C++, 26,552 queries)")
r = np.array([rows[k]["A*"][2] / rows[k]["Dijkstra"][2] for k in keys])
ax[1].hist(np.clip(r, 0, 2), bins=40, color="#d1495b"); ax[1].axvline(1, color="k", ls="--")
ax[1].set_xlabel("A* time / Dijkstra time  (<1: A* faster)"); ax[1].set_ylabel("queries"); ax[1].set_title(f"A* faster on {100*(r<1).mean():.1f}% of queries")
plt.tight_layout(); plt.savefig("cpp/astar_vs_dijkstra.png", dpi=150)
