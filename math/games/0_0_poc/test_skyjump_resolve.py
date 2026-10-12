import unittest
import random

from skyjump_resolve import (
    CONFIG,
    authoritative_from_events,
    evaluate_drawn_round,
    load_fixtures,
    resolve_round,
    resume_events,
    round_book_amount,
    round_to_book_events,
    rgs_payout_multiplier,
)
from skyjump_validate import validate_skyjump_config


class SkyJumpResolveTests(unittest.TestCase):
    def test_canonical_config_valid(self):
        errors = validate_skyjump_config(CONFIG)
        self.assertEqual(errors, [])

    def test_seeded_repeatability(self):
        a = resolve_round(random.Random(11))
        b = resolve_round(random.Random(11))
        self.assertEqual(a.finalWinX, b.finalWinX)
        self.assertEqual(a.distanceTotal, b.distanceTotal)

    def test_max_win_and_signs(self):
        rng = random.Random(99)
        max_win = CONFIG["hills"]["normal"]["maxWin"]
        for _ in range(500):
            result = resolve_round(rng)
            self.assertGreaterEqual(result.distanceTotal, 0)
            self.assertGreaterEqual(result.localMultiplier, 1)
            self.assertLessEqual(result.finalWinX, max_win)
            self.assertEqual(result.capped, result.isCapped)

    def test_fixtures_and_book_shape(self):
        fixtures = load_fixtures()
        self.assertGreaterEqual(len(fixtures), 3)
        for fixture in fixtures:
            result = evaluate_drawn_round(fixture)
            self.assertLessEqual(result.finalWinX, result.maxWin)
            events = round_to_book_events(result)
            types = [event["type"] for event in events]
            self.assertEqual(types[0], "skyjumpWeather")
            self.assertEqual(types[1:7], ["skyjumpSlot"] * 6)
            self.assertEqual(types[7], "skyjumpResult")
            self.assertIn("setTotalWin", types)
            self.assertIn("finalWin", types)
            self.assertEqual(events[1]["slotIndex"], 1)
            self.assertEqual(events[6]["slotIndex"], 6)
            self.assertEqual(events[6]["role"], "finalMultiplier")
            self.assertEqual(events[0]["schemaVersion"], 1)
            self.assertEqual(events[7]["isCapped"], result.isCapped)
            self.assertEqual(events[7]["amount"], round_book_amount(result.finalWinX))
            self.assertEqual(events[7]["schemaVersion"], 1)
            self.assertEqual(events[7]["costMultiplier"], result.costMultiplier)
            self.assertEqual(events[7]["isPayHit"], result.finalWinX > 0)
            self.assertEqual(events[7]["isBreakEven"], result.finalWinX >= result.costMultiplier)
            self.assertEqual(events[7]["isProfit"], result.finalWinX > result.costMultiplier)

    def test_combined_hill_and_multiplier_profiles(self):
        from skyjump_resolve import tables_for_mode

        tables = tables_for_mode("BASE", hill_id="flying", multiplier_table_id="max")
        self.assertEqual(tables["hillId"], "flying")
        self.assertEqual(tables["multiplierTableId"], "max")

    def test_payout_band_edges(self):
        from skyjump_resolve import lookup_payout

        curve = CONFIG["hills"]["normal"]["payoutCurve"]
        self.assertEqual(lookup_payout(curve, 115.9), 0)
        self.assertEqual(lookup_payout(curve, 116), 0.252)
        self.assertEqual(lookup_payout(curve, 124), 0.588)

    def test_book_amount_bankers_rounding(self):
        self.assertEqual(int(round(111.4)), 111)
        self.assertEqual(int(round(111.5)), 112)
        self.assertEqual(int(round(112.5)), 112)
        self.assertEqual(int(round(113.5)), 114)
        self.assertEqual(round_book_amount(1.114), int(round(1.114 * 100)))
        self.assertEqual(round_book_amount(1.125), int(round(1.125 * 100)))
        self.assertEqual(round_book_amount(7.2), int(round(7.2 * 100)))
        self.assertEqual(round_book_amount(500), 50000)

    def test_resume_after_wincap(self):
        fixtures = {row["id"]: row for row in load_fixtures()}
        result = evaluate_drawn_round(fixtures["hill-cap"])
        self.assertTrue(result.capped)
        events = round_to_book_events(result)
        self.assertIn("wincap", [event["type"] for event in events])
        expected = authoritative_from_events(events)
        before, after = resume_events(events, "wincap")
        self.assertEqual(authoritative_from_events(before + after), expected)
        self.assertEqual(after[0]["type"], "setTotalWin")

    def test_resume_interrupt_points_keep_authority(self):
        result = evaluate_drawn_round(load_fixtures()[1])
        events = round_to_book_events(result)
        expected = authoritative_from_events(events)
        points = [
            ("skyjumpWeather", None),
            ("skyjumpSlot", 1),
            ("skyjumpSlot", 2),
            ("skyjumpSlot", 3),
            ("skyjumpSlot", 4),
            ("skyjumpSlot", 5),
            ("skyjumpSlot", 6),
            ("skyjumpResult", None),
        ]
        if any(event["type"] == "wincap" for event in events):
            points.append(("wincap", None))
        for after_type, slot_index in points:
            before, after = resume_events(events, after_type, slot_index)
            reconstructed = before + after
            self.assertEqual(authoritative_from_events(reconstructed), expected)
            self.assertGreaterEqual(len(after), 1)

    def test_fixture_economic_semantics(self):
        fixtures = {row["id"]: row for row in load_fixtures()}
        miss = evaluate_drawn_round(fixtures["steady-miss"])
        small = evaluate_drawn_round(fixtures["small-payout"])
        profit = evaluate_drawn_round(fixtures["premium-profit"])
        loss = evaluate_drawn_round(fixtures["premium-economic-loss"])
        cap = evaluate_drawn_round(fixtures["hill-cap"])
        self.assertEqual(miss.finalWinX, 0)
        self.assertEqual(miss.finalMultiplier["multiplier"], 0)
        self.assertGreater(small.finalWinX, 0)
        self.assertLess(small.finalWinX, 1)
        self.assertTrue(profit.finalWinX > profit.costMultiplier)
        self.assertTrue(loss.finalWinX > 0)
        self.assertTrue(loss.finalWinX < loss.costMultiplier)
        self.assertTrue(cap.capped)

    def test_canonical_config_loaded(self):
        self.assertEqual(CONFIG["meta"]["gameID"], "0_0_poc")
        self.assertEqual(len(CONFIG["slots"]), 5)
        self.assertIn("volatilityModel", CONFIG)
        self.assertEqual(CONFIG["meta"]["mathVersion"], 3)
        self.assertEqual(CONFIG["eventSchemaVersion"], 1)
        self.assertEqual(CONFIG["buyModes"]["base"]["costMultiplier"], 1)

    def test_math_sdk_writer_emits_per_slot_events(self):
        import sys
        from pathlib import Path

        math_root = Path(__file__).resolve().parents[2]
        if str(math_root) not in sys.path:
            sys.path.insert(0, str(math_root))
        from game_config import GameConfig
        from gamestate import GameState

        config = GameConfig()
        gamestate = GameState(config)
        gamestate.betmode = "BASE"
        gamestate.criteria = "basegame"
        gamestate.sim = 7
        gamestate.run_spin(7)
        types = [event["type"] for event in gamestate.book.events]
        self.assertEqual(types[:8], [
            "skyjumpWeather",
            "skyjumpSlot",
            "skyjumpSlot",
            "skyjumpSlot",
            "skyjumpSlot",
            "skyjumpSlot",
            "skyjumpSlot",
            "skyjumpResult",
        ])
        self.assertIn("setTotalWin", types)
        self.assertIn("finalWin", types)
        self.assertNotIn("reveal", types)
        self.assertNotIn("skyjumpSlots", types)

    def test_mode_tables_use_published_maxwin(self):
        from skyjump_resolve import tables_for_mode

        expected = {
            "BASE": ("normal", "standard", 1, 500),
            "LARGE_HILL": ("large", "standard", 3, 4000),
            "SKI_FLYING": ("flying", "standard", 6, 25000),
            "MULT_10_100": ("normal", "plus", 11.3, 6000),
            "MULT_20_200": ("normal", "max", 22.6, 12000),
        }
        self.assertEqual(CONFIG["hills"]["normal"]["maxWin"], 500)
        for rgs_key, (hill, profile, cost, max_win) in expected.items():
            tables = tables_for_mode(rgs_key)
            self.assertEqual(tables["hillId"], hill, rgs_key)
            self.assertEqual(tables["multiplierTableId"], profile, rgs_key)
            self.assertEqual(tables["costMultiplier"], cost, rgs_key)
            self.assertEqual(tables["maxWin"], max_win, rgs_key)

    def test_mult_mode_cap_is_not_normal_hill_500(self):
        fixtures = {row["id"]: row for row in load_fixtures()}
        hill_default = evaluate_drawn_round(fixtures["hill-cap"])
        self.assertEqual(hill_default.maxWin, 500)
        self.assertTrue(hill_default.capped)
        mode_cap = evaluate_drawn_round(
            {
                **fixtures["hill-cap"],
                "maxWin": 6000,
                "costMultiplier": 11.3,
            }
        )
        self.assertEqual(mode_cap.maxWin, 6000)
        self.assertGreater(mode_cap.finalWinX, hill_default.finalWinX)
        self.assertLessEqual(mode_cap.finalWinX, 6000)

    def test_writer_passes_each_published_mode(self):
        import sys
        from pathlib import Path

        from skyjump_resolve import tables_for_mode

        math_root = Path(__file__).resolve().parents[2]
        if str(math_root) not in sys.path:
            sys.path.insert(0, str(math_root))
        from game_config import GameConfig
        from gamestate import GameState

        config = GameConfig()
        self.assertEqual(
            list(config.published_rgs_keys),
            ["BASE", "LARGE_HILL", "SKI_FLYING", "MULT_10_100", "MULT_20_200"],
        )
        gamestate = GameState(config)
        for rgs_key in config.published_rgs_keys:
            tables = tables_for_mode(rgs_key)
            gamestate.betmode = rgs_key
            gamestate.criteria = "basegame"
            gamestate.sim = 11
            gamestate.run_spin(11)
            types = [event["type"] for event in gamestate.book.events]
            result = next(event for event in gamestate.book.events if event["type"] == "skyjumpResult")
            self.assertEqual(types[0], "skyjumpWeather", rgs_key)
            self.assertEqual(result["costMultiplier"], tables["costMultiplier"], rgs_key)
            self.assertEqual(result["maxWin"], tables["maxWin"], rgs_key)
            self.assertEqual(result["hillProfile"], tables["hillId"], rgs_key)
            self.assertEqual(result["multiplierProfile"], tables["multiplierTableId"], rgs_key)
            self.assertLessEqual(result["finalWinX"], tables["maxWin"], rgs_key)
            self.assertIn("finalWin", types, rgs_key)
            payload = gamestate.book.to_json()
            amount = payload["payoutMultiplier"]
            self.assertEqual(amount, result["amount"], rgs_key)
            for event in payload["events"]:
                if event["type"] in {"setWin", "wincap", "setTotalWin", "finalWin", "skyjumpResult"}:
                    self.assertEqual(event["amount"], amount, f"{rgs_key} {event['type']}")

    def test_rgs_amount_tie_cases(self):
        for value in [12.075, 12.025, 1.005, 0.005, 1.015, 0.015, 0.252, 0.588, 2.415]:
            amount = rgs_payout_multiplier(value)
            self.assertEqual(amount, int(round(value * 100)), value)
            self.assertEqual(amount, round_book_amount(value), value)
        self.assertEqual(rgs_payout_multiplier(12.075), 1208)
        self.assertEqual(int(round(round(12.075, 2) * 100)), 1207)
        self.assertEqual(rgs_payout_multiplier(12.025), int(round(12.025 * 100)))
        self.assertEqual(rgs_payout_multiplier(1.005), int(round(1.005 * 100)))
        self.assertEqual(rgs_payout_multiplier(0.005), int(round(0.005 * 100)))

    def test_book_json_uses_same_integer_as_events(self):
        # books.py encodes payoutMultiplier as int(round(payout_multiplier * 100, 0)).
        # Store the already-rounded integer as amount/100 so that path cannot create a
        # second monetary truth.
        for value in [0, 0.252, 0.588, 1.218, 2.415, 12.075, 12.025, 500]:
            amount = rgs_payout_multiplier(value)
            encoded = int(round((amount / 100.0) * 100, 0))
            self.assertEqual(encoded, amount, value)

    def test_stake_lut_format_rejects_cent_resolution(self):
        """Document the installed SDK rule. Do not quantize canonical 0.01x math."""
        self.assertEqual(rgs_payout_multiplier(0.252), 25)
        self.assertEqual(25 % 10, 5)
        self.assertNotEqual(rgs_payout_multiplier(0.252) % 10, 0)
        tenth = int(round(0.252 * 10)) * 10
        self.assertEqual(tenth, 30)
        self.assertNotEqual(tenth, rgs_payout_multiplier(0.252))


if __name__ == "__main__":
    unittest.main()
