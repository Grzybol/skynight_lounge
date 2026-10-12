"""Phase 4A research candidates. Live Phase 3 config is never written."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from skyjump_v2_coach_search import replace_isolated_low, summarize
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reels import COACH_ID

HERE = Path(__file__).resolve().parent
PHASE3_SNAPSHOT = HERE / "phase4a2_research" / "phase3_live_config_snapshot_pre4b.json"


def research_base_config(config: dict | None = None) -> dict:
    """Research strip construction must start from pre-4B Phase 3 strips."""
    if config is not None:
        return config
    if PHASE3_SNAPSHOT.exists():
        return json.loads(PHASE3_SNAPSHOT.read_text(encoding="utf-8"))
    return load_v2_config()


PHASE3_TOKEN_TIERS = {
    "1": 840000,
    "2": 130000,
    "3": 25000,
    "4": 4500,
    "5": 492,
    "6": 8,
}
# Paying-economy research tables. Phase 3 latent EV (~6x/mystery) is not collector-safe.
# Collectors pay the full effective board sum, so face EV must sit far below Phase 3.
PAYING_TOKEN_TIERS = {
    "1": 997200,
    "2": 2200,
    "3": 450,
    "4": 100,
    "5": 42,
    "6": 8,
}
PAYING_TOKEN_RICHER = {
    "1": 994000,
    "2": 4500,
    "3": 1000,
    "4": 350,
    "5": 142,
    "6": 8,
}
PAYING_TOKEN_LEANER = {
    "1": 998000,
    "2": 1500,
    "3": 300,
    "4": 100,
    "5": 92,
    "6": 8,
}
PHASE3_VALUE_WEIGHTS = {
    "1": {"1": 5, "2": 4, "3": 3, "4": 2},
    "2": {"5": 5, "10": 3, "15": 2},
    "3": {"25": 5, "50": 3, "100": 2},
    "4": {"150": 4, "200": 3, "250": 2, "500": 1},
    "5": {"750": 4, "1000": 3, "2500": 2, "5000": 1},
    "6": {"10000": 5, "25000": 3, "50000": 1},
}
PAYING_VALUE_WEIGHTS = {
    "1": {"1": 90, "2": 3, "3": 1, "4": 1},
    "2": {"5": 22, "10": 2, "15": 1},
    "3": {"25": 20, "50": 2, "100": 1},
    "4": {"150": 14, "200": 3, "250": 2, "500": 1},
    "5": {"750": 14, "1000": 3, "2500": 2, "5000": 1},
    "6": {"10000": 8, "25000": 2, "50000": 1},
}
DEFAULT_THERMAL = {"2": 70, "3": 20, "4": 7, "5": 2, "10": 1, "20": 1}


def cleaned_base_strips(config: dict | None = None) -> list[list[str]]:
    config = research_base_config(config)
    return [[("L3" if cell == COACH_ID else cell) for cell in strip] for strip in config["reelModel"]["strips"]]


def place_coach(cleaned: list[list[str]], reels: list[int], stops: int = 1) -> list[list[str]]:
    strips = deepcopy(cleaned)
    for reel in reels:
        strips[reel] = replace_isolated_low(strips[reel], stops)
    return strips


def place_coach_extended(cleaned: list[list[str]], reel: int, length: int) -> list[str]:
    """Research-only longer strip with one Coach for intermediate frequency."""
    base = list(cleaned[reel])
    base = [("L3" if cell == COACH_ID else cell) for cell in base]
    if length < len(base):
        raise ValueError("extended length must be >= base")
    pad = ["L3"] * (length - len(base))
    strip = base + pad
    for index, symbol in enumerate(strip):
        if symbol != "L3":
            continue
        prev_s = strip[(index - 1) % length]
        next_s = strip[(index + 1) % length]
        if prev_s == COACH_ID or next_s == COACH_ID:
            continue
        if prev_s == "L3" and next_s == "L3":
            continue
        strip[index] = COACH_ID
        return strip
    strip[0] = COACH_ID
    return strip


def coach_models(config: dict | None = None) -> dict[str, dict]:
    """A = current Phase 3 (2+4). B = reel 2 only. C = mid-band via extended strip."""
    config = research_base_config(config)
    cleaned = cleaned_base_strips(config)
    paylines = config["paylines"]
    paytable = config["paytable"]["awards"]

    a_strips = place_coach(cleaned, [1, 3], 1)
    b_strips = place_coach(cleaned, [1], 1)
    # Candidate C: reel 2 normal + reel 4 longer strip (one Coach) → ~14-16% any.
    c_strips = deepcopy(cleaned)
    c_strips[1] = replace_isolated_low(c_strips[1], 1)
    extended = place_coach_extended(cleaned, 3, 80)
    for index in range(52, len(extended)):
        if extended[index] == "L3":
            extended[index] = "L2" if index % 2 == 0 else "L3"
    c_strips[3] = extended
    a_meta = summarize(a_strips, paylines, paytable)
    b_meta = summarize(b_strips, paylines, paytable)
    c_meta = summarize(c_strips, paylines, paytable)
    return {
        "A": {
            "id": "A",
            "label": "reels 2+4 (Phase 3 live)",
            "strips": a_strips,
            "meta": a_meta,
            "reels0": [1, 3],
        },
        "B": {
            "id": "B",
            "label": "reel 2 only",
            "strips": b_strips,
            "meta": b_meta,
            "reels0": [1],
        },
        "C": {
            "id": "C",
            "label": "reel 2 + extended reel 4 (research mid-band)",
            "strips": c_strips,
            "meta": c_meta,
            "reels0": [1, 3],
            "extendedReel4Length": 80,
        },
    }


def base_candidate(
    *,
    candidate_id: str,
    coach_id: str,
    mystery_weights: dict[str, int],
    token_tiers: dict[str, int] | None = None,
    token_values: dict | None = None,
    thermal_weights: dict[str, int] | None = None,
    gate_max_floor: int = 3,
    notes: str = "",
) -> dict:
    return {
        "id": candidate_id,
        "coachModelId": coach_id,
        "notes": notes,
        "maxWinX": 50_000,
        "gateMaxFloor": gate_max_floor,
        "mysteryResultWeights": mystery_weights,
        "tokenTierWeights": token_tiers or dict(PAYING_TOKEN_TIERS),
        "tokenValueWeights": token_values or deepcopy(PAYING_VALUE_WEIGHTS),
        "thermalWeights": thermal_weights or dict(DEFAULT_THERMAL),
    }


def search_space() -> list[dict]:
    """Deterministic discrete search over economy knobs."""
    mystery_sets = [
        {"FLIGHT_TOKEN": 920, "THERMAL_LIFT": 40, "GATE_UPGRADE": 3, "JUDGE": 30, "HEAD_JUDGE": 7},
        {"FLIGHT_TOKEN": 900, "THERMAL_LIFT": 45, "GATE_UPGRADE": 4, "JUDGE": 40, "HEAD_JUDGE": 11},
        {"FLIGHT_TOKEN": 885, "THERMAL_LIFT": 50, "GATE_UPGRADE": 5, "JUDGE": 60, "HEAD_JUDGE": 10},
        {"FLIGHT_TOKEN": 875, "THERMAL_LIFT": 55, "GATE_UPGRADE": 5, "JUDGE": 65, "HEAD_JUDGE": 10},
        {"FLIGHT_TOKEN": 865, "THERMAL_LIFT": 55, "GATE_UPGRADE": 5, "JUDGE": 72, "HEAD_JUDGE": 10},
        {"FLIGHT_TOKEN": 880, "THERMAL_LIFT": 50, "GATE_UPGRADE": 6, "JUDGE": 55, "HEAD_JUDGE": 10},
        {"FLIGHT_TOKEN": 890, "THERMAL_LIFT": 48, "GATE_UPGRADE": 7, "JUDGE": 50, "HEAD_JUDGE": 9},
        {"FLIGHT_TOKEN": 915, "THERMAL_LIFT": 40, "GATE_UPGRADE": 3, "JUDGE": 35, "HEAD_JUDGE": 7},
        {"FLIGHT_TOKEN": 935, "THERMAL_LIFT": 32, "GATE_UPGRADE": 2, "JUDGE": 26, "HEAD_JUDGE": 5},
        {"FLIGHT_TOKEN": 850, "THERMAL_LIFT": 60, "GATE_UPGRADE": 5, "JUDGE": 80, "HEAD_JUDGE": 12},
    ]
    token_sets = [
        ("paying", PAYING_TOKEN_TIERS),
        ("leaner", PAYING_TOKEN_LEANER),
        ("richer", PAYING_TOKEN_RICHER),
        ("p3legacy", PHASE3_TOKEN_TIERS),
    ]
    thermal_sets = [
        ("mild", {"2": 55, "3": 28, "4": 12, "5": 4, "10": 1, "20": 1}),
        ("default", DEFAULT_THERMAL),
        ("soft20", {"2": 90, "3": 55, "4": 30, "5": 16, "10": 7, "20": 1}),
        ("hot", {"2": 35, "3": 28, "4": 18, "5": 12, "10": 5, "20": 2}),
    ]

    out = []
    index = 0
    for coach_id in ("A", "B", "C"):
        for m_i, mystery in enumerate(mystery_sets):
            for t_name, tiers in token_sets:
                if t_name == "p3legacy" and coach_id == "A" and m_i > 1:
                    continue
                for th_name, thermal in thermal_sets:
                    for gate_floor in (3, 4):
                        if coach_id == "A" and t_name == "richer" and th_name == "hot":
                            continue
                        if t_name == "p3legacy" and th_name == "hot":
                            continue
                        index += 1
                        values = PAYING_VALUE_WEIGHTS if t_name != "p3legacy" else PHASE3_VALUE_WEIGHTS
                        out.append(
                            base_candidate(
                                candidate_id=f"S{index:04d}_{coach_id}_m{m_i}_{t_name}_{th_name}_g{gate_floor}",
                                coach_id=coach_id,
                                mystery_weights=mystery,
                                token_tiers=tiers,
                                token_values=values,
                                thermal_weights=thermal,
                                gate_max_floor=gate_floor,
                                notes=(
                                    f"search coach={coach_id} mystery={m_i} "
                                    f"tokens={t_name} thermal={th_name} gateMax={gate_floor}"
                                ),
                            )
                        )
    return out


def handcrafted_finalist_seeds() -> list[dict]:
    """Named seeds always evaluated. Tuned toward ~9–11pp feature RTP."""
    return [
        base_candidate(
            candidate_id="H01_B_R2",
            coach_id="B",
            mystery_weights={
                "FLIGHT_TOKEN": 875,
                "THERMAL_LIFT": 55,
                "GATE_UPGRADE": 5,
                "JUDGE": 65,
                "HEAD_JUDGE": 10,
            },
            token_tiers=PAYING_TOKEN_TIERS,
            gate_max_floor=3,
            notes="Primary: Coach B, rare Gate, moderate Judge, crushed paying tokens (~10pp screen)",
        ),
        base_candidate(
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
            gate_max_floor=3,
            notes="Coach B slightly fewer Judges than H01",
        ),
        base_candidate(
            candidate_id="H03_B_R3",
            coach_id="B",
            mystery_weights={
                "FLIGHT_TOKEN": 865,
                "THERMAL_LIFT": 55,
                "GATE_UPGRADE": 5,
                "JUDGE": 72,
                "HEAD_JUDGE": 10,
            },
            token_tiers=PAYING_TOKEN_TIERS,
            gate_max_floor=3,
            notes="Coach B higher Judge rate for feel (~11pp screen)",
        ),
        base_candidate(
            candidate_id="H04_B_gate4",
            coach_id="B",
            mystery_weights={
                "FLIGHT_TOKEN": 880,
                "THERMAL_LIFT": 50,
                "GATE_UPGRADE": 6,
                "JUDGE": 55,
                "HEAD_JUDGE": 10,
            },
            token_tiers=PAYING_TOKEN_TIERS,
            gate_max_floor=4,
            notes="Gate max floor T4 comparison under rare Gate",
        ),
        base_candidate(
            candidate_id="H05_C_mid",
            coach_id="C",
            mystery_weights={
                "FLIGHT_TOKEN": 915,
                "THERMAL_LIFT": 40,
                "GATE_UPGRADE": 3,
                "JUDGE": 35,
                "HEAD_JUDGE": 7,
            },
            token_tiers=PAYING_TOKEN_TIERS,
            gate_max_floor=3,
            notes="Mid Coach frequency (~15%) with rarer collectors",
        ),
        base_candidate(
            candidate_id="H06_A_phase3_coach",
            coach_id="A",
            mystery_weights={
                "FLIGHT_TOKEN": 935,
                "THERMAL_LIFT": 32,
                "GATE_UPGRADE": 2,
                "JUDGE": 26,
                "HEAD_JUDGE": 5,
            },
            token_tiers=PAYING_TOKEN_TIERS,
            gate_max_floor=3,
            notes="Keep Phase 3 Coach rate; collectors must be very rare → worse dead-Coach feel",
        ),
    ]


if __name__ == "__main__":
    import json

    models = coach_models()
    print(
        json.dumps(
            {
                key: {
                    "label": row["label"],
                    "pAny": row["meta"]["pAny"],
                    "pGe2": row["meta"]["pGe2"],
                    "lineRtp": row["meta"]["lineRtp"],
                    "reels0": row["reels0"],
                }
                for key, row in models.items()
            },
            indent=2,
        )
    )
    print("search_space", len(search_space()))
    print("handcrafted", [row["id"] for row in handcrafted_finalist_seeds()])
