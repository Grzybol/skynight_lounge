"""Phase 7A.1 — full-round PT2 / BODY1 / WR interaction certification (research only).

Does not mutate live config. Writes artifacts under phase7a1_research/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, new_bonus_state, resolve_fs_spin
from skyjump_v2_phase6b import ensure_phase6_state, set_stage_selection_mode
from skyjump_v2_phase7a_research import apply_body
from skyjump_v2_reels import REGULAR_IDS

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7a1_research"
P7A = HERE / "phase7a_research"
P_TRIGGER = 0.00652967825443787
BASE_RTP = 71.212
PHASE5B_PP = 17.92705
PHASE6_PP = 4.689
PHASE6_SE = 0.078
CURRENT_GAME = 93.828
MAX_WIN = 50_000.0
REL = {"LARGE_HILL": 1.0, "SKI_FLYING": 3.0, "WORLD_CUP": 6.0, "PERFECT_V": 12.0}
ORDER = ["P1", "P2", "P3", "M1", "M2", "M3", "L1", "L2", "L3"]


def _sha_config() -> str:
    return hashlib.sha256((HERE / "skyjump_v2_config.json").read_bytes()).hexdigest()


def _start_tier(rng, mix) -> str:
    roll = rng.random()
    cursor = 0.0
    for tier in TIERS:
        cursor += mix["conditional"][tier]
        if roll < cursor:
            return tier
    return "LARGE_HILL"


def load_pt2_awards() -> dict:
    pt2 = json.loads((P7A / "paytables.json").read_text(encoding="utf-8"))["PT2"]["awards"]
    return {s: {str(k): float(v) for k, v in pt2[s].items()} for s in REGULAR_IDS}


def with_paytable(cfg: dict, awards: dict) -> dict:
    local = json.loads(json.dumps(cfg))
    local["paytable"]["awards"] = {
        s: {str(k): float(v) for k, v in awards[s].items()} for s in REGULAR_IDS
    }
    return local


def pctile(xs, p):
    if not xs:
        return 0.0
    ordered = sorted(xs)
    return ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1)))]


def instrumented(rng, tier, cand, cfg, pay, *, collect_wr_ops: bool = False) -> dict:
    """One bonus under Phase 6C.1 semantics with line / rejump / visibility / WR ops."""
    set_stage_selection_mode("W2_PURE")
    state = new_bonus_state(tier, initial_spins=cand.initialSpins)
    ensure_phase6_state(state)
    line_fs = 0.0
    line_rj = 0.0
    had_rj = had_wk = False
    t5 = t6 = 0
    wr_ops = []
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        accrued = float(state.bonusWinXCapped)
        spin_tier = state.bonusTier
        if collect_wr_ops:
            wr_ops.append(
                {
                    "tier": spin_tier,
                    "accruedBonusX": accrued,
                    "fillX": max(0.0, MAX_WIN - accrued),
                    "rel": REL[spin_tier],
                }
            )
        result = resolve_fs_spin(rng, state, cand, config=cfg, paying_candidate=pay)
        line_fs += float(result["lineWinX"])
        feats = result.get("features") or {}
        had_rj = had_rj or bool(feats.get("rejumpCount"))
        had_wk = had_wk or bool(feats.get("windKeyCount"))
        for event in feats.get("phase6Events") or []:
            if event.get("type") == "skyjumpRejumpLineWins":
                line_rj += float(event.get("lineWinX") or 0)
        for tok in feats.get("tokens") or []:
            tier_i = int(tok.get("tier") or 0)
            if tier_i == 5:
                t5 += 1
            elif tier_i == 6:
                t6 += 1
        # tokens may also appear under resolves / board — count collector faces if present
        for col in feats.get("collections") or []:
            for face in col.get("tokens") or []:
                tier_i = int(face.get("tier") or 0)
                if tier_i == 5:
                    t5 += 1
                elif tier_i == 6:
                    t6 += 1
    return {
        "bonusWinXCapped": state.bonusWinXCapped,
        "bonusWinXRaw": state.bonusWinXRaw,
        "maxWinReached": state.maxWinReached,
        "lineFsX": line_fs,
        "lineRejumpX": line_rj,
        "hadRejump": had_rj,
        "hadWind": had_wk,
        "hadPhase6": had_rj or had_wk,
        "t5Count": t5,
        "t6Count": t6,
        "capDragX": max(0.0, state.bonusWinXRaw - state.bonusWinXCapped),
        "wrOps": wr_ops,
    }


def _build_variants(cfg):
    pt0 = {s: {str(k): float(v) for k, v in cfg["paytable"]["awards"][s].items()} for s in REGULAR_IDS}
    pt2 = load_pt2_awards()
    return {
        "PT0_BODY0": with_paytable(cfg, pt0),
        "PT0_BODY1": apply_body(with_paytable(cfg, pt0), "BODY1"),
        "PT2_BODY0": with_paytable(cfg, pt2),
        "PT2_BODY1": apply_body(with_paytable(cfg, pt2), "BODY1"),
    }


def _chunk_worker(args):
    seed0, n, collect_wr = args
    cfg = load_v2_config()
    mix = base_trigger_mix(cfg)
    variants = _build_variants(cfg)
    pays = {k: live_candidate_from_config(v) for k, v in variants.items()}
    cands = {k: bonus_candidate_from_config(v) for k, v in variants.items()}
    rows = {k: [] for k in variants}
    wr_ops_all = []
    for i in range(n):
        tier = _start_tier(random.Random(seed0 + i), mix)
        for key, vcfg in variants.items():
            row = instrumented(
                random.Random(seed0 + i),
                tier,
                cands[key],
                vcfg,
                pays[key],
                collect_wr_ops=(collect_wr and key == "PT2_BODY1"),
            )
            if collect_wr and key == "PT2_BODY1":
                wr_ops_all.extend(row["wrOps"])
            row.pop("wrOps", None)
            row["startTier"] = tier
            rows[key].append(row)
    return {"rows": rows, "wrOps": wr_ops_all, "n": n, "seed0": seed0}


def summarize_rows(rows):
    xs = [r["bonusWinXCapped"] for r in rows]
    n = len(rows)
    return {
        "n": n,
        "meanX": statistics.fmean(xs),
        "median": statistics.median(xs),
        "p25": pctile(xs, 0.25),
        "p75": pctile(xs, 0.75),
        "p90": pctile(xs, 0.90),
        "p95": pctile(xs, 0.95),
        "p99": pctile(xs, 0.99),
        "p99_9": pctile(xs, 0.999),
        "pLt5": sum(1 for x in xs if x < 5) / n,
        "pLt10": sum(1 for x in xs if x < 10) / n,
        "pCap": sum(1 for r in rows if r["maxWinReached"]) / n,
        "meanCapDrag": statistics.fmean(r["capDragX"] for r in rows),
        "meanLineFsX": statistics.fmean(r["lineFsX"] for r in rows),
        "meanLineRejumpX": statistics.fmean(r["lineRejumpX"] for r in rows),
        "pRejump": sum(1 for r in rows if r["hadRejump"]) / n,
        "pWind": sum(1 for r in rows if r["hadWind"]) / n,
        "pPhase6": sum(1 for r in rows if r["hadPhase6"]) / n,
        "meanT5": statistics.fmean(r["t5Count"] for r in rows),
        "meanT6": statistics.fmean(r["t6Count"] for r in rows),
        "seMeanX": statistics.stdev(xs) / math.sqrt(n) if n > 1 else 0.0,
    }


def paired_delta_pp(a_rows, b_rows):
    """Incremental game RTP pp of b vs a on common streams."""
    diffs = [b["bonusWinXCapped"] - a["bonusWinXCapped"] for a, b in zip(a_rows, b_rows)]
    mean_d = statistics.fmean(diffs)
    se = statistics.stdev(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
    return {
        "meanDeltaX": mean_d,
        "pp": mean_d * P_TRIGGER * 100.0,
        "sePp": se * P_TRIGGER * 100.0,
        "lineFsDeltaX": statistics.fmean(b["lineFsX"] - a["lineFsX"] for a, b in zip(a_rows, b_rows)),
        "lineRjDeltaX": statistics.fmean(
            b["lineRejumpX"] - a["lineRejumpX"] for a, b in zip(a_rows, b_rows)
        ),
    }


def wr_fill_from_ops(ops):
    if not ops:
        return {}
    wsum = sum(o["rel"] for o in ops)
    e_accrued = sum(o["rel"] * o["accruedBonusX"] for o in ops) / wsum
    e_fill = sum(o["rel"] * o["fillX"] for o in ops) / wsum
    # also unweighted per-opportunity mean
    e_accrued_flat = statistics.fmean(o["accruedBonusX"] for o in ops)
    e_fill_flat = statistics.fmean(o["fillX"] for o in ops)
    return {
        "nOps": len(ops),
        "eAccruedBonusWeighted": e_accrued,
        "eIncrementalFillWeighted": e_fill,
        "eAccruedBonusFlat": e_accrued_flat,
        "eIncrementalFillFlat": e_fill_flat,
        "note": "Weights = WR-C tier intensity 1:3:6:12 on opportunity spins; BASE prior not included",
    }


def solve_wr(target_game_rtp, core_rtp, e_fill, mix):
    """Solve global WR scale for WR-C so game RTP ~= target. core_rtp excludes WR."""
    need_pp = target_game_rtp - core_rtp
    need_frac = need_pp / 100.0
    # Per paid round EV from WR = p_paid * e_fill_round, but opportunities are per FS spin.
    # Model: each FS spin opportunity fires with p = c * rel[tier].
    # E[WR$ per bonus] = E[sum_ops c*rel*fill] = c * sum_ops(rel*fill)/n_bonuses
    # From ops list we can get mean_weighted_fill_mass_per_bonus = (sum rel*fill) / n_bonuses
    # Then E[WR per bonus] = c * mass, WR_pp = P_TRIGGER * c * mass * 100
    # need_frac = P_TRIGGER * c * mass => c = need_frac / (P_TRIGGER * mass)
    return need_pp, need_frac


def validate_artifacts(cfg):
    pt = json.loads((P7A / "paytables.json").read_text(encoding="utf-8"))
    pt2 = pt["PT2"]["awards"]
    mono = all(pt2[s]["3"] <= pt2[s]["4"] <= pt2[s]["5"] for s in ORDER)
    grain = all(abs(round(float(v) / 0.1) * 0.1 - float(v)) < 1e-9 for s in ORDER for v in pt2[s].values())
    breaks = []
    for m in ("3", "4", "5"):
        vals = [float(pt2[s][m]) for s in ORDER]
        for i in range(len(vals) - 1):
            if vals[i] + 1e-12 < vals[i + 1]:
                breaks.append({"match": int(m), "left": ORDER[i], "right": ORDER[i + 1], "vals": [vals[i], vals[i + 1]]})
    pt0 = {s: {str(k): float(v) for k, v in cfg["paytable"]["awards"][s].items()} for s in REGULAR_IDS}
    base0 = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], pt0)["lineRtp"] * 100
    base2 = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], load_pt2_awards())["lineRtp"] * 100
    b1 = apply_body(cfg, "BODY1")
    body_ok = (
        b1["flightTokens"]["tiers"]["5"]["weight"] == cfg["flightTokens"]["tiers"]["5"]["weight"]
        and b1["flightTokens"]["tiers"]["6"]["weight"] == cfg["flightTokens"]["tiers"]["6"]["weight"]
        and b1["flightTokens"]["valueWeights"]["5"] == cfg["flightTokens"]["valueWeights"]["5"]
        and b1["flightTokens"]["valueWeights"]["6"] == cfg["flightTokens"]["valueWeights"]["6"]
    )
    return {
        "configSha256": _sha_config(),
        "pt2Monotonic": mono,
        "pt2Grain01": grain,
        "pt2ClassHierarchyPass": len(breaks) == 0,
        "pt2HierarchyBreaks": breaks,
        "body1T5T6Unchanged": body_ok,
        "baseExact": {"PT0": base0, "PT2": base2, "deltaPp": base2 - base0},
        "wrRatio": REL,
    }


def run_matrix(n: int, seed: int, workers: int, collect_wr: bool):
    OUT.mkdir(parents=True, exist_ok=True)
    chunk = max(2_000, n // max(1, workers * 4))
    tasks = []
    left = n
    cur = seed
    while left > 0:
        take = min(chunk, left)
        tasks.append((cur, take, collect_wr))
        cur += take
        left -= take
    t0 = time.time()
    merged = {k: [] for k in ("PT0_BODY0", "PT0_BODY1", "PT2_BODY0", "PT2_BODY1")}
    wr_ops = []
    if workers <= 1:
        for task in tasks:
            part = _chunk_worker(task)
            for k, rows in part["rows"].items():
                merged[k].extend(rows)
            wr_ops.extend(part["wrOps"])
            print(f"chunk {part['seed0']} n={part['n']} elapsed={time.time()-t0:.1f}s", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_chunk_worker, task): task for task in tasks}
            done = 0
            for fut in as_completed(futs):
                part = fut.result()
                for k, rows in part["rows"].items():
                    merged[k].extend(rows)
                wr_ops.extend(part["wrOps"])
                done += part["n"]
                print(f"done {done}/{n} elapsed={time.time()-t0:.1f}s", flush=True)
    return merged, wr_ops, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=7_701_000_000)
    ap.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 4))))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        args.n = 2_000
        args.workers = 1

    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_v2_config()
    validation = validate_artifacts(cfg)
    (OUT / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print("VALIDATION", json.dumps(validation, indent=2), flush=True)

    # freeze already may exist; refresh semantic snap
    freeze = {
        "configSha256": validation["configSha256"],
        "certifiedStack": {
            "BASE": BASE_RTP,
            "Phase5B": PHASE5B_PP,
            "Phase6": PHASE6_PP,
            "Phase6SE": PHASE6_SE,
            "total": CURRENT_GAME,
        },
        "artAuthority": "docs/skyjump-v2/23_SYMBOL_ASSET_MANIFEST.md",
        "artLock": "PASS",
        "wait": "NONE",
        "phase6": deepcopy(cfg["freeSpins"]["phase6"]),
        "livePaytable": validation["baseExact"],
    }
    (OUT / "live_freeze.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")

    print(f"MATRIX n={args.n} workers={args.workers}", flush=True)
    merged, wr_ops, elapsed = run_matrix(args.n, args.seed, args.workers, collect_wr=True)
    summaries = {k: summarize_rows(rows) for k, rows in merged.items()}
    (OUT / "matrix_summaries.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    # Paired deltas
    a = merged["PT0_BODY0"]
    deltas = {
        "BODY1_standalone": paired_delta_pp(a, merged["PT0_BODY1"]),
        "PT2_standalone": paired_delta_pp(a, merged["PT2_BODY0"]),
        "PT2_BODY1_combo": paired_delta_pp(a, merged["PT2_BODY1"]),
        "BODY1_on_PT2": paired_delta_pp(merged["PT2_BODY0"], merged["PT2_BODY1"]),
        "PT2_on_BODY1": paired_delta_pp(merged["PT0_BODY1"], merged["PT2_BODY1"]),
    }
    interaction_pp = (
        deltas["PT2_BODY1_combo"]["pp"]
        - deltas["BODY1_standalone"]["pp"]
        - deltas["PT2_standalone"]["pp"]
    )
    deltas["interactionPp"] = interaction_pp
    (OUT / "paired_deltas.json").write_text(json.dumps(deltas, indent=2), encoding="utf-8")

    base_delta = validation["baseExact"]["deltaPp"]
    pt2_fs_pp = deltas["PT2_standalone"]["lineFsDeltaX"] * P_TRIGGER * 100.0
    pt2_rj_pp = deltas["PT2_standalone"]["lineRjDeltaX"] * P_TRIGGER * 100.0
    # Total PT2 full-game from paired bonus mean delta + exact BASE
    pt2_bonus_total_pp = deltas["PT2_standalone"]["pp"]
    # Bonus total includes FS lines + rejump lines + any feature coupling via lines affecting room/cap.
    # Feature-nonline residual:
    pt2_bonus_nonline_pp = pt2_bonus_total_pp - pt2_fs_pp - pt2_rj_pp
    pt2_full = {
        "baseLineDeltaPp": base_delta,
        "fsInitialLineDeltaPp": pt2_fs_pp,
        "rejumpLineDeltaPp": pt2_rj_pp,
        "bonusNonLineResidualPp": pt2_bonus_nonline_pp,
        "bonusTotalDeltaPp": pt2_bonus_total_pp,
        "totalFullGameDeltaPp": base_delta + pt2_bonus_total_pp,
        "seBonusPp": deltas["PT2_standalone"]["sePp"],
    }
    (OUT / "pt2_decomposition.json").write_text(json.dumps(pt2_full, indent=2), encoding="utf-8")

    wr_fill = wr_fill_from_ops(wr_ops)
    # mass per bonus: sum(rel*fill)/n_bonuses
    n_bonus = len(a)
    mass = sum(o["rel"] * o["fillX"] for o in wr_ops) / n_bonus if n_bonus else 0.0
    wr_fill["fillMassPerBonus"] = mass
    wr_fill["meanOpsPerBonus"] = len(wr_ops) / n_bonus if n_bonus else 0.0
    (OUT / "wr_fill.json").write_text(json.dumps(wr_fill, indent=2), encoding="utf-8")

    # Core RTP without WR = CURRENT + PT2_full + BODY1_standalone + interaction
    # Prefer combo measurement: CURRENT - Phase6? No: CURRENT already includes live PT0+BODY0+Phase6.
    # Adding research overlays:
    core_from_combo = CURRENT_GAME + deltas["PT2_BODY1_combo"]["pp"] + base_delta
    # Wait: PT2_BODY1_combo paired delta is BONUS-only (includes FS/RJ line effects of PT2 and BODY1).
    # BASE line PT2 delta is NOT in bonus sim — must add base_delta separately.
    # But PT2_standalone bonus already includes FS/RJ line deltas of PT2.
    # BODY1 doesn't change BASE.
    # So: projected_without_WR = CURRENT + base_delta + PT2_BODY1_combo.pp
    # where combo.pp is vs PT0_BODY0 on bonuses only.
    # CORRECT: CURRENT uses PT0 live. Combo replaces bonus economy with PT2+BODY1.
    # BASE lines on paid non-bonus and on trigger base still use paytable — scatter trigger BASE
    # also uses PT2 for its line wins. CURRENT's BASE 71.212 includes lines at PT0.
    # So we must add exact BASE line delta for ALL paid rounds: +base_delta.
    # Bonus component of CURRENT includes FS lines at PT0; combo.pp already nets the bonus change
    # including FS/RJ line uplift and BODY1. Good.
    core_rtp = CURRENT_GAME + base_delta + deltas["PT2_BODY1_combo"]["pp"]

    mix = base_trigger_mix(cfg)
    cond = mix["conditional"]

    def wr_scale_for_pp(wr_pp: float):
        # WR_pp/100 = P_TRIGGER * c * mass  => c = (wr_pp/100) / (P_TRIGGER * mass)
        c = (wr_pp / 100.0) / (P_TRIGGER * mass) if mass else 0.0
        by_tier_p_spin = {t: c * REL[t] for t in TIERS}
        # P(WR|bonus) ≈ 1 - prod over ops (1 - p_spin) ≈ sum p for rare; use exact from ops mean
        # E[1 - prod(1-p)] hard; use E[sum p] for rare approx = c * mean_rel_sum_per_bonus
        mean_rel_sum = sum(o["rel"] for o in wr_ops) / n_bonus if n_bonus else 0.0
        p_bonus_approx = c * mean_rel_sum  # rare-event approx
        # Better: Monte estimate from ops — for each bonus, p = 1 - prod(1 - c*rel)
        # Reconstruct per-bonus ops counts by recounting — approximate with Poisson: 1-exp(-c*rel_sum)
        p_bonus = None
        # Use rare approx for reporting; also compute spin rates
        p_paid = p_bonus_approx * P_TRIGGER
        # Exact EV check: E[WR$ per bonus] = c * mass; WR_pp = P_TRIGGER * c * mass * 100 = wr_pp by construction
        return {
            "targetWrPp": wr_pp,
            "c": c,
            "byTierPSpin": by_tier_p_spin,
            "pPerTriggeredBonusApprox": p_bonus_approx,
            "oneInBonusesApprox": (1.0 / p_bonus_approx) if p_bonus_approx else None,
            "pPaidRoundApprox": p_paid,
            "oneInPaidRoundsApprox": (1.0 / p_paid) if p_paid else None,
            "eFillUsed": wr_fill["eIncrementalFillWeighted"],
            "fillMassPerBonus": mass,
        }

    # Recompute p(bonus) more carefully by grouping ops into bonuses of equal length... 
    # We didn't keep bonus boundaries in wr_ops. Recompute with a second pass light? 
    # For rare WR, sum p ≈ 1-prod is fine. Also compute P(WR|start tier) via intensity * spins.

    def candidate(wr_pp, label):
        scale = wr_scale_for_pp(wr_pp)
        projected = core_rtp + wr_pp
        # Uncertainty: Phase6 SE 0.078, BODY/PT2 paired SE from combo
        se_sim = math.hypot(PHASE6_SE, deltas["PT2_BODY1_combo"]["sePp"])
        point_reserve = 96.50 - projected
        safe_reserve = point_reserve - 1.96 * se_sim
        return {
            "id": label,
            "wrPp": wr_pp,
            "projectedRtp": projected,
            "coreRtpWithoutWr": core_rtp,
            "pointReservePp": point_reserve,
            "safeReservePp": safe_reserve,
            "seCombinedPp": se_sim,
            "wr": scale,
            "inPreferredBand": 96.25 <= projected <= 96.35,
        }

    # Solve CFINAL for ~96.30
    target = 96.30
    wr_needed = target - core_rtp
    cands = {
        "C2": candidate(0.45, "C2"),
        "C3": candidate(0.50, "C3"),
        "C8": candidate(0.55, "C8"),
        "CFINAL_SOLVED": candidate(wr_needed, "CFINAL_SOLVED"),
    }
    # Refine CFINAL preferred center clamp if needed
    cands["CFINAL_SOLVED"]["solveTarget"] = target
    cands["CFINAL_SOLVED"]["wrPpSolved"] = wr_needed

    # Per-start-tier P(WR|bonus starts T): need mean intensity mass by start tier
    # Approximate: p_bonus|start ≈ c * E[sum rel over spins | start]
    # Collect from summaries only — optional second light pass skipped; use overall.

    out = {
        "elapsedSec": elapsed,
        "n": n_bonus,
        "seed": args.seed,
        "validation": validation,
        "pt2Decomposition": pt2_full,
        "pairedDeltas": deltas,
        "summaries": summaries,
        "wrFill": wr_fill,
        "coreRtpWithoutWr": core_rtp,
        "candidates": cands,
        "recommended": "CFINAL_SOLVED" if cands["CFINAL_SOLVED"]["safeReservePp"] >= 0.05 else (
            "C3" if cands["C3"]["safeReservePp"] >= 0.05 else "BLOCKED"
        ),
    }
    (OUT / "certification.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("pt2Decomposition", "pairedDeltas", "wrFill", "coreRtpWithoutWr", "candidates", "recommended")}, indent=2))
    print("WROTE", OUT / "certification.json")


if __name__ == "__main__":
    main()
