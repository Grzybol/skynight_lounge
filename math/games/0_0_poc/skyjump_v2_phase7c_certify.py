"""Phase 7C certification helpers: BASE MC, replay parity, grain, schema."""

from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path

from skyjump_v2_events import round_book_amount
from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_freespins import resolve_v2_buy_round, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import base_trigger_mix

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / "phase7c_research"


def validate_book_events(events: list[dict]) -> None:
    if not events:
        raise ValueError("empty events")
    finals = [e for e in events if e.get("type") == "finalWin"]
    if len(finals) != 1:
        raise ValueError(f"expected one finalWin, got {len(finals)}")
    sets = [e for e in events if e.get("type") == "setTotalWin"]
    if not sets:
        raise ValueError("missing setTotalWin")
    # last settlement pair
    if events[-1]["type"] != "finalWin" or events[-2]["type"] != "setTotalWin":
        raise ValueError("settlement must end the book")
    if events[-1]["amount"] != events[-2]["amount"]:
        raise ValueError("setTotalWin/finalWin amount mismatch")
    amount = int(events[-1]["amount"])
    if amount < 0 or amount > 5_000_000:
        raise ValueError("amount out of range")
    if amount > 0 and amount % 10 != 0:
        raise ValueError("payout grain")
    wr_idxs = [i for i, e in enumerate(events) if e.get("type") == "skyjumpWorldRecord"]
    if wr_idxs:
        wr_i = wr_idxs[0]
        after = events[wr_i + 1 :]
        for e in after:
            if e["type"] in {
                "skyjumpLineWins",
                "skyjumpMysteryResolve",
                "skyjumpRejumpStart",
                "skyjumpJudgeCollect",
                "skyjumpHeadJudgeCollect",
            }:
                raise ValueError("monetary feature after WR")
    # indices
    for i, e in enumerate(events):
        if e.get("index") is not None and int(e["index"]) != i:
            raise ValueError("non-monotonic index")


def reducer_payout_from_events(events: list[dict]) -> float:
    """Frontend-compatible: finalWin amount / 100."""
    for e in reversed(events):
        if e.get("type") == "finalWin":
            return float(e["amount"]) / 100.0
    raise ValueError("no finalWin")


def base_mc(n: int = 200_000, seed: int = 42) -> dict:
    cfg = load_v2_config()
    cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
    mix = base_trigger_mix(cfg)
    p_trig = float(mix["P_scatterGe3"])
    # Exact BASE line RTP (PT2H)
    line = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], cfg["paytable"]["awards"])["lineRtp"] * 100
    xs = []
    bonus_xs = []
    for i in range(n):
        result = resolve_v2_round(random.Random(seed + i), config=cfg)
        xs.append(float(result["roundWinXCapped"]))
        if result["isBonus"]:
            bonus_xs.append(float(result["roundWinXCapped"]))
    mean = statistics.fmean(xs)
    se = math.sqrt(statistics.pvariance(xs) / n)
    # Analytical WR add (paid-round)
    p_wr = float(cert["candidates"]["H2"]["wr"]["pPaidRoundApprox"])
    e_fill = float(cert["candidates"]["H2"]["wr"]["eFillUsed"])
    # Natural MC almost never hits WR; add analytical
    mean_adj = mean + p_wr * e_fill
    return {
        "n": n,
        "mcMeanX": mean,
        "mcMeanAdjWrX": mean_adj,
        "mcRtpPct": mean_adj * 100.0,
        "sePp": se * 100.0,
        "ci95": [(mean_adj - 1.96 * se) * 100, (mean_adj + 1.96 * se) * 100],
        "exactBaseLinePct": line,
        "pTrigger": p_trig,
        "bonusHits": len(bonus_xs),
        "pWrPaid": p_wr,
        "wrContributionPp": p_wr * e_fill * 100.0,
        "artifactProjected": 96.290,
    }


def replay_sample(mode: str, n: int = 1000) -> dict:
    import zstandard as zstd

    path = HERE / "library_v2" / "publish_files" / f"books_{mode}.jsonl.zst"
    if not path.exists():
        return {"ok": False, "reason": "missing books"}
    dctx = zstd.ZstdDecompressor()
    checked = 0
    mismatches = 0
    with path.open("rb") as fh:
        with dctx.stream_reader(fh) as reader:
            buf = b""
            while checked < n:
                chunk = reader.read(1 << 20)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf and checked < n:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    book = json.loads(line.decode("utf-8"))
                    validate_book_events(book["events"])
                    redux = reducer_payout_from_events(book["events"])
                    expected = book["payoutMultiplier"] / 100.0
                    if abs(redux - expected) > 1e-9:
                        mismatches += 1
                    checked += 1
    return {"ok": mismatches == 0, "checked": checked, "mismatches": mismatches}


if __name__ == "__main__":
    RESEARCH.mkdir(parents=True, exist_ok=True)
    base = base_mc(50_000)
    (RESEARCH / "base_mc.json").write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(base, indent=2))
