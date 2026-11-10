"""python3 -m unittest discover tests"""

import itertools
import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cost_model import CostParams, build_g_prime, edge_cost  # noqa: E402
from data_loader import load  # noqa: E402
from pathfinding import a_star, alt, bidirectional_dijkstra, alt_heuristic, build_landmarks, dijkstra, heuristic_scale, straight  # noqa: E402


class CostTests(unittest.TestCase):
    def test_doc_example(self):
        # PBL1_DAY2: distance 100, slope 10% -> final_cost 125
        c = edge_cost(dict(distance_m="100", slope="10", stairs_status="no", edge_type="walkway",
                           direction_allowed="True"), CostParams())
        self.assertAlmostEqual(c["final_cost"], 125.0)

    def test_removed_edges(self):
        base = dict(distance_m="10", slope="0", stairs_status="no", edge_type="walkway",
                    direction_allowed="True")
        self.assertIsNone(edge_cost({**base, "stairs_status": "yes"}, CostParams()))
        self.assertIsNone(edge_cost({**base, "edge_type": "steps"}, CostParams()))
        self.assertIsNone(edge_cost({**base, "obstacle": "BLOCKED"}, CostParams()))
        self.assertIsNone(edge_cost({**base, "direction_allowed": "False"}, CostParams()))

    def test_downhill_and_missing_slope(self):
        base = dict(distance_m="10", stairs_status="no", edge_type="walkway", direction_allowed="True")
        self.assertEqual(edge_cost({**base, "slope": "-20"}, CostParams())["final_cost"], 10)
        c = edge_cost({**base, "slope": ""}, CostParams())
        self.assertEqual(c["final_cost"], 10)
        self.assertTrue(c["slope_missing"])


class CampusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load(ROOT / "data")
        cls.adj = build_g_prime(cls.data.edges, CostParams())
        cls.alpha = heuristic_scale(cls.data.coords, cls.adj)

    def test_heuristic_consistent(self):
        c = self.data.coords
        for u, out in self.adj.items():
            for v, _, w in out:
                self.assertLessEqual(self.alpha * straight(c, u, v), w + 1e-9)

    def test_astar_matches_dijkstra(self):
        nodes = sorted({e["node_id"] for e in self.data.entrances})
        for s, t in itertools.combinations(nodes, 2):
            a = a_star(self.data.coords, self.adj, s, t, self.alpha)
            d = dijkstra(self.data.coords, self.adj, s, t)
            self.assertEqual(a.found, d.found)
            if a.found:
                self.assertTrue(math.isclose(a.cost, d.cost, abs_tol=1e-6))
                self.assertLessEqual(a.expanded, d.expanded)

    def test_alt_matches_dijkstra(self):
        lm = build_landmarks(self.adj, k=8)
        nodes = sorted({e["node_id"] for e in self.data.entrances})
        for s, t in itertools.combinations(nodes, 2):
            a = alt(self.data.coords, self.adj, s, t, lm, self.alpha)
            d = dijkstra(self.data.coords, self.adj, s, t)
            self.assertEqual(a.found, d.found)
            if a.found:
                self.assertTrue(math.isclose(a.cost, d.cost, abs_tol=1e-6))

    def test_bidirectional_matches_dijkstra(self):
        nodes = sorted({e["node_id"] for e in self.data.entrances})
        for s, t in itertools.combinations(nodes, 2):
            b = bidirectional_dijkstra(self.adj, s, t)
            d = dijkstra(self.data.coords, self.adj, s, t)
            self.assertEqual(b.found, d.found)
            if b.found:
                self.assertTrue(math.isclose(b.cost, d.cost, abs_tol=1e-6))
                total = 0.0
                for (u, v), eid in zip(zip(b.nodes, b.nodes[1:]), b.edges):
                    e = self.data.edge_by_id[eid]
                    self.assertEqual((e["source"], e["target"]), (u, v))
                    total += edge_cost(e, CostParams())["final_cost"]
                self.assertTrue(math.isclose(total, b.cost, abs_tol=1e-6))

    def test_alt_heuristic_consistent(self):
        lm = build_landmarks(self.adj, k=8)
        rng = random.Random(1)
        for t in rng.sample(sorted(self.adj), 20):
            h = alt_heuristic(self.data.coords, lm, t, self.alpha)
            self.assertEqual(h(t), 0.0)
            for u, out in self.adj.items():
                for v, _, w in out:
                    if math.isfinite(h(v)):
                        self.assertLessEqual(h(u), w + h(v) + 1e-6)

    def test_route_is_stair_free_and_connected(self):
        rng = random.Random(0)
        nodes = [e["node_id"] for e in self.data.entrances]
        for _ in range(50):
            s, t = rng.sample(nodes, 2)
            r = a_star(self.data.coords, self.adj, s, t, self.alpha)
            if not r.found:
                continue
            total = 0.0
            for (u, v), eid in zip(zip(r.nodes, r.nodes[1:]), r.edges):
                e = self.data.edge_by_id[eid]
                self.assertEqual((e["source"], e["target"]), (u, v))
                self.assertNotEqual(e["stairs_status"], "yes")
                total += edge_cost(e, CostParams())["final_cost"]
            self.assertAlmostEqual(total, r.cost, places=6)


if __name__ == "__main__":
    unittest.main()
