"""Phase 7C.1 — BASE RTP reconciliation tests (read-only vs artifacts)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import base_trigger_mix

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c1_research"
P7C = HERE / "phase7c_research"
EXPECTED = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"


class Phase7C1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        cls.strata = json.loads((OUT / "base_lut_strata.json").read_text(encoding="utf-8"))
        cls.gap = json.loads((OUT / "lut_vs_hybrid_gap.json").read_text(encoding="utf-8"))
        cls.corr = json.loads((OUT / "corrected_stratified.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((OUT / "freeze_snapshot.json").read_text(encoding="utf-8"))
        cls.wr = json.loads((OUT / "wr_double_count_audit.json").read_text(encoding="utf-8"))

    def test_00_config_frozen(self):
        self.assertTrue(self.freeze["match"])
        self.assertEqual(self.freeze["configSha256"], EXPECTED)
        self.assertEqual(int(self.cfg["meta"]["mathVersion"]), 2)

    def test_01_line_anchor(self):
        line = exact_line_rtp(
            self.cfg["reelModel"]["strips"], self.cfg["paylines"], self.cfg["paytable"]["awards"]
        )["lineRtp"]
        self.assertAlmostEqual(line * 100, 60.29946, places=4)

    def test_02_wr_hybrid_no_double_count(self):
        self.assertEqual(self.wr["answer"], "B")
        self.assertAlmostEqual(self.wr["wrContributionPp"], 0.45694, places=4)

    def test_03_lut_partition_and_recon(self):
        self.assertTrue(self.strata["partitionPass"])
        self.assertTrue(self.strata["stratumReconMatch"])
        self.assertAlmostEqual(self.strata["sumNormalizedP"], 1.0, places=12)

    def test_04_wr_lut_weight(self):
        wr = json.loads((OUT / "wr_lut_weight.json").read_text(encoding="utf-8"))
        self.assertTrue(wr["pass"])

    def test_05_gap_explained_by_freegame_means(self):
        self.assertAlmostEqual(self.gap["sumGapPp"], self.gap["reportedLutMinusHybridPp"], delta=0.01)
        self.assertEqual(self.gap["primaryDriver"]["bucket"], "freegame_LARGE_HILL")

    def test_06_pv_weight_floor_detected(self):
        pv = next(s for s in self.strata["strata"] if s["name"] == "freegame_PERFECT_V")
        self.assertGreater(pv["normalizedP"], pv["theoreticalP"] * 2)

    def test_07_acceptance_gate_currently_fails(self):
        self.assertFalse(self.summary["acceptanceGate"]["pass"])
        self.assertGreater(abs(self.corr["lutMinusCorrectedHybridPp"]), 0.10)

    def test_08_no_economy_mutation(self):
        self.assertFalse(self.summary["liveEconomyModified"])
        buy = json.loads((P7C / "buy_modes.json").read_text(encoding="utf-8"))
        # costs unchanged provisional values
        by = {m["rgsKey"]: m for m in buy["modes"]}
        self.assertAlmostEqual(by["LARGE_HILL"]["costMultiplier"], 32.5, places=6)


if __name__ == "__main__":
    unittest.main()
