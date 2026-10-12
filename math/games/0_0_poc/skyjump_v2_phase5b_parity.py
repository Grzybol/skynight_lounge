"""Emit one bonus book and compare the TS reducer snapshot."""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_reducer import reduce_events

config = load_v2_config()
rng = random.Random(4)
book = None
for _ in range(4000):
    result = resolve_v2_round(rng, config=config)
    if result["isBonus"]:
        book = result
        break
if book is None:
    raise SystemExit("no bonus")
events_path = HERE / "phase5b_research" / "parity_events.json"
out_path = HERE / "phase5b_research" / "parity_ts.json"
events_path.parent.mkdir(exist_ok=True)
events_path.write_text(json.dumps(book["events"]), encoding="utf-8")
py = reduce_events(book["events"])
script = ROOT / "frontend" / "apps" / "poc" / "src" / "game" / "skyjump_v2" / "reducerParity.ts"
subprocess.check_call(
    [
        "node",
        "--experimental-strip-types",
        str(script),
        str(events_path),
        str(out_path),
    ],
    cwd=script.parent,
)
ts = json.loads(out_path.read_text(encoding="utf-8"))
keys = [
    "bonusActive",
    "bonusTier",
    "freeSpinsRemaining",
    "freeSpinsPlayed",
    "tokenFloorTier",
    "guaranteedGateUsed",
    "pendingTierUpgrade",
    "coachGuaranteeState",
]
for key in keys:
    if py[key] != ts[key]:
        raise SystemExit(f"mismatch {key}: py={py[key]!r} ts={ts[key]!r}")
if abs(float(py["bonusWinXCapped"]) - float(ts["bonusWinXCapped"])) > 1e-6:
    raise SystemExit("bonus win mismatch")
if abs(float(py["roundWinXCapped"]) - float(ts["roundWinXCapped"])) > 1e-6:
    raise SystemExit("round win mismatch")
if py["persistentMysteryTargets"] != ts["persistentMysteryTargets"]:
    raise SystemExit("targets mismatch")
if py["board"] != ts["board"]:
    raise SystemExit("board mismatch")
print("PY/TS parity PASS", py["bonusTier"], py["roundWinXCapped"])
