"""Phase 6B live book-size sample + forced analytic tails. Research/metrics only."""

from __future__ import annotations

import json
import random
import statistics
import zlib
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config, resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import base_trigger_mix, simulate_bonus, TIERS

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase6b_research"
CAP = 50_000.0
SCALE = 1.5  # live tokenValueScale for FS collectors (Phase 5 mid)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(q * (len(ordered) - 1))))
    return float(ordered[idx])


def forced_tails() -> dict:
    def case(label: str, face: float, collectors: float, thermals: float, flight: float) -> dict:
        raw = face * SCALE * thermals * collectors * flight
        capped = min(raw, CAP)
        return {"case": label, "raw": raw, "capped": capped, "drag": max(0.0, raw - capped)}

    rows = [
        case("T5_750_HJ_27x", 750, 2, 1, 27),
        case("T5_5000_J_4x", 5000, 1, 1, 4),
        case("T5_5000_HJ_4x", 5000, 2, 1, 4),
        case("T5_5000_J_th2x3_flight3", 5000, 1, 6, 3),
        case("T6_10000_J_1x", 10000, 1, 1, 1),
        case("T6_10000_HJ_2x", 10000, 2, 1, 2),
        case("T6_10000_J_th2_flight3", 10000, 1, 2, 3),
        case("T6_10000_J_flight27", 10000, 1, 1, 27),
        case("T6_10000_HJ_flight27", 10000, 2, 1, 27),
        case("T6_10000_J_th2_flight27", 10000, 1, 2, 27),
        case("T6_25000_J_1x", 25000, 1, 1, 1),
        case("T6_25000_HJ_flight4", 25000, 2, 1, 4),
        case("T6_50000_J_1x", 50000, 1, 1, 1),
        case("T6_50000_HJ_27x", 50000, 2, 1, 27),
        case("T6_10000_laterJ_recollect_plus_newT4_2x", 10000 + 100, 1, 1, 2),
        case("T6_10000_twoJ_same_batch_2x", 10000, 2, 1, 2),
        case("multi_collector_mult_T5_T6_HJ_8x", 750 + 10000, 2, 1, 8),
        case("rejump_T6_later_HJ_4x", 10000, 2, 1, 4),
    ]
    forced_raw_max = max(r["raw"] for r in rows)
    forced_capped_max = max(r["capped"] for r in rows)
    return {
        "scale": SCALE,
        "cap": CAP,
        "rows": rows,
        "forcedRawMax": forced_raw_max,
        "forcedCappedMax": forced_capped_max,
        "allCappedLe50k": all(r["capped"] <= CAP for r in rows),
    }


def book_sizes(cfg, n_bonus: int = 4000, seed: int = 20260925) -> dict:
    event_counts: list[int] = []
    byte_counts: list[int] = []
    zstd_counts: list[int] = []
    bonus_seen = 0
    for i in range(n_bonus * 40):
        book = resolve_v2_round(random.Random(seed + i), config=cfg)
        if not book.get("isBonus"):
            continue
        events = book["events"]
        blob = json.dumps(events, separators=(",", ":")).encode("utf-8")
        event_counts.append(len(events))
        byte_counts.append(len(blob))
        zstd_counts.append(len(zlib.compress(blob, 6)))
        bonus_seen += 1
        if bonus_seen >= n_bonus:
            break
    return {
        "nBonusBooks": bonus_seen,
        "events": {
            "mean": statistics.fmean(event_counts),
            "p95": _quantile(event_counts, 0.95),
            "p99": _quantile(event_counts, 0.99),
            "max": max(event_counts) if event_counts else 0,
        },
        "uncompressedBytes": {
            "mean": statistics.fmean(byte_counts),
            "p95": _quantile(byte_counts, 0.95),
            "p99": _quantile(byte_counts, 0.99),
            "max": max(byte_counts) if byte_counts else 0,
        },
        "zlibLevel6Bytes": {
            "mean": statistics.fmean(zstd_counts),
            "p95": _quantile(zstd_counts, 0.95),
            "p99": _quantile(zstd_counts, 0.99),
            "max": max(zstd_counts) if zstd_counts else 0,
            "note": "zlib level 6 estimate; not zstd",
        },
    }


def natural_cap_from_live_validate() -> dict:
    path = OUT / "live_validate.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    phase6 = data.get("phase6") or {}
    return {
        "pCap": phase6.get("pCap"),
        "meanCapDrag": phase6.get("meanCapDrag"),
        "n": phase6.get("n"),
        "seed": data.get("seed"),
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cfg = load_v2_config()
    tails = forced_tails()
    print("forced tails:", tails["forcedRawMax"], "->", tails["forcedCappedMax"])
    print("measuring book sizes…", flush=True)
    books = book_sizes(cfg)
    print(
        f"books n={books['nBonusBooks']} events mean={books['events']['mean']:.1f} "
        f"p99={books['events']['p99']} bytes mean={books['uncompressedBytes']['mean']:.0f} "
        f"p99={books['uncompressedBytes']['p99']}",
        flush=True,
    )
    payload = {
        "forcedTails": tails,
        "bookSizes": books,
        "naturalCapFrom1M": natural_cap_from_live_validate(),
    }
    path = OUT / "book_tails.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
