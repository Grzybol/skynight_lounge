"""Phase 4C exact / semi-exact probability tables for live F01 (measurement only)."""

from __future__ import annotations

from skyjump_v2_phase4a_economy import RESULT_ORDER, THERMAL_MULTS
from skyjump_v2_paying import live_candidate_from_config
from skyjump_v2_tokens import DEFAULT_VALUES, token_tables


def normalize(weights: dict[str, float] | dict[int, float]) -> dict:
    total = float(sum(weights.values()))
    if total <= 0:
        raise ValueError("empty weights")
    return {key: float(value) / total for key, value in weights.items()}


def exact_mystery_result_probs(config: dict) -> dict[str, float]:
    candidate = live_candidate_from_config(config)
    raw = {label: float(candidate["mysteryResultWeights"][label]) for label in RESULT_ORDER}
    return normalize(raw)


def exact_token_tier_probs(config: dict) -> dict[int, float]:
    tables = token_tables(config)
    raw = {tier: float(tables["tierWeights"][tier - 1]) for tier in range(1, 7)}
    return normalize(raw)


def exact_token_face_probs(config: dict) -> dict[int, dict[float, float]]:
    tables = token_tables(config)
    out: dict[int, dict[float, float]] = {}
    for tier in range(1, 7):
        values = tables["values"][tier]
        weights = tables["valueWeights"][tier]
        total = float(sum(weights))
        out[tier] = {float(value): float(weight) / total for value, weight in zip(values, weights, strict=True)}
    return out


def exact_thermal_mult_probs(config: dict) -> dict[int, float]:
    candidate = live_candidate_from_config(config)
    raw = {int(mult): float(candidate["thermalWeights"][str(mult)]) for mult in THERMAL_MULTS}
    return normalize(raw)


def exact_token_ev_by_tier(config: dict) -> dict[int, float]:
    faces = exact_token_face_probs(config)
    return {tier: sum(value * prob for value, prob in dist.items()) for tier, dist in faces.items()}


def exact_flight_token_joint(config: dict) -> dict:
    """Per-Mystery: P(FLIGHT_TOKEN ∧ tier ∧ face) and marginals."""
    p_result = exact_mystery_result_probs(config)
    p_tier = exact_token_tier_probs(config)
    p_face = exact_token_face_probs(config)
    p_ft = p_result["FLIGHT_TOKEN"]
    by_tier = {}
    by_face_t6 = {}
    for tier in range(1, 7):
        by_tier[tier] = p_ft * p_tier[tier]
        if tier == 6:
            for face, p_f in p_face[6].items():
                by_face_t6[face] = p_ft * p_tier[6] * p_f
    return {
        "pFlightToken": p_ft,
        "pTierGivenFlight": p_tier,
        "pFaceGivenTier": p_face,
        "pFlightAndTier": by_tier,
        "pFlightAndT6Face": by_face_t6,
        "evFaceGivenTier": exact_token_ev_by_tier(config),
        "pMysteryResults": p_result,
        "pThermalMult": exact_thermal_mult_probs(config),
    }


def config_fingerprint(config: dict) -> dict:
    economy = config["featureEconomy"]
    tokens = config["flightTokens"]
    return {
        "candidateOrigin": economy.get("candidateOrigin"),
        "featureEconomyVersion": economy.get("featureEconomyVersion"),
        "mysteryResultWeights": dict(economy["mysteryResultWeights"]),
        "thermalWeights": dict(economy["thermalWeights"]),
        "gateMaxFloor": economy.get("gateMaxFloor"),
        "maxWinX": economy.get("maxWinX"),
        "tokenTierWeights": {str(t): tokens["tiers"][str(t)]["weight"] for t in range(1, 7)},
        "tokenValueWeights": {str(t): dict(tokens["valueWeights"][str(t)]) for t in range(1, 7)},
        "coachModelId": config.get("coachModel", {}).get("modelId"),
        "stripLengths": [len(s) for s in config["reelModel"]["strips"]],
        "coachCounts": [s.count("C") for s in config["reelModel"]["strips"]],
    }
