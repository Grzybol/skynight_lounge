"""Phase 5C DEV bonus sample books: schema, settlement, and resume reconstruction."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_reducer import reduce_events

SAMPLES = HERE / "skyjump_v2_bonus_samples.json"
RESERVE = {
    "setTotalWin",
    "skyjumpWeather",
    "skyjumpSlot",
    "skyjumpResult",
    "skyjumpSpinStart",
    "skyjumpBoardReveal",
    "skyjumpLineWins",
    "skyjumpScatterResult",
    "skyjumpCoachSignal",
    "skyjumpMysteryTransform",
    "skyjumpMysteryResolve",
    "skyjumpGateUpgrade",
    "skyjumpThermalLift",
    "skyjumpJudgeCollect",
    "skyjumpHeadJudgeCollect",
    "skyjumpCapReached",
    "skyjumpFreeSpinsStart",
    "skyjumpFreeSpinStart",
    "skyjumpFreeSpinState",
    "skyjumpBonusUpgrade",
    "skyjumpFreeSpinEnd",
    "skyjumpPersistentTargetsApply",
    "skyjumpPersistentTargetsUpdate",
    "skyjumpGuaranteedGate",
    "wincap",
}
COMPARE = (
    "bonusActive",
    "bonusTier",
    "freeSpinsRemaining",
    "freeSpinsPlayed",
    "totalFreeSpinsAwarded",
    "tokenFloorTier",
    "persistentMysteryTargets",
    "guaranteedGateUsed",
    "maxWinReached",
    "roundWinXCapped",
    "pendingTierUpgrade",
)


def resume_events(events: list[dict], index: int) -> list[dict]:
    before = [event for offset, event in enumerate(events) if offset < index and event["type"] in RESERVE]
    return before + events[index:]


class Phase5CSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(SAMPLES.read_text(encoding="utf-8"))
        cls.by_id = {row["id"]: row for row in cls.payload["samples"]}

    def test_catalog(self):
        self.assertTrue(self.payload["nonProduction"])
        self.assertEqual(len(self.by_id), 24)
        raw = SAMPLES.read_text(encoding="utf-8")
        self.assertNotIn("Math.random", raw)
        self.assertNotIn("crypto.getRandomValues", raw)

    def test_every_sample_settles_once_inside_caps(self):
        for sample in self.payload["samples"]:
            events = sample["events"]
            self.assertEqual([event["index"] for event in events], list(range(len(events))), sample["id"])
            self.assertEqual(sum(1 for event in events if event["type"] == "finalWin"), 1, sample["id"])
            self.assertEqual(sum(1 for event in events if event["type"] == "skyjumpSpinStart"), 1, sample["id"])
            starts = [event for event in events if event["type"] == "skyjumpFreeSpinsStart"]
            self.assertEqual(len(starts), 1, sample["id"])
            self.assertEqual(starts[0]["wagerCostMultiplier"], 0, sample["id"])
            awarded = [
                int(event["totalFreeSpinsAwarded"])
                for event in events
                if "totalFreeSpinsAwarded" in event
            ]
            self.assertTrue(awarded, sample["id"])
            self.assertLessEqual(max(awarded), 40, sample["id"])
            self.assertLessEqual(float(sample["expect"]["roundWinX"]), 50_000, sample["id"])
            end = reduce_events(events)
            self.assertFalse(end["bonusActive"], sample["id"])
            self.assertLessEqual(float(end["roundWinXCapped"]), 50_000, sample["id"])
            again = reduce_events(events)
            self.assertEqual(end["roundWinXCapped"], again["roundWinXCapped"], sample["id"])

    def test_trigger_and_progression_samples(self):
        def scatter(sample):
            return next(event for event in sample["events"] if event["type"] == "skyjumpScatterResult")

        self.assertEqual(scatter(self.by_id["01"])["count"], 3)
        self.assertFalse(scatter(self.by_id["01"])["perfectV"])
        self.assertEqual(self.by_id["01"]["expect"]["startTier"], "LARGE_HILL")
        self.assertEqual(self.by_id["01"]["expect"]["spinsPlayed"], 10)
        self.assertEqual(scatter(self.by_id["02"])["count"], 4)
        self.assertEqual(self.by_id["02"]["expect"]["startTier"], "SKI_FLYING")
        self.assertGreaterEqual(scatter(self.by_id["03"])["count"], 5)
        self.assertFalse(scatter(self.by_id["03"])["perfectV"])
        self.assertEqual(self.by_id["03"]["expect"]["startTier"], "WORLD_CUP")
        self.assertTrue(scatter(self.by_id["04"])["perfectV"])
        self.assertEqual(self.by_id["04"]["expect"]["startTier"], "PERFECT_V")
        self.assertEqual(self.by_id["05"]["expect"]["finalTier"], "SKI_FLYING")
        self.assertEqual(self.by_id["07"]["expect"]["finalTier"], "PERFECT_V")
        retrigger = next(
            event
            for event in self.by_id["08"]["events"]
            if event["type"] == "skyjumpBonusUpgrade"
        )
        self.assertEqual(retrigger["fromTier"], "PERFECT_V")
        self.assertEqual(retrigger["toTier"], "PERFECT_V")
        self.assertEqual(retrigger["spinsAdded"], 5)
        self.assertFalse(retrigger["tierChanged"])
        self.assertGreaterEqual(len(self.by_id["09"]["expect"]["persistentTargets"]), 1)
        self.assertEqual(len(self.by_id["10"]["expect"]["persistentTargets"]), 2)
        self.assertNotEqual(
            self.by_id["11"]["expect"]["behaviourBSelected"],
            self.by_id["11"]["expect"]["behaviourBExcluded"],
        )
        self.assertTrue(any(event["type"] == "skyjumpGuaranteedGate" for event in self.by_id["12"]["events"]))
        self.assertIn("naturalGateSpin", self.by_id["13"]["expect"])
        self.assertGreaterEqual(self.by_id["14"]["expect"]["floorAtEnd"], self.by_id["14"]["expect"]["floorRaisedTo"])
        self.assertGreater(self.by_id["14"]["expect"]["floorRaisedTo"], 1)
        self.assertGreater(self.by_id["15"]["expect"]["tokenThenLaterSpin"], 1)
        self.assertGreater(self.by_id["16"]["expect"]["spinsPlayed"], 15)
        self.assertGreater(self.by_id["16"]["expect"]["totalAwarded"], 15)
        capped = [
            event
            for event in self.by_id["17"]["events"]
            if event["type"] == "skyjumpBonusUpgrade" and event["totalFreeSpinsAwarded"] == 40
        ]
        self.assertTrue(any(event["spinsRequested"] == 5 and event["spinsAdded"] == 0 for event in capped))
        self.assertLessEqual(max(event["totalFreeSpinsAwarded"] for event in capped), 40)
        natural = self.by_id["13"]
        spin_index = natural["expect"]["naturalGateSpin"]
        slice_events = []
        capturing = False
        for event in natural["events"]:
            if event["type"] == "skyjumpFreeSpinStart" and event.get("spinIndex") == spin_index:
                capturing = True
                slice_events = [event]
                continue
            if not capturing:
                continue
            slice_events.append(event)
            if event["type"] == "skyjumpFreeSpinEnd":
                break
        slice_types = [event["type"] for event in slice_events]
        self.assertIn("skyjumpGateUpgrade", slice_types)
        self.assertNotIn("skyjumpGuaranteedGate", slice_types)
        self.assertTrue(
            any(
                event["type"] == "skyjumpMysteryResolve" and event.get("resultType") == "FLIGHT_TOKEN"
                for event in self.by_id["15"]["events"]
            )
        )
        cap = next(event for event in self.by_id["18"]["events"] if event["type"] == "skyjumpCapReached")
        self.assertTrue(cap["terminated"])
        self.assertEqual(cap["cappedTotalWinX"], 50_000)
        self.assertEqual(self.by_id["18"]["expect"]["spinsPlayed"], 1)
        self.assertLess(self.by_id["18"]["expect"]["spinsPlayed"], 10)

    def test_resume_matches_uninterrupted_final_state(self):
        for sample_id in ("19", "20", "21", "22", "23", "24"):
            sample = self.by_id[sample_id]
            events = sample["events"]
            index = int(sample["resumeIndex"])
            self.assertGreater(index, 0, sample_id)
            self.assertLess(index, len(events), sample_id)
            full = reduce_events(events)
            resumed = reduce_events(resume_events(events, index))
            for key in COMPARE:
                self.assertEqual(full.get(key), resumed.get(key), f"{sample_id} {key}")


if __name__ == "__main__":
    unittest.main()
