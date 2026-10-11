"""Persist mid-spin append EV counterfactual vs live end-of-spin (measurement only)."""

from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import base_trigger_mix, simulate_bonus
from skyjump_v2_phase6b import set_mid_spin_persist_append, set_stage_selection_mode
from skyjump_v2_phase6c_certify import P_TRIGGER, _start_tier

OUT = Path(__file__).resolve().parent / "phase6c1_research"


def main(n: int = 100_000, seed: int = 6_200_000_000) -> None:
    cfg = load_v2_config()
    cand = bonus_candidate_from_config(cfg)
    pay = live_candidate_from_config(cfg)
    mix = base_trigger_mix(cfg)
    set_stage_selection_mode("W2_PURE")

    live_xs = []
    research_xs = []
    for i in range(n):
        tier = _start_tier(random.Random(seed + i), mix)
        set_mid_spin_persist_append(False)
        live = simulate_bonus(random.Random(seed + i), tier, cand, config=cfg, paying_candidate=pay)
        set_mid_spin_persist_append(True)
        research = simulate_bonus(random.Random(seed + i), tier, cand, config=cfg, paying_candidate=pay)
        set_mid_spin_persist_append(False)
        live_xs.append(live["bonusWinXCapped"])
        research_xs.append(research["bonusWinXCapped"])

    delta = statistics.fmean(research_xs) - statistics.fmean(live_xs)
    payload = {
        "n": n,
        "seed": seed,
        "liveMeanX": statistics.fmean(live_xs),
        "midSpinAppendMeanX": statistics.fmean(research_xs),
        "deltaX": delta,
        "deltaPp": delta * P_TRIGGER * 100.0,
        "action": "KEEP_LIVE",
        "note": "Positive delta means research mid-spin append is hotter than live.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "persist_ev_counterfactual.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
