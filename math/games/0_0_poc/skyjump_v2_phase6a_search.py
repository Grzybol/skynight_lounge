"""Phase 6A candidate screen. Research only. Does not write live config."""

from __future__ import annotations

import json
import random
import statistics
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase4a_economy import build_token_tables
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, simulate_bonus
from skyjump_v2_phase6a_engine import Phase6Spec, refill_catalogs, simulate_phase6_bonus

OUT = HERE / "phase6a_research"
BASE_TOKEN = 752
FIXED = {
    "THERMAL_LIFT": 42,
    "GATE_UPGRADE": 6,
    "JUDGE": 170,
    "HEAD_JUDGE": 30,
}
# (rejump, wind) taken from FLIGHT_TOKEN. Sum must stay <= 752.
MODEL_WEIGHTS = {
    "A": {
        "LARGE_HILL": (40, 18),
        "SKI_FLYING": (70, 40),
        "WORLD_CUP": (90, 60),
        "PERFECT_V": (110, 80),
    },
    "B": {
        "LARGE_HILL": (55, 0),
        "SKI_FLYING": (75, 36),
        "WORLD_CUP": (90, 55),
        "PERFECT_V": (100, 75),
    },
    "C": {
        "LARGE_HILL": (48, 12),
        "SKI_FLYING": (78, 36),
        "WORLD_CUP": (96, 56),
        "PERFECT_V": (112, 76),
    },
    "C_LO": {
        "LARGE_HILL": (28, 6),
        "SKI_FLYING": (48, 18),
        "WORLD_CUP": (64, 32),
        "PERFECT_V": (80, 48),
    },
    "C_HI": {
        "LARGE_HILL": (70, 22),
        "SKI_FLYING": (110, 55),
        "WORLD_CUP": (130, 80),
        "PERFECT_V": (150, 100),
    },
}


def table_for(pair: tuple[int, int]) -> dict[str, int]:
    rejump, wind = pair
    token = BASE_TOKEN - rejump - wind
    if token <= 0:
        raise ValueError(f"token weight exhausted by {pair}")
    weights = {"FLIGHT_TOKEN": token, "REJUMP": rejump, "WIND_KEY": wind}
    weights.update(FIXED)
    if sum(weights.values()) != 1000:
        raise ValueError(f"weights sum {sum(weights.values())}")
    return weights


def make_spec(
    spec_id: str,
    *,
    availability: str,
    ladder: str = "K1",
    stage_rule: str = "W2",
    saturation: str = "B",
    perfect_v: str = "PV1",
    max_rejumps: int = 2,
) -> Phase6Spec:
    weights = {tier: table_for(MODEL_WEIGHTS[availability][tier]) for tier in TIERS}
    return Phase6Spec(
        id=spec_id,
        weights_by_tier=weights,
        ladder=ladder,
        stage_rule=stage_rule,
        saturation=saturation,
        availability=availability,
        perfect_v=perfect_v,
        max_rejumps_per_spin=max_rejumps,
        max_chain_depth=8,
    )


def zero_feature(spec: Phase6Spec, feature: str) -> Phase6Spec:
    weights = {}
    for tier, table in spec.weights_by_tier.items():
        copied = dict(table)
        moved = int(copied.get(feature, 0))
        copied[feature] = 0
        copied["FLIGHT_TOKEN"] = int(copied["FLIGHT_TOKEN"]) + moved
        weights[tier] = copied
    return Phase6Spec(
        id=spec.id + ":" + feature.lower(),
        weights_by_tier=weights,
        ladder=spec.ladder,
        stage_rule=spec.stage_rule,
        saturation=spec.saturation,
        availability=spec.availability,
        perfect_v="PV1" if feature == "WIND_KEY" else spec.perfect_v,
        max_rejumps_per_spin=0 if feature == "REJUMP" else spec.max_rejumps_per_spin,
        max_chain_depth=spec.max_chain_depth,
    )


def build_context(config: dict) -> dict:
    paying = live_candidate_from_config(config)
    live = bonus_candidate_from_config(config)
    # Research uses the promoted bonus mystery table as the frozen base, then
    # reallocates from FLIGHT_TOKEN. It does not read tier-local research copies.
    paying = dict(paying)
    paying["mysteryResultWeights"] = dict(live.mysteryResultWeights)
    paying["tokenValueScale"] = float(live.tokenValueScale)
    regular = {row["id"] for row in config["symbols"]["regular"]}
    return {
        "config": config,
        "paying": paying,
        "live": live,
        "strips_by_tier": live.tierReels,
        "catalogs_by_tier": {tier: refill_catalogs(strips) for tier, strips in live.tierReels.items()},
        "regular_ids": regular,
        "paylines": config["paylines"],
        "paytable": config["paytable"]["awards"],
        "scatter_id": config["symbols"]["scatter"]["id"],
        "mystery_id": config["mysteryModel"]["id"],
        "coach_id": config["coachModel"]["id"],
        "perfect_rows": tuple(config["scatterModel"]["perfectVRows"]),
        "max_floor": int(paying["gateMaxFloor"]),
        "scale": float(live.tokenValueScale),
        "thermal_weights": paying["thermalWeights"],
        "token_tables": build_token_tables(paying),
        "initial_spins": live.initialSpins,
        "max_spins": live.maxFreeSpins,
        "max_targets": live.maxPersistentTargets,
        "upgrade_rule": live.upgradeRule,
        "max_win_x": float(live.maxWinX),
        "mix": base_trigger_mix(config),
    }


def _kwargs(ctx: dict, prior: float = 0.0) -> dict:
    return {
        "strips_by_tier": ctx["strips_by_tier"],
        "catalogs_by_tier": ctx["catalogs_by_tier"],
        "config": ctx["config"],
        "paying": ctx["paying"],
        "regular_ids": ctx["regular_ids"],
        "paylines": ctx["paylines"],
        "paytable": ctx["paytable"],
        "scatter_id": ctx["scatter_id"],
        "mystery_id": ctx["mystery_id"],
        "coach_id": ctx["coach_id"],
        "perfect_rows": ctx["perfect_rows"],
        "max_floor": ctx["max_floor"],
        "scale": ctx["scale"],
        "thermal_weights": ctx["thermal_weights"],
        "token_tables": ctx["token_tables"],
        "initial_spins": ctx["initial_spins"],
        "max_spins": ctx["max_spins"],
        "max_targets": ctx["max_targets"],
        "upgrade_rule": ctx["upgrade_rule"],
        "round_prior_win_x": prior,
        "max_win_x": ctx["max_win_x"],
    }


def _start_tier(rng, mix: dict) -> str:
    roll = rng.random()
    cursor = 0.0
    conditional = mix["conditional"]
    for tier in TIERS:
        cursor += conditional[tier]
        if roll <= cursor:
            return tier
    return TIERS[-1]


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def summarise(rows: list[dict], p_trigger: float) -> dict:
    capped = [row["capped"] for row in rows]
    mean = statistics.fmean(capped)
    mults = [row["multiplier"] for row in rows]
    events = [row["events"] for row in rows]
    # Compact event payload stands in for one book record. Calibrated later.
    return {
        "n": len(rows),
        "meanX": mean,
        "medianX": _quantile(capped, 0.50),
        "p90X": _quantile(capped, 0.90),
        "p95X": _quantile(capped, 0.95),
        "p99X": _quantile(capped, 0.99),
        "p999X": _quantile(capped, 0.999),
        "rtpPp": mean * p_trigger * 100.0,
        "meanSpins": statistics.fmean(row["spins"] for row in rows),
        "pRejump": sum(row["rejumps"] > 0 for row in rows) / len(rows),
        "pWind": sum(row["windKeys"] > 0 for row in rows) / len(rows),
        "pMultGt1": sum(row["multiplier"] > 1 for row in rows) / len(rows),
        "pBoth": sum(row["rejumps"] > 0 and row["windKeys"] > 0 for row in rows) / len(rows),
        "pMultiRejump": sum(row["rejumps"] >= 2 for row in rows) / len(rows),
        "pRejump3": sum(row["rejumps"] >= 3 for row in rows) / len(rows),
        "pRejump5": sum(row["rejumps"] >= 5 for row in rows) / len(rows),
        "meanRejumps": statistics.fmean(row["rejumps"] for row in rows),
        "meanWind": statistics.fmean(row["windKeys"] for row in rows),
        "meanMult": statistics.fmean(mults),
        "medianMult": _quantile(mults, 0.50),
        "pMult2": sum(value >= 2 for value in mults) / len(rows),
        "pMult4": sum(value >= 4 for value in mults) / len(rows),
        "pMult6": sum(value >= 6 for value in mults) / len(rows),
        "pMult9": sum(value >= 9 for value in mults) / len(rows),
        "pMult12": sum(value >= 12 for value in mults) / len(rows),
        "maxMult": max(mults),
        "pCap": sum(row["cap"] for row in rows) / len(rows),
        "meanCapDrag": statistics.fmean(row["capDrag"] for row in rows),
        "meanLineRejump": statistics.fmean(row["lineRejump"] for row in rows),
        "meanLineInitial": statistics.fmean(row["lineInitial"] for row in rows),
        "meanCollectorRaw": statistics.fmean(row["collectorRaw"] for row in rows),
        "meanCollectorPaid": statistics.fmean(row["collectorPaid"] for row in rows),
        "pTrunc": sum(row["truncated"] > 0 for row in rows) / len(rows),
        "pBound": sum(row["hitBound"] for row in rows) / len(rows),
        "meanChain": statistics.fmean(row["maxChain"] for row in rows),
        "maxChain": max(row["maxChain"] for row in rows),
        "pLock25": sum(row["maxLocked"] > 0.25 for row in rows) / len(rows),
        "pLock50": sum(row["maxLocked"] > 0.50 for row in rows) / len(rows),
        "pLock75": sum(row["maxLocked"] > 0.75 for row in rows) / len(rows),
        "meanEvents": statistics.fmean(events),
        "p95Events": _quantile(events, 0.95),
        "p99Events": _quantile(events, 0.99),
        "maxEvents": max(events),
    }


def run_mix(ctx: dict, spec: Phase6Spec, n: int, seed: int) -> list[dict]:
    mix = ctx["mix"]
    rows = []
    call = _kwargs(ctx)
    for index in range(n):
        rng = random.Random(seed + index)
        tier = _start_tier(rng, mix)
        rows.append(simulate_phase6_bonus(rng, tier, spec, **call))
    return rows


def run_tier(ctx: dict, spec: Phase6Spec, tier: str, n: int, seed: int) -> list[dict]:
    call = _kwargs(ctx)
    rows = []
    for index in range(n):
        rng = random.Random(seed + index)
        rows.append(simulate_phase6_bonus(rng, tier, spec, **call))
    return rows


def run_baseline(ctx: dict, n: int, seed: int) -> float:
    mix = ctx["mix"]
    live = ctx["live"]
    total = 0.0
    for index in range(n):
        rng = random.Random(seed + index)
        tier = _start_tier(rng, mix)
        result = simulate_bonus(
            rng,
            tier,
            live,
            config=ctx["config"],
            paying_candidate=ctx["paying"],
            round_prior_win_x=0.0,
        )
        total += result["bonusWinXCapped"]
    return total / n


def book_size_sample(rows: list[dict]) -> dict:
    """Estimate serialized size from the event counter. One event ~ 240 bytes."""
    sizes = [int(row["events"]) * 240 for row in rows]
    blobs = [json.dumps({"events": row["events"], "win": round(row["capped"], 4)}).encode() for row in rows[:200]]
    packed = [len(zlib.compress(blob, 6)) for blob in blobs]
    return {
        "assumedBytesPerEvent": 240,
        "meanBytes": statistics.fmean(sizes),
        "p95Bytes": _quantile(sizes, 0.95),
        "p99Bytes": _quantile(sizes, 0.99),
        "maxBytes": max(sizes),
        "sampleCompressedMean": statistics.fmean(packed) if packed else 0,
    }


def screen_specs() -> list[Phase6Spec]:
    return [
        make_spec("P6A_C_K1_W2_R2_PV1", availability="C", max_rejumps=3),
        make_spec("P6A_A_K1_W2_R2_PV1", availability="A", max_rejumps=3),
        make_spec("P6A_B_K1_W2_R2_PV1", availability="B", max_rejumps=3),
        make_spec("P6A_CLO_K1_W2_R2_PV1", availability="C_LO", max_rejumps=3),
        make_spec("P6A_CHI_K1_W2_R2_PV1", availability="C_HI", max_rejumps=3),
        make_spec("P6A_C_K1_W2_R1_PV1", availability="C", max_rejumps=2),
        make_spec("P6A_C_K1_W2_R3_PV1", availability="C", max_rejumps=8),
        make_spec("P6A_C_K2_W2_R2_PV1", availability="C", ladder="K2", max_rejumps=3),
        make_spec("P6A_C_K3_W2_R2_PV1", availability="C", ladder="K3", max_rejumps=3),
        make_spec("P6A_C_K1_W1_R2_PV1", availability="C", stage_rule="W1", max_rejumps=3),
        make_spec("P6A_C_K1_W2_R2_PV2", availability="C", perfect_v="PV2", max_rejumps=3),
        make_spec("P6A_C_K1_W2_R2_PV3", availability="C", perfect_v="PV3", max_rejumps=3),
        make_spec("P6A_C_K1_W2_R2_PV1_SATA", availability="C", saturation="A", max_rejumps=3),
    ]


def print_row(spec: Phase6Spec, stats: dict, baseline_pp: float) -> None:
    incremental = stats["rtpPp"] - baseline_pp
    reserve = 96.50 - (71.212 + stats["rtpPp"])
    print(
        f"{spec.id:28} mean={stats['meanX']:.2f} incPp={incremental:.2f} "
        f"reserve={reserve:.2f} pRJ={stats['pRejump']:.3f} pWK={stats['pWind']:.3f} "
        f"pM4={stats['pMult4']:.3f} cap={stats['pCap']:.5f} trunc={stats['pTrunc']:.4f} "
        f"ev={stats['meanEvents']:.1f}",
        flush=True,
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "screen"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    config = load_v2_config()
    ctx = build_context(config)
    p_trigger = ctx["mix"]["P_scatterGe3"]
    OUT.mkdir(exist_ok=True)
    if mode == "parity":
        base = run_baseline(ctx, n, 20260922)
        blank = make_spec("P6A_BASELINE", availability="B", max_rejumps=0)
        for tier in TIERS:
            blank.weights_by_tier[tier] = table_for((0, 0))
        rows = run_mix(ctx, blank, n, 20260922)
        stats = summarise(rows, p_trigger)
        print(f"phase5b={base:.3f} phase6blank={stats['meanX']:.3f} n={n}", flush=True)
        return
    if mode == "one":
        spec = next(row for row in screen_specs() if row.id == sys.argv[3])
        rows = run_mix(ctx, spec, n, 20260922)
        stats = summarise(rows, p_trigger)
        print(json.dumps({"id": spec.id, **stats}, indent=2))
        return
    baseline_mean = 27.45472
    baseline_pp = baseline_mean * p_trigger * 100.0
    payload = {"pTrigger": p_trigger, "baselineMean": baseline_mean, "baselinePp": baseline_pp, "screen": []}
    for spec in screen_specs():
        rows = run_mix(ctx, spec, n, 20260922)
        stats = summarise(rows, p_trigger)
        print_row(spec, stats, baseline_pp)
        payload["screen"].append({"id": spec.id, "availability": spec.availability, "ladder": spec.ladder, "stage": spec.stage_rule, "saturation": spec.saturation, "perfectV": spec.perfect_v, "maxRejumps": spec.max_rejumps_per_spin, **stats, "book": book_size_sample(rows)})
    path = OUT / f"screen_n{n}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
