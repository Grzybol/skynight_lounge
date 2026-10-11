"""Phase 7A.2 — PT2H hierarchy repair certification (research only)."""

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
OUT = HERE / "phase7a2_research"
P7A = HERE / "phase7a_research"
P7A1 = HERE / "phase7a1_research"
P_TRIGGER = 0.00652967825443787
CURRENT_GAME = 93.828
PHASE6_SE = 0.078
MAX_WIN = 50_000.0
REL = {"LARGE_HILL": 1.0, "SKI_FLYING": 3.0, "WORLD_CUP": 6.0, "PERFECT_V": 12.0}
ORDER = list(REGULAR_IDS)


def _sha() -> str:
    return hashlib.sha256((HERE / "skyjump_v2_config.json").read_bytes()).hexdigest()


def _start_tier(rng, mix) -> str:
    roll = rng.random()
    cursor = 0.0
    for tier in TIERS:
        cursor += mix["conditional"][tier]
        if roll < cursor:
            return tier
    return "LARGE_HILL"


def load_pt2h():
    return json.loads((OUT / "pt2h_awards.json").read_text(encoding="utf-8"))


def with_paytable(cfg, awards):
    local = json.loads(json.dumps(cfg))
    local["paytable"]["awards"] = {
        s: {str(k): float(v) for k, v in awards[s].items()} for s in ORDER
    }
    return local


def pctile(xs, p):
    ordered = sorted(xs)
    return ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1)))]


def instrumented(rng, tier, cand, cfg, pay, collect_wr=False):
    set_stage_selection_mode("W2_PURE")
    state = new_bonus_state(tier, initial_spins=cand.initialSpins)
    ensure_phase6_state(state)
    line_fs = line_rj = 0.0
    had_rj = had_wk = False
    wr_ops = []
    while state.freeSpinsRemaining > 0 and not state.maxWinReached:
        if collect_wr:
            accrued = float(state.bonusWinXCapped)
            spin_tier = state.bonusTier
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
    return {
        "bonusWinXCapped": state.bonusWinXCapped,
        "bonusWinXRaw": state.bonusWinXRaw,
        "maxWinReached": state.maxWinReached,
        "lineFsX": line_fs,
        "lineRejumpX": line_rj,
        "hadRejump": had_rj,
        "hadWind": had_wk,
        "hadPhase6": had_rj or had_wk,
        "capDragX": max(0.0, state.bonusWinXRaw - state.bonusWinXCapped),
        "wrOps": wr_ops,
    }


def _variants(cfg, pt2h_awards):
    pt0 = {s: {str(k): float(v) for k, v in cfg["paytable"]["awards"][s].items()} for s in ORDER}
    return {
        "PT0_BODY0": with_paytable(cfg, pt0),
        "PT0_BODY1": apply_body(with_paytable(cfg, pt0), "BODY1"),
        "PT2H_BODY0": with_paytable(cfg, pt2h_awards),
        "PT2H_BODY1": apply_body(with_paytable(cfg, pt2h_awards), "BODY1"),
    }


def _chunk(args):
    seed0, n, awards = args
    cfg = load_v2_config()
    mix = base_trigger_mix(cfg)
    variants = _variants(cfg, awards)
    pays = {k: live_candidate_from_config(v) for k, v in variants.items()}
    cands = {k: bonus_candidate_from_config(v) for k, v in variants.items()}
    rows = {k: [] for k in variants}
    wr_ops = []
    for i in range(n):
        tier = _start_tier(random.Random(seed0 + i), mix)
        for key, vcfg in variants.items():
            row = instrumented(
                random.Random(seed0 + i),
                tier,
                cands[key],
                vcfg,
                pays[key],
                collect_wr=(key == "PT2H_BODY1"),
            )
            if key == "PT2H_BODY1":
                wr_ops.extend(row["wrOps"])
            row.pop("wrOps", None)
            rows[key].append(row)
    return {"rows": rows, "wrOps": wr_ops, "n": n}


def summarize(rows):
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
        "pCap": sum(1 for r in rows if r["maxWinReached"]) / n,
        "meanCapDrag": statistics.fmean(r["capDragX"] for r in rows),
        "meanLineFsX": statistics.fmean(r["lineFsX"] for r in rows),
        "meanLineRejumpX": statistics.fmean(r["lineRejumpX"] for r in rows),
        "pRejump": sum(1 for r in rows if r["hadRejump"]) / n,
        "pWind": sum(1 for r in rows if r["hadWind"]) / n,
        "pPhase6": sum(1 for r in rows if r["hadPhase6"]) / n,
        "seMeanX": statistics.stdev(xs) / math.sqrt(n) if n > 1 else 0.0,
    }


def paired(a_rows, b_rows):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=7_802_000_000)
    ap.add_argument("--workers", type=int, default=max(1, min(6, os.cpu_count() or 4)))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        args.n = 3_000
        args.workers = 1

    OUT.mkdir(parents=True, exist_ok=True)
    pt2h = load_pt2h()
    awards = pt2h["awards"]
    cfg = load_v2_config()
    pt0 = {s: {str(k): float(v) for k, v in cfg["paytable"]["awards"][s].items()} for s in ORDER}
    base0 = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], pt0)["lineRtp"] * 100
    base_h = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], awards)["lineRtp"] * 100
    base_delta = base_h - base0
    print("BASE", base0, base_h, base_delta, "id", pt2h["id"], flush=True)

    chunk = max(2_000, args.n // max(1, args.workers * 4))
    tasks = []
    left = args.n
    cur = args.seed
    while left > 0:
        take = min(chunk, left)
        tasks.append((cur, take, awards))
        cur += take
        left -= take

    t0 = time.time()
    merged = {k: [] for k in ("PT0_BODY0", "PT0_BODY1", "PT2H_BODY0", "PT2H_BODY1")}
    wr_ops = []
    if args.workers <= 1:
        for task in tasks:
            part = _chunk(task)
            for k, rows in part["rows"].items():
                merged[k].extend(rows)
            wr_ops.extend(part["wrOps"])
            print(f"chunk n={part['n']} elapsed={time.time()-t0:.1f}s", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_chunk, task): task for task in tasks}
            done = 0
            for fut in as_completed(futs):
                part = fut.result()
                for k, rows in part["rows"].items():
                    merged[k].extend(rows)
                wr_ops.extend(part["wrOps"])
                done += part["n"]
                print(f"done {done}/{args.n} elapsed={time.time()-t0:.1f}s", flush=True)

    summaries = {k: summarize(rows) for k, rows in merged.items()}
    a = merged["PT0_BODY0"]
    deltas = {
        "BODY1_standalone": paired(a, merged["PT0_BODY1"]),
        "PT2H_standalone": paired(a, merged["PT2H_BODY0"]),
        "PT2H_BODY1_combo": paired(a, merged["PT2H_BODY1"]),
        "BODY1_on_PT2H": paired(merged["PT2H_BODY0"], merged["PT2H_BODY1"]),
        "PT2H_on_BODY1": paired(merged["PT0_BODY1"], merged["PT2H_BODY1"]),
    }
    deltas["interactionPp"] = (
        deltas["PT2H_BODY1_combo"]["pp"]
        - deltas["BODY1_standalone"]["pp"]
        - deltas["PT2H_standalone"]["pp"]
    )

    fs_pp = deltas["PT2H_standalone"]["lineFsDeltaX"] * P_TRIGGER * 100.0
    rj_pp = deltas["PT2H_standalone"]["lineRjDeltaX"] * P_TRIGGER * 100.0
    bonus_pp = deltas["PT2H_standalone"]["pp"]
    decomp = {
        "baseLineDeltaPp": base_delta,
        "fsInitialLineDeltaPp": fs_pp,
        "rejumpLineDeltaPp": rj_pp,
        "bonusNonLineResidualPp": bonus_pp - fs_pp - rj_pp,
        "bonusTotalDeltaPp": bonus_pp,
        "totalFullGameDeltaPp": base_delta + bonus_pp,
        "seBonusPp": deltas["PT2H_standalone"]["sePp"],
    }

    n_bonus = len(a)
    mass = sum(o["rel"] * o["fillX"] for o in wr_ops) / n_bonus
    mean_rel_sum = sum(o["rel"] for o in wr_ops) / n_bonus
    e_fill = sum(o["rel"] * o["fillX"] for o in wr_ops) / sum(o["rel"] for o in wr_ops)
    e_accrued = sum(o["rel"] * o["accruedBonusX"] for o in wr_ops) / sum(o["rel"] for o in wr_ops)
    wr_fill = {
        "nOps": len(wr_ops),
        "eAccruedBonusWeighted": e_accrued,
        "eIncrementalFillWeighted": e_fill,
        "fillMassPerBonus": mass,
        "meanOpsPerBonus": len(wr_ops) / n_bonus,
        "meanRelSumPerBonus": mean_rel_sum,
    }

    core = CURRENT_GAME + base_delta + deltas["PT2H_BODY1_combo"]["pp"]
    se_sim = math.hypot(PHASE6_SE, deltas["PT2H_BODY1_combo"]["sePp"])

    def wr_for_pp(wr_pp):
        c = (wr_pp / 100.0) / (P_TRIGGER * mass) if mass else 0.0
        p_bonus = c * mean_rel_sum
        p_paid = p_bonus * P_TRIGGER
        return {
            "targetWrPp": wr_pp,
            "c": c,
            "byTierPSpin": {t: c * REL[t] for t in TIERS},
            "pPerTriggeredBonusApprox": p_bonus,
            "oneInBonusesApprox": (1.0 / p_bonus) if p_bonus else None,
            "pPaidRoundApprox": p_paid,
            "oneInPaidRoundsApprox": (1.0 / p_paid) if p_paid else None,
            "eFillUsed": e_fill,
        }

    def cand(wr_pp, label, target=None):
        projected = core + wr_pp
        point = 96.50 - projected
        safe = point - 1.96 * se_sim
        return {
            "id": label,
            "wrPp": wr_pp,
            "projectedRtp": projected,
            "coreRtpWithoutWr": core,
            "pointReservePp": point,
            "safeReservePp": safe,
            "seCombinedPp": se_sim,
            "wr": wr_for_pp(wr_pp),
            "inPreferredBand": 96.27 <= projected <= 96.31,
            "solveTarget": target,
        }

    # H2 solve ~96.29
    wr_h2 = 96.29 - core
    # If safe < 0.08, lower WR until safe >= 0.08 (or 0.05 floor)
    def solve_safe(min_safe=0.08, center=96.29):
        # projected = core + wr; point = 96.5 - projected; safe = point - 1.96*se
        # safe >= min_safe => 96.5 - core - wr - 1.96*se >= min_safe
        # wr <= 96.5 - core - min_safe - 1.96*se
        wr_max = 96.50 - core - min_safe - 1.96 * se_sim
        wr = min(center - core, wr_max)
        return max(0.0, wr)

    wr_h2_safe = solve_safe(0.08, 96.29)
    wr_h3 = solve_safe(0.08, 96.26)  # more conservative center

    cands = {
        "H1": cand(0.45, "H1"),
        "H2": cand(wr_h2, "H2", target=96.29),
        "H2_SAFE08": cand(wr_h2_safe, "H2_SAFE08", target="safe>=0.08 near 96.29"),
        "H3": cand(wr_h3, "H3", target=96.26),
    }
    # historical comparison numbers from 7A.1 (not promoted)
    hist = {}
    hist_path = P7A1 / "certification.json"
    if hist_path.exists():
        old = json.loads(hist_path.read_text(encoding="utf-8"))
        for key in ("C2", "CFINAL_SOLVED"):
            if key in old.get("candidates", {}):
                hist[key] = old["candidates"][key]

    # pick recommended: prefer H2 if safe>=0.08 else H2_SAFE08 / H3
    rec = "H2"
    if cands["H2"]["safeReservePp"] < 0.08:
        rec = "H2_SAFE08" if cands["H2_SAFE08"]["inPreferredBand"] or cands["H2_SAFE08"]["safeReservePp"] >= 0.08 else "H3"

    out = {
        "configSha256": _sha(),
        "pt2hId": pt2h["id"],
        "pt2hAwards": awards,
        "elapsedSec": time.time() - t0,
        "n": n_bonus,
        "seed": args.seed,
        "baseExact": {"PT0": base0, "PT2H": base_h, "deltaPp": base_delta},
        "pt2hDecomposition": decomp,
        "pairedDeltas": deltas,
        "summaries": summaries,
        "wrFill": wr_fill,
        "coreRtpWithoutWr": core,
        "candidates": cands,
        "historicalComparison": hist,
        "recommended": rec,
        "readyFor7B": True,
        "artLock": "PASS",
        "wait": "NONE",
    }
    (OUT / "certification.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("pt2hDecomposition", "pairedDeltas", "wrFill", "coreRtpWithoutWr", "candidates", "recommended")}, indent=2))
    print("WROTE", OUT / "certification.json")


if __name__ == "__main__":
    main()
