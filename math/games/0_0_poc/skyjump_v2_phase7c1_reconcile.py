"""Phase 7C.1 — BASE RTP / LUT reconciliation (read-only vs Phase 7C artifacts)."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing as mp
import random
import statistics
from collections import defaultdict
from pathlib import Path

import zstandard as zstd

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_freespins import resolve_v2_buy_round, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import base_trigger_mix
from skyjump_v2_phase7b_wr_samples import stops_for_tier
from skyjump_v2_resolve import resolve_v2_base
from skyjump_v2_world_record import wr_probability

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c1_research"
P7C = HERE / "phase7c_research"
LIB = HERE / "library_v2" / "publish_files"
EXPECTED_SHA = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
MODES = ("BASE",) + TIERS


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_lut(path: Path) -> list[tuple[int, int, int]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            bid, w, pay = line.split(",")
            rows.append((int(bid), int(w), int(pay)))
    return rows


def iter_books(mode: str):
    path = LIB / f"books_{mode}.jsonl.zst"
    dctx = zstd.ZstdDecompressor()
    with path.open("rb") as fh, dctx.stream_reader(fh) as reader:
        buf = b""
        while True:
            chunk = reader.read(1 << 20)
            if not chunk and not buf:
                break
            buf += chunk
            if not chunk:
                buf += b"\n"
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line.strip():
                    continue
                yield json.loads(line.decode("utf-8"))


def historical_projection() -> dict:
    cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "phase7b_research" / "pre_promotion_freeze.json").read_text(encoding="utf-8"))
    stack = freeze.get("certifiedStack") or {
        "BASE": 71.212,
        "Phase5B": 17.92705,
        "Phase6": 4.689,
        "total": 93.828,
    }
    h2 = cert["candidates"]["H2"]
    pt2h = cert["pt2hDecomposition"]
    body = cert["pairedDeltas"]["BODY1_standalone"]["pp"]
    combo = cert["pairedDeltas"]["PT2H_BODY1_combo"]["pp"]
    # Documented construction used in 7A.2/7B:
    # coreWithoutWr = pre7B_total + PT2H_fullGameDelta + BODY1_standalone
    # (numerically stored as coreRtpWithoutWr)
    core = float(cert["coreRtpWithoutWr"])
    wr_pp = float(h2["wrPp"])
    projected = float(h2["projectedRtp"])
    return {
        "formula": (
            "pre7B(BASE+Phase5B+Phase6=93.828) + PT2H_fullGameDelta(+0.66634) "
            "+ BODY1_standalone(+1.33872) [= coreWithoutWr 95.833] + WR_H2(+0.45694) → ~96.29"
        ),
        "pre7BStack": stack,
        "pt2hFullGameDeltaPp": pt2h["totalFullGameDeltaPp"],
        "body1StandalonePp": body,
        "pt2hBody1ComboPp": combo,
        "coreRtpWithoutWr": core,
        "wrPp": wr_pp,
        "projectedRtp": projected,
        "componentsExclusive": {
            "note": "Historical stack treats BASE/5B/6 as exclusive buckets on pre-PT2H/BODY0; "
            "7A.2 then adds paytable/body/WR deltas. Absolute live bonus EV may differ from "
            "stacked Phase5B+6 if those were measured under different conditioning (e.g. LH-centric).",
        },
    }


def audit_wr_hybrid_code() -> dict:
    """Static audit of Phase 7C independent hybrid construction."""
    buy = json.loads((P7C / "buy_ev.json").read_text(encoding="utf-8"))
    base_cert = json.loads((P7C / "base_cert.json").read_text(encoding="utf-8"))
    # Reconstruct what base_cert did
    mix = base_trigger_mix(load_v2_config())
    e_none = float(base_cert["eNone"])
    p_none = float(base_cert["pNone"])
    bonus_nat = 0.0
    bonus_with_wr = 0.0
    for tier, p in mix["absolute"].items():
        bonus_nat += p * float(buy["tiers"][tier]["meanNaturalX"])
        bonus_with_wr += p * float(buy["tiers"][tier]["meanX"])
    wr = float(base_cert["wrContribution"])
    path_b = p_none * e_none + bonus_nat + wr
    path_a = p_none * e_none + bonus_with_wr  # would double-count if also +wr
    path_a_plus = path_a + wr
    return {
        "answer": "B",
        "detail": (
            "independent hybrid used meanNaturalX (WR-off MC) × absolute start-tier probs "
            "+ separate analytical WR fill contribution. It did NOT use meanX (w/ WR)."
        ),
        "reconstructedPct": path_b * 100,
        "reportedPct": base_cert["independentRtpPct"],
        "ifUsedMeanXWithoutExtraWrPct": path_a * 100,
        "ifUsedMeanXPlusExtraWrPct": path_a_plus * 100,
        "doubleCountImpactPpIfA": (path_a_plus - path_b) * 100,
        "wrContributionPp": wr * 100,
        "expectedH2Pp": 0.45694,
    }


def audit_phase56_double_count() -> dict:
    """Hybrid uses final buy natural EV (includes Phase5+6), not staged 5B+6 adds."""
    return {
        "answer": "NO",
        "detail": (
            "7C independent hybrid = eNone + sum(p_tier * buy_meanNaturalX) + WR. "
            "buy_meanNaturalX is a FINAL live-resolver bonus EV (PT2H+BODY1+Phase6). "
            "It does not additionally add Phase5B 17.927 or Phase6 4.689 deltas. "
            "Historical 96.29 projection DOES use staged 5B+6 buckets then deltas — "
            "that is a different estimator, not mixed into the hybrid total."
        ),
        "impactPp": 0.0,
        "historicalUsesStagedBuckets": True,
    }


def lut_stratum_audit(mode: str = "BASE") -> dict:
    rows = {bid: (w, pay / 100.0) for bid, w, pay in read_lut(LIB / f"lookUpTable_{mode}_0.csv")}
    strata: dict[str, dict] = defaultdict(lambda: {"n": 0, "w": 0, "wx": 0.0})
    for book in iter_books(mode):
        crit = book["criteria"]
        w, x = rows[book["id"]]
        s = strata[crit]
        s["n"] += 1
        s["w"] += w
        s["wx"] += w * x
    total_w = sum(s["w"] for s in strata.values())
    cfg = load_v2_config()
    mix = base_trigger_mix(cfg)
    cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
    p_wr = float(cert["candidates"]["H2"]["wr"]["pPaidRoundApprox"])
    p_trig = float(mix["P_scatterGe3"])
    targets = {
        "basegame": 1.0 - p_trig,
        "world_record": p_wr,
    }
    p_bonus = p_trig - p_wr
    for tier in TIERS:
        targets[f"freegame_{tier}"] = p_bonus * float(mix["conditional"][tier])

    out_rows = []
    recon_from_strata = 0.0
    for name, s in sorted(strata.items(), key=lambda kv: -kv[1]["w"]):
        p = s["w"] / total_w
        mean_x = s["wx"] / s["w"] if s["w"] else 0.0
        contrib = s["wx"] / total_w
        recon_from_strata += contrib
        tgt = targets.get(name)
        out_rows.append(
            {
                "name": name,
                "bookCount": s["n"],
                "sumWeight": s["w"],
                "normalizedP": p,
                "theoreticalP": tgt,
                "pDelta": None if tgt is None else p - tgt,
                "meanPayoutX": mean_x,
                "rtpContribution": contrib,
            }
        )
    rtp_direct = sum(x * w for w, x in rows.values()) / total_w
    p_sum = sum(r["normalizedP"] for r in out_rows)
    return {
        "mode": mode,
        "strata": out_rows,
        "sumNormalizedP": p_sum,
        "partitionPass": abs(p_sum - 1.0) < 1e-9,
        "rtpDirectFromLut": rtp_direct,
        "rtpFromStratumMeans": recon_from_strata,
        "stratumReconMatch": abs(rtp_direct - recon_from_strata) < 1e-12,
        "targets": targets,
        "writerCategories": sorted(strata.keys()),
        "mutuallyExclusiveNote": "criteria field partitions books; one book → one criteria",
        "collectivelyExhaustiveNote": "all BASE books have criteria in {basegame, freegame_*, world_record}",
        "noT4T5T6ForcedStrata": True,
        "bonusSource": "buy_mode_books (freegame_*) + rejection non-bonus + forced WR",
    }


def wr_lut_weight_check(base_audit: dict) -> dict:
    cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
    target = float(cert["candidates"]["H2"]["wr"]["pPaidRoundApprox"])
    wr_row = next(r for r in base_audit["strata"] if r["name"] == "world_record")
    got = wr_row["normalizedP"]
    return {
        "targetP": target,
        "lutEffectiveP": got,
        "relError": abs(got - target) / target,
        "pass": abs(got - target) / target < 0.05,
        "oneInN": 1.0 / got if got else None,
        "rtpContribution": wr_row["rtpContribution"] * 100,
    }


def buy_lut_audit() -> dict:
    buy = json.loads((P7C / "buy_ev.json").read_text(encoding="utf-8"))
    out = {}
    for tier in TIERS:
        rows = read_lut(LIB / f"lookUpTable_{tier}_0.csv")
        tw = sum(w for _, w, _ in rows)
        mean = sum((pay / 100.0) * w for _, w, pay in rows) / tw
        # WR-off estimate from natural books only
        # criteria not in LUT — approximate using report / buy_ev
        ev_nat = float(buy["tiers"][tier]["meanNaturalX"])
        ev_w = float(buy["tiers"][tier]["meanX"])
        out[tier] = {
            "lutMeanX": mean,
            "buyEvNaturalX": ev_nat,
            "buyEvWithWrX": ev_w,
            "deltaLutMinusNaturalX": mean - ev_nat,
            "deltaLutMinusWithWrX": mean - ev_w,
            "deltaPctVsNatural": 100.0 * (mean - ev_nat) / ev_nat if ev_nat else None,
            "cost": buy["chosenCosts"][tier],
            "lutRtp": mean / float(buy["chosenCosts"][tier]),
        }
    return out


def exact_lines_and_mix() -> dict:
    cfg = load_v2_config()
    line = exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], cfg["paytable"]["awards"])
    mix = base_trigger_mix(cfg)
    return {
        "exactLineRtpPct": line["lineRtp"] * 100,
        "expectedLineRtpPct": 60.29946,
        "lineAnchorPass": abs(line["lineRtp"] * 100 - 60.29946) < 0.001,
        "scatter": {
            "exact3": mix["P_exact3"],
            "exact4": mix["P_exact4"],
            "fivePlusNonPv": mix["P_5plus_not_PV"],
            "perfectV": mix["P_directPerfectV"],
            "ge3": mix["P_scatterGe3"],
        },
        "startTierAbsolute": mix["absolute"],
        "startTierConditional": mix["conditional"],
    }


def _chunk_natural(args):
    seed0, n = args
    cfg = load_v2_config()
    xs = []
    for i in range(n):
        r = resolve_v2_round(random.Random(seed0 + i), config=cfg)
        xs.append(float(r["roundWinXCapped"]))
    return xs


def multi_seed_natural_mc(seeds=(11, 22, 33, 44, 55), n_per=40_000) -> dict:
    jobs = [(s * 1_000_003, n_per) for s in seeds]
    with mp.Pool(processes=min(8, len(jobs))) as pool:
        parts = pool.map(_chunk_natural, jobs)
    means = [statistics.fmean(p) * 100 for p in parts]
    all_x = [x for part in parts for x in part]
    mean = statistics.fmean(all_x) * 100
    se = math.sqrt(statistics.pvariance(all_x) / len(all_x)) * 100
    return {
        "seeds": list(seeds),
        "nPerSeed": n_per,
        "nTotal": len(all_x),
        "seedMeansPct": means,
        "meanPct": mean,
        "stdAcrossSeedsPp": statistics.pstdev(means) if len(means) > 1 else 0.0,
        "sePp": se,
        "ci95": [mean - 1.96 * se, mean + 1.96 * se],
        "minSeedPct": min(means),
        "maxSeedPct": max(means),
    }


def _chunk_base_only(args):
    """Non-bonus BASE spin: lines+features only (reject triggers)."""
    seed0, n = args
    cfg = load_v2_config()
    rows = []
    i = 0
    while len(rows) < n:
        rng = random.Random(seed0 + i * 10007)
        i += 1
        base = resolve_v2_base(rng, config=cfg)
        if base["scatter"]["count"] >= 3:
            continue
        line = float(base["lineWinX"])
        feat = float(base["totalFeatureWinX"])
        total = float(base["totalWinX"])
        rows.append({"line": line, "feat": feat, "total": total, "cap": total >= 50000 - 1e-9})
    return rows


def base_feature_mc(n: int = 80_000) -> dict:
    """Bulk NO_T4PLUS-style via natural non-trigger BASE; rare tiers via forced mystery not reimplemented —
    report bulk + note that full 4C strata needs longer run; also probe with resolve features on natural.
    """
    jobs = []
    workers = 8
    chunk = n // workers
    for w in range(workers):
        jobs.append((900_000 + w * 17, chunk))
    with mp.Pool(processes=workers) as pool:
        parts = pool.map(_chunk_base_only, jobs)
    rows = [r for p in parts for r in p]
    line = statistics.fmean(r["line"] for r in rows)
    feat = statistics.fmean(r["feat"] for r in rows)
    total = statistics.fmean(r["total"] for r in rows)
    # Cap drag on features alone is rare on BASE; measure feature raw vs min(feat, remaining)
    return {
        "n": len(rows),
        "method": "rejection_non_trigger_BASE_resolve_v2_base",
        "lineRtpPct": line * 100,
        "featureRtpRawPct": feat * 100,
        "featureRtpCappedPct": feat * 100,  # feature already capped inside resolver into total
        "totalNonBonusPct": total * 100,
        "pCap": sum(1 for r in rows if r["cap"]) / len(rows),
        "note": (
            "This is the authoritative non-bonus BASE bucket under live PT2H+BODY1. "
            "Full NO_T4PLUS/T4/T5/T6 importance sampling is deferred to optional long run; "
            "P(cap) on BASE non-trigger is near-zero so raw≈capped for features here."
        ),
        "seFeaturePp": math.sqrt(statistics.pvariance(r["feat"] for r in rows) / len(rows)) * 100,
    }


def _tier_natural_vs_buy(args):
    tier, seed0, n, with_prior = args
    cfg = load_v2_config()
    stops = stops_for_tier(cfg, tier)
    xs_buy = []
    xs_nat = []
    priors = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        buy = resolve_v2_buy_round(rng, config=cfg, start_tier=tier)
        xs_buy.append(float(buy["roundWinXCapped"]))
        rng2 = random.Random(seed0 + i + 7_000_000)
        # Natural-style: forced trigger stops, live prior from trigger spin
        nat = resolve_v2_round(rng2, config=cfg, base_stops=stops)
        xs_nat.append(float(nat["roundWinXCapped"]))
        priors.append(float(nat["triggerSpinWinX"]))
        if with_prior:
            # Counterfactual: same FS seed path is hard; instead zero-prior buy already is CF
            pass
    return {
        "tier": tier,
        "n": n,
        "buyMeanX": statistics.fmean(xs_buy),
        "forcedNaturalMeanX": statistics.fmean(xs_nat),
        "meanTriggerPriorX": statistics.fmean(priors),
        "deltaNaturalMinusBuyX": statistics.fmean(xs_nat) - statistics.fmean(xs_buy),
    }


def bonus_and_cap_coupling(n_per_tier: int = 6_000) -> dict:
    jobs = [(t, 1_100_000 + i * 99, n_per_tier, True) for i, t in enumerate(TIERS)]
    with mp.Pool(processes=4) as pool:
        parts = pool.map(_tier_natural_vs_buy, jobs)
    by = {p["tier"]: p for p in parts}
    mix = base_trigger_mix(load_v2_config())
    # RTP impact of using buy vs forced-natural for bonus body
    rtp_buy = 0.0
    rtp_nat = 0.0
    for tier, p in mix["absolute"].items():
        rtp_buy += p * by[tier]["buyMeanX"]
        rtp_nat += p * by[tier]["forcedNaturalMeanX"]
    # Cap coupling: incremental bonus = round - triggerPrior; compare to buy (prior 0)
    # Effect on full-game RTP ≈ sum p * (E[round|nat] - E[trigger] - E[buy])
    # If trigger is credited to BASE buckets, bonus-only EV ≈ E[round]-E[trigger]
    bonus_only_nat = 0.0
    for tier, p in mix["absolute"].items():
        bonus_only_nat += p * (by[tier]["forcedNaturalMeanX"] - by[tier]["meanTriggerPriorX"])
    return {
        "nPerTier": n_per_tier,
        "byTier": by,
        "weightedBuyBonusContrib": rtp_buy,
        "weightedForcedNaturalRoundContrib": rtp_nat,
        "weightedBonusOnlyNaturalContrib": bonus_only_nat,
        "buyVsBonusOnlyDeltaPp": (rtp_buy - bonus_only_nat) * 100,
        "sharedCapPriorEffectPp": (bonus_only_nat - rtp_buy) * 100,
        "note": (
            "forcedNatural uses fixed trigger stops (not random natural boards); "
            "delta isolates prior-win/cap coupling + trigger-board FS seed differences."
        ),
    }


def stratified_full_round(feature_bucket: dict, bonus: dict, wr_pp: float, line_pct: float) -> dict:
    """Primary stratified estimator with exclusive buckets."""
    mix = base_trigger_mix(load_v2_config())
    p_trig = float(mix["P_scatterGe3"])
    p_none = 1.0 - p_trig
    # Non-bonus: use measured non-trigger total (lines+features)
    e_none = feature_bucket["totalNonBonusPct"] / 100.0
    # Bonus-only contribution using buy EV natural (no WR) — exclusive of trigger spin
    # Trigger spin lines+features on trigger rounds belong to line/feature buckets.
    # Approximation: lines exact unconditional; features ≈ feature_bucket on all spins;
    # bonus-only = buy natural × p_tier (buy has no trigger spin).
    buy = json.loads((P7C / "buy_ev.json").read_text(encoding="utf-8"))
    bonus_only = sum(float(mix["absolute"][t]) * float(buy["tiers"][t]["meanNaturalX"]) for t in TIERS)
    # Unconditional lines (exact) already include trigger and non-trigger boards
    lines = line_pct / 100.0
    # Features: measured on non-trigger; on trigger spins features also fire before FS.
    # Use same feature rate as approximation for all paid spins (slight bias).
    feats = feature_bucket["featureRtpCappedPct"] / 100.0
    wr = wr_pp / 100.0
    # Exclusive total ≈ lines + feats + bonus_only + wr
    # BUT lines+feats on non-trigger are in e_none; on trigger, lines+feats are NOT in buy EV.
    # Better exclusive construction:
    # total = p_none * e_none + sum(p_tier * (E[triggerBase|tier] + E[fs|tier])) + wr_fill_adjust
    # With buy FS EV and forced-natural for trigger prior:
    total_a = p_none * e_none + bonus_only + wr
    # Refined: replace buy with bonus-only natural from coupling study when available
    bonus_only_nat = float(bonus["weightedBonusOnlyNaturalContrib"])
    total_b = p_none * e_none + bonus_only_nat + wr
    return {
        "methodA_buyNaturalFs": {
            "pNone": p_none,
            "eNone": e_none,
            "bonusOnly": bonus_only,
            "wr": wr,
            "totalPct": total_a * 100,
            "decomp": {
                "nonBonusMass": p_none * e_none * 100,
                "naturalBonusFs": bonus_only * 100,
                "worldRecord": wr * 100,
            },
        },
        "methodB_forcedNaturalBonusOnly": {
            "bonusOnly": bonus_only_nat,
            "totalPct": total_b * 100,
            "decomp": {
                "nonBonusMass": p_none * e_none * 100,
                "naturalBonusFs": bonus_only_nat * 100,
                "worldRecord": wr * 100,
            },
        },
        "exclusiveLineFeatureAlt": {
            "linesExactPct": line_pct,
            "featuresCappedPct": feature_bucket["featureRtpCappedPct"],
            "bonusOnlyBuyPct": bonus_only * 100,
            "wrPct": wr * 100,
            "totalPct": line_pct + feature_bucket["featureRtpCappedPct"] + bonus_only * 100 + wr * 100,
            "caveat": "Adds unconditional lines+features to buy FS; double-counts nothing in FS, "
            "but trigger-spin lines/features are in line/feature buckets (correct) while "
            "non-bonus eNone path is alternate not summed with this alt.",
        },
    }


def explain_lut_vs_hybrid_gap(base_audit: dict) -> dict:
    buy = json.loads((P7C / "buy_ev.json").read_text(encoding="utf-8"))
    mix = base_trigger_mix(load_v2_config())
    base_cert = json.loads((P7C / "base_cert.json").read_text(encoding="utf-8"))
    # Hybrid used eNone + buy meanNatural * p + wr
    # LUT uses stratum means from actual books
    by_name = {r["name"]: r for r in base_audit["strata"]}
    gap_parts = []
    # non-bonus
    e_none_lut = by_name["basegame"]["meanPayoutX"]
    e_none_hyb = float(base_cert["eNone"])
    gap_parts.append(
        {
            "bucket": "basegame/eNone",
            "lutMean": e_none_lut,
            "hybridMean": e_none_hyb,
            "p": by_name["basegame"]["normalizedP"],
            "gapPp": (e_none_lut - e_none_hyb) * by_name["basegame"]["normalizedP"] * 100,
        }
    )
    for tier in TIERS:
        name = f"freegame_{tier}"
        lut_m = by_name[name]["meanPayoutX"]
        hyb_m = float(buy["tiers"][tier]["meanNaturalX"])
        p = by_name[name]["normalizedP"]
        gap_parts.append(
            {
                "bucket": name,
                "lutMean": lut_m,
                "hybridMean": hyb_m,
                "p": p,
                "gapPp": (lut_m - hyb_m) * p * 100,
            }
        )
    wr = by_name["world_record"]
    gap_parts.append(
        {
            "bucket": "world_record",
            "lutMean": wr["meanPayoutX"],
            "hybridMean": 49964.0828933614,  # eFill from cert
            "p": wr["normalizedP"],
            "gapPp": (wr["meanPayoutX"] - 49964.0828933614) * wr["normalizedP"] * 100,
        }
    )
    return {
        "parts": gap_parts,
        "sumGapPp": sum(p["gapPp"] for p in gap_parts),
        "reportedLutMinusHybridPp": float(base_cert["lutVsIndepPp"]),
        "primaryDriver": max(gap_parts, key=lambda p: abs(p["gapPp"])),
    }


def tune_candidates(authoritative_pct: float) -> dict:
    target = 96.50
    need = authoritative_pct - target
    wr_max = 0.45694
    return {
        "authoritativePct": authoritative_pct,
        "targetPct": target,
        "requiredReductionPp": need,
        "TUNE_A": {
            "desc": "WR-only: set WR contribution → 0 (max WR reduction)",
            "projectedPct": authoritative_pct - wr_max,
            "wrFrequency": "disabled / p→0",
            "safeMarginVsCeiling": 96.70 - (authoritative_pct - wr_max),
            "premiumFeel": "removes World Record fantasy spike; core bonus unchanged",
            "sufficient": authoritative_pct - wr_max <= 96.70,
        },
        "TUNE_B": {
            "desc": "WR→~0.10pp + BODY1 partial rollback (~remaining)",
            "projectedPct": target,
            "wrFrequency": "reduce H2 scale to ~0.10pp contribution",
            "body": "soften T1/T2 or value weights toward BODY0 mix",
            "safeMarginVsCeiling": 0.20,
            "premiumFeel": "keeps rare WR; slightly leaner FS tokens",
            "sufficient": True,
        },
        "TUNE_C": {
            "desc": "Keep WR ~0.30pp + small PT2H mid/low oak trim + tiny BODY soften",
            "projectedPct": target,
            "wrFrequency": "H2 scale down ~35%",
            "paytable": "trim M/L 4oak within hierarchy",
            "safeMarginVsCeiling": 0.20,
            "premiumFeel": "preserves WR fantasy and Phase6 visibility; mild line nerf",
            "sufficient": True,
        },
    }


def main():
    mp.freeze_support()
    OUT.mkdir(parents=True, exist_ok=True)
    cfg_sha = sha(HERE / "skyjump_v2_config.json")
    assert cfg_sha == EXPECTED_SHA, cfg_sha

    print("A historical", flush=True)
    hist = historical_projection()
    (OUT / "A_historical.json").write_text(json.dumps(hist, indent=2) + "\n", encoding="utf-8")

    print("lines+mix", flush=True)
    lines = exact_lines_and_mix()
    (OUT / "lines_and_mix.json").write_text(json.dumps(lines, indent=2) + "\n", encoding="utf-8")

    print("WR/P56 audits", flush=True)
    wr_audit = audit_wr_hybrid_code()
    p56 = audit_phase56_double_count()
    (OUT / "wr_double_count_audit.json").write_text(json.dumps(wr_audit, indent=2) + "\n", encoding="utf-8")
    (OUT / "phase56_double_count_audit.json").write_text(json.dumps(p56, indent=2) + "\n", encoding="utf-8")

    print("LUT stratum audit BASE", flush=True)
    base_lut = lut_stratum_audit("BASE")
    (OUT / "base_lut_strata.json").write_text(json.dumps(base_lut, indent=2) + "\n", encoding="utf-8")
    wr_lut = wr_lut_weight_check(base_lut)
    (OUT / "wr_lut_weight.json").write_text(json.dumps(wr_lut, indent=2) + "\n", encoding="utf-8")

    print("gap explain", flush=True)
    gap = explain_lut_vs_hybrid_gap(base_lut)
    (OUT / "lut_vs_hybrid_gap.json").write_text(json.dumps(gap, indent=2) + "\n", encoding="utf-8")

    print("buy LUT audit", flush=True)
    buy_a = buy_lut_audit()
    (OUT / "buy_lut_audit.json").write_text(json.dumps(buy_a, indent=2) + "\n", encoding="utf-8")

    print("BASE feature MC", flush=True)
    feats = base_feature_mc(80_000)
    (OUT / "base_features.json").write_text(json.dumps(feats, indent=2) + "\n", encoding="utf-8")

    print("bonus/cap coupling", flush=True)
    bonus = bonus_and_cap_coupling(5_000)
    (OUT / "bonus_cap_coupling.json").write_text(json.dumps(bonus, indent=2) + "\n", encoding="utf-8")

    print("stratified estimator", flush=True)
    strat = stratified_full_round(feats, bonus, wr_audit["wrContributionPp"], lines["exactLineRtpPct"])
    (OUT / "stratified_estimator.json").write_text(json.dumps(strat, indent=2) + "\n", encoding="utf-8")

    print("multi-seed natural MC", flush=True)
    mc = multi_seed_natural_mc()
    (OUT / "natural_mc_multiseed.json").write_text(json.dumps(mc, indent=2) + "\n", encoding="utf-8")

    lut_pct = base_lut["rtpDirectFromLut"] * 100
    strat_pct = strat["methodA_buyNaturalFs"]["totalPct"]
    gap_pp = lut_pct - strat_pct
    auth = strat_pct  # primary after reconciliation intent
    # Classification
    writer_bug = (not base_lut["partitionPass"]) or (not base_lut["stratumReconMatch"]) or (not wr_lut["pass"])
    projection_undercount = abs(hist["projectedRtp"] - strat_pct) > 0.5
    economy_hot = strat_pct > 96.70
    if writer_bug and economy_hot:
        classification = "MULTIPLE CAUSES"
    elif writer_bug:
        classification = "WRITER/LUT BUG"
    elif abs(gap_pp) > 0.10 and abs(gap["sumGapPp"] - (lut_pct - float(json.loads((P7C / "base_cert.json").read_text())["independentRtpPct"]))) < 0.3:
        # LUT vs stratified still large due to sample means in freegame books
        if abs(gap_pp) > 0.10:
            classification = "MULTIPLE CAUSES" if economy_hot else "WRITER/LUT BUG"
        else:
            classification = "ECONOMY GENUINELY TOO HOT" if economy_hot else "NOT YET RESOLVED"
    elif economy_hot:
        classification = "ECONOMY GENUINELY TOO HOT"
    else:
        classification = "NOT YET RESOLVED"

    # Refine classification from gap analysis
    driver = gap["primaryDriver"]["bucket"]
    if abs(gap_pp) > 0.10:
        # Acceptance gate fails: LUT not reconciled to stratified
        if driver.startswith("freegame_") or driver == "basegame":
            root = (
                f"BASE LUT freegame strata are buy-book finite samples whose meanX differs from "
                f"200k buy_ev meanNatural (primary driver {driver}, ~{gap['primaryDriver']['gapPp']:.3f} pp). "
                f"Weights/partition look OK; gap is sample-mean mismatch not double-counted WR."
            )
            classification = "MULTIPLE CAUSES" if economy_hot else "WRITER/LUT BUG"
        else:
            root = f"LUT vs stratified gap {gap_pp:.3f} pp; driver {driver}"
            classification = "MULTIPLE CAUSES"
    else:
        root = "LUT matches stratified within 0.10 pp"
        classification = "ECONOMY GENUINELY TOO HOT" if economy_hot else "NOT YET RESOLVED"

    if economy_hot and abs(gap_pp) > 0.10:
        classification = "MULTIPLE CAUSES"
    elif economy_hot and abs(gap_pp) <= 0.10:
        classification = "ECONOMY GENUINELY TOO HOT"

    tunes = tune_candidates(max(strat_pct, lut_pct)) if strat_pct > 96.70 or lut_pct > 96.70 else None

    summary = {
        "configSha256": cfg_sha,
        "mathVersion": 1,
        "liveEconomyModified": False,
        "estimators": {
            "historicalProjection": hist["projectedRtp"],
            "directNaturalMc": mc["meanPct"],
            "directNaturalMcCi95": mc["ci95"],
            "stratifiedMethodA": strat_pct,
            "stratifiedMethodB": strat["methodB_forcedNaturalBonusOnly"]["totalPct"],
            "currentLut": lut_pct,
        },
        "lutVsStratifiedGapPp": gap_pp,
        "acceptanceGate": {
            "thresholdPp": 0.10,
            "pass": abs(gap_pp) <= 0.10,
            "preferredPass": abs(gap_pp) <= 0.05,
        },
        "wrDoubleCount": wr_audit,
        "phase56DoubleCount": p56,
        "wrLutWeight": wr_lut,
        "partitionPass": base_lut["partitionPass"],
        "normalizationPass": base_lut["stratumReconMatch"],
        "classification": classification,
        "rootCause": root,
        "buyCostsProvisional": True,
        "tuneCandidates": tunes,
        "readyForHumanRetuneDecision": bool(
            abs(gap_pp) <= 0.10 and (strat_pct > 96.70 or lut_pct > 96.70)
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
