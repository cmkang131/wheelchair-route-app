"""Part 2 — A* (and Dijkstra for comparison) on G'.

f(v) = g(v) + h(v),  h(v) = alpha * D(v, t)
D     = Haversine straight-line distance (m)
alpha = min over edges of final_cost(e) / D(e)  (<= 1)

Every edge then satisfies alpha*D(u,v) <= cost(u,v); with the triangle inequality
h(u) <= cost(u,v) + h(v), so h is consistent and A* returns the optimal cost.
(alpha is needed because the export rounds distance_m to mm, so a few edges are
slightly shorter than their Haversine distance; alpha is about 0.999.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from heapq import heappop, heappush

R = 6_371_008.8


def haversine(p: tuple[float, float], q: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = p, q
    dla, dlo = math.radians(la2 - la1), math.radians(lo2 - lo1)
    x = (math.sin(dla / 2) ** 2 + math.cos(math.radians(la1))
         * math.cos(math.radians(la2)) * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(min(1.0, x)))


def heuristic_scale(coords, adj) -> float:
    a = math.inf
    for u, out in adj.items():
        for v, _, c in out:
            d = haversine(coords[u], coords[v])
            if d > 0:
                a = min(a, c / d)
    return 0.0 if a is math.inf else min(a, 1.0)


@dataclass
class Route:
    found: bool
    cost: float = math.inf
    nodes: list[str] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)
    expanded: int = 0          # nodes popped and processed


def search(coords, adj, s: str, t: str, alpha: float = 0.0) -> Route:
    """alpha > 0: A*.  alpha = 0: Dijkstra (h = 0)."""
    if s == t:
        return Route(True, 0.0, [s], [], 0)
    if alpha > 0:
        tc, memo = coords[t], {}
        def h(v):                       # cache: each node's h is computed once
            if v not in memo:
                memo[v] = alpha * haversine(coords[v], tc)
            return memo[v]
    else:
        def h(v):
            return 0.0
    g = {s: 0.0}
    parent: dict[str, tuple[str, str]] = {}
    closed: set[str] = set()
    heap = [(h(s), 0, s)]
    seq = 1
    while heap:
        _, _, u = heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        if u == t:
            nodes, edges = [t], []
            while nodes[-1] != s:
                p, e = parent[nodes[-1]]
                edges.append(e)
                nodes.append(p)
            return Route(True, g[t], nodes[::-1], edges[::-1], len(closed))
        for v, e, c in adj.get(u, ()):
            ng = g[u] + c
            if ng < g.get(v, math.inf):
                g[v] = ng
                parent[v] = (u, e)
                heappush(heap, (ng + h(v), seq, v))
                seq += 1
    return Route(False, expanded=len(closed))


def search_h(adj, s: str, t: str, h) -> Route:
    """A* with any consistent heuristic function h(v)."""
    if s == t:
        return Route(True, 0.0, [s], [], 0)
    g = {s: 0.0}
    parent: dict[str, tuple[str, str]] = {}
    closed: set[str] = set()
    heap = [(h(s), 0, s)]
    seq = 1
    while heap:
        f, _, u = heappop(heap)
        if u in closed:
            continue
        if math.isinf(f):
            break                   # every remaining node is proven unable to reach t
        closed.add(u)
        if u == t:
            nodes, edges = [t], []
            while nodes[-1] != s:
                p, e = parent[nodes[-1]]
                edges.append(e)
                nodes.append(p)
            return Route(True, g[t], nodes[::-1], edges[::-1], len(closed))
        for v, e, c in adj.get(u, ()):
            ng = g[u] + c
            if ng < g.get(v, math.inf):
                g[v] = ng
                parent[v] = (u, e)
                heappush(heap, (ng + h(v), seq, v))
                seq += 1
    return Route(False, expanded=len(closed))


# ---------------------------------------------------------------------------
# ALT = A* + Landmarks + Triangle inequality
#
# Precompute, for a few landmarks L, the exact costs d(L, v) and d(v, L) for
# every node v (one Dijkstra on G' and one on reversed G' per landmark).
# Triangle inequality on shortest-path costs gives two lower bounds on d(v, t):
#     d(L, t) <= d(L, v) + d(v, t)   ->   d(v, t) >= d(L, t) - d(L, v)
#     d(v, L) <= d(v, t) + d(t, L)   ->   d(v, t) >= d(v, L) - d(t, L)
# h(v) = max(0, alpha*D(v,t), all landmark bounds). Each bound is a consistent
# potential, and a max of consistent heuristics is consistent, so ALT returns
# the same optimal cost as Dijkstra.
# ---------------------------------------------------------------------------

def _all_costs(adj, src) -> dict[str, float]:
    dist = {src: 0.0}
    heap = [(0.0, src)]
    done = set()
    while heap:
        d, u = heappop(heap)
        if u in done:
            continue
        done.add(u)
        for v, _, c in adj.get(u, ()):
            nd = d + c
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heappush(heap, (nd, v))
    return dist


def _reverse(adj):
    rev: dict[str, list] = {}
    for u, out in adj.items():
        for v, e, c in out:
            rev.setdefault(v, []).append((u, e, c))
    return rev


@dataclass
class Landmarks:
    ids: list[str]
    to: list[dict[str, float]]     # to[i][v]   = d(L_i, v)
    frm: list[dict[str, float]]    # frm[i][v]  = d(v, L_i)


def build_landmarks(adj, k: int = 8, seed_node: str | None = None) -> Landmarks:
    """Farthest-point selection: each new landmark is the node farthest (by cost)
    from the landmarks chosen so far, so they spread to the campus edges."""
    nodes = set(adj) | {v for out in adj.values() for v, _, _ in out}
    rev = _reverse(adj)
    start = seed_node or max(nodes, key=lambda v: len(adj.get(v, ())))
    # largest strongly reachable area from the start
    reach = _all_costs(adj, start)
    nearest = {v: math.inf for v in reach}
    ids, to, frm = [], [], []
    cur = max(reach, key=reach.get)
    for _ in range(k):
        ids.append(cur)
        d_to, d_from = _all_costs(adj, cur), _all_costs(rev, cur)
        to.append(d_to)
        frm.append(d_from)
        for v in nearest:
            nearest[v] = min(nearest[v], d_to.get(v, math.inf) + d_from.get(v, math.inf))
        cand = [v for v in nearest if math.isfinite(nearest[v]) and v not in ids]
        if not cand:
            break
        cur = max(cand, key=nearest.get)
    return Landmarks(ids, to, frm)


def alt_heuristic(coords, lm: Landmarks, t: str, alpha: float):
    fwd = [(d, d[t]) for d in lm.to if t in d]          # landmarks that reach t
    bwd = [(d, d[t]) for d in lm.frm if t in d]         # landmarks t can reach
    tc = coords[t]
    memo: dict[str, float] = {}

    def h(v):
        if v in memo:
            return memo[v]
        best = alpha * haversine(coords[v], tc) if alpha > 0 else 0.0
        for d, dlt in fwd:
            best = max(best, dlt - d.get(v, math.inf))   # -inf if L cannot reach v
        for d, dtl in bwd:
            best = max(best, d.get(v, math.inf) - dtl)   # +inf: v cannot reach t
        memo[v] = best
        return best
    return h


def alt(coords, adj, s, t, lm: Landmarks, alpha=None) -> Route:
    a = heuristic_scale(coords, adj) if alpha is None else alpha
    return search_h(adj, s, t, alt_heuristic(coords, lm, t, a))


# ---------------------------------------------------------------------------
# Bidirectional Dijkstra
#
# Search forward from s on G' and backward from t on reversed G' at the same
# time, always advancing the side with the smaller queue top. mu is the best
# s-t cost seen so far through any edge joining the two searches. Stop when
# top_f + top_b >= mu: any unseen path must cost at least top_f + top_b, so mu
# is optimal. Each side only grows a ball of radius about d(s,t)/2.
# ---------------------------------------------------------------------------

def bidirectional_dijkstra(adj, s: str, t: str, rev=None) -> Route:
    if s == t:
        return Route(True, 0.0, [s], [], 0)
    rev = rev if rev is not None else _reverse(adj)
    dist = ({s: 0.0}, {t: 0.0})
    par: tuple[dict, dict] = ({}, {})
    done = (set(), set())
    heaps = ([(0.0, s)], [(0.0, t)])
    graphs = (adj, rev)
    mu, meet = math.inf, None
    while heaps[0] and heaps[1]:
        if heaps[0][0][0] + heaps[1][0][0] >= mu:
            break
        side = 0 if heaps[0][0][0] <= heaps[1][0][0] else 1
        d, u = heappop(heaps[side])
        if u in done[side]:
            continue
        done[side].add(u)
        other = dist[1 - side]
        for v, e, c in graphs[side].get(u, ()):
            nd = d + c
            if nd < dist[side].get(v, math.inf):
                dist[side][v] = nd
                par[side][v] = (u, e)
                heappush(heaps[side], (nd, v))
            if v in other and nd + other[v] < mu:
                mu, meet = nd + other[v], v
    expanded = len(done[0]) + len(done[1])
    if meet is None:
        return Route(False, expanded=expanded)
    left, edges = [meet], []
    while left[-1] != s:
        p, e = par[0][left[-1]]
        edges.append(e)
        left.append(p)
    nodes, edges = left[::-1], edges[::-1]
    cur = meet
    while cur != t:
        n, e = par[1][cur]          # reversed edge (n <- cur) is original cur -> n
        edges.append(e)
        nodes.append(n)
        cur = n
    return Route(True, mu, nodes, edges, expanded)


def a_star(coords, adj, s, t, alpha=None) -> Route:
    return search(coords, adj, s, t, heuristic_scale(coords, adj) if alpha is None else alpha)


def dijkstra(coords, adj, s, t) -> Route:
    return search(coords, adj, s, t, 0.0)
