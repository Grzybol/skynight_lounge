"""Phase 7B — PT2H_LADDER + BODY1 + WR-C H2 promotion tests."""

from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import new_bonus_state, resolve_fs_spin
from skyjump_v2_resolve import resolve_v2_base
from skyjump_v2_world_record import choose_wr_position, try_world_record, wr_probability

HERE = Path(__file__).resolve().parent
ART_PT2H = HERE / "phase7a2_research" / "pt2h_awards.json"
ART_CERT = HERE / "phase7a2_research" / "certification.json"
FREEZE = HERE / "phase7b_research" / "pre_promotion_freeze.json"
CFG_PATH = HERE / "skyjump_v2_config.json"
WR_SAMPLES = HERE / "skyjump_v2_wr_samples.json"
SYMBOLS = ["P1", "P2", "P3", "M1", "M2", "M3", "L1", "L2", "L3"]
ORDER = ["P1", "P2", "P3", "M1", "M2", "M3", "L1", "L2", "L3"]
TIERS = ["LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V"]
INTENSITY = {"LARGE_HILL": 1, "SKI_FLYING": 3, "WORLD_CUP": 6, "PERFECT_V": 12}


class Phase7BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.pt2h = json.loads(ART_PT2H.read_text(encoding="utf-8"))
        cls.freeze = json.loads(FREEZE.read_text(encoding="utf-8"))

    def test_00_pre_promotion_certified_stack(self):
        stack = self.freeze["certifiedStack"]
        self.assertAlmostEqual(stack["BASE"], 71.212, places=3)
        self.assertAlmostEqual(stack["Phase5B"], 17.92705, places=5)
        self.assertAlmostEqual(stack["Phase6"], 4.689, places=3)
        self.assertAlmostEqual(stack["total"], 93.828, places=3)

    def test_01_pt2h_exact_awards(self):
        live = self.cfg["paytable"]["awards"]
        art = self.pt2h["awards"]
        self.assertEqual(self.cfg["paytable"]["candidateOrigin"], "PT2H_LADDER")
        for sym in SYMBOLS:
            for oak in ("3", "4", "5"):
                self.assertAlmostEqual(float(live[sym][oak]), float(art[sym][oak]), places=9)

    def test_02_hierarchy_and_mono_and_grain(self):
        awards = self.cfg["paytable"]["awards"]
        for oak in ("3", "4", "5"):
            vals = [float(awards[s][oak]) for s in ORDER]
            for a, b in zip(vals, vals[1:]):
                self.assertGreaterEqual(a, b - 1e-12, f"hierarchy fail {oak}")
        for sym in SYMBOLS:
            a3, a4, a5 = (float(awards[sym][k]) for k in ("3", "4", "5"))
            self.assertLessEqual(a3, a4 + 1e-12)
            self.assertLessEqual(a4, a5 + 1e-12)
            for v in (a3, a4, a5):
                self.assertAlmostEqual(round(v * 10) / 10, v, places=9)

    def test_03_body1_exact_and_scope(self):
        ft = self.cfg["flightTokens"]
        self.assertEqual(ft.get("candidateOrigin") or ft.get("bodyCandidate"), "BODY1")
        frozen_w = {int(k): int(v) for k, v in self.freeze["tierWeights"].items()}
        live_weights = {int(k): int(row["weight"]) for k, row in ft["tiers"].items()}
        self.assertEqual(live_weights[1], frozen_w[1] - 40)
        self.assertEqual(live_weights[2], frozen_w[2] + 40)
        for tier in (3, 4, 5, 6):
            self.assertEqual(live_weights[tier], frozen_w[tier])
        self.assertEqual(ft["valueWeights"]["1"], {"1": 90, "2": 6, "3": 3, "4": 1})
        self.assertEqual(ft["valueWeights"]["2"], {"5": 22, "10": 4, "15": 2})
        self.assertEqual(
            {str(k): int(v) for k, v in ft["valueWeights"]["5"].items()},
            {str(k): int(v) for k, v in self.freeze["vw5"].items()},
        )
        self.assertEqual(
            {str(k): int(v) for k, v in ft["valueWeights"]["6"].items()},
            {str(k): int(v) for k, v in self.freeze["vw6"].items()},
        )

    def test_04_phase6_mystery_weights_unchanged(self):
        live = self.cfg["freeSpins"]["phase6"]["packs"]
        frozen = self.freeze["phase6"]["packs"]
        self.assertEqual(live, frozen)
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["candidateOrigin"], "P6A1_E_E1")
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["stageRule"], "W2_PURE")
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["maxRejumpsPerSpin"], 2)
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["maxFeatureChainDepth"], 8)

    def test_05_wr_config_h2(self):
        wr = self.cfg["worldRecord"]
        self.assertTrue(wr["enabled"])
        self.assertEqual(wr["architecture"], "WR-C")
        self.assertEqual(wr["candidateOrigin"], "H2")
        self.assertEqual(wr["availability"], "FREE_SPINS_ONLY")
        self.assertEqual(wr["symbolId"], "SPECIAL_WORLD_RECORD")
        cert = json.loads(ART_CERT.read_text(encoding="utf-8"))
        h2 = cert["candidates"]["H2"]["wr"]
        self.assertAlmostEqual(float(wr["c"]), float(h2["c"]), places=18)
        for tier in TIERS:
            self.assertAlmostEqual(
                float(wr["byTierPSpin"][tier]), float(h2["byTierPSpin"][tier]), places=18
            )
            self.assertEqual(int(wr["tierRelativeIntensity"][tier]), INTENSITY[tier])

    def test_06_wr_fs_only_not_base(self):
        base = resolve_v2_base(random.Random(1), config=self.cfg)
        self.assertNotIn("worldRecord", base)
        events = resolve_v2_round(random.Random(2), config=self.cfg)["events"]
        if not any(e["type"] == "skyjumpFreeSpinsStart" for e in events):
            self.assertFalse(any(e["type"] == "skyjumpWorldRecord" for e in events))

    def test_07_wr_position_center_and_fallback(self):
        board = [["L3"] * 5 for _ in range(5)]
        self.assertEqual(choose_wr_position(board, "S"), {"reel": 2, "row": 2})
        board[2][2] = "S"
        board[0][0] = "S"  # skip first cell
        board[0][1] = "L1"
        self.assertEqual(choose_wr_position(board, "S"), {"reel": 0, "row": 1})

    def test_08_wr_fill_to_cap_and_zero_at_cap(self):
        class R0:
            def random(self):
                return 0.0

        board = [["L3"] * 5 for _ in range(5)]
        hit = try_world_record(
            R0(),
            board=board,
            config=self.cfg,
            bonus_tier="LARGE_HILL",
            free_spin_index=1,
            accrued_round_win_x=100.0,
            free_spins_remaining_before_consume=8,
        )
        self.assertIsNotNone(hit)
        self.assertAlmostEqual(hit["worldRecordIncrementX"], 49900.0)
        self.assertAlmostEqual(hit["finalRoundWinX"], 50000.0)
        hit2 = try_world_record(
            R0(),
            board=board,
            config=self.cfg,
            bonus_tier="LARGE_HILL",
            free_spin_index=1,
            accrued_round_win_x=50000.0,
            free_spins_remaining_before_consume=3,
        )
        self.assertAlmostEqual(hit2["worldRecordIncrementX"], 0.0)
        self.assertTrue(hit2["terminated"])

    def test_09_wr_forced_terminates_no_lines(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["worldRecord"]["byTierPSpin"] = {t: 1.0 for t in TIERS}
        candidate = bonus_candidate_from_config(cfg)
        paying = live_candidate_from_config(cfg)
        state = new_bonus_state("LARGE_HILL", initial_spins=10)
        result = resolve_fs_spin(
            random.Random(9),
            state,
            candidate,
            config=cfg,
            paying_candidate=paying,
            round_prior_win_x=0.0,
        )
        self.assertIn("worldRecord", result)
        self.assertEqual(result["wins"], [])
        self.assertEqual(result["lineWinX"], 0.0)
        self.assertTrue(state.maxWinReached)
        self.assertEqual(state.freeSpinsRemaining, 0)

    def test_10_t6_not_special_wr(self):
        t6 = self.cfg["flightTokens"]["tiers"]["6"]
        self.assertEqual(t6["id"], "T6")
        self.assertEqual(t6["name"], "TOKEN_WORLD_RECORD")
        self.assertEqual(self.cfg["worldRecord"]["symbolId"], "SPECIAL_WORLD_RECORD")
        self.assertNotEqual(self.cfg["worldRecord"]["symbolId"], t6["id"])
        self.assertEqual(self.cfg["flightTokens"]["specialWorldRecordId"], "SPECIAL_WORLD_RECORD")
        self.assertEqual(self.cfg["flightTokens"]["t6Id"], "TOKEN_WORLD_RECORD")

    def test_11_tier_wr_rates(self):
        c = float(self.cfg["worldRecord"]["c"])
        for tier in TIERS:
            self.assertAlmostEqual(wr_probability(self.cfg, tier), c * INTENSITY[tier], places=18)

    def test_12_wr_samples_exist_and_non_production(self):
        self.assertTrue(WR_SAMPLES.exists())
        data = json.loads(WR_SAMPLES.read_text(encoding="utf-8"))
        self.assertTrue(data["nonProduction"])
        self.assertEqual(len(data["samples"]), 14)
        for row in data["samples"]:
            types = [e["type"] for e in row["events"]]
            self.assertIn("skyjumpWorldRecord", types)
            wr_i = types.index("skyjumpWorldRecord")
            after = types[wr_i + 1 :]
            for forbidden in (
                "skyjumpLineWins",
                "skyjumpMysteryResolve",
                "skyjumpRejumpStart",
                "skyjumpJudgeCollect",
            ):
                self.assertNotIn(forbidden, after)
            finals = [e for e in row["events"] if e["type"] == "finalWin"]
            self.assertEqual(len(finals), 1)
            self.assertLessEqual(row["roundWinXCapped"], 50000.0 + 1e-9)

    def test_13_config_provenance(self):
        live_hash = hashlib.sha256(CFG_PATH.read_bytes()).hexdigest()
        self.assertNotEqual(live_hash, self.freeze["configSha256"])
        meta = self.cfg["meta"]
        self.assertEqual(meta.get("paytableCandidate"), "PT2H_LADDER")
        self.assertEqual(meta.get("bonusBodyCandidate"), "BODY1")
        self.assertEqual(meta.get("worldRecordCandidate"), "H2")
        self.assertEqual(int(meta.get("featureEconomyVersion") or 0), 2)


if __name__ == "__main__":
    unittest.main()
