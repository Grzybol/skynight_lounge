"""Schema-v2 BASE book events. Phase 4B emits paying feature events."""

from __future__ import annotations


def round_book_amount(win_x: float, multiplier: int = 100) -> int:
    if win_x != win_x or win_x in (float("inf"), float("-inf")):
        raise ValueError("non-finite win")
    return round(win_x * multiplier)


def round_to_v2_events(result: dict, *, book_amount_multiplier: int = 100, source: str = "math") -> list[dict]:
    line_win = float(result["lineWinX"])
    feature_win = float(result.get("totalFeatureWinX", 0) or 0)
    feature_raw = float(result.get("totalFeatureWinXRaw", feature_win) or 0)
    total = float(result.get("totalWinX", line_win + feature_win))
    amount = round_book_amount(total, book_amount_multiplier)
    scatter = result["scatter"]
    features = result.get("features") or {}
    paying = bool(features.get("paying"))
    events = [
        {
            "index": 0,
            "type": "skyjumpSpinStart",
            "schemaVersion": 2,
            "mode": result.get("mode", "BASE"),
            "isFreeSpin": bool(result.get("isFreeSpin", False)),
            "source": source,
            "stops": list(result["stops"]),
        },
        {
            "index": 1,
            "type": "skyjumpBoardReveal",
            "schemaVersion": 2,
            "board": result["board"],
        },
        {
            "index": 2,
            "type": "skyjumpLineWins",
            "schemaVersion": 2,
            "wins": result["wins"],
            "lineWinX": line_win,
        },
        {
            "index": 3,
            "type": "skyjumpScatterResult",
            "schemaVersion": 2,
            "positions": scatter["positions"],
            "count": scatter["count"],
            "perfectV": scatter["perfectV"],
            "trigger": scatter.get("trigger"),
            "fromBoard": scatter.get("fromBoard", "initialReveal"),
        },
    ]
    for coach in features.get("coaches") or []:
        events.append(
            {
                "index": len(events),
                "type": "skyjumpCoachSignal",
                "schemaVersion": 2,
                "coachPosition": coach["coachPosition"],
                "selectedSymbolId": coach["selectedSymbolId"],
                "selectedPositions": coach["selectedPositions"],
                "sequenceIndex": coach["sequenceIndex"],
                "noOp": bool(coach.get("noOp")),
                "reason": coach.get("reason"),
            }
        )
        if coach.get("noOp"):
            continue
        match = next(
            (
                row
                for row in features.get("transforms") or []
                if row["sequenceIndex"] == coach["sequenceIndex"]
            ),
            None,
        )
        if match:
            events.append(
                {
                    "index": len(events),
                    "type": "skyjumpMysteryTransform",
                    "schemaVersion": 2,
                    "sourceSymbolId": match["sourceSymbolId"],
                    "positions": match["positions"],
                    "sequenceIndex": match["sequenceIndex"],
                }
            )

    # 1) Resolve all Mystery identities first.
    for row in features.get("resolves") or []:
        result_type = row.get("resultType") or "FLIGHT_TOKEN"
        payload = {
            "index": len(events),
            "type": "skyjumpMysteryResolve",
            "schemaVersion": 2,
            "position": row["position"],
            "resultType": result_type,
        }
        if result_type == "FLIGHT_TOKEN":
            payload.update(
                {
                    "tokenTier": row["tokenTier"],
                    "tokenId": row["tokenId"],
                    "tokenName": row["tokenName"],
                    "tokenValueX": float(row.get("faceValueX") if row.get("faceValueX") is not None else row["tokenValueX"]),
                    "faceValueX": float(row.get("faceValueX") if row.get("faceValueX") is not None else row["tokenValueX"]),
                    "effectiveValueX": float(
                        row.get("effectiveValueX")
                        if row.get("effectiveValueX") is not None
                        else row.get("faceValueX") or row["tokenValueX"]
                    ),
                }
            )
        elif result_type == "THERMAL_LIFT":
            payload["thermalMult"] = int(row["thermalMult"])
        events.append(payload)

    # 2) Gate upgrades (sequential, math-owned replacements).
    for gate in features.get("gateEvents") or []:
        events.append(
            {
                "index": len(events),
                "type": "skyjumpGateUpgrade",
                "schemaVersion": 2,
                "position": gate["position"],
                "floorBefore": gate["floorBefore"],
                "floorAfter": gate["floorAfter"],
                "replacements": gate["replacements"],
            }
        )

    # 3) Thermal effective values (faces immutable).
    if paying:
        for reel, col in enumerate(features.get("cells") or []):
            for row_index, cell in enumerate(col):
                if cell.get("kind") != "thermal":
                    continue
                affected = []
                for tr, tc in _thermal_neighbours(reel, row_index):
                    token = features["cells"][tr][tc]
                    if token.get("kind") != "token":
                        continue
                    affected.append(
                        {
                            "reel": tr,
                            "row": tc,
                            "faceValueX": float(token["faceValueX"]),
                            "effectiveValueX": float(token["effectiveValueX"]),
                            "appliedThermals": list(token.get("appliedThermals") or []),
                        }
                    )
                events.append(
                    {
                        "index": len(events),
                        "type": "skyjumpThermalLift",
                        "schemaVersion": 2,
                        "position": {"reel": reel, "row": row_index},
                        "thermalMult": int(cell["thermalMult"]),
                        "affectedTokens": affected,
                    }
                )

    # 4) Collectors — explicit passes (Head Judge = two events).
    for collection in features.get("collections") or []:
        ctype = collection["type"]
        event_type = "skyjumpJudgeCollect" if ctype == "JUDGE" else "skyjumpHeadJudgeCollect"
        events.append(
            {
                "index": len(events),
                "type": event_type,
                "schemaVersion": 2,
                "position": collection["position"],
                "passIndex": int(collection.get("pass", 1)),
                "collectedX": float(collection["collectedX"]),
                "effectiveTokenSumX": float(
                    collection.get("effectiveTokenSumX", features.get("effectiveTokenSumX") or 0)
                ),
                "tokenContributions": list(collection.get("tokenContributions") or []),
            }
        )

    if features.get("capHit"):
        events.append(
            {
                "index": len(events),
                "type": "skyjumpCapReached",
                "schemaVersion": 2,
                "rawTotalWinX": float(features.get("totalWinXRaw") or result.get("totalWinXRaw") or total),
                "cappedTotalWinX": float(features.get("totalWinXCapped") or total),
                "capDragX": float(features.get("capDragX") or 0),
                "maxWinX": 50_000,
            }
        )

    events.extend(
        [
            {
                "index": len(events),
                "type": "skyjumpResult",
                "schemaVersion": 2,
                "totalLineWinX": line_win,
                "totalFeatureWinX": feature_win,
                "totalFeatureWinXRaw": feature_raw,
                "totalWinX": total,
                "totalWinXRaw": float(result.get("totalWinXRaw", total)),
                "amount": amount,
                "latentTokenValueX": float(features.get("latentTokenValueX") or 0),
                "tokenFloorTier": int(features.get("tokenFloorTier") or 1),
                "capHit": bool(features.get("capHit")),
            },
            {"index": len(events), "type": "setTotalWin", "amount": amount},
            {"index": len(events), "type": "finalWin", "amount": amount},
        ]
    )
    win_sum = sum(float(win["payoutX"]) for win in result["wins"])
    if abs(win_sum - line_win) > 1e-9:
        raise ValueError("totalLineWinX must equal sum of line events")
    if total < 0 or feature_win < 0:
        raise ValueError("payout cannot be negative")
    for index, event in enumerate(events):
        event["index"] = index
    return events


def _thermal_neighbours(reel: int, row: int) -> list[tuple[int, int]]:
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = reel + dr, row + dc
            if 0 <= nr < 5 and 0 <= nc < 5:
                out.append((nr, nc))
    return out
