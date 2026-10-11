"""Small SkyJump book smoke library. Not a production publish set."""

from __future__ import annotations

import json
import random
from pathlib import Path

from skyjump_resolve import evaluate_drawn_round, load_fixtures, resolve_round, round_to_book_events, tables_for_mode, CONFIG

OUT = Path(__file__).with_name("library") / "smoke"
OUT.mkdir(parents=True, exist_ok=True)


def write_jsonl(name: str, books: list[dict]) -> Path:
    path = OUT / name
    with path.open("w", encoding="utf-8") as handle:
        for book in books:
            handle.write(json.dumps(book, separators=(",", ":")) + "\n")
    return path


def main() -> None:
    fixtures = {row["id"]: row for row in load_fixtures()}
    labeled = []
    for fixture_id, payload in fixtures.items():
        result = evaluate_drawn_round(payload)
        events = round_to_book_events(result)
        labeled.append(
            {
                "id": fixture_id,
                "mode": f"{payload['hillId']}:{payload['multiplierTableId']}",
                "payoutMultiplier": result.finalWinX,
                "capped": result.capped,
                "costMultiplier": result.costMultiplier,
                "isPayHit": result.finalWinX > 0,
                "isBreakEven": result.finalWinX >= result.costMultiplier,
                "isProfit": result.finalWinX > result.costMultiplier,
                "events": events,
            }
        )
    write_jsonl("skyjump_fixture_books.jsonl", labeled)

    modes = [
        mode["rgsKey"]
        for mode in CONFIG["buyModes"].values()
        if mode.get("enabled", True)
    ]
    for mode_name in modes:
        tables = tables_for_mode(mode_name)
        books = []
        for sim in range(8):
            rng = random.Random(7 + sim)
            result = resolve_round(
                rng,
                hill_id=tables["hillId"],
                multiplier_table_id=tables["multiplierTableId"],
                bet=1.0,
                max_win=tables["maxWin"],
                cost_multiplier=tables["costMultiplier"],
            )
            events = round_to_book_events(result)
            books.append(
                {
                    "id": f"{mode_name}-{sim}",
                    "mode": mode_name,
                    "cost": tables["costMultiplier"],
                    "payoutMultiplier": result.finalWinX,
                    "events": events,
                }
            )
        path = write_jsonl(f"books_{mode_name}_smoke.jsonl", books)
        types = [event["type"] for event in books[0]["events"]]
        assert types[0] == "skyjumpWeather"
        assert types[1:7] == ["skyjumpSlot"] * 6
        print(mode_name, path.name, "events", types[:8], "n", len(books))

    print("smoke library", OUT)
    print("fixtures", [row["id"] for row in labeled])


if __name__ == "__main__":
    main()
