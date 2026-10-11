# SKYJUMP V2 — Phase 6B Rejump + Wind Key / Flight Multiplier Implementation

**Status:** Historical LIVE implementation record (Phase 6B).
**Superseded for live Wind stage selection by Phase 6C.1** — see `21_PHASE6C1_PURE_W2_ALIGNMENT_CERTIFICATION.md`.
Live `stageRule` is now **`W2_PURE`** (approved E1). Charged-stage priority remains only as an audit/counterfactual helper.

**Branch:** `feat/skyjump-v2-5x5`
**Promoted candidate:** `P6A1_E_E1`
**Architecture at 6B ship:** R-BATCH + W-CHARGE, K1, W2 + charged-stage priority, saturation B, PV1
**Max Rejumps / Free Spin:** 2
**Hard chain depth:** 8

> **Phase 6C.1 note:** Section 3 documents the **6B charged-priority** rule that was live at 6B/6C measurement time. It is **not** the current live payout rule.

Phase 6A F1 and Phase 6A.1 research remain archived. Weights were not retuned during implementation.

SPECIAL_WORLD_RECORD, premium paytable retune, production books/LUT: **not started**.

---

## 1. Pre-promotion freeze

Recorded in `math/games/0_0_poc/phase6b_research/pre_promotion_freeze.json`.

| Check | Result |
| --- | --- |
| BASE mystery (855/42/3/85/15) | unchanged |
| Phase 5B FS core before promote (752/42/6/170/30) | archived under `phase5bMysteryResultWeightsArchive` |
| Phase 5B origin `FS5A_U1_P2_M40_mid_E15j2` | kept |
| Weighted core bonus 27.45472× | reference retained |
| Game before Phase 6 ~89.139% | reference retained |
| Expected E1 +5.195 pp → ~94.334%, reserve ~2.166 | target for live validation |

Config SHA before promote: see freeze file.

---

## 2. Promoted Mystery tables (sum 1000)

New mass from `FLIGHT_TOKEN` only. Fixed: Thermal 42, Gate 6, Judge 170, Head Judge 30.

| Tier | FT | REJUMP | WIND_KEY |
| --- | ---: | ---: | ---: |
| LARGE_HILL | 724 | 22 | 6 |
| SKI_FLYING | 702 | 36 | 14 |
| WORLD_CUP | 682 | 48 | 22 |
| PERFECT_V | 662 | 60 | 30 |

BASE paid Mystery tables: **unchanged** (no REJUMP / WIND_KEY).

Live config: `freeSpins.phase6.candidateOrigin = P6A1_E_E1`, `enabled: true`.
Loader: `bonus_candidate_from_config` fills `mysteryResultWeightsByTier`.

---

## 3. W-CHARGE + charged-stage priority

Each stage `{value: 1|2|3, charge: 0|1}`.

On `WIND_KEY`:

1. Eligible = stages with value &lt; 3.
2. If any eligible has `charge == 1`: choose among those with lowest value (RNG ties) → **UPGRADE** (charge→0, value+1).
3. Else: choose among lowest-value eligible → **CHARGE** (charge 0→1, value unchanged).

Global multiplier = product of stage values only. Charge-only Keys do not change GLOBAL.

Saturation B: all values at 3 → remove WIND_KEY from Mystery draw pool (renormalize). No no-op Wind events.

---

## 4. R-BATCH

Per Mystery batch:

1. Identities known
2. Gates
3. Wind Keys
4. Thermals recomputed on current board
5. Collectors created in **this** batch settle once → `payoutSpent`
6. Queued Rejump → redrop
7. New batch

Early Judges never collect tokens born after their settle. Later Judges may recollect preserved tokens. Thermals after a Rejump can change effective values for later collectors only.

---

## 5. Rejump lifecycle

Preserve: tokens, thermals, gates, judges (incl. spent), head judges, wind keys, resolved coaches, initial scatters.
Refill: ordinary regulars only; **no Scatter** (non-scatter catalog replacement).
Pay new 28-line wins only. Persist targets → new coaches (no Perfect V guaranteed Coach on redrop) → new Mysteries → R-BATCH.
Max 2 applied / spin; further draws → explicit truncated `skyjumpRejumpEnd` (pay 0).

---

## 6. Events

| Type | Role |
| --- | --- |
| `skyjumpWindKey` | CHARGE / UPGRADE transition |
| `skyjumpRejumpStart` | preserve / redrop positions |
| `skyjumpRejumpBoard` | new board cells |
| `skyjumpRejumpLineWins` | new-board lines |
| `skyjumpRejumpEnd` | applied / truncated |
| Judge / HeadJudge collect | + `batchIndex`, `rawTokenCollectionX`, `flightMultiplierX`, `paidCollectionX`, `payoutSpentAfter` |

Snapshot (`skyjumpFreeSpinState`): `flightMultiplier` stages+charges, `windKeysCollected`, `rejumpsThisBonus`, `featureBatchIndex`, `rejumpState`, `globalFlightMultiplier`.

---

## 7. Frontend placeholder

Bonus HUD flight panel: RUN-UP / TAKEOFF / FLIGHT with charge boxes + GLOBAL.
Wind toast distinguishes CHARGE vs UPGRADE (no fake × bump on charge).
Rejump highlights preserved cells; patches redropped cells (no full-board fade).

---

## 8. Live validation (1M, seed 20260925)

Source: `phase6b_research/live_validate.json` + `book_tails.json`.

| Metric | Value |
| --- | ---: |
| Phase 6-on mean (1M) | 36.4203× |
| Increment vs certified Phase 5B 27.45472× | **+5.854 pp** |
| New game RTP | **94.993%** |
| Future reserve (to 96.50%) | **1.507 pp** |
| Paired n | 200,000 |
| Feature-off mean | 27.7276× |
| Phase 6-on (paired) | 36.6970× |
| Paired delta | +8.969× |
| Paired incremental RTP | **+5.857 pp** |

Visibility (approx.):

| | P(Rejump) | P(Wind) | P(any Phase6) |
| --- | ---: | ---: | ---: |
| Mix | 16.63% | 7.60% | 19.74% |
| Large Hill | 14.44% | 5.95% | 17.30% |

E1 research expected ~+5.195 pp / ~94.334% / reserve ~2.166. Live sits **~+0.66 pp** above that expectation (charged-stage priority EV + stream noise). **Not retuned in 6B.** Treat as a Phase 6C investigation item before calling RTP certified.

Natural cap (1M): pCap ≈ 1.3e-5, mean cap drag ≈ 1.55×.
Forced analytic tails: raw max 4,050,000× → capped 50,000×; all cases ≤50k after cap.

Book sizes (1019 bonus books, uncompressed JSON events):

| | events | uncompressed bytes | zlib-6 bytes |
| --- | ---: | ---: | ---: |
| mean | 102.2 | 26,640 | 2,823 |
| P95 | 191 | 52,619 | 4,600 |
| P99 | 273 | 84,918 | 6,781 |
| max | 666 | 221,054 | 14,522 |

zlib-6 is a local estimate only (not zstd).

### Manual `/dev-preview` QA

PHASE 6 SAMPLE source + turbo replay at **1280×720** and **960×540**:

- Wind charge (■□, GLOBAL unchanged)
- Wind upgrade / GLOBAL ×2
- Rejump preserve + REJUMP DONE banner
- Truncation sample present (`15_truncated`)
- Multiplier persistence across spins / tiers (samples 19–20, 23)

DEV catalog: 19 books (`skyjump_v2_phase6_samples.json`); missing natural `16_coach_after_rejump` and `24_cap` within 120k seed scan.

---

## 9. Files

| Path | Role |
| --- | --- |
| `skyjump_v2_phase6b.py` | Live R-BATCH + W-CHARGE resolver |
| `skyjump_v2_phase6b_promote.py` | Config promote |
| `skyjump_v2_phase6b_freeze.py` | Pre-promote freeze |
| `skyjump_v2_phase6b_validate.py` | 1M / paired validation |
| `skyjump_v2_phase6b_book_tails.py` | Forced tails + book sizes |
| `skyjump_v2_phase6b_samples.py` | DEV books |
| `test_skyjump_v2_phase6b.py` | Unit tests |
| `skyjump_v2_config.json` `freeSpins.phase6` | Live switch + tables |
| FE reducer / handlers / HUD / board | Placeholder replay |

---

## 10. RTP budget

| | Value |
| --- | ---: |
| BASE | 71.212% |
| Phase 5B FS (certified ref) | 17.927 pp |
| Before Phase 6 | 89.139% |
| E1 expected incremental | ~5.195 pp |
| After Phase 6 (E1 expected) | ~94.334% |
| Reserve (E1 expected) | ~2.166 pp |
| **Live 1M incremental** | **~5.854 pp** |
| **Live game RTP** | **~94.993%** |
| **Live reserve** | **~1.507 pp** |
| Production target | 96.50% |

Paired feature-off control is required (do not treat a single unpaired 1M gap as certified).

---

## 11. Next

Phase 6C certification must reconcile the live vs E1 ~0.66 pp gap, then freeze. Do not start World Record, premium paytable retune, or production books here.
