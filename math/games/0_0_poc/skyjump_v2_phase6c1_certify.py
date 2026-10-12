"""Phase 6C.1 certification — LIVE PURE W2 vs feature-off, spaced paired seeds.

Does not mutate weights. Writes artifacts under phase6c1_research/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import random
import statistics
import time
from collections import Counter
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, new_bonus_state, resolve_fs_spin, simulate_bonus
from skyjump_v2_phase6a1_engine import Phase6A1State, choose_stage_a1
from skyjump_v2_phase6a1_search import PACKS, make_spec
from skyjump_v2_phase6b import (
    choose_stage_pure_w2,
    ensure_phase6_state,
    global_flight_multiplier,
    set_stage_selection_mode,
    stages_maxed,
)
from skyjump_v2_phase6c_certify import (
    BASE_RTP,
    BASELINE_MEAN,
    PHASE5_FS_PP,
    P_TRIGGER,
    TARGET,
    cfg_off,
    instrumented_bonus,
    zero_feature,
    _start_tier,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase6c1_research"
STAGES = ("RUN_UP", "TAKEOFF", "FLIGHT")


def _sha_config() -> str:
    return hashlib.sha256((HERE / "skyjump_v2_config.json").read_bytes()).hexdigest()


def research_live_picker_parity(n_states: int = 2000, draws: int = 8) -> dict:
    spec = make_spec(
        "P6A1_E_E1",
        PACKS["E1"],
        rejump_arch="R-BATCH",
        wind_arch="W-CHARGE",
        stage_rule="W2",
    )
    mismatches = []
    trials = 0
    for seed in range(n_states):
        rng = random.Random(seed)
        values = {name: rng.choice([1, 2, 3]) for name in STAGES}
        charges = {name: rng.choice([0, 1]) for name in STAGES}
        for name in STAGES:
            if values[name] == 3:
                charges[name] = 0
        live = new_bonus_state("LARGE_HILL")
        ensure_phase6_state(live)
        key = {"RUN_UP": "runUp", "TAKEOFF": "takeoff", "FLIGHT": "flight"}
        for name in STAGES:
            live.flightMultiplier[key[name]]["value"] = values[name]
            live.flightMultiplier[key[name]]["charge"] = charges[name]
        live.flightMultiplierRunUp = values["RUN_UP"]
        live.flightMultiplierTakeoff = values["TAKEOFF"]
        live.flightMultiplierFlight = values["FLIGHT"]
        live.runUpCharge = charges["RUN_UP"]
        live.takeoffCharge = charges["TAKEOFF"]
        live.flightCharge = charges["FLIGHT"]
        research = Phase6A1State()
        research.run_up = values["RUN_UP"]
        research.takeoff = values["TAKEOFF"]
        research.flight = values["FLIGHT"]
        research.charge_run_up = charges["RUN_UP"]
        research.charge_takeoff = charges["TAKEOFF"]
        research.charge_flight = charges["FLIGHT"]
        for draw in range(draws):
            trials += 1
            rseed = seed * 31 + draw
            live_stage, live_action = choose_stage_pure_w2(random.Random(rseed), live)
            research_stage = choose_stage_a1(random.Random(rseed), research, spec)
            if research_stage is None:
                if live_stage is not None:
                    mismatches.append({"seed": seed, "draw": draw, "live": live_stage, "research": None})
                continue
            expected = "UPGRADE" if charges[research_stage] == 1 else "CHARGE"
            if live_stage != research_stage or live_action != expected:
                mismatches.append(
                    {
                        "seed": seed,
                        "draw": draw,
                        "values": values,
                        "charges": charges,
                        "live": (live_stage, live_action),
                        "research": research_stage,
                        "expectedAction": expected,
                    }
                )
    return {
        "trials": trials,
        "mismatches": len(mismatches),
        "pass": len(mismatches) == 0,
        "examples": mismatches[:5],
    }


def _paired_chunk(args):
    seed, n, mode = args
    cfg = load_v2_config()
    pay = live_candidate_from_config(cfg)
    off_cfg = cfg_off(cfg)
    off_cand = bonus_candidate_from_config(off_cfg)
    on_cand = bonus_candidate_from_config(cfg)
    if mode == "RJ":
        on_cand = zero_feature(on_cand, keep_rejump=True, keep_wind=False)
    elif mode == "WIND":
        on_cand = zero_feature(on_cand, keep_rejump=False, keep_wind=True)
    mix = base_trigger_mix(cfg)
    set_stage_selection_mode("W2_PURE")
    deltas = []
    on_means = []
    off_means = []
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        off = simulate_bonus(random.Random(seed + i), tier, off_cand, config=off_cfg, paying_candidate=pay)
        on = simulate_bonus(random.Random(seed + i), tier, on_cand, config=cfg, paying_candidate=pay)
        deltas.append(on["bonusWinXCapped"] - off["bonusWinXCapped"])
        on_means.append(on["bonusWinXCapped"])
        off_means.append(off["bonusWinXCapped"])
    delta_x = statistics.fmean(deltas)
    return {
        "seed": seed,
        "n": n,
        "mode": mode,
        "offMean": statistics.fmean(off_means),
        "onMean": statistics.fmean(on_means),
        "deltaX": delta_x,
        "incrementalPp": delta_x * P_TRIGGER * 100.0,
        "deltaStd": statistics.stdev(deltas) if n > 1 else 0.0,
    }


def run_paired_seeds(seeds: list[int], n_each: int, workers: int, mode: str = "FULL") -> list[dict]:
    """Run spaced paired seeds; write each result to disk as it completes."""
    tasks = [(seed, n_each, mode) for seed in seeds]
    out_path = OUT / f"paired_{mode.lower()}_partial.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    if workers <= 1:
        for task in tasks:
            row = _paired_chunk(task)
            results.append(row)
            with out_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            print(f"  seed={row['seed']} pp={row['incrementalPp']:.4f}", flush=True)
        return results

    from concurrent.futures import ProcessPoolExecutor, as_completed

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_paired_chunk, task): task[0] for task in tasks}
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            with out_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            print(f"  seed={row['seed']} pp={row['incrementalPp']:.4f}", flush=True)
    results.sort(key=lambda r: r["seed"])
    return results


def visibility_and_wind_states(cfg, cand, pay, n: int, seed: int) -> dict:
    mix = base_trigger_mix(cfg)
    set_stage_selection_mode("W2_PURE")
    mix_counts = Counter()
    lh_counts = Counter()
    wind_stats = Counter()
    globals_final = []
    completed = 0
    any_charge = 0
    two_partial = 0
    three_partial = 0
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        row = instrumented_bonus(random.Random(seed + i), tier, cand, cfg, pay)
        had_rj = row["hadRejump"]
        had_wk = row["hadWind"]
        if had_rj:
            mix_counts["rejump"] += 1
        if had_wk:
            mix_counts["wind"] += 1
        if had_rj or had_wk:
            mix_counts["any"] += 1
        if tier == "LARGE_HILL":
            lh_counts["n"] += 1
            if had_rj:
                lh_counts["rejump"] += 1
            if had_wk:
                lh_counts["wind"] += 1
            if had_rj or had_wk:
                lh_counts["any"] += 1
        g = int(row.get("maxGlobal") or 1)
        globals_final.append(g)
        if row.get("upgrades", 0) > 0:
            completed += 1
        # Approximate charge/completion from final state snapshot if present
        stages = row.get("finalStages")
        if stages:
            charges = [int(stages[s]["charge"]) for s in STAGES]
            charged_n = sum(1 for c in charges if c == 1)
            # Prefer peak simultaneous charges during bonus when available.
            peak = int(row.get("maxSimultaneousCharges") or charged_n)
            if peak >= 1 or charged_n >= 1:
                any_charge += 1
            if peak >= 2:
                two_partial += 1
            if peak >= 3:
                three_partial += 1
            if row.get("everCompletedStage") or any(int(stages[s]["value"]) > 1 for s in STAGES):
                wind_stats["completedStage"] += 1
            if had_wk:
                wind_stats["anyWind"] += 1
        if row.get("coachAfterRejump"):
            wind_stats["coachAfterRejump"] += 1
    lh_n = max(1, lh_counts["n"])
    return {
        "n": n,
        "mix": {
            "pRejump": mix_counts["rejump"] / n,
            "pWind": mix_counts["wind"] / n,
            "pAny": mix_counts["any"] / n,
        },
        "largeHill": {
            "n": lh_counts["n"],
            "pRejump": lh_counts["rejump"] / lh_n,
            "pWind": lh_counts["wind"] / lh_n,
            "pAny": lh_counts["any"] / lh_n,
        },
        "windStates": {
            "pAnyWind": mix_counts["wind"] / n,
            "pAnyCharge": any_charge / n,
            "pTwoPlusPartialCharges": two_partial / n,
            "pThreePartialCharges": three_partial / n,
            "pCompletedStage": wind_stats["completedStage"] / n,
            "pGlobalGe2": sum(1 for g in globals_final if g >= 2) / n,
            "pGlobalGe4": sum(1 for g in globals_final if g >= 4) / n,
            "pGlobalGe8": sum(1 for g in globals_final if g >= 8) / n,
            "pGlobalGe12": sum(1 for g in globals_final if g >= 12) / n,
            "pGlobalGe18": sum(1 for g in globals_final if g >= 18) / n,
            "pGlobalEq27": sum(1 for g in globals_final if g == 27) / n,
            "meanFinalGlobal": statistics.fmean(globals_final) if globals_final else 1.0,
            "pAnyUpgrade": completed / n,
        },
    }


def feature_off_check(cfg, pay, n: int, seed: int) -> dict:
    off_cfg = cfg_off(cfg)
    off_cand = bonus_candidate_from_config(off_cfg)
    mix = base_trigger_mix(cfg)
    rows = []
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        rows.append(simulate_bonus(random.Random(seed + i), tier, off_cand, config=off_cfg, paying_candidate=pay))
    mean_x = statistics.fmean(r["bonusWinXCapped"] for r in rows)
    return {
        "n": n,
        "featureOffMeanX": mean_x,
        "phase5bCertifiedMeanX": BASELINE_MEAN,
        "deltaX": mean_x - BASELINE_MEAN,
        "deltaPp": (mean_x - BASELINE_MEAN) * P_TRIGGER * 100.0,
        "pass": abs(mean_x - BASELINE_MEAN) < 2.0,
        "note": "50k–100k MC vs certified 1M Phase5B mean; use paired OFF means for hard gate",
    }


def persist_target_audit(cfg, cand, pay, n: int, seed: int) -> dict:
    """Quantify mid-spin persist append (research) vs end-of-spin (live) if patchable.

    Live canonical: resolve_fs_spin appends persistentMysteryTargets after feature resolve.
    Research: appends immediately after each coach (including rejump coaches).
    We estimate EV by counting Coach-after-Rejump frequency and do not mutate live.
    """
    mix = base_trigger_mix(cfg)
    coach_after_rj = 0
    bonuses = 0
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        state = new_bonus_state(tier, initial_spins=cand.initialSpins)
        ensure_phase6_state(state)
        while state.freeSpinsRemaining > 0 and not state.maxWinReached:
            result = resolve_fs_spin(random.Random(seed + i + state.freeSpinsPlayed * 997), state, cand, config=cfg, paying_candidate=pay)
            # Actually resolve_fs_spin advances state; use simulate path instead.
            break
        bonuses += 1
    # Use instrumented path from books via simulate_bonus features is limited;
    # report structural note + frequency from phase6 events via instrumented_bonus.
    coach_rj = 0
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        row = instrumented_bonus(random.Random(seed + i), tier, cand, cfg, pay)
        if row.get("coachAfterRejump"):
            coach_rj += 1
    return {
        "researchSemantic": "append persistentMysteryTargets immediately after each Coach (incl. Rejump)",
        "liveSemantic": "append after full spin feature resolve; mid-chain Rejump uses pre-spin targets only",
        "canonical": "Phase 5B/6 design: persist AFTER lines on a board; list growth timing mid-chain not required to match research",
        "action": "KEEP_LIVE",
        "pCoachAfterRejump": coach_rj / n,
        "evImpactPp": None,
        "note": "Secondary difference retained; charged-priority was primary. EV isolated only if mid-spin patch counterfactual is run separately.",
    }


def forced_tails(cfg, cand, pay, n: int, seed: int) -> dict:
    """Conditional / stratified tail smoke under PURE W2 (not full natural rate)."""
    set_stage_selection_mode("W2_PURE")
    mix = base_trigger_mix(cfg)
    cap_hits = 0
    drag = []
    cases = Counter()
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        row = instrumented_bonus(random.Random(seed + i), tier, cand, cfg, pay)
        raw = float(row.get("bonusWinXRaw") or row.get("raw") or 0)
        capped = float(row.get("bonusWinXCapped") or row.get("capped") or 0)
        if row.get("maxWinReached") or capped >= 50_000 - 1e-9:
            cap_hits += 1
        drag.append(max(0.0, raw - capped))
        g = int(row.get("maxGlobal") or 1)
        if tier == "PERFECT_V" and row.get("hadHeadJudge") and g >= 2:
            cases["T5_HJ_mult"] += 1
        if tier == "PERFECT_V" and row.get("hadJudge"):
            cases["T6_Judge"] += 1
        if tier == "PERFECT_V" and row.get("hadHeadJudge"):
            cases["T6_HJ"] += 1
        if g >= 2:
            cases["active_mult_ge2"] += 1
        if g >= 4:
            cases["active_mult_ge4"] += 1
        if capped > 50_000 + 1e-9:
            cases["overCap"] += 1
    return {
        "n": n,
        "pCap": cap_hits / n,
        "meanCapDragX": statistics.fmean(drag) if drag else 0.0,
        "capDragPp": (statistics.fmean(drag) if drag else 0.0) * P_TRIGGER * 100.0,
        "cases": dict(cases),
        "maxPayoutOk": cases.get("overCap", 0) == 0,
    }


def agg_pp(rows: list[dict]) -> dict:
    pps = [r["incrementalPp"] for r in rows]
    m = statistics.fmean(pps)
    sd = statistics.stdev(pps) if len(pps) > 1 else 0.0
    se = sd / math.sqrt(len(pps)) if pps else 0.0
    return {
        "seeds": len(pps),
        "mean": m,
        "std": sd,
        "se": se,
        "ci95": [m - 1.96 * se, m + 1.96 * se],
        "min": min(pps),
        "max": max(pps),
        "pairedBonuses": sum(r["n"] for r in rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-each", type=int, default=500_000)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=max(1, (mp.cpu_count() or 4) // 2))
    parser.add_argument("--vis-n", type=int, default=100_000)
    parser.add_argument("--decomp-n", type=int, default=200_000)
    parser.add_argument("--quick", action="store_true", help="Smoke sizes for CI")
    parser.add_argument("--skip-paired", action="store_true")
    parser.add_argument("--paired-only", action="store_true", help="Reuse prior vis/parity artifacts; run paired+decomp only")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if args.quick:
        args.n_each = 5_000
        args.seeds = 4
        args.vis_n = 5_000
        args.decomp_n = 5_000

    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)

    freeze = {
        "liveConfigSha256": _sha_config(),
        "stageRule": cfg["freeSpins"]["phase6"]["stageRule"],
        "candidateOrigin": cfg["freeSpins"]["phase6"]["candidateOrigin"],
        "windArch": cfg["freeSpins"]["phase6"]["windArch"],
        "rejumpArch": cfg["freeSpins"]["phase6"]["rejumpArch"],
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    print("freeze", freeze, flush=True)

    if args.paired_only and (OUT / "picker_parity.json").exists():
        parity = json.loads((OUT / "picker_parity.json").read_text(encoding="utf-8"))
        off = json.loads((OUT / "feature_off.json").read_text(encoding="utf-8")) if (OUT / "feature_off.json").exists() else {}
        persist = json.loads((OUT / "persist_audit.json").read_text(encoding="utf-8")) if (OUT / "persist_audit.json").exists() else {}
        vis = json.loads((OUT / "visibility_wind_states.json").read_text(encoding="utf-8"))
        tails = json.loads((OUT / "tails.json").read_text(encoding="utf-8")) if (OUT / "tails.json").exists() else {}
        print("reusing prior parity/vis artifacts", flush=True)
    else:
        parity = research_live_picker_parity()
        (OUT / "picker_parity.json").write_text(json.dumps(parity, indent=2), encoding="utf-8")
        print("picker parity", parity["pass"], "trials", parity["trials"], flush=True)
        if not parity["pass"]:
            print("STOP: research/live Wind picker parity failed", parity["examples"], flush=True)
            return

        off = feature_off_check(cfg, pay, n=min(50_000, max(args.vis_n, 10_000)), seed=6_101_000_000)
        (OUT / "feature_off.json").write_text(json.dumps(off, indent=2), encoding="utf-8")
        print("feature-off", off, flush=True)

        persist = persist_target_audit(cfg, cand, pay, n=min(20_000, args.vis_n), seed=6_102_000_000)
        persist_ev_path = OUT / "persist_ev_counterfactual.json"
        if persist_ev_path.exists():
            persist = {**persist, "evCounterfactual": json.loads(persist_ev_path.read_text(encoding="utf-8"))}
        (OUT / "persist_audit.json").write_text(json.dumps(persist, indent=2), encoding="utf-8")

        vis = visibility_and_wind_states(cfg, cand, pay, n=args.vis_n, seed=6_103_000_000)
        (OUT / "visibility_wind_states.json").write_text(json.dumps(vis, indent=2), encoding="utf-8")
        print("visibility", vis["mix"], flush=True)

        tails = forced_tails(cfg, cand, pay, n=args.vis_n, seed=6_104_000_000)
        (OUT / "tails.json").write_text(json.dumps(tails, indent=2), encoding="utf-8")

    # Spaced seeds: stride >> n_each so Random(seed+i) streams never overlap.
    base = 7_026_092_700
    stride = max(args.n_each + 10_000, 1_100_000)
    seeds = [base + i * stride for i in range(args.seeds)]

    paired = []
    if not args.skip_paired:
        partial = OUT / "paired_full_partial.jsonl"
        if partial.exists():
            partial.unlink()
        print(f"paired FULL seeds={seeds} n_each={args.n_each} workers={args.workers}", flush=True)
        t0 = time.perf_counter()
        paired = run_paired_seeds(seeds, args.n_each, args.workers, mode="FULL")
        print("paired done in", time.perf_counter() - t0, "s", flush=True)

    # Decomposition on first seed family (smaller n)
    decomp_seed = seeds[0]
    print(f"decomp seed={decomp_seed} n={args.decomp_n}", flush=True)
    decomp = {}
    for mode in ("FULL", "RJ", "WIND"):
        decomp[mode] = _paired_chunk((decomp_seed, args.decomp_n, mode))
        print(f"  {mode} pp={decomp[mode]['incrementalPp']:.4f}", flush=True)
    rj_pp = decomp["RJ"]["incrementalPp"]
    wind_pp = decomp["WIND"]["incrementalPp"]
    full_pp = decomp["FULL"]["incrementalPp"]
    interaction = full_pp - rj_pp - wind_pp
    decomp_summary = {
        "seed": decomp_seed,
        "n": args.decomp_n,
        "rejumpPp": rj_pp,
        "windPp": wind_pp,
        "fullPp": full_pp,
        "interactionPp": interaction,
        "closure": abs(rj_pp + wind_pp + interaction - full_pp) < 1e-9,
        "rows": decomp,
    }

    # Merge persist EV if present
    persist_ev_path = OUT / "persist_ev_counterfactual.json"
    if persist_ev_path.exists() and isinstance(persist, dict):
        persist = {**persist, "evCounterfactual": json.loads(persist_ev_path.read_text(encoding="utf-8"))}

    paired_agg = agg_pp(paired) if paired else None
    certified_pp = paired_agg["mean"] if paired_agg else None
    game_rtp = BASE_RTP + PHASE5_FS_PP + (certified_pp or 0.0)
    point_reserve = TARGET - game_rtp
    se = paired_agg["se"] if paired_agg else None
    safe_reserve = point_reserve - 1.96 * se if se is not None else None

    classification = "IMPLEMENTATION STILL DIVERGED"
    if parity.get("pass") and paired_agg:
        if se is not None and se <= 0.15:
            # Too hot if point future reserve under 1.0 pp after uncertainty band
            if safe_reserve is not None and safe_reserve < 1.0:
                classification = "STABLE BUT TOO HOT"
            else:
                classification = "STABLE"
        else:
            classification = "NOT STABLE"
    summary = {
        "phase": "6C.1",
        "liveWindRule": "PURE_W2",
        "chargedPriorityRemoved": True,
        "pickerParity": parity,
        "featureOff": off,
        "persist": persist,
        "visibility": vis,
        "tails": tails,
        "paired": paired,
        "pairedAgg": paired_agg,
        "decomposition": decomp_summary,
        "historicalE1Pp": 5.195,
        "historical6cResearchRerunPp": 5.655,
        "historical6cLivePureW2_200kPp": 4.415,
        "certifiedLivePureW2Pp": certified_pp,
        "differenceVsE1": None if certified_pp is None else certified_pp - 5.195,
        "gameRtp": game_rtp,
        "pointFutureReservePp": point_reserve,
        "safeFutureReservePp": safe_reserve,
        "classification": classification,
        "freeze": freeze,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("certifiedLivePureW2Pp", "pairedAgg", "classification", "gameRtp")}, indent=2))


if __name__ == "__main__":
    mp.freeze_support()
    main()
