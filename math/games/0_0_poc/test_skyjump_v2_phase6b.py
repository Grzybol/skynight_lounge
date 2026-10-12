"""Phase 6B structural and semantic tests."""

from __future__ import annotations

import random
import unittest
from copy import deepcopy

from skyjump_v2_freespins import bonus_candidate_from_config, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import new_bonus_state, resolve_fs_spin, simulate_bonus
from skyjump_v2_phase6a_search import table_for
from skyjump_v2_phase6a1_search import PACKS
from skyjump_v2_phase6b import (
    apply_wind_key,
    choose_stage,
    choose_stage_charge_priority,
    choose_stage_pure_w2,
    ensure_phase6_state,
    global_flight_multiplier,
    phase6_enabled,
    stages_maxed,
)


class Phase6BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.cand = bonus_candidate_from_config(cls.cfg)
        cls.pay = live_candidate_from_config(cls.cfg)

    def test_stage_rule_is_pure_w2(self):
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["stageRule"], "W2_PURE")
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["candidateOrigin"], "P6A1_E_E1")

    def test_phase6_enabled_and_e1_weights(self):
        self.assertTrue(phase6_enabled(self.cfg))
        self.assertEqual(self.cfg["freeSpins"]["phase6"]["candidateOrigin"], "P6A1_E_E1")
        for tier, pair in PACKS["E1"].items():
            expected = table_for(pair)
            got = self.cand.mysteryResultWeightsByTier[tier]
            self.assertEqual(got, expected)
            self.assertEqual(sum(got.values()), 1000)

    def test_base_has_no_phase6(self):
        base = self.cfg["featureEconomy"]["mysteryResultWeights"]
        self.assertNotIn("REJUMP", base)
        self.assertNotIn("WIND_KEY", base)
        self.assertEqual(base["FLIGHT_TOKEN"], 855)

    def test_charge_then_upgrade_same_stage(self):
        """W-CHARGE still requires two Keys on the same stage (isolate via unique lowest)."""
        state = new_bonus_state("LARGE_HILL")
        ensure_phase6_state(state)
        # TAKEOFF/FLIGHT already at x2 → only RUN_UP is lowest eligible.
        state.flightMultiplier["takeoff"]["value"] = 2
        state.flightMultiplier["flight"]["value"] = 2
        state.flightMultiplierTakeoff = 2
        state.flightMultiplierFlight = 2
        d1 = apply_wind_key(state, random.Random(0), {"kind": "wind"})
        self.assertEqual(d1["selectedStage"], "RUN_UP")
        self.assertEqual(d1["action"], "CHARGE")
        self.assertEqual(d1["newGlobalMultiplier"], 4)  # 1×2×2
        d2 = apply_wind_key(state, random.Random(1), {"kind": "wind"})
        self.assertEqual(d2["selectedStage"], "RUN_UP")
        self.assertEqual(d2["action"], "UPGRADE")
        self.assertEqual(d2["newStageValue"], 2)
        self.assertEqual(d2["newCharge"], 0)
        self.assertEqual(d2["newGlobalMultiplier"], 8)  # 2×2×2

    def test_pure_w2_ignores_charge_when_selecting(self):
        state = new_bonus_state("LARGE_HILL")
        ensure_phase6_state(state)
        state.flightMultiplier["runUp"]["charge"] = 1
        state.runUpCharge = 1
        # Pure W2 may pick TAKEOFF/FLIGHT CHARGE, not forced RUN_UP UPGRADE.
        stage, action = choose_stage_pure_w2(random.Random(0), state)
        self.assertIn(stage, ("RUN_UP", "TAKEOFF", "FLIGHT"))
        # Historical priority would force RUN_UP UPGRADE.
        prio_stage, prio_action = choose_stage_charge_priority(random.Random(0), state)
        self.assertEqual((prio_stage, prio_action), ("RUN_UP", "UPGRADE"))
        # Live choose_stage defaults to pure W2.
        live_stage, live_action = choose_stage(random.Random(0), state)
        self.assertEqual((live_stage, live_action), (stage, action))
        self.assertNotEqual((live_stage, live_action), (prio_stage, prio_action))

    def test_multiple_partial_charges_valid(self):
        state = new_bonus_state("LARGE_HILL")
        ensure_phase6_state(state)
        state.flightMultiplier["runUp"]["charge"] = 1
        state.flightMultiplier["takeoff"]["charge"] = 1
        state.flightMultiplier["flight"]["charge"] = 1
        state.runUpCharge = state.takeoffCharge = state.flightCharge = 1
        self.assertEqual(global_flight_multiplier(state), 1)
        stage, action = choose_stage_pure_w2(random.Random(3), state)
        self.assertEqual(action, "UPGRADE")
        self.assertIn(stage, ("RUN_UP", "TAKEOFF", "FLIGHT"))

    def test_saturation_b(self):
        state = new_bonus_state("LARGE_HILL")
        ensure_phase6_state(state)
        for name in ("runUp", "takeoff", "flight"):
            state.flightMultiplier[name]["value"] = 3
            state.flightMultiplier[name]["charge"] = 0
        state.flightMultiplierRunUp = 3
        state.flightMultiplierTakeoff = 3
        state.flightMultiplierFlight = 3
        self.assertTrue(stages_maxed(state))
        self.assertEqual(global_flight_multiplier(state), 27)

    def test_bonus_runs_bounded(self):
        res = simulate_bonus(
            random.Random(42),
            "LARGE_HILL",
            self.cand,
            config=self.cfg,
            paying_candidate=self.pay,
        )
        self.assertLessEqual(res["freeSpinsPlayed"], 40)
        self.assertLessEqual(res["bonusWinXCapped"], 50_000)

    def test_spent_collector_and_rejump_events(self):
        # Search a spin that emits rejump or wind
        found_rj = False
        found_wk = False
        for seed in range(2000):
            state = new_bonus_state("PERFECT_V")
            ensure_phase6_state(state)
            result = resolve_fs_spin(
                random.Random(seed),
                state,
                self.cand,
                config=self.cfg,
                paying_candidate=self.pay,
            )
            feats = result["features"]
            if feats.get("rejumpCount"):
                found_rj = True
                for collection in feats.get("collections") or []:
                    self.assertTrue(collection.get("payoutSpentAfter", True))
                    self.assertIn("batchIndex", collection)
                    self.assertIn("flightMultiplierX", collection)
                # no unpaid collectors remain paid=false without payoutSpent if they collected
            if feats.get("windKeyCount"):
                found_wk = True
            if found_rj and found_wk:
                break
        self.assertTrue(found_rj)
        self.assertTrue(found_wk)

    def test_third_rejump_truncated_search(self):
        # Hard to force naturally; verify truncate event shape when rejumpState reports truncated
        truncated_seen = False
        for seed in range(5000):
            state = new_bonus_state("PERFECT_V")
            ensure_phase6_state(state)
            result = resolve_fs_spin(
                random.Random(seed),
                state,
                self.cand,
                config=self.cfg,
                paying_candidate=self.pay,
            )
            if int(result["features"].get("truncatedRejumps") or 0) > 0:
                truncated_seen = True
                ends = [
                    e
                    for e in result["features"].get("phase6Events") or []
                    if e["type"] == "skyjumpRejumpEnd" and e.get("truncated")
                ]
                self.assertTrue(ends)
                self.assertLessEqual(result["features"]["rejumpCount"], 2)
                break
        # Truncation is rare; soft-skip if not found in sample (hard chain needs many RJ draws)
        if not truncated_seen:
            self.skipTest("no truncated third rejump in 5000 Perfect V spins")

    def test_round_book_emits_phase6_fields(self):
        for seed in range(3000):
            book = resolve_v2_round(random.Random(seed), config=self.cfg)
            if not book["isBonus"]:
                continue
            snaps = [e for e in book["events"] if e["type"] == "skyjumpFreeSpinState"]
            self.assertTrue(snaps)
            snap = snaps[-1]
            self.assertIn("flightMultiplier", snap)
            self.assertIn("globalFlightMultiplier", snap)
            self.assertIn("windKeysCollected", snap)
            return
        self.fail("no bonus book found")

    def test_line_wins_not_multiplied_by_flight(self):
        # Structural: collections use flightMultiplierX; rejump line events do not.
        for seed in range(3000):
            state = new_bonus_state("SKI_FLYING")
            ensure_phase6_state(state)
            # Seed a 2x multiplier
            state.flightMultiplier["runUp"]["value"] = 2
            state.flightMultiplierRunUp = 2
            result = resolve_fs_spin(
                random.Random(seed),
                state,
                self.cand,
                config=self.cfg,
                paying_candidate=self.pay,
            )
            for event in result["features"].get("phase6Events") or []:
                if event["type"] == "skyjumpRejumpLineWins":
                    # lineWinX is raw lines — no flight field
                    self.assertNotIn("flightMultiplierX", event)
                    return
        self.skipTest("no rejump line win in sample")


if __name__ == "__main__":
    unittest.main()
