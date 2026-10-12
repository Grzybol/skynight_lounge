# Phase 7C.4 — Final production math freeze

**Status:** PRODUCTION MATH FROZEN  
**Branch:** `feat/skyjump-v2-5x5`  
**Economy retune:** NO (Phase 7C.3 authority approved)

## Authoritative freeze

| Item | Value |
|---|---|
| Pre-promote config SHA | `d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0` |
| Final config SHA | `d3f5b13b38018f4757a3c6fd816dfa0cbfe314f33ca6f79f6c078ffc00677956` |
| mathVersion | **1 → 2** |
| Economy | PT2H_LADDER + BODY1 + WR-C H2 + Phase 6 PURE W2 / W-CHARGE / R-BATCH |
| maxWinX | 50000 |

## Actual LUT RTP (publication books × LUT weights)

| Mode | Cost | Actual LUT RTP | vs authority |
|---|---:|---:|---|
| BASE | 1.0 | **96.3907%** | gap ≈ 0.0000 pp |
| LARGE_HILL | 30.2 | 96.3802% | ≤0.05 pp |
| SKI_FLYING | 196.9 | 96.5029% | ≤0.05 pp |
| WORLD_CUP | 412.8 | 96.5358% | ≤0.05 pp |
| PERFECT_V | 1369.1 | 96.5347% | ≤0.05 pp |

Cross-mode: min 96.3802% · max 96.5358% · **spread 0.1556 pp** (≤0.50 required, ≤0.20 preferred) · all ≤96.70%.

## Book counts

| Mode | Books |
|---|---:|
| BASE | 350040 |
| LARGE_HILL | 120024 |
| SKI_FLYING | 80024 |
| WORLD_CUP | 60024 |
| PERFECT_V | 60024 |

## Rare-event weights

| Event | Target | Effective | Gate |
|---|---|---|---|
| PV | 1.9755474637131444e-9 | matched within scale | PASS |
| WR | ~9.1455e-8 | matched within scale | PASS |

## Publication package

Clean staging (Stake artifacts only):

`stake-upload-final/math/`

Contains: `index.json`, `books_*.jsonl.zst`, `lookUpTable_*_0.csv`.

Machine-readable fingerprint:

`math/games/0_0_poc/phase7c4_release_manifest.json`

## Validation

- Schema / indexes / 5×5 / FS / grain: PASS (all books)
- Replay (≥1000/mode + WR/specials) via Python FE twin reducer: PASS
- Cap ≤50000×: PASS
- Clean regen determinism smoke: PASS
- Historical Phase 7C–7C.3 research dirs retained (non-production)

## Frontend

`skyjump_v2_config.json` now owns `buyModes`. Frontend reads costs from canonical V2 config (`V2_ENABLED_MODES`). No hardcoded buy costs. Typekit / art / audio remain out of scope.

## Classification

**PRODUCTION MATH FROZEN** — ready for frontend/asset production phase (math side).
