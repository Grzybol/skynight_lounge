"""Phase 7A research — paytable / WR / BODY. Research only; does not promote live config."""

from __future__ import annotations

import json
import math
import random
import statistics
from copy import deepcopy
from pathlib import Path

from skyjump_v2_exact import cell_prob, exact_line_rtp, exact_match_prob
from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, simulate_bonus
from skyjump_v2_reels import REGULAR_IDS

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7a_research"
P_TRIGGER = 0.00652967825443787
MAX_WIN = 50_000.0
GRAIN = 0.1
PREMIUM = ("P1", "P2", "P3")
MID = ("M1", "M2", "M3")
LOW = ("L1", "L2", "L3")

# Hand-crafted feel seeds (monotonic; fit recovers via mid 4/5 after light L cuts).
PT1_FEEL = {
    "P1": {"3": 8, "4": 40, "5": 150},
    "P2": {"3": 5, "4": 22, "5": 75},
    "P3": {"3": 4, "4": 16, "5": 50},
    "M1": {"3": 1.6, "4": 3.3, "5": 10},
    "M2": {"3": 1.3, "4": 2.8, "5": 8},
    "M3": {"3": 1.0, "4": 2.5, "5": 6},
    "L1": {"3": 0.8, "4": 1.7, "5": 3.6},
    "L2": {"3": 0.5, "4": 1.3, "5": 2.7},
    "L3": {"3": 0.4, "4": 1.1, "5": 2.2},
}
PT2_FEEL = {
    "P1": {"3": 10, "4": 50, "5": 200},
    "P2": {"3": 6, "4": 28, "5": 100},
    "P3": {"3": 5, "4": 20, "5": 65},
    "M1": {"3": 1.6, "4": 3.3, "5": 12},
    "M2": {"3": 1.3, "4": 2.8, "5": 9},
    "M3": {"3": 1.0, "4": 2.5, "5": 6.5},
    "L1": {"3": 0.8, "4": 1.7, "5": 3.6},
    "L2": {"3": 0.5, "4": 1.3, "5": 2.7},
    "L3": {"3": 0.3, "4": 1.1, "5": 2.2},
}
PT3_FEEL = {
    "P1": {"3": 12, "4": 60, "5": 250},
    "P2": {"3": 7, "4": 35, "5": 120},
    "P3": {"3": 6, "4": 26, "5": 90},
    "M1": {"3": 1.6, "4": 3.5, "5": 14},
    "M2": {"3": 1.3, "4": 3.0, "5": 10},
    "M3": {"3": 1.0, "4": 2.5, "5": 7},
    "L1": {"3": 0.8, "4": 1.7, "5": 3.6},
    "L2": {"3": 0.5, "4": 1.3, "5": 2.7},
    "L3": {"3": 0.3, "4": 1.1, "5": 2.2},
}


def _start_tier(rng, mix) -> str:
    roll = rng.random()
    cursor = 0.0
    for tier in TIERS:
        cursor += mix["conditional"][tier]
        if roll < cursor:
            return tier
    return "LARGE_HILL"


def awards_dict(cfg):
    return {
        symbol: {str(k): float(v) for k, v in cfg["paytable"]["awards"][symbol].items()}
        for symbol in REGULAR_IDS
    }


def round_grain(x: float) -> float:
    return round(x / GRAIN) * GRAIN


def enforce_mono(a):
    for symbol in REGULAR_IDS:
        a[symbol]["3"] = max(0.2, round_grain(a[symbol]["3"]))
        a[symbol]["4"] = max(a[symbol]["3"], round_grain(a[symbol]["4"]))
        a[symbol]["5"] = max(a[symbol]["4"], round_grain(a[symbol]["5"]))
    return a


def line_pct(strips, paylines, awards) -> float:
    return exact_line_rtp(strips, paylines, awards)["lineRtp"] * 100.0


def analyse_paytable(strips, paylines, awards):
    rtp = exact_line_rtp(strips, paylines, awards)
    by = rtp["bySymbol"]
    n_lines = len(paylines)
    reel_probs = {s: [cell_prob(strip, s) for strip in strips] for s in REGULAR_IDS}
    hit = {}
    for symbol in REGULAR_IDS:
        probs = reel_probs[symbol]
        p3 = exact_match_prob(probs, 3)
        p4 = exact_match_prob(probs, 4)
        p5 = exact_match_prob(probs, 5)
        den = p3 + p4 + p5
        hit[symbol] = {
            "pAny": 1.0 - (1.0 - den) ** n_lines,
            "p4": 1.0 - (1.0 - p4) ** n_lines,
            "p5": 1.0 - (1.0 - p5) ** n_lines,
            "avgMatch": (
                (p3 * float(awards[symbol]["3"]) + p4 * float(awards[symbol]["4"]) + p5 * float(awards[symbol]["5"]))
                / den
                if den
                else 0.0
            ),
        }
    ge = {str(t): 0.0 for t in (5, 10, 25, 50)}
    for symbol in REGULAR_IDS:
        probs = reel_probs[symbol]
        for match in (3, 4, 5):
            pay = float(awards[symbol][str(match)])
            p = exact_match_prob(probs, match)
            for t in (5, 10, 25, 50):
                if pay >= t:
                    ge[str(t)] += n_lines * p
    premium = sum(by[s]["rtp"] for s in PREMIUM)
    mid = sum(by[s]["rtp"] for s in MID)
    low = sum(by[s]["rtp"] for s in LOW)
    return {
        "metrics": {
            "line": rtp["lineRtp"] * 100.0,
            "prem": premium * 100.0,
            "mid": mid * 100.0,
            "low": low * 100.0,
            "by": {s: by[s]["rtp"] * 100.0 for s in REGULAR_IDS},
        },
        "awards": {s: {k: round(float(v) + 1e-9, 1) for k, v in awards[s].items()} for s in REGULAR_IDS},
        "hit": hit,
        "expectedLinesGe": ge,
        "pPremiumUnion": 1.0 - math.prod(1.0 - hit[s]["pAny"] for s in PREMIUM),
    }


def fit_target(strips, paylines, feel, target_pct: float):
    a = enforce_mono(deepcopy(feel))
    for _ in range(400):
        cur = line_pct(strips, paylines, a)
        delta = cur - target_pct
        if abs(delta) < 0.015:
            break
        if delta > 0:
            trimmed = False
            for s in ("L3", "L2", "L1"):
                if a[s]["3"] > 0.2:
                    a[s]["3"] = round_grain(a[s]["3"] - 0.1)
                    trimmed = True
                    break
            if not trimmed:
                for s in ("L3", "L2", "L1"):
                    if a[s]["4"] > a[s]["3"] + 0.05:
                        a[s]["4"] = round_grain(a[s]["4"] - 0.1)
                        break
        else:
            a["M3"]["5"] = round_grain(a["M3"]["5"] + 0.2)
            a["M2"]["5"] = round_grain(a["M2"]["5"] + 0.2)
            a["M1"]["5"] = round_grain(a["M1"]["5"] + 0.2)
            if delta < -0.5:
                a["M3"]["4"] = round_grain(a["M3"]["4"] + 0.1)
                a["M2"]["4"] = round_grain(a["M2"]["4"] + 0.1)
            if delta < -1.0:
                a["P3"]["4"] = round_grain(a["P3"]["4"] + 0.2)
                a["P2"]["4"] = round_grain(a["P2"]["4"] + 0.2)
        enforce_mono(a)
    return a


def wr_analytics(rtp_pp, mix):
    e_accrued = 12.0
    e_incremental = MAX_WIN - e_accrued
    p_paid = (rtp_pp / 100.0) / e_incremental
    p_bonus = p_paid / P_TRIGGER
    rel = {"LARGE_HILL": 1.0, "SKI_FLYING": 3.0, "WORLD_CUP": 6.0, "PERFECT_V": 12.0}
    cond = mix["conditional"]
    weighted = sum(cond[t] * rel[t] for t in TIERS)
    c = p_bonus / weighted
    by_tier = {t: c * rel[t] for t in TIERS}
    return {
        "architecture": "WR-C",
        "availability": "Free Spins only; tier-weighted independent board special",
        "targetRtpPp": rtp_pp,
        "eIncrementalX": e_incremental,
        "pPaidRound": p_paid,
        "oneInPaidRounds": 1.0 / p_paid,
        "pPerTriggeredBonus": p_bonus,
        "oneInBonuses": 1.0 / p_bonus,
        "byTierP": by_tier,
        "pWrGivenPerfectVTierStart": by_tier["PERFECT_V"],
    }


def apply_body(cfg, mode):
    local = json.loads(json.dumps(cfg))
    vw = local["flightTokens"]["valueWeights"]
    tiers = local["flightTokens"]["tiers"]
    if mode == "BODY1":
        vw["1"] = {"1": 90, "2": 6, "3": 3, "4": 1}
        vw["2"] = {"5": 22, "10": 4, "15": 2}
        take = 40
        tiers["1"]["weight"] = int(tiers["1"]["weight"]) - take
        tiers["2"]["weight"] = int(tiers["2"]["weight"]) + take
    elif mode == "BODY2":
        vw["1"] = {"1": 80, "2": 10, "3": 6, "4": 4}
        vw["2"] = {"5": 18, "10": 7, "15": 3}
        take = 100
        tiers["1"]["weight"] = int(tiers["1"]["weight"]) - take
        tiers["2"]["weight"] = int(tiers["2"]["weight"]) + take
    assert int(tiers["5"]["weight"]) == 32
    assert int(tiers["6"]["weight"]) == 8
    assert sum(int(tiers[str(i)]["weight"]) for i in range(1, 7)) == 1_000_000
    return local


def sim_body(cfg, n, seed):
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    mix = base_trigger_mix(cfg)
    rows = []
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        rows.append(simulate_bonus(random.Random(seed + i), tier, cand, config=cfg, paying_candidate=pay))
    capped = [r["bonusWinXCapped"] for r in rows]
    ordered = sorted(capped)

    def pct(p):
        return ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1)))]

    return {
        "n": n,
        "meanX": statistics.fmean(capped),
        "median": statistics.median(capped),
        "p25": pct(0.25),
        "p75": pct(0.75),
        "p99_9": pct(0.999),
        "pCap": sum(1 for r in rows if r["maxWinReached"]) / n,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_v2_config()
    strips = cfg["reelModel"]["strips"]
    paylines = cfg["paylines"]
    base = awards_dict(cfg)
    mix = base_trigger_mix(cfg)
    control_pct = line_pct(strips, paylines, base)

    pt0 = analyse_paytable(strips, paylines, base)
    pt0["delta"] = 0.0
    paytables = {"PT0": pt0}
    for name, feel, target in (
        ("PT1", PT1_FEEL, control_pct),
        ("PT2", PT2_FEEL, control_pct + 0.60),
        ("PT3", PT3_FEEL, control_pct + 1.00),
    ):
        awards = fit_target(strips, paylines, feel, target)
        row = analyse_paytable(strips, paylines, awards)
        row["delta"] = row["metrics"]["line"] - control_pct
        paytables[name] = row
        print(
            name,
            f"line={row['metrics']['line']:.3f}",
            f"prem={row['metrics']['prem']:.3f}",
            f"d={row['delta']:.3f}",
        )
    (OUT / "paytables.json").write_text(json.dumps(paytables, indent=2), encoding="utf-8")

    wr = {k: wr_analytics(float(k), mix) for k in ("0.35", "0.40", "0.45", "0.50", "0.55")}
    (OUT / "world_record.json").write_text(json.dumps(wr, indent=2), encoding="utf-8")

    bodies = {}
    body0 = sim_body(cfg, n=100_000, seed=8_201_000_000)
    bodies["BODY0"] = body0
    print("BODY0", body0)
    for mode in ("BODY1", "BODY2"):
        cfg_b = apply_body(cfg, mode)
        row = sim_body(cfg_b, n=100_000, seed=8_201_000_000)
        row["incrementalPp"] = (row["meanX"] - body0["meanX"]) * P_TRIGGER * 100.0
        bodies[mode] = row
        print(mode, row["median"], row["meanX"], row["incrementalPp"])
    (OUT / "body.json").write_text(json.dumps(bodies, indent=2), encoding="utf-8")

    candidates = []
    combos = [
        ("C1", 0.40, "PT1", "BODY1"),
        ("C2", 0.45, "PT2", "BODY1"),
        ("C3", 0.50, "PT2", "BODY1"),
        ("C4", 0.40, "PT3", "BODY0"),
        ("C5", 0.35, "PT2", "BODY0"),
        ("C6", 0.40, "PT1", "BODY0"),
        ("C7", 0.50, "PT3", "BODY1"),
        ("C8", 0.55, "PT2", "BODY1"),
    ]
    for cid, wr_pp, pt, body in combos:
        pt_delta = paytables[pt]["delta"]
        body_pp = 0.0 if body == "BODY0" else bodies[body]["incrementalPp"]
        projected = 93.828 + wr_pp + pt_delta + body_pp
        candidates.append(
            {
                "id": cid,
                "wrPp": wr_pp,
                "paytable": pt,
                "body": body,
                "paytableDeltaPp": pt_delta,
                "bodyDeltaPp": body_pp,
                "projectedRtp": projected,
                "calibrationReservePp": 96.50 - projected,
                "inPreferredBand": 96.30 <= projected <= 96.45,
            }
        )
    (OUT / "candidates.json").write_text(json.dumps(candidates, indent=2), encoding="utf-8")
    print(json.dumps(candidates, indent=2))


if __name__ == "__main__":
    main()
