"""Phase 7C.4 — production math freeze helpers (economy frozen; LUT convergence)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c4_research"
P7C3 = HERE / "phase7c3_research"
EXPECTED_SHA_PRE = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"
WEIGHT_SCALE = 10**15
AUTH_BASE_RTP = 0.9639073610676338
CEILING = 0.9670
MAX_WIN = 50_000.0

PRICE_A_DESIGN = {
    "LARGE_HILL": 30.2,
    "SKI_FLYING": 196.9,
    "WORLD_CUP": 412.8,
    "PERFECT_V": 1369.1,
}

LEAF_ORDER = (
    "BASE_NO_TRIGGER",
    "BASE_TRIGGER_LH_WR_OFF",
    "BASE_TRIGGER_SF_WR_OFF",
    "BASE_TRIGGER_WC_WR_OFF",
    "BASE_TRIGGER_PV_WR_OFF",
    "WORLD_RECORD",
)

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


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def load_authority() -> dict:
    auth = json.loads((P7C3 / "base_authoritative.json").read_text(encoding="utf-8"))
    buy = json.loads((P7C3 / "buy_certification.json").read_text(encoding="utf-8"))
    lh = json.loads((P7C3 / "lh_strata" / "BASE_LH.json").read_text(encoding="utf-8"))
    return {"base": auth, "buy": buy, "lh": lh}


def buy_auth_means(buy: dict) -> dict[str, dict]:
    """WR-off EV + WR contribution → final auth mean (no double-count)."""
    out = {}
    for tier, row in buy["buyEv"].items():
        ev_off = float(row["evX"])
        p_wr = float(row["pWr"])
        # Incremental WR: with prob p_wr, round becomes 50000 instead of WR-off outcome.
        # Auth mean used in 7C.3 PRICE_A: (1-p)*ev_off + p*50000
        mean_final = (1.0 - p_wr) * ev_off + p_wr * MAX_WIN
        wr_contrib = mean_final - ev_off
        out[tier] = {
            "evWrOff": ev_off,
            "pWr": p_wr,
            "wrContributionX": wr_contrib,
            "authMeanFinal": mean_final,
        }
    return out


def calibrate_weights(xs: list[float], target_mean: float, total_weight: int) -> list[int]:
    """Exponential tilt so weighted mean ≈ target_mean; integer weights sum to total_weight.

    Books remain real samples; only relative sampling weights are adjusted for LUT
    convergence to the certified authoritative conditional mean.
    """
    n = len(xs)
    if n == 0:
        return []
    if n == 1 or total_weight <= 0:
        return [max(1, total_weight)] if total_weight > 0 else [0]

    m0 = sum(xs) / n
    if abs(m0 - target_mean) < 1e-12:
        base = total_weight // n
        rem = total_weight - base * n
        return [base + (1 if i < rem else 0) for i in range(n)]

    # Bound λ search using range of x to avoid overflow
    xmin, xmax = min(xs), max(xs)
    span = max(xmax - xmin, 1e-9)

    def wmean(lam: float) -> float:
        # stable: subtract max of lam*(x-m0)
        scores = [lam * (x - m0) for x in xs]
        peak = max(scores)
        ws = [math.exp(min(700.0, max(-700.0, s - peak))) for s in scores]
        sw = sum(ws) or 1.0
        return sum(w * x for w, x in zip(ws, xs)) / sw

    # λ range covering strong tilt without overflow
    lo, hi = -50.0 / span, 50.0 / span
    # Ensure target is between min and max attainable
    target = min(max(target_mean, xmin + 1e-12), xmax - 1e-12)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        wm = wmean(mid)
        if wm < target:
            lo = mid
        else:
            hi = mid
    lam = 0.5 * (lo + hi)
    scores = [lam * (x - m0) for x in xs]
    peak = max(scores)
    raw = [math.exp(min(700.0, max(-700.0, s - peak))) for s in scores]
    sraw = sum(raw) or 1.0
    exact = [total_weight * r / sraw for r in raw]
    floors = [int(math.floor(v)) for v in exact]
    if sum(floors) > total_weight:
        floors = [max(0, f) for f in floors]
    assigned = sum(floors)
    rem = total_weight - assigned
    order = sorted(range(n), key=lambda i: exact[i] - floors[i], reverse=True)
    out = list(floors)
    i = 0
    while rem > 0 and n > 0:
        out[order[i % n]] += 1
        rem -= 1
        i += 1
        if i > n * 5:
            break
    if sum(out) != total_weight:
        diff = total_weight - sum(out)
        j = max(range(n), key=lambda k: out[k])
        out[j] = max(0, out[j] + diff)
    return out


def weighted_mean(xs: list[float], ws: list[int]) -> float:
    tw = sum(ws)
    if tw <= 0:
        return 0.0
    return sum(x * w for x, w in zip(xs, ws)) / tw


def lut_rtp_from_rows(payouts_x: list[float], weights: list[int]) -> float:
    tw = sum(weights)
    if tw <= 0:
        return 0.0
    return sum(x * w for x, w in zip(payouts_x, weights)) / tw
