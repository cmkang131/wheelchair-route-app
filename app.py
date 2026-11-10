"""Wheelchair Route App (PBL1) — Streamlit + Folium.

Components (team app design):
 1 Data loader   -> data_loader.py      (Graph Builder export)
 2 Edge cost     -> cost_model.py       (Part 1)
 3 Path finding  -> pathfinding.py      (Part 2, A*; Dijkstra for comparison)
 4 Route summary, 5 Map view, 6 Screen  -> this file
Run: bash run_mac.sh   (or: python -m streamlit run app.py)
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from cost_model import CostParams, build_g_prime, edge_cost, has_stairs
from data_loader import load
from pathfinding import a_star, dijkstra, heuristic_scale

DATA_DIR = Path(__file__).parent / "data"
STEEP = 0.0833   # 1:12, usual maximum ramp slope for wheelchairs

st.set_page_config(page_title="Wheelchair Route (Demo)", layout="wide")


@st.cache_data
def get_data(path: str):
    return load(path)


data = get_data(str(DATA_DIR))

# ---- 6. Screen: sidebar ---------------------------------------------------
st.sidebar.header("Start / destination")
choices = {}
for r in data.entrances:
    if r["wheelchair_accessible"].strip().lower() != "yes":
        continue
    label = f"{data.buildings.get(r['building_id'], r['building_id'])} · {r['name']}"
    choices.setdefault(label, r["node_id"])
labels = sorted(choices)
def _idx(name, default):
    return next((i for i, l in enumerate(labels) if l.startswith(name)), default)
start = st.sidebar.selectbox("Start", labels, index=_idx("Dormitory 21", 0))
goal = st.sidebar.selectbox("Destination", labels,
                            index=_idx("LG Cooperative", min(1, len(labels) - 1)))

st.sidebar.header("Cost model (Part 1)")
a = st.sidebar.number_input("Slope penalty a", 0.0, 100.0, 5.0, 0.5)
std = st.sidebar.number_input("Standard slope (%)", 0.0, 20.0, 5.0, 0.5) / 100
elev = st.sidebar.number_input("Elevator penalty (m)", 0.0, 500.0, 0.0, 10.0)
obs = st.sidebar.number_input("Obstacle penalty (m)", 0.0, 500.0, 0.0, 10.0)
params = CostParams(a=a, standard_slope=std, elevator_penalty=elev, obstacle_penalty=obs)

# ---- 2. Edge cost + 3. Path finding ---------------------------------------
adj = build_g_prime(data.edges, params)
alpha = heuristic_scale(data.coords, adj)
s, t = choices[start], choices[goal]



def timed(fn, runs=5):
    """Run a search several times; keep the fastest time (one run is too noisy)."""
    best = float("inf")
    for _ in range(runs):
        t0 = time.perf_counter(); res = fn(); best = min(best, time.perf_counter() - t0)
    return res, best


route, t_a = timed(lambda: a_star(data.coords, adj, s, t, alpha))
ref, t_d = timed(lambda: dijkstra(data.coords, adj, s, t))

# distance-only baseline: every allowed edge, stairs included, cost = distance
base_adj = {}
for e in data.edges:
    if str(e.get("direction_allowed", "True")).lower() == "true":
        base_adj.setdefault(e["source"], []).append((e["target"], e["edge_id"], float(e["distance_m"])))
base = dijkstra(data.coords, base_adj, s, t)

st.title("Wheelchair route finder · POSTECH (Demo)")
st.info("Demo version: graph edges are not reviewed yet, and slope penalty values are assumptions.")
st.caption(f"{start}  →  {goal}")

if not route.found:
    st.error("No stair-free route between these entrances in the current graph.")
else:
    # ---- 4. Route summary --------------------------------------------------
    rows = [dict(edge_id=e, **edge_cost(data.edge_by_id[e], params)) for e in route.edges]
    df = pd.DataFrame(rows)
    length = df.C_distance.sum()
    slopes = [data.edge_by_id[e]["slope"] for e in route.edges]
    steep = sum(1 for x in slopes if x not in ("", None) and float(x) / 100 > STEEP)
    proxies = sum(data.edge_by_id[e]["edge_type"] == "road_proxy" for e in route.edges)
    base_stairs = base.found and any(has_stairs(data.edge_by_id[e]) for e in base.edges)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Route length", f"{length:,.0f} m")
    c2.metric("Total cost", f"{route.cost:,.0f}")
    c3.metric("Slope penalty", f"{df.C_slope.sum():,.0f}")
    if base.found:
        c4.metric("Distance-only path", f"{base.cost:,.0f} m",
                  f"{length - base.cost:+,.0f} m", delta_color="off")

    warn = []
    if base_stairs:
        warn.append("The distance-only path uses stairs; this route avoids them.")
    if steep:
        warn.append(f"{steep} segment(s) steeper than 8.33% (1:12).")
    if df.slope_missing.any():
        warn.append(f"{int(df.slope_missing.sum())} segment(s) have no slope data (no penalty applied).")
    if proxies:
        warn.append(f"{proxies} segment(s) follow a road centre line, not a checked sidewalk.")
    if df.C_elevator.gt(0).any():
        warn.append("Route uses an elevator.")
    for w in warn:
        st.warning(w)

    with st.expander("A* vs Dijkstra"):
        st.table(pd.DataFrame({
            "algorithm": ["Dijkstra", "A* (straight line)"],
            "total cost": [round(x.cost, 2) for x in (ref, route)],
            "nodes expanded": [x.expanded for x in (ref, route)],
            "time (ms, best of 5)": [round(x * 1000, 2) for x in (t_d, t_a)],
        }).set_index("algorithm"))
        st.caption(f"h(v) = {alpha:.4f} × straight-line distance to the destination. "
                   f"Same cost: {math.isclose(route.cost, ref.cost, abs_tol=1e-6)}")

    # ---- 5. Map view -------------------------------------------------------
    pts = [p for e in route.edges for p in data.geometry(e)]
    m = folium.Map(location=pts[len(pts) // 2], zoom_start=16, tiles="OpenStreetMap")
    for e in data.edges:
        if has_stairs(e):
            folium.PolyLine(data.geometry(e["edge_id"]), color="#c0392b", weight=3,
                            opacity=0.7, tooltip="stairs").add_to(m)
    if base.found:
        folium.PolyLine([p for e in base.edges for p in data.geometry(e)], color="#555555",
                        weight=4, dash_array="8 8",
                        tooltip=f"distance only {base.cost:.0f} m").add_to(m)
    folium.PolyLine(pts, color="#1f5fbf", weight=6,
                    tooltip=f"accessible route {length:.0f} m").add_to(m)
    folium.Marker(data.coords[s], tooltip=start, icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(data.coords[t], tooltip=goal, icon=folium.Icon(color="red")).add_to(m)
    m.fit_bounds([[min(p[0] for p in pts), min(p[1] for p in pts)],
                  [max(p[0] for p in pts), max(p[1] for p in pts)]])
    st_folium(m, height=560, use_container_width=True, returned_objects=[])
    st.caption("Blue: accessible route · grey dashed: distance-only path · red: stairs (removed)")

    with st.expander("Edge costs on this route"):
        st.dataframe(df.round(2), use_container_width=True)
