"""Live Phase 4B paying feature helpers. Builds F01-shaped candidate from config."""

from __future__ import annotations

from skyjump_v2_tokens import token_tables


def live_candidate_from_config(config: dict) -> dict:
    economy = config["featureEconomy"]
    tables = token_tables(config)
    return {
        "id": economy.get("candidateOrigin", "live"),
        "coachModelId": config.get("coachModel", {}).get("modelId", "E"),
        "maxWinX": float(economy.get("maxWinX", 50_000)),
        "gateMaxFloor": int(economy.get("gateMaxFloor", 3)),
        "mysteryResultWeights": {
            key: int(value) for key, value in economy["mysteryResultWeights"].items()
        },
        "tokenTierWeights": {str(tier): int(tables["tierWeights"][tier - 1]) for tier in range(1, 7)},
        "tokenValueWeights": {
            str(tier): {
                str(value): int(weight)
                for value, weight in zip(tables["values"][tier], tables["valueWeights"][tier], strict=True)
            }
            for tier in range(1, 7)
        },
        "thermalWeights": {str(key): int(value) for key, value in economy["thermalWeights"].items()},
        "conditionalCollectors": bool(economy.get("conditionalCollectors", False)),
    }


def has_paying_economy(config: dict) -> bool:
    return bool(config.get("featureEconomy")) and not config.get("flightTokens", {}).get("doNotAutoPay", True)
