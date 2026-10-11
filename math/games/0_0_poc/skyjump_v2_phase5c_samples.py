"""Deterministic DEV bonus books for /dev-preview. Does not retune live weights."""

from __future__ import annotations

import json
import random
from pathlib import Path

from skyjump_v2_exact import scatter_on_board
from skyjump_v2_freespins import bonus_candidate_from_config, resolve_v2_round
from skyjump_v2_lines import evaluate_paylines, load_v2_config
from skyjump_v2_reels import board_from_stops, visible_window

HERE = Path(__file__).resolve().parent
OUT = HERE / "skyjump_v2_bonus_samples.json"
PV_ROWS = (0, 1, 2, 1, 0)


def scatter_rows(strip: list[str], stop: int) -> list[int]:
    window = visible_window(strip, stop)
    return [row for row, symbol in enumerate(window) if symbol == "S"]


def catalog(strips: list[list[str]]) -> list[dict[int, list[int]]]:
    tables: list[dict[int, list[int]]] = []
    for strip in strips:
        groups: dict[int, list[int]] = {}
        for stop in range(len(strip)):
            count = len(scatter_rows(strip, stop))
            groups.setdefault(count, []).append(stop)
        tables.append(groups)
    return tables


def first_stop(groups: dict[int, list[int]], count: int) -> int:
    choices = groups.get(count) or []
    if not choices:
        raise RuntimeError(f"no stop with {count} scatters")
    return choices[0]


def stops_for_exact_count(strips: list[list[str]], count: int, *, perfect_v: bool) -> list[int]:
    groups = catalog(strips)
    if perfect_v:
        chosen = []
        for reel, strip in enumerate(strips):
            found = None
            for stop in range(len(strip)):
                rows = scatter_rows(strip, stop)
                if rows == [PV_ROWS[reel]]:
                    found = stop
                    break
            if found is None:
                raise RuntimeError(f"reel {reel} has no Perfect V row")
            chosen.append(found)
        board = board_from_stops(strips, chosen)
        scatter = scatter_on_board(board, "S", PV_ROWS)
        if not scatter["perfectV"]:
            raise RuntimeError("Perfect V stops did not form the pattern")
        return chosen

    # Prefer one scatter on `count` distinct reels and zero on the rest.
    from itertools import combinations

    for combo in combinations(range(5), count):
        chosen = []
        ok = True
        for reel in range(5):
            need = 1 if reel in combo else 0
            if need not in groups[reel]:
                ok = False
                break
            chosen.append(first_stop(groups[reel], need))
        if not ok:
            continue
        board = board_from_stops(strips, chosen)
        scatter = scatter_on_board(board, "S", PV_ROWS)
        if scatter["count"] == count and not scatter["perfectV"]:
            return chosen
    raise RuntimeError(f"no exact-{count} scatter stops")


def quiet_stop(strips: list[list[str]]) -> list[int]:
    groups = catalog(strips)
    return [first_stop(groups[reel], 0) for reel in range(5)]


def upgrade_stop(strips: list[list[str]]) -> list[int]:
    groups = catalog(strips)
    # 1+1+1 on the first three reels that can show one scatter.
    from itertools import combinations

    for combo in combinations(range(5), 3):
        chosen = []
        ok = True
        for reel in range(5):
            need = 1 if reel in combo else 0
            if need not in groups[reel]:
                ok = False
                break
            chosen.append(first_stop(groups[reel], need))
        if not ok:
            continue
        board = board_from_stops(strips, chosen)
        if scatter_on_board(board, "S", PV_ROWS)["count"] >= 3:
            return chosen
    raise RuntimeError("no upgrade stops")


def play(config, base_stops, decide, *, prior=None, seed=5):
    def next_fs_stops(state):
        return decide(state)

    return resolve_v2_round(
        random.Random(seed),
        config=config,
        base_stops=base_stops,
        next_fs_stops=next_fs_stops,
        round_prior_win_x=prior,
    )


def quiet_decide(tables):
    def decide(state):
        return tables[state.bonusTier]["quiet"]

    return decide


def upgrade_then_quiet(tables, upgrades: int):
    left = {"n": upgrades}

    def decide(state):
        if left["n"] > 0:
            left["n"] -= 1
            return tables[state.bonusTier]["upgrade"]
        return tables[state.bonusTier]["quiet"]

    return decide


def pack(sample_id: str, title: str, result: dict, *, resume_index=None, expect_extra=None) -> dict:
    bonus = result["bonus"]
    events = result["events"]
    awarded = max(int(event.get("totalFreeSpinsAwarded") or 0) for event in events if "totalFreeSpinsAwarded" in event)
    expect = {
        "startTier": bonus["startTier"],
        "finalTier": bonus["finalTier"],
        "spinsPlayed": bonus["freeSpinsPlayed"],
        "totalAwarded": awarded or 10,
        "upgradeCount": bonus["upgradeCount"],
        "retriggerCount": bonus["retriggerCount"],
        "maxWinReached": bonus["maxWinReached"],
        "roundWinX": result["roundWinXCapped"],
        "persistentTargets": list(bonus["persistentMysteryTargets"]),
        "tokenFloorTier": bonus["tokenFloorTier"],
        "guaranteedGateUsed": bonus["guaranteedGateUsed"],
    }
    if expect_extra:
        expect.update(expect_extra)
    row = {
        "id": sample_id,
        "title": title,
        "resumeIndex": resume_index,
        "expect": expect,
        "events": events,
    }
    return row


def event_index(events, predicate, *, last=False):
    found = None
    for index, event in enumerate(events):
        if predicate(event):
            found = index
            if not last:
                return index
    if found is None:
        raise RuntimeError("resume event not found")
    return found


def main():
    config = load_v2_config()
    candidate = bonus_candidate_from_config(config)
    base_strips = config["reelModel"]["strips"]
    base3 = stops_for_exact_count(base_strips, 3, perfect_v=False)
    base4 = stops_for_exact_count(base_strips, 4, perfect_v=False)
    base5 = stops_for_exact_count(base_strips, 5, perfect_v=False)
    base_pv = stops_for_exact_count(base_strips, 5, perfect_v=True)
    tables = {}
    for tier, strips in candidate.tierReels.items():
        tables[tier] = {"quiet": quiet_stop(strips), "upgrade": upgrade_stop(strips)}
        board = board_from_stops(strips, tables[tier]["quiet"])
        if scatter_on_board(board, "S", PV_ROWS)["count"] != 0:
            raise RuntimeError(f"{tier} quiet stop still shows scatter")

    win_stop = None
    paytable = config["paytable"]["awards"]
    paylines = config["paylines"]
    regular = {row["id"] for row in config["symbols"]["regular"]}
    scatter_id = config["symbols"]["scatter"]["id"]
    for seed in range(400):
        rng = random.Random(seed)
        stops = [rng.randrange(len(strip)) for strip in candidate.tierReels["LARGE_HILL"]]
        board = board_from_stops(candidate.tierReels["LARGE_HILL"], stops)
        if scatter_on_board(board, "S", PV_ROWS)["count"] >= 3:
            continue
        evaluated = evaluate_paylines(board, paylines=paylines, paytable=paytable, scatter_id=scatter_id, regular_ids=regular)
        if evaluated["lineWinX"] > 0:
            win_stop = stops
            break
    if win_stop is None:
        raise RuntimeError("no winning Large Hill stop")

    samples = []
    print("01", flush=True)
    samples.append(pack("01", "3 Scatter to Large Hill, 10 spins", play(config, base3, quiet_decide(tables))))
    print("02", flush=True)
    samples.append(pack("02", "4 Scatter to Ski Flying", play(config, base4, quiet_decide(tables))))
    print("03", flush=True)
    samples.append(pack("03", "5 Scatter to World Cup", play(config, base5, quiet_decide(tables))))
    print("04", flush=True)
    samples.append(pack("04", "Direct Perfect V", play(config, base_pv, quiet_decide(tables))))
    print("05", flush=True)
    samples.append(pack("05", "Large Hill upgrades to Ski Flying", play(config, base3, upgrade_then_quiet(tables, 1))))
    print("06", flush=True)
    samples.append(pack("06", "Large Hill to Ski Flying to World Cup", play(config, base3, upgrade_then_quiet(tables, 2))))
    print("07", flush=True)
    samples.append(pack("07", "Large Hill through Perfect V", play(config, base3, upgrade_then_quiet(tables, 3))))
    print("08", flush=True)
    samples.append(pack("08", "Perfect V retrigger stays Perfect V", play(config, base_pv, upgrade_then_quiet(tables, 1))))

    def seeded_book(base_stops, seed: int):
        stop_rng = random.Random(seed + 17_171)

        def decide(state):
            strips = candidate.tierReels[state.bonusTier]
            return [stop_rng.randrange(len(strip)) for strip in strips]

        return play(config, base_stops, decide, seed=seed)

    def first_book(label, base_stops, accept, tries=2500):
        print(label, flush=True)
        for seed in range(tries):
            result = seeded_book(base_stops, seed)
            extra = accept(result)
            if extra is not None:
                print(f"  seed {seed}", flush=True)
                return result, extra
        raise RuntimeError(f"no book for {label}")

    def persistent_count(result) -> int:
        return len(result["bonus"]["persistentMysteryTargets"])

    book09, _ = first_book("09", base4, lambda result: {} if persistent_count(result) >= 1 else None)
    samples.append(pack("09", "Ski Flying adds persistent target 1", book09))
    book10, _ = first_book("10", base4, lambda result: {} if persistent_count(result) == 2 else None)
    samples.append(pack("10", "Ski Flying adds persistent target 2", book10))

    def behaviour_b(result):
        targets: list[str] = []
        for event in result["events"]:
            if event["type"] == "skyjumpCoachSignal":
                selected = event.get("selectedSymbolId")
                if targets and selected and selected not in targets:
                    return {"behaviourBExcluded": targets[0], "behaviourBSelected": selected}
            if event["type"] == "skyjumpPersistentTargetsUpdate":
                targets = list(event["persistentMysteryTargets"])
        return None

    book11, extra11 = first_book("11", base4, behaviour_b)
    samples.append(pack("11", "Duplicate persistent target behaviour B", book11, expect_extra=extra11))

    def has_guaranteed_gate(result):
        return {} if any(event["type"] == "skyjumpGuaranteedGate" for event in result["events"]) else None

    def natural_gate_without_inject(result):
        spin_events: list[dict] = []
        for event in result["events"]:
            if event["type"] == "skyjumpFreeSpinStart":
                spin_events = [event]
                continue
            spin_events.append(event)
            if event["type"] != "skyjumpFreeSpinEnd":
                continue
            types = [row["type"] for row in spin_events]
            if "skyjumpGateUpgrade" in types and "skyjumpGuaranteedGate" not in types:
                return {"naturalGateSpin": spin_events[0]["spinIndex"]}
        return None

    book12, _ = first_book("12", base5, has_guaranteed_gate)
    samples.append(pack("12", "World Cup guaranteed Gate", book12))
    book13, extra13 = first_book("13", base5, natural_gate_without_inject, tries=4000)
    samples.append(pack("13", "World Cup natural Gate does not inject another", book13, expect_extra=extra13))

    def floor_persists(result):
        floors = [
            int(event["tokenFloorTier"])
            for event in result["events"]
            if event["type"] == "skyjumpFreeSpinState"
        ]
        if len(floors) < 3:
            return None
        raised = next((floor for floor in floors if floor > 1), None)
        if raised is None or floors[-1] < raised:
            return None
        return {"floorRaisedTo": raised, "floorAtEnd": floors[-1]}

    book14, extra14 = first_book("14", base5, floor_persists)
    samples.append(pack("14", "Token floor persists across Free Spins", book14, expect_extra=extra14))

    def token_then_reset(result):
        seen_token = False
        for event in result["events"]:
            if event["type"] == "skyjumpMysteryResolve" and event.get("resultType") == "FLIGHT_TOKEN":
                seen_token = True
            if seen_token and event["type"] == "skyjumpFreeSpinStart" and int(event["spinIndex"]) > 1:
                return {"tokenThenLaterSpin": int(event["spinIndex"])}
        return None

    book15, extra15 = first_book("15", base3, token_then_reset)
    samples.append(pack("15", "Spin-local Flight Tokens reset on the next Free Spin", book15, expect_extra=extra15))

    print("16", flush=True)
    samples.append(pack("16", "Retriggers push the bonus past 15 spins", play(config, base3, upgrade_then_quiet(tables, 2))))

    print("17", flush=True)
    blocked = {"done": False}

    def decide_max(state):
        if state.spinsAwardedTotal < 40:
            return tables[state.bonusTier]["upgrade"]
        if not blocked["done"]:
            blocked["done"] = True
            return tables[state.bonusTier]["upgrade"]
        return tables[state.bonusTier]["quiet"]

    samples.append(pack("17", "Awarded spins stop at 40", play(config, base3, decide_max, seed=17)))

    print("18", flush=True)

    def decide_cap(state):
        if state.freeSpinsPlayed == 0:
            return win_stop
        return tables[state.bonusTier]["quiet"]

    samples.append(
        pack(
            "18",
            "Max win terminates the bonus",
            play(config, base3, decide_cap, prior=49_999.9, seed=18),
            expect_extra={"syntheticCapPrior": True},
        )
    )

    def resume_at(source_id: str, sample_id: str, title: str, predicate, *, last=False):
        source = next(row for row in samples if row["id"] == source_id)
        index = event_index(source["events"], predicate, last=last)
        copy = json.loads(json.dumps(source))
        copy["id"] = sample_id
        copy["title"] = title
        copy["resumeIndex"] = index
        return copy

    samples.append(
        resume_at(
            "01",
            "19",
            "Resume mid Large Hill",
            lambda event: event["type"] == "skyjumpFreeSpinStart" and event["spinIndex"] == 5,
        )
    )
    samples.append(
        resume_at(
            "05",
            "20",
            "Resume immediately after tier upgrade",
            lambda event: event["type"] == "skyjumpBonusUpgrade" and event.get("tierChanged"),
        )
    )
    # Resume index is the upgrade event itself so reconstruction includes it,
    # then playback continues with the following events. Tests use index+? 
    # "immediately after" means the cursor is the first event after the upgrade.
    samples[-1]["resumeIndex"] += 1
    samples.append(
        resume_at(
            "10",
            "21",
            "Resume Ski Flying with 2 persistent targets",
            lambda event: event["type"] == "skyjumpPersistentTargetsUpdate" and len(event.get("persistentMysteryTargets") or []) == 2,
        )
    )
    samples[-1]["resumeIndex"] += 1
    samples.append(
        resume_at(
            "12",
            "22",
            "Resume World Cup after guaranteed Gate",
            lambda event: event["type"] == "skyjumpGuaranteedGate",
        )
    )
    samples[-1]["resumeIndex"] += 1
    samples.append(
        resume_at(
            "04",
            "23",
            "Resume in Perfect V",
            lambda event: event["type"] == "skyjumpFreeSpinState" and event.get("bonusTier") == "PERFECT_V",
        )
    )
    samples[-1]["resumeIndex"] += 1
    samples.append(
        resume_at(
            "01",
            "24",
            "Resume immediately before the final Free Spin",
            lambda event: event["type"] == "skyjumpFreeSpinStart",
            last=True,
        )
    )

    payload = {
        "nonProduction": True,
        "phase": "5C",
        "note": "DEV preview books generated by the live resolver with forced stops. Not a production LUT.",
        "samples": samples,
    }
    OUT.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {OUT} samples={len(samples)} bytes={OUT.stat().st_size}", flush=True)


if __name__ == "__main__":
    main()
