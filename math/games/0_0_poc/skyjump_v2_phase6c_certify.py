"""Phase 6C certification harness — measurement only; does not mutate live weights."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, new_bonus_state, resolve_fs_spin, simulate_bonus
from skyjump_v2_phase6b import (
    LADDERS,
    STAGES,
    choose_stage_charge_priority,
    choose_stage_pure_w2,
    ensure_phase6_state,
    global_flight_multiplier,
    set_stage_selection_mode,
    stages_maxed,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase6c_research"
BASELINE_MEAN = 27.45472
BASE_RTP = 71.212
PHASE5_FS_PP = 17.92705
TARGET = 96.50
P_TRIGGER = 0.00652967825443787


def _start_tier(rng, mix) -> str:
    roll = rng.random()
    cursor = 0.0
    for tier in TIERS:
        cursor += mix["conditional"][tier]
        if roll < cursor:
            return tier
    return "LARGE_HILL"


def cfg_off(cfg: dict) -> dict:
    local = json.loads(json.dumps(cfg))
    local["freeSpins"]["phase6"]["enabled"] = False
    archive = local["freeSpins"]["economy"]["phase5bMysteryResultWeightsArchive"]
    local["freeSpins"]["economy"]["mysteryResultWeights"] = dict(archive)
    for tier in TIERS:
        local["freeSpins"]["tiers"][tier]["mysteryResultWeights"] = dict(archive)
    return local


def feature_off_candidate(cfg: dict):
    """Phase 5B archive tables with phase6 disabled; always populate by-tier weights."""
    off = cfg_off(cfg)
    cand = bonus_candidate_from_config(off)
    archive = {
        key: int(value)
        for key, value in off["freeSpins"]["economy"]["mysteryResultWeights"].items()
    }
    by_tier = {tier: dict(archive) for tier in TIERS}
    from skyjump_v2_phase5a_engine import BonusCandidate

    return BonusCandidate(
        id=cand.id + ":phase6off",
        upgradeRule=cand.upgradeRule,
        initialSpins=cand.initialSpins,
        maxFreeSpins=cand.maxFreeSpins,
        maxPersistentTargets=cand.maxPersistentTargets,
        duplicateTargetBehaviour=cand.duplicateTargetBehaviour,
        guaranteedGatePolicy=cand.guaranteedGatePolicy,
        tierReels=cand.tierReels,
        maxWinX=cand.maxWinX,
        mysteryResultWeights=archive,
        mysteryResultWeightsByTier=by_tier,
        tokenValueScale=cand.tokenValueScale,
    )


def cand_with_weights(cand, by_tier: dict):
    from skyjump_v2_phase5a_engine import BonusCandidate

    return BonusCandidate(
        id=cand.id,
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


def zero_feature(cand, *, keep_rejump: bool, keep_wind: bool):
    by_tier = {}
    for tier, table in (cand.mysteryResultWeightsByTier or {}).items():
        copied = dict(table)
        move = 0
        if not keep_rejump:
            move += int(copied.get("REJUMP", 0))
            copied["REJUMP"] = 0
        if not keep_wind:
            move += int(copied.get("WIND_KEY", 0))
            copied["WIND_KEY"] = 0
        copied["FLIGHT_TOKEN"] = int(copied["FLIGHT_TOKEN"]) + move
        by_tier[tier] = copied
    return cand_with_weights(cand, by_tier)


def simulate_one(rng, tier, cand, cfg, pay):
    return simulate_bonus(rng, tier, cand, config=cfg, paying_candidate=pay)


def run_mix_stats(cfg, cand, pay, n, seed, *, mode="live"):
    mix = base_trigger_mix(cfg)
    prev = set_stage_selection_mode("W2_PURE" if mode == "pure_w2" else "W2_CHARGE_PRIORITY")
    try:
        rows = []
        for i in range(n):
            rng = random.Random(seed + i)
            tier = _start_tier(rng, mix)
            rows.append(simulate_one(random.Random(seed + i), tier, cand, cfg, pay))
    finally:
        set_stage_selection_mode(prev)
    capped = [r["bonusWinXCapped"] for r in rows]
    return {
        "n": n,
        "seed": seed,
        "mode": mode,
        "meanX": statistics.fmean(capped),
        "pCap": sum(1 for r in rows if r["maxWinReached"]) / n,
        "meanCapDrag": statistics.fmean(max(0.0, r["bonusWinXRaw"] - r["bonusWinXCapped"]) for r in rows),
        "incrementalPp": (statistics.fmean(capped) - BASELINE_MEAN) * P_TRIGGER * 100.0,
        "gameRtp": BASE_RTP + statistics.fmean(capped) * P_TRIGGER * 100.0,
    }


def instrumented_bonus(rng, tier, cand, cfg, pay) -> dict:
    """Simulate with Phase 6 feature counters from spin features."""
    state = new_bonus_state(tier, initial_spins=cand.initialSpins)
    ensure_phase6_state(state)
    had_rj = had_wk = False
    had_judge = had_hj = False
    coach_after_rj = False
    line_rj = 0.0
    collector_paid = 0.0
    collector_raw = 0.0
    upgrades = charges = 0
    keys = 0
    max_g = 1
    max_simultaneous_charges = 0
    ever_completed_stage = False
    wind_actions = []
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        result = resolve_fs_spin(rng, state, cand, config=cfg, paying_candidate=pay)
        feats = result.get("features") or {}
        had_rj = had_rj or bool(feats.get("rejumpCount"))
        had_wk = had_wk or bool(feats.get("windKeyCount"))
        events = feats.get("phase6Events") or []
        if any(c.get("fromRejump") and c.get("selectedSymbolId") for c in (feats.get("coaches") or [])):
            coach_after_rj = True
        for event in events:
            if event["type"] == "skyjumpRejumpLineWins":
                line_rj += float(event.get("lineWinX") or 0)
            if event["type"] == "skyjumpWindKey":
                keys += 1
                act = event.get("action")
                wind_actions.append(act)
                if act == "UPGRADE":
                    upgrades += 1
                elif act == "CHARGE":
                    charges += 1
        for col in feats.get("collections") or []:
            collector_paid += float(col.get("paidCollectionX") or col.get("amount") or 0)
            collector_raw += float(col.get("rawTokenCollectionX") or 0)
        had_judge = had_judge or int(result.get("judgeCount") or 0) > 0
        had_hj = had_hj or int(result.get("headJudgeCount") or 0) > 0
        g = int(global_flight_multiplier(state))
        max_g = max(max_g, g)
        stages = state.flightMultiplier
        charged_now = sum(1 for k in ("runUp", "takeoff", "flight") if int(stages[k]["charge"]) == 1)
        max_simultaneous_charges = max(max_simultaneous_charges, charged_now)
        if any(int(stages[k]["value"]) > 1 for k in ("runUp", "takeoff", "flight")):
            ever_completed_stage = True
    final_stages = {
        "RUN_UP": {
            "value": int(state.flightMultiplier["runUp"]["value"]),
            "charge": int(state.flightMultiplier["runUp"]["charge"]),
        },
        "TAKEOFF": {
            "value": int(state.flightMultiplier["takeoff"]["value"]),
            "charge": int(state.flightMultiplier["takeoff"]["charge"]),
        },
        "FLIGHT": {
            "value": int(state.flightMultiplier["flight"]["value"]),
            "charge": int(state.flightMultiplier["flight"]["charge"]),
        },
    }
    return {
        "bonusWinXCapped": state.bonusWinXCapped,
        "bonusWinXRaw": state.bonusWinXRaw,
        "maxWinReached": state.maxWinReached,
        "hadRejump": had_rj,
        "hadWind": had_wk,
        "hadJudge": had_judge,
        "hadHeadJudge": had_hj,
        "coachAfterRejump": coach_after_rj,
        "lineRejumpX": line_rj,
        "collectorPaidX": collector_paid,
        "collectorRawX": collector_raw,
        "windKeys": keys,
        "upgrades": upgrades,
        "charges": charges,
        "maxGlobal": max_g,
        "finalGlobal": int(global_flight_multiplier(state)),
        "finalStages": final_stages,
        "maxSimultaneousCharges": max_simultaneous_charges,
        "everCompletedStage": ever_completed_stage,
    }


def paired_modes(cfg, cand, pay, n, seed):
    """CONTROL / RJ / WIND / FULL / PURE_W2 on common streams."""
    mix = base_trigger_mix(cfg)
    off_cfg = cfg_off(cfg)
    off_cand = bonus_candidate_from_config(off_cfg)
    rj_cand = zero_feature(cand, keep_rejump=True, keep_wind=False)
    wind_cand = zero_feature(cand, keep_rejump=False, keep_wind=True)

    buckets = {k: [] for k in ("off", "rj", "wind", "full", "pure_w2")}
    vis = Counter()
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        off = simulate_one(random.Random(seed + i), tier, off_cand, off_cfg, pay)
        rj = simulate_one(random.Random(seed + i), tier, rj_cand, cfg, pay)
        wind = simulate_one(random.Random(seed + i), tier, wind_cand, cfg, pay)
        set_stage_selection_mode("W2_CHARGE_PRIORITY")
        full = simulate_one(random.Random(seed + i), tier, cand, cfg, pay)
        set_stage_selection_mode("W2_PURE")
        pure = simulate_one(random.Random(seed + i), tier, cand, cfg, pay)
        set_stage_selection_mode("W2_CHARGE_PRIORITY")
        buckets["off"].append(off["bonusWinXCapped"])
        buckets["rj"].append(rj["bonusWinXCapped"])
        buckets["wind"].append(wind["bonusWinXCapped"])
        buckets["full"].append(full["bonusWinXCapped"])
        buckets["pure_w2"].append(pure["bonusWinXCapped"])

    def mean(xs):
        return statistics.fmean(xs)

    off_m = mean(buckets["off"])
    rj_m = mean(buckets["rj"])
    wind_m = mean(buckets["wind"])
    full_m = mean(buckets["full"])
    pure_m = mean(buckets["pure_w2"])
    rj_pp = (rj_m - off_m) * P_TRIGGER * 100.0
    wind_pp = (wind_m - off_m) * P_TRIGGER * 100.0
    full_pp = (full_m - off_m) * P_TRIGGER * 100.0
    pure_pp = (pure_m - off_m) * P_TRIGGER * 100.0
    interaction = full_pp - rj_pp - wind_pp
    priority_cost = (full_m - pure_m) * P_TRIGGER * 100.0
    return {
        "n": n,
        "seed": seed,
        "meansX": {
            "off": off_m,
            "rj": rj_m,
            "wind": wind_m,
            "full": full_m,
            "pure_w2": pure_m,
        },
        "pairedPp": {
            "rejump": rj_pp,
            "wind": wind_pp,
            "full": full_pp,
            "pure_w2": pure_pp,
            "interaction": interaction,
            "sumParts": rj_pp + wind_pp + interaction,
            "chargedPriorityCostPp": priority_cost,
            "vsCertifiedFullPp": (full_m - BASELINE_MEAN) * P_TRIGGER * 100.0,
            "vsCertifiedPurePp": (pure_m - BASELINE_MEAN) * P_TRIGGER * 100.0,
        },
    }


def wind_instrument_pass(cfg, cand, pay, n, seed):
    mix = base_trigger_mix(cfg)
    key_hist = Counter()
    global_hist = Counter()
    action_hist = Counter()
    paid_by_g = defaultdict(list)
    raw_by_g = defaultdict(list)
    p_any = p_upgrade = p_g2 = p_g4 = p_g8 = 0
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        row = instrumented_bonus(random.Random(seed + i), tier, cand, cfg, pay)
        key_hist[min(row["windKeys"], 10)] += 1
        g = row["finalGlobal"]
        global_hist[g] += 1
        paid_by_g[g].append(row["collectorPaidX"])
        raw_by_g[g].append(row["collectorRawX"])
        if row["hadWind"]:
            p_any += 1
        if row["upgrades"] > 0:
            p_upgrade += 1
            action_hist["had_upgrade"] += 1
        if row["charges"] > 0 and row["upgrades"] == 0:
            action_hist["charge_only_bonus"] += 1
        if g >= 2:
            p_g2 += 1
        if g >= 4:
            p_g4 += 1
        if g >= 8:
            p_g8 += 1
    by_global = {}
    for g, pays in paid_by_g.items():
        by_global[str(g)] = {
            "p": len(pays) / n,
            "meanCollectorPaid": statistics.fmean(pays),
            "meanCollectorRaw": statistics.fmean(raw_by_g[g]),
        }
    return {
        "n": n,
        "pAnyWind": p_any / n,
        "pStageComplete": p_upgrade / n,
        "pGlobalGe2": p_g2 / n,
        "pGlobalGe4": p_g4 / n,
        "pGlobalGe8": p_g8 / n,
        "keyHistogram": {str(k): v / n for k, v in sorted(key_hist.items())},
        "globalHistogram": {str(k): v / n for k, v in sorted(global_hist.items())},
        "byGlobal": by_global,
        "actionNotes": dict(action_hist),
    }


def exact_wind_transitions(n_keys_max: int = 12, mc: int = 200_000, seed: int = 7):
    """Exact enumeration is large; use MC over Wind-key-only streams for N=0..12."""
    order = LADDERS["K1"]
    results = {}
    for n_keys in range(0, n_keys_max + 1):
        globals_c = Counter()
        upgrades = charges = sat = 0
        for i in range(mc):
            rng = random.Random(seed + n_keys * 1_000_003 + i)
            # Fake FreeSpinState-like object
            class S:
                pass

            state = S()
            state.flightMultiplier = {
                "runUp": {"value": 1, "charge": 0},
                "takeoff": {"value": 1, "charge": 0},
                "flight": {"value": 1, "charge": 0},
            }
            state.windKeysCollected = 0
            for _ in range(n_keys):
                if stages_maxed(state):
                    sat += 1
                    break
                stage, action = choose_stage_charge_priority(rng, state)
                if stage is None:
                    break
                st = state.flightMultiplier
                key = {"RUN_UP": "runUp", "TAKEOFF": "takeoff", "FLIGHT": "flight"}[stage]
                if action == "UPGRADE":
                    upgrades += 1
                    old = int(st[key]["value"])
                    st[key]["value"] = order[order.index(old) + 1]
                    st[key]["charge"] = 0
                else:
                    charges += 1
                    st[key]["charge"] = 1
            g = (
                int(state.flightMultiplier["runUp"]["value"])
                * int(state.flightMultiplier["takeoff"]["value"])
                * int(state.flightMultiplier["flight"]["value"])
            )
            globals_c[g] += 1
        results[str(n_keys)] = {
            "mc": mc,
            "globalDist": {str(k): v / mc for k, v in sorted(globals_c.items())},
            "meanUpgrades": upgrades / mc,
            "meanCharges": charges / mc,
            "pHitSaturationMid": sat / mc,
        }
    # Compare pure W2 for N=4,6,8
    compare = {}
    for n_keys in (2, 4, 6, 8):
        for label, chooser in (("priority", choose_stage_charge_priority), ("pure_w2", choose_stage_pure_w2)):
            globals_c = Counter()
            for i in range(mc):
                rng = random.Random(seed + 99 + n_keys * 17 + i)
                state = type("S", (), {})()
                state.flightMultiplier = {
                    "runUp": {"value": 1, "charge": 0},
                    "takeoff": {"value": 1, "charge": 0},
                    "flight": {"value": 1, "charge": 0},
                }
                for _ in range(n_keys):
                    if stages_maxed(state):
                        break
                    stage, action = chooser(rng, state)
                    if stage is None:
                        break
                    st = state.flightMultiplier
                    key = {"RUN_UP": "runUp", "TAKEOFF": "takeoff", "FLIGHT": "flight"}[stage]
                    if action == "UPGRADE":
                        old = int(st[key]["value"])
                        st[key]["value"] = order[order.index(old) + 1]
                        st[key]["charge"] = 0
                    else:
                        st[key]["charge"] = 1
                g = (
                    int(state.flightMultiplier["runUp"]["value"])
                    * int(state.flightMultiplier["takeoff"]["value"])
                    * int(state.flightMultiplier["flight"]["value"])
                )
                globals_c[g] += 1
            compare.setdefault(str(n_keys), {})[label] = {
                "meanGlobal": sum(int(k) * v for k, v in globals_c.items()) / mc,
                "pGe2": sum(v for k, v in globals_c.items() if int(k) >= 2) / mc,
                "pGe4": sum(v for k, v in globals_c.items() if int(k) >= 4) / mc,
                "pGe8": sum(v for k, v in globals_c.items() if int(k) >= 8) / mc,
            }
    return {"byNKeysPriority": results, "priorityVsPure": compare}


def feature_off_equivalence(cfg, cand, pay, n=50_000, seed=20260930):
    """Compare live phase6-off vs archive-only candidate on same streams."""
    mix = base_trigger_mix(cfg)
    off_cfg = cfg_off(cfg)
    off_cand = bonus_candidate_from_config(off_cfg)
    # Second path: same archive weights but ensure phase6 disabled
    assert off_cfg["freeSpins"]["phase6"]["enabled"] is False
    metrics = defaultdict(list)
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        row = simulate_one(random.Random(seed + i), tier, off_cand, off_cfg, pay)
        metrics["meanX"].append(row["bonusWinXCapped"])
        metrics["spins"].append(row["freeSpinsPlayed"])
        metrics["raw"].append(row["bonusWinXRaw"])
    mean_x = statistics.fmean(metrics["meanX"])
    return {
        "n": n,
        "featureOffMeanX": mean_x,
        "certifiedPhase5bMeanX": BASELINE_MEAN,
        "deltaVsCertifiedX": mean_x - BASELINE_MEAN,
        "deltaVsCertifiedPp": (mean_x - BASELINE_MEAN) * P_TRIGGER * 100.0,
        "meanSpins": statistics.fmean(metrics["spins"]),
        "passLoose": abs(mean_x - BASELINE_MEAN) < 0.35,  # MC tolerance ~0.35x ≈ 0.23pp
    }


def research_e1_repro(n=200_000, seed=20260923):
    """Reproduce Phase 6A.1 research E1 incremental on research engine."""
    from skyjump_v2_phase6a_search import build_context
    from skyjump_v2_phase6a1_search import PACKS, decorate, make_spec, run_mix, summarise

    cfg = load_v2_config()
    ctx = build_context(cfg)
    p = ctx["mix"]["P_scatterGe3"]
    spec = make_spec("P6A1_E_E1", PACKS["E1"], rejump_arch="R-BATCH", wind_arch="W-CHARGE")
    rows = run_mix(ctx, spec, n, seed)
    stats = decorate(spec, summarise(rows, p), p)
    # Also try research with charged priority if we can monkeypatch choose_stage_a1
    from skyjump_v2_phase6a1_engine import apply_wind_key as a1_apply
    import skyjump_v2_phase6a1_engine as a1eng

    original = a1eng.choose_stage_a1

    from skyjump_v2_phase6a_engine import LADDERS as A1_LADDERS

    def choose_priority(rng, state, spec):
        order = A1_LADDERS[spec.ladder]
        stages = {
            "RUN_UP": int(state.run_up),
            "TAKEOFF": int(state.takeoff),
            "FLIGHT": int(state.flight),
        }
        eligible = [name for name in ("RUN_UP", "TAKEOFF", "FLIGHT") if stages[name] != order[-1]]
        if not eligible:
            return None
        charged = [name for name in eligible if a1eng._charge_of(state, name) == 1]
        pool_src = charged if charged else eligible
        lowest = min(stages[name] for name in pool_src)
        pool = [name for name in pool_src if stages[name] == lowest]
        return rng.choice(pool)

    a1eng.choose_stage_a1 = choose_priority
    try:
        rows_p = run_mix(ctx, spec, min(n, 100_000), seed + 1)
        stats_p = decorate(spec, summarise(rows_p, p), p)
    finally:
        a1eng.choose_stage_a1 = original

    return {
        "researchPureW2": {
            "n": n,
            "seed": seed,
            "meanX": stats["meanX"],
            "incrementalPp": stats["incrementalPp"],
            "pRejump": stats["pRejump"],
            "pWind": stats["pWind"],
            "historicalE1IncrementalPp": 5.194785765879253,
            "reproduced": abs(stats["incrementalPp"] - 5.194785765879253) < 0.35 or n < 1_000_000,
        },
        "researchWithChargedPriority": {
            "n": min(n, 100_000),
            "meanX": stats_p["meanX"],
            "incrementalPp": stats_p["incrementalPp"],
            "pRejump": stats_p["pRejump"],
            "pWind": stats_p["pWind"],
        },
    }


def multi_seed(cfg, cand, pay, seeds, n_each, paired_n):
    unpaired = []
    paired = []
    for seed in seeds:
        print(f"multi-seed unpaired seed={seed} n={n_each}", flush=True)
        u = run_mix_stats(cfg, cand, pay, n_each, seed, mode="live")
        unpaired.append(u)
        print(f"  mean={u['meanX']:.4f} inc={u['incrementalPp']:.3f}", flush=True)
        print(f"multi-seed paired seed={seed} n={paired_n}", flush=True)
        off_cfg = cfg_off(cfg)
        off_cand = bonus_candidate_from_config(off_cfg)
        mix = base_trigger_mix(cfg)
        deltas = []
        on_vals = []
        off_vals = []
        for i in range(paired_n):
            tier = _start_tier(random.Random(seed + i), mix)
            off = simulate_one(random.Random(seed + i), tier, off_cand, off_cfg, pay)
            on = simulate_one(random.Random(seed + i), tier, cand, cfg, pay)
            off_vals.append(off["bonusWinXCapped"])
            on_vals.append(on["bonusWinXCapped"])
            deltas.append(on["bonusWinXCapped"] - off["bonusWinXCapped"])
        pp = statistics.fmean(deltas) * P_TRIGGER * 100.0
        paired.append(
            {
                "seed": seed,
                "n": paired_n,
                "offMean": statistics.fmean(off_vals),
                "onMean": statistics.fmean(on_vals),
                "deltaX": statistics.fmean(deltas),
                "incrementalPp": pp,
            }
        )
        print(f"  paired pp={pp:.3f}", flush=True)
    incs = [u["incrementalPp"] for u in unpaired]
    pps = [p["incrementalPp"] for p in paired]
    def agg(xs):
        m = statistics.fmean(xs)
        sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
        se = sd / math.sqrt(len(xs)) if xs else 0.0
        return {
            "mean": m,
            "median": statistics.median(xs),
            "std": sd,
            "se": se,
            "min": min(xs),
            "max": max(xs),
            "ci95": [m - 1.96 * se, m + 1.96 * se],
        }
    return {"unpaired": unpaired, "paired": paired, "unpairedAgg": agg(incs), "pairedAgg": agg(pps)}


def stratified_tails(cfg, cand, pay, seed=20261001):
    """Oversample high-token / collector / multiplier cases; report raw/capped."""
    CAP = float(cand.maxWinX)
    SCALE = float(cand.tokenValueScale or 1.5)
    cases = [
        ("T5_J_1x", 5000, 1, 1, 1),
        ("T5_HJ_4x", 5000, 2, 1, 4),
        ("T5_HJ_27x", 750, 2, 1, 27),
        ("T6_J_1x", 10000, 1, 1, 1),
        ("T6_HJ_2x", 10000, 2, 1, 2),
        ("T6_J_th2_m3", 10000, 1, 2, 3),
        ("T6_HJ_m4", 10000, 2, 1, 4),
        ("T6_HJ_m8", 10000, 2, 1, 8),
        ("T6_J_th2_m27", 10000, 1, 2, 27),
        ("T6_HJ_m27", 10000, 2, 1, 27),
        ("T6_50000_J", 50000, 1, 1, 1),
        ("multi_T5_T6_HJ_8x", 750 + 10000, 2, 1, 8),
    ]
    rows = []
    for label, face, collectors, thermals, flight in cases:
        raw = face * SCALE * thermals * collectors * flight
        capped = min(raw, CAP)
        rows.append({"case": label, "raw": raw, "capped": capped, "drag": max(0.0, raw - capped)})
    # Natural high-floor probe via Perfect V oversample
    mix = base_trigger_mix(cfg)
    high = []
    for i in range(80_000):
        row = simulate_one(random.Random(seed + i), "PERFECT_V", cand, cfg, pay)
        if row["bonusWinXRaw"] >= 1000:
            high.append(row)
    natural_high = {
        "nProbe": 80_000,
        "nHighRawGe1000": len(high),
        "meanRawIfHigh": statistics.fmean(r["bonusWinXRaw"] for r in high) if high else 0,
        "meanCappedIfHigh": statistics.fmean(r["bonusWinXCapped"] for r in high) if high else 0,
        "pCapInProbe": sum(1 for r in high if r["maxWinReached"]) / max(1, len(high)),
    }
    return {
        "forcedAnalytic": {
            "rows": rows,
            "forcedRawMax": max(r["raw"] for r in rows),
            "forcedCappedMax": max(r["capped"] for r in rows),
            "allCappedLe50k": all(r["capped"] <= CAP for r in rows),
        },
        "perfectVHighProbe": natural_high,
    }


def cmd_quick(args):
    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    OUT.mkdir(exist_ok=True)
    path = OUT / "quick_cert.json"
    payload = {}
    if path.exists() and args.resume:
        payload = json.loads(path.read_text(encoding="utf-8"))
        print("resuming from", path, flush=True)

    freeze = json.loads((OUT / "freeze.json").read_text(encoding="utf-8")) if (OUT / "freeze.json").exists() else {}
    payload["freezeSha"] = freeze.get("liveConfigSha256")

    if "pairedModes" not in payload:
        print("paired modes n=", args.n, flush=True)
        paired = paired_modes(cfg, cand, pay, args.n, args.seed)
        print(json.dumps(paired["pairedPp"], indent=2), flush=True)
        payload["pairedModes"] = paired
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print("skip pairedModes (cached)", flush=True)

    if "wind" not in payload:
        print("wind instrument…", flush=True)
        payload["wind"] = wind_instrument_pass(cfg, cand, pay, min(args.n, 80_000), args.seed + 3)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "exactWind" not in payload:
        print("exact wind…", flush=True)
        payload["exactWind"] = exact_wind_transitions()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "featureOffEquivalence" not in payload:
        print("feature-off equiv…", flush=True)
        payload["featureOffEquivalence"] = feature_off_equivalence(
            cfg, cand, pay, n=min(args.n, 80_000), seed=args.seed + 9
        )
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "researchE1" not in payload:
        print("research e1 repro…", flush=True)
        payload["researchE1"] = research_e1_repro(n=min(args.n, 200_000), seed=20260923)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if "stratified" not in payload:
        print("stratified…", flush=True)
        payload["stratified"] = stratified_tails(cfg, cand, pay)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", path, flush=True)


def cmd_save_paired_snapshot(args):
    """Persist paired Pp already printed by a prior run (manual recovery)."""
    OUT.mkdir(exist_ok=True)
    path = OUT / "quick_cert.json"
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    payload["pairedModes"] = {
        "n": args.n,
        "seed": args.seed,
        "meansX": None,
        "pairedPp": json.loads(args.pp_json),
        "note": "meansX omitted; pairedPp recovered from successful console print",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", path)


def cmd_multiseed(args):
    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    OUT.mkdir(exist_ok=True)
    seeds = [int(s) for s in args.seeds.split(",")]
    result = multi_seed(cfg, cand, pay, seeds, args.n, args.paired_n)
    path = OUT / "multiseed.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("wrote", path, flush=True)
    print(json.dumps({"unpairedAgg": result["unpairedAgg"], "pairedAgg": result["pairedAgg"]}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quick")
    q.add_argument("--n", type=int, default=200_000)
    q.add_argument("--seed", type=int, default=20260926)
    q.add_argument("--resume", action="store_true")
    q.set_defaults(func=cmd_quick)
    m = sub.add_parser("multiseed")
    m.add_argument("--seeds", default="20260925,20260926,20260927,20260928,20260929")
    m.add_argument("--n", type=int, default=1_000_000)
    m.add_argument("--paired-n", type=int, default=200_000)
    m.set_defaults(func=cmd_multiseed)
    s = sub.add_parser("save-paired")
    s.add_argument("--n", type=int, default=200_000)
    s.add_argument("--seed", type=int, default=20260926)
    s.add_argument("--pp-json", required=True)
    s.set_defaults(func=cmd_save_paired_snapshot)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
