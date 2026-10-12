"""Structural checks for Phase 6A.1 research architectures."""

from __future__ import annotations

import unittest

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase6a_engine import LADDERS as LADDERS6A
from skyjump_v2_phase6a_search import build_context, table_for
from skyjump_v2_phase6a1_search import f1_benchmark, make_spec, run_mix


class Phase6A1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = build_context(load_v2_config())

    def test_f1_weights_unchanged(self):
        spec = f1_benchmark()
        lh = spec.weights_by_tier["LARGE_HILL"]
        self.assertEqual(lh["REJUMP"], 10)
        self.assertEqual(lh["WIND_KEY"], 1)
        self.assertEqual(lh["FLIGHT_TOKEN"], 741)
        self.assertEqual(spec.rejump_arch, "R-DELAYED")
        self.assertEqual(spec.wind_arch, "W-IMMEDIATE")

    def test_architectures_run_bounded(self):
        pack = {
            "LARGE_HILL": (22, 4),
            "SKI_FLYING": (36, 10),
            "WORLD_CUP": (48, 16),
            "PERFECT_V": (60, 24),
        }
        for rejump_arch, wind_arch in (
            ("R-BATCH", "W-IMMEDIATE"),
            ("R-DELAYED", "W-NEXT-SPIN"),
            ("R-BATCH", "W-NEXT-SPIN"),
            ("R-BATCH", "W-CHARGE"),
        ):
            spec = make_spec(
                f"t_{rejump_arch}_{wind_arch}",
                pack,
                rejump_arch=rejump_arch,
                wind_arch=wind_arch,
            )
            rows = run_mix(self.ctx, spec, 80, 3)
            for row in rows:
                self.assertLessEqual(row["spins"], 40)
                self.assertLessEqual(row["capped"], 50_000)
                self.assertLessEqual(row["maxChain"], 8)
                self.assertEqual(
                    row["multiplier"],
                    row["runUp"] * row["takeoff"] * row["flight"],
                )
                for stage in (row["runUp"], row["takeoff"], row["flight"]):
                    self.assertIn(stage, LADDERS6A["K1"])

    def test_table_sum(self):
        self.assertEqual(sum(table_for((28, 6)).values()), 1000)


if __name__ == "__main__":
    unittest.main()
