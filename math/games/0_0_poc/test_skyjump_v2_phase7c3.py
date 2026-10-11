"""Phase 7C.3 smoke tests — precision scaffolding (no live economy mutation)."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c3_common import (
    EXPECTED_SHA,
    LH_STRATA,
    classify_bonus_row,
    leaf_probabilities,
    lh_stratum_id,
    paid_wr_p,
    sha_config,
)
from skyjump_v2_phase7c2_conditional import exact_start_mix

HERE = Path(__file__).resolve().parent


class TestPhase7C3(unittest.TestCase):
    def test_config_frozen(self):
        cfg = load_v2_config()
        self.assertEqual(int(cfg["meta"]["mathVersion"]), 2)
        # 7C.3 pre-promote pin preserved in freeze snapshot (historical)
        snap = json.loads((HERE / "phase7c3_research" / "freeze_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snap["liveConfigSha256"], EXPECTED_SHA)
        self.assertTrue(snap["shaMatch"])

    def test_line_anchor(self):
        cfg = load_v2_config()
        line = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], cfg["paytable"]["awards"])["lineRtp"]
        self.assertAlmostEqual(line * 100, 60.29946, places=4)

    def test_leaf_partition_sums(self):
        cfg = load_v2_config()
        mix = exact_start_mix(cfg)
        probs = leaf_probabilities(mix, paid_wr_p())
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=12)

    def test_lh_strata_mece_labels(self):
        self.assertEqual(len(LH_STRATA), len(set(LH_STRATA)))
        # synthetic row classification
        row = {
            "coll": "BOTH",
            "gfmBucket": "2_4",
            "rejBucket": "0",
            "x": 1,
            "trig": 0,
            "bonusOnly": 1,
            "gfm": 3,
            "rej": 0,
            "floor": 1,
            "cap": False,
            "length": 10,
            "judges": 1,
            "headJudges": 1,
        }
        self.assertEqual(lh_stratum_id(row), "BOTH_GFM2P")

    def test_research_dir(self):
        self.assertTrue((HERE / "phase7c3_research" / "freeze_snapshot.json").exists())
        snap = json.loads((HERE / "phase7c3_research" / "freeze_snapshot.json").read_text(encoding="utf-8"))
        self.assertTrue(snap["shaMatch"])


if __name__ == "__main__":
    unittest.main()
