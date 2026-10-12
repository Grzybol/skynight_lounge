"""Phase 7C.3 — paired CRN prior-cap effect (actual triggerSpinWinX vs prior=0)."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import ConditionalBaseSampler, wr_off_config
from skyjump_v2_phase7c3_common import OUT, assert_frozen, dump_json, mean_se

LEAVES = (
    "BASE_TRIGGER_LH_WR_OFF",
    "BASE_TRIGGER_SF_WR_OFF",
    "BASE_TRIGGER_WC_WR_OFF",
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=201)
    args = ap.parse_args()
    assert_frozen()
    cfg = wr_off_config(load_v2_config())
    sampler = ConditionalBaseSampler(load_v2_config())
    out = {}
    for leaf in LEAVES:
        diffs = []
        xs_act = []
        xs_zero = []
        for i in range(args.n):
            # Common reel/feature stream via identical RNG seed + same stops
            seed = args.seed + i * 17 + hash(leaf) % 10007
            stops = sampler.sample(random.Random(seed), leaf)
            r_act = resolve_v2_round(random.Random(seed + 1), config=cfg, base_stops=stops)
            # prior=0 forces trigger win used as cap prior to 0
            r_zero = resolve_v2_round(
                random.Random(seed + 1), config=cfg, base_stops=stops, round_prior_win_x=0.0
            )
            a = float(r_act["roundWinXCapped"])
            z = float(r_zero["roundWinXCapped"])
            xs_act.append(a)
            xs_zero.append(z)
            diffs.append(a - z)
        md, sd = mean_se(diffs)
        ma, sa = mean_se(xs_act)
        mz, sz = mean_se(xs_zero)
        out[leaf] = {
            "n": args.n,
            "meanActual": ma,
            "meanPrior0": mz,
            "meanDiff": md,
            "seDiff": sd,
            "absMeanDiff": abs(md),
            "negligible": abs(md) < 0.05 and (sd * 1.96 < 0.10 if sd < float("inf") else False),
        }
        print(f"{leaf}: diff={md:.6f} se={sd:.6f} negl={out[leaf]['negligible']}", flush=True)
    dump_json(OUT / "prior_cap_crn.json", {"paired": out, "conclusion": "negligible" if all(v["negligible"] for v in out.values()) else "small_or_uncertain"})
    print("wrote prior_cap_crn.json", flush=True)


if __name__ == "__main__":
    main()
