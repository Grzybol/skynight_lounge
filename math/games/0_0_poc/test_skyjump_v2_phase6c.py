"""Phase 6C certification tests — measurement helpers; no live weight mutation."""

from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import new_bonus_state
from skyjump_v2_phase6b import (
    choose_stage_charge_priority,
    choose_stage_pure_w2,
    ensure_phase6_state,
    set_stage_selection_mode,
)
from skyjump_v2_phase6c_certify import (
    BASELINE_MEAN,
    cfg_off,
    exact_wind_transitions,
    feature_off_equivalence,
    zero_feature,
)

HERE = Path(__file__).resolve().parent
FREEZE = HERE / "phase6c_research" / "freeze.json"


class Phase6CTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.cand = bonus_candidate_from_config(cls.cfg)
        cls.pay = live_candidate_from_config(cls.cfg)

    def test_freeze_exists_as_historical_snapshot(self):
        self.assertTrue(FREEZE.exists())
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        self.assertEqual(freeze["phase6"]["candidateOrigin"], "P6A1_E_E1")
        self.assertEqual(freeze["baseMystery"]["FLIGHT_TOKEN"], 855)
        self.assertNotIn("REJUMP", freeze["baseMystery"])
        # Phase 6C freeze captured charged-priority live; 6C.1 changed stageRule.
        self.assertEqual(freeze["phase6"].get("stageRule"), "W2_CHARGE_PRIORITY")

    def test_charged_priority_differs_from_pure_w2(self):
        state = new_bonus_state("LARGE_HILL")
        ensure_phase6_state(state)
        state.flightMultiplier["runUp"]["charge"] = 1
        state.runUpCharge = 1
        # Same RNG stream — priority must upgrade RUN_UP; pure may pick another stage.
        prio = choose_stage_charge_priority(random.Random(0), state)
        pure = choose_stage_pure_w2(random.Random(0), state)
        self.assertEqual(prio, ("RUN_UP", "UPGRADE"))
        self.assertNotEqual(prio, pure)

    def test_stage_override_restores(self):
        prev = set_stage_selection_mode("W2_PURE")
        set_stage_selection_mode("W2_CHARGE_PRIORITY")
        restored = set_stage_selection_mode(prev)
        self.assertEqual(restored, "W2_CHARGE_PRIORITY")
        set_stage_selection_mode("W2_PURE")

    def test_zero_feature_preserves_sum(self):
        rj = zero_feature(self.cand, keep_rejump=True, keep_wind=False)
        for tier, table in rj.mysteryResultWeightsByTier.items():
            self.assertEqual(sum(table.values()), 1000)
            self.assertEqual(table["WIND_KEY"], 0)
            self.assertGreater(table["REJUMP"], 0)

    def test_feature_off_config(self):
        off = cfg_off(self.cfg)
        self.assertFalse(off["freeSpins"]["phase6"]["enabled"])
        self.assertEqual(
            off["freeSpins"]["tiers"]["LARGE_HILL"]["mysteryResultWeights"]["FLIGHT_TOKEN"],
            752,
        )

    def test_exact_wind_transitions_shape(self):
        data = exact_wind_transitions(n_keys_max=4, mc=5_000, seed=1)
        self.assertIn("0", data["byNKeysPriority"])
        self.assertIn("2", data["priorityVsPure"])
        self.assertGreater(
            data["priorityVsPure"]["4"]["priority"]["meanGlobal"],
            0.9,
        )

    def test_synthetic_samples_present(self):
        samples = json.loads((HERE / "skyjump_v2_phase6_samples.json").read_text(encoding="utf-8"))
        ids = {s["id"] for s in samples["samples"]}
        self.assertIn("16_coach_after_rejump", ids)
        self.assertIn("24_cap", ids)
        self.assertTrue(samples["nonProduction"])
        cap = next(s for s in samples["samples"] if s["id"] == "24_cap")
        self.assertTrue(any(e["type"] == "skyjumpCapReached" for e in cap["events"]))
        coach = next(s for s in samples["samples"] if s["id"] == "16_coach_after_rejump")
        types = [e["type"] for e in coach["events"]]
        self.assertLess(types.index("skyjumpRejumpStart"), types.index("skyjumpCoach"))

    def test_feature_off_near_phase5b(self):
        # Small n smoke — full check lives in certify quick.
        res = feature_off_equivalence(self.cfg, self.cand, self.pay, n=2_000, seed=1)
        self.assertLess(abs(res["featureOffMeanX"] - BASELINE_MEAN), 2.5)


if __name__ == "__main__":
    unittest.main()
