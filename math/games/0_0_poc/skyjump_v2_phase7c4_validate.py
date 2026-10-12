"""Phase 7C.4 — event schema validation + replay parity + grain checks."""

from __future__ import annotations

import json
import random
from pathlib import Path

import zstandard as zstd

from skyjump_v2_events import round_book_amount
from skyjump_v2_phase7c4_common import OUT, dump_json
from skyjump_v2_reducer import reduce_events

HERE = Path(__file__).resolve().parent
LIB = HERE / "library_v2_phase7c4" / "publish_files"

MODES = ("BASE", "LARGE_HILL", "SKI_FLYING", "WORLD_CUP", "PERFECT_V")
SCALE = float(round_book_amount(1.0))


def validate_book(book: dict) -> list[str]:
    errs = []
    events = book.get("events") or []
    if not events:
        return ["empty events"]
    idxs = [e.get("index") for e in events if "index" in e]
    if idxs and (len(idxs) != len(set(idxs)) or idxs != sorted(idxs)):
        errs.append("bad indexes")
    types = [e.get("type") for e in events]
    if "finalWin" not in types:
        errs.append("missing finalWin")
    if types.count("finalWin") != 1:
        errs.append(f"finalWin count={types.count('finalWin')}")
    if types.count("setTotalWin") < 1:
        errs.append("missing setTotalWin")
    pay = int(book.get("payoutMultiplier") or 0)
    if pay < 0:
        errs.append("neg payout")
    final = next((e for e in events if e.get("type") == "finalWin"), None)
    if final is None:
        errs.append("finalWin!=payoutMultiplier")
    else:
        amt = final.get("amount")
        if amt is None or int(amt) != pay:
            errs.append("finalWin!=payoutMultiplier")
    if pay > 0 and pay % 10 != 0:
        errs.append("grain")
    seen_final = False
    for e in events:
        if e.get("type") == "finalWin":
            seen_final = True
            continue
        if seen_final and e.get("type") in {"setTotalWin", "setWin", "winInfo"}:
            errs.append("monetary after finalWin")
            break
    for e in events:
        if e.get("type") == "skyjumpFreeSpinState":
            if int(e.get("freeSpinsPlayed") or 0) > 40:
                errs.append("FS>40")
        if e.get("type", "").startswith("skyjump") and e.get("schemaVersion") not in (None, 2):
            errs.append(f"schema {e.get('type')}")
        if e.get("type") == "skyjumpBoardReveal":
            board = e.get("board")
            if board and len(board) != 5:
                errs.append("board not 5 reels")
            elif board:
                for col in board:
                    if len(col) != 5:
                        errs.append("board not 5 rows")
                        break
    return errs


def reducer_payout(events: list[dict]) -> float:
    """FE-compatible: replay through Python twin reducer; payout from finalWin amount."""
    state = reduce_events(events)
    for e in reversed(events):
        if e.get("type") == "finalWin":
            pay_x = float(e["amount"]) / SCALE
            tw = state.get("totalWinX")
            if tw is not None and abs(float(tw) - pay_x) > 1e-4 and float(tw) > 0 and pay_x > 0:
                raise ValueError(f"reducer totalWinX {tw} != finalWin {pay_x}")
            return pay_x
    raise ValueError("no finalWin")


def stream_books(path: Path):
    dctx = zstd.ZstdDecompressor()
    with path.open("rb") as fh:
        with dctx.stream_reader(fh) as reader:
            buf = b""
            while True:
                chunk = reader.read(1 << 20)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line.strip():
                        yield json.loads(line.decode("utf-8"))
            if buf.strip():
                yield json.loads(buf.decode("utf-8"))


def run_validation(sample_n: int = 1000) -> dict:
    report = {"modes": {}, "pass": True, "replayPass": True, "grainPass": True}
    max_pay_x = 0.0
    grain_fails = 0
    for mode in MODES:
        path = LIB / f"books_{mode}.jsonl.zst"
        if not path.exists():
            report["modes"][mode] = {"error": "missing books"}
            report["pass"] = False
            report["replayPass"] = False
            continue
        print(f"validate {mode}…", flush=True)
        errs_all = []
        book_count = 0
        schema_error_count = 0
        # Reservoir sample for replay + always keep rare/special
        rng = random.Random(74 + hash(mode) % 997)
        reservoir: list[dict] = []
        specials: list[dict] = []
        for b in stream_books(path):
            book_count += 1
            errs = validate_book(b)
            if "grain" in errs:
                grain_fails += 1
            if errs:
                schema_error_count += 1
                if len(errs_all) < 20:
                    errs_all.append({"id": b.get("id"), "errs": errs})
            pay_x = float(b.get("payoutMultiplier") or 0) / SCALE
            max_pay_x = max(max_pay_x, pay_x)
            is_special = (
                b.get("criteria") in {"WORLD_RECORD", "world_record"}
                or pay_x >= 49_000
                or any(e.get("type") == "skyjumpWorldRecord" for e in (b.get("events") or []))
            )
            if is_special:
                specials.append(b)
            elif len(reservoir) < sample_n:
                reservoir.append(b)
            else:
                j = rng.randrange(book_count)
                if j < sample_n:
                    reservoir[j] = b

        sample = reservoir + [b for b in specials if b["id"] not in {x["id"] for x in reservoir}]
        mismatches = []
        for b in sample:
            try:
                rp = reducer_payout(b["events"])
            except Exception as exc:  # noqa: BLE001
                mismatches.append({"id": b["id"], "error": str(exc)})
                continue
            bp = float(b["payoutMultiplier"]) / SCALE
            if abs(rp - bp) > 1e-6:
                mismatches.append({"id": b["id"], "reducer": rp, "book": bp})

        mode_pass = schema_error_count == 0 and len(mismatches) == 0

        report["modes"][mode] = {
            "bookCount": book_count,
            "schemaErrors": schema_error_count,
            "schemaErrorSamples": errs_all[:5],
            "replaySample": len(sample),
            "replaySpecials": len(specials),
            "replayMismatches": len(mismatches),
            "mismatchSamples": mismatches[:5],
            "pass": mode_pass,
        }
        if not report["modes"][mode]["pass"]:
            report["pass"] = False
        if mismatches:
            report["replayPass"] = False
        print(
            f"  {mode}: books={book_count} schemaErr={schema_error_count} "
            f"replay={len(sample)} mis={len(mismatches)}",
            flush=True,
        )

    report["maxObservedX"] = max_pay_x
    report["capPass"] = max_pay_x <= 50_000 + 1e-9
    report["grainPass"] = grain_fails == 0
    if not report["capPass"] or not report["grainPass"]:
        report["pass"] = False
    dump_json(OUT / "validation_report.json", report)
    print(
        json.dumps(
            {
                "pass": report["pass"],
                "replayPass": report["replayPass"],
                "grainPass": report["grainPass"],
                "maxX": max_pay_x,
                "modes": {m: report["modes"][m].get("pass") for m in report["modes"]},
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    run_validation(1000)
