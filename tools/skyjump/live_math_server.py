#!/usr/bin/env python3
"""Local live math HTTP for SkyJump V2 manual QA (natural resolve, not fixtures).

DEV-only. Serves resolve_v2_round / resolve_v2_buy_round from frozen mathVersion 2
config. Not Stake RGS and not a certified PAR claim from a short session — session
RTP is an empirical running mean.

Usage (repo root or any cwd):
  python tools/skyjump/live_math_server.py
  python tools/skyjump/live_math_server.py --port 8765

Endpoints:
  GET  /health
  GET  /stats
  POST /play  JSON { "mode": "BASE"|"LARGE_HILL"|..., "seed": optional int }
  POST /reset-stats
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
MATH_GAME = ROOT / "math" / "games" / "0_0_poc"
if str(MATH_GAME) not in sys.path:
    sys.path.insert(0, str(MATH_GAME))

from skyjump_v2_freespins import resolve_v2_buy_round, resolve_v2_round  # noqa: E402
from skyjump_v2_lines import load_v2_config  # noqa: E402

CONFIG = load_v2_config()
BUY_MODES = CONFIG.get("buyModes") or {}
MATH_VERSION = int(CONFIG["meta"]["mathVersion"])
STARTED_AT = time.time()

_lock = threading.Lock()
_stats = {
    "spins": 0,
    "wageredCostX": 0.0,
    "returnedWinX": 0.0,
    "hits": 0,
    "bonuses": 0,
    "byMode": {},
}
_play_counter = 0


def _cors(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Cache-Control", "no-store")


def _json(handler: BaseHTTPRequestHandler, code: int, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    _cors(handler)
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _session_rtp() -> float | None:
    if _stats["wageredCostX"] <= 0:
        return None
    return 100.0 * _stats["returnedWinX"] / _stats["wageredCostX"]


def _mode_meta(mode_key: str) -> dict:
    mode = BUY_MODES.get(mode_key)
    if not mode:
        raise KeyError(f"unknown mode {mode_key}")
    return mode


def resolve_play(*, mode_key: str, seed: int | None) -> dict:
    mode = _mode_meta(mode_key)
    rng = random.Random(seed) if seed is not None else random.Random()
    cost = float(mode["costMultiplier"])
    if mode.get("type") == "buy":
        tier = str(mode.get("startsBonusTier") or mode_key)
        result = resolve_v2_buy_round(
            rng,
            config=CONFIG,
            start_tier=tier,
            wager_cost_multiplier=cost,
        )
        criteria = f"live-buy:{mode_key}"
    else:
        result = resolve_v2_round(rng, config=CONFIG)
        criteria = "live-base"
    win_x = float(result["roundWinXCapped"])
    events = result["events"]
    amount_event = next((e for e in reversed(events) if e.get("type") == "finalWin"), None)
    amount = int(amount_event["amount"]) if amount_event and "amount" in amount_event else 0
    global _play_counter
    with _lock:
        _play_counter += 1
        play_id = 100_000 + _play_counter
        _stats["spins"] += 1
        _stats["wageredCostX"] += cost
        _stats["returnedWinX"] += win_x
        if win_x > 0:
            _stats["hits"] += 1
        if result.get("isBonus"):
            _stats["bonuses"] += 1
        bucket = _stats["byMode"].setdefault(
            mode_key,
            {"spins": 0, "wageredCostX": 0.0, "returnedWinX": 0.0, "hits": 0, "bonuses": 0},
        )
        bucket["spins"] += 1
        bucket["wageredCostX"] += cost
        bucket["returnedWinX"] += win_x
        if win_x > 0:
            bucket["hits"] += 1
        if result.get("isBonus"):
            bucket["bonuses"] += 1
        session_rtp = _session_rtp()

    trigger = float(result.get("triggerSpinWinX") or 0.0)
    return {
        "id": play_id,
        "mode": mode_key,
        "seed": seed,
        "costMultiplier": cost,
        "roundWinXCapped": win_x,
        "roundWinXRaw": float(result.get("roundWinXRaw") or win_x),
        "isBonus": bool(result.get("isBonus")),
        "events": events,
        "payoutMultiplier": win_x,
        "amount": amount,
        "criteria": criteria,
        "baseGameWins": trigger,
        "freeGameWins": max(0.0, win_x - trigger),
        "mathVersion": MATH_VERSION,
        "session": {
            "spins": _stats["spins"],
            "sessionRtpPct": session_rtp,
            "wageredCostX": _stats["wageredCostX"],
            "returnedWinX": _stats["returnedWinX"],
            "hits": _stats["hits"],
            "bonuses": _stats["bonuses"],
            "note": "Empirical session RTP from natural resolve; LUT BASE claim is 96.3907%.",
        },
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[live-math] {self.address_string()} {fmt % args}\n")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        _cors(self)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/health", "/"):
            _json(
                self,
                200,
                {
                    "ok": True,
                    "service": "skyjump-v2-live-math",
                    "mathVersion": MATH_VERSION,
                    "mathStatus": CONFIG["meta"].get("mathStatus"),
                    "baseLutRtpPct": (BUY_MODES.get("BASE") or {}).get("rtp"),
                    "uptimeSec": round(time.time() - STARTED_AT, 1),
                    "modes": sorted(BUY_MODES.keys()),
                },
            )
            return
        if path == "/stats":
            with _lock:
                payload = {
                    **_stats,
                    "sessionRtpPct": _session_rtp(),
                    "mathVersion": MATH_VERSION,
                }
            _json(self, 200, payload)
            return
        _json(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/reset-stats":
            with _lock:
                _stats["spins"] = 0
                _stats["wageredCostX"] = 0.0
                _stats["returnedWinX"] = 0.0
                _stats["hits"] = 0
                _stats["bonuses"] = 0
                _stats["byMode"] = {}
            _json(self, 200, {"ok": True})
            return
        if path != "/play":
            _json(self, 404, {"error": "not_found"})
            return
        try:
            body = _read_json(self)
            mode_key = str(body.get("mode") or "BASE").upper()
            seed = body.get("seed")
            seed_i = int(seed) if seed is not None and seed != "" else None
            if mode_key not in BUY_MODES:
                _json(self, 400, {"error": f"unknown mode {mode_key}", "modes": sorted(BUY_MODES)})
                return
            payload = resolve_play(mode_key=mode_key, seed=seed_i)
            _json(self, 200, payload)
        except Exception as exc:  # noqa: BLE001 — surface to QA client
            _json(self, 500, {"error": str(exc), "type": type(exc).__name__})


def main() -> int:
    parser = argparse.ArgumentParser(description="SkyJump V2 local live math server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        f"[live-math] mathVersion={MATH_VERSION} listening http://{args.host}:{args.port}",
        flush=True,
    )
    print("[live-math] POST /play  GET /health  GET /stats", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[live-math] stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
