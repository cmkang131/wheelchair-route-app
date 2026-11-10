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
    h = (lambda v: alpha * haversine(coords[v], coords[t])) if alpha > 0 else (lambda v: 0.0)
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


def a_star(coords, adj, s, t, alpha=None) -> Route:
    return search(coords, adj, s, t, heuristic_scale(coords, adj) if alpha is None else alpha)


def dijkstra(coords, adj, s, t) -> Route:
    return search(coords, adj, s, t, 0.0)
