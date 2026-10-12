# SKYJUMP V2 — Implementation Plan

**Status:** Phase 0B–7D complete on `feat/skyjump-v2-5x5` — see `19`–`21`, `27`, `28`–`35`. **Production math frozen** (`mathVersion: 2`). Frontend production hardening (7D) complete; Phase 8 awaits Filip USER_ART / USER_AUDIO. Local natural play: `/live-preview` + `tools/skyjump/live_math_server.py` (doc `35`).
**Rule:** V1 code and frozen math stay in tree. V2 is additive until a later cutover.

Phase 0 git snapshot was completed via an isolated V2 worktree (Option C baseline + selected reusable files). The original V1 working tree was left untouched.

Each phase lists: goal, modules, tests, manual acceptance, rollback, dependencies.

---

## PHASE 0 — Preserve V1 + branch + docs

**Goal:** V1 recoverable exactly; V2 docs canonical; work happens on `feat/skyjump-v2-5x5`.

**Done when:**

- Working tree clean
- Tag `skyjump-v1-stake-review-3.7` on canonical V1 (`main` at the Stake-review commit)
- Branch `feat/skyjump-v2-5x5` created from that tag / `main`
- This folder `docs/skyjump-v2/` present (seven files)
- Nothing pushed unless a human asks

**Modules:** git only + `docs/skyjump-v2/*`. No gameplay.

**Tests:** `git show skyjump-v1-stake-review-3.7` matches intended SHA.

**Manual:** none.

**Rollback:** delete the V2 branch; tag remains.

**Dependencies:** clean working tree. **Phase 0B completed** on `feat/skyjump-v2-5x5` from commit `3691a62` plus the approved reusable files. Tag `skyjump-v1-stake-review-3.7` remains on canonical V1 `c0585f7`.

Canonical docs live in `docs/skyjump-v2/` on this branch.

---

## PHASE 1 — 5×5 board shell (no specials)

**Status:** Implemented on `feat/skyjump-v2-5x5` (placeholder art, DEV fixtures, no production math).

**Goal:** Visible 5×5 placeholder grid, spin/reveal, 28 paylines, line-win **display** from fixture books. No tokens, no mystery, no FS.

**Modules (new, V1 files kept):**

- `math/games/0_0_poc/skyjump_v2_config.json` — lineage/symbols/28 paylines/5×5/1280×720. No production weights or paytable
- `math/games/0_0_poc/skyjump_v2_dev_paytable.json` — **NON-PRODUCTION / FIXTURE/TEST ONLY**
- `math/games/0_0_poc/skyjump_v2_phase1_fixtures.json` — ten deterministic boards
- `math/games/0_0_poc/skyjump_v2_lines.py` — pure evaluator; DEV paytable only with `allow_dev_paytable=True`
- `frontend/apps/poc/src/game/skyjump_v2/` — JSON import, evaluator (tests/fixtures), schema-v2 events, DEV fixture books
- `frontend/apps/poc/src/components/skyjump_v2/SkyJumpV2Board.svelte`
- This branch **routes to the V2 board by default**. V1 strip/weather/overlay components remain in tree and are unmounted, not deleted

**Implementation notes:**

- Placeholder tiles P1–P3, M1–M3, L1–L3, S (programmatic shapes/colours)
- Sequential left-to-right reel stop from `skyjumpBoardReveal` (turbo is timing-only)
- Highlight paths listed in supplied `skyjumpLineWins` events. Frontend does **not** authoritatively evaluate money
- Local `/dev-preview` fixtures cycle 01–10. Query `?fixture=04` or the DEV inspector pins a fixture. Fixture source is `import.meta.env.DEV` + localDemo + localhost only
- Logical design size is 1280×720 in V2 config. The Stake HUD still uses existing `createLayout` / `mainLayoutStandard()` scaling; the 5×5 board is placed in the scaled playfield above the HUD dock. The browser canvas is not hardcoded to 1280×720
- DEV payline inspector (lines 1–28) is hidden unless DEV localDemo

**Automated tests:**

- `node --experimental-strip-types tools/skyjump/test-v2-phase1.ts`
- `pytest math/tests/test_skyjump_v2_phase1.py`
- Existing V1 `test-math.ts` / `test_config_parity_poc.py` still required

**Manual:**

- `/dev-preview`: menu → spin fixtures → 5×5 readable at 1280×720, 1920×1080, 960×540, 640×360
- HUD still works; no controls off-screen
- No-win, 3/4/5-match, multi-line, overlap, scatter-ignored fixtures

**Rollback:** unmount V2 board and restore V1 strip imports in `Game.svelte`; V1 math files stay untouched.

**Dependencies:** Phase 0B git snapshot.

**Not in Phase 1:** production books, Flight Tokens, Coach, Mystery, Thermal, Gate Upgrade, Rejump, Judge, Wind Key, World Record, Free Spins, feature-buy math.

---

## PHASE 2 — Math V2 foundation

**Status:** Implemented on `feat/skyjump-v2-5x5`. PHASE 2 PROVISIONAL BASE MATH. Report: `08_PHASE2_BASE_MATH_REPORT.md`.

**Goal:** New resolver lineage: symbol model, 5 virtual strips, provisional 0.10× paytable, scatter counting, schema-2 BASE events, analytical + ≥1M simulation. No specials.

**Modules:**

- `skyjump_v2_config.json` — 28 paylines unchanged; reel strips; provisional paytable; scatter model; grain; simulation seed
- `skyjump_v2_reels.py` / `skyjump_v2_exact.py` / `skyjump_v2_search.py` / `skyjump_v2_resolve.py` / `skyjump_v2_events.py` / `skyjump_v2_simulate.py`
- `skyjump_v2_lines.py` (no wilds; production path requires an explicit paytable)
- DEV math samples + `/dev-preview` MATH SAMPLE replay
- Do **not** edit `skyjump_config.json` or V1 `run.py` production path
- Do **not** write production `books_*.jsonl.zst` / LUT / `stake-upload/math`

**Tests:**

- Reel wraparound, deterministic stops, same seed → same sim
- Scatter ignored by lines, counted, Perfect V detection
- 0.10× grain; evaluator Python/TS parity
- Theoretical line RTP vs 5M-spin simulation
- Event serialization / replay; `totalFeatureWinX = 0`
- Phase 1 fixture tests still pass

**Manual:** `/dev-preview` FIXTURES still cycle 01–10. MATH SAMPLE replays Python books.

**Rollback:** keep Phase 1 fixtures; disable math-sample source.

**Dependencies:** Phase 1 fixtures prove FE can play schema 2.

**Not in Phase 2:** Flight Tokens, Coach, Mystery, Thermal, Gate Upgrade, Rejump, Judge, Wind Key, World Record, Free Spins, feature buys, production books.

---

## PHASE 3 — Flight Tokens, Mystery, Coach Signal

**Status:** Implemented on `feat/skyjump-v2-5x5`. PHASE 3 PROVISIONAL FEATURE MATH. Report: `09_PHASE3_COACH_MYSTERY_TOKEN_REPORT.md`.

**Goal:** Book events for tokens, Coach, Mystery transform/resolve. FE renders placeholders. Still no Thermal/Rejump/collectors.

**Modules:** `skyjump_v2_tokens.py`, `skyjump_v2_features.py`, `skyjump_v2_reducer.py`, schema-v2 Coach/Mystery events, FEATURE SAMPLE replay.

**Tests:** Coach only selects existing regulars; cannot select scatter/token/special; Mystery result always explicit; tokens do not auto-pay; reducer replay; no FE RNG.

**Manual:** `/dev-preview` source **FEATURE SAMPLE** (Coach highlight → Mystery transform → token face value).

**Rollback:** feature weights 0; Phase 2 BASE still runs from frozen math samples.

**Dependencies:** Phase 2.

**Not in Phase 3:** Thermal Lift, Gate Upgrade, Rejump, Judge, Head Judge, Wind Key, Flight Multiplier, World Record special, Free Spins execution, feature buys, production books.

---

## PHASE 4B — Paying BASE features (F01_E_feel)

**Status:** Implemented on `feat/skyjump-v2-5x5`. PHASE 4B PROVISIONAL PAYING FEATURE MATH. Report: `12_PHASE4B_BASE_FEATURE_IMPLEMENTATION.md`.

**Goal:** Promote `F01_E_feel` onto live config: paying Mystery mix, Gate, Thermal, Judge/Head Judge, 50,000× cap, Coach E strips, FEATURE SAMPLE 01–17, placeholder FE animation.

**Done when:**

- `featureEconomyVersion: 1`, `candidateOrigin: F01_E_feel`, `mathVersion: 1`
- Resolution order: board → lines → scatter → Coach → mysteries → gate → thermal → collectors → cap → result
- `pytest tests/test_skyjump_v2_phase4b.py` passes
- `/dev-preview` **FEATURE SAMPLE** replays fixtures 01–17

**Not in Phase 4B:** Free Spins, Rejump, Wind Key / Flight Multiplier, production books.

**Dependencies:** Phase 3.

---

## PHASE 4 (remainder) — Rejump, Wind Key, Flight Multiplier

**Status:** **SUPERSEDED.** Shipped as **Phase 6B** on Free Spins (not BASE Phase 4 remainder); aligned to PURE W2 in **Phase 6C.1**. See `19_PHASE6B_REJUMP_WIND_IMPLEMENTATION.md` and `21_PHASE6C1_PURE_W2_ALIGNMENT_CERTIFICATION.md`.

**Historical goal (absorbed):** Full feature chain with Rejump loops and global Flight Multiplier.

---

## PHASE 5 — Free Spin state machine

**Status:** Phase 5A research is in `14_PHASE5A_FREE_SPIN_ECONOMY_AUDIT.md`. Phase 5B promoted `FS5A_U1_P2_M40_mid_E15j2` and implemented the core bonus. Buy modes are still not implemented. Production books are not generated.

**Goal:** Four tiers, U1 progression, persistence flags, one economic round, placeholder HUD. Buy-mode costs stay TBD.

**Modules:** bonus reducer, `skyjumpFreeSpins*`, `checkIsBonusGame` ADAPT, snapshot types.

**Tests:** Perfect V pattern detection; 3/4/5 scatter; persistence of targets/floor/G; no scatter farming on Rejump.

**Manual:** FS HUD: tier, spins, targets, floor, G. Autoplay through a short fixture bonus.

**Rollback:** scatter trigger disabled; BASE-only.

**Dependencies:** Phase 4.

---

## PHASE 6 — Rejump + Wind Key / Flight Multiplier (mechanics)

**Status:** **COMPLETE** (6B implement → 6C measure → 6C.1 PURE W2 align). Live Free Spins only. Certified interim Phase 6 incremental **+4.689 pp** (doc 21). Phase 6 config is **FROZEN**.

**Not in Phase 6:** production books/LUT. (World Record + paytable promotion moved to Phase 7B — now live.)

---

## PHASE 7A / 7B — Final economy + symbol lock

**Phase 7A status:** COMPLETE — research + art lock (`22`, `23`, `24`, `25`).

**Phase 7B status:** **COMPLETE** — promoted **PT2H_LADDER + BODY1 + WR-C H2** live in `skyjump_v2_config.json`, resolver, and frontend replay. Report: `27_PHASE7B_FINAL_ECONOMY_IMPLEMENTATION.md`.

**Promoted:** hierarchy-fixed paytable, BODY1 token tables, FS-only World Record (fill-to-50,000×, terminate chain), `symbolAssetRegistry.ts` + runtime asset paths.

**Pre-promotion certified stack:** BASE 71.212% + Phase 5B 17.92705 + Phase 6 4.689 = **93.828%**.

**Projected pre-book RTP:** **~96.290%** — **NOT** final production-certified.

**Not in Phase 7B:** feature-buy pricing, production books, LUTs, `mathVersion` bump (deferred to 7C+ book freeze), final raster art (doc `26`).

**Tests:** `test_skyjump_v2_phase7b.py`, `skyjump_v2_phase7b_smoke.py`, WR samples JSON.

---

## PHASE 7C — Production math freeze (books / LUT / buy pricing)

**Status:** **EXECUTED — NEEDS HUMAN RTP CALIBRATION** (report `28_PHASE7C_PRODUCTION_MATH_CERTIFICATION.md`).

| Item | Result |
| --- | --- |
| Writer | `skyjump_v2_phase7c_books.py` → `library_v2/` → `stake-upload/math/` (V1 untouched) |
| Book counts | ≥100,020 / mode (BASE stratified 200,020) |
| Buy LUT RTP | ~96.50% each; costs 32.5 / 197.7 / 416.7 / 1381.2 |
| BASE LUT RTP | **~98.12%** — **above 96.70% ceiling** |
| Cross-mode | **FAIL** (~1.63 pp with BASE) |
| WR-C H2 | Unchanged; WR-only **cannot** close BASE gap |
| mathVersion | **1** (bump deferred) |
| Canonical buy surface | `phase7c_research/buy_modes.json` |

**Next:** human economy retune (not WR-only), then re-LUT BASE, re-check ceiling/spread, then bump `mathVersion` + promote `buyModes` into live config.

---

## PHASE 7C.1 — BASE RTP / LUT reconciliation

**Status:** COMPLETE (diagnostic) — report `29_PHASE7C1_BASE_RTP_RECONCILIATION.md`.

| Item | Result |
| --- | --- |
| Live economy / mathVersion | **unchanged** (SHA `d6879d5c…`, mathVersion **1**) |
| WR / Phase5+6 double-count | **NO** (hybrid used WR-off tier EV + one WR term) |
| LUT partition / recon | **PASS**; Perfect V weight-floor overweight (~0.002 pp) |
| LUT vs corrected stratified | **0.48 pp** — acceptance **FAIL** (≤0.10) |
| Classification | **MULTIPLE CAUSES** (hybrid undercount + hot freegame book means + projection undercount + economy likely still hot) |
| Human retune decision | **NO** until BASE freegame means reconciled |

---

## PHASE 7C.2 — Authoritative BASE strata rebuild

**Status:** BASE acceptance **PASS** — report `30_PHASE7C2_AUTHORITATIVE_RTP_AND_STRATA_REBUILD.md`.

| Item | Result |
| --- | --- |
| Natural-trigger BASE books (not buy slices) | **YES** |
| Authoritative BASE RTP | **95.861%** |
| New BASE LUT | **95.861%** (gap ~0) |
| Old 7C LUT bias | **+2.26 pp** (buy-sourced freegame) |
| Economy vs 96.70 ceiling | **WITHIN LIMIT** |
| Buy costs | provisional only (EV-priced); LUT agreement still loose |
| mathVersion / live config | **unchanged** |

---

## PHASE 7C.3 — High-precision BASE / buy EV + cross-mode pricing

**Status:** Complete on `feat/skyjump-v2-5x5` — see `31_PHASE7C3_HIGH_PRECISION_RTP_CERTIFICATION.md`.

| Item | Result |
|------|--------|
| Goal | Reduce BASE SE; certify buy EV/LUT; design PRICE_A/B |
| Live economy | **UNCHANGED** |
| BASE RTP | **96.391%** SE **0.080 pp**; upper 95% **96.547%** → ceiling **PASS** |
| LH contrib SE | **0.0595 pp** (7.92M natural; preferred 0.05 not met) |
| SF / WC contrib SE | **0.019 / 0.003 pp** |
| BASE LUT | 2-SE compatibility **PASS** |
| PRICE_A spread | **0.156 pp** PASS; costs design-only (LH 30.2 / SF 196.9 / WC 412.8 / PV 1369.1) |
| Classification | **PRODUCTION ECONOMY VALID — NO RETUNE** |
| mathVersion / promotion | **unchanged** — await human freeze |

---

## PHASE 7C.4 — Final production math freeze

**Status:** Complete — see `32_PHASE7C4_PRODUCTION_MATH_FREEZE.md`.

| Item | Result |
|------|--------|
| Economy retune | **NO** |
| mathVersion | **1 → 2** |
| BASE actual LUT RTP | **96.3907%** (gap ≈0 pp vs 7C.3 authority) |
| Buy costs promoted | LH **30.2** / SF **196.9** / WC **412.8** / PV **1369.1** |
| Buy LUT RTP | LH 96.3802 / SF 96.5029 / WC 96.5358 / PV 96.5347 |
| Cross-mode spread | **0.1556 pp** PASS |
| Staging | `stake-upload-final/math/` |
| Manifest | `math/games/0_0_poc/phase7c4_release_manifest.json` |
| Classification | **PRODUCTION MATH FROZEN** |

**Next:** Phase 7D frontend production hardening (complete — see `33`), then Phase 8 art/audio drop-in.

---

## PHASE 7D — Frontend production hardening

**Status:** Complete — see `33_PHASE7D_FRONTEND_PRODUCTION_HARDENING.md` + `34_FRONTEND_MANUAL_QA_CHECKLIST.md`.

| Item | Result |
|------|--------|
| Math | **UNCHANGED** (mathVersion 2 frozen) |
| Event handlers | Complete for typed V2 skyjump* + settlement |
| Timing modes | NORMAL / TURBO / CATCH_UP |
| Input lock | `overlayOpen` via `presentationLock` for V2 presentation |
| Resume reserves | + WorldRecord + FreeSpinsEnd + finalWin |
| Buy costs | Config-driven only |
| Font | Typekit removed; system fallback |
| Audio | Semantic hooks wired (shared sprites / safe fallback) |
| Manual QA | `34_FRONTEND_MANUAL_QA_CHECKLIST.md` |

---

## PHASE 7 — Frontend feature animation, resume, turbo/autoplay

**Status:** Superseded / completed as **Phase 7D** above.

---

## PHASE 8 — Final art / audio replacement

**Goal:** Replace placeholders using **local ComfyUI only** (`http://127.0.0.1:8188`). Register in `assets.ts`. If Comfy down, keep placeholders + manifest note.

**Modules:** `assets/skyjump/v2/`, audio mapping. Do not import Odin/Nordic packs.

**Tests:** asset registry; production build strips illegal folders if needed.

**Manual:** desktop + 480×900 visual pass.

**Dependencies:** Phase 7 (so art meets real layout).

---

## PHASE 9 — Responsive QA, Stake session, bundle, ACP

**Goal:** Viewport matrix; RGS authenticate/play/end-round; production bundle; ACP validation. `gameID` still `0_0_poc` until real ids.

**Modules:** CI extras for V2 tests; upload pipeline **copy**, do not overwrite V1 `stake-upload` until a human cutover.

**Tests:** production build; `check-placeholders`; no `/dev-preview` prerender.

**Manual:** Stake session QA checklist (auth, buy modes once costs exist, replay, disconnect).

**Rollback:** keep serving V1 package.

**Dependencies:** Phases 6–8.

---

## Cross-cutting rules for every phase

- Canonical JSON for numbers; no magic in Svelte
- Format touched frontend with prettier
- Do not force-push `main`
- Do not delete farmer / V1 SkyJump trees
- If code disagrees with `docs/skyjump-v2`, amend the doc first
