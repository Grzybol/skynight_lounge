"""One-shot micro screen for gap packs. Research only."""

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase6a_search import build_context
from skyjump_v2_phase6a1_search import decorate, make_spec, run_mix, run_tier, summarise

ctx = build_context(load_v2_config())
p = ctx["mix"]["P_scatterGe3"]
n, seed = 8000, 803
micros = [
    ("B21", {"LARGE_HILL": (21, 1), "SKI_FLYING": (35, 3), "WORLD_CUP": (46, 6), "PERFECT_V": (58, 10)}, "R-BATCH", "W-IMMEDIATE"),
    ("B23", {"LARGE_HILL": (23, 1), "SKI_FLYING": (38, 3), "WORLD_CUP": (50, 6), "PERFECT_V": (62, 10)}, "R-BATCH", "W-IMMEDIATE"),
    ("C_THIN", {"LARGE_HILL": (10, 2), "SKI_FLYING": (18, 4), "WORLD_CUP": (24, 7), "PERFECT_V": (32, 12)}, "R-DELAYED", "W-NEXT-SPIN"),
    ("C_MICRO", {"LARGE_HILL": (8, 2), "SKI_FLYING": (16, 5), "WORLD_CUP": (22, 8), "PERFECT_V": (30, 12)}, "R-DELAYED", "W-NEXT-SPIN"),
    ("C_LH2", {"LARGE_HILL": (10, 2), "SKI_FLYING": (18, 3), "WORLD_CUP": (24, 6), "PERFECT_V": (32, 10)}, "R-DELAYED", "W-NEXT-SPIN"),
    ("D20_2", {"LARGE_HILL": (20, 2), "SKI_FLYING": (34, 6), "WORLD_CUP": (44, 10), "PERFECT_V": (56, 16)}, "R-BATCH", "W-NEXT-SPIN"),
    ("D22_2", {"LARGE_HILL": (22, 2), "SKI_FLYING": (36, 6), "WORLD_CUP": (48, 10), "PERFECT_V": (60, 16)}, "R-BATCH", "W-NEXT-SPIN"),
    ("D17_3", {"LARGE_HILL": (17, 3), "SKI_FLYING": (28, 7), "WORLD_CUP": (38, 12), "PERFECT_V": (50, 18)}, "R-BATCH", "W-NEXT-SPIN"),
    ("D19_2", {"LARGE_HILL": (19, 2), "SKI_FLYING": (32, 6), "WORLD_CUP": (42, 11), "PERFECT_V": (54, 17)}, "R-BATCH", "W-NEXT-SPIN"),
    ("E25_9", {"LARGE_HILL": (25, 9), "SKI_FLYING": (42, 20), "WORLD_CUP": (54, 28), "PERFECT_V": (66, 36)}, "R-BATCH", "W-CHARGE"),
]
for name, pack, rj, wn in micros:
    spec = make_spec(f"P6A1_{name}", pack, rejump_arch=rj, wind_arch=wn)
    rows = run_mix(ctx, spec, n, seed)
    lh = run_tier(ctx, spec, "LARGE_HILL", 6000, seed + 17)
    s = decorate(spec, summarise(rows, p), p)
    lh_s = summarise(lh, p)
    print(
        f"{name:10} inc={s['incrementalPp']:6.2f} res={s['reservePp']:5.2f} "
        f"pRJ={s['pRejump']:.3f} pWK={s['pWind']:.3f} any={s['pAnyPhase6']:.3f} "
        f"LH={lh_s['pRejump']:.3f}/{lh_s['pWind']:.3f}/{lh_s['pAnyPhase6']:.3f} "
        f"med={s['medianX']:.1f} p90={s['p90X']:.1f}",
        flush=True,
    )
