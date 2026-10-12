# SKYJUMP V2 — Frontend Manual QA Checklist (Filip)

**Branch:** `feat/skyjump-v2-5x5`  
**App:** `frontend/apps/poc` · `/dev-preview` (DEV only)  
**Math:** frozen 7C.4 — do not retune while QA’ing presentation.

**Local:** http://localhost:3011/dev-preview  

Mark each box after hands-on verification.

---

## DEV entry points

| Task | Where |
| --- | --- |
| Audio QA soundboard | DEV PREVIEW → board DEV inspector → **Audio QA** |
| Rapid hover stress | Audio QA → **Rapid hover 250 / 100 / 50ms** |
| Rapid paylines | Audio QA → **Rapid paylines** |
| Feature overlap | Audio QA → **Feature overlap** |
| Turbo audio chain | Audio QA → **Turbo chain** |
| Catch-up silence | Audio QA → **Catch-up silence** |
| Settings volumes | Modal Settings (master / SFX / BGM) — not duplicated in Audio QA |

---

## BASE

- [ ] Spin shows sequential 5×5 reel stop
- [ ] Line wins highlight book-provided lines only
- [ ] Multi-line cycles or groups without FE recompute
- [ ] No-win spin settles cleanly
- [ ] Turbo shortens delays; order unchanged
- [ ] SPIN/BET/Space locked during presentation

## Coach / Mystery

- [ ] Coach indicates event-selected symbol
- [ ] Transform → closed Mystery → resolve sequence
- [ ] No FE symbol selection
- [ ] Catch-up / resume shows final Mystery state

## Tokens

- [ ] T1–T6 art or placeholder shows
- [ ] Face value is dynamic text (not baked in PNG)
- [ ] Numeric reveal separate from artwork

## Thermal / Gate

- [ ] Thermal ×N overlay readable
- [ ] Affected tokens indicated
- [ ] Face value still visible / not permanently overwritten
- [ ] Gate shows floor up + replacements from event

## Judge / Head Judge

- [ ] Judge collection sweep uses event amounts
- [ ] Head Judge uses **final** `sym_feat_head_judge.png` (not Judge art)
- [ ] Head Judge visually distinct (two-pass)
- [ ] Head Judge SFX pass 1 full / pass 2 quieter
- [ ] No FE recompute of collected totals

## Rejump

- [ ] Settled batch → trigger → clear ordinary → redrop → lines → features
- [ ] Preserved tokens/thermals/gates/collectors/Wind/Coach/scatters remain
- [ ] No fake scatter on refill
- [ ] Spent collectors stay inert

## Wind / Flight Multiplier

- [ ] RUN-UP / TAKEOFF / FLIGHT HUD updates from events
- [ ] Charge / upgrade / global G from events only
- [ ] No FE stage-selection logic

## Free Spins

- [ ] Tier name readable (LARGE HILL / SKI FLYING / WORLD CUP / PERFECT V)
- [ ] Remaining spins / token floor / persistent targets / FM visible
- [ ] +5 spins / tier upgrade timing matches book (not one spin early)
- [ ] Perfect V retrigger stays Perfect V

## World Record

- [ ] SPECIAL_WORLD_RECORD ≠ T6 Token World Record look
- [ ] Terminal WR → 50,000× → chain cancelled → one settlement
- [ ] No ordinary feature animations after terminal WR
- [ ] Catch-up lands on max-win terminal state

## Buy modes

- [ ] Costs: LH 30.2 / SF 196.9 / WC 412.8 / PV 1369.1 from config
- [ ] Labels / RGS keys correct
- [ ] Long costs fit buy dialog

## Turbo / Autoplay

- [ ] Turbo is timing-only
- [ ] Autoplay waits for settlement unlock
- [ ] AUTOPLAY control cancels future rounds
- [ ] STOP (BET button while spinning) cancels future autoplay rounds even mid-presentation
- [ ] Current paid round / Free Spins / Rejump still settles after STOP
- [ ] After settlement, autoplay is OFF and UI returns to non-autoplay
- [ ] STOP during ordinary base / Free Spins / Rejump / turbo behaves as above
- [ ] WR/cap cannot skip into next play

## Paytable / Info (Phase 8A)

- [ ] Paytable shows V2 regular symbols P1–L3 with 3/4/5 from config (not hardcoded)
- [ ] Paytable explains 28 lines L→R, reel-1 start, scatter not on lines
- [ ] Feature cards present (Bib, Coach, Mystery, Tokens, Thermal, Gate, Judge, Head Judge, Rejump, Wind, Special WR)
- [ ] Mini 5×5 payline viewer prev/next works for lines 1–28
- [ ] No V1 weather / six-slot / distance payout copy
- [ ] Info guide covers How to Play → Buy Bonus without Phase-2 / solver jargon
- [ ] Panels scroll; close/back works; no HUD overlap at 1920 / 1280 / 960 / 640

## Phase 8F — real gameplay hard-wiring

**Report:** `docs/skyjump-v2/39_REAL_UI_IMPLEMENTATION_MATRIX.md`  
**Primary:** http://localhost:3011/live-preview  

- [ ] SPIN primary control (not “BET” label); STOP distinct
- [ ] BET − / SPIN / + read as one cluster
- [ ] Status plate READY / NO WIN / WIN with plate art
- [ ] Line win: progressive stroke + visible travelling spark PNG + end glint
- [ ] Multi-line sequential draw
- [ ] FS / Retrigger / Tier / mode title PNGs on real events
- [ ] BIG→WR celebrations on real settlement (not showcase-only)

## Phase 8E — placement / scale / timing

**Report:** `docs/skyjump-v2/38_FINAL_VISUAL_PLACEMENT_PASS.md`  
**Primary:** http://localhost:3011/live-preview @ 1280×720  

Trigger from `/dev-preview` scenarios (no random spins required):

- [ ] Win titles BIG → WR share one slot; mild scale ramp only
- [ ] Count-up under title; particles do not cover amount
- [ ] FS / Retrigger / Tier banners use distinct slots; no stack
- [ ] Mode titles LH/SF/WC/PV identical geometry
- [ ] Status plate compact under board; Mode badge fits PERFECT V
- [ ] Modal headers compact (no giant transparent canvas gaps)
- [ ] Payline spark ~24px · end glint ~30px
- [ ] TURBO compresses cosmetic holds; settlement unchanged

## Phase 8D — 1280×720 layout (primary: `/live-preview`)

**Local:** http://localhost:3011/live-preview · logical 1280×720  
**Report:** `docs/skyjump-v2/37_FINAL_1280_UI_LAYOUT_PASS.md`

Do **not** mark approved on Filip’s behalf.

### Stage / hierarchy

- [ ] At 1280×720: board dominant; logo secondary (top-right); HUD readable; no awkward floats
- [ ] Status plate always present under board (`READY` idle); no row-5 overlap
- [ ] Ambient frame/grid FX visible but weaker than win/feature/payline/WR
- [ ] Presets 768 / 640 / 480 / 400 CSS-scale the same layout (no independent redesign)

### DEV scenarios (visual)

| Scenario | Where |
| --- | --- |
| BASE idle + spin | `/live-preview` or `/dev-preview` |
| Line win / multi-payline | `/dev-preview` DEV scenarios |
| BIG / MEGA / SUPER / MAX / WORLD RECORD | `/dev-preview` win scenarios |
| FREE SPINS / RETRIGGER / TIER UPGRADE | `/dev-preview` bonus scenarios |
| LH / SF / WC / PV mode titles | Free Spins tier scenarios |
| Paytable | MENU → Paytable @ 1280 |
| Info | MENU → Info / How to Play @ 1280 |

- [ ] BIG ≠ WORLD RECORD intensity
- [ ] Count-up readable; long values scale (no clip)
- [ ] Particles frame celebration; title + amount stay clear
- [ ] Bonus banners do not stack multiple title PNGs
- [ ] Payline spark + end glint readable, not oversized
- [ ] Tier emblem LH≡SF debt still visible if emblems shown (known art debt)

## Payline draw FX (Phase 8A)

- [ ] Winning line draws progressively (not instant pop)
- [ ] Travelling icy/gold spark follows the tip on NORMAL
- [ ] Multiple lines draw sequentially (readable, not spaghetti)
- [ ] Turbo: faster draw / shorter hold / reduced spark
- [ ] Catch-up / reduced motion: no long draw delay
- [ ] Line geometry matches book-provided positions only

## SFX — retrigger / overlap (Filip listening)

- [ ] Rapid mouse across HUD buttons: repeated hover SFX (not one stuck cue)
- [ ] Audio QA Rapid hover 250ms — all meaningful cues audible
- [ ] Audio QA Rapid hover 100ms — natural overlap, no EOF lock drops
- [ ] Audio QA Rapid hover 50ms — voice limiting OK, not collapsed to one sound
- [ ] Fast PAYLINE_DRAW → COMPLETE → next DRAW does not drop cues
- [ ] Rapid Scatter lands remain audible before Scatter Trigger
- [ ] Head Judge pass 2 audible while pass 1 may still be decaying
- [ ] Wind Charge → Upgrade → Transition all audible
- [ ] Feature overlap (Mystery → Token → Thermal → Judge) all audible
- [ ] No painful clipping storm during overlaps
- [ ] Master mute / SFX 0 suppresses every pooled voice

## SFX — final custom pack (Filip listening)

Mute / volume (global controls must apply to all new SFX):

- [ ] SFX global mute / master volume 0 suppresses all custom hooks
- [ ] SFX volume slider scales custom gameplay vs UI
- [ ] BGM volume independent; BGM stays under feature SFX
- [ ] UI clicks quieter than feature triggers

Paylines:

- [ ] `sfx_payline_draw` starts when line draw begins
- [ ] `sfx_payline_complete` near draw end / spark arrival
- [ ] Multiple lines: sequential/staggered — no ten-at-once stack
- [ ] Turbo: shorter presentation; overlap throttled
- [ ] Catch-up: no long cosmetic SFX spam

Scatter / Free Spins:

- [ ] Scatter land on meaningful Bib reel stop (throttled if several)
- [ ] Scatter trigger **once** when bonus confirmed (not per scatter)
- [ ] FS start once at Free Spins entry
- [ ] FS retrigger once per retrigger event
- [ ] Tier upgrade once when tier change is presented (not HUD rerender)

Features:

- [ ] Mystery open/reveal synced to Mystery presentation
- [ ] Token reveal synced to token value presentation
- [ ] Thermal synced to Thermal activation
- [ ] Gate synced to floor/replacement upgrade
- [ ] Judge collect with sweep
- [ ] Head Judge: pass 1 full cue; pass 2 accent (gainScale) — not awkward double restart
- [ ] Rejump: one coherent cue per activation; double Rejump sequential not clipping
- [ ] Wind charge / Wind upgrade (+ short transition after upgrade only)
- [ ] Coach: visual only (no dedicated SFX) — confirm no crash / no fake download

Rare / terminal:

- [ ] World Record sting first
- [ ] Max Win after WR (or on CapReached) — not muddy simultaneous overlap
- [ ] Soft BGM duck on FS trigger / WR / Max Win, then restore
- [ ] Bonus end on Free Spins end
- [ ] BAD/MISS: **not** on ordinary no-win base spins (optional / disabled)

Turbo / resume:

- [ ] Turbo feature chains: no painful SFX spam (payline/scatter/token limited)
- [ ] Catch-up / reconnect: no historical soundtrack replay
- [ ] Mid Free Spins resume — state only, no FS_START replay
- [ ] After Gate / Wind charge / before·after Rejump / before·after WR — audio only for newly presented events

Hygiene:

- [ ] No external audio URLs
- [ ] Missing file fails silent (no crash / no per-frame spam)
- [ ] BGM playlist unchanged (frostbet)

## Resume

- [ ] After board reveal
- [ ] After line wins
- [ ] Mid Coach / Mystery
- [ ] After Gate / mid Judge
- [ ] Before / during Rejump
- [ ] After Wind charge
- [ ] Mid Free Spins / after retrigger
- [ ] Before / after World Record
- [ ] Before / after final settlement  
  → Final reducer state matches uninterrupted play  
  → No historical SFX replay on catch-up

## Responsive

- [ ] 1920×1080
- [ ] 1280×720
- [ ] 960×540
- [ ] 640×360
- [ ] Mobile landscape  
  Board readable; HUD not overlapping; WR/buy fit; no overflow

## Font / offline

- [ ] No Typekit / Google Fonts network request
- [ ] Local `@font-face` only (`SkyjumpDisplay` / `SkyjumpUI` from `static/assets/fonts/skyjump/`)
- [ ] UI readable on system fallback stack if woff2 missing

## Phase 8C — final UI pack / win presentation

- [ ] BIG / MEGA / SUPER titles appear at presentation thresholds only (10× / 50× / 200×)
- [ ] WORLD RECORD title only when WR event / flag is set (not stake-threshold)
- [ ] MAX WIN title only on cap / max-win path (not stake-threshold)
- [ ] Count-up shows authoritative payout amount; animation cosmetic only
- [ ] Payline spark head + end glint visible on progressive lines
- [ ] Bonus / mode title banners for Free Spins, Retrigger, Tier Upgrade, modes
- [ ] Paytable / Info headers + panel decor resolve via `uiAssetRegistry`
- [ ] DEV Assets gallery lists all registry keys (inspector → Assets)
- [ ] No duplicate registry URLs; missing asset → graceful fallback (no crash)

## Phase 8C.1 — PNG alpha repair / visibility (Filip)

All Phase 8C pack files are `.png` RGBA after repair. Leave boxes unchecked until verified.

- [ ] **Asset alpha** — DEV inspector → **Assets** → switch **Checkerboard / White / Navy**; headers, decor, FX, and titles show true transparency (no solid black matte)
- [ ] **UI PACK SHOWCASE** — Scenario → **UI PACK SHOWCASE** (`ui:showcase`); pack chrome / plates / titles render without black boxes
- [ ] **BIG WIN (showcase)** — Scenario → **BIG WIN (showcase)** (`ui:big`); title + glow/snow/ice/sparkles (no coin/flash)
- [ ] **MEGA WIN (showcase)** — Scenario → **MEGA WIN (showcase)** (`ui:mega`); title + coin sparkle
- [ ] **SUPER WIN (showcase)** — Scenario → **SUPER WIN (showcase)** (`ui:super`)
- [ ] **MAX WIN (showcase)** — Scenario → **MAX WIN (showcase)** (`ui:max`); flash accent
- [ ] **WORLD RECORD (showcase)** — Scenario → **WORLD RECORD (showcase)** (`ui:worldRecord`); WR title + flash (optional book **wr-01**)
- [ ] **Paytable / Info transparency** — Scenario → **Paytable (decorated)** / **Info / Rules (decorated)** (`modal:paytable` / `modal:rules`); headers + panel decor have alpha, not opaque black rectangles
- [ ] **Status plate after spin** — any spin that settles a win bar (`showWin`); `SkyJumpV2StatusPlate` visible on board win bar
- [ ] **Mode badge during Free Spins only** — FS banner with `bonusHud.tier` set shows `SkyJumpV2ModeBadge`; **not** always-on in BASE
- [ ] **Payline spark on line wins** — any line-win fixture / spin; progressive path shows spark head + end glint

Matrix reference: `36A_UI_ASSET_VISIBILITY_MATRIX.md`.

## Assets / audio fallback

- [ ] Missing PNG → placeholder (never broken image)
- [ ] Drop PNG into `static/assets/skyjump_v2/symbols/` → appears after reload
- [ ] Remove PNG → placeholder returns
- [ ] Missing SFX does not crash

## Production hygiene

- [ ] `/dev-preview` 404 outside DEV
- [ ] No research JSON in prod bundle
- [ ] No V1 strip mounted as active game
