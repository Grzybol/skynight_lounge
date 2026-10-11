# Local live math gameplay (SkyJump V2)

Natural `resolve_v2_round` / buy rounds for manual QA. Not fixture replay.

## Start

```powershell
# repo root
python tools/skyjump/live_math_server.py

# frontend/apps/poc (port 3011 if 3010 is stale V1)
..\..\node_modules\.bin\vite.cmd --host 0.0.0.0 --port 3011
```

Open **http://localhost:3011/live-preview**

In local DEV, bare **http://localhost:3011/** (no `rgs_url`) redirects here — Stake RGS authenticate is not available without session params.

Badge shows empirical session RTP. LUT BASE claim is **96.3907%** (`mathVersion: 2`). Hundreds of spins still swing hard; use the math simulator for serious RTP checks.

Buy modes use promoted PRICE_A costs from live config.
