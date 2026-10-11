"""Phase 5A research-only bonus reel / Coach / Scatter models.

Does NOT mutate live BASE F01 strips. Builds in-memory strip variants for Free Spin tiers.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from skyjump_v2_exact import exact_line_rtp, exact_scatter_distribution, exact_symbol_window_distribution
from skyjump_v2_reels import COACH_ID, SCATTER_ID


def _clean_coaches(strips: list[list[str]]) -> list[list[str]]:
    return [[("L3" if cell == COACH_ID else cell) for cell in strip] for strip in strips]


def _place_isolated(strip: list[str], count: int, symbol: str = COACH_ID) -> list[str]:
    next_strip = list(strip)
    placed = 0
    length = len(next_strip)
    for index, cell in enumerate(next_strip):
        if placed >= count:
            break
        if cell != "L3":
            continue
        prev_s = next_strip[(index - 1) % length]
        next_s = next_strip[(index + 1) % length]
        if prev_s == symbol or next_s == symbol:
            continue
        if prev_s == "L3" and next_s == "L3":
            continue
        next_strip[index] = symbol
        placed += 1
    if placed < count:
        # Fallback: replace any L3
        for index, cell in enumerate(next_strip):
            if placed >= count:
                break
            if cell == "L3":
                next_strip[index] = symbol
                placed += 1
    if placed < count:
        raise ValueError(f"could not place {count} of {symbol}")
    return next_strip


def _adjust_scatter(strip: list[str], target_count: int) -> list[str]:
    next_strip = list(strip)
    current = sum(1 for cell in next_strip if cell == SCATTER_ID)
    if current == target_count:
        return next_strip
    if current < target_count:
        need = target_count - current
        for index, cell in enumerate(next_strip):
            if need <= 0:
                break
            if cell == "L3":
                next_strip[index] = SCATTER_ID
                need -= 1
        if need > 0:
            raise ValueError("could not add scatters")
        return next_strip
    # remove excess
    remove = current - target_count
    for index, cell in enumerate(next_strip):
        if remove <= 0:
            break
        if cell == SCATTER_ID:
            next_strip[index] = "L3"
            remove -= 1
    return next_strip


def build_bonus_strips(
    base_strips: list[list[str]],
    *,
    coach_plan: dict[int, int],
    scatter_plan: dict[int, int] | None = None,
) -> list[list[str]]:
    """coach_plan / scatter_plan map reel index -> stop count."""
    strips = _clean_coaches(deepcopy(base_strips))
    for reel, count in coach_plan.items():
        if count <= 0:
            continue
        strips[reel] = _place_isolated(strips[reel], count, COACH_ID)
    if scatter_plan is not None:
        for reel, count in scatter_plan.items():
            strips[reel] = _adjust_scatter(strips[reel], count)
    return strips


def summarize_strips(strips: list[list[str]], paylines, paytable) -> dict:
    coach_dist = exact_symbol_window_distribution(strips, COACH_ID)
    p_any = 1.0 - coach_dist.get(0, 0.0)
    scatter = exact_scatter_distribution(strips)
    p_sc3 = sum(prob for count, prob in scatter.items() if count >= 3)
    line = exact_line_rtp(strips, paylines, paytable)["lineRtp"]
    return {
        "pAnyCoach": p_any,
        "pCoachGe2": sum(prob for count, prob in coach_dist.items() if count >= 2),
        "pScatterGe3": p_sc3,
        "lineRtp": line,
        "coachDist": {str(k): v for k, v in sorted(coach_dist.items()) if v},
        "scatterDist": {str(k): v for k, v in sorted(scatter.items()) if k >= 1 and v},
    }


# Named bonus reel families used by Phase 5A search.
# BASE Coach E: reels 1+3 have 1 C each on 120-stop strips → P(any)≈8.16%.
# Scatter BASE: [1,2,1,2,1] → P(≥3)≈0.65297%.

REEL_FAMILIES: dict[str, dict] = {
    # Scatter density notes (approx P(≥3) → P(≥1 upgrade in 10 spins)):
    #   BASE [1,2,1,2,1] ≈ 0.653% → ~6.3%
    #   Soft [1,1,1,1,1] ≈ 0.33% → ~3.3% (too rare)
    #   Mid+ [1,3,1,2,1] / [2,2,1,2,1] ≈ 1.0–1.5% → ~10–14% (target band)
    #   Hot  [2,3,1,3,1] ≈ 2%+ → ~18–22%
    "LH_C2_Sbase": {
        "coach_plan": {1: 2, 3: 2},
        "scatter_plan": {0: 1, 1: 2, 2: 1, 3: 2, 4: 1},
    },
    "LH_C2_Smid": {
        "coach_plan": {1: 2, 3: 2},
        "scatter_plan": {0: 1, 1: 3, 2: 1, 3: 2, 4: 1},
    },
    "LH_C2_Shot": {
        "coach_plan": {1: 2, 3: 2},
        "scatter_plan": {0: 2, 1: 3, 2: 1, 3: 3, 4: 1},
    },
    "LH_C3_Smid": {
        "coach_plan": {1: 3, 3: 2},
        "scatter_plan": {0: 1, 1: 3, 2: 1, 3: 2, 4: 1},
    },
    "LH_C2r124_Smid": {
        "coach_plan": {1: 2, 2: 1, 3: 2},
        "scatter_plan": {0: 1, 1: 3, 2: 1, 3: 2, 4: 1},
    },
    # Ski Flying
    "SF_C3_Smid": {
        "coach_plan": {1: 3, 3: 3},
        "scatter_plan": {0: 1, 1: 3, 2: 1, 3: 2, 4: 1},
    },
    "SF_C3_Shot": {
        "coach_plan": {1: 3, 3: 3},
        "scatter_plan": {0: 2, 1: 3, 2: 1, 3: 3, 4: 1},
    },
    # World Cup
    "WC_C4_Smid": {
        "coach_plan": {1: 4, 3: 3},
        "scatter_plan": {0: 1, 1: 3, 2: 1, 3: 2, 4: 1},
    },
    "WC_C4_Shot": {
        "coach_plan": {1: 4, 3: 3},
        "scatter_plan": {0: 2, 1: 3, 2: 1, 3: 3, 4: 1},
    },
    # Perfect V (guarantee still forces ≥1 Coach activation)
    "PV_C5_Smid": {
        "coach_plan": {1: 5, 3: 4},
        "scatter_plan": {0: 1, 1: 3, 2: 1, 3: 2, 4: 1},
    },
    "PV_C6_Shot": {
        "coach_plan": {1: 5, 2: 1, 3: 5},
        "scatter_plan": {0: 2, 1: 3, 2: 1, 3: 3, 4: 1},
    },
}


def materialize_family(base_strips: list[list[str]], family_id: str) -> list[list[str]]:
    spec = REEL_FAMILIES[family_id]
    return build_bonus_strips(
        base_strips,
        coach_plan=spec["coach_plan"],
        scatter_plan=spec["scatter_plan"],
    )


def list_families() -> Iterable[str]:
    return REEL_FAMILIES.keys()
