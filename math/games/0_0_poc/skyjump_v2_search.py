"""Deterministic BASE line-game search. Exact RTP; optional short MC for hit-rate."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_exact import exact_line_rtp, exact_perfect_v_prob, exact_scatter_distribution
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reels import (
    HIERARCHY,
    REGULAR_IDS,
    SCATTER_ID,
    assert_hierarchy,
    grain_ok,
    longest_run,
    mix_strip,
)

PAYTABLE_FAMILIES = [
    {
        "P1": {"3": 2.0, "4": 8.0, "5": 30.0},
        "P2": {"3": 1.5, "4": 5.0, "5": 18.0},
        "P3": {"3": 1.2, "4": 4.0, "5": 12.0},
        "M1": {"3": 0.8, "4": 2.5, "5": 8.0},
        "M2": {"3": 0.6, "4": 2.0, "5": 6.0},
        "M3": {"3": 0.5, "4": 1.5, "5": 5.0},
        "L1": {"3": 0.4, "4": 1.2, "5": 3.0},
        "L2": {"3": 0.3, "4": 1.0, "5": 2.5},
        "L3": {"3": 0.2, "4": 0.8, "5": 2.0},
    },
    {
        "P1": {"3": 2.5, "4": 10.0, "5": 40.0},
        "P2": {"3": 2.0, "4": 6.0, "5": 20.0},
        "P3": {"3": 1.5, "4": 5.0, "5": 15.0},
        "M1": {"3": 1.0, "4": 3.0, "5": 8.0},
        "M2": {"3": 0.8, "4": 2.5, "5": 6.0},
        "M3": {"3": 0.6, "4": 2.0, "5": 5.0},
        "L1": {"3": 0.5, "4": 1.5, "5": 4.0},
        "L2": {"3": 0.4, "4": 1.2, "5": 3.0},
        "L3": {"3": 0.3, "4": 1.0, "5": 2.5},
    },
    {
        "P1": {"3": 3.0, "4": 12.0, "5": 50.0},
        "P2": {"3": 2.0, "4": 8.0, "5": 25.0},
        "P3": {"3": 1.5, "4": 5.0, "5": 15.0},
        "M1": {"3": 1.0, "4": 3.5, "5": 10.0},
        "M2": {"3": 0.8, "4": 2.5, "5": 7.0},
        "M3": {"3": 0.6, "4": 2.0, "5": 5.0},
        "L1": {"3": 0.4, "4": 1.5, "5": 4.0},
        "L2": {"3": 0.3, "4": 1.2, "5": 3.0},
        "L3": {"3": 0.2, "4": 1.0, "5": 2.5},
    },
    {
        "P1": {"3": 2.0, "4": 10.0, "5": 35.0},
        "P2": {"3": 1.5, "4": 6.0, "5": 20.0},
        "P3": {"3": 1.2, "4": 4.0, "5": 12.0},
        "M1": {"3": 0.8, "4": 2.5, "5": 8.0},
        "M2": {"3": 0.7, "4": 2.0, "5": 6.0},
        "M3": {"3": 0.5, "4": 1.6, "5": 4.5},
        "L1": {"3": 0.4, "4": 1.2, "5": 3.5},
        "L2": {"3": 0.3, "4": 1.0, "5": 2.5},
        "L3": {"3": 0.2, "4": 0.8, "5": 2.0},
    },
]


def scale_paytable(table: dict, three: float, four: float, five: float) -> dict:
    out = {}
    for symbol, awards in table.items():
        scaled = {
            "3": round(awards["3"] * three, 1),
            "4": round(awards["4"] * four, 1),
            "5": round(awards["5"] * five, 1),
        }
        out[symbol] = scaled
    return out


def paytable_legal(table: dict) -> bool:
    previous = None
    for symbol in HIERARCHY:
        awards = table[symbol]
        if not (awards["3"] < awards["4"] < awards["5"]):
            return False
        if not all(grain_ok(value) and value > 0 for value in awards.values()):
            return False
        if previous is not None:
            if awards["3"] > previous["3"] or awards["5"] > previous["5"]:
                return False
        previous = awards
    return True


def count_templates(length: int, scatter: int) -> list[dict[str, int]]:
    room = length - scatter
    templates = []
    # (P1,P2,P3,M1,M2,M3,L1,L2,L3)
    cores = [
        (1, 2, 3, 4, 5, 6, 7, 8, 9),
        (1, 2, 3, 4, 5, 6, 8, 9, 11),
        (1, 2, 4, 5, 6, 7, 8, 9, 10),
        (2, 3, 4, 5, 6, 7, 8, 9, 10),
        (1, 2, 3, 5, 6, 7, 8, 10, 12),
        (1, 3, 4, 5, 6, 7, 8, 9, 11),
        (2, 3, 4, 5, 6, 7, 9, 10, 12),
        (1, 2, 3, 4, 5, 6, 9, 10, 12),
    ]
    for core in cores:
        total = sum(core)
        if total > room:
            continue
        leftover = room - total
        counts = dict(zip(REGULAR_IDS, core, strict=True))
        # dump leftover into lows while keeping hierarchy
        extra = leftover
        while extra > 0:
            if counts["L3"] <= counts["L2"] + 2:
                counts["L3"] += 1
            elif counts["L2"] <= counts["L1"] + 2:
                counts["L2"] += 1
            else:
                counts["L1"] += 1
            extra -= 1
        counts[SCATTER_ID] = scatter
        if sum(counts.values()) != length:
            continue
        try:
            assert_hierarchy({key: counts[key] for key in REGULAR_IDS})
        except ValueError:
            continue
        templates.append(counts)
    return templates


def jitter_counts(base: dict[str, int], reel: int) -> dict[str, int]:
    counts = dict(base)
    if reel in (0, 4) and counts["L3"] > counts["L2"]:
        counts["L3"] -= 1
        counts["L1"] += 1
    if reel == 2 and counts["P1"] >= 1 and counts["L3"] > counts["L2"]:
        counts["P3"] += 1
        counts["L3"] -= 1
    if reel == 1 and counts["M1"] < counts["M2"]:
        counts["M1"] += 1
        counts["M3"] -= 1
        if counts["M3"] < counts["M2"]:
            counts["M3"] += 1
            counts["M2"] -= 1
    return counts


def score_candidate(rtp: float, scatter_ge3: float, max_run: int, p1_share: float, l3_share: float) -> float:
    target = 0.60
    rtp_pen = abs(rtp - target) * 12
    if rtp < 0.55 or rtp > 0.66:
        rtp_pen += 2.0
    scatter_pen = 0.0
    if scatter_ge3 <= 0:
        scatter_pen = 5.0
    else:
        one_in = 1.0 / scatter_ge3
        if one_in < 80:
            scatter_pen = (80 - one_in) / 40
        elif one_in > 280:
            scatter_pen = (one_in - 280) / 200
    run_pen = max(0, max_run - 2) * 0.35
    hier_pen = 0.0
    if p1_share > l3_share * 0.45:
        hier_pen += 1.5
    if l3_share < 0.12:
        hier_pen += 0.8
    return rtp_pen + scatter_pen + run_pen + hier_pen


def search(limit: int = 80) -> list[dict]:
    config = load_v2_config()
    paylines = config["paylines"]
    candidates = []
    seen = set()
    for length in (48, 52, 56, 60):
        for scatter in (1,):
            for template in count_templates(length, scatter):
                for family_index, family in enumerate(PAYTABLE_FAMILIES):
                    for three, four, five in (
                        (1.0, 1.0, 1.0),
                        (1.2, 1.0, 0.9),
                        (1.4, 1.1, 1.0),
                        (1.6, 1.1, 0.9),
                        (0.9, 1.0, 1.2),
                        (1.3, 1.2, 1.1),
                    ):
                        paytable = scale_paytable(family, three, four, five)
                        if not paytable_legal(paytable):
                            continue
                        key = (length, family_index, three, four, five, tuple(sorted(template.items())))
                        if key in seen:
                            continue
                        seen.add(key)
                        rng = random.Random(20260921 + length * 17 + family_index)
                        strips = []
                        max_run = 1
                        ok = True
                        for reel in range(5):
                            counts = jitter_counts(template, reel)
                            if sum(counts.values()) != length:
                                ok = False
                                break
                            try:
                                assert_hierarchy({symbol: counts[symbol] for symbol in REGULAR_IDS})
                            except ValueError:
                                counts = dict(template)
                            strip = mix_strip(counts, rng)
                            max_run = max(max_run, longest_run(strip))
                            strips.append(strip)
                        if not ok:
                            continue
                        rtp = exact_line_rtp(strips, paylines, paytable)["lineRtp"]
                        scatter_dist = exact_scatter_distribution(strips)
                        ge3 = sum(prob for count, prob in scatter_dist.items() if count >= 3)
                        freqs = [strip.count("P1") / length for strip in strips]
                        l3 = [strip.count("L3") / length for strip in strips]
                        p1_share = sum(freqs) / 5
                        l3_share = sum(l3) / 5
                        penalty = score_candidate(rtp, ge3, max_run, p1_share, l3_share)
                        candidates.append(
                            {
                                "score": penalty,
                                "lineRtp": rtp,
                                "scatterGe3": ge3,
                                "perfectV": exact_perfect_v_prob(strips),
                                "maxRun": max_run,
                                "length": length,
                                "paytable": paytable,
                                "strips": strips,
                                "template": template,
                                "family": family_index,
                                "scale": [three, four, five],
                            }
                        )
                        if len(candidates) >= limit * 6:
                            break
                    if len(candidates) >= limit * 6:
                        break
                if len(candidates) >= limit * 6:
                    break
            if len(candidates) >= limit * 6:
                break
        if len(candidates) >= limit * 6:
            break
    candidates.sort(key=lambda row: row["score"])
    return candidates[: max(12, limit)]


def main() -> None:
    rows = search()
    summary = []
    for index, row in enumerate(rows[:8]):
        summary.append(
            {
                "rank": index + 1,
                "score": round(row["score"], 4),
                "lineRtp": round(row["lineRtp"], 6),
                "scatterGe3": row["scatterGe3"],
                "scatterOneIn": None if row["scatterGe3"] <= 0 else round(1 / row["scatterGe3"], 1),
                "perfectVOneIn": round(1 / row["perfectV"], 1) if row["perfectV"] else None,
                "maxRun": row["maxRun"],
                "length": row["length"],
                "family": row["family"],
                "scale": row["scale"],
            }
        )
        print(json.dumps(summary[-1]))
    out = HERE / "skyjump_v2_search_preview.json"
    payload = {
        "nonProduction": True,
        "candidates": [
            {
                **{key: row[key] for key in ("score", "lineRtp", "scatterGe3", "perfectV", "maxRun", "length", "family", "scale", "template", "paytable")},
                "strips": row["strips"],
            }
            for row in rows[:5]
        ],
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
