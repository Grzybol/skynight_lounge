"""Natural multi-seed MC cross-check for Phase 7C.2."""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import random
import statistics
from pathlib import Path

from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config

HERE = Path(__file__).resolve().parent
OUT = HERE / "phase7c2_research"


def _chunk(args):
    seed0, n = args
    cfg = load_v2_config()
    xs = []
    for i in range(n):
        xs.append(float(resolve_v2_round(random.Random(seed0 + i), config=cfg)["roundWinXCapped"]))
    return xs


def main():
    mp.freeze_support()
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = (11, 22, 33, 44, 55)
    n_per = 25_000
    jobs = [(s * 1_000_003, n_per) for s in seeds]
    with mp.Pool(processes=5) as pool:
        parts = pool.map(_chunk, jobs)
    means = [statistics.fmean(p) * 100 for p in parts]
    all_x = [x for p in parts for x in p]
    mean = statistics.fmean(all_x) * 100
    se = math.sqrt(statistics.pvariance(all_x) / len(all_x)) * 100
    auth = json.loads((OUT / "base_rebuild.json").read_text(encoding="utf-8"))["authoritativeRtpPct"]
    out = {
        "seeds": list(seeds),
        "nPer": n_per,
        "seedMeansPct": means,
        "meanPct": mean,
        "sePp": se,
        "ci95": [mean - 1.96 * se, mean + 1.96 * se],
        "stdAcrossSeeds": statistics.pstdev(means),
        "authPct": auth,
        "authInsideCi": (mean - 1.96 * se) <= auth <= (mean + 1.96 * se),
    }
    (OUT / "natural_mc.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
