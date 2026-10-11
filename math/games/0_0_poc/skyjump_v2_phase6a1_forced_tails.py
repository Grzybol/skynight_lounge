"""Forced tail cases for Phase 6A.1 (analytic). Research only."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "phase6a1_research"
SCALE = 1.5
CAP = 50_000.0


def case(label: str, face: float, collectors: float, thermals: float, flight: float) -> dict:
    raw = face * SCALE * thermals * collectors * flight
    capped = min(raw, CAP)
    return {
        "case": label,
        "raw": raw,
        "capped": capped,
        "drag": max(0.0, raw - capped),
    }


def main() -> None:
    rows = [
        case("T5_750_J_1x", 750, 1, 1, 1),
        case("T5_750_HJ_27x", 750, 2, 1, 27),
        case("T5_5000_J_4x", 5000, 1, 1, 4),
        case("T5_5000_J_8x", 5000, 1, 1, 8),
        case("T5_5000_HJ_4x", 5000, 2, 1, 4),
        case("T5_5000_J_th2x3_flight3", 5000, 1, 6, 3),
        case("T6_10000_J_1x", 10000, 1, 1, 1),
        case("T6_10000_HJ_2x", 10000, 2, 1, 2),
        case("T6_10000_J_th2_flight3", 10000, 1, 2, 3),
        case("T6_25000_J_1x", 25000, 1, 1, 1),
        case("T6_25000_HJ_1x", 25000, 2, 1, 1),
        case("T6_50000_J_1x", 50000, 1, 1, 1),
        case("T6_50000_HJ_27x", 50000, 2, 1, 27),
        # R-BATCH: early Judge spent; later Judge recollects preserved T6 + new tokens.
        case("T6_10000_laterJ_after_spentJ_1x", 10000, 1, 1, 1),
        case("T6_10000_laterJ_recollect_plus_newT4_2x", 10000 + 100, 1, 1, 2),
        case("T6_10000_twoJ_same_batch_2x", 10000, 2, 1, 2),
    ]
    OUT.mkdir(exist_ok=True)
    path = OUT / "forced_tails.json"
    path.write_text(json.dumps({"scale": SCALE, "cap": CAP, "rows": rows}, indent=2), encoding="utf-8")
    for row in rows:
        print(f"{row['case']:40} raw={row['raw']:10.0f} cap={row['capped']:8.0f} drag={row['drag']:10.0f}")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
