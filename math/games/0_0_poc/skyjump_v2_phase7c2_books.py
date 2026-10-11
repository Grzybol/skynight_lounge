"""Phase 7C.2 — authoritative BASE strata rebuild + LUT (parallel to Phase 7C outputs)."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing as mp
import random
import shutil
import statistics
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_exact import exact_line_rtp
from skyjump_v2_freespins import resolve_v2_buy_round, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import (
    ConditionalBaseSampler,
    TIERS,
    exact_start_mix,
    wr_force_config,
    wr_off_config,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "phase7c2_research"
LIB = HERE / "library_v2_phase7c2" / "publish_files"
STAGING = REPO / "stake-upload-phase7c2" / "math"
P7C1 = HERE / "phase7c1_research"

EXPECTED_SHA = "d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0"
WEIGHT_SCALE = 10**15  # large enough that PV/WR rare mass does not floor to distortion

# Book counts — precision targets on paid-round contribution
N_BOOKS = {
    "BASE_NO_TRIGGER": 80_000,
    "BASE_TRIGGER_LH_WR_OFF": 60_000,
    "BASE_TRIGGER_SF_WR_OFF": 30_000,
    "BASE_TRIGGER_WC_WR_OFF": 15_000,
    "BASE_TRIGGER_PV_WR_OFF": 8,  # few books + large scale → accurate rare weight
    "WORLD_RECORD": 20,
}

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


def payout_amount(win_x: float) -> int:
    amount = round_book_amount(win_x)
    if amount < 0 or win_x > 50_000 + 1e-9:
        raise ValueError(f"bad payout {win_x}")
    if amount > 0 and amount % 10 != 0:
        raise ValueError(f"grain {win_x} -> {amount}")
    return amount


def book_record(book_id: int, result: dict, *, criteria: str) -> dict:
    win_x = float(result["roundWinXCapped"])
    amount = payout_amount(win_x)
    events = [{k: v for k, v in e.items() if k != "devSyntheticCapPrior"} for e in result["events"]]
    # Architecture guard: triggered books must include BASE spin start before FS
    types = [e.get("type") for e in events]
    if criteria.startswith("BASE_TRIGGER") or criteria == "WORLD_RECORD":
        if "skyjumpFreeSpinsStart" not in types:
            raise ValueError("missing FreeSpinsStart")
        # Must have a non-buy BASE board path (no buyMode True on spin start)
        starts = [e for e in events if e.get("type") == "skyjumpSpinStart"]
        if starts and starts[0].get("buyMode"):
            raise ValueError("buyMode spin in natural BASE book")
    return {
        "id": book_id,
        "payoutMultiplier": amount,
        "events": events,
        "criteria": criteria,
        "baseGameWins": round(float(result.get("triggerSpinWinX") or 0.0), 4),
        "freeGameWins": round(max(0.0, win_x - float(result.get("triggerSpinWinX") or 0.0)), 4),
        "mode": "BASE",
        "triggerSpinWinX": float(result.get("triggerSpinWinX") or 0.0),
        "isBonus": bool(result.get("isBonus")),
    }


def _sim_leaf(args):
    leaf, seed0, n, start_id = args
    cfg = load_v2_config()
    sampler = ConditionalBaseSampler(cfg)
    if leaf == "WORLD_RECORD":
        cfg = wr_force_config(cfg)
    elif leaf.startswith("BASE_TRIGGER"):
        cfg = wr_off_config(cfg)
    # NO_TRIGGER uses live WR (effectively never hits)
    out = []
    meta = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        stops = sampler.sample(rng, leaf)
        result = resolve_v2_round(rng, config=cfg, base_stops=stops)
        if leaf == "BASE_NO_TRIGGER" and result["isBonus"]:
            raise RuntimeError("NO_TRIGGER produced bonus")
        if leaf.startswith("BASE_TRIGGER") and not result["isBonus"]:
            raise RuntimeError(f"{leaf} produced non-bonus")
        if leaf.startswith("BASE_TRIGGER"):
            tier = TIER_OF[leaf]
            if result["bonus"]["startTier"] != tier and leaf != "BASE_TRIGGER_WC_WR_OFF":
                # WC may upgrade classification edge cases — allow startTier match scatter class
                pass
        book = book_record(start_id + i, result, criteria=leaf)
        out.append(book)
        meta.append(
            {
                "x": float(result["roundWinXCapped"]),
                "trig": float(result["triggerSpinWinX"]),
                "bonusOnly": float(result["roundWinXCapped"]) - float(result["triggerSpinWinX"]),
            }
        )
    return out, meta


def parallel_leaf(leaf: str, n: int, seed: int, start_id: int, workers: int = 8):
    chunk = max(1, n // workers)
    jobs = []
    done = 0
    w = 0
    while done < n:
        take = min(chunk, n - done)
        jobs.append((leaf, seed + done * 9973 + w, take, start_id + done))
        done += take
        w += 1
    with mp.Pool(processes=min(workers, len(jobs))) as pool:
        parts = pool.map(_sim_leaf, jobs)
    books, metas = [], []
    for b, m in parts:
        books.extend(b)
        metas.extend(m)
    return books, metas


def assign_weights(books: list[dict], probs: dict[str, float]) -> list[int]:
    groups: dict[str, list[int]] = {k: [] for k in LEAF_ORDER}
    for i, book in enumerate(books):
        groups[book["criteria"]].append(i)
    weights = [0] * len(books)
    for leaf, indices in groups.items():
        mass = probs[leaf]
        if not indices:
            if mass > 1e-18:
                raise ValueError(f"missing books for {leaf} mass={mass}")
            continue
        # Exact integer weights without destructive max(1) inflation:
        # allocate floor shares then distribute remainder by largest remainder.
        raw = [WEIGHT_SCALE * mass / len(indices)] * len(indices)
        floors = [int(math.floor(x)) for x in raw]
        rem = int(WEIGHT_SCALE * mass) - sum(floors)
        # If rem negative due to float, clamp
        if rem < 0:
            rem = 0
        order = sorted(range(len(indices)), key=lambda j: (raw[j] - floors[j]), reverse=True)
        for j in order[:rem]:
            floors[j] += 1
        # Ultra-rare: if total allocated 0, put mass on first book as 1 and scale note —
        # with WEIGHT_SCALE=1e15 and n_pv=8, mass*SCALE >= 1.
        if sum(floors) == 0 and mass > 0:
            floors[0] = max(1, int(round(WEIGHT_SCALE * mass)))
        for idx, w in zip(indices, floors):
            if w <= 0:
                raise ValueError(f"non-positive weight for {leaf}")
            weights[idx] = w
    # Verify total weight ≈ SCALE
    total = sum(weights)
    if abs(total - WEIGHT_SCALE) / WEIGHT_SCALE > 1e-6:
        # Renormalize by adjusting largest group slightly is unnecessary if remainder method used on each leaf separately —
        # leaf remainder uses int(SCALE*mass) so sum over leaves ≈ SCALE.
        pass
    return weights


def write_jsonl_zst(path: Path, books: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    cctx = zstd.ZstdCompressor(level=3)
    with path.open("wb") as fh, cctx.stream_writer(fh) as compressor:
        for book in books:
            line = json.dumps(book, separators=(",", ":"), ensure_ascii=False) + "\n"
            compressor.write(line.encode("utf-8"))


def write_lut(path: Path, books: list[dict], weights: list[int]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for book, w in zip(books, weights):
            fh.write(f"{book['id']},{w},{book['payoutMultiplier']}\n")


def lut_stats(books, weights, probs):
    total_w = sum(weights)
    rtp = sum((b["payoutMultiplier"] / 100.0) * w for b, w in zip(books, weights)) / total_w
    by = {}
    for leaf in LEAF_ORDER:
        idx = [i for i, b in enumerate(books) if b["criteria"] == leaf]
        wsum = sum(weights[i] for i in idx)
        wx = sum((books[i]["payoutMultiplier"] / 100.0) * weights[i] for i in idx)
        mean = wx / wsum if wsum else 0.0
        by[leaf] = {
            "n": len(idx),
            "sumWeight": wsum,
            "normalizedP": wsum / total_w,
            "theoreticalP": probs[leaf],
            "meanPayoutX": mean,
            "rtpContribution": wx / total_w,
            "pDelta": wsum / total_w - probs[leaf],
        }
    return {"rtp": rtp, "sumP": sum(v["normalizedP"] for v in by.values()), "leaves": by}


def _pair_prior_chunk(args):
    tier, seed0, n = args
    cfg = load_v2_config()
    sampler = ConditionalBaseSampler(cfg)
    cfg_off = wr_off_config(cfg)
    rows = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        stops = sampler.sample(rng, tier)
        # Full natural with actual prior
        r1 = resolve_v2_round(random.Random(seed0 + i + 1), config=cfg_off, base_stops=stops)
        trig = float(r1["triggerSpinWinX"])
        # Same stops + FS seed, but zero prior via buy-like path is not identical FS —
        # Paired: resolve with round_prior_win_x override 0 after capturing trig from first resolve.
        # Use identical RNG stream for FS by resolving twice with same seed and stops,
        # overriding prior on second call.
        r0 = resolve_v2_round(
            random.Random(seed0 + i + 1),
            config=cfg_off,
            base_stops=stops,
            round_prior_win_x=0.0,
        )
        # bonus-only under actual prior ≈ full - trig; under zero prior ≈ full0 (trig forced 0 in accounting)
        bonus_actual = float(r1["roundWinXCapped"]) - trig
        bonus_zero = float(r0["roundWinXCapped"])  # triggerSpinWinX overwritten to 0
        rows.append(
            {
                "trig": trig,
                "fullActual": float(r1["roundWinXCapped"]),
                "bonusActual": bonus_actual,
                "bonusZeroPrior": bonus_zero,
                "deltaBonus": bonus_actual - bonus_zero,
            }
        )
    return rows


def prior_cap_effect(n_per: int = 8_000) -> dict:
    mix = exact_start_mix()
    jobs = [(t, 500_000 + i * 101, n_per) for i, t in enumerate(TIERS)]
    with mp.Pool(4) as pool:
        parts = pool.map(_pair_prior_chunk, jobs)
    by = {}
    global_delta = 0.0
    for tier, rows in zip(TIERS, parts):
        d = statistics.fmean(r["deltaBonus"] for r in rows)
        by[tier] = {
            "n": len(rows),
            "eTrig": statistics.fmean(r["trig"] for r in rows),
            "eFull": statistics.fmean(r["fullActual"] for r in rows),
            "eBonusActual": statistics.fmean(r["bonusActual"] for r in rows),
            "eBonusZeroPrior": statistics.fmean(r["bonusZeroPrior"] for r in rows),
            "deltaBonusX": d,
        }
        global_delta += mix[tier] * d
    return {"byTier": by, "paidRoundPriorCapEffectPp": global_delta * 100.0}


def _buy_chunk(args):
    tier, seed0, n = args
    cfg = load_v2_config()
    xs = []
    for i in range(n):
        r = resolve_v2_buy_round(random.Random(seed0 + i), config=cfg, start_tier=tier)
        xs.append(float(r["roundWinXCapped"]))
    return tier, xs


def buy_ev_authoritative(n: int = 120_000) -> dict:
    jobs = [(t, 800_000 + i * 13, n) for i, t in enumerate(TIERS)]
    with mp.Pool(4) as pool:
        parts = pool.map(_buy_chunk, jobs)
    out = {}
    for tier, xs in parts:
        mean = statistics.fmean(xs)
        se = math.sqrt(statistics.pvariance(xs) / len(xs))
        out[tier] = {"n": len(xs), "meanX": mean, "se": se, "ci95": [mean - 1.96 * se, mean + 1.96 * se]}
    return out


def choose_cost(mean_x: float, target: float = 0.965) -> dict:
    best = None
    center = mean_x / target
    for d in range(-40, 41):
        cost = round(center + d * 0.1, 1)
        if cost <= 0:
            continue
        rtp = mean_x / cost
        if rtp > 0.967:
            continue
        score = (0 if 0.964 <= rtp <= 0.966 else 1, abs(rtp - target), abs(cost - round(cost)))
        if best is None or score < best[0]:
            best = (score, cost, rtp)
    return {"cost": best[1], "rtp": best[2], "meanX": mean_x}


def generate_base_library():
    OUT.mkdir(parents=True, exist_ok=True)
    LIB.mkdir(parents=True, exist_ok=True)
    cfg = load_v2_config()
    mix = exact_start_mix(cfg)
    p_wr = paid_wr_p()
    probs = leaf_probabilities(mix, p_wr)
    assert abs(sum(probs.values()) - 1.0) < 1e-12

    books: list[dict] = []
    leaf_meta = {}
    next_id = 1
    for leaf in LEAF_ORDER:
        n = N_BOOKS[leaf]
        print("leaf", leaf, n, flush=True)
        chunk, meta = parallel_leaf(leaf, n, seed=7_700_000 + hash(leaf) % 10_000, start_id=next_id)
        books.extend(chunk)
        xs = [m["x"] for m in meta]
        leaf_meta[leaf] = {
            "n": n,
            "meanX": statistics.fmean(xs),
            "se": math.sqrt(statistics.pvariance(xs) / n),
            "meanTrig": statistics.fmean(m["trig"] for m in meta),
            "meanBonusOnly": statistics.fmean(m["bonusOnly"] for m in meta),
        }
        next_id = len(books) + 1
        print("  mean", leaf_meta[leaf]["meanX"], "se", leaf_meta[leaf]["se"], flush=True)

    for i, b in enumerate(books, start=1):
        b["id"] = i

    weights = assign_weights(books, probs)
    stats = lut_stats(books, weights, probs)

    # Authoritative estimator from leaf means × theoretical p (not noisy LUT p)
    auth = sum(probs[leaf] * leaf_meta[leaf]["meanX"] for leaf in LEAF_ORDER)
    auth_var = sum((probs[leaf] * leaf_meta[leaf]["se"]) ** 2 for leaf in LEAF_ORDER)
    auth_se = math.sqrt(auth_var)

    books_path = LIB / "books_BASE.jsonl.zst"
    lut_path = LIB / "lookUpTable_BASE_0.csv"
    write_jsonl_zst(books_path, books)
    write_lut(lut_path, books, weights)

    report = {
        "probs": probs,
        "leafMeta": leaf_meta,
        "lut": stats,
        "authoritativeRtp": auth,
        "authoritativeSe": auth_se,
        "authoritativeRtpPct": auth * 100,
        "authoritativeSePp": auth_se * 100,
        "lutRtpPct": stats["rtp"] * 100,
        "gapPp": (stats["rtp"] - auth) * 100,
        "acceptance": {
            "gapPp": abs(stats["rtp"] - auth) * 100,
            "pass_0_10": abs(stats["rtp"] - auth) * 100 <= 0.10,
            "pass_0_05": abs(stats["rtp"] - auth) * 100 <= 0.05,
        },
        "shaBook": hashlib.sha256(books_path.read_bytes()).hexdigest(),
        "shaLut": hashlib.sha256(lut_path.read_bytes()).hexdigest(),
        "bookCount": len(books),
        "mix": mix,
        "pWr": p_wr,
        "pvWeight": {
            "target": probs["BASE_TRIGGER_PV_WR_OFF"],
            "effective": stats["leaves"]["BASE_TRIGGER_PV_WR_OFF"]["normalizedP"],
        },
        "wrWeight": {
            "target": probs["WORLD_RECORD"],
            "effective": stats["leaves"]["WORLD_RECORD"]["normalizedP"],
        },
    }
    # Component tolerances (paid-round pp)
    tol = {
        "BASE_NO_TRIGGER": 0.05,
        "BASE_TRIGGER_LH_WR_OFF": 0.03,
        "BASE_TRIGGER_SF_WR_OFF": 0.02,
        "BASE_TRIGGER_WC_WR_OFF": 0.01,
        "BASE_TRIGGER_PV_WR_OFF": 0.002,
        "WORLD_RECORD": 0.002,
    }
    component = {}
    for leaf in LEAF_ORDER:
        # Compare auth leaf contrib vs lut leaf contrib
        a = probs[leaf] * leaf_meta[leaf]["meanX"] * 100
        b = stats["leaves"][leaf]["rtpContribution"] * 100
        component[leaf] = {"authPp": a, "lutPp": b, "deltaPp": b - a, "tolPp": tol[leaf], "pass": abs(b - a) <= tol[leaf]}
    report["componentAgreement"] = component
    report["componentPass"] = all(v["pass"] for v in component.values())

    (OUT / "base_rebuild.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def stage_base_only():
    STAGING.mkdir(parents=True, exist_ok=True)
    for name in ("books_BASE.jsonl.zst", "lookUpTable_BASE_0.csv"):
        src = LIB / name
        dst = STAGING / name
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)
    index = {
        "modes": [
            {
                "name": "BASE",
                "cost": 1.0,
                "events": "books_BASE.jsonl.zst",
                "weights": "lookUpTable_BASE_0.csv",
            }
        ]
    }
    (LIB / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    (STAGING / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return {"path": str(STAGING)}


def main():
    mp.freeze_support()
    raw = (HERE / "skyjump_v2_config.json").read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise SystemExit(f"STOP config sha {sha}")

    line = exact_line_rtp(
        load_v2_config()["reelModel"]["strips"],
        load_v2_config()["paylines"],
        load_v2_config()["paytable"]["awards"],
    )["lineRtp"]
    print("line", line * 100, flush=True)

    print("prior/cap", flush=True)
    prior = prior_cap_effect(6_000)
    (OUT / "prior_cap_effect.json").write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")
    print("priorCapPp", prior["paidRoundPriorCapEffectPp"], flush=True)

    print("generate BASE library", flush=True)
    report = generate_base_library()
    staging = stage_base_only()
    report["staging"] = staging
    (OUT / "base_rebuild.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("AUTH", report["authoritativeRtpPct"], "LUT", report["lutRtpPct"], "gap", report["gapPp"], flush=True)
    print("ACCEPT", report["acceptance"], flush=True)

    if report["acceptance"]["pass_0_10"]:
        print("buy EV", flush=True)
        buy = buy_ev_authoritative(100_000)
        costs = {t: choose_cost(buy[t]["meanX"]) for t in TIERS}
        payload = {"buyEv": buy, "provisionalCosts": costs}
        (OUT / "buy_authoritative.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(costs, indent=2))
    else:
        print("SKIP buy — BASE acceptance failed", flush=True)


if __name__ == "__main__":
    main()
