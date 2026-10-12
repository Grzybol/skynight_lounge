"""Phase 4A.2 feel-refinement candidates. Live Phase 3 config is never written.

Preserves Phase 4A H02_B_R1 as an immutable benchmark reference.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from skyjump_v2_coach_search import replace_isolated_low, summarize
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase4a_candidates import (
    DEFAULT_THERMAL,
    PAYING_TOKEN_TIERS,
    PAYING_VALUE_WEIGHTS,
    base_candidate as _base4a,
    coach_models as coach_models_4a,
    research_base_config,
)
from skyjump_v2_reels import COACH_ID

HERE = Path(__file__).resolve().parent
H02_PATH = HERE / "phase4a_research" / "candidate_H02_B_R1.json"

# Feel pass: denser collectors need even leaner faces to hold ~10pp feature RTP.
FEEL_TOKEN_TIERS = {
    "1": 999400,
    "2": 400,
    "3": 120,
    "4": 40,
    "5": 32,
    "6": 8,
}
FEEL_TOKEN_LEANER = {
    "1": 999700,
    "2": 220,
    "3": 60,
    "4": 20,
    "5": 32,
    "6": 8,
}
FEEL_VALUE_WEIGHTS = {
    "1": {"1": 99, "2": 1, "3": 1, "4": 1},
    "2": {"5": 26, "10": 1, "15": 1},
    "3": {"25": 24, "50": 1, "100": 1},
    "4": {"150": 18, "200": 2, "250": 1, "500": 1},
    "5": {"750": 18, "1000": 2, "2500": 1, "5000": 1},
    "6": {"10000": 8, "25000": 2, "50000": 1},
}


def extend_freq_preserving(strip: list[str], length: int) -> list[str]:
    """Lengthen a strip by cycling its existing cells (preserves mix; avoids L3-pad RTP drift)."""
    base = list(strip)
    if length < len(base):
        raise ValueError("extended length must be >= base")
    out = list(base)
    index = 0
    while len(out) < length:
        out.append(base[index % len(base)])
        index += 1
    return out


def cleaned_base_strips(config: dict | None = None) -> list[list[str]]:
    config = research_base_config(config)
    return [[("L3" if cell == COACH_ID else cell) for cell in strip] for strip in config["reelModel"]["strips"]]


def sparse_two_reel(cleaned: list[list[str]], length_r2: int, length_r4: int) -> list[list[str]]:
    strips = deepcopy(cleaned)
    strips[1] = replace_isolated_low(extend_freq_preserving(cleaned[1], length_r2), 1)
    strips[3] = replace_isolated_low(extend_freq_preserving(cleaned[3], length_r4), 1)
    return strips


def coach_models_4a2(config: dict | None = None) -> dict[str, dict]:
    """A/B retained for compare; D/E/F = two-reel sparse freq-preserving extensions."""
    config = research_base_config(config)
    base = coach_models_4a(config)
    cleaned = cleaned_base_strips(config)
    paylines = config["paylines"]
    paytable = config["paytable"]["awards"]

    specs = {
        "D": (100, 100, "reels 2+4 sparse 100/100 (feel mid)"),
        "E": (120, 120, "reels 2+4 sparse 120/120 (feel lower Coach)"),
        "F": (90, 90, "reels 2+4 sparse 90/90 (feel higher Coach)"),
    }
    out = {
        "A": base["A"],
        "B": base["B"],
        "C": base["C"],
    }
    for key, (len2, len4, label) in specs.items():
        strips = sparse_two_reel(cleaned, len2, len4)
        meta = summarize(strips, paylines, paytable)
        out[key] = {
            "id": key,
            "label": label,
            "strips": strips,
            "meta": meta,
            "reels0": [1, 3],
            "stripLengths": {2: len2, 4: len4},
        }
    return out


def base_candidate(
    *,
    candidate_id: str,
    coach_id: str,
    mystery_weights: dict[str, int],
    token_tiers: dict[str, int] | None = None,
    token_values: dict | None = None,
    thermal_weights: dict[str, int] | None = None,
    gate_max_floor: int = 3,
    conditional_collectors: bool = False,
    mystery_no_token: dict[str, int] | None = None,
    mystery_when_token: dict[str, int] | None = None,
    notes: str = "",
) -> dict:
    row = _base4a(
        candidate_id=candidate_id,
        coach_id=coach_id,
        mystery_weights=mystery_weights,
        token_tiers=token_tiers or FEEL_TOKEN_TIERS,
        token_values=token_values or deepcopy(FEEL_VALUE_WEIGHTS),
        thermal_weights=thermal_weights or dict(DEFAULT_THERMAL),
        gate_max_floor=gate_max_floor,
        notes=notes,
    )
    row["phase"] = "4A.2"
    row["conditionalCollectors"] = bool(conditional_collectors)
    if conditional_collectors:
        row["mysteryResultWeightsNoToken"] = mystery_no_token or dict(mystery_weights)
        row["mysteryResultWeightsWhenToken"] = mystery_when_token or dict(mystery_weights)
    return row


def h02_benchmark() -> dict:
    """Frozen Phase 4A recommended candidate (benchmark only; not promoted)."""
    if H02_PATH.exists():
        row = json.loads(H02_PATH.read_text(encoding="utf-8"))
    else:
        row = _base4a(
            candidate_id="H02_B_R1",
            coach_id="B",
            mystery_weights={
                "FLIGHT_TOKEN": 885,
                "THERMAL_LIFT": 50,
                "GATE_UPGRADE": 5,
                "JUDGE": 60,
                "HEAD_JUDGE": 10,
            },
            token_tiers=PAYING_TOKEN_TIERS,
            token_values=deepcopy(PAYING_VALUE_WEIGHTS),
            gate_max_floor=3,
            notes="Phase 4A benchmark fallback",
        )
    row = dict(row)
    row["id"] = "H02_B_R1"
    row["phase"] = "4A"
    row["benchmark"] = True
    row["conditionalCollectors"] = False
    row["notes"] = "Phase 4A benchmark — do not promote; feel baseline"
    return row


def feel_handcrafted_seeds() -> list[dict]:
    """Named 4A.2 seeds: denser Judges, ultra-lean tokens, two-reel sparse Coaches."""
    return [
        h02_benchmark(),
        base_candidate(
            candidate_id="F01_E_feel",
            coach_id="E",
            mystery_weights={
                "FLIGHT_TOKEN": 855,
                "THERMAL_LIFT": 42,
                "GATE_UPGRADE": 3,
                "JUDGE": 85,
                "HEAD_JUDGE": 15,
            },
            token_tiers=FEEL_TOKEN_TIERS,
            notes="Primary feel: lower two-reel Coach E + denser Judges + ultra-lean faces",
        ),
        base_candidate(
            candidate_id="F02_E_collect",
            coach_id="E",
            mystery_weights={
                "FLIGHT_TOKEN": 845,
                "THERMAL_LIFT": 42,
                "GATE_UPGRADE": 4,
                "JUDGE": 95,
                "HEAD_JUDGE": 14,
            },
            token_tiers=FEEL_TOKEN_TIERS,
            notes="Higher-collector E variant (feel push)",
        ),
        base_candidate(
            candidate_id="F03_D_tworeel",
            coach_id="D",
            mystery_weights={
                "FLIGHT_TOKEN": 875,
                "THERMAL_LIFT": 38,
                "GATE_UPGRADE": 3,
                "JUDGE": 72,
                "HEAD_JUDGE": 12,
            },
            token_tiers=FEEL_TOKEN_LEANER,
            notes="Best mid two-reel D with leaner faces to hold RTP",
        ),
        base_candidate(
            candidate_id="F04_F_higher",
            coach_id="F",
            mystery_weights={
                "FLIGHT_TOKEN": 885,
                "THERMAL_LIFT": 35,
                "GATE_UPGRADE": 3,
                "JUDGE": 65,
                "HEAD_JUDGE": 12,
            },
            token_tiers=FEEL_TOKEN_LEANER,
            notes="Higher two-reel Coach F; collectors moderated for RTP",
        ),
        base_candidate(
            candidate_id="F05_B_collect",
            coach_id="B",
            mystery_weights={
                "FLIGHT_TOKEN": 855,
                "THERMAL_LIFT": 42,
                "GATE_UPGRADE": 3,
                "JUDGE": 85,
                "HEAD_JUDGE": 15,
            },
            token_tiers=FEEL_TOKEN_TIERS,
            notes="Single-reel B denser collectors (no multi-Coach)",
        ),
        base_candidate(
            candidate_id="F06_E_cond",
            coach_id="E",
            mystery_weights={
                "FLIGHT_TOKEN": 855,
                "THERMAL_LIFT": 42,
                "GATE_UPGRADE": 3,
                "JUDGE": 85,
                "HEAD_JUDGE": 15,
            },
            mystery_no_token={
                "FLIGHT_TOKEN": 935,
                "THERMAL_LIFT": 28,
                "GATE_UPGRADE": 3,
                "JUDGE": 26,
                "HEAD_JUDGE": 8,
            },
            mystery_when_token={
                "FLIGHT_TOKEN": 840,
                "THERMAL_LIFT": 38,
                "GATE_UPGRADE": 3,
                "JUDGE": 100,
                "HEAD_JUDGE": 19,
            },
            conditional_collectors=True,
            token_tiers=FEEL_TOKEN_TIERS,
            notes="Conditional Judge weighting research on Coach E",
        ),
        base_candidate(
            candidate_id="F07_E_safe",
            coach_id="E",
            mystery_weights={
                "FLIGHT_TOKEN": 870,
                "THERMAL_LIFT": 40,
                "GATE_UPGRADE": 3,
                "JUDGE": 75,
                "HEAD_JUDGE": 12,
            },
            token_tiers=FEEL_TOKEN_TIERS,
            notes="Safer RTP E with moderate collectors",
        ),
        base_candidate(
            candidate_id="F08_D_cond",
            coach_id="D",
            mystery_weights={
                "FLIGHT_TOKEN": 860,
                "THERMAL_LIFT": 40,
                "GATE_UPGRADE": 3,
                "JUDGE": 78,
                "HEAD_JUDGE": 19,
            },
            mystery_no_token={
                "FLIGHT_TOKEN": 930,
                "THERMAL_LIFT": 28,
                "GATE_UPGRADE": 3,
                "JUDGE": 28,
                "HEAD_JUDGE": 11,
            },
            mystery_when_token={
                "FLIGHT_TOKEN": 820,
                "THERMAL_LIFT": 40,
                "GATE_UPGRADE": 3,
                "JUDGE": 110,
                "HEAD_JUDGE": 27,
            },
            conditional_collectors=True,
            token_tiers=FEEL_TOKEN_LEANER,
            notes="Conditional collectors on mid Coach D",
        ),
    ]


def feel_search_space() -> list[dict]:
    mystery_sets = [
        {"FLIGHT_TOKEN": 870, "THERMAL_LIFT": 40, "GATE_UPGRADE": 3, "JUDGE": 75, "HEAD_JUDGE": 12},
        {"FLIGHT_TOKEN": 858, "THERMAL_LIFT": 42, "GATE_UPGRADE": 3, "JUDGE": 82, "HEAD_JUDGE": 15},
        {"FLIGHT_TOKEN": 855, "THERMAL_LIFT": 42, "GATE_UPGRADE": 3, "JUDGE": 85, "HEAD_JUDGE": 15},
        {"FLIGHT_TOKEN": 845, "THERMAL_LIFT": 42, "GATE_UPGRADE": 4, "JUDGE": 95, "HEAD_JUDGE": 14},
        {"FLIGHT_TOKEN": 875, "THERMAL_LIFT": 38, "GATE_UPGRADE": 3, "JUDGE": 72, "HEAD_JUDGE": 12},
        {"FLIGHT_TOKEN": 885, "THERMAL_LIFT": 35, "GATE_UPGRADE": 3, "JUDGE": 65, "HEAD_JUDGE": 12},
    ]
    token_sets = [("feel", FEEL_TOKEN_TIERS), ("feel_lean", FEEL_TOKEN_LEANER)]
    out = []
    index = 0
    for coach_id in ("D", "E", "F", "B"):
        for m_i, mystery in enumerate(mystery_sets):
            for t_name, tiers in token_sets:
                index += 1
                out.append(
                    base_candidate(
                        candidate_id=f"G{index:03d}_{coach_id}_m{m_i}_{t_name}",
                        coach_id=coach_id,
                        mystery_weights=mystery,
                        token_tiers=tiers,
                        gate_max_floor=3,
                        notes=f"feel-search coach={coach_id} m={m_i} tokens={t_name}",
                    )
                )
    return out


if __name__ == "__main__":
    models = coach_models_4a2()
    print(
        json.dumps(
            {
                key: {
                    "label": row["label"],
                    "pAny": row["meta"]["pAny"],
                    "pGe2": row["meta"]["pGe2"],
                    "lineRtp": row["meta"]["lineRtp"],
                    "reels0": row["reels0"],
                    "stripLengths": row.get("stripLengths"),
                }
                for key, row in models.items()
                if key in ("A", "B", "D", "E", "F")
            },
            indent=2,
        )
    )
    print("seeds", [row["id"] for row in feel_handcrafted_seeds()])
    print("search", len(feel_search_space()))
