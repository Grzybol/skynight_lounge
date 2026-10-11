"""Phase 7C — production math freeze: books, LUT, RTP, buy costs, fingerprint."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from skyjump_v2_events import round_book_amount
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c_certify import reducer_payout_from_events, validate_book_events

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESEARCH = HERE / "phase7c_research"
LIBRARY = HERE / "library_v2" / "publish_files"
STAGING = REPO / "stake-upload" / "math"
EXPECTED_SHA = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"
MODES = ("BASE", "LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
CEILING = 0.967
SPREAD_MAX_PP = 0.50


def _read_lut(path: Path) -> list[tuple[int, int, int]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            bid, w, pay = line.split(",")
            rows.append((int(bid), int(w), int(pay)))
    return rows


def _lut_rtp(rows: list[tuple[int, int, int]], cost: float) -> float:
    num = sum((pay / 100.0) * w for _, w, pay in rows)
    den = sum(w * cost for _, w, _ in rows)
    return num / den if den else 0.0


class Phase7CTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_v2_config()
        cls.buy = json.loads((RESEARCH / "buy_ev.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((RESEARCH / "pre_cert_freeze.json").read_text(encoding="utf-8"))
        cls.report = json.loads((RESEARCH / "books_report.json").read_text(encoding="utf-8"))
        cls.base_cert = json.loads((RESEARCH / "base_cert.json").read_text(encoding="utf-8"))
        cls.fingerprint = None
        if (RESEARCH / "production_fingerprint.json").exists():
            cls.fingerprint = json.loads((RESEARCH / "production_fingerprint.json").read_text(encoding="utf-8"))

    def test_00_pre_cert_freeze_sha(self):
        self.assertTrue(self.freeze["match"])
        self.assertEqual(self.freeze["configSha256"], EXPECTED_SHA)

    def test_01_no_v1_resurrected_modes(self):
        modes = self.cfg.get("buyModes") or {}
        for banned in ("MULT_10_100", "MULT_20_200", "mult_10_100", "mult_20_200"):
            self.assertNotIn(banned, modes)

    def test_02_buy_costs_from_lut_band(self):
        self.assertEqual(self.buy.get("pricedFrom"), "LUT_mean")
        for tier in TIERS:
            cost = self.buy["chosenCosts"][tier]
            rtp = self.report["modes"][tier]["lutRtp"]
            self.assertAlmostEqual(cost, self.report["costs"][tier], places=6)
            self.assertLessEqual(rtp, CEILING + 1e-12, tier)
            self.assertGreaterEqual(rtp, 0.964 - 1e-6, tier)
        buy_rtps = [self.report["modes"][t]["lutRtp"] for t in TIERS]
        self.assertLessEqual((max(buy_rtps) - min(buy_rtps)) * 100, SPREAD_MAX_PP)

    def test_03_artifacts_present_and_clean(self):
        self.assertTrue((LIBRARY / "index.json").exists())
        for mode in MODES:
            self.assertTrue((LIBRARY / f"books_{mode}.jsonl.zst").exists(), mode)
            self.assertTrue((LIBRARY / f"lookUpTable_{mode}_0.csv").exists(), mode)
        self.assertTrue(STAGING.exists())
        leaked = [
            p.name
            for p in STAGING.rglob("*")
            if p.is_file()
            and (p.suffix in {".md", ".py"} or (p.suffix == ".json" and p.name != "index.json"))
        ]
        self.assertEqual(leaked, [])

    def test_04_book_counts_lut_integrity(self):
        for mode in MODES:
            info = self.report["modes"][mode]
            self.assertGreaterEqual(info["bookCount"], 100_000)
            rows = _read_lut(LIBRARY / f"lookUpTable_{mode}_0.csv")
            self.assertEqual(len(rows), info["bookCount"])
            self.assertTrue(all(w > 0 for _, w, _ in rows))
            self.assertTrue(all(0 <= pay <= 5_000_000 for _, _, pay in rows))
            self.assertTrue(all(pay == 0 or pay % 10 == 0 for _, _, pay in rows))
            cost = float(info["cost"])
            rtp = _lut_rtp(rows, cost)
            self.assertAlmostEqual(rtp, info["lutRtp"], places=9)

    def test_05_base_exceeds_ceiling_calibration_needed(self):
        base_rtp = self.report["modes"]["BASE"]["lutRtp"]
        self.assertGreater(base_rtp, CEILING)
        self.assertEqual(self.base_cert["classification"], "NEEDS HUMAN RTP CALIBRATION")
        self.assertFalse(self.base_cert["wrOnlyCanReachBand"])
        # mathVersion must remain pre-freeze until BASE is in band
        self.assertEqual(int(self.cfg["meta"]["mathVersion"]), 2)

    def test_06_wr_weighted_probability_base(self):
        cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
        expected = float(cert["candidates"]["H2"]["wr"]["pPaidRoundApprox"])
        rows = _read_lut(LIBRARY / "lookUpTable_BASE_0.csv")
        # Recover effective p from book criteria via report field when present
        got = float(self.report["modes"]["BASE"]["effectiveWrP"])
        self.assertAlmostEqual(got, expected, delta=max(expected * 0.05, 1e-12))

    def test_07_max_win_and_grain(self):
        self.assertEqual(round_book_amount(0.1), 10)
        self.assertEqual(round_book_amount(50_000), 5_000_000)
        for mode in MODES:
            self.assertLessEqual(self.report["modes"][mode]["maxPayoutX"], 50_000.0)
            self.assertGreaterEqual(self.report["modes"][mode]["minPayoutX"], 0.0)

    def test_08_replay_parity_sample(self):
        try:
            import zstandard as zstd
        except ImportError:
            self.skipTest("zstandard missing")
        for mode in MODES:
            path = LIBRARY / f"books_{mode}.jsonl.zst"
            dctx = zstd.ZstdDecompressor()
            checked = 0
            with path.open("rb") as fh, dctx.stream_reader(fh) as reader:
                buf = b""
                while checked < 200:
                    chunk = reader.read(1 << 20)
                    if not chunk:
                        break
                    buf += chunk
                    while b"\n" in buf and checked < 200:
                        line, buf = buf.split(b"\n", 1)
                        if not line.strip():
                            continue
                        book = json.loads(line.decode("utf-8"))
                        validate_book_events(book["events"])
                        redux = reducer_payout_from_events(book["events"])
                        expected = book["payoutMultiplier"] / 100.0
                        self.assertAlmostEqual(redux, expected, places=9, msg=f"{mode} id={book['id']}")
                        blob = json.dumps(book)
                        self.assertNotIn("localDemo", blob)
                        self.assertNotIn("devSynthetic", blob)
                        self.assertNotIn("researchCandidate", blob)
                        checked += 1
            self.assertGreaterEqual(checked, 200, mode)

    def test_09_canonical_buy_modes_sidecar(self):
        path = RESEARCH / "buy_modes.json"
        self.assertTrue(path.exists())
        modes = json.loads(path.read_text(encoding="utf-8"))
        by_key = {m["rgsKey"]: m for m in modes["modes"]}
        self.assertEqual(by_key["BASE"]["costMultiplier"], 1.0)
        for tier in TIERS:
            self.assertAlmostEqual(
                float(by_key[tier]["costMultiplier"]),
                float(self.buy["chosenCosts"][tier]),
                places=6,
            )

    def test_10_no_frontend_rng_in_books_pipeline(self):
        src = (HERE / "skyjump_v2_phase7c_books.py").read_text(encoding="utf-8")
        self.assertIn("resolve_v2_round", src)
        self.assertIn("resolve_v2_buy_round", src)
        self.assertNotIn("Math.random", src)

    def test_11_index_costs_match(self):
        index = json.loads((LIBRARY / "index.json").read_text(encoding="utf-8"))
        by_name = {m["name"]: m for m in index["modes"]}
        for mode in MODES:
            self.assertAlmostEqual(float(by_name[mode]["cost"]), float(self.report["costs"][mode]), places=6)


if __name__ == "__main__":
    unittest.main()
