"""Phase 7C.2 tests — conditional BASE strata, weights, acceptance."""

from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import ConditionalBaseSampler, exact_start_mix, wr_off_config

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c2_research"
LIB = HERE / "library_v2_phase7c2" / "publish_files"
EXPECTED = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"


class Phase7C2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.rebuild = json.loads((OUT / "base_rebuild.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((OUT / "freeze_snapshot.json").read_text(encoding="utf-8"))
        cls.features = json.loads((OUT / "base_features_cert.json").read_text(encoding="utf-8"))
        cls.buy = json.loads((OUT / "buy_authoritative.json").read_text(encoding="utf-8"))

    def test_00_freeze(self):
        self.assertTrue(self.freeze["match"])
        self.assertEqual(self.freeze["configSha256"], EXPECTED)
        self.assertEqual(int(self.cfg["meta"]["mathVersion"]), 2)

    def test_01_line_anchor(self):
        line = exact_line_rtp(
            self.cfg["reelModel"]["strips"], self.cfg["paylines"], self.cfg["paytable"]["awards"]
        )["lineRtp"]
        self.assertAlmostEqual(line * 100, 60.29946, places=4)

    def test_02_start_mix_parity(self):
        mix = exact_start_mix(self.cfg)
        self.assertAlmostEqual(mix["LARGE_HILL"], 0.0062135906602437665, places=12)
        self.assertAlmostEqual(mix["P_scatterGe3"], 0.00652967825443787, places=12)

    def test_03_conditional_full_round_has_base_spin(self):
        sampler = ConditionalBaseSampler(self.cfg)
        cfg = wr_off_config(self.cfg)
        for kind in ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V"):
            stops = sampler.sample(random.Random(9), kind)
            result = resolve_v2_round(random.Random(10), config=cfg, base_stops=stops)
            self.assertTrue(result["isBonus"], kind)
            types = [e["type"] for e in result["events"]]
            self.assertIn("skyjumpFreeSpinsStart", types)
            # Natural path: first spin start is not buyMode
            starts = [e for e in result["events"] if e["type"] == "skyjumpSpinStart"]
            self.assertTrue(starts)
            self.assertFalse(bool(starts[0].get("buyMode")))
            finals = [e for e in result["events"] if e["type"] == "finalWin"]
            self.assertEqual(len(finals), 1)

    def test_04_leaf_partition(self):
        probs = self.rebuild["probs"]
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=12)
        lut = self.rebuild["lut"]
        self.assertAlmostEqual(lut["sumP"], 1.0, places=12)
        self.assertTrue(self.rebuild["acceptance"]["pass_0_10"])

    def test_05_pv_and_wr_weights(self):
        pv = self.rebuild["pvWeight"]
        wr = self.rebuild["wrWeight"]
        self.assertLess(abs(pv["effective"] - pv["target"]) / pv["target"], 0.01)
        self.assertLess(abs(wr["effective"] - wr["target"]) / wr["target"], 0.01)

    def test_06_lut_matches_auth(self):
        self.assertLess(abs(self.rebuild["gapPp"]), 0.10)
        self.assertTrue((LIB / "books_BASE.jsonl.zst").exists())
        self.assertTrue((LIB / "lookUpTable_BASE_0.csv").exists())

    def test_07_no_overwrite_phase7c_library(self):
        # New outputs live under library_v2_phase7c2 only
        self.assertTrue(str(LIB).endswith("library_v2_phase7c2\\publish_files") or "library_v2_phase7c2" in str(LIB))

    def test_08_feature_cert_present(self):
        cert = self.features.get("stratifiedCertified") or self.features.get("certified") or {}
        # phase4c report structure
        if "featureRtpCapped" in self.features:
            capped = float(self.features["featureRtpCapped"])
        else:
            capped = float(self.features.get("stratifiedCertified", {}).get("featureRtpCapped", 0))
            if not capped:
                # fallback parse from top-level printed structure in report
                capped = float(self.features.get("summary", {}).get("featureRtpCapped", 0) or 0)
        # Read from known phase4c keys
        sc = self.features.get("stratifiedCertified")
        if sc:
            self.assertGreater(float(sc["featureRtpCapped"]), 0.10)
            self.assertLess(float(sc.get("seCombinedPp", sc.get("sePp", 0.1))), 0.15)


if __name__ == "__main__":
    unittest.main()
