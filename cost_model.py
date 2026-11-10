"""Part 1 — edge cost model (team PBL1 design).

    For each edge e in E:
        stairs exist            -> remove e
        obstacle == BLOCKED     -> remove e
        direction not allowed   -> remove e
        C_distance = distance
        C_slope    = distance * a * max(0, slope - standard_slope)
        C_elevator = elevator penalty   (if the edge uses an elevator)
        C_obstacle = obstacle penalty   (if a non-blocking obstacle is recorded)
        C_all = C_distance + C_slope + C_elevator + C_obstacle
    Return G' = usable edges with C_all.

Slopes in edges.csv are percent (10 = 10%), so they are divided by 100.
Default a=5, standard_slope=5% reproduce the doc example (100 m, 10% -> 125).
An edge with no slope value keeps C_slope = 0 and is flagged slope_missing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostParams:
    a: float = 5.0                  # slope penalty value
    standard_slope: float = 0.05    # 5 %
    elevator_penalty: float = 0.0   # metres-equivalent, added once per elevator edge
    obstacle_penalty: float = 0.0   # metres-equivalent, non-blocking obstacle


def _true(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def has_stairs(edge: dict) -> bool:
    return (str(edge.get("stairs_status", "")).strip().lower() == "yes"
            or edge.get("edge_type") == "steps"
            or _true(edge.get("stairs")))


def is_blocked(edge: dict) -> bool:
    return str(edge.get("obstacle", "")).strip().upper() == "BLOCKED"


def slope_ratio(edge: dict) -> float | None:
    s = str(edge.get("slope", "")).strip()
    if s in {"", "nan", "None"}:
        return None
    return float(s) / 100.0


def edge_cost(edge: dict, p: CostParams) -> dict | None:
    """Return the cost breakdown for one directed edge, or None if removed."""
    if has_stairs(edge) or is_blocked(edge) or not _true(edge.get("direction_allowed", True)):
        return None
    d = float(edge["distance_m"])
    s = slope_ratio(edge)
    c_slope = 0.0 if s is None else d * p.a * max(0.0, s - p.standard_slope)
    c_elev = p.elevator_penalty if _true(edge.get("elevator")) else 0.0
    obstacle = str(edge.get("obstacle", "")).strip()
    c_obs = p.obstacle_penalty if obstacle not in {"", "nan", "None"} else 0.0
    return dict(C_distance=d, C_slope=c_slope, C_elevator=c_elev, C_obstacle=c_obs,
                final_cost=d + c_slope + c_elev + c_obs, slope_missing=s is None)


def build_g_prime(edges: list[dict], p: CostParams) -> dict[str, list[tuple[str, str, float]]]:
    """G' as an adjacency list: node -> [(next_node, edge_id, final_cost)]."""
    adj: dict[str, list[tuple[str, str, float]]] = {}
    for e in edges:
        c = edge_cost(e, p)
        if c is not None:
            adj.setdefault(e["source"], []).append((e["target"], e["edge_id"], c["final_cost"]))
    return adj
