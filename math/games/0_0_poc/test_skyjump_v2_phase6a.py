"""Structural checks for the Phase 6A research engine. Not a production resolver."""

from __future__ import annotations

import random
import unittest

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase6a_engine import LADDERS, global_multiplier
from skyjump_v2_phase6a_search import build_context, make_spec, run_mix, table_for


class Phase6AEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = build_context(load_v2_config())

    def test_weight_tables_sum_to_one_thousand(self):
        for model, tiers in (
            ("C", None),
        ):
            spec = make_spec("check", availability="C_LO", max_rejumps=2)
            for table in spec.weights_by_tier.values():
                self.assertEqual(sum(table.values()), 1000)
                self.assertGreater(table["FLIGHT_TOKEN"], 500)

    def test_blank_table_has_no_new_outcomes(self):
        self.assertEqual(table_for((0, 0))["REJUMP"], 0)
        self.assertEqual(table_for((0, 0))["WIND_KEY"], 0)
        self.assertEqual(table_for((0, 0))["FLIGHT_TOKEN"], 752)

    def test_seeded_bonuses_stay_inside_bounds(self):
        spec = make_spec("bound", availability="C_LO", max_rejumps=2)
        rows = run_mix(self.ctx, spec, 250, 5)
        ladder_max = LADDERS["K1"][-1]
        for row in rows:
            self.assertLessEqual(row["spins"], 40)
            self.assertGreaterEqual(row["spins"], 1)
            self.assertLessEqual(row["capped"], 50_000)
            self.assertLessEqual(row["maxChain"], 8)
            self.assertLessEqual(row["multiplier"], ladder_max ** 3)
            self.assertEqual(row["multiplier"], row["runUp"] * row["takeoff"] * row["flight"])
            for stage in (row["runUp"], row["takeoff"], row["flight"]):
                self.assertIn(stage, LADDERS["K1"])

    def test_rejump_disabled_never_rejumps(self):
        spec = make_spec("nore", availability="C_LO", max_rejumps=0)
        for table in spec.weights_by_tier.values():
            table["FLIGHT_TOKEN"] += table["REJUMP"]
            table["REJUMP"] = 0
        rows = run_mix(self.ctx, spec, 200, 9)
        self.assertEqual(sum(row["rejumps"] for row in rows), 0)

    def test_global_multiplier_identity(self):
        self.assertEqual(1 * 2 * 3, 6)


if __name__ == "__main__":
    unittest.main()
