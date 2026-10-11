"""Lightweight invariants for canonical SkyJump JSON. Not a heavy schema framework."""

from __future__ import annotations

from typing import Any


def validate_skyjump_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    meta = config.get("meta") or {}
    if not meta.get("gameID"):
        errors.append("meta.gameID is required")
    if int(config.get("eventSchemaVersion") or 0) < 1:
        errors.append("eventSchemaVersion must be >= 1")
    if int(meta.get("mathVersion") or 0) < 1:
        errors.append("meta.mathVersion must be >= 1")
    if float(meta.get("targetRtp") or 0) <= 0:
        errors.append("meta.targetRtp must be > 0")
    if int(config.get("bookAmountMultiplier") or 0) <= 0:
        errors.append("bookAmountMultiplier must be > 0")

    weather = config.get("weather") or []
    weather_ids = [row.get("id") for row in weather]
    if len(weather_ids) != len(set(weather_ids)):
        errors.append("weather IDs must be unique")
    for row in weather:
        if float(row.get("weight") or 0) <= 0:
            errors.append(f"weather {row.get('id')} weight must be > 0")

    hills = config.get("hills") or {}
    if "normal" not in hills:
        errors.append("default hill 'normal' is missing")
    for hill_id, hill in hills.items():
        if float(hill.get("baseDistance") or 0) <= 0:
            errors.append(f"hill {hill_id} baseDistance must be > 0")
        if float(hill.get("maxWin") or 0) <= 0:
            errors.append(f"hill {hill_id} maxWin must be > 0")
        curve = hill.get("payoutCurve") or []
        prev_max = None
        for band in curve:
            lo = float(band["minDistance"])
            hi = float(band["maxDistance"])
            if hi <= lo:
                errors.append(f"hill {hill_id} payout band not ordered: {lo}-{hi}")
            if prev_max is not None and lo < prev_max:
                errors.append(f"hill {hill_id} payout bands overlap at {lo}")
            prev_max = hi

    slots = config.get("slots") or []
    for role in slots:
        ids = [symbol.get("id") for symbol in role.get("symbols") or []]
        if len(ids) != len(set(ids)):
            errors.append(f"slot {role.get('id')} symbol IDs must be unique")
        for symbol in role.get("symbols") or []:
            if float(symbol.get("weight") or 0) <= 0:
                errors.append(f"symbol {symbol.get('id')} weight must be > 0")
            if float(symbol.get("localMultiplier") or 0) < 1:
                errors.append(f"symbol {symbol.get('id')} localMultiplier must be >= 1")

    multipliers = config.get("finalMultipliers") or {}
    for table_id, rows in multipliers.items():
        ids = [row.get("id") for row in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"multiplier table {table_id} IDs must be unique")
        for row in rows:
            if float(row.get("weight") or 0) <= 0:
                errors.append(f"multiplier {table_id}/{row.get('id')} weight must be > 0")
            if float(row.get("multiplier") or 0) < 1:
                errors.append(f"multiplier {table_id}/{row.get('id')} must be >= 1")

    miss_tables = config.get("finalMultiplierMissTables") or {}
    for table_id, rows in miss_tables.items():
        if table_id not in multipliers:
            errors.append(f"miss table {table_id} has no pay table")
        ids = [row.get("id") for row in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"miss table {table_id} IDs must be unique")
        for row in rows:
            if float(row.get("weight") or 0) <= 0:
                errors.append(f"miss multiplier {table_id}/{row.get('id')} weight must be > 0")
            if float(row.get("multiplier") or 0) < 1:
                errors.append(f"miss multiplier {table_id}/{row.get('id')} must be >= 1")

    vol = config.get("volatilityModel") or {}
    for key in ("epicBoost", "rareBoost", "uncommonBoost", "commonNerf", "minWeight", "biasClamp"):
        if key not in vol:
            errors.append(f"volatilityModel.{key} is required")

    modes = config.get("buyModes") or {}
    if "base" not in modes:
        errors.append("default buyMode 'base' is missing")
    ids = [mode.get("id") for mode in modes.values()]
    if len(ids) != len(set(ids)):
        errors.append("buyMode ids must be unique")
    for mode_id, mode in modes.items():
        if not mode.get("enabled", True):
            continue
        if float(mode.get("costMultiplier") or 0) <= 0:
            errors.append(f"buyMode {mode_id} costMultiplier is required")
        hill_id = mode.get("hillProfile")
        table_id = mode.get("multiplierProfile")
        if hill_id not in hills:
            errors.append(f"buyMode {mode_id} unknown hill {hill_id}")
        if table_id not in multipliers:
            errors.append(f"buyMode {mode_id} unknown multiplier table {table_id}")
        published = float(mode.get("maxWin") or 0)
        if published <= 0:
            errors.append(f"buyMode {mode_id} maxWin must be > 0")

    return errors


def assert_valid(config: dict[str, Any]) -> None:
    errors = validate_skyjump_config(config)
    if errors:
        raise ValueError("SkyJump config invalid:\n- " + "\n- ".join(errors))
