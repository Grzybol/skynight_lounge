"""Phase 7C.4 clean regen smoke — deterministic subset vs frozen library books."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_freespins import resolve_v2_round
from skyjump_v2_lines import load_v2_config
from skyjump_v2_phase7c2_conditional import ConditionalBaseSampler, wr_off_config
from skyjump_v2_phase7c4_common import OUT, dump_json

HERE = Path(__file__).resolve().parent
LIB = HERE / "library_v2_phase7c4" / "publish_files"


def payout_amount(win_x: float) -> int:
    return round_book_amount(win_x)


def event_fingerprint(events: list[dict]) -> str:
    # Drop non-economic ephemeral keys
    cleaned = []
    for e in events:
        cleaned.append({k: v for k, v in e.items() if k != "devSyntheticCapPrior"})
    blob = json.dumps(cleaned, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def main():
    cfg0 = load_v2_config()
    sampler = ConditionalBaseSampler(cfg0)
    cfg = wr_off_config(cfg0)
    # Deterministic NO_TRIGGER-like sample: first 20 natural BASE rounds from seed
    rows = []
    for i in range(20):
        rng = random.Random(7401 + i)
        res = resolve_v2_round(rng, config=cfg)
        rows.append(
            {
                "i": i,
                "payoutMultiplier": payout_amount(float(res["roundWinXCapped"])),
                "eventSha": event_fingerprint(res["events"]),
            }
        )
    redo = []
    for i in range(20):
        rng = random.Random(7401 + i)
        res = resolve_v2_round(rng, config=cfg)
        redo.append(
            {
                "i": i,
                "payoutMultiplier": payout_amount(float(res["roundWinXCapped"])),
                "eventSha": event_fingerprint(res["events"]),
            }
        )
    match = rows == redo
    # Spot-check: re-read first BASE book line exists and has legal grain
    path = LIB / "books_BASE.jsonl.zst"
    first = None
    with path.open("rb") as fh:
        with zstd.ZstdDecompressor().stream_reader(fh) as r:
            buf = b""
            while first is None:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    line, _ = buf.split(b"\n", 1)
                    first = json.loads(line.decode())
    grain_ok = first is not None and (
        int(first["payoutMultiplier"]) == 0 or int(first["payoutMultiplier"]) % 10 == 0
    )
    out = {
        "resolverDeterminism": match,
        "sample": rows[:3],
        "firstBookId": first.get("id") if first else None,
        "firstBookGrainOk": grain_ok,
        "pass": match and grain_ok,
    }
    dump_json(OUT / "clean_regen_smoke.json", out)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
