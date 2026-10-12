# SKYJUMP V2 — Phase 7C Production Math Certification

**Status:** **NEEDS HUMAN RTP CALIBRATION** — books/LUTs generated; buy modes priced from LUT means; **BASE exceeds Stake 96.70% ceiling**; `mathVersion` **not bumped** (remains **1**).
**Branch:** `feat/skyjump-v2-5x5`
**Prior:** Phase 7B APPROVED (`27_PHASE7B_FINAL_ECONOMY_IMPLEMENTATION.md`)
**Worktree:** `skifly-casino-v2` only. V1 writer / V1 `mathVersion` 3 untouched.

---

## 1. Pre-certification freeze

| Field | Value |
| --- | --- |
| Live config SHA (7B) | `d6879d5c9ef3d08386486cd03712d6042e366543597a5c453ca8b1da6f2edbd0` |
| Match | **PASS** |
| Economy | PT2H_LADDER + BODY1 + WR-C H2 |
| Phase 6 | R-BATCH / W-CHARGE / PURE W2 / K1 / max 2 Rejumps / chain 8 |
| Artifact | `math/games/0_0_poc/phase7c_research/pre_cert_freeze.json` |

---

## 2. Modes (V2 only)

| Mode | Type | Notes |
| --- | --- | --- |
| BASE | default | 1.0× wager; natural FS |
| LARGE_HILL | buy | Direct-start FS |
| SKI_FLYING | buy | Direct-start FS |
| WORLD_CUP | buy | Direct-start FS |
| PERFECT_V | buy | Direct-start FS |

V1 distance / MULT_* modes **not** resurrected.

---

## 3. Buy-mode EV (200k / tier + forced WR fill)

| Tier | mean X (w/ WR) | SE | median | P99 | P(cap) | mean spins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LARGE_HILL | 30.6088 | 0.797 | 9.3 | 349.7 | 3.5e-5 | 10.43 |
| SKI_FLYING | 189.2577 | — | — | — | — | — |
| WORLD_CUP | 401.9057 | — | — | — | — | — |
| PERFECT_V | 1311.2979 | — | — | — | — | — |

Full percentiles: `phase7c_research/buy_ev.json`.

---

## 4. Buy costs (from **LUT mean payout**, not EV projection)

Target center ~96.50%; hard ceiling 96.70%; Stake 0.1 grain.

| Mode | LUT mean X | Cost | LUT RTP |
| --- | ---: | ---: | ---: |
| LARGE_HILL | 31.3617 | **32.5** | **96.4975%** |
| SKI_FLYING | 190.7599 | **197.7** | **96.4896%** |
| WORLD_CUP | 402.1030 | **416.7** | **96.4970%** |
| PERFECT_V | 1332.8289 | **1381.2** | **96.4979%** |

Buy-only cross-mode spread: **0.008 pp** — PASS.

Canonical FE surface (do not hardcode elsewhere): `phase7c_research/buy_modes.json` (promote into `skyjump_v2_config.json` `buyModes` only after BASE calibration + mathVersion freeze).

---

## 5. Production books / LUT

Writer: `skyjump_v2_phase7c_books.py` → `library_v2/publish_files/` → staged `stake-upload/math/`.
Does **not** modify V1 `run.py`.

| Mode | Books | Compressed bytes | Book SHA256 | LUT SHA256 |
| --- | ---: | ---: | --- | --- |
| BASE | 200,020 | 250,669,779 | `830d733a…f633` | `724b2389…059b5` |
| LARGE_HILL | 100,020 | 127,208,429 | `400fe67c…38ae` | `0ce72a27…9560` |
| SKI_FLYING | 100,020 | 243,507,591 | `3f92c448…5492` | `970f0724…a3fc` |
| WORLD_CUP | 100,020 | 289,191,502 | `2db5e46d…74cb` | `c18ca041…c05a` |
| PERFECT_V | 100,020 | 488,906,266 | `6a4fd4f1…28ac` | `36457c00…16f41` |

Full digests: `phase7c_research/books_report.json`. Local paths (gitignored staging): `library_v2/publish_files/`, `stake-upload/math/`.

Contract: one paid play → one book → full FS if any → one settlement. Frontend RNG: none.

---

## 6. World Record weighting

| Quantity | Value |
| --- | --- |
| H2 paid-round p | ≈ **9.145e-8** (1 in ~10.9M) |
| LUT effective p (BASE) | ≈ **9.146e-8** |
| RTP contribution | ≈ **0.457 pp** |
| H2 unchanged | **YES** |

Natural WR not required in 100k samples; explicit WR strata + LUT weights.

---

## 7. BASE RTP certification (blocker)

| Estimate | RTP |
| --- | ---: |
| Phase 7B projected pre-book | 96.290% |
| Independent hybrid (eNone + buy natural × mix + WR) | **97.365%** |
| **BASE LUT (weighted)** | **98.120%** |
| Stake ceiling | **96.70%** |

**FAIL** ceiling. Cross-mode spread with buys ≈ **1.63 pp** — FAIL (≤0.50 pp).

### H2 / WR-only calibration (not applied)

| Item | Value |
| --- | ---: |
| Current BASE LUT | 98.120% |
| Delta to 96.50% center | **−1.620 pp** |
| Current WR contribution | **+0.457 pp** |
| WR-only can reach band? | **NO** |

Even zeroing WR leaves ~97.66% independent / ~97.66%+ LUT residual above ceiling. **Human table retune required** (paytable / body / Phase 6) — out of scope for auto 7C.

---

## 8. Cap / grain / replay

| Check | Result |
| --- | --- |
| All books 0 ≤ payout ≤ 50,000× | PASS (max observed 50,000×) |
| Payout grain (`amount % 10 == 0` for >0) | PASS |
| Replay parity (200+/mode sample; reducer `finalWin`) | PASS |
| DEV/research leak in `stake-upload/math` | **NONE** |

---

## 9. mathVersion

| Field | Value |
| --- | --- |
| Current | **1** (unchanged) |
| Bump | **Deferred** until BASE LUT ≤96.70% and cross-mode PASS |
| V1 mathVersion | **3** (untouched) |

---

## 10. Tests

- `test_skyjump_v2_phase7c.py` — schema/LUT/buy band/BASE calibration gate/replay/clean staging
- Prior Phase 1–7B regressions remain authoritative for mechanics

---

## 11. Classification

**NEEDS HUMAN RTP CALIBRATION**

Buy modes are production-priceable at ~96.50%. BASE paid-round LUT/independent estimates exceed Stake ceiling; WR-C H2 cannot close the gap. Do not publish as certified production math until a human-approved economy retune (not WR-only).
