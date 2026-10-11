"""Phase 3 Monte Carlo: lines + Coach + Mystery + latent token exposure."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import (
    exact_line_rtp,
    exact_perfect_v_prob,
    exact_scatter_distribution,
    exact_symbol_window_distribution,
    scatter_on_board,
)
from skyjump_v2_features import resolve_features
from skyjump_v2_lines import line_win_summary, load_v2_config
from skyjump_v2_reels import COACH_ID, REGULAR_IDS, board_from_stops, frequency_table
from skyjump_v2_simulate import BUCKETS, _bucket
from skyjump_v2_tokens import exact_token_value_distribution, percentile_from_dist, token_tables


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(math.ceil(q / 100.0 * len(ordered)) - 1)))
    return float(ordered[index])


def simulate_features(spins: int, seed: int, config: dict | None = None) -> dict:
    config = config or load_v2_config()
    strips = config["reelModel"]["strips"]
    paytable = config["paytable"]["awards"]
    paylines = config["paylines"]
    scatter_id = config["symbols"]["scatter"]["id"]
    regular_ids = {row["id"] for row in config["symbols"]["regular"]}
    pattern = tuple(config["scatterModel"]["perfectVRows"])
    rng = random.Random(seed)
    tables = token_tables(config)

    total = 0.0
    total_sq = 0.0
    hits = 0
    multi = 0
    win_lines = 0
    winning_pays: list[float] = []
    premium_ge5 = 0
    premium_hits = Counter()
    maximum = 0.0
    ge = {5: 0, 10: 0, 25: 0, 50: 0, 100: 0}
    buckets = {name: 0 for name, _, _ in BUCKETS}
    scatter_hist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, "5+": 0}
    perfect = 0

    coach_any = 0
    coach_ge2 = 0
    coach_hist = Counter()
    selected = Counter()
    mystery_counts: list[int] = []
    mystery_by_type: dict[str, list[int]] = {symbol: [] for symbol in REGULAR_IDS}
    latent_coach: list[float] = []
    latent_spin = 0.0
    token_any = 0
    tier_spins = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    tail = {100: 0, 500: 0, 2500: 0, 10000: 0, 50000: 0}
    max_latent_spin = 0.0
    max_mystery = 0
    token_values: list[float] = []
    noop = 0

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
        features = resolve_features(board, rng, config)

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
        coaches = features["coaches"]
        n_coach = len(coaches)
        coach_hist[n_coach] += 1
        if n_coach:
            coach_any += 1
        if n_coach >= 2:
            coach_ge2 += 1
        spin_latent = features["latentTokenValueX"]
        latent_spin += spin_latent
        max_latent_spin = max(max_latent_spin, spin_latent)
        if features["resolves"]:
            token_any += 1
        spin_tiers = set()
        spin_max = 0.0
        for token in features["resolves"]:
            token_values.append(token["tokenValueX"])
            spin_tiers.add(token["tokenTier"])
            spin_max = max(spin_max, token["tokenValueX"])
        for tier in spin_tiers:
            tier_spins[tier] += 1
        for threshold in tail:
            if spin_max >= threshold:
                tail[threshold] += 1
        for selected_id, mystery_n in zip(
            features["selectedSymbolIds"], features["mysteriesPerCoach"], strict=True
        ):
            selected[selected_id] += 1
            mystery_counts.append(mystery_n)
            mystery_by_type[selected_id].append(mystery_n)
            max_mystery = max(max_mystery, mystery_n)
        if coaches:
            active = max(1, sum(1 for coach in coaches if not coach.get("noOp")))
            for _coach in coaches:
                if not _coach.get("noOp"):
                    latent_coach.append(spin_latent / active)
        noop += sum(1 for coach in coaches if coach.get("noOp"))

        premium_ge5_spin = False
        if win > 0:
            for rows in paylines.values():
                first = board[0][rows[0]]
                if first not in {"P1", "P2", "P3"}:
                    continue
                match = 1
                for reel in range(1, 5):
                    if board[reel][rows[reel]] != first:
                        break
                    match += 1
                if match >= 3:
                    premium_hits[f"{first}:{min(match, 5)}"] += 1
                    payout = float(paytable.get(first, {}).get(str(min(match, 5)), 0) or 0)
                    if payout >= 5:
                        premium_ge5_spin = True
        if premium_ge5_spin:
            premium_ge5 += 1

    mean = total / spins
    variance = max(0.0, total_sq / spins - mean * mean)
    std = math.sqrt(variance)
    winning_pays.sort()
    median = winning_pays[len(winning_pays) // 2] if winning_pays else 0.0
    exact = exact_line_rtp(strips, paylines, paytable)
    scatter_exact = exact_scatter_distribution(strips, scatter_id)
    coach_exact = exact_symbol_window_distribution(strips, COACH_ID)
    token_exact = exact_token_value_distribution(tables)
    return {
        "nonProduction": True,
        "mathStatus": "PHASE 3 PROVISIONAL FEATURE MATH",
        "spins": spins,
        "seed": seed,
        "theoreticalLineRtp": exact["lineRtp"],
        "simulatedLineRtp": mean,
        "rtpDelta": mean - exact["lineRtp"],
        "hitRate": hits / spins,
        "zeroWinRate": (spins - hits) / spins,
        "multiLineHitRate": multi / spins,
        "avgWinGivenWin": (sum(winning_pays) / hits) if hits else 0.0,
        "medianWinningPayout": median,
        "stdDev": std,
        "volatilityProxy": std,
        "maxObservedLineWinX": maximum,
        "pWinGe": {str(key): ge[key] / spins for key in ge},
        "avgWinningPaylines": (win_lines / hits) if hits else 0.0,
        "payoutDistribution": {name: buckets[name] / spins for name, _, _ in BUCKETS},
        "scatterCounts": {str(key): scatter_hist[key] / spins for key in (0, 1, 2, 3, 4, "5+")},
        "scatterGe3": sum(scatter_hist[key] for key in (3, 4, "5+")) / spins,
        "perfectVRate": perfect / spins,
        "exactScatter": {
            str(key): scatter_exact.get(int(key), 0.0) if key != "5+" else sum(v for k, v in scatter_exact.items() if k >= 5)
            for key in (0, 1, 2, 3, 4, "5+")
        },
        "exactScatterGe3": sum(prob for count, prob in scatter_exact.items() if count >= 3),
        "exactPerfectV": exact_perfect_v_prob(strips, pattern, scatter_id),
        "frequencies": frequency_table(strips),
        "bySymbolTheoretical": exact["bySymbol"],
        "coach": {
            "pAny": coach_any / spins,
            "pGe2": coach_ge2 / spins,
            "hist": {str(key): coach_hist[key] / spins for key in sorted(coach_hist)},
            "exactAny": 1.0 - coach_exact.get(0, 0.0),
            "exactGe2": sum(prob for count, prob in coach_exact.items() if count >= 2),
            "noOp": noop / spins,
            "selection": {key: selected[key] / max(1, sum(selected.values())) for key in REGULAR_IDS},
        },
        "mysteriesPerCoach": {
            "mean": (sum(mystery_counts) / len(mystery_counts)) if mystery_counts else 0.0,
            "median": _pct(mystery_counts, 50),
            "p90": _pct(mystery_counts, 90),
            "p95": _pct(mystery_counts, 95),
            "p99": _pct(mystery_counts, 99),
            "max": max_mystery,
            "n": len(mystery_counts),
            "bySelected": {
                symbol: {
                    "mean": (sum(values) / len(values)) if values else 0.0,
                    "median": _pct(values, 50),
                    "p90": _pct(values, 90),
                    "p99": _pct(values, 99),
                    "max": max(values) if values else 0,
                    "n": len(values),
                }
                for symbol, values in mystery_by_type.items()
            },
        },
        "tokenExact": token_exact,
        "latent": {
            "perMysteryExpected": token_exact["expected"],
            "perMysteryMedian": percentile_from_dist(token_exact["byValue"], 50),
            "perMysteryP90": percentile_from_dist(token_exact["byValue"], 90),
            "perMysteryP95": percentile_from_dist(token_exact["byValue"], 95),
            "perMysteryP99": percentile_from_dist(token_exact["byValue"], 99),
            "perMysteryP999": percentile_from_dist(token_exact["byValue"], 99.9),
            "perMysteryMaxPossible": max(token_exact["byValue"]),
            "perSpinExpected": latent_spin / spins,
            "perCoachMean": (sum(latent_coach) / len(latent_coach)) if latent_coach else 0.0,
            "perCoachMedian": _pct(latent_coach, 50),
            "perCoachP90": _pct(latent_coach, 90),
            "perCoachP95": _pct(latent_coach, 95),
            "perCoachP99": _pct(latent_coach, 99),
            "perSpinMaxObserved": max_latent_spin,
            "pAnyToken": token_any / spins,
            "pTier": {str(tier): tier_spins[tier] / spins for tier in tier_spins},
        },
        "tailPerSpin": {str(key): tail[key] / spins for key in tail},
        "premium": {
            "lineHits": dict(premium_hits),
            "pSpinPremiumLineGe5": premium_ge5 / spins,
        },
        "observedTokenMean": (sum(token_values) / len(token_values)) if token_values else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spins", type=int, default=5_000_000)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()
    report = simulate_features(args.spins, args.seed)
    print(
        json.dumps(
            {
                "theo": report["theoreticalLineRtp"],
                "sim": report["simulatedLineRtp"],
                "hit": report["hitRate"],
                "pCoach": report["coach"]["pAny"],
                "pCoach2": report["coach"]["pGe2"],
                "mystMean": report["mysteriesPerCoach"]["mean"],
                "latentSpin": report["latent"]["perSpinExpected"],
                "tokenEV": report["tokenExact"]["expected"],
            },
            indent=2,
        )
    )
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
