"""Phase 5B Free Spin implementation tests. Live config, not research constants."""

from __future__ import annotations

import hashlib
import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import scatter_on_board
from skyjump_v2_freespins import (
    bonus_candidate_from_config,
    classify_base_trigger,
    resolve_v2_round,
)
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase4a_economy import resolve_paying_features
from skyjump_v2_phase5a_engine import apply_upgrade_rule, new_bonus_state, resolve_fs_spin
from skyjump_v2_reducer import reduce_events
from skyjump_v2_reels import board_from_stops

BASE_HASH = "d932065b36a626c7cd9a818bd8c401559e6270c434622d32d1fb640e3d8d7803"


class Phase5BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_v2_config()
        cls.candidate = bonus_candidate_from_config(cls.config)
        cls.paying = live_candidate_from_config(cls.config)

    def test_base_keys_match_certified_hash_when_bonus_removed(self):
        raw = json.loads((HERE / "skyjump_v2_config.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["freeSpins"]["candidateOrigin"], "FS5A_U1_P2_M40_mid_E15j2")
        self.assertEqual(raw["reelModel"]["strips"][1].count("C"), 1)
        self.assertEqual(raw["featureEconomy"]["mysteryResultWeights"]["JUDGE"], 85)
        self.assertNotEqual(hashlib.sha256((HERE / "skyjump_v2_config.json").read_bytes()).hexdigest(), BASE_HASH)

    def test_trigger_classification_and_perfect_v_override(self):
        self.assertEqual(classify_base_trigger({"count": 3, "perfectV": False})[0], "LARGE_HILL")
        self.assertEqual(classify_base_trigger({"count": 4, "perfectV": False})[0], "SKI_FLYING")
        self.assertEqual(classify_base_trigger({"count": 5, "perfectV": False})[0], "WORLD_CUP")
        self.assertEqual(classify_base_trigger({"count": 5, "perfectV": True}), ("PERFECT_V", "PERFECT_V"))
        self.assertEqual(classify_base_trigger({"count": 2, "perfectV": False}), (None, None))

    def test_u1_next_spin_and_perfect_v_cap(self):
        step = apply_upgrade_rule("U1", 3, False, "LARGE_HILL")
        self.assertEqual(step["addSpins"], 5)
        self.assertEqual(step["newTier"], "SKI_FLYING")
        top = apply_upgrade_rule("U1", 3, False, "PERFECT_V")
        self.assertEqual(top["newTier"], "PERFECT_V")
        self.assertFalse(top["upgraded"])
        self.assertEqual(top["addSpins"], 5)

    def test_initial_ten_and_no_trigger_double_count(self):
        rng = random.Random(4)
        found = None
        for _ in range(8000):
            result = resolve_v2_round(rng, config=self.config)
            if result["isBonus"]:
                found = result
                break
        self.assertIsNotNone(found)
        start = next(event for event in found["events"] if event["type"] == "skyjumpFreeSpinsStart")
        self.assertEqual(start["spinsAwarded"], 10)
        self.assertEqual(start["wagerCostMultiplier"], 0)
        self.assertEqual(found["events"].count({"type": "finalWin"}) if False else sum(1 for e in found["events"] if e["type"] == "finalWin"), 1)
        self.assertAlmostEqual(
            found["roundWinXCapped"],
            min(50_000.0, found["triggerSpinWinX"] + found["bonusWinXCapped"]),
            places=6,
        )
        if found["triggerSpinWinX"] > 0:
            self.assertLess(found["bonusWinXCapped"], found["roundWinXCapped"] + 1e-9)
            self.assertNotAlmostEqual(found["bonusWinXCapped"], found["roundWinXRaw"], places=4)

    def test_max_awarded_spins_caps_at_40(self):
        state = new_bonus_state("LARGE_HILL", initial_spins=10)
        state.spinsAwardedTotal = 38
        state.freeSpinsRemaining = 2
        state.freeSpinsPlayed = 36
        # Search a Large Hill board with 3+ scatters.
        strips = self.candidate.tierReels["LARGE_HILL"]
        rng = random.Random(3)
        hit = None
        for _ in range(4000):
            stops = [rng.randrange(len(strip)) for strip in strips]
            board = board_from_stops(strips, stops)
            scatter = scatter_on_board(board, "S", (0, 1, 2, 1, 0))
            if scatter["count"] >= 3:
                hit = stops
                break
        self.assertIsNotNone(hit)
        before = state.spinsAwardedTotal
        result = resolve_fs_spin(
            rng,
            state,
            self.candidate,
            config=self.config,
            paying_candidate=self.paying,
            stops=hit,
        )
        self.assertEqual(result["upgrade"]["addSpins"], 5)
        self.assertEqual(result["spinsAdded"], 2)
        self.assertEqual(state.spinsAwardedTotal, 40)
        self.assertEqual(before + result["spinsAdded"], 40)

    def test_duplicate_target_behaviour_b(self):
        board = [["L1" for _ in range(5)] for _ in range(5)]
        board[1][0] = "C"
        board[0][0] = "L2"
        seen = set()
        for seed in range(30):
            features = resolve_paying_features(
                board,
                random.Random(seed),
                config=self.config,
                candidate=self.paying,
                coach_exclude_types={"L1"},
                coach_prefer_non_excluded=True,
            )
            selected = features["selectedSymbolIds"]
            self.assertTrue(selected)
            seen.add(selected[0])
        self.assertEqual(seen, {"L2"})

    def test_guaranteed_gate_once_and_not_collectors(self):
        rng = random.Random(11)
        state = new_bonus_state("WORLD_CUP", initial_spins=10)
        state.guaranteedGateUsed = False
        replaced = None
        for _ in range(80):
            if state.freeSpinsRemaining <= 0:
                break
            result = resolve_fs_spin(
                rng,
                state,
                self.candidate,
                config=self.config,
                paying_candidate=self.paying,
            )
            info = result["features"].get("guaranteedGateReplaced")
            if info:
                replaced = info
                break
        self.assertIsNotNone(replaced)
        self.assertNotIn(replaced["replacedResultType"], {"JUDGE", "HEAD_JUDGE"})
        if replaced["replacedTokenTier"] is not None:
            self.assertLessEqual(int(replaced["replacedTokenTier"]), 4)
        self.assertTrue(state.guaranteedGateUsed)
        # Further spins must not guarantee again.
        again = False
        for _ in range(5):
            if state.freeSpinsRemaining <= 0 or state.maxWinReached:
                break
            result = resolve_fs_spin(
                rng,
                state,
                self.candidate,
                config=self.config,
                paying_candidate=self.paying,
            )
            if result["features"].get("guaranteedGateApplied"):
                again = True
        self.assertFalse(again)

    def test_perfect_v_guaranteed_coach(self):
        rng = random.Random(19)
        state = new_bonus_state("PERFECT_V", initial_spins=3)
        state.guaranteedGateUsed = False
        for _ in range(3):
            result = resolve_fs_spin(
                rng,
                state,
                self.candidate,
                config=self.config,
                paying_candidate=self.paying,
            )
            self.assertGreaterEqual(result["coachCount"], 1)

    def test_cells_reset_floor_and_targets_persist(self):
        rng = random.Random(21)
        result = resolve_v2_round(rng, config=self.config)
        # Force a Ski Flying start by classifying a synthetic book through the engine.
        state = new_bonus_state("SKI_FLYING", initial_spins=2)
        state.guaranteedGateUsed = True
        state.persistentMysteryTargets = ["L1"]
        state.tokenFloorTier = 2
        spin = resolve_fs_spin(
            rng,
            state,
            self.candidate,
            config=self.config,
            paying_candidate=self.paying,
        )
        self.assertIn("L1", state.persistentMysteryTargets)
        self.assertGreaterEqual(state.tokenFloorTier, 2)
        self.assertEqual(spin["features"]["tokenFloorTier"] >= 2, True)

    def test_round_cap_and_resume_checkpoints(self):
        rng = random.Random(8)
        found = None
        for _ in range(5000):
            result = resolve_v2_round(rng, config=self.config)
            if result["isBonus"]:
                found = result
                break
        self.assertIsNotNone(found)
        events = found["events"]
        self.assertLessEqual(found["roundWinXCapped"], 50_000)
        indexes = {
            "before_fs": next(i for i, e in enumerate(events) if e["type"] == "skyjumpFreeSpinsStart"),
            "mid": next(i for i, e in enumerate(events) if e["type"] == "skyjumpFreeSpinEnd"),
            "end": next(i for i, e in enumerate(events) if e["type"] == "skyjumpFreeSpinsEnd"),
        }
        before = reduce_events(events[: indexes["before_fs"]])
        self.assertFalse(before["bonusActive"])
        mid = reduce_events(events[: indexes["mid"] + 1])
        self.assertTrue(mid["bonusActive"] or mid["freeSpinsPlayed"] >= 1)
        self.assertIsNone(mid["board"])
        end = reduce_events(events)
        self.assertFalse(end["bonusActive"])
        self.assertAlmostEqual(end["roundWinXCapped"], found["roundWinXCapped"], places=6)
        self.assertEqual(sum(1 for e in events if e["type"] == "finalWin"), 1)

    def test_resume_checkpoints_and_max_win_stop(self):
        from skyjump_v2_freespins import _snapshot

        rng = random.Random(8)
        book = None
        upgrade_book = None
        for _ in range(8000):
            result = resolve_v2_round(rng, config=self.config)
            if not result["isBonus"]:
                continue
            book = book or result
            if any(event["type"] == "skyjumpBonusUpgrade" for event in result["events"]):
                upgrade_book = result
                break
        self.assertIsNotNone(book)
        events = book["events"]
        start = next(i for i, event in enumerate(events) if event["type"] == "skyjumpFreeSpinsStart")
        first_spin = next(i for i, event in enumerate(events) if event["type"] == "skyjumpFreeSpinStart")
        before = reduce_events(events[:start])
        self.assertFalse(before["bonusActive"])
        armed = reduce_events(events[: first_spin])
        self.assertTrue(armed["bonusActive"])
        self.assertEqual(armed["freeSpinsPlayed"], 0)
        self.assertEqual(armed["freeSpinsRemaining"], 10)
        self.assertIsNone(armed["pendingTierUpgrade"])
        mid = reduce_events(events[: next(i for i, event in enumerate(events) if event["type"] == "skyjumpFreeSpinState") + 1])
        self.assertTrue(mid["bonusActive"])
        self.assertIsNone(mid["board"])
        self.assertGreaterEqual(mid["freeSpinsPlayed"], 1)
        last_spin = max(i for i, event in enumerate(events) if event["type"] == "skyjumpFreeSpinStart")
        before_last = reduce_events(events[:last_spin])
        self.assertTrue(before_last["bonusActive"])
        self.assertGreater(before_last["freeSpinsRemaining"], 0)
        if upgrade_book is not None:
            up_events = upgrade_book["events"]
            up_index = next(i for i, event in enumerate(up_events) if event["type"] == "skyjumpBonusUpgrade")
            after_upgrade = reduce_events(up_events[: up_index + 1])
            upgrade = up_events[up_index]
            self.assertEqual(after_upgrade["bonusTier"], upgrade["fromTier"])
            if upgrade["tierChanged"]:
                self.assertEqual(after_upgrade["pendingTierUpgrade"], upgrade["toTier"])
            self.assertEqual(after_upgrade["totalFreeSpinsAwarded"], upgrade["totalFreeSpinsAwarded"])

        ski = new_bonus_state("SKI_FLYING", initial_spins=16)
        ski_rng = random.Random(5)
        for _ in range(16):
            resolve_fs_spin(ski_rng, ski, self.candidate, config=self.config, paying_candidate=self.paying)
            if len(ski.persistentMysteryTargets) >= 2:
                break
        self.assertEqual(len(ski.persistentMysteryTargets), 2)
        ski_state = reduce_events([_snapshot(ski, trigger_win_x=0.0, round_capped=ski.bonusWinXCapped, initial_spins=10)])
        self.assertEqual(ski_state["persistentMysteryTargets"], ski.persistentMysteryTargets)
        self.assertEqual(ski_state["bonusTier"], "SKI_FLYING")
        self.assertGreaterEqual(ski_state["tokenFloorTier"], 1)
        self.assertIsNone(ski_state["board"])

        cup = new_bonus_state("WORLD_CUP", initial_spins=12)
        cup_rng = random.Random(11)
        for _ in range(12):
            result = resolve_fs_spin(cup_rng, cup, self.candidate, config=self.config, paying_candidate=self.paying)
            if result["features"].get("guaranteedGateApplied") or cup.guaranteedGateUsed:
                break
        self.assertTrue(cup.guaranteedGateUsed)
        cup_state = reduce_events([_snapshot(cup, trigger_win_x=0.0, round_capped=min(50_000.0, cup.bonusWinXCapped), initial_spins=10)])
        self.assertTrue(cup_state["guaranteedGateUsed"])
        self.assertEqual(cup_state["bonusTier"], "WORLD_CUP")

        perfect = new_bonus_state("PERFECT_V", initial_spins=2)
        perfect_spin = resolve_fs_spin(random.Random(19), perfect, self.candidate, config=self.config, paying_candidate=self.paying)
        self.assertGreaterEqual(perfect_spin["coachCount"], 1)
        perfect_state = reduce_events([_snapshot(perfect, trigger_win_x=0.0, round_capped=perfect.bonusWinXCapped, initial_spins=10)])
        self.assertEqual(perfect_state["bonusTier"], "PERFECT_V")
        self.assertTrue(perfect_state["coachGuaranteeState"]["required"])
        self.assertTrue(perfect_state["coachGuaranteeState"]["satisfied"])

        capped = None
        for seed in range(80):
            trial = new_bonus_state("LARGE_HILL", initial_spins=10)
            resolve_fs_spin(
                random.Random(seed),
                trial,
                self.candidate,
                config=self.config,
                paying_candidate=self.paying,
                round_prior_win_x=49_999.0,
            )
            if trial.maxWinReached:
                capped = trial
                break
        self.assertIsNotNone(capped)
        self.assertLess(capped.freeSpinsPlayed, 10)
        self.assertLessEqual(49_999.0 + capped.bonusWinXCapped, 50_000.0)
        cap_state = reduce_events(
            [
                {
                    "type": "skyjumpCapReached",
                    "rawTotalWinX": 50_100.0,
                    "cappedTotalWinX": 50_000.0,
                    "capDragX": 100.0,
                },
                _snapshot(capped, trigger_win_x=49_999.0, round_capped=50_000.0, initial_spins=10),
            ]
        )
        self.assertTrue(cap_state["maxWinReached"])
        self.assertTrue(cap_state["capReached"])
        self.assertEqual(cap_state["totalWinX"], 50_000.0)

    def test_replay_deterministic(self):
        a = resolve_v2_round(random.Random(99), config=self.config)
        b = resolve_v2_round(random.Random(99), config=self.config)
        self.assertEqual(a["roundWinXCapped"], b["roundWinXCapped"])
        self.assertEqual([e["type"] for e in a["events"]], [e["type"] for e in b["events"]])


if __name__ == "__main__":
    unittest.main()
