"""Thin-weight Phase 6A confirmation. Research only. Does not write live config."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import TIERS
from skyjump_v2_phase6a_engine import Phase6Spec
from skyjump_v2_phase6a_search import OUT, build_context, run_mix, summarise, table_for

# (rejump, wind) taken from FLIGHT_TOKEN. Integer weights, sum stays 1000.
PACKS = {
    "G1": {
        "LARGE_HILL": (10, 1),
        "SKI_FLYING": (18, 3),
        "WORLD_CUP": (24, 6),
        "PERFECT_V": (32, 10),
    },
    "G2": {
        "LARGE_HILL": (12, 1),
        "SKI_FLYING": (22, 4),
        "WORLD_CUP": (30, 8),
        "PERFECT_V": (40, 12),
    },
    "G3": {
        "LARGE_HILL": (14, 1),
        "SKI_FLYING": (24, 4),
        "WORLD_CUP": (32, 8),
        "PERFECT_V": (42, 12),
    },
    "G4": {
        "LARGE_HILL": (16, 1),
        "SKI_FLYING": (28, 4),
        "WORLD_CUP": (36, 8),
        "PERFECT_V": (48, 12),
    },
    "G5": {
        "LARGE_HILL": (12, 2),
        "SKI_FLYING": (22, 6),
        "WORLD_CUP": (30, 10),
        "PERFECT_V": (40, 14),
    },
    "G6": {
        "LARGE_HILL": (8, 2),
        "SKI_FLYING": (16, 5),
        "WORLD_CUP": (24, 8),
        "PERFECT_V": (32, 12),
    },
    "G7": {
        "LARGE_HILL": (18, 0),
        "SKI_FLYING": (30, 6),
        "WORLD_CUP": (40, 10),
        "PERFECT_V": (50, 16),
    },
    "G8": {
        "LARGE_HILL": (10, 0),
        "SKI_FLYING": (20, 6),
        "WORLD_CUP": (28, 10),
        "PERFECT_V": (36, 14),
    },
}

BASELINE_MEAN = 27.45472
WINSOR = 2500.0


def spec_from(pack_id, pack, max_rj=2, ladder="K1", rule="W2", pv="PV1", saturation="B"):
    weights = {tier: table_for(pack[tier]) for tier in TIERS}
    wind_lh = pack["LARGE_HILL"][1]
    return Phase6Spec(
        f"P6A_{pack_id}_{ladder}_{rule}_R{max_rj}_{pv}_{saturation}",
        weights,
        ladder,
        rule,
        saturation,
        "C" if wind_lh else "B",
        pv,
        max_rj,
        8,
    )


def body_stats(rows: list[dict]) -> dict:
    capped = [row["capped"] for row in rows]
    winsor = [min(value, WINSOR) for value in capped]
    total = sum(capped) or 1.0
    tail = sum(value for value in capped if value > WINSOR)
    return {
        "winsorMeanX": statistics.fmean(winsor),
        "tailShare": tail / total,
        "nAboveWinsor": sum(value > WINSOR for value in capped),
        "maxX": max(capped),
    }


def mult_bins(rows: list[dict], p_trigger: float) -> dict:
    bands = [
        ("1x", lambda value: value == 1),
        ("2x", lambda value: value == 2),
        ("3x", lambda value: value == 3),
        ("4-5x", lambda value: 4 <= value <= 5),
        ("6-8x", lambda value: 6 <= value <= 8),
        ("9-15x", lambda value: 9 <= value <= 15),
        ("16x+", lambda value: value >= 16),
    ]
    out = {}
    n = len(rows) or 1
    for name, pred in bands:
        group = [row for row in rows if pred(row["multiplier"])]
        if not group:
            out[name] = {"p": 0.0, "meanRaw": 0.0, "meanPaid": 0.0, "rtpPp": 0.0}
            continue
        mean_paid = statistics.fmean(row["collectorPaid"] for row in group)
        out[name] = {
            "p": len(group) / n,
            "meanRaw": statistics.fmean(row["collectorRaw"] for row in group),
            "meanPaid": mean_paid,
            "rtpPp": mean_paid * (len(group) / n) * p_trigger * 100.0,
        }
    return out


def report(spec, rows, p_trigger, baseline_pp):
    stats = summarise(rows, p_trigger)
    extra = body_stats(rows)
    stats.update(extra)
    inc = stats["rtpPp"] - baseline_pp
    reserve = 96.50 - (71.212 + stats["rtpPp"])
    lh = spec.weights_by_tier["LARGE_HILL"]
    print(
        f"{spec.id}\n  inc={inc:6.2f} reserve={reserve:5.2f} mean={stats['meanX']:.2f} "
        f"winMean={extra['winsorMeanX']:.2f} tailShare={extra['tailShare']:.3f} "
        f"med={stats['medianX']:.2f} pRJ={stats['pRejump']:.3f} pWK={stats['pWind']:.3f} "
        f"mM={stats['meanMult']:.3f} p99={stats['p99X']:.1f} cap={stats['pCap']:.5f} "
        f"drag={stats['meanCapDrag']:.2f} lineRJ={stats['meanLineRejump']:.3f} "
        f"LH={lh['REJUMP']}/{lh['WIND_KEY']} trunc={stats['pTrunc']:.4f} "
        f"lock75={stats['pLock75']:.4f} ev={stats['meanEvents']:.1f}",
        flush=True,
    )
    return stats


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 606
    mode = sys.argv[3] if len(sys.argv) > 3 else "screen"
    ctx = build_context(load_v2_config())
    p_trigger = ctx["mix"]["P_scatterGe3"]
    baseline_pp = BASELINE_MEAN * p_trigger * 100.0
    jobs = [
        spec_from("G1", PACKS["G1"]),
        spec_from("G2", PACKS["G2"]),
        spec_from("G3", PACKS["G3"]),
        spec_from("G4", PACKS["G4"]),
        spec_from("G5", PACKS["G5"]),
        spec_from("G6", PACKS["G6"]),
        spec_from("G7", PACKS["G7"]),
        spec_from("G8", PACKS["G8"]),
    ]
    if mode == "one":
        jobs = [jobs[int(sys.argv[4])]]
    OUT.mkdir(exist_ok=True)
    payload = {"n": n, "seed": seed, "baselineMeanX": BASELINE_MEAN, "pTrigger": p_trigger, "rows": []}
    for spec in jobs:
        rows = run_mix(ctx, spec, n, seed)
        stats = report(spec, rows, p_trigger, baseline_pp)
        stats["id"] = spec.id
        stats["weights"] = spec.weights_by_tier
        stats["ladder"] = spec.ladder
        stats["stageRule"] = spec.stage_rule
        stats["saturation"] = spec.saturation
        stats["perfectV"] = spec.perfect_v
        stats["maxRejumps"] = spec.max_rejumps_per_spin
        stats["availability"] = spec.availability
        stats["bins"] = mult_bins(rows, p_trigger)
        stats["incrementalPp"] = stats["rtpPp"] - baseline_pp
        stats["reservePp"] = 96.50 - (71.212 + stats["rtpPp"])
        stats["newGameRtp"] = 71.212 + stats["rtpPp"]
        payload["rows"].append(stats)
    path = OUT / f"confirm_n{n}_s{seed}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
