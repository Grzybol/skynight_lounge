# Garden Bounty — locked production spec

Last updated: 2026-09-14

Canonical mechanics live in `math/games/0_0_poc/game_config.py`. The frontend
`config.ts`, HTML paytable/rules, and optimizer RTP splits must match this file.

Stake-assigned identifiers (`poc_studio`, `0_0_poc`, UI `0.0.0`) stay until ACP
issues finals. Public title is **Garden Bounty**.

| Parameter | Locked value |
| --- | --- |
| Board | 5×3, 20 paylines, left to right |
| RTP | **0.97** |
| Max win | 5000× |
| Modes | `base` cost 1.0; `bonus` buy-bonus cost 100.0 |
| Symbols | H1–H4, L1–L5, W (wild + multiplier), S (scatter) |
| H5 | Art-only spare. Not in paytable, reels, or local demo sampler |
| W / H1 pays (3 / 4 / 5) | 10 / 20 / 50 |
| Free Spins (base) | 3 → 8, 4 → 12, 5 → 15 |
| Retrigger (free game) | 2 → 3, 3 → 5, 4 → 8, 5 → 12 |
| Wild multiplier | Free game only, minimum 2× |
| Buy Bonus | Shipped; RGS jurisdiction may disable it |
| Optimizer split (base) | wincap 0.001 + freegame 0.367 + basegame 0.602 |
| Optimizer split (bonus) | wincap 0.001 + freegame 0.969 |

Parity check: `python -m pytest math/tests/test_config_parity_poc.py` from a
math environment that can import `games/0_0_poc`.
