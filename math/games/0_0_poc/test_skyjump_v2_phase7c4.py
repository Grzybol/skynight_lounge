"""Phase 7C.4 production math freeze tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c4_common import EXPECTED_SHA_PRE, OUT, PRICE_A_DESIGN, sha_file

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
STAGING = REPO / "stake-upload-final" / "math"
MANIFEST = HERE / "phase7c4_release_manifest.json"
CFG = HERE / "skyjump_v2_config.json"
V1_CFG = HERE / "skyjump_config.json"
MODES = ("BASE", "LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")


class TestPhase7C4(unittest.TestCase):
    def test_freeze_snapshot_pre_promote(self):
        snap = json.loads((OUT / "freeze_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snap["prePromotionConfigSha256"], EXPECTED_SHA_PRE)
        self.assertTrue(snap["match"])
        self.assertEqual(int(snap["mathVersionBefore"]), 1)

    def test_base_lut_gate(self):
        base = json.loads((OUT / "base_lut_report.json").read_text(encoding="utf-8"))
        self.assertTrue(base["pass_0_05"])
        self.assertTrue(base["ceilingPass"])
        self.assertTrue(base["dualPathMatch"])
        self.assertLessEqual(base["gapPp"], 0.05)

    def test_buy_lut_and_cross_mode(self):
        buy = json.loads((OUT / "buy_lut_report.json").read_text(encoding="utf-8"))
        self.assertTrue(buy["allGatesPass"])
        self.assertTrue(buy["crossModeActual"]["spreadPass"])
        self.assertTrue(buy["crossModeActual"]["ceilingPass"])
        self.assertLessEqual(buy["crossModeActual"]["spreadPp"], 0.50)
        for t, design in PRICE_A_DESIGN.items():
            self.assertAlmostEqual(buy["pricing"]["costs"][t], design, places=1)

    def test_validation(self):
        val = json.loads((OUT / "validation_report.json").read_text(encoding="utf-8"))
        self.assertTrue(val["pass"])
        self.assertTrue(val["replayPass"])
        self.assertTrue(val["grainPass"])
        self.assertTrue(val["capPass"])

    def test_promoted_config(self):
        cfg = load_v2_config()
        self.assertEqual(int(cfg["meta"]["mathVersion"]), 2)
        self.assertIn("buyModes", cfg)
        self.assertEqual(cfg["buyModes"]["LARGE_HILL"]["costMultiplier"], 30.2)
        self.assertEqual(cfg["buyModes"]["SKI_FLYING"]["costMultiplier"], 196.9)
        self.assertEqual(cfg["buyModes"]["WORLD_CUP"]["costMultiplier"], 412.8)
        self.assertEqual(cfg["buyModes"]["PERFECT_V"]["costMultiplier"], 1369.1)
        v1 = json.loads(V1_CFG.read_text(encoding="utf-8"))
        self.assertEqual(int(v1["meta"]["mathVersion"]), 3)

    def test_staging_clean(self):
        self.assertTrue(STAGING.exists())
        names = {p.name for p in STAGING.iterdir() if p.is_file()}
        wanted = {
            "index.json",
            *[f"books_{m}.jsonl.zst" for m in MODES],
            *[f"lookUpTable_{m}_0.csv" for m in MODES],
        }
        self.assertEqual(names, wanted)
        index = json.loads((STAGING / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([m["name"] for m in index["modes"]], list(MODES))
        # no V1 legacy keys
        for m in index["modes"]:
            self.assertNotIn(m["name"], {"MULT_10_100", "MULT_20_200"})

    def test_release_manifest(self):
        self.assertTrue(MANIFEST.exists())
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(man["classification"], "PRODUCTION MATH FROZEN")
        self.assertEqual(man["mathVersion"]["new"], 2)
        self.assertEqual(man["configSha"]["before"], EXPECTED_SHA_PRE)
        self.assertEqual(man["devResearchLeak"], "NONE")
        self.assertEqual(sha_file(CFG), man["configSha"]["final"])


if __name__ == "__main__":
    unittest.main()
