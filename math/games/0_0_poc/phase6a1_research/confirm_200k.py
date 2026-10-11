"""200k confirmation for thinner in-band packs after large overshoots."""

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase6a_search import build_context
from skyjump_v2_phase6a1_search import PACKS, decorate, make_spec, run_mix, run_tier, summarise, f1_benchmark

ctx = build_context(load_v2_config())
p = ctx["mix"]["P_scatterGe3"]
n, seed = 200_000, 20260924

jobs = [
    ("F1", f1_benchmark()),
    ("B15", make_spec("B15", PACKS["B15"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE")),
    ("B1", make_spec("B1", PACKS["B1"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE")),
    ("D0", make_spec("D0", PACKS["D0"], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN")),
    ("D05", make_spec("D05", PACKS["D05"], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN")),
    ("D1", make_spec("D1", PACKS["D1"], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN")),
    ("D19_2", make_spec("D19_2", PACKS["D19_2"], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN")),
    ("E05", make_spec("E05", PACKS["E05"], rejump_arch="R-BATCH", wind_arch="W-CHARGE")),
    ("E1", make_spec("E1", PACKS["E1"], rejump_arch="R-BATCH", wind_arch="W-CHARGE")),
    ("E2", make_spec("E2", PACKS["E2"], rejump_arch="R-BATCH", wind_arch="W-CHARGE")),
    ("E0", make_spec("E0", PACKS["E0"], rejump_arch="R-BATCH", wind_arch="W-CHARGE")),
]

for name, spec in jobs:
    rows = run_mix(ctx, spec, n, seed)
    lh = run_tier(ctx, spec, "LARGE_HILL", 40_000, seed + 11)
    s = decorate(spec, summarise(rows, p), p)
    lh_s = summarise(lh, p)
    print(
        f"{name:8} inc={s['incrementalPp']:6.3f} res={s['reservePp']:5.3f} "
        f"pRJ={s['pRejump']:.4f} pWK={s['pWind']:.4f} any={s['pAnyPhase6']:.4f} "
        f"med={s['medianX']:.2f} p90={s['p90X']:.1f} p99={s['p99X']:.1f} "
        f"LH={lh_s['pRejump']:.3f}/{lh_s['pWind']:.3f}/{lh_s['pAnyPhase6']:.3f} "
        f"cap={s['pCap']:.6f} pend={s['pPendingUnused']:.4f}",
        flush=True,
    )
