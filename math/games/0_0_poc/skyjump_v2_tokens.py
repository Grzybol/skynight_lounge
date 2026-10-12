"""Provisional Flight Token tables. Tokens do not auto-pay in Phase 3."""

from __future__ import annotations

from skyjump_v2_reels import grain_ok

TIER_IDS = {
    1: "T1",
    2: "T2",
    3: "T3",
    4: "T4",
    5: "T5",
    6: "T6",
}
TIER_NAMES = {
    1: "ROOKIE_TOKEN",
    2: "K_POINT_TOKEN",
    3: "LARGE_HILL_TOKEN",
    4: "SKI_FLYING_TOKEN",
    5: "WORLD_CUP_TOKEN",
    6: "TOKEN_WORLD_RECORD",
}
SPECIAL_WORLD_RECORD_ID = "SPECIAL_WORLD_RECORD"
DEFAULT_VALUES = {
    1: (1, 2, 3, 4),
    2: (5, 10, 15),
    3: (25, 50, 100),
    4: (150, 200, 250, 500),
    5: (750, 1000, 2500, 5000),
    6: (10000, 25000, 50000),
}


def token_tables(config: dict) -> dict:
    tokens = config["flightTokens"]
    tiers = tokens["tiers"]
    value_weights = tokens["valueWeights"]
    order = sorted(int(key) for key in tiers)
    return {
        "doNotAutoPay": tokens.get("doNotAutoPay", True),
        "t6Id": tokens.get("t6Id", TIER_NAMES[6]),
        "specialWorldRecordId": tokens.get("specialWorldRecordId", SPECIAL_WORLD_RECORD_ID),
        "order": order,
        "ids": {tier: tiers[str(tier)]["id"] for tier in order},
        "names": {tier: tiers[str(tier)]["name"] for tier in order},
        "tierWeights": [int(tiers[str(tier)]["weight"]) for tier in order],
        "values": {tier: [int(v) for v in DEFAULT_VALUES[tier]] for tier in order},
        "valueWeights": {
            tier: [int(value_weights[str(tier)][str(value)]) for value in DEFAULT_VALUES[tier]]
            for tier in order
        },
    }


def assert_token_tables(tables: dict) -> None:
    if tables["t6Id"] == tables["specialWorldRecordId"]:
        raise ValueError("T6 token id must not equal SPECIAL_WORLD_RECORD")
    if tables["ids"][6] != "T6":
        raise ValueError("tier 6 display id must be T6")
    if tables["names"][6] != "TOKEN_WORLD_RECORD":
        raise ValueError("tier 6 name must be TOKEN_WORLD_RECORD")
    for tier, values in tables["values"].items():
        if tuple(values) != DEFAULT_VALUES[tier]:
            raise ValueError(f"tier {tier} values must stay canonical")
        if not all(grain_ok(value, 0.1) and value > 0 for value in values):
            raise ValueError(f"tier {tier} values must be 0.10x compatible")
        if any(weight <= 0 for weight in tables["valueWeights"][tier]):
            raise ValueError(f"tier {tier} value weights must be positive")
    if any(weight < 0 for weight in tables["tierWeights"]):
        raise ValueError("tier weights must be non-negative")
    if tables["tierWeights"][-1] <= 0:
        raise ValueError("T6 must remain possible")
    if sum(tables["tierWeights"]) <= 0:
        raise ValueError("empty token weights")


def sample_token(rng, tables: dict) -> dict:
    tier = rng.choices(tables["order"], weights=tables["tierWeights"], k=1)[0]
    values = tables["values"][tier]
    value = rng.choices(values, weights=tables["valueWeights"][tier], k=1)[0]
    return {
        "resultType": "FLIGHT_TOKEN",
        "tokenTier": tier,
        "tokenId": tables["ids"][tier],
        "tokenName": tables["names"][tier],
        "tokenValueX": float(value),
    }


def exact_token_value_distribution(tables: dict) -> dict:
    tier_total = float(sum(tables["tierWeights"]))
    dist: dict[float, float] = {}
    by_tier = {}
    expected = 0.0
    for tier, tier_weight in zip(tables["order"], tables["tierWeights"], strict=True):
        p_tier = tier_weight / tier_total
        values = tables["values"][tier]
        weights = tables["valueWeights"][tier]
        value_total = float(sum(weights))
        tier_ev = 0.0
        value_dist = {}
        for value, weight in zip(values, weights, strict=True):
            p = p_tier * (weight / value_total)
            dist[float(value)] = dist.get(float(value), 0.0) + p
            value_dist[str(value)] = weight / value_total
            tier_ev += (weight / value_total) * value
            expected += p * value
        by_tier[str(tier)] = {"p": p_tier, "ev": tier_ev, "values": value_dist}
    return {"expected": expected, "byValue": dist, "byTier": by_tier}


def percentile_from_dist(dist: dict[float, float], q: float) -> float:
    target = q / 100.0
    cumulative = 0.0
    last = 0.0
    for value in sorted(dist):
        cumulative += dist[value]
        last = value
        if cumulative >= target:
            return value
    return last
