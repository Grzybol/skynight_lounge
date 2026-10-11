"""Phase 6A.1 architecture screen. Research only. Does not write live config."""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import TIERS
from skyjump_v2_phase6a_search import OUT as OUT6A
from skyjump_v2_phase6a_search import (
    BASE_TOKEN,
    _kwargs,
    _quantile,
    _start_tier,
    build_context,
    table_for,
)
from skyjump_v2_phase6a1_engine import Phase6A1Spec, simulate_phase6a1_bonus

OUT = Path(__file__).resolve().parent / "phase6a1_research"
BASELINE_MEAN = 27.45472
BYTES_PER_EVENT = 281
EXTRA_BYTES_PER_REJUMP = 1680

# F1 frozen benchmark weights (Phase 6A).
F1_WEIGHTS = {
    "LARGE_HILL": (10, 1),
    "SKI_FLYING": (18, 3),
    "WORLD_CUP": (24, 6),
    "PERFECT_V": (32, 10),
}


def pack_weights(pack: dict[str, tuple[int, int]]) -> dict[str, dict[str, int]]:
    return {tier: table_for(pack[tier]) for tier in TIERS}


def make_spec(
    spec_id: str,
    pack: dict[str, tuple[int, int]],
    *,
    rejump_arch: str,
    wind_arch: str,
    max_rejumps: int = 2,
    ladder: str = "K1",
    stage_rule: str = "W2",
    saturation: str = "B",
    perfect_v: str = "PV1",
) -> Phase6A1Spec:
    wind_lh = pack["LARGE_HILL"][1]
    return Phase6A1Spec(
        id=spec_id,
        weights_by_tier=pack_weights(pack),
        ladder=ladder,
        stage_rule=stage_rule,
        saturation=saturation,
        availability="C" if wind_lh else "B",
        perfect_v=perfect_v,
        max_rejumps_per_spin=max_rejumps,
        max_chain_depth=8,
        rejump_arch=rejump_arch,
        wind_arch=wind_arch,
    )


def f1_benchmark() -> Phase6A1Spec:
    return make_spec(
        "P6A1_A_F1_RDELAY_WIMM",
        F1_WEIGHTS,
        rejump_arch="R-DELAYED",
        wind_arch="W-IMMEDIATE",
    )


def summarise(rows: list[dict], p_trigger: float) -> dict:
    capped = [row["capped"] for row in rows]
    events = [row["events"] for row in rows]
    sizes = [row["events"] * BYTES_PER_EVENT + row["rejumps"] * EXTRA_BYTES_PER_REJUMP for row in rows]
    n = len(rows)

    def p_any(pred) -> float:
        return sum(1 for row in rows if pred(row)) / n

    mult_bins = (1, 2, 4, 8, 12, 18, 27)
    collector_by_mult = {m: 0.0 for m in mult_bins}
    for row in rows:
        for key, value in (row.get("collectorByMult") or {}).items():
            mult = int(key)
            if mult in collector_by_mult:
                collector_by_mult[mult] += float(value)
            elif mult >= 27:
                collector_by_mult[27] += float(value)

    return {
        "n": n,
        "meanX": statistics.fmean(capped),
        "p25X": _quantile(capped, 0.25),
        "medianX": _quantile(capped, 0.50),
        "p75X": _quantile(capped, 0.75),
        "p90X": _quantile(capped, 0.90),
        "p95X": _quantile(capped, 0.95),
        "p99X": _quantile(capped, 0.99),
        "p999X": _quantile(capped, 0.999),
        "rtpPp": statistics.fmean(capped) * p_trigger * 100.0,
        "meanSpins": statistics.fmean(row["spins"] for row in rows),
        "pRejump": p_any(lambda row: row["rejumps"] > 0),
        "pWind": p_any(lambda row: row["windKeys"] > 0),
        "pAnyPhase6": p_any(lambda row: row["rejumps"] > 0 or row["windKeys"] > 0),
        "pBoth": p_any(lambda row: row["rejumps"] > 0 and row["windKeys"] > 0),
        "pMultiRejump": p_any(lambda row: row["rejumps"] >= 2),
        "meanRejumps": statistics.fmean(row["rejumps"] for row in rows),
        "meanWind": statistics.fmean(row["windKeys"] for row in rows),
        "meanMult": statistics.fmean(row["multiplier"] for row in rows),
        "meanActiveMult": statistics.fmean(row.get("meanActiveMult", row["multiplier"]) for row in rows),
        "medianMult": _quantile([row["multiplier"] for row in rows], 0.50),
        "pMult2": p_any(lambda row: row["multiplier"] >= 2),
        "pMult4": p_any(lambda row: row["multiplier"] >= 4),
        "pMult8": p_any(lambda row: row["multiplier"] >= 8),
        "pMult9": p_any(lambda row: row["multiplier"] >= 9),
        "maxMult": max(row["multiplier"] for row in rows),
        "pCap": p_any(lambda row: row["cap"]),
        "meanCapDrag": statistics.fmean(row["capDrag"] for row in rows),
        "meanLineRejump": statistics.fmean(row["lineRejump"] for row in rows),
        "meanLineInitial": statistics.fmean(row["lineInitial"] for row in rows),
        "meanCollectorRaw": statistics.fmean(row["collectorRaw"] for row in rows),
        "meanCollectorPaid": statistics.fmean(row["collectorPaid"] for row in rows),
        "meanCollectorInitial": statistics.fmean(row["collectorInitialBatch"] for row in rows),
        "meanCollectorAfterRj": statistics.fmean(row["collectorAfterRejump"] for row in rows),
        "meanRecollection": statistics.fmean(row["collectorRecollection"] for row in rows),
        "meanPostRjTokens": statistics.fmean(row.get("postRejumpTokens", 0) for row in rows),
        "meanPostRjJudges": statistics.fmean(row.get("postRejumpJudges", 0) for row in rows),
        "pTrunc": p_any(lambda row: row["truncated"] > 0),
        "pBound": p_any(lambda row: row["hitBound"]),
        "meanChain": statistics.fmean(row["maxChain"] for row in rows),
        "maxChain": max(row["maxChain"] for row in rows),
        "meanEvents": statistics.fmean(events),
        "p95Events": _quantile(events, 0.95),
        "p99Events": _quantile(events, 0.99),
        "maxEvents": max(events),
        "meanBytes": statistics.fmean(sizes),
        "p99Bytes": _quantile(sizes, 0.99),
        "maxBytes": max(sizes),
        "pPendingUnused": p_any(lambda row: row.get("pendingUnused", 0) > 0),
        "meanKeysFinal": statistics.fmean(row.get("keysOnFinalSpin", 0) for row in rows),
        "meanKeysFuture": statistics.fmean(row.get("keysWithFutureSpin", 0) for row in rows),
        "meanSpinsAfterKey": statistics.fmean(row.get("spinsAfterFirstKey", 0) for row in rows),
        "pMaterialPlus5VsMean": p_any(lambda row: row["capped"] >= BASELINE_MEAN + 5.0),
        "collectorRtpByMult": {
            str(m): (collector_by_mult[m] / n) * p_trigger * 100.0 for m in mult_bins
        },
    }


def run_mix(ctx: dict, spec: Phase6A1Spec, n: int, seed: int) -> list[dict]:
    mix = ctx["mix"]
    call = _kwargs(ctx)
    rows = []
    for index in range(n):
        rng = random.Random(seed + index)
        tier = _start_tier(rng, mix)
        rows.append(simulate_phase6a1_bonus(rng, tier, spec, **call))
    return rows


def run_tier(ctx: dict, spec: Phase6A1Spec, tier: str, n: int, seed: int) -> list[dict]:
    call = _kwargs(ctx)
    rows = []
    for index in range(n):
        rng = random.Random(seed + index)
        rows.append(simulate_phase6a1_bonus(rng, tier, spec, **call))
    return rows


def decorate(spec: Phase6A1Spec, stats: dict, p_trigger: float) -> dict:
    stats = dict(stats)
    stats["id"] = spec.id
    stats["rejumpArch"] = spec.rejump_arch
    stats["windArch"] = spec.wind_arch
    stats["weights"] = spec.weights_by_tier
    stats["incrementalPp"] = stats["rtpPp"] - BASELINE_MEAN * p_trigger * 100.0
    stats["reservePp"] = 96.50 - (71.212 + stats["rtpPp"])
    stats["newGameRtp"] = 71.212 + stats["rtpPp"]
    stats["lineRejumpPp"] = stats["meanLineRejump"] * p_trigger * 100.0
    stats["collectorAfterRjPp"] = stats["meanCollectorAfterRj"] * p_trigger * 100.0
    stats["recollectionPp"] = stats["meanRecollection"] * p_trigger * 100.0
    return stats


# Higher-visibility packs for decoupled architectures. Integer weights from FLIGHT_TOKEN.
# Screen1 (n=12k) showed B1+ and C1+/D1+ overshoot; thin packs target 4.5–5.5 pp.
PACKS = {
    # Architecture controls at F1 Mystery weights (measure arch delta only).
    "CTRL_F1": {
        "LARGE_HILL": (10, 1),
        "SKI_FLYING": (18, 3),
        "WORLD_CUP": (24, 6),
        "PERFECT_V": (32, 10),
    },
    # R-BATCH + W-IMMEDIATE: more rejump, thin wind
    "B0": {"LARGE_HILL": (14, 1), "SKI_FLYING": (24, 3), "WORLD_CUP": (32, 6), "PERFECT_V": (42, 10)},
    "B05": {"LARGE_HILL": (16, 1), "SKI_FLYING": (28, 3), "WORLD_CUP": (36, 6), "PERFECT_V": (48, 10)},
    "B1": {"LARGE_HILL": (18, 1), "SKI_FLYING": (30, 3), "WORLD_CUP": (40, 6), "PERFECT_V": (52, 10)},
    "B15": {"LARGE_HILL": (20, 1), "SKI_FLYING": (34, 3), "WORLD_CUP": (44, 6), "PERFECT_V": (56, 10)},
    "B2": {"LARGE_HILL": (22, 1), "SKI_FLYING": (36, 3), "WORLD_CUP": (48, 6), "PERFECT_V": (60, 10)},
    "B3": {"LARGE_HILL": (28, 1), "SKI_FLYING": (44, 3), "WORLD_CUP": (56, 6), "PERFECT_V": (70, 10)},
    # R-DELAYED + W-NEXT-SPIN: F1-like rejump, modest wind lift
    "C0": {"LARGE_HILL": (10, 2), "SKI_FLYING": (18, 5), "WORLD_CUP": (24, 9), "PERFECT_V": (32, 14)},
    "C05": {"LARGE_HILL": (10, 2), "SKI_FLYING": (18, 6), "WORLD_CUP": (24, 10), "PERFECT_V": (32, 16)},
    "C1": {"LARGE_HILL": (10, 3), "SKI_FLYING": (18, 7), "WORLD_CUP": (24, 12), "PERFECT_V": (32, 18)},
    "C15": {"LARGE_HILL": (12, 3), "SKI_FLYING": (20, 8), "WORLD_CUP": (28, 14), "PERFECT_V": (36, 20)},
    "C2": {"LARGE_HILL": (10, 4), "SKI_FLYING": (18, 10), "WORLD_CUP": (24, 16), "PERFECT_V": (32, 24)},
    # R-BATCH + W-NEXT-SPIN
    "D0": {"LARGE_HILL": (14, 2), "SKI_FLYING": (24, 5), "WORLD_CUP": (32, 9), "PERFECT_V": (42, 14)},
    "D05": {"LARGE_HILL": (16, 2), "SKI_FLYING": (28, 6), "WORLD_CUP": (36, 10), "PERFECT_V": (48, 16)},
    "D1": {"LARGE_HILL": (18, 2), "SKI_FLYING": (30, 6), "WORLD_CUP": (40, 10), "PERFECT_V": (52, 16)},
    "D15": {"LARGE_HILL": (18, 3), "SKI_FLYING": (30, 7), "WORLD_CUP": (40, 12), "PERFECT_V": (52, 18)},
    "D2": {"LARGE_HILL": (20, 3), "SKI_FLYING": (34, 8), "WORLD_CUP": (44, 14), "PERFECT_V": (56, 20)},
    "D3": {"LARGE_HILL": (22, 4), "SKI_FLYING": (36, 10), "WORLD_CUP": (48, 16), "PERFECT_V": (60, 24)},
    # R-BATCH + W-CHARGE (immediate charge; more wind keys)
    "E0": {"LARGE_HILL": (18, 5), "SKI_FLYING": (30, 12), "WORLD_CUP": (40, 18), "PERFECT_V": (52, 26)},
    "E05": {"LARGE_HILL": (20, 6), "SKI_FLYING": (34, 14), "WORLD_CUP": (44, 20), "PERFECT_V": (56, 28)},
    "E1": {"LARGE_HILL": (22, 6), "SKI_FLYING": (36, 14), "WORLD_CUP": (48, 22), "PERFECT_V": (60, 30)},
    "E15": {"LARGE_HILL": (22, 8), "SKI_FLYING": (36, 18), "WORLD_CUP": (48, 26), "PERFECT_V": (60, 34)},
    "E2": {"LARGE_HILL": (24, 8), "SKI_FLYING": (40, 18), "WORLD_CUP": (52, 26), "PERFECT_V": (64, 34)},
    "E3": {"LARGE_HILL": (28, 10), "SKI_FLYING": (44, 22), "WORLD_CUP": (56, 30), "PERFECT_V": (70, 40)},
    # Micro-screen finalists (registered for large runner).
    "B23": {"LARGE_HILL": (23, 1), "SKI_FLYING": (38, 3), "WORLD_CUP": (50, 6), "PERFECT_V": (62, 10)},
    "C_LH2": {"LARGE_HILL": (10, 2), "SKI_FLYING": (18, 3), "WORLD_CUP": (24, 6), "PERFECT_V": (32, 10)},
    "D17_3": {"LARGE_HILL": (17, 3), "SKI_FLYING": (28, 7), "WORLD_CUP": (38, 12), "PERFECT_V": (50, 18)},
    "D19_2": {"LARGE_HILL": (19, 2), "SKI_FLYING": (32, 6), "WORLD_CUP": (42, 11), "PERFECT_V": (54, 17)},
    "E25_9": {"LARGE_HILL": (25, 9), "SKI_FLYING": (42, 20), "WORLD_CUP": (54, 28), "PERFECT_V": (66, 36)},
    # B1 weights under R-BATCH + W-NEXT (best D-family in band).
    "D_B1": {"LARGE_HILL": (18, 1), "SKI_FLYING": (30, 3), "WORLD_CUP": (40, 6), "PERFECT_V": (52, 10)},
}


def screen_jobs() -> list[Phase6A1Spec]:
    jobs = [f1_benchmark()]
    # Architecture-only controls at F1 weights.
    jobs.append(
        make_spec("P6A1_CTRL_RBATCH_WIMM", PACKS["CTRL_F1"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE")
    )
    jobs.append(
        make_spec("P6A1_CTRL_RDELAY_WNEXT", PACKS["CTRL_F1"], rejump_arch="R-DELAYED", wind_arch="W-NEXT-SPIN")
    )
    jobs.append(
        make_spec("P6A1_CTRL_RBATCH_WNEXT", PACKS["CTRL_F1"], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN")
    )
    jobs.append(
        make_spec("P6A1_CTRL_RBATCH_WCHARGE", PACKS["CTRL_F1"], rejump_arch="R-BATCH", wind_arch="W-CHARGE")
    )
    for name, pack in PACKS.items():
        if name == "CTRL_F1":
            continue
        if name.startswith("B"):
            jobs.append(make_spec(f"P6A1_B_{name}", pack, rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE"))
        elif name.startswith("C"):
            jobs.append(make_spec(f"P6A1_C_{name}", pack, rejump_arch="R-DELAYED", wind_arch="W-NEXT-SPIN"))
        elif name.startswith("D"):
            jobs.append(make_spec(f"P6A1_D_{name}", pack, rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN"))
        elif name.startswith("E"):
            jobs.append(make_spec(f"P6A1_E_{name}", pack, rejump_arch="R-BATCH", wind_arch="W-CHARGE"))
    return jobs


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 701
    ctx = build_context(load_v2_config())
    p_trigger = ctx["mix"]["P_scatterGe3"]
    _ = BASELINE_MEAN * p_trigger * 100.0
    OUT.mkdir(exist_ok=True)
    payload = {"n": n, "seed": seed, "baselineMeanX": BASELINE_MEAN, "rows": []}
    for spec in screen_jobs():
        rows = run_mix(ctx, spec, n, seed)
        lh = run_tier(ctx, spec, "LARGE_HILL", min(n, 8000), seed + 17)
        stats = decorate(spec, summarise(rows, p_trigger), p_trigger)
        lh_stats = summarise(lh, p_trigger)
        stats["lh"] = {
            "pRejump": lh_stats["pRejump"],
            "pWind": lh_stats["pWind"],
            "pAnyPhase6": lh_stats["pAnyPhase6"],
            "pBoth": lh_stats["pBoth"],
            "medianX": lh_stats["medianX"],
            "p90X": lh_stats["p90X"],
        }
        payload["rows"].append(stats)
        print(
            f"{spec.id:32} inc={stats['incrementalPp']:6.2f} res={stats['reservePp']:5.2f} "
            f"pRJ={stats['pRejump']:.3f} pWK={stats['pWind']:.3f} any={stats['pAnyPhase6']:.3f} "
            f"med={stats['medianX']:.1f} p90={stats['p90X']:.1f} "
            f"LH rj/wk/any={stats['lh']['pRejump']:.3f}/{stats['lh']['pWind']:.3f}/{stats['lh']['pAnyPhase6']:.3f} "
            f"cap={stats['pCap']:.5f} pend={stats['pPendingUnused']:.3f}",
            flush=True,
        )
    path = OUT / f"screen_n{n}_s{seed}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path}", flush=True)
    _ = OUT6A, BASE_TOKEN


if __name__ == "__main__":
    main()
