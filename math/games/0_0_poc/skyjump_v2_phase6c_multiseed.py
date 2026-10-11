"""Multi-seed Phase 6C unpaired+paired using live resolver. Measurement only."""

from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase6c_certify import BASELINE_MEAN, P_TRIGGER, BASE_RTP, cfg_off, run_mix_stats, _start_tier
from skyjump_v2_phase5a_engine import base_trigger_mix, simulate_bonus

OUT = Path(__file__).resolve().parent / "phase6c_research"


def agg(xs):
    m = statistics.fmean(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    se = sd / math.sqrt(len(xs)) if xs else 0.0
    return {
        "mean": m,
        "median": statistics.median(xs),
        "std": sd,
        "se": se,
        "min": min(xs),
        "max": max(xs),
        "ci95": [m - 1.96 * se, m + 1.96 * se],
    }


def main():
    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    off_cfg = cfg_off(cfg)
    off_cand = bonus_candidate_from_config(off_cfg)
    mix = base_trigger_mix(cfg)

    # Seed 20260925: reuse Phase 6B 1M unpaired if present
    unpaired = []
    live_path = Path(__file__).resolve().parent / "phase6b_research" / "live_validate.json"
    if live_path.exists():
        live = json.loads(live_path.read_text(encoding="utf-8"))
        mean_x = live["phase6"]["meanX"]
        unpaired.append(
            {
                "seed": live["seed"],
                "n": live["n"],
                "meanX": mean_x,
                "incrementalPp": (mean_x - BASELINE_MEAN) * P_TRIGGER * 100.0,
                "pCap": live["phase6"].get("pCap"),
                "meanCapDrag": live["phase6"].get("meanCapDrag"),
                "source": "phase6b_live_validate",
            }
        )
        print("imported 1M seed", live["seed"], "inc", unpaired[-1]["incrementalPp"], flush=True)

    # Spaced seeds so Random(seed+i) streams do not overlap across seeds.
    extra_seeds = [2_026_092_600, 3_026_092_600, 4_026_092_600, 5_026_092_600]
    n_each = 200_000
    for seed in extra_seeds:
        print(f"unpaired seed={seed} n={n_each}", flush=True)
        u = run_mix_stats(cfg, cand, pay, n_each, seed, mode="live")
        unpaired.append(u)
        print(f"  mean={u['meanX']:.4f} inc={u['incrementalPp']:.3f}", flush=True)

    paired = []
    # Include prior 6B paired for seed 20260925 (unique stream family)
    if live_path.exists():
        live = json.loads(live_path.read_text(encoding="utf-8"))
        if "paired" in live:
            paired.append(
                {
                    "seed": live["seed"],
                    "n": live["paired"]["n"],
                    "offMean": live["paired"]["featureOffMeanX"],
                    "onMean": live["paired"]["phase6MeanX"],
                    "deltaX": live["paired"]["pairedDeltaX"],
                    "incrementalPp": live["paired"]["pairedIncrementalPp"],
                    "source": "phase6b_live_validate",
                }
            )

    paired_n = 100_000
    # Spaced far from 20260925..20260925+200000 and from each other
    for seed in [6_026_092_600, 7_026_092_600, 8_026_092_600, 9_026_092_600]:
        print(f"paired seed={seed} n={paired_n}", flush=True)
        deltas = []
        for i in range(paired_n):
            tier = _start_tier(random.Random(seed + i), mix)
            off = simulate_bonus(random.Random(seed + i), tier, off_cand, config=off_cfg, paying_candidate=pay)
            on = simulate_bonus(random.Random(seed + i), tier, cand, config=cfg, paying_candidate=pay)
            deltas.append(on["bonusWinXCapped"] - off["bonusWinXCapped"])
        inc = statistics.fmean(deltas) * P_TRIGGER * 100.0
        paired.append({"seed": seed, "n": paired_n, "deltaX": statistics.fmean(deltas), "incrementalPp": inc})
        print(f"  paired pp={inc:.3f}", flush=True)

    incs = [u["incrementalPp"] for u in unpaired]
    pps = [p["incrementalPp"] for p in paired]
    payload = {
        "unpaired": unpaired,
        "paired": paired,
        "unpairedAgg": agg(incs),
        "pairedAgg": agg(pps),
        "certifiedSuggestion": {
            "prefer": "pairedAgg.mean",
            "gameRtp": BASE_RTP + BASELINE_MEAN * P_TRIGGER * 100.0 + statistics.fmean(pps),
            "note": "gameRtp uses certified Phase5B core + paired Phase6 incremental",
        },
    }
    path = OUT / "multiseed.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", path)
    print(json.dumps({"unpairedAgg": payload["unpairedAgg"], "pairedAgg": payload["pairedAgg"]}, indent=2))


if __name__ == "__main__":
    main()
