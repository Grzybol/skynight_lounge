"""SkyJump math — loads canonical JSON config. Engine foundation, not certified RTP."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(__file__).with_name("skyjump_config.json")
FIXTURE_PATH = Path(__file__).with_name("skyjump_fixtures.json")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    from skyjump_validate import assert_valid

    assert_valid(payload)
    return payload


CONFIG = load_config()
BOOK_AMOUNT_MULTIPLIER = int(CONFIG.get("bookAmountMultiplier", 100))
EVENT_SCHEMA_VERSION = int(CONFIG.get("eventSchemaVersion", 1))
VOLATILITY = CONFIG["volatilityModel"]


def js_round(value: float, decimals: int) -> float:
    """Match JavaScript Math.round for non-negative presentation values."""
    factor = 10**decimals
    return math.floor(value * factor + 0.5) / factor


def rgs_payout_multiplier(final_win_x: float) -> int:
    """Authoritative Stake integer for this mathVersion.

    books.py / RGS docs: payoutMultiplier 100 = 1.0x nominal bet, 1150 = 11.5x.
    Conversion is Python 3 half-to-even: int(round(finalWinX * 100)).

    Do not round(finalWinX, 2) first. That is a second monetary truth.
    Stake's local RGS helper also requires payoutMultiplier % 10 == 0 (0.10x
    steps). That constraint is reported separately; this function does not
    silently quantize 0.01x math to 0.10x.
    """
    return int(round(float(final_win_x) * BOOK_AMOUNT_MULTIPLIER))


def round_book_amount(win_x: float, multiplier: int = BOOK_AMOUNT_MULTIPLIER) -> int:
    """Alias for the single RGS integer conversion. multiplier must stay 100."""
    if multiplier != BOOK_AMOUNT_MULTIPLIER:
        return int(round(float(win_x) * multiplier))
    return rgs_payout_multiplier(win_x)


def pick_weighted(items: list[dict], rng, weight_key: str = "weight") -> dict:
    total = sum(max(0.0, float(item[weight_key])) for item in items)
    if total <= 0:
        raise ValueError("Weighted table has no positive weights")
    cursor = rng.random() * total
    for item in items:
        cursor -= max(0.0, float(item[weight_key]))
        if cursor <= 0:
            return item
    return items[-1]


def lookup_payout(curve: list[dict], distance: float) -> float:
    for band in curve:
        if distance >= band["minDistance"] and distance < band["maxDistance"]:
            return float(band["baseWinX"])
    return float(curve[-1]["baseWinX"]) if curve else 0.0


def apply_volatility_bias(symbols: list[dict], volatility_bias: float) -> list[dict]:
    if volatility_bias <= 0:
        return symbols
    biased = []
    for symbol in symbols:
        rarity = symbol.get("rarity", "common")
        rare_boost = {
            "epic": float(VOLATILITY["epicBoost"]),
            "rare": float(VOLATILITY["rareBoost"]),
            "uncommon": float(VOLATILITY["uncommonBoost"]),
        }.get(rarity, 1)
        common_nerf = 1 - volatility_bias * float(VOLATILITY["commonNerf"]) if rarity == "common" else 1
        weight = max(
            float(VOLATILITY["minWeight"]),
            float(symbol["weight"]) * (1 + (rare_boost - 1) * volatility_bias) * common_nerf,
        )
        biased.append({**symbol, "weight": weight})
    return biased


def lerp(min_value: float, max_value: float, t: float) -> float:
    return min_value + (max_value - min_value) * t


def _mode_lookup() -> dict[str, dict]:
    by_key: dict[str, dict] = {}
    for mode in CONFIG["buyModes"].values():
        by_key[mode["id"]] = mode
        by_key[str(mode["id"]).upper()] = mode
        by_key[str(mode.get("rgsKey") or mode["id"]).upper()] = mode
    return by_key


MODE_LOOKUP = _mode_lookup()


def tables_for_mode(mode_key: str, hill_id: str | None = None, multiplier_table_id: str | None = None) -> dict:
    key = mode_key.upper().replace("-", "_")
    mode = dict(MODE_LOOKUP.get(key) or MODE_LOOKUP["BASE"])
    hill = hill_id or mode["hillProfile"]
    table = multiplier_table_id or mode["multiplierProfile"]
    return {
        "id": mode["id"],
        "rgsKey": mode.get("rgsKey") or mode["id"].upper(),
        "hillId": hill,
        "hillProfile": hill,
        "multiplierTableId": table,
        "multiplierProfile": table,
        "costMultiplier": float(mode["costMultiplier"]),
        "maxWin": float(mode["maxWin"]),
        "enabled": bool(mode.get("enabled", True)),
        "type": mode.get("type") or "default",
    }


def require_weather(weather_id: str) -> dict:
    for row in CONFIG["weather"]:
        if row["id"] == weather_id:
            return row
    raise KeyError(f"Unknown weather: {weather_id}")


def require_symbol(role_index: int, symbol_id: str) -> dict:
    role = CONFIG["slots"][role_index]
    for symbol in role["symbols"]:
        if symbol["id"] == symbol_id:
            return symbol
    raise KeyError(f"Unknown slot symbol: {symbol_id}")


def require_multiplier(table_id: str, multiplier_id: str) -> dict:
    for row in CONFIG["finalMultipliers"][table_id]:
        if row["id"] == multiplier_id:
            return row
    miss = (CONFIG.get("finalMultiplierMissTables") or {}).get(table_id) or []
    for row in miss:
        if row["id"] == multiplier_id:
            return row
    raise KeyError(f"Unknown final multiplier: {multiplier_id}")


def finals_for_pay_state(table_id: str, base_win_x: float) -> list[dict]:
    miss = (CONFIG.get("finalMultiplierMissTables") or {}).get(table_id)
    if base_win_x <= 0 and miss:
        return miss
    return CONFIG["finalMultipliers"][table_id]


@dataclass
class SkyJumpRound:
    bet: float
    hillId: str
    multiplierTableId: str
    weather: dict
    slots: list[dict]
    finalMultiplier: dict
    distanceTotal: float
    baseWinX: float
    localMultiplier: float
    localFactors: list[float]
    finalWinX: float
    capped: bool
    isCapped: bool
    maxWin: float
    moneyWin: float
    costMultiplier: float

    def summary(self) -> dict:
        return {
            "distanceTotal": self.distanceTotal,
            "baseWinX": self.baseWinX,
            "localMultiplier": self.localMultiplier,
            "finalMultiplier": self.finalMultiplier["multiplier"],
            "finalWinX": self.finalWinX,
            "capped": self.capped,
            "amount": round_book_amount(self.finalWinX),
            "moneyWin": self.moneyWin,
        }


def settle_round(
    *,
    bet: float,
    hill_id: str,
    multiplier_table_id: str,
    weather: dict,
    slots: list[dict],
    final_multiplier: dict,
    max_win: float | None = None,
    cost_multiplier: float = 1.0,
) -> SkyJumpRound:
    hill = CONFIG["hills"][hill_id]
    distance_total = js_round(
        max(
            0.0,
            float(hill["baseDistance"]) + float(weather["distanceDelta"]) + sum(float(slot["distanceValue"]) for slot in slots),
        ),
        1,
    )
    base_win_x = lookup_payout(hill["payoutCurve"], distance_total)
    if base_win_x <= 0:
        final_multiplier = {"id": "x0", "label": "x0", "multiplier": 0}
    local_factors = [max(1, float(slot["localMultiplier"])) for slot in slots if max(1, float(slot["localMultiplier"])) > 1]
    local_multiplier = 1.0
    for slot in slots:
        local_multiplier *= max(1.0, float(slot["localMultiplier"]))
    uncapped = js_round(base_win_x * local_multiplier * float(final_multiplier["multiplier"]), 4)
    cap = float(hill["maxWin"] if max_win is None else max_win)
    capped = uncapped > cap
    final_win_x = js_round(min(uncapped, cap), 4)
    # moneyWin is debug/presentation only. Settlement uses round_book_amount(finalWinX).
    money_win = js_round(max(0.0, bet) * final_win_x, 2)
    return SkyJumpRound(
        bet=bet,
        hillId=hill_id,
        multiplierTableId=multiplier_table_id,
        weather=weather,
        slots=slots,
        finalMultiplier=final_multiplier,
        distanceTotal=distance_total,
        baseWinX=base_win_x,
        localMultiplier=local_multiplier,
        localFactors=local_factors,
        finalWinX=final_win_x,
        capped=capped,
        isCapped=capped,
        maxWin=cap,
        moneyWin=money_win,
        costMultiplier=float(cost_multiplier),
    )


def evaluate_drawn_round(payload: dict) -> SkyJumpRound:
    weather_base = require_weather(payload["weatherId"])
    weather = {
        **weather_base,
        "temperatureC": payload["temperatureC"],
        "windSpeedMs": payload["windSpeedMs"],
        "visibilityPct": payload["visibilityPct"],
    }
    slot_ids = payload["slotIds"]
    if len(slot_ids) != 5:
        raise ValueError("Expected 5 slot ids")
    slots = []
    for index, symbol_id in enumerate(slot_ids):
        symbol = require_symbol(index, symbol_id)
        role = CONFIG["slots"][index]
        slots.append(
            {
                **symbol,
                "roleId": role["id"],
                "reelIndex": index,
                "localMultiplier": max(1, symbol["localMultiplier"]),
            }
        )
    return settle_round(
        bet=float(payload["bet"]),
        hill_id=payload["hillId"],
        multiplier_table_id=payload["multiplierTableId"],
        weather=weather,
        slots=slots,
        final_multiplier=require_multiplier(payload["multiplierTableId"], payload["finalMultiplierId"]),
        max_win=payload.get("maxWin"),
        cost_multiplier=float(payload.get("costMultiplier") or 1),
    )


def resolve_round(
    rng,
    hill_id: str = "normal",
    multiplier_table_id: str = "standard",
    bet: float = 1.0,
    max_win: float | None = None,
    cost_multiplier: float = 1.0,
) -> SkyJumpRound:
    hill = CONFIG["hills"][hill_id]
    weather_base = pick_weighted(CONFIG["weather"], rng)
    weather = {
        **weather_base,
        "temperatureC": js_round(lerp(weather_base["temperatureRange"][0], weather_base["temperatureRange"][1], rng.random()), 1),
        "windSpeedMs": js_round(lerp(weather_base["windSpeedRange"][0], weather_base["windSpeedRange"][1], rng.random()), 1),
        "visibilityPct": int(round(lerp(weather_base["visibilityRange"][0], weather_base["visibilityRange"][1], rng.random()))),
    }
    combined_bias = min(float(VOLATILITY["biasClamp"]), max(0.0, float(weather["volatilityBias"]) + float(hill["volatilityProfile"])))
    slots = []
    for index, role in enumerate(CONFIG["slots"]):
        table = apply_volatility_bias(role["symbols"], combined_bias)
        symbol = pick_weighted(table, rng)
        slots.append(
            {
                **symbol,
                "roleId": role["id"],
                "reelIndex": index,
                "localMultiplier": max(1, symbol["localMultiplier"]),
            }
        )
    distance_total = js_round(
        max(
            0.0,
            float(hill["baseDistance"]) + float(weather["distanceDelta"]) + sum(float(slot["distanceValue"]) for slot in slots),
        ),
        1,
    )
    base_win_x = lookup_payout(hill["payoutCurve"], distance_total)
    final_multiplier = pick_weighted(finals_for_pay_state(multiplier_table_id, base_win_x), rng)
    return settle_round(
        bet=bet,
        hill_id=hill_id,
        multiplier_table_id=multiplier_table_id,
        weather=weather,
        slots=slots,
        final_multiplier=final_multiplier,
        max_win=max_win,
        cost_multiplier=cost_multiplier,
    )


def win_level_for(final_win_x: float, cost_multiplier: float = 1.0) -> int:
    if final_win_x <= 0:
        return 1
    returned = final_win_x / max(float(cost_multiplier), 1e-9)
    if returned < 1:
        return 2
    if returned < 2:
        return 3
    if returned < 5:
        return 4
    if returned < 10:
        return 5
    if returned < 25:
        return 6
    if returned < 50:
        return 7
    if returned < 100:
        return 8
    if returned < 250:
        return 9
    return 10


def _common_event_fields(book_index: int, event_type: str) -> dict:
    return {"index": book_index, "type": event_type, "schemaVersion": EVENT_SCHEMA_VERSION}


def round_to_book_events(round_result: SkyJumpRound) -> list[dict]:
    amount = round_book_amount(round_result.finalWinX)
    roles = [
        {"id": role["id"], "index": role["index"], "label": role["shortLabel"], "iconKey": role["iconKey"]}
        for role in CONFIG["slots"]
    ] + [{"id": "multiplier", "index": 5, "label": "MULT", "iconKey": "multiplier"}]
    events: list[dict] = [
        {
            **_common_event_fields(0, "skyjumpWeather"),
            "weatherId": round_result.weather["id"],
            "weather": {
                "id": round_result.weather["id"],
                "label": round_result.weather["label"],
                "iconKey": round_result.weather["iconKey"],
                "temperatureC": round_result.weather["temperatureC"],
                "windSpeedMs": round_result.weather["windSpeedMs"],
                "windDirection": round_result.weather["windDirection"],
                "visibilityPct": round_result.weather["visibilityPct"],
                "distanceDelta": round_result.weather["distanceDelta"],
            },
            "winnerId": round_result.weather["id"],
        }
    ]
    for slot in round_result.slots:
        slot_index = int(slot["reelIndex"]) + 1
        events.append(
            {
                **_common_event_fields(slot_index, "skyjumpSlot"),
                "slotIndex": slot_index,
                "role": slot["roleId"],
                "symbolId": slot["id"],
                "id": slot["id"],
                "label": slot["label"],
                "distanceValue": slot["distanceValue"],
                "localMultiplier": slot["localMultiplier"],
                "rarity": slot["rarity"],
                "artKey": slot["artKey"],
                "reelIndex": slot["reelIndex"],
                "roleId": slot["roleId"],
            }
        )
    events.append(
        {
            **_common_event_fields(6, "skyjumpSlot"),
            "slotIndex": 6,
            "role": "finalMultiplier",
            "finalMultiplier": {
                "id": round_result.finalMultiplier["id"],
                "label": round_result.finalMultiplier["label"],
                "multiplier": round_result.finalMultiplier["multiplier"],
            },
            "label": round_result.finalMultiplier["label"],
            "reelIndex": 5,
            "roleId": "multiplier",
        }
    )
    events.append(
        {
            **_common_event_fields(7, "skyjumpResult"),
            "hillId": round_result.hillId,
            "hillProfile": round_result.hillId,
            "multiplierTableId": round_result.multiplierTableId,
            "multiplierProfile": round_result.multiplierTableId,
            "distanceTotal": round_result.distanceTotal,
            "baseWinX": round_result.baseWinX,
            "localMultiplier": round_result.localMultiplier,
            "localFactors": round_result.localFactors,
            "finalMultiplier": round_result.finalMultiplier["multiplier"],
            "finalWinX": round_result.finalWinX,
            "moneyWin": round_result.moneyWin,  # debug/presentation only; settlement uses amount
            "capped": round_result.capped,
            "isCapped": round_result.isCapped,
            "maxWin": round_result.maxWin,
            "costMultiplier": round_result.costMultiplier,
            "returnMultiplier": round_result.finalWinX / max(round_result.costMultiplier, 1e-9),
            "netMultiplier": (round_result.finalWinX - round_result.costMultiplier) / max(round_result.costMultiplier, 1e-9),
            "isPayHit": round_result.finalWinX > 0,
            "isBreakEven": round_result.finalWinX >= round_result.costMultiplier,
            "isProfit": round_result.finalWinX > round_result.costMultiplier,
            "amount": amount,
            "roles": roles,
            "slots": [
                {
                    "roleId": slot["roleId"],
                    "label": slot["label"],
                    "distanceValue": slot["distanceValue"],
                    "localMultiplier": slot["localMultiplier"],
                }
                for slot in round_result.slots
            ],
        }
    )
    if round_result.capped:
        events.append({"index": 8, "type": "wincap", "amount": amount})
    elif amount > 0:
        events.append(
            {
                "index": 8,
                "type": "setWin",
                "amount": amount,
                "winLevel": win_level_for(round_result.finalWinX, round_result.costMultiplier),
            }
        )
    events.append({"index": len(events), "type": "setTotalWin", "amount": amount})
    events.append({"index": len(events), "type": "finalWin", "amount": amount})
    return events


def authoritative_from_events(events: list[dict]) -> dict:
    result = next(event for event in events if event["type"] == "skyjumpResult")
    total = next(event for event in events if event["type"] == "setTotalWin")
    return {
        "distance": result["distanceTotal"],
        "baseWinX": result["baseWinX"],
        "localMultiplier": result["localMultiplier"],
        "finalMultiplier": result["finalMultiplier"],
        "finalWinX": result["finalWinX"],
        "amount": total["amount"],
    }


def resume_events(events: list[dict], after_type: str, slot_index: int | None = None) -> tuple[list[dict], list[dict]]:
    """Split a book at an interrupt point. Does not reroll."""
    split_at = 0
    for i, event in enumerate(events):
        if after_type == "skyjumpSlot" and event["type"] == "skyjumpSlot" and event.get("slotIndex") == slot_index:
            split_at = i + 1
            break
        if event["type"] == after_type and after_type != "skyjumpSlot":
            split_at = i + 1
            break
    return events[:split_at], events[split_at:]


def load_fixtures() -> list[dict]:
    if not FIXTURE_PATH.exists():
        return []
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)
