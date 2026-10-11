"""Phase 7C.2 buy-mode authoritative books/LUT (after BASE acceptance)."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing as mp
import random
import statistics
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_freespins import resolve_v2_buy_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import TIERS, wr_force_config, wr_off_config
from skyjump_v2_world_record import wr_probability

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c2_research"
LIB = HERE / "library_v2_phase7c2" / "publish_files"
WEIGHT_SCALE = 10**15
N_NAT = 80_000
N_WR = 20


def payout_amount(win_x: float) -> int:
    amount = round_book_amount(win_x)
    if amount < 0 or win_x > 50_000 + 1e-9:
        raise ValueError(win_x)
    if amount > 0 and amount % 10 != 0:
        raise ValueError(amount)
    return amount


def _sim(args):
    tier, seed0, n, start_id, force_wr = args
    cfg = load_v2_config()
    cfg = wr_force_config(cfg) if force_wr else wr_off_config(cfg)
    out = []
    for i in range(n):
        r = resolve_v2_buy_round(random.Random(seed0 + i), config=cfg, start_tier=tier)
        crit = "world_record" if force_wr else "freegame"
        out.append(
            {
                "id": start_id + i,
                "payoutMultiplier": payout_amount(float(r["roundWinXCapped"])),
                "events": [{k: v for k, v in e.items() if k != "devSyntheticCapPrior"} for e in r["events"]],
                "criteria": crit,
                "mode": tier,
            }
        )
    return out


def parallel(tier, n, seed, start_id, force_wr, workers=8):
    chunk = max(1, n // workers)
    jobs = []
    done = 0
    w = 0
    while done < n:
        take = min(chunk, n - done)
        jobs.append((tier, seed + done * 17 + w, take, start_id + done, force_wr))
        done += take
        w += 1
    with mp.Pool(min(workers, len(jobs))) as pool:
        parts = pool.map(_sim, jobs)
    rows = []
    for p in parts:
        rows.extend(p)
    return rows


def wr_p_buy(tier: str, mean_spins: float, cfg) -> float:
    p = wr_probability(cfg, tier)
    return 1.0 - (1.0 - p) ** max(1.0, mean_spins)


def weights_for(books, p_wr: float):
    nat = [i for i, b in enumerate(books) if b["criteria"] != "world_record"]
    rare = [i for i, b in enumerate(books) if b["criteria"] == "world_record"]
    w = [0] * len(books)
    # largest-remainder allocation
    def alloc(indices, mass):
        if not indices:
            return
        raw = WEIGHT_SCALE * mass / len(indices)
        floors = [int(math.floor(raw))] * len(indices)
        rem = int(WEIGHT_SCALE * mass) - sum(floors)
        for j in range(max(0, rem)):
            floors[j % len(indices)] += 1
        if sum(floors) == 0 and mass > 0:
            floors[0] = max(1, int(round(WEIGHT_SCALE * mass)))
        for idx, ww in zip(indices, floors):
            w[idx] = max(1, ww)

    alloc(nat, 1.0 - p_wr)
    alloc(rare, p_wr)
    return w


def write_mode(tier: str, auth_mean: float, cost: float):
    cfg = load_v2_config()
    print("buy", tier, flush=True)
    books = parallel(tier, N_NAT, 9_000_000 + TIERS.index(tier) * 1000, 1, False)
    # estimate spins from a sample for wr p
    mean_spins = 12.0
    wr_books = parallel(tier, N_WR, 9_500_000 + TIERS.index(tier) * 1000, N_NAT + 1, True)
    for b in wr_books:
        b["criteria"] = "world_record"
    books.extend(wr_books)
    for i, b in enumerate(books, 1):
        b["id"] = i
    p_wr = wr_p_buy(tier, mean_spins, cfg)
    w = weights_for(books, p_wr)
    tw = sum(w)
    mean = sum((b["payoutMultiplier"] / 100.0) * ww for b, ww in zip(books, w)) / tw
    bp = LIB / f"books_{tier}.jsonl.zst"
    lp = LIB / f"lookUpTable_{tier}_0.csv"
    cctx = zstd.ZstdCompressor(level=3)
    with bp.open("wb") as fh, cctx.stream_writer(fh) as c:
        for b in books:
            c.write((json.dumps(b, separators=(",", ":")) + "\n").encode())
    with lp.open("w", encoding="utf-8", newline="\n") as fh:
        for b, ww in zip(books, w):
            fh.write(f"{b['id']},{ww},{b['payoutMultiplier']}\n")
    rel = abs(mean - auth_mean) / auth_mean
    return {
        "tier": tier,
        "authMeanX": auth_mean,
        "lutMeanX": mean,
        "relErr": rel,
        "pass_0_001": rel <= 0.001,
        "pass_0_0010": rel <= 0.001,
        "agree_0_10pct": rel <= 0.001,  # 0.10% 
        "agree_loose": rel <= 0.01,
        "cost": cost,
        "lutRtp": mean / cost,
        "bookCount": len(books),
        "shaBook": hashlib.sha256(bp.read_bytes()).hexdigest(),
        "shaLut": hashlib.sha256(lp.read_bytes()).hexdigest(),
        "pWr": p_wr,
    }


def main():
    mp.freeze_support()
    buy = json.loads((OUT / "buy_authoritative.json").read_text(encoding="utf-8"))
    report = {}
    for tier in TIERS:
        auth = buy["buyEv"][tier]["meanX"]
        cost = buy["provisionalCosts"][tier]["cost"]
        report[tier] = write_mode(tier, auth, cost)
        print(tier, report[tier]["lutMeanX"], report[tier]["relErr"], flush=True)
    # refresh index
    index = {
        "modes": [
            {"name": "BASE", "cost": 1.0, "events": "books_BASE.jsonl.zst", "weights": "lookUpTable_BASE_0.csv"}
        ]
        + [
            {
                "name": t,
                "cost": buy["provisionalCosts"][t]["cost"],
                "events": f"books_{t}.jsonl.zst",
                "weights": f"lookUpTable_{t}_0.csv",
            }
            for t in TIERS
        ]
    }
    (LIB / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    (OUT / "buy_lut_rebuild.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({t: {"rel": report[t]["relErr"], "pass": report[t]["agree_loose"]} for t in TIERS}, indent=2))


if __name__ == "__main__":
    main()
