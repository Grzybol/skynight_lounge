"""Large-sample Phase 6A.1 finalists. Research only. Does not write live config.

Finalists (post screen / micro):
  A  F1 benchmark — R-DELAYED + W-IMMEDIATE
  B  B23 — best R-BATCH + W-IMMEDIATE in/near band
  C  C_LH2 — best R-DELAYED + W-NEXT-SPIN in band
  D  D17_3 — best R-BATCH + W-NEXT-SPIN visibility in band
  E  E25_9 — best R-BATCH + W-CHARGE in band
  R  CTRL R-BATCH + W-NEXT at F1 weights — reserve-max architecture control
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase6a_search import _kwargs, _start_tier, build_context, table_for
from skyjump_v2_phase6a1_engine import Phase6A1Spec, simulate_phase6a1_bonus
from skyjump_v2_phase6a1_search import (
    OUT,
    PACKS,
    decorate,
    f1_benchmark,
    make_spec,
    run_mix,
    run_tier,
    summarise,
)
from skyjump_v2_phase5a_engine import TIERS

SEED = 20260923


def blank_spec() -> Phase6A1Spec:
    """Phase 5B research proxy: no Rejump / Wind Mystery mass."""
    pack = {tier: (0, 0) for tier in TIERS}
    return make_spec("P6A1_BLANK_P5B", pack, rejump_arch="R-DELAYED", wind_arch="W-IMMEDIATE")


def paired_material(ctx: dict, spec: Phase6A1Spec, n: int, seed: int) -> dict:
    """Same-stream Phase 5B blank vs candidate; P(candidate - blank >= 5x)."""
    mix = ctx["mix"]
    call = _kwargs(ctx)
    blank = blank_spec()
    deltas = []
    material = 0
    for index in range(n):
        tier = _start_tier(random.Random(seed + index), mix)
        base = simulate_phase6a1_bonus(random.Random(seed + index), tier, blank, **call)
        cand = simulate_phase6a1_bonus(random.Random(seed + index), tier, spec, **call)
        delta = cand["capped"] - base["capped"]
        deltas.append(delta)
        if delta >= 5.0:
            material += 1
    return {
        "n": n,
        "pMaterialPlus5Paired": material / n,
        "meanDeltaX": sum(deltas) / n,
        "pAnyPositiveDelta": sum(1 for d in deltas if d > 1e-9) / n,
    }


def finalist_specs() -> dict[str, Phase6A1Spec]:
    return {
        "A": f1_benchmark(),
        "B": make_spec("P6A1_B_B23", PACKS["B23"], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE"),
        "C": make_spec("P6A1_C_CLH2", PACKS["C_LH2"], rejump_arch="R-DELAYED", wind_arch="W-NEXT-SPIN"),
        "D": make_spec("P6A1_D_D17_3", PACKS["D17_3"], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN"),
        "E": make_spec("P6A1_E_E25_9", PACKS["E25_9"], rejump_arch="R-BATCH", wind_arch="W-CHARGE"),
        "R": make_spec(
            "P6A1_RESERVE_RBATCH_WNEXT",
            PACKS["CTRL_F1"],
            rejump_arch="R-BATCH",
            wind_arch="W-NEXT-SPIN",
        ),
    }


def jobs_for(worker: str):
    specs = finalist_specs()
    if worker == "A":
        # Top + runner-up at 1M; F1 + D (R-BATCH + W-NEXT) are the primary duel.
        return [
            ("mix", specs["A"], 1_000_000, SEED, None),
            ("mix", specs["D"], 1_000_000, SEED, None),
            ("tier", specs["A"], 100_000, SEED + 11, "LARGE_HILL"),
            ("tier", specs["D"], 100_000, SEED + 11, "LARGE_HILL"),
            ("paired", specs["D"], 100_000, SEED, None),
            ("paired", specs["A"], 50_000, SEED, None),
        ]
    if worker == "B":
        return [
            ("mix", specs["B"], 500_000, SEED, None),
            ("mix", specs["C"], 500_000, SEED, None),
            ("mix", specs["E"], 500_000, SEED, None),
            ("mix", specs["R"], 500_000, SEED, None),
            ("tier", specs["B"], 60_000, SEED + 11, "LARGE_HILL"),
            ("tier", specs["C"], 60_000, SEED + 11, "LARGE_HILL"),
            ("tier", specs["E"], 60_000, SEED + 11, "LARGE_HILL"),
            ("tier", specs["D"], 40_000, SEED + 11, "SKI_FLYING"),
            ("paired", specs["E"], 80_000, SEED, None),
            ("paired", specs["B"], 50_000, SEED, None),
        ]
    # Worker T: forced-ish tail slice via high seed count on hot tiers for D/E/F1.
    return [
        ("tier", specs["A"], 80_000, SEED + 101, "PERFECT_V"),
        ("tier", specs["D"], 80_000, SEED + 101, "PERFECT_V"),
        ("tier", specs["E"], 80_000, SEED + 101, "PERFECT_V"),
        ("tier", specs["A"], 80_000, SEED + 201, "WORLD_CUP"),
        ("tier", specs["D"], 80_000, SEED + 201, "WORLD_CUP"),
        ("tier", specs["E"], 80_000, SEED + 201, "WORLD_CUP"),
    ]


def main() -> None:
    worker = sys.argv[1] if len(sys.argv) > 1 else "A"
    # Optional override: python ... A B23 C_LH2 D17_3 E25_9 CTRL_F1
    if len(sys.argv) > 2:
        b_id, c_id, d_id, e_id, r_id = sys.argv[2:7]

        def finalist_specs_override() -> dict[str, Phase6A1Spec]:
            return {
                "A": f1_benchmark(),
                "B": make_spec(f"P6A1_B_{b_id}", PACKS[b_id], rejump_arch="R-BATCH", wind_arch="W-IMMEDIATE"),
                "C": make_spec(f"P6A1_C_{c_id}", PACKS[c_id], rejump_arch="R-DELAYED", wind_arch="W-NEXT-SPIN"),
                "D": make_spec(f"P6A1_D_{d_id}", PACKS[d_id], rejump_arch="R-BATCH", wind_arch="W-NEXT-SPIN"),
                "E": make_spec(f"P6A1_E_{e_id}", PACKS[e_id], rejump_arch="R-BATCH", wind_arch="W-CHARGE"),
                "R": make_spec(
                    f"P6A1_RESERVE_{r_id}",
                    PACKS[r_id],
                    rejump_arch="R-BATCH",
                    wind_arch="W-NEXT-SPIN",
                ),
            }

        global finalist_specs  # noqa: PLW0603
        finalist_specs = finalist_specs_override  # type: ignore[assignment]

    ctx = build_context(load_v2_config())
    p_trigger = ctx["mix"]["P_scatterGe3"]
    OUT.mkdir(exist_ok=True)
    path = OUT / f"large_{worker}.jsonl"
    if path.exists():
        path.unlink()
    for kind, spec, n, seed, tier in jobs_for(worker):
        if kind == "paired":
            stats = {"id": spec.id, "kind": "paired", "tier": None, **paired_material(ctx, spec, n, seed)}
            stats["rejumpArch"] = spec.rejump_arch
            stats["windArch"] = spec.wind_arch
        elif kind == "mix":
            rows = run_mix(ctx, spec, n, seed)
            stats = decorate(spec, summarise(rows, p_trigger), p_trigger)
            stats["kind"] = "mix"
            stats["tier"] = None
        else:
            rows = run_tier(ctx, spec, tier, n, seed)
            stats = decorate(spec, summarise(rows, p_trigger), p_trigger)
            stats["kind"] = "tier"
            stats["tier"] = tier
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(stats) + "\n")
        if kind == "paired":
            print(
                f"{worker} {stats['id']} paired n={n} "
                f"pMat5={stats['pMaterialPlus5Paired']:.4f} meanDelta={stats['meanDeltaX']:.3f}",
                flush=True,
            )
        else:
            print(
                f"{worker} {stats['id']} {kind} {tier or 'MIX'} n={n} "
                f"inc={stats['incrementalPp']:.3f} res={stats['reservePp']:.3f} "
                f"pRJ={stats['pRejump']:.4f} pWK={stats['pWind']:.4f} any={stats['pAnyPhase6']:.4f} "
                f"med={stats['medianX']:.2f} p90={stats['p90X']:.1f} p99={stats['p99X']:.1f} "
                f"cap={stats['pCap']:.6f} pend={stats.get('pPendingUnused', 0):.4f}",
                flush=True,
            )


if __name__ == "__main__":
    main()
