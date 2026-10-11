"""Write non-production Phase 2 math-sample books. Not Stake production books."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_events import round_to_v2_events
from skyjump_v2_resolve import resolve_v2_base

OUT = HERE / "skyjump_v2_math_samples.json"
SEED = 20260921


def _pack(sample_id: str, title: str, result: dict) -> dict:
    events = round_to_v2_events(result, source="math")
    return {
        "id": sample_id,
        "title": title,
        "stops": result["stops"],
        "board": result["board"],
        "lineWinX": result["lineWinX"],
        "totalFeatureWinX": result["totalFeatureWinX"],
        "totalWinX": result["totalWinX"],
        "scatterCount": result["scatter"]["count"],
        "perfectV": result["scatter"]["perfectV"],
        "events": events,
    }


def collect_samples() -> list[dict]:
    rng = random.Random(SEED)
    sequential = [resolve_v2_base(rng) for _ in range(8)]
    samples = [
        _pack("01", "deterministic seed spin 0", sequential[0]),
        _pack("02", "deterministic seed spin 1", sequential[1]),
    ]
    wanted = {
        "03": ("zero line win", lambda row: row["lineWinX"] == 0),
        "04": ("single line win", lambda row: len(row["wins"]) == 1),
        "05": ("multi-line win", lambda row: len(row["wins"]) >= 2),
        "06": ("three or more scatters", lambda row: row["scatter"]["count"] >= 3),
        "07": ("four scatters", lambda row: row["scatter"]["count"] == 4),
        "08": ("line win at least 5x", lambda row: row["lineWinX"] >= 5),
    }
    found: dict[str, dict] = {}
    hunt = random.Random(SEED + 99)
    for _ in range(400_000):
        result = resolve_v2_base(hunt)
        for sample_id, (title, predicate) in wanted.items():
            if sample_id in found:
                continue
            if predicate(result):
                found[sample_id] = _pack(sample_id, title, result)
        if len(found) == len(wanted):
            break
    missing = [key for key in wanted if key not in found]
    if missing:
        raise RuntimeError(f"could not find samples {missing}")
    samples.extend(found[key] for key in ("03", "04", "05", "06", "07", "08"))
    return samples


def main() -> None:
    samples = collect_samples()
    payload = {
        "nonProduction": True,
        "usage": "DEV/TEST math-sample replay only. Not production books or LUT.",
        "mathStatus": "PHASE 2 PROVISIONAL BASE MATH",
        "seed": SEED,
        "samples": samples,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} n={len(samples)}")


if __name__ == "__main__":
    main()
