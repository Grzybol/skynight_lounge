"""Re-measure the promoted live Free Spin candidate. Direct start states, not BASE farming."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skyjump_v2_freespins import bonus_candidate_from_config
from skyjump_v2_lines import load_v2_config
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_phase5a_engine import TIERS, base_trigger_mix
from skyjump_v2_phase5a_finalists import run_mix_weighted
from skyjump_v2_phase5a_search import run_start_tier_batch

OUT = Path(__file__).resolve().parent / "phase5b_research"
OUT.mkdir(exist_ok=True)


def main() -> None:
    n_mix = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    n_tier = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
    config = load_v2_config()
    paying = live_candidate_from_config(config)
    candidate = bonus_candidate_from_config(config)
    mix = base_trigger_mix(config)
    mix_stats = run_mix_weighted(
        candidate, n=n_mix, seed=20260921, config=config, paying=paying, mix=mix
    )
    per_tier = {}
    for index, tier in enumerate(TIERS):
        per_tier[tier] = run_start_tier_batch(
            candidate,
            tier,
            n=n_tier,
            seed=20260921 + index * 100_003,
            config=config,
            paying=paying,
        )
        print(
            f"{tier} mean={per_tier[tier]['meanX']:.2f} "
            f"reachSF={per_tier[tier]['pReach']['SKI_FLYING']:.4f} "
            f"WC={per_tier[tier]['pReach']['WORLD_CUP']:.4f} "
            f"PV={per_tier[tier]['pReach']['PERFECT_V']:.4f}",
            flush=True,
        )
    print(
        f"weighted={mix_stats['meanX']:.4f} fsPp={mix_stats['fsRtpPp']:.4f} "
        f"reserve={mix_stats['futureReservePp']:.4f} spins={mix_stats['meanSpins']:.3f} "
        f"max={mix_stats['maxSpinsObserved']}",
        flush=True,
    )
    payload = {"mixWeighted": mix_stats, "perTier": per_tier, "nMix": n_mix, "nTier": n_tier}
    path = OUT / f"live_mix{n_mix}_tier{n_tier}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
