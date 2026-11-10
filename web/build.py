"""Rebuild web/index.html from data/*.csv:  python3 web/build.py"""
import csv, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(n): return list(csv.DictReader(open(ROOT / "data" / n, encoding="utf-8-sig")))
N, E, B, EN = read("nodes.csv"), read("edges.csv"), read("buildings.csv"), read("entrances.csv")
lat0 = sum(float(n["latitude"]) for n in N) / len(N); lon0 = sum(float(n["longitude"]) for n in N) / len(N)
kx, ky = math.cos(math.radians(lat0)) * 111320, 110540
xy = lambda la, lo: [round((lo - lon0) * kx, 1), round(-(la - lat0) * ky, 1)]
nodes = {n["node_id"]: (float(n["latitude"]), float(n["longitude"])) for n in N}
nid = {n: i for i, n in enumerate(nodes)}
geoms, glist, edges = {}, [], []
for e in E:
    if e["source"] not in nodes or e["target"] not in nodes: continue
    key = tuple(sorted([e["source"], e["target"]])) + (round(float(e["distance_m"]), 1),)
    if key not in geoms:
        pts = json.loads(e["geometry_json"] or "[]") or [nodes[e["source"]], nodes[e["target"]]]
        geoms[key] = len(glist); glist.append([c for p in pts for c in xy(float(p[0]), float(p[1]))])
    stairs = e["stairs_status"].lower() == "yes" or e["edge_type"] == "steps" or e["stairs"].lower() == "true"
    edges.append([nid[e["source"]], nid[e["target"]], float(e["distance_m"]),
                  None if e["slope"] == "" else float(e["slope"]), int(stairs),
                  int(e["direction_allowed"].lower() == "true"), e["edge_type"],
                  int(e["elevator"].lower() == "true"), e["obstacle"] or "", geoms[key], e["edge_id"]])
bl = {b["building_id"]: b["name"] for b in B}
ents = [[bl.get(r["building_id"], r["building_id"]), r["name"], nid[r["node_id"]]]
        for r in EN if r["wheelchair_accessible"].lower() == "yes" and r["node_id"] in nid]
data = dict(nodes=[[round(a, 7), round(b, 7)] + xy(a, b) for a, b in nodes.values()],
            edges=edges, geoms=glist, entrances=ents)
t = (ROOT / "web" / "template.html").read_text()
(ROOT / "web" / "index.html").write_text(t.replace("__DATA__", json.dumps(data, separators=(",", ":"))))
print("wrote web/index.html")
