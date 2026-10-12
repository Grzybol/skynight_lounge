"""Deterministic Monte Carlo for SkyJump V2 BASE line math."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import exact_line_rtp, exact_perfect_v_prob, exact_scatter_distribution, scatter_on_board
from skyjump_v2_lines import line_win_summary, load_v2_config
from skyjump_v2_reels import board_from_stops, frequency_table

BUCKETS = (
    ("0x", 0.0, 0.0),
    (">0-1x", 0.0, 1.0),
    ("1-2x", 1.0, 2.0),
    ("2-5x", 2.0, 5.0),
    ("5-10x", 5.0, 10.0),
    ("10-25x", 10.0, 25.0),
    ("25-50x", 25.0, 50.0),
    ("50-100x", 50.0, 100.0),
    ("100x+", 100.0, math.inf),
)


def _bucket(win: float) -> str:
    if win <= 0:
        return "0x"
    for name, low, high in BUCKETS[1:]:
        if name == "100x+":
            if win >= 100:
                return name
        elif win > low and win <= high:
            return name
    return "100x+"


def simulate(spins: int, seed: int, config: dict | None = None) -> dict:
    config = config or load_v2_config()
    strips = config["reelModel"]["strips"]
    paytable = config["paytable"]["awards"]
    paylines = config["paylines"]
    scatter_id = config["symbols"]["scatter"]["id"]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    pattern = tuple(config["scatterModel"]["perfectVRows"])
    rng = random.Random(seed)

    total = 0.0
    total_sq = 0.0
    hits = 0
    multi = 0
    win_lines = 0
    winning_pays: list[float] = []
    maximum = 0.0
    ge = {5: 0, 10: 0, 25: 0, 50: 0, 100: 0}
    buckets = {name: 0 for name, _, _ in BUCKETS}
    scatter_hist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, "5+": 0}
    perfect = 0

    for _ in range(spins):
        stops = [rng.randrange(len(strip)) for strip in strips]
        board = board_from_stops(strips, stops)
        win, line_hits = line_win_summary(
            board,
            paylines=paylines,
            paytable=paytable,
            scatter_id=scatter_id,
            regular_ids=regular_ids,
        )
        scatter = scatter_on_board(board, scatter_id, pattern)
        total += win
        total_sq += win * win
        maximum = max(maximum, win)
        buckets[_bucket(win)] += 1
        count = scatter["count"]
        if count >= 5:
            scatter_hist["5+"] += 1
        else:
            scatter_hist[count] += 1
        if scatter["perfectV"]:
            perfect += 1
        if win > 0:
            hits += 1
            winning_pays.append(win)
            win_lines += line_hits
            if line_hits > 1:
                multi += 1
            for threshold in ge:
                if win >= threshold:
                    ge[threshold] += 1

    mean = total / spins
    variance = max(0.0, total_sq / spins - mean * mean)
    std = math.sqrt(variance)
    winning_pays.sort()
    median = winning_pays[len(winning_pays) // 2] if winning_pays else 0.0
    zero = spins - hits
    exact = exact_line_rtp(strips, paylines, paytable)
    scatter_exact = exact_scatter_distribution(strips, scatter_id)
    return {
        "nonProduction": True,
        "mathStatus": "PHASE 2 PROVISIONAL BASE MATH",
        "spins": spins,
        "seed": seed,
        "theoreticalLineRtp": exact["lineRtp"],
        "simulatedLineRtp": mean,
        "rtpDelta": mean - exact["lineRtp"],
        "hitRate": hits / spins,
        "zeroWinRate": zero / spins,
        "multiLineHitRate": multi / spins,
        "avgWinGivenWin": (sum(winning_pays) / hits) if hits else 0.0,
        "medianWinningPayout": median,
        "stdDev": std,
        "volatilityProxy": std,
        "maxObservedLineWinX": maximum,
        "pWinGe": {str(key): ge[key] / spins for key in ge},
        "avgWinningPaylines": (win_lines / hits) if hits else 0.0,
        "payoutDistribution": {name: buckets[name] / spins for name, _, _ in BUCKETS},
        "scatterCounts": {
            str(key): scatter_hist[key] / spins for key in (0, 1, 2, 3, 4, "5+")
        },
        "scatterGe3": sum(scatter_hist[key] for key in (3, 4, "5+")) / spins,
        "perfectVRate": perfect / spins,
        "exactScatter": {str(key): scatter_exact.get(int(key), 0.0) if key != "5+" else sum(v for k, v in scatter_exact.items() if k >= 5) for key in (0, 1, 2, 3, 4, "5+")},
        "exactScatterGe3": sum(prob for count, prob in scatter_exact.items() if count >= 3),
        "exactPerfectV": exact_perfect_v_prob(strips, pattern, scatter_id),
        "frequencies": frequency_table(strips),
        "bySymbolTheoretical": exact["bySymbol"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spins", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()
    report = simulate(args.spins, args.seed)
    text = json.dumps(report, indent=2)
    print(text[:2000])
    print("...")
    print(
        f"theo={report['theoreticalLineRtp']:.6f} sim={report['simulatedLineRtp']:.6f} "
        f"hit={report['hitRate']:.4f} spins={report['spins']}"
    )
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
