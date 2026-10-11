"""Phase 4C multi-seed natural Monte Carlo cross-check (measurement only)."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from skyjump_v2_lines import load_v2_config
from skyjump_v2_resolve import resolve_v2_base

OUT = HERE / "phase4c_research" / "natural_multiseed.json"


def natural_mc(spins: int, seed: int, config: dict) -> dict:
    rng = random.Random(seed)
    line = 0.0
    raw = 0.0
    capped = 0.0
    drag = 0.0
    caps = 0
    max_raw = 0.0
    for _ in range(spins):
        result = resolve_v2_base(rng, config=config)
        line += float(result["lineWinX"])
        fr = float(result.get("totalFeatureWinXRaw") or 0)
        fc = float(result.get("totalFeatureWinX") or 0)
        raw += fr
        capped += fc
        features = result.get("features") or {}
        if features.get("capHit"):
            caps += 1
            drag += float(features.get("capDragX") or 0)
        max_raw = max(max_raw, float(result.get("totalWinXRaw") or 0))
    return {
        "spins": spins,
        "seed": seed,
        "lineRtp": line / spins,
        "featureRtpRaw": raw / spins,
        "featureRtpCapped": capped / spins,
        "capHits": caps,
        "capFrequency": caps / spins,
        "capDragRtp": drag / spins,
        "maxRawTotalWinX": max_raw,
    }


def summarize_seeds(rows: list[dict]) -> dict:
    capped = [r["featureRtpCapped"] for r in rows]
    raw = [r["featureRtpRaw"] for r in rows]
    line = [r["lineRtp"] for r in rows]
    caps = [r["capHits"] for r in rows]

    def stats(vals: list[float]) -> dict:
        ordered = sorted(vals)
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / max(1, len(vals) - 1)
        return {
            "mean": mean,
            "median": ordered[len(ordered) // 2],
            "min": ordered[0],
            "max": ordered[-1],
            "std": math.sqrt(var),
        }

    return {
        "nSeeds": len(rows),
        "spinsPerSeed": rows[0]["spins"] if rows else 0,
        "spinsTotal": sum(r["spins"] for r in rows),
        "line": stats(line),
        "featureRaw": stats(raw),
        "featureCapped": stats(capped),
        "capHitsTotal": sum(caps),
        "seeds": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spins", type=int, default=10_000_000)
    parser.add_argument("--seeds", type=str, default="42,43,44,45,46")
    parser.add_argument("--seed-index", type=int, default=-1, help="Run only this seed index from --seeds")
    args = parser.parse_args()
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    config = load_v2_config()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if args.seed_index >= 0:
        seed = seeds[args.seed_index]
        print(f"natural MC seed={seed} spins={args.spins}", flush=True)
        row = natural_mc(args.spins, seed, config)
        path = OUT.parent / f"natural_seed_{seed}.json"
        path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        print("wrote", path, "capped", row["featureRtpCapped"], "caps", row["capHits"])
        return

    rows = []
    for seed in seeds:
        print(f"natural MC seed={seed} spins={args.spins}", flush=True)
        row = natural_mc(args.spins, seed, config)
        rows.append(row)
        print("  capped", row["featureRtpCapped"], "raw", row["featureRtpRaw"], "caps", row["capHits"])
    summary = summarize_seeds(rows)
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    print("capped mean", summary["featureCapped"]["mean"], "std", summary["featureCapped"]["std"])


if __name__ == "__main__":
    main()
