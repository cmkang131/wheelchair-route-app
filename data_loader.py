"""Read the Graph Builder export (nodes, edges, buildings, entrances CSV)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


def _read(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


@dataclass
class CampusData:
    coords: dict[str, tuple[float, float]]
    edges: list[dict]
    edge_by_id: dict[str, dict]
    buildings: dict[str, str]
    entrances: list[dict]

    def geometry(self, edge_id: str) -> list[tuple[float, float]]:
        e = self.edge_by_id[edge_id]
        try:
            pts = json.loads(e.get("geometry_json") or "[]")
        except json.JSONDecodeError:
            pts = []
        if len(pts) < 2:
            pts = [self.coords[e["source"]], self.coords[e["target"]]]
        return [(float(a), float(b)) for a, b in pts]


def load(data_dir: str | Path) -> CampusData:
    d = Path(data_dir)
    coords = {r["node_id"]: (float(r["latitude"]), float(r["longitude"]))
              for r in _read(d / "nodes.csv")}
    edges = [e for e in _read(d / "edges.csv") if e["source"] in coords and e["target"] in coords]
    buildings = {r["building_id"]: r["name"] for r in _read(d / "buildings.csv")}
    entrances = [r for r in _read(d / "entrances.csv") if r["node_id"] in coords]
    return CampusData(coords, edges, {e["edge_id"]: e for e in edges}, buildings, entrances)
