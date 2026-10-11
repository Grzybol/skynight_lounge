"""Final large confirm on seed 20260923 for in-band 6A.1 candidates."""

from __future__ import annotations

import json
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase6a_search import build_context
from skyjump_v2_phase6a1_large import paired_material
from skyjump_v2_phase6a1_search import (
    OUT,
    PACKS,
    decorate,
    make_spec,
    run_mix,
    run_tier,
    summarise,
)

SEED = 20260923


def main() -> None:
    ctx = build_context(load_v2_config())
    p = ctx["mix"]["P_scatterGe3"]
    OUT.mkdir(exist_ok=True)
    path = OUT / "large_final.jsonl"
    if path.exists():
        path.unlink()

    # Thinner D: R-BATCH + W-NEXT with C_LH2 weights, and rejump-only lift.
    d_clh2 = make_spec(
        "P6A1_D_RBATCH_CLH2",
        PACKS["C_LH2"],
        rejump_arch="R-BATCH",
        wind_arch="W-NEXT-SPIN",
    )
    d_rj14 = make_spec(
        "P6A1_D_RJ14_W1",
        {
            "LARGE_HILL": (14, 1),
            "SKI_FLYING": (24, 3),
            "WORLD_CUP": (32, 6),
            "PERFECT_V": (42, 10),
        },
        rejump_arch="R-BATCH",
        wind_arch="W-NEXT-SPIN",
    )
    jobs = [
        ("mix", make_spec("P6A1_B_B1", PACKS["B1"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE"), 1_000_000, None),
        ("mix", make_spec("P6A1_E_E1", PACKS["E1"], rejump_arch="R-BATCH", wind_arch="W-CHARGE"), 1_000_000, None),
        ("mix", d_clh2, 500_000, None),
        ("mix", d_rj14, 500_000, None),
        ("mix", make_spec("P6A1_E_E05", PACKS["E05"], rejump_arch="R-BATCH", wind_arch="W-CHARGE"), 500_000, None),
        ("tier", make_spec("P6A1_E_E1", PACKS["E1"], rejump_arch="R-BATCH", wind_arch="W-CHARGE"), 100_000, "LARGE_HILL"),
        ("tier", make_spec("P6A1_B_B1", PACKS["B1"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE"), 80_000, "LARGE_HILL"),
        ("tier", d_clh2, 60_000, "LARGE_HILL"),
        ("paired", make_spec("P6A1_E_E1", PACKS["E1"], rejump_arch="R-BATCH", wind_arch="W-CHARGE"), 100_000, None),
        ("paired", make_spec("P6A1_B_B1", PACKS["B1"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE"), 50_000, None),
    ]

    for kind, spec, n, tier in jobs:
        if kind == "paired":
            stats = {"id": spec.id, "kind": "paired", "tier": None, **paired_material(ctx, spec, n, SEED)}
            stats["rejumpArch"] = spec.rejump_arch
            stats["windArch"] = spec.wind_arch
            print(
                f"FINAL {stats['id']} paired n={n} pMat5={stats['pMaterialPlus5Paired']:.4f} "
                f"meanDelta={stats['meanDeltaX']:.3f}",
                flush=True,
            )
        elif kind == "mix":
            rows = run_mix(ctx, spec, n, SEED)
            stats = decorate(spec, summarise(rows, p), p)
            stats["kind"] = "mix"
            stats["tier"] = None
            print(
                f"FINAL {stats['id']} mix n={n} inc={stats['incrementalPp']:.3f} res={stats['reservePp']:.3f} "
                f"pRJ={stats['pRejump']:.4f} pWK={stats['pWind']:.4f} any={stats['pAnyPhase6']:.4f} "
                f"med={stats['medianX']:.2f} p90={stats['p90X']:.1f} p99={stats['p99X']:.1f} "
                f"cap={stats['pCap']:.6f} pend={stats['pPendingUnused']:.4f} "
                f"ev={stats['meanEvents']:.1f}/{stats['p99Events']:.0f}",
                flush=True,
            )
        else:
            rows = run_tier(ctx, spec, tier, n, SEED + 11)
            stats = decorate(spec, summarise(rows, p), p)
            stats["kind"] = "tier"
            stats["tier"] = tier
            print(
                f"FINAL {stats['id']} tier {tier} n={n} "
                f"LH rj/wk/any/both={stats['pRejump']:.4f}/{stats['pWind']:.4f}/"
                f"{stats['pAnyPhase6']:.4f}/{stats['pBoth']:.4f} "
                f"med={stats['medianX']:.2f} p90={stats['p90X']:.1f}",
                flush=True,
            )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(stats) + "\n")


if __name__ == "__main__":
    main()
