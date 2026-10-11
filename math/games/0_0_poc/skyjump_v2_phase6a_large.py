"""Large-sample Phase 6A finalists. Research only. Does not write live config."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import TIERS
from skyjump_v2_phase6a_engine import Phase6Spec
from skyjump_v2_phase6a_confirm import body_stats, mult_bins, spec_from
from skyjump_v2_phase6a_search import OUT, build_context, run_mix, run_tier, summarise, table_for, zero_feature

BASELINE_MEAN = 27.45472
# Phase 5C sample books measured 281 uncompressed bytes per event.
BYTES_PER_EVENT = 281
# A rejump board event is larger than an average Phase 5C event.
EXTRA_BYTES_PER_REJUMP = 4 * 420

G1 = {
    "LARGE_HILL": (10, 1),
    "SKI_FLYING": (18, 3),
    "WORLD_CUP": (24, 6),
    "PERFECT_V": (32, 10),
}
# Same total feature weight as G1, with Large Hill wind moved onto higher tiers.
G1_B = {
    "LARGE_HILL": (11, 0),
    "SKI_FLYING": (18, 4),
    "WORLD_CUP": (24, 7),
    "PERFECT_V": (32, 11),
}


def _blank() -> Phase6Spec:
    weights = {tier: table_for((0, 0)) for tier in TIERS}
    return Phase6Spec("P6A_BLANK", weights, "K1", "W2", "B", "C", "PV1", 0, 8)


def jobs_for(worker: str) -> list[tuple]:
    """(kind, spec, n, seed, tier or None)."""
    f1 = spec_from("F1", G1, max_rj=2, ladder="K1", rule="W2", pv="PV1", saturation="B")
    f1.id = "P6A_F1_C_K1_W2_R1_PV1_B"
    if worker == "A":
        return [
            ("mix", _blank(), 500_000, 20260922, None),
            ("mix", f1, 1_000_000, 20260922, None),
            ("mix", zero_feature(f1, "WIND_KEY"), 1_000_000, 20260922, None),
            ("mix", zero_feature(f1, "REJUMP"), 1_000_000, 20260922, None),
            ("tier", f1, 80_000, 20260922, "LARGE_HILL"),
            ("tier", f1, 40_000, 20260922, "SKI_FLYING"),
            ("tier", f1, 20_000, 20260922, "WORLD_CUP"),
            ("tier", f1, 20_000, 20260922, "PERFECT_V"),
            ("tier", spec_from("F1PV2", G1, pv="PV2"), 20_000, 20260922, "PERFECT_V"),
            ("tier", spec_from("F1PV3", G1, pv="PV3"), 20_000, 20260922, "PERFECT_V"),
        ]
    f2 = spec_from("F2", G1, max_rj=3)
    f2.id = "P6A_F2_C_K1_W2_R2_PV1_B"
    f3 = spec_from("F3", G1, max_rj=8)
    f3.id = "P6A_F3_C_K1_W2_R3_PV1_B"
    f4 = spec_from("F4", G1, rule="W1")
    f4.id = "P6A_F4_C_K1_W1_R1_PV1_B"
    f5 = spec_from("F5", G1, ladder="K2")
    f5.id = "P6A_F5_C_K2_W2_R1_PV1_B"
    f6 = spec_from("F6", G1_B, max_rj=2)
    f6.id = "P6A_F6_B_K1_W2_R1_PV1_B"
    return [
        ("mix", f2, 1_000_000, 20260922, None),
        ("mix", zero_feature(f2, "WIND_KEY"), 500_000, 20260922, None),
        ("mix", zero_feature(f2, "REJUMP"), 500_000, 20260922, None),
        ("mix", f3, 500_000, 20260922, None),
        ("mix", f4, 500_000, 20260922, None),
        ("mix", f5, 500_000, 20260922, None),
        ("mix", f6, 500_000, 20260922, None),
    ]


def _book(rows: list[dict]) -> dict:
    sizes = [row["events"] * BYTES_PER_EVENT + row["rejumps"] * EXTRA_BYTES_PER_REJUMP for row in rows]
    sizes.sort()

    def q(p: float) -> float:
        return sizes[min(len(sizes) - 1, int(round((len(sizes) - 1) * p)))]

    return {
        "bytesPerEvent": BYTES_PER_EVENT,
        "extraBytesPerRejump": EXTRA_BYTES_PER_REJUMP,
        "meanBytes": sum(sizes) / len(sizes),
        "p95Bytes": q(0.95),
        "p99Bytes": q(0.99),
        "maxBytes": sizes[-1],
    }


def _pack(spec: Phase6Spec, rows: list[dict], p_trigger: float, kind: str, tier: str | None) -> dict:
    stats = summarise(rows, p_trigger)
    stats.update(body_stats(rows))
    stats["bins"] = mult_bins(rows, p_trigger)
    stats["book"] = _book(rows)
    stats["id"] = spec.id
    stats["kind"] = kind
    stats["tier"] = tier
    stats["ladder"] = spec.ladder
    stats["stageRule"] = spec.stage_rule
    stats["saturation"] = spec.saturation
    stats["perfectV"] = spec.perfect_v
    stats["maxRejumps"] = spec.max_rejumps_per_spin
    stats["availability"] = spec.availability
    stats["weights"] = spec.weights_by_tier
    stats["incrementalPp"] = stats["rtpPp"] - BASELINE_MEAN * p_trigger * 100.0
    stats["reservePp"] = 96.50 - (71.212 + stats["rtpPp"])
    stats["newGameRtp"] = 71.212 + stats["rtpPp"]
    stats["lineRejumpPp"] = stats["meanLineRejump"] * p_trigger * 100.0
    return stats


def main() -> None:
    worker = sys.argv[1] if len(sys.argv) > 1 else "A"
    ctx = build_context(load_v2_config())
    p_trigger = ctx["mix"]["P_scatterGe3"]
    OUT.mkdir(exist_ok=True)
    path = OUT / f"large_{worker}.jsonl"
    for kind, spec, n, seed, tier in jobs_for(worker):
        if kind == "mix":
            rows = run_mix(ctx, spec, n, seed)
        else:
            rows = run_tier(ctx, spec, tier, n, seed)
        stats = _pack(spec, rows, p_trigger, kind, tier)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(stats) + "\n")
        print(
            f"{worker} {stats['id']} {kind} {tier or 'MIX'} n={n} "
            f"inc={stats['incrementalPp']:.3f} mean={stats['meanX']:.3f} "
            f"med={stats['medianX']:.2f} pRJ={stats['pRejump']:.4f} pWK={stats['pWind']:.4f} "
            f"cap={stats['pCap']:.6f} drag={stats['meanCapDrag']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
