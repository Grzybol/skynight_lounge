"""Phase 7C V2 production books + LUT writer (parallel to V1; does not touch run.py)."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing as mp
import random
import shutil
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_freespins import resolve_v2_buy_round, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase5a_engine import base_trigger_mix
from skyjump_v2_phase7b_wr_samples import stops_for_tier
from skyjump_v2_world_record import wr_probability

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LIBRARY = HERE / "library_v2" / "publish_files"
STAGING = REPO / "stake-upload" / "math"
RESEARCH = HERE / "phase7c_research"

MODES = ("BASE", "LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
TIERS = ("LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
N_NATURAL = {
    "BASE": 100_000,
    "LARGE_HILL": 100_000,
    "SKI_FLYING": 100_000,
    "WORLD_CUP": 100_000,
    "PERFECT_V": 100_000,
}
# Stratified BASE counts (production)
N_BASE_NONE = 100_000
N_BASE_TIER = {
    "LARGE_HILL": 40_000,
    "SKI_FLYING": 25_000,
    "WORLD_CUP": 20_000,
    "PERFECT_V": 15_000,
}
N_WR_STRATA = 20
WEIGHT_SCALE = 10**12
TARGET_RTP = 0.965
RTP_LO = 0.964
RTP_HI = 0.966
CEILING = 0.967


def payout_amount(win_x: float) -> int:
    amount = round_book_amount(win_x)
    if amount < 0:
        raise ValueError("negative payout")
    if win_x > 50_000 + 1e-9:
        raise ValueError("payout exceeds cap")
    if amount > 0 and amount % 10 != 0:
        raise ValueError(f"payout grain fail {win_x} -> {amount}")
    return amount


def book_record(book_id: int, result: dict, *, criteria: str, mode: str) -> dict:
    win_x = float(result["roundWinXCapped"])
    amount = payout_amount(win_x)
    events = result["events"]
    cleaned = []
    for event in events:
        row = {k: v for k, v in event.items() if k != "devSyntheticCapPrior"}
        cleaned.append(row)
    base_wins = float(result.get("triggerSpinWinX") or 0.0)
    if result.get("base") and not result.get("isBonus"):
        base_wins = win_x
    free_wins = max(0.0, win_x - base_wins) if result.get("isBonus") else 0.0
    if mode != "BASE":
        base_wins = 0.0
        free_wins = win_x
    return {
        "id": book_id,
        "payoutMultiplier": amount,
        "events": cleaned,
        "criteria": criteria,
        "baseGameWins": round(base_wins, 4),
        "freeGameWins": round(free_wins, 4),
        "mode": mode,
    }


def _sim_base(args):
    seed0, n, start_id = args
    cfg = load_v2_config()
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        result = resolve_v2_round(rng, config=cfg)
        out.append(
            book_record(
                start_id + i,
                result,
                criteria="basegame" if not result["isBonus"] else "freegame",
                mode="BASE",
            )
        )
    return out


def _sim_base_none(args):
    """Rejection-sample non-bonus BASE paid rounds."""
    seed0, n, start_id = args
    cfg = load_v2_config()
    out = []
    i = 0
    while len(out) < n:
        rng = random.Random(seed0 + i * 1_000_003)
        result = resolve_v2_round(rng, config=cfg)
        i += 1
        if result["isBonus"]:
            continue
        out.append(book_record(start_id + len(out), result, criteria="basegame", mode="BASE"))
    return out


def _sim_base_tier(args):
    """Forced-tier BASE trigger via math-owned stops + live FS body."""
    tier, seed0, n, start_id, force_wr = args
    cfg = load_v2_config()
    stops = stops_for_tier(cfg, tier)
    if force_wr:
        cfg = json.loads(json.dumps(cfg))
        cfg["worldRecord"]["byTierPSpin"] = {t: 1.0 for t in TIERS}
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        result = resolve_v2_round(rng, config=cfg, base_stops=stops)
        if not result["isBonus"]:
            raise RuntimeError(f"forced stops failed for {tier}")
        crit = "world_record" if force_wr else f"freegame_{tier}"
        out.append(book_record(start_id + i, result, criteria=crit, mode="BASE"))
    return out


def _sim_buy(args):
    tier, seed0, n, start_id, force_wr, cost = args
    cfg = load_v2_config()
    if force_wr:
        cfg = json.loads(json.dumps(cfg))
        cfg["worldRecord"]["byTierPSpin"] = {t: 1.0 for t in TIERS}
    out = []
    for i in range(n):
        rng = random.Random(seed0 + i)
        result = resolve_v2_buy_round(rng, config=cfg, start_tier=tier, wager_cost_multiplier=cost)
        crit = "world_record" if force_wr else "freegame"
        if force_wr and not any(e.get("type") == "skyjumpWorldRecord" for e in result["events"]):
            crit = "freegame"
        out.append(book_record(start_id + i, result, criteria=crit, mode=tier))
    return out


def parallel_map(fn, jobs, workers=8):
    with mp.Pool(processes=min(workers, max(1, len(jobs)))) as pool:
        parts = pool.map(fn, jobs)
    rows = []
    for part in parts:
        rows.extend(part)
    return rows


def chunk_jobs(n, seed, start_id, make_job, workers=8):
    chunk = max(1, n // workers)
    jobs = []
    done = 0
    w = 0
    while done < n:
        take = min(chunk, n - done)
        jobs.append(make_job(seed + done * 9973 + w, take, start_id + done))
        done += take
        w += 1
    return jobs


def write_jsonl_zst(path: Path, books: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    cctx = zstd.ZstdCompressor(level=3)
    with path.open("wb") as fh:
        with cctx.stream_writer(fh) as compressor:
            for book in books:
                line = json.dumps(book, separators=(",", ":"), ensure_ascii=False) + "\n"
                compressor.write(line.encode("utf-8"))


def write_lut(path: Path, books: list[dict], weights: list[int]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for book, weight in zip(books, weights):
            if weight <= 0:
                raise ValueError("illegal weight")
            fh.write(f"{book['id']},{weight},{book['payoutMultiplier']}\n")


def lut_rtp(books, weights, cost: float) -> float:
    num = 0.0
    den = 0.0
    for book, w in zip(books, weights):
        num += (book["payoutMultiplier"] / 100.0) * w
        den += w * cost
    return num / den if den else 0.0


def lut_mean_x(books, weights) -> float:
    total_w = sum(weights)
    if not total_w:
        return 0.0
    return sum((b["payoutMultiplier"] / 100.0) * w for b, w in zip(books, weights)) / total_w


def paid_wr_p() -> float:
    cert = json.loads((HERE / "phase7a2_research" / "certification.json").read_text(encoding="utf-8"))
    return float(cert["candidates"]["H2"]["wr"]["pPaidRoundApprox"])


def assign_weights_base_stratified(books: list[dict], cfg: dict) -> list[int]:
    """Weight by exact trigger mix + explicit WR paid-round probability."""
    mix = base_trigger_mix(cfg)
    p_trig = float(mix["P_scatterGe3"])
    p_wr = paid_wr_p()
    p_none = max(0.0, 1.0 - p_trig)
    p_bonus = max(0.0, p_trig - p_wr)
    cond = mix["conditional"]

    groups: dict[str, list[int]] = {
        "basegame": [],
        "world_record": [],
        **{f"freegame_{t}": [] for t in TIERS},
    }
    for i, book in enumerate(books):
        crit = book["criteria"]
        if crit in groups:
            groups[crit].append(i)
        elif crit == "freegame":
            # legacy untyped freegame — fold into LH
            groups["freegame_LARGE_HILL"].append(i)
        else:
            raise ValueError(f"unknown criteria {crit}")

    weights = [0] * len(books)

    def fill(indices: list[int], mass: float):
        if not indices:
            if mass > 0:
                raise ValueError(f"missing books for mass {mass}")
            return
        w = max(1, int(round(WEIGHT_SCALE * mass / len(indices))))
        for i in indices:
            weights[i] = w

    fill(groups["basegame"], p_none)
    for tier in TIERS:
        fill(groups[f"freegame_{tier}"], p_bonus * float(cond[tier]))
    fill(groups["world_record"], p_wr)
    if any(w <= 0 for w in weights):
        raise ValueError("zero weight book")
    return weights


def assign_weights_buy(books: list[dict], tier: str, cfg: dict) -> list[int]:
    buy_ev_path = RESEARCH / "buy_ev.json"
    if buy_ev_path.exists():
        buy = json.loads(buy_ev_path.read_text(encoding="utf-8"))
        p = float(buy["tiers"][tier]["wrP"])
    else:
        p = 1.0 - (1.0 - wr_probability(cfg, tier)) ** 12
    natural = [i for i, b in enumerate(books) if b["criteria"] != "world_record"]
    rare = [i for i, b in enumerate(books) if b["criteria"] == "world_record"]
    weights = [0] * len(books)
    if not rare:
        return [1] * len(books)
    w_nat = max(1, int(round(WEIGHT_SCALE * (1.0 - p) / max(1, len(natural)))))
    w_rare = max(1, int(round(WEIGHT_SCALE * p / len(rare))))
    for i in natural:
        weights[i] = w_nat
    for i in rare:
        weights[i] = w_rare
    return weights


def effective_p(weights, books, criteria="world_record") -> float:
    total = sum(weights)
    rare = sum(w for b, w in zip(books, weights) if b["criteria"] == criteria)
    return rare / total if total else 0.0


def mode_size_stats(books: list[dict], books_path: Path, lut_path: Path, weights, cost: float) -> dict:
    rtp = lut_rtp(books, weights, cost)
    raw_sizes = [len(json.dumps(b, separators=(",", ":"))) for b in books[:: max(1, len(books) // 2000)]]
    # Full uncompressed estimate from sample
    mean_chars = sum(raw_sizes) / len(raw_sizes) if raw_sizes else 0
    return {
        "bookCount": len(books),
        "compressedBytes": books_path.stat().st_size,
        "uncompressedBytesEst": int(mean_chars * len(books)),
        "lutBytes": lut_path.stat().st_size,
        "shaBook": hashlib.sha256(books_path.read_bytes()).hexdigest(),
        "shaLut": hashlib.sha256(lut_path.read_bytes()).hexdigest(),
        "lutRtp": rtp,
        "meanPayoutX": lut_mean_x(books, weights),
        "effectiveWrP": effective_p(weights, books),
        "maxPayoutX": max(b["payoutMultiplier"] for b in books) / 100.0,
        "minPayoutX": min(b["payoutMultiplier"] for b in books) / 100.0,
        "pCap": sum(1 for b in books if b["payoutMultiplier"] >= 5_000_000) / len(books),
        "cost": cost,
        "meanBookCharsSample": mean_chars,
        "maxBookCharsSample": max(raw_sizes) if raw_sizes else 0,
    }


def generate_base_stratified(cfg: dict) -> dict:
    books: list[dict] = []
    # Non-bonus
    jobs = chunk_jobs(N_BASE_NONE, 7_100_000, 1, lambda seed, take, sid: (seed, take, sid))
    books.extend(parallel_map(_sim_base_none, jobs))
    next_id = len(books) + 1
    # Tier strata
    for tier in TIERS:
        n = N_BASE_TIER[tier]
        jobs = chunk_jobs(
            n,
            7_300_000 + TIERS.index(tier) * 10_000,
            next_id,
            lambda seed, take, sid, t=tier: (t, seed, take, sid, False),
        )
        books.extend(parallel_map(_sim_base_tier, jobs))
        next_id = len(books) + 1
    # WR strata (forced WR on LH trigger path)
    jobs = chunk_jobs(
        N_WR_STRATA,
        7_200_000,
        next_id,
        lambda seed, take, sid: ("LARGE_HILL", seed, take, sid, True),
    )
    wr_books = parallel_map(_sim_base_tier, jobs)
    for b in wr_books:
        b["criteria"] = "world_record"
    books.extend(wr_books)

    for i, book in enumerate(books, start=1):
        book["id"] = i

    weights = assign_weights_base_stratified(books, cfg)
    books_path = LIBRARY / "books_BASE.jsonl.zst"
    lut_path = LIBRARY / "lookUpTable_BASE_0.csv"
    write_jsonl_zst(books_path, books)
    write_lut(lut_path, books, weights)
    stats = mode_size_stats(books, books_path, lut_path, weights, 1.0)
    stats.update(
        {
            "natural": N_BASE_NONE,
            "tierStrata": dict(N_BASE_TIER),
            "wrStrata": N_WR_STRATA,
            "stratified": True,
        }
    )
    return stats


def generate_mode(mode: str, cost: float, cfg: dict) -> dict:
    n = N_NATURAL[mode]
    books: list[dict] = []
    if mode == "BASE":
        return generate_base_stratified(cfg)

    jobs = chunk_jobs(
        n,
        8_000_000 + MODES.index(mode) * 100_000,
        1,
        lambda seed, take, sid: (mode, seed, take, sid, False, cost),
    )
    books.extend(parallel_map(_sim_buy, jobs))
    wr_jobs = chunk_jobs(
        N_WR_STRATA,
        8_500_000 + MODES.index(mode) * 100_000,
        n + 1,
        lambda seed, take, sid: (mode, seed, take, sid, True, cost),
    )
    wr_books = parallel_map(_sim_buy, wr_jobs)
    for b in wr_books:
        b["criteria"] = "world_record"
    books.extend(wr_books)

    for i, book in enumerate(books, start=1):
        book["id"] = i

    weights = assign_weights_buy(books, mode, cfg)
    books_path = LIBRARY / f"books_{mode}.jsonl.zst"
    lut_path = LIBRARY / f"lookUpTable_{mode}_0.csv"
    write_jsonl_zst(books_path, books)
    write_lut(lut_path, books, weights)
    stats = mode_size_stats(books, books_path, lut_path, weights, cost)
    stats.update({"natural": n, "wrStrata": N_WR_STRATA, "stratified": False})
    return stats


def choose_cost(mean_x: float) -> dict:
    best = None
    center = mean_x / TARGET_RTP
    for d in range(-40, 41):
        cost = round(center + d * 0.1, 1)
        if cost <= 0:
            continue
        rtp = mean_x / cost
        if rtp > CEILING:
            continue
        score = (
            0 if RTP_LO <= rtp <= RTP_HI else 1,
            abs(rtp - TARGET_RTP),
            abs(cost - round(cost)),
            abs(2 * cost - round(2 * cost)),
        )
        if best is None or score < best[0]:
            best = (score, cost, rtp)
    if best is None:
        cost = round(center, 1)
        return {"cost": cost, "rtp": mean_x / cost}
    return {"cost": best[1], "rtp": best[2]}


def read_lut_mean(path: Path) -> float:
    num = 0.0
    den = 0.0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            _bid, w, pay = line.split(",")
            w_i = int(w)
            num += (int(pay) / 100.0) * w_i
            den += w_i
    return num / den if den else 0.0


def reprice_buy_costs_from_luts() -> dict:
    """Solve buy costs from actual LUT mean payouts (no book regen)."""
    costs = {"BASE": 1.0}
    means = {}
    rtps = {}
    for tier in TIERS:
        mean_x = read_lut_mean(LIBRARY / f"lookUpTable_{tier}_0.csv")
        chosen = choose_cost(mean_x)
        costs[tier] = chosen["cost"]
        means[tier] = mean_x
        rtps[tier] = chosen["rtp"] * 100.0
    spread = max(rtps.values()) - min(rtps.values())
    return {
        "costs": costs,
        "means": means,
        "rtps": rtps,
        "spreadPp": spread,
        "pass": spread <= 0.50 and all(r / 100.0 <= CEILING for r in rtps.values()),
    }


def write_index(costs: dict):
    modes = []
    for mode in MODES:
        modes.append(
            {
                "name": mode,
                "cost": costs[mode],
                "events": f"books_{mode}.jsonl.zst",
                "weights": f"lookUpTable_{mode}_0.csv",
            }
        )
    index = {"modes": modes}
    (LIBRARY / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def stage_upload():
    STAGING.mkdir(parents=True, exist_ok=True)
    # Replace files in place — Windows/OneDrive can deny rmtree on the folder.
    wanted = ["index.json", *[f"books_{m}.jsonl.zst" for m in MODES], *[f"lookUpTable_{m}_0.csv" for m in MODES]]
    for name in wanted:
        src = LIBRARY / name
        if not src.exists():
            raise FileNotFoundError(src)
        dst = STAGING / name
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)
    # Drop any stray files not in the production set
    allowed = set(wanted)
    for path in list(STAGING.iterdir()):
        if path.name not in allowed:
            if path.is_file():
                path.unlink()
    leaked = [
        p.name
        for p in STAGING.rglob("*")
        if p.is_file() and (p.suffix in {".md", ".py"} or (p.suffix == ".json" and p.name != "index.json"))
    ]
    return {"path": str(STAGING), "leaked": leaked}


def refresh_report_rtps(report: dict, costs: dict) -> dict:
    for mode in MODES:
        mean_x = read_lut_mean(LIBRARY / f"lookUpTable_{mode}_0.csv")
        cost = costs[mode]
        report["modes"][mode]["cost"] = cost
        report["modes"][mode]["meanPayoutX"] = mean_x
        report["modes"][mode]["lutRtp"] = mean_x / cost
        report["modes"][mode]["shaLut"] = hashlib.sha256(
            (LIBRARY / f"lookUpTable_{mode}_0.csv").read_bytes()
        ).hexdigest()
        report["modes"][mode]["shaBook"] = hashlib.sha256(
            (LIBRARY / f"books_{mode}.jsonl.zst").read_bytes()
        ).hexdigest()
    report["costs"] = costs
    report["crossMode"] = {
        "rtps": {m: report["modes"][m]["lutRtp"] * 100 for m in MODES},
        "spreadPp": (
            max(report["modes"][m]["lutRtp"] for m in MODES) - min(report["modes"][m]["lutRtp"] for m in MODES)
        )
        * 100,
    }
    return report


def main():
    mp.freeze_support()
    RESEARCH.mkdir(parents=True, exist_ok=True)
    LIBRARY.mkdir(parents=True, exist_ok=True)
    cfg = load_v2_config()
    buy_path = RESEARCH / "buy_ev.json"
    if not buy_path.exists():
        raise SystemExit("run skyjump_v2_phase7c_buy_ev.py first")
    buy = json.loads(buy_path.read_text(encoding="utf-8"))
    # Initial costs from EV search; final buy costs come from LUT reprice after generation
    costs = {"BASE": 1.0, **buy["chosenCosts"]}

    report = {"costs": costs, "modes": {}}
    for mode in MODES:
        print("generating", mode, flush=True)
        report["modes"][mode] = generate_mode(mode, costs[mode], cfg)
        print(mode, report["modes"][mode]["lutRtp"], report["modes"][mode]["bookCount"], flush=True)

    priced = reprice_buy_costs_from_luts()
    costs = priced["costs"]
    # Persist canonical buy presentation + update buy_ev chosen
    buy["chosenCosts"] = {t: costs[t] for t in TIERS}
    buy["chosenRtps"] = priced["rtps"]
    buy["crossModeSpreadPp"] = priced["spreadPp"]
    buy["crossModePass"] = priced["pass"]
    buy["pricedFrom"] = "LUT_mean"
    buy_path.write_text(json.dumps(buy, indent=2) + "\n", encoding="utf-8")

    modes_out = {
        "mathLineage": "skyjump-v2",
        "modes": [
            {
                "rgsKey": "BASE",
                "playerName": "Base",
                "type": "default",
                "costMultiplier": 1.0,
                "maxWin": 50000,
                "enabled": True,
            }
        ]
        + [
            {
                "rgsKey": t,
                "playerName": t.replace("_", " ").title(),
                "type": "buy",
                "costMultiplier": costs[t],
                "maxWin": 50000,
                "enabled": True,
                "startsBonusTier": t,
            }
            for t in TIERS
        ],
    }
    (RESEARCH / "buy_modes.json").write_text(json.dumps(modes_out, indent=2) + "\n", encoding="utf-8")

    write_index(costs)
    report = refresh_report_rtps(report, costs)
    staging = stage_upload()
    report["staging"] = staging
    report["buyReprice"] = priced
    (RESEARCH / "books_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["crossMode"], indent=2))


def rebuild_base_and_reprice():
    """Regenerate stratified BASE only; reprice buys from existing LUTs; restage."""
    mp.freeze_support()
    cfg = load_v2_config()
    print("regenerating stratified BASE", flush=True)
    base_stats = generate_base_stratified(cfg)
    print("BASE", base_stats["lutRtp"], base_stats["bookCount"], flush=True)
    report = json.loads((RESEARCH / "books_report.json").read_text(encoding="utf-8"))
    report["modes"]["BASE"] = base_stats
    priced = reprice_buy_costs_from_luts()
    costs = priced["costs"]
    buy = json.loads((RESEARCH / "buy_ev.json").read_text(encoding="utf-8"))
    buy["chosenCosts"] = {t: costs[t] for t in TIERS}
    buy["chosenRtps"] = priced["rtps"]
    buy["crossModeSpreadPp"] = priced["spreadPp"]
    buy["crossModePass"] = priced["pass"]
    buy["pricedFrom"] = "LUT_mean"
    (RESEARCH / "buy_ev.json").write_text(json.dumps(buy, indent=2) + "\n", encoding="utf-8")
    write_index(costs)
    report = refresh_report_rtps(report, costs)
    report["staging"] = stage_upload()
    report["buyReprice"] = priced
    (RESEARCH / "books_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["crossMode"], indent=2))
    print(json.dumps(priced, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rebuild-base":
        rebuild_base_and_reprice()
    else:
        main()
