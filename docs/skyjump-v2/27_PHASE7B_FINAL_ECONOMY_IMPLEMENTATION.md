# SKYJUMP V2 — Phase 7B Final Economy Implementation

**Status:** COMPLETE — promoted economy **PT2H_LADDER + BODY1 + WR-C H2** is live in config + resolver + frontend replay.
**Branch:** `feat/skyjump-v2-5x5`
**Prior:** Phase 7A.2 approval (`25_PHASE7A2_PAYTABLE_REPAIR_AND_FINAL_ECONOMY.md`)
**Tests:** `math/games/0_0_poc/test_skyjump_v2_phase7b.py`, `skyjump_v2_phase7b_smoke.py`, `skyjump_v2_wr_samples.json`
**Art:** independent — `26_PRODUCTION_ASSET_TODO.md` (WAIT = NONE)

Do **not** treat projected RTP below as production-certified. Do **not** generate production books or LUTs in this phase.

---

## 1. Pre-promotion certified stack (frozen reference)

Measured stack **before** Phase 7B promotion (PT0 / BODY0 / no WR). Stored in `math/games/0_0_poc/phase7b_research/pre_promotion_freeze.json`.

| Component | Value |
| --- | ---: |
| BASE | **71.212%** |
| Phase 5B | **+17.92705 pp** |
| Phase 6 PURE W2 | **+4.689 pp** (SE 0.078) |
| **Total (pre-7B)** | **93.828%** |

Phase 6 config remains **FROZEN**: R-BATCH, W-CHARGE, PURE W2, K1 ladder `{1,2,3}`, **max 2** persistent targets, **max chain 8**, max **2** Rejumps per spin path. No Phase 6 retune in 7B.

---

## 2. Promoted economy (live)

| Layer | ID | Δ pp (design) | Notes |
| --- | --- | ---: | --- |
| Paytable | **PT2H_LADDER** | +0.60328 (BASE lines exact) | Hierarchy-repaired mid 4oak ladder; see doc `25` |
| Bonus body | **BODY1** | +1.40177 (PT2H+BODY1 combo) | T1/T2 face redistribution only; T5/T6 fixed |
| World Record | **WR-C @ H2** | **+0.45694** | FS-only; fill-to-50,000× |
| **Projected full-game** | — | **~96.290%** | Pre-book projection — **NOT final production-certified** |

Config markers (unchanged until book freeze):

| Field | Value |
| --- | --- |
| `mathVersion` | **1** (bump at Phase 7C+ book freeze) |
| `featureEconomyVersion` | **2** |
| `paytable.candidateOrigin` | `PT2H_LADDER` |
| `flightTokens.candidateOrigin` | `BODY1` |
| `worldRecord.candidateOrigin` | `H2` |

Live file: `math/games/0_0_poc/skyjump_v2_config.json`.

---

## 3. PT2H_LADDER awards (live)

| Symbol | 3OAK | 4OAK | 5OAK |
| --- | ---: | ---: | ---: |
| P1 | 10.0 | 50.0 | 200.0 |
| P2 | 6.0 | 33.2 | 100.0 |
| P3 | 5.0 | 25.2 | 65.0 |
| M1 | 1.6 | **6.5** | 24.6 |
| M2 | 1.3 | **6.0** | 21.6 |
| M3 | 1.0 | **5.5** | 19.1 |
| L1 | 0.8 | 1.7 | 3.6 |
| L2 | 0.5 | 1.3 | 2.7 |
| L3 | 0.3 | 1.1 | **2.0** |

Exact BASE line RTP on Coach E strips: **60.29946%**. Reel strips unchanged.

---

## 4. BODY1 (live)

- T1 weight −40, T2 weight +40 (per tier tables); T3–T6 weights unchanged vs BODY0 freeze.
- Value-weight tables per doc `25` / `test_skyjump_v2_phase7b.py`.
- Visibility: P(Rejump) / P(Wind) identical BODY0 vs BODY1; cap rate unchanged.

---

## 5. WR-C @ H2 — semantics

| Field | Spec |
| --- | --- |
| Architecture | **WR-C** — FS-only board special |
| Availability | Free Spins only (`FREE_SPINS_ONLY`) |
| Trigger timing | **After initial board, before line evaluation** (phase 1b) |
| Mechanism | Independent Bernoulli per FS spin: `p = c × tierRelativeIntensity` |
| Tier ratio | **1 : 3 : 6 : 12** (LH : SF : WC : PV) |
| Symbol | **`SPECIAL_WORLD_RECORD`** on board at math-owned position |
| Fill | Incremental award fills economic round to **`maxWinX = 50,000×`** |
| Event | Emit **`skyjumpWorldRecord`** → terminate FS / Rejump / feature chain |
| Settlement | **One** final round settlement; no double-pay if already at cap |
| Distinct from | **`TOKEN_WORLD_RECORD` (T6)** — collectible token, not the WR special |

Display position (math-owned): prefer `(reel=2, row=2)` if not Scatter; else first reel-major non-Scatter cell. Scatter count uses **pre-overlay** initial reveal.

H2 scale (doc `25`): WR RTP **0.45694 pp**; paid-round **p ≈ 9.15e-8** (~1 in 10.9M); P(WR \| bonus) **~1.40e-5**.

---

## 6. Asset registry (runtime contract)

| Role | Path |
| --- | --- |
| Registry | `frontend/apps/poc/src/game/skyjump_v2/symbolAssetRegistry.ts` |
| Runtime PNGs | `frontend/apps/poc/static/assets/skyjump_v2/symbols/` |
| Source / master drop | `assets/skyjump_v2/source/symbols/` (768×768 PNG RGBA masters; copy same filename to runtime) |

Filenames locked in doc `23` / registry `V2_SYMBOL_FILENAMES`. Missing PNGs fall back to CSS placeholders (`placeholders.ts`).

---

## 7. Explicitly NOT done (Phase 7B)

| Item | Status |
| --- | --- |
| Feature-buy pricing | **NOT priced** — costs remain TBD |
| Production books / LUT | **NOT generated** — Phase 7C+ |
| Final RTP certification | **NOT certified** — projected ~96.290% only |
| `mathVersion` bump | Deferred to book freeze (7C+) |
| Font offline bundle | FONT_DECISION — see doc `26` |
| Final raster symbol art | USER_ART TODO — placeholders remain |

---

## 8. Verification

```text
pytest math/games/0_0_poc/test_skyjump_v2_phase7b.py
python math/games/0_0_poc/skyjump_v2_phase7b_smoke.py
```

Smoke asserts: pre-promotion stack 93.828%, PT2H awards match research, BODY1 weights, WR-C disabled on BASE, WR samples terminate chain, `featureEconomyVersion: 2`.

---

## 9. Ready for Phase 7C?

**YES** — when separately tasked: production book writer, LUT, cross-mode RTP certification, buy-mode EV pricing, `mathVersion` bump at freeze.
