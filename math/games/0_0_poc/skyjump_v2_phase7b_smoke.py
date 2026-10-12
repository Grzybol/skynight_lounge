"""Phase 7B live-resolver smoke (NOT final production RTP certification)."""

from __future__ import annotations

import json
import random
from pathlib import Path

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix, new_bonus_state, resolve_fs_spin
from skyjump_v2_world_record import wr_probability

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7b_research" / "smoke.json"
ART = HERE / "phase7a2_research" / "certification.json"
FREEZE = HERE / "phase7b_research" / "pre_promotion_freeze.json"
N = 25_000  # smoke only; Phase 7A.2 used 1M for promotion cert


def body0(cfg, freeze):
    local = json.loads(json.dumps(cfg))
    for k, w in freeze["tierWeights"].items():
        local["flightTokens"]["tiers"][str(k)]["weight"] = int(w)
    local["flightTokens"]["valueWeights"]["1"] = {str(k): int(v) for k, v in freeze["vw1"].items()}
    local["flightTokens"]["valueWeights"]["2"] = {str(k): int(v) for k, v in freeze["vw2"].items()}
    local["worldRecord"]["enabled"] = False
    return local


def no_wr(cfg):
    local = json.loads(json.dumps(cfg))
    local["worldRecord"]["enabled"] = False
    return local


def mean_bonus(cfg, n, seed):
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    mix = base_trigger_mix(cfg)["conditional"]
    total = 0.0
    for i in range(n):
        rng = random.Random(seed + i)
        u = rng.random()
        acc = 0.0
        tier = TIERS[0]
        for t in TIERS:
            acc += mix[t]
            if u <= acc:
                tier = t
                break
        state = new_bonus_state(tier, initial_spins=cand.initialSpins)
        while state.freeSpinsRemaining > 0 and not state.maxWinReached:
            resolve_fs_spin(
                random.Random(seed + i * 1_000_003 + state.freeSpinsPlayed),
                state,
                cand,
                config=cfg,
                paying_candidate=pay,
            )
        total += state.bonusWinXCapped
    return total / n


def main():
    cfg = load_v2_config()
    cert = json.loads(ART.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    h2 = cert["candidates"]["H2"]
    mix = base_trigger_mix(cfg)
    p_trig = float(mix["P_scatterGe3"])
    b1 = cert["pairedDeltas"]["BODY1_standalone"]
    # Prefer consistent p from paired cert (meanΔX → pp)
    if abs(b1["meanDeltaX"]) > 1e-12:
        p_trig = b1["pp"] / (b1["meanDeltaX"] * 100.0)

    pt0_awards = {
        "P1": {"3": 4.0, "4": 11.0, "5": 36.0},
        "P2": {"3": 2.4, "4": 7.0, "5": 18.0},
        "P3": {"3": 1.8, "4": 5.0, "5": 12.0},
        "M1": {"3": 1.0, "4": 2.5, "5": 6.0},
        "M2": {"3": 0.8, "4": 2.0, "5": 5.0},
        "M3": {"3": 0.6, "4": 1.6, "5": 4.0},
        "L1": {"3": 0.4, "4": 1.0, "5": 2.0},
        "L2": {"3": 0.3, "4": 0.8, "5": 1.6},
        "L3": {"3": 0.2, "4": 0.6, "5": 1.2},
    }
    # Prefer archived PT0 from phase7a2 if stored
    pt0_path = HERE / "phase7a2_research" / "pt0_awards.json"
    if pt0_path.exists():
        pt0_awards = json.loads(pt0_path.read_text(encoding="utf-8"))["awards"]
    else:
        # Use cert baseExact comparison via exact on live vs freeze P1 only incomplete —
        # fall back to certification baseExact figures for PT0
        pt0_awards = None

    strips = cfg["reelModel"]["strips"]
    paylines = cfg["paylines"]
    live_line = exact_line_rtp(strips, paylines, cfg["paytable"]["awards"])["lineRtp"] * 100
    base_delta_art = float(cert["baseExact"]["deltaPp"])
    pt2h_full = float(cert["pt2hDecomposition"]["totalFullGameDeltaPp"])
    body1_pp = float(cert["pairedDeltas"]["BODY1_standalone"]["pp"])
    wr_pp = float(h2["wrPp"])

    cfg0 = body0(cfg, freeze)
    cfg1 = no_wr(cfg)
    m0 = mean_bonus(cfg0, N, 710_000)
    m1 = mean_bonus(cfg1, N, 710_000)
    body_smoke_pp = (m1 - m0) * p_trig * 100.0

    wr = cfg["worldRecord"]
    report = {
        "note": "Phase 7B implementation smoke — NOT final book/RTP certification",
        "n": N,
        "pTriggerUsed": p_trig,
        "liveConfig": {
            "paytable": cfg["paytable"]["candidateOrigin"],
            "body": cfg["flightTokens"].get("bodyCandidate"),
            "worldRecord": wr["candidateOrigin"],
            "c": wr["c"],
            "byTierPSpin": wr["byTierPSpin"],
            "liveBaseLinePct": live_line,
            "artifactPt2hBaseLinePct": cert["baseExact"]["PT2H"],
            "baseLineMatch": abs(live_line - cert["baseExact"]["PT2H"]) < 1e-9,
        },
        "artifact": {
            "pt2hFullDeltaPp": pt2h_full,
            "body1Pp": body1_pp,
            "wrPp": wr_pp,
            "projectedRtp": h2["projectedRtp"],
            "pPaidRound": h2["wr"]["pPaidRoundApprox"],
            "oneInPaidRounds": h2["wr"]["oneInPaidRoundsApprox"],
            "pWrGivenBonus": h2["wr"]["pPerTriggeredBonusApprox"],
        },
        "smokeBody1": {
            "mean0": m0,
            "mean1": m1,
            "deltaX": m1 - m0,
            "pp": body_smoke_pp,
            "artifactPp": body1_pp,
            "absDeviationPp": abs(body_smoke_pp - body1_pp),
            "passLt0_10": abs(body_smoke_pp - body1_pp) < 0.10,
        },
        "wrLiveMatchesArtifact": all(
            abs(float(wr["byTierPSpin"][t]) - float(h2["wr"]["byTierPSpin"][t])) < 1e-18 for t in TIERS
        ),
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
