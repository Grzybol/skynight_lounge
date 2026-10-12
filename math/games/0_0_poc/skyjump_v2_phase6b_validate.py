"""Live Phase 6B 1M validation + paired feature-off control. Research metrics only."""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, simulate_bonus
from skyjump_v2_phase6a_search import table_for

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase6b_research" / "live_validate.json"
BASELINE_MEAN = 27.45472
BASE_RTP = 71.212
TARGET = 96.50


def _start_tier(rng, mix) -> str:
    roll = rng.random()
    cursor = 0.0
    for tier in TIERS:
        cursor += mix["conditional"][tier]
        if roll < cursor:
            return tier
    return "LARGE_HILL"


def feature_off_candidate(cand):
    """Zero REJUMP/WIND back into FLIGHT_TOKEN per tier (paired control)."""
    from skyjump_v2_phase5a_engine import BonusCandidate

    by_tier = {}
    for tier, table in (cand.mysteryResultWeightsByTier or {}).items():
        copied = dict(table)
        moved = int(copied.get("REJUMP", 0)) + int(copied.get("WIND_KEY", 0))
        copied["REJUMP"] = 0
        copied["WIND_KEY"] = 0
        copied["FLIGHT_TOKEN"] = int(copied["FLIGHT_TOKEN"]) + moved
        by_tier[tier] = copied
    return BonusCandidate(
        id=cand.id + ":off",
        upgradeRule=cand.upgradeRule,
        initialSpins=cand.initialSpins,
        maxFreeSpins=cand.maxFreeSpins,
        maxPersistentTargets=cand.maxPersistentTargets,
        duplicateTargetBehaviour=cand.duplicateTargetBehaviour,
        guaranteedGatePolicy=cand.guaranteedGatePolicy,
        tierReels=cand.tierReels,
        maxWinX=cand.maxWinX,
        mysteryResultWeights=by_tier.get("LARGE_HILL"),
        mysteryResultWeightsByTier=by_tier,
        tokenValueScale=cand.tokenValueScale,
    )


def run_mix(cfg, cand, pay, n, seed, *, force_phase6_off_config=False):
    mix = base_trigger_mix(cfg)
    p_trigger = mix["P_scatterGe3"]
    # Temporarily disable phase6 in config copy for true feature-off path through resolve_fs_spin
    local_cfg = json.loads(json.dumps(cfg))
    if force_phase6_off_config:
        local_cfg["freeSpins"]["phase6"]["enabled"] = False
        # restore phase5 mystery tables
        archive = local_cfg["freeSpins"]["economy"].get("phase5bMysteryResultWeightsArchive")
        if archive:
            local_cfg["freeSpins"]["economy"]["mysteryResultWeights"] = dict(archive)
            for tier in TIERS:
                local_cfg["freeSpins"]["tiers"][tier]["mysteryResultWeights"] = dict(archive)
        off = bonus_candidate_from_config(local_cfg)
    else:
        off = cand
        local_cfg = cfg

    rows = []
    for i in range(n):
        rng = random.Random(seed + i)
        tier = _start_tier(rng, mix)
        rows.append(
            simulate_bonus(
                random.Random(seed + i),
                tier,
                off,
                config=local_cfg,
                paying_candidate=pay,
            )
        )
    capped = [r["bonusWinXCapped"] for r in rows]
    return {
        "n": n,
        "meanX": statistics.fmean(capped),
        "medianX": statistics.median(capped),
        "p90X": sorted(capped)[int(0.9 * (n - 1))],
        "p99X": sorted(capped)[int(0.99 * (n - 1))],
        "pCap": sum(1 for r in rows if r["maxWinReached"]) / n,
        "meanCapDrag": statistics.fmean(
            max(0.0, r["bonusWinXRaw"] - r["bonusWinXCapped"]) for r in rows
        ),
        "p_trigger": p_trigger,
    }


def paired(cfg, cand, pay, n, seed):
    mix = base_trigger_mix(cfg)
    p_trigger = mix["P_scatterGe3"]
    off_cand = feature_off_candidate(cand)
    # Feature-off still uses phase6 code path with zero weights — R-BATCH unused.
    # Prefer disabling phase6 entirely for true Phase 5B live control.
    cfg_off = json.loads(json.dumps(cfg))
    cfg_off["freeSpins"]["phase6"]["enabled"] = False
    archive = cfg_off["freeSpins"]["economy"]["phase5bMysteryResultWeightsArchive"]
    cfg_off["freeSpins"]["economy"]["mysteryResultWeights"] = dict(archive)
    for tier in TIERS:
        cfg_off["freeSpins"]["tiers"][tier]["mysteryResultWeights"] = dict(archive)
    off_live = bonus_candidate_from_config(cfg_off)

    deltas = []
    on_vals = []
    off_vals = []
    p_rj = p_wk = p_any = 0
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        off = simulate_bonus(
            random.Random(seed + i), tier, off_live, config=cfg_off, paying_candidate=pay
        )
        on = simulate_bonus(
            random.Random(seed + i), tier, cand, config=cfg, paying_candidate=pay
        )
        off_vals.append(off["bonusWinXCapped"])
        on_vals.append(on["bonusWinXCapped"])
        deltas.append(on["bonusWinXCapped"] - off["bonusWinXCapped"])
        # Visibility from on path via stats proxies: use feature flags in stats if present
    return {
        "n": n,
        "featureOffMeanX": statistics.fmean(off_vals),
        "phase6MeanX": statistics.fmean(on_vals),
        "pairedDeltaX": statistics.fmean(deltas),
        "pairedIncrementalPp": statistics.fmean(deltas) * p_trigger * 100.0,
        "p_trigger": p_trigger,
    }


def visibility(cfg, cand, pay, n, seed, tier=None):
    mix = base_trigger_mix(cfg)
    p_rj = p_wk = p_any = p_both = 0
    for i in range(n):
        rng = random.Random(seed + i)
        start = tier or _start_tier(rng, mix)
        state_seed = seed + i
        # Use spin-level aggregation via simulate + recount from a custom probe
        from skyjump_v2_phase5a_engine import new_bonus_state, resolve_fs_spin
        from skyjump_v2_phase6b import ensure_phase6_state

        state = new_bonus_state(start, initial_spins=cand.initialSpins)
        ensure_phase6_state(state)
        had_rj = had_wk = False
        safety = 0
        while state.freeSpinsRemaining > 0 and not state.maxWinReached:
            result = resolve_fs_spin(
                random.Random(state_seed + safety * 10007),
                state,
                cand,
                config=cfg,
                paying_candidate=pay,
            )
            # BUG: different RNG stream — must use single rng advancing
            safety += 1
            if safety > 50:
                break
            had_rj = had_rj or bool(result["features"].get("rejumpCount"))
            had_wk = had_wk or bool(result["features"].get("windKeyCount"))
        # This visibility helper is approximate; main path uses single Random below.
        del had_rj, had_wk
    # Correct visibility with one Random stream
    p_rj = p_wk = p_any = p_both = 0
    for i in range(n):
        rng = random.Random(seed + i)
        start = tier or _start_tier(random.Random(seed + i), mix)
        from skyjump_v2_phase5a_engine import new_bonus_state, resolve_fs_spin
        from skyjump_v2_phase6b import ensure_phase6_state

        state = new_bonus_state(start, initial_spins=cand.initialSpins)
        ensure_phase6_state(state)
        had_rj = had_wk = False
        while state.freeSpinsRemaining > 0 and not state.maxWinReached:
            result = resolve_fs_spin(
                rng,
                state,
                cand,
                config=cfg,
                paying_candidate=pay,
            )
            had_rj = had_rj or bool(result["features"].get("rejumpCount"))
            had_wk = had_wk or bool(result["features"].get("windKeyCount"))
        if had_rj:
            p_rj += 1
        if had_wk:
            p_wk += 1
        if had_rj or had_wk:
            p_any += 1
        if had_rj and had_wk:
            p_both += 1
    return {
        "n": n,
        "tier": tier or "MIX",
        "pRejump": p_rj / n,
        "pWind": p_wk / n,
        "pAnyPhase6": p_any / n,
        "pBoth": p_both / n,
    }


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20260925
    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    mix = base_trigger_mix(cfg)
    p_trigger = mix["P_scatterGe3"]

    print(f"running mix n={n} seed={seed}", flush=True)
    on = run_mix(cfg, cand, pay, n, seed)
    print(f"phase6 mean={on['meanX']:.4f}", flush=True)
    pair_n = min(n, 200_000)
    print(f"paired n={pair_n}", flush=True)
    pair = paired(cfg, cand, pay, pair_n, seed)
    print(
        f"off={pair['featureOffMeanX']:.4f} on={pair['phase6MeanX']:.4f} "
        f"delta={pair['pairedDeltaX']:.4f} pp={pair['pairedIncrementalPp']:.3f}",
        flush=True,
    )
    vis_mix = visibility(cfg, cand, pay, min(n, 100_000), seed)
    vis_lh = visibility(cfg, cand, pay, min(n, 80_000), seed + 11, tier="LARGE_HILL")
    print("vis mix", vis_mix, flush=True)
    print("vis LH", vis_lh, flush=True)

    inc_vs_cert = (on["meanX"] - BASELINE_MEAN) * p_trigger * 100.0
    new_game = BASE_RTP + on["meanX"] * p_trigger * 100.0
    payload = {
        "n": n,
        "seed": seed,
        "phase6": on,
        "paired": pair,
        "visibilityMix": vis_mix,
        "visibilityLargeHill": vis_lh,
        "incrementVsCertifiedPp": inc_vs_cert,
        "newGameRtp": new_game,
        "reservePp": TARGET - new_game,
        "expectedE1": {"inc": 5.195, "game": 94.334, "reserve": 2.166},
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("incrementVsCertifiedPp", "newGameRtp", "reservePp")}, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
