"""Phase 7C.3 — shared helpers (precision only; live config frozen)."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path

from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import base_trigger_mix
from skyjump_v2_phase7c2_conditional import exact_start_mix

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c3_research"
P7C2 = HERE / "phase7c2_research"
EXPECTED_SHA = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"
WEIGHT_SCALE = 10**15
MAX_WIN = 50_000.0

LEAF_ORDER = (
    "BASE_NO_TRIGGER",
    "BASE_TRIGGER_LH_WR_OFF",
    "BASE_TRIGGER_SF_WR_OFF",
    "BASE_TRIGGER_WC_WR_OFF",
    "BASE_TRIGGER_PV_WR_OFF",
    "WORLD_RECORD",
)

TIER_OF = {
    "BASE_TRIGGER_LH_WR_OFF": "LARGE_HILL",
    "BASE_TRIGGER_SF_WR_OFF": "SKI_FLYING",
    "BASE_TRIGGER_WC_WR_OFF": "WORLD_CUP",
    "BASE_TRIGGER_PV_WR_OFF": "PERFECT_V",
}


def sha_config() -> str:
    return hashlib.sha256((HERE / "skyjump_v2_config.json").read_bytes()).hexdigest()


def assert_frozen() -> dict:
    """Historical 7C.3 helper. After 7C.4, mathVersion is 2 and buyModes are promoted;
    economy tables remain the 7C.3 freeze (SHA no longer matches pre-promote pin)."""
    cfg = load_v2_config()
    mv = cfg.get("mathVersion")
    if mv is None and isinstance(cfg.get("meta"), dict):
        mv = cfg["meta"].get("mathVersion")
    if mv is not None and int(mv) not in (1, 2):
        raise RuntimeError(f"unexpected mathVersion {mv}")
    return cfg


def paid_wr_p() -> float:
    cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
    return float(cert["candidates"]["H2"]["wr"]["pPaidRoundApprox"])


def leaf_probabilities(mix: dict, p_wr: float) -> dict[str, float]:
    p_trig = float(mix["P_scatterGe3"])
    p_none = 1.0 - p_trig
    p_bonus = max(0.0, p_trig - p_wr)
    cond = mix["conditional"]
    return {
        "BASE_NO_TRIGGER": p_none,
        "BASE_TRIGGER_LH_WR_OFF": p_bonus * float(cond["LARGE_HILL"]),
        "BASE_TRIGGER_SF_WR_OFF": p_bonus * float(cond["SKI_FLYING"]),
        "BASE_TRIGGER_WC_WR_OFF": p_bonus * float(cond["WORLD_CUP"]),
        "BASE_TRIGGER_PV_WR_OFF": p_bonus * float(cond["PERFECT_V"]),
        "WORLD_RECORD": p_wr,
    }


def exact_line_anchor(cfg: dict | None = None) -> float:
    cfg = cfg or load_v2_config()
    return float(
        exact_line_rtp(cfg["reelModel"]["strips"], cfg["paylines"], cfg["paytable"]["awards"])["lineRtp"]
    )


def load_feature_cert() -> dict:
    path = P7C2 / "base_features_cert.json"
    return json.loads(path.read_text(encoding="utf-8"))


def mean_se(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return 0.0, float("inf")
    if len(xs) == 1:
        return float(xs[0]), float("inf")
    m = statistics.mean(xs)
    se = statistics.stdev(xs) / math.sqrt(len(xs))
    return float(m), float(se)


def ci95(mean: float, se: float) -> list[float]:
    return [mean - 1.96 * se, mean + 1.96 * se]


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    if len(ys) == 1:
        return float(ys[0])
    k = (len(ys) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(ys[int(k)])
    return float(ys[f] + (ys[c] - ys[f]) * (k - f))


def classify_bonus_row(result: dict) -> dict:
    """Extract MECE LH/SF/WC stratification features from a full-round result."""
    bonus = result.get("bonus") or {}
    x = float(result["roundWinXCapped"])
    trig = float(result.get("triggerSpinWinX") or 0.0)
    b = x - trig
    spins = result.get("spins") or []
    judges = sum(int(s.get("judgeCount") or 0) for s in spins)
    hj = sum(int(s.get("headJudgeCount") or 0) for s in spins)
    snap = None
    for e in result.get("events") or []:
        if e.get("type") == "skyjumpFreeSpinState":
            snap = e
    rej = int(snap.get("rejumpsThisBonus") or 0) if snap else int(getattr(result, "rejumpsThisBonus", 0) or 0)
    gfm = int(snap.get("globalFlightMultiplier") or 1) if snap else 1
    floor = int(bonus.get("tokenFloorTierEnd") or 0)
    cap = bool(bonus.get("maxWinReached"))
    length = int(bonus.get("freeSpinsPlayed") or 0)
    if hj > 0 and judges > 0:
        coll = "BOTH"
    elif hj > 0:
        coll = "HEAD"
    elif judges > 0:
        coll = "JUDGE"
    else:
        coll = "NONE"
    if gfm >= 5:
        gb = "5p"
    elif gfm >= 2:
        gb = "2_4"
    else:
        gb = "1"
    if rej >= 2:
        rj = "2p"
    elif rej == 1:
        rj = "1"
    else:
        rj = "0"
    return {
        "x": x,
        "trig": trig,
        "bonusOnly": b,
        "coll": coll,
        "gfmBucket": gb,
        "rejBucket": rj,
        "gfm": gfm,
        "rej": rej,
        "floor": floor,
        "cap": cap,
        "length": length,
        "judges": judges,
        "headJudges": hj,
    }


def lh_stratum_id(row: dict) -> str:
    """Smallest high-R² MECE partition for LH (pilot-validated).

    GFM≥2 collapses to one BOTH_GFM2P bucket — GFM≥5 is too rare for stable p̂.
    """
    coll = row["coll"]
    gb = row["gfmBucket"]
    rj = row["rejBucket"]
    if coll == "NONE":
        return "NONE"
    if coll == "HEAD":
        return "HEAD"
    if coll == "JUDGE":
        if gb != "1" or rj == "2p":
            return "JUDGE_HOT"
        return "JUDGE_COLD"
    # BOTH
    if gb != "1":
        return "BOTH_GFM2P"
    if rj == "2p":
        return "BOTH_RJ2"
    if rj == "1":
        return "BOTH_WARM"
    return "BOTH_COLD"


LH_STRATA = (
    "NONE",
    "HEAD",
    "JUDGE_COLD",
    "JUDGE_HOT",
    "BOTH_COLD",
    "BOTH_WARM",
    "BOTH_RJ2",
    "BOTH_GFM2P",
)


def buy_stratum_id(row: dict) -> str:
    """Shared buy/FS partition (collector × flight-mult × rejump heat)."""
    return lh_stratum_id(row)


def dump_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
