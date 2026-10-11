"""Phase 7C.4 — converged BASE production library (actual LUT RTP gate)."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import random
import time
from collections import defaultdict
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import ConditionalBaseSampler, wr_force_config, wr_off_config
from skyjump_v2_phase7c3_common import classify_bonus_row, lh_stratum_id
from skyjump_v2_phase7c4_common import (
    AUTH_BASE_RTP,
    CEILING,
    EXPECTED_SHA_PRE,
    LEAF_ORDER,
    LH_STRATA,
    OUT,
    WEIGHT_SCALE,
    calibrate_weights,
    dump_json,
    load_authority,
    lut_rtp_from_rows,
    sha_file,
    weighted_mean,
)

HERE = Path(__file__).resolve().parent
LIB = HERE / "library_v2_phase7c4" / "publish_files"

# Production book budgets
N_NONE = 100_000
N_LH_TOTAL = 160_000
N_SF = 60_000
N_WC = 30_000
N_PV = 16
N_WR = 24


def payout_amount(win_x: float) -> int:
    amount = round_book_amount(win_x)
    if amount < 0 or win_x > 50_000 + 1e-9:
        raise ValueError(win_x)
    if amount > 0 and amount % 10 != 0:
        raise ValueError(f"grain {win_x}->{amount}")
    return amount


def book_record(book_id: int, result: dict, *, criteria: str, stratum: str | None = None) -> dict:
    win_x = float(result["roundWinXCapped"])
    amount = payout_amount(win_x)
    events = [{k: v for k, v in e.items() if k != "devSyntheticCapPrior"} for e in result["events"]]
    # Architecture guards
    types = [e.get("type") for e in events]
    if criteria.startswith("BASE_TRIGGER") or criteria == "WORLD_RECORD":
        if "skyjumpFreeSpinsStart" not in types:
            raise ValueError("missing FS start")
        starts = [e for e in events if e.get("type") == "skyjumpSpinStart"]
        if starts and starts[0].get("buyMode"):
            raise ValueError("buyMode in BASE book")
    row = {
        "id": book_id,
        "payoutMultiplier": amount,
        "events": events,
        "criteria": criteria,
        "baseGameWins": round(float(result.get("triggerSpinWinX") or 0.0), 4),
        "freeGameWins": round(max(0.0, win_x - float(result.get("triggerSpinWinX") or 0.0)), 4),
        "mode": "BASE",
        "triggerSpinWinX": float(result.get("triggerSpinWinX") or 0.0),
        "isBonus": bool(result.get("isBonus")),
        "x": win_x,
    }
    if stratum:
        row["stratum"] = stratum
    return row


def _sim_none(args):
    seed0, n, start_id = args
    cfg = load_v2_config()
    sampler = ConditionalBaseSampler(cfg)
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        stops = sampler.sample(rng, "BASE_NO_TRIGGER")
        res = resolve_v2_round(rng, config=cfg, base_stops=stops)
        if res["isBonus"]:
            raise RuntimeError("NO_TRIGGER bonus")
        out.append(book_record(start_id + i, res, criteria="BASE_NO_TRIGGER"))
    return out


def _sim_leaf(args):
    leaf, seed0, n, start_id = args
    cfg0 = load_v2_config()
    sampler = ConditionalBaseSampler(cfg0)
    cfg = wr_force_config(cfg0) if leaf == "WORLD_RECORD" else wr_off_config(cfg0)
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        stops = sampler.sample(rng, leaf)
        res = resolve_v2_round(rng, config=cfg, base_stops=stops)
        stratum = None
        if leaf == "BASE_TRIGGER_LH_WR_OFF":
            stratum = lh_stratum_id(classify_bonus_row(res))
        out.append(book_record(start_id + i, res, criteria=leaf, stratum=stratum))
    return out


def _sim_lh_until(args):
    """Rejection-fill one LH stratum."""
    stratum, seed0, need, max_attempts = args
    cfg0 = load_v2_config()
    sampler = ConditionalBaseSampler(cfg0)
    cfg = wr_off_config(cfg0)
    got = []
    attempts = 0
    i = 0
    while len(got) < need and attempts < max_attempts:
        rng = random.Random(seed0 + i)
        i += 1
        attempts += 1
        stops = sampler.sample(rng, "BASE_TRIGGER_LH_WR_OFF")
        res = resolve_v2_round(rng, config=cfg, base_stops=stops)
        s = lh_stratum_id(classify_bonus_row(res))
        if s == stratum:
            got.append(book_record(0, res, criteria="BASE_TRIGGER_LH_WR_OFF", stratum=s))
    return got, attempts


def parallel_chunks(worker, make_jobs, workers: int):
    jobs = make_jobs()
    with mp.Pool(min(workers, max(1, len(jobs)))) as pool:
        parts = pool.map(worker, jobs)
    rows = []
    for p in parts:
        rows.extend(p)
    return rows


def allocate_lh_counts(p_hat: dict[str, float], total: int) -> dict[str, int]:
    raw = {s: max(80, int(round(total * float(p_hat[s])))) for s in LH_STRATA}
    # Boost rare hot strata slightly for mean stability
    for s in ("BOTH_GFM2P", "BOTH_RJ2", "JUDGE_HOT", "BOTH_WARM"):
        raw[s] = max(raw[s], 400)
    # Rescale to ~total
    ssum = sum(raw.values())
    scale = total / ssum
    out = {s: max(50, int(round(v * scale))) for s, v in raw.items()}
    # Fix remainder
    diff = total - sum(out.values())
    out["NONE"] = max(50, out["NONE"] + diff)
    return out


def build_base(workers: int, seed: int) -> dict:
    t0 = time.time()
    assert sha_file(HERE / "skyjump_v2_config.json") == EXPECTED_SHA_PRE
    auth_pack = load_authority()
    auth = auth_pack["base"]
    probs = auth["probs"]
    means = {
        "BASE_NO_TRIGGER": float(auth["conditionalMeans"]["NO_TRIGGER"]["meanX"]),
        "BASE_TRIGGER_LH_WR_OFF": float(auth["conditionalMeans"]["LH"]["meanX"]),
        "BASE_TRIGGER_SF_WR_OFF": float(auth["conditionalMeans"]["SF"]["meanX"]),
        "BASE_TRIGGER_WC_WR_OFF": float(auth["conditionalMeans"]["WC"]["meanX"]),
        "BASE_TRIGGER_PV_WR_OFF": float(auth["conditionalMeans"]["PV"]["meanX"]),
        "WORLD_RECORD": 50_000.0,
    }
    p_hat = auth_pack["lh"]["pHat"]
    # Prefer natural LH overall mean as leaf target; stratum means from BASE_LH for tilt targets
    stratum_means = {s: float(auth_pack["lh"]["meanStats"][s]["mean"]) for s in LH_STRATA}
    # Rescale stratum means so sum p_s * μ_s == leaf auth mean (preserve relative structure)
    blend = sum(float(p_hat[s]) * stratum_means[s] for s in LH_STRATA)
    leaf_mu = means["BASE_TRIGGER_LH_WR_OFF"]
    if blend > 0:
        scale_m = leaf_mu / blend
        stratum_means = {s: stratum_means[s] * scale_m for s in LH_STRATA}

    LIB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    scale = float(round_book_amount(1.0))

    all_books: list[dict] = []
    next_id = 1
    leaf_meta = {}

    # --- NO_TRIGGER ---
    print(f"BASE_NO_TRIGGER n={N_NONE}", flush=True)
    chunk = max(1, N_NONE // workers)

    def jobs_none():
        jobs, done, w = [], 0, 0
        while done < N_NONE:
            take = min(chunk, N_NONE - done)
            jobs.append((seed + done * 17 + w, take, next_id + done))
            done += take
            w += 1
        return jobs

    none_books = parallel_chunks(_sim_none, jobs_none, workers)
    for b in none_books:
        b["id"] = next_id
        next_id += 1
    xs = [b["x"] for b in none_books]
    W = int(round(probs["BASE_NO_TRIGGER"] * WEIGHT_SCALE))
    ws = calibrate_weights(xs, means["BASE_NO_TRIGGER"], W)
    for b, w in zip(none_books, ws):
        b["weight"] = w
    all_books.extend(none_books)
    leaf_meta["BASE_NO_TRIGGER"] = {
        "n": len(none_books),
        "trueP": probs["BASE_NO_TRIGGER"],
        "effectiveP": sum(ws) / WEIGHT_SCALE,
        "authMean": means["BASE_NO_TRIGGER"],
        "rawMean": sum(xs) / len(xs),
        "weightedMean": weighted_mean(xs, ws),
        "sumWeight": sum(ws),
    }
    print(
        f"  raw={leaf_meta['BASE_NO_TRIGGER']['rawMean']:.5f} "
        f"wmean={leaf_meta['BASE_NO_TRIGGER']['weightedMean']:.5f} "
        f"auth={means['BASE_NO_TRIGGER']:.5f}",
        flush=True,
    )

    # --- LH: natural pool + rare top-up ---
    counts = allocate_lh_counts(p_hat, N_LH_TOTAL)
    print(f"LH target counts={counts} sum={sum(counts.values())}", flush=True)
    print(f"LH natural pool n={N_LH_TOTAL}", flush=True)
    chunk = max(1, N_LH_TOTAL // workers)
    jobs = []
    done = 0
    w = 0
    while done < N_LH_TOTAL:
        take = min(chunk, N_LH_TOTAL - done)
        jobs.append(("BASE_TRIGGER_LH_WR_OFF", seed + 500_000 + done * 19 + w, take, 1 + done))
        done += take
        w += 1
    with mp.Pool(min(workers, len(jobs))) as pool:
        parts = pool.map(_sim_leaf, jobs)
    pool_books: list[dict] = []
    for p in parts:
        pool_books.extend(p)
    by_s: dict[str, list] = defaultdict(list)
    for b in pool_books:
        by_s[b.get("stratum") or "NONE"].append(b)

    lh_books = []
    lh_sub = {}
    for s in LH_STRATA:
        need = counts[s]
        have = by_s.get(s) or []
        print(f"  {s}: natural={len(have)} need={need}", flush=True)
        if len(have) < need:
            missing = need - len(have)
            print(f"    rejection top-up {missing}", flush=True)
            got = []
            attempts = 0
            i = 0
            # single-process top-up for simplicity/correctness on rare strata
            cfg0 = load_v2_config()
            sampler = ConditionalBaseSampler(cfg0)
            cfg = wr_off_config(cfg0)
            while len(got) < missing and attempts < max(500_000, missing * 500):
                rng = random.Random(seed + 8_000_000 + hash(s) % 99991 + i)
                i += 1
                attempts += 1
                stops = sampler.sample(rng, "BASE_TRIGGER_LH_WR_OFF")
                res = resolve_v2_round(rng, config=cfg, base_stops=stops)
                if lh_stratum_id(classify_bonus_row(res)) == s:
                    got.append(book_record(0, res, criteria="BASE_TRIGGER_LH_WR_OFF", stratum=s))
            have = have + got
            print(f"    after top-up={len(have)} attempts={attempts}", flush=True)
        got = have[:need]
        if len(got) < need:
            raise RuntimeError(f"LH stratum {s} underfilled {len(got)}<{need}")
        p_s = float(p_hat[s]) * float(probs["BASE_TRIGGER_LH_WR_OFF"])
        W_s = max(len(got), int(round(p_s * WEIGHT_SCALE)))
        xs_s = [b["x"] for b in got]
        ws_s = calibrate_weights(xs_s, stratum_means[s], W_s)
        for b, wt in zip(got, ws_s):
            b["weight"] = wt
        lh_books.extend(got)
        lh_sub[s] = {
            "n": len(got),
            "trueP": p_s,
            "effectiveP": sum(ws_s) / WEIGHT_SCALE,
            "pHat": float(p_hat[s]),
            "authMean": stratum_means[s],
            "rawMean": sum(xs_s) / len(xs_s),
            "weightedMean": weighted_mean(xs_s, ws_s),
            "sumWeight": sum(ws_s),
        }
        print(
            f"    raw={lh_sub[s]['rawMean']:.3f} wmean={lh_sub[s]['weightedMean']:.3f} "
            f"auth={stratum_means[s]:.3f}",
            flush=True,
        )

    # Renormalize LH total weight exactly to leaf probability (preserve relative stratum weights)
    lh_W_target = int(round(probs["BASE_TRIGGER_LH_WR_OFF"] * WEIGHT_SCALE))
    lh_W_now = sum(b["weight"] for b in lh_books)
    if lh_W_now != lh_W_target and lh_W_now > 0:
        # scale then fix remainder
        scaled = []
        for b in lh_books:
            scaled.append(max(0, int(round(b["weight"] * lh_W_target / lh_W_now))))
        diff = lh_W_target - sum(scaled)
        idx = max(range(len(scaled)), key=lambda i: scaled[i])
        scaled[idx] = max(0, scaled[idx] + diff)
        for b, w in zip(lh_books, scaled):
            b["weight"] = w

    for b in lh_books:
        b["id"] = next_id
        next_id += 1
    all_books.extend(lh_books)
    xs_lh = [b["x"] for b in lh_books]
    ws_lh = [b["weight"] for b in lh_books]
    leaf_meta["BASE_TRIGGER_LH_WR_OFF"] = {
        "n": len(lh_books),
        "trueP": probs["BASE_TRIGGER_LH_WR_OFF"],
        "effectiveP": sum(ws_lh) / WEIGHT_SCALE,
        "authMean": means["BASE_TRIGGER_LH_WR_OFF"],
        "rawMean": sum(xs_lh) / len(xs_lh),
        "weightedMean": weighted_mean(xs_lh, ws_lh),
        "sumWeight": sum(ws_lh),
        "subStrata": lh_sub,
    }
    print(
        f"LH leaf wmean={leaf_meta['BASE_TRIGGER_LH_WR_OFF']['weightedMean']:.4f} "
        f"auth={means['BASE_TRIGGER_LH_WR_OFF']:.4f}",
        flush=True,
    )

    # --- SF / WC / PV / WR ---
    for leaf, n in (
        ("BASE_TRIGGER_SF_WR_OFF", N_SF),
        ("BASE_TRIGGER_WC_WR_OFF", N_WC),
        ("BASE_TRIGGER_PV_WR_OFF", N_PV),
        ("WORLD_RECORD", N_WR),
    ):
        print(f"{leaf} n={n}", flush=True)
        chunk = max(1, n // max(1, min(workers, n)))

        def jobs():
            jobs_, done, w = [], 0, 0
            while done < n:
                take = min(chunk, n - done)
                jobs_.append((leaf, seed + hash(leaf) % 100000 + done * 19 + w, take, next_id + done))
                done += take
                w += 1
            return jobs_

        books = parallel_chunks(_sim_leaf, jobs, workers)
        for b in books:
            b["id"] = next_id
            next_id += 1
        xs = [b["x"] for b in books]
        W = max(len(books), int(round(probs[leaf] * WEIGHT_SCALE)))
        # PV/WR: keep at least 1 per book after scale
        if leaf in ("BASE_TRIGGER_PV_WR_OFF", "WORLD_RECORD"):
            # exact mass via large equal weights
            w_each = max(1, W // len(books))
            ws = [w_each] * len(books)
            # fix sum
            ws[-1] += W - sum(ws)
            # If mean must match and WR is exact 50000, OK. PV: tilt if needed
            if leaf == "BASE_TRIGGER_PV_WR_OFF":
                ws = calibrate_weights(xs, means[leaf], W)
        else:
            ws = calibrate_weights(xs, means[leaf], W)
        for b, w in zip(books, ws):
            b["weight"] = w
        all_books.extend(books)
        leaf_meta[leaf] = {
            "n": len(books),
            "trueP": probs[leaf],
            "effectiveP": sum(ws) / WEIGHT_SCALE,
            "authMean": means[leaf],
            "rawMean": sum(xs) / len(xs),
            "weightedMean": weighted_mean(xs, ws),
            "sumWeight": sum(ws),
        }
        print(
            f"  wmean={leaf_meta[leaf]['weightedMean']:.4f} auth={means[leaf]:.4f} "
            f"pDiff={leaf_meta[leaf]['effectiveP']-probs[leaf]:.3e}",
            flush=True,
        )

    # Global weight renormalization to sum exactly WEIGHT_SCALE (probability 1)
    total_w = sum(int(b["weight"]) for b in all_books)
    if total_w != WEIGHT_SCALE:
        # Adjust NO_TRIGGER residual (largest mass)
        diff = WEIGHT_SCALE - total_w
        for b in all_books:
            if b["criteria"] == "BASE_NO_TRIGGER" and b["weight"] + diff > 0:
                b["weight"] += diff
                break
        # refresh none meta
        none_ws = [b["weight"] for b in all_books if b["criteria"] == "BASE_NO_TRIGGER"]
        none_xs = [b["x"] for b in all_books if b["criteria"] == "BASE_NO_TRIGGER"]
        leaf_meta["BASE_NO_TRIGGER"]["sumWeight"] = sum(none_ws)
        leaf_meta["BASE_NO_TRIGGER"]["effectiveP"] = sum(none_ws) / WEIGHT_SCALE
        leaf_meta["BASE_NO_TRIGGER"]["weightedMean"] = weighted_mean(none_xs, none_ws)

    # Write books + LUT
    books_path = LIB / "books_BASE.jsonl.zst"
    lut_path = LIB / "lookUpTable_BASE_0.csv"
    cctx = zstd.ZstdCompressor(level=3)
    with open(books_path, "wb") as f:
        with cctx.stream_writer(f) as zw:
            for b in all_books:
                row = {k: v for k, v in b.items() if k not in {"x", "weight"}}
                zw.write((json.dumps(row, separators=(",", ":")) + "\n").encode())
    with lut_path.open("w", encoding="utf-8") as f:
        for b in all_books:
            f.write(f"{b['id']},{b['weight']},{b['payoutMultiplier']}\n")

    # Actual LUT RTP — path A: from in-memory weights
    xs_all = [b["x"] for b in all_books]
    ws_all = [int(b["weight"]) for b in all_books]
    rtp_a = lut_rtp_from_rows(xs_all, ws_all)

    # Path B: re-read LUT CSV + books payouts
    id_to_x = {b["id"]: b["payoutMultiplier"] / scale for b in all_books}
    rtp_b_num = 0.0
    rtp_b_den = 0
    with lut_path.open(encoding="utf-8") as f:
        for line in f:
            bid_s, w_s, pay_s = line.strip().split(",")
            w = int(w_s)
            x = int(pay_s) / scale
            rtp_b_num += w * x
            rtp_b_den += w
    rtp_b = rtp_b_num / rtp_b_den if rtp_b_den else 0.0

    gap_a = abs(rtp_a - AUTH_BASE_RTP) * 100
    gap_b = abs(rtp_b - AUTH_BASE_RTP) * 100
    dual_ok = abs(rtp_a - rtp_b) < 1e-12

    # Leaf contributions
    contrib = {}
    for leaf in LEAF_ORDER:
        books = [b for b in all_books if b["criteria"] == leaf]
        xs = [b["x"] for b in books]
        ws = [int(b["weight"]) for b in books]
        tw = sum(ws)
        mean = weighted_mean(xs, ws)
        contrib[leaf] = {
            "effectiveP": tw / WEIGHT_SCALE,
            "weightedMean": mean,
            "rtpContribution": (tw / WEIGHT_SCALE) * mean,
            "authMean": means[leaf],
            "authContribution": probs[leaf] * means[leaf],
            "contribDiffPp": ((tw / WEIGHT_SCALE) * mean - probs[leaf] * means[leaf]) * 100,
            "pError": tw / WEIGHT_SCALE - probs[leaf],
        }

    report = {
        "actualLutRtp": rtp_a,
        "actualLutRtpPct": rtp_a * 100,
        "actualLutRtpPathB": rtp_b,
        "dualPathMatch": dual_ok,
        "authRtp": AUTH_BASE_RTP,
        "authRtpPct": AUTH_BASE_RTP * 100,
        "gapPp": gap_a,
        "gapPathBPp": gap_b,
        "pass_0_05": gap_a <= 0.05 and rtp_a < CEILING,
        "pass_0_03": gap_a <= 0.03,
        "ceilingPass": rtp_a < CEILING,
        "leafMeta": leaf_meta,
        "contributions": contrib,
        "bookCount": len(all_books),
        "sumWeight": sum(ws_all),
        "weightScale": WEIGHT_SCALE,
        "shaBook": sha_file(books_path),
        "shaLut": sha_file(lut_path),
        "paths": {"books": str(books_path), "lut": str(lut_path)},
        "pv": {
            "target": probs["BASE_TRIGGER_PV_WR_OFF"],
            "effective": leaf_meta["BASE_TRIGGER_PV_WR_OFF"]["effectiveP"],
            "pass": abs(leaf_meta["BASE_TRIGGER_PV_WR_OFF"]["effectiveP"] - probs["BASE_TRIGGER_PV_WR_OFF"])
            < probs["BASE_TRIGGER_PV_WR_OFF"] * 0.05 + 1e-18,
        },
        "wr": {
            "target": probs["WORLD_RECORD"],
            "effective": leaf_meta["WORLD_RECORD"]["effectiveP"],
            "pass": abs(leaf_meta["WORLD_RECORD"]["effectiveP"] - probs["WORLD_RECORD"])
            < probs["WORLD_RECORD"] * 0.05 + 1e-18,
        },
        "wallSeconds": time.time() - t0,
    }
    dump_json(OUT / "base_lut_report.json", report)
    print(
        f"BASE LUT RTP={rtp_a*100:.4f}% auth={AUTH_BASE_RTP*100:.4f}% gap={gap_a:.4f}pp "
        f"pass={report['pass_0_05']} dual={dual_ok} wall={report['wallSeconds']:.1f}s",
        flush=True,
    )
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7401)
    args = ap.parse_args()
    mp.freeze_support()
    build_base(args.workers, args.seed)


if __name__ == "__main__":
    main()
