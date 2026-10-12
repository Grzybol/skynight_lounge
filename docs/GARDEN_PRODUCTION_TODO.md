# Garden Bounty production handoff

Last updated: 2026-09-15

Active product branch: `feat/garden-reskin` (merged to `main` via PR #2).
Readiness docs branch: `docs/stake-com-readiness` (from `origin/main`).

Target: a reviewable Garden Bounty build prepared for Stake Engine developer testing
and eventual Stake.com release.

Stake.com gap analysis and phased plan (2026-09-14):

- [STAKE_COM_READINESS.md](./STAKE_COM_READINESS.md) — what exists vs what is missing
- [STAKE_COM_ROADMAP.md](./STAKE_COM_ROADMAP.md) — development plan to a real game

## How to continue

Read `AGENTS.md`, invoke `$garden-bounty-development`, inspect `git status -sb`, and
start from the first unchecked item below. Do not treat `/dev-preview` payout sampling
as production math. Follow the roadmap phases: spec lock → math books → FE events/QA
→ assets/licensing → ACP session → review package.

## Current checkpoint

- Garden art, background, symbols, HUD, modals, loader, ambience, win presentation,
  Free Spins, transitions, and sunflower token are active on `main`.
- Local `/dev-preview` verified 2026-09-14 (Vite on **4010** — Windows Hyper-V
  blocks 3010 here): idle HUD, garden 5×3 board, Space/BET debit `$1000 → $999`,
  portrait 480×900 reflow OK, `/` waits on authenticate without RGS.
- Python **3.12.10** and Rust/Cargo **1.97.1** are installed on this machine.
  Project venv is `math/.venv` (gitignored). Local compressed
  `library/publish_files/` exists after the 100k/mode run; it is not in git.
- Frontend vs Python RTP and W/H1 paytable are locked in `docs/GAME_SPEC.md`
  (RTP **0.97**, W/H1 **10/20/50**). Run `math/tests/test_config_parity_poc.py`.
- Local math: uncompressed 100-sim debug + compressed **100k/mode**
  optimizer pack (LUT RTP 0.97, RGS format checks passed). `library/` stays
  gitignored — hashes in `docs/MATH_RUN.md`.
- HUD ticker and logo both say `GARDEN BOUNTY`.
- Garden HUD / slot (2026-09-14): desktop slot group scales ~1.18 around the
  reel board so the wooden frame and symbols fill more of the viewport.
  Side HUD uses `HUD_SCALE.side` 1.42 / plus 1.42; bottom HUD uses 1.16.
  Side rails still track the scaled outer frame box.
- WIN meter is running net for Auto Spin and manual BET (stake subtracted
  each round, payouts added, can go negative). Auto Spin start still
  resets the meter for a new session. Bottom WIN/AUTO/BET/TURBO align to
  the slot frame center. Menu flyout keeps full button spacing and is
  vertically centered on the left rail (not packed against the top).
  Single-win autospin limits still use the current round payout only.
  H1 straw hat is a plain farmer hat after a local Qwen Image Edit + BiRefNet
  pass (seed `9302105`); no lamp or circular badge remains.
- Stake Engine ACP credentials, final game/team ID, and release approval remain
  external.

## P0 — close the visual release candidate

- [ ] Run a complete desktop regression in `/dev-preview`: base spin, random win,
      symbol win, BIG WIN/token particles, anticipation, loader, bonus flow, Free
      Spins counter, all modals, real BET controls, Auto Spin, Buy Bonus, and reset.
- [ ] Repeat the relevant flows at 480x900 portrait and fix clipping, unreadable
      labels, oversized modals, or inaccessible controls.
- [ ] Confirm every completed flow returns to `Auto 0 · Machine idle`.
- [x] Remove the H1 miner headlamp from the straw hat (ComfyUI Qwen Image Edit +
      BiRefNet, seed `9302105`, 2026-09-15).
- [ ] Replace H4/H5 and default demo audio, or record explicit commercial reuse
      permission. Do not assume sample-asset licensing.
- [ ] Remove or quarantine inactive demo assets only after the asset audit confirms
      they are not loaded and recovery is preserved in Git.

## P0 — lock the production game specification

- [ ] Confirm the final provider/team name, public game title, Stake Engine game ID,
      semantic version, target markets, and whether Buy Bonus is permitted.
- [x] Choose one target RTP and document it. Current mismatch: frontend `0.9700`,
      Python math `0.9670`.
- [x] Reconcile the entire frontend/Python paytable. Known mismatch: W and H1 payouts
      differ between `frontend/apps/poc/src/game/config.ts` and
      `math/games/0_0_poc/game_config.py`.
- [x] Confirm base/bonus costs, max win, Free Spins triggers/retriggers, wild
      multipliers, and paylines. See `docs/GAME_SPEC.md`. Volatility / hit rate /
      bonus frequency remain PAR outputs from Phase 1 math.
- [ ] Rename remaining placeholders such as `poc_studio`, `poc_slot`, `0_0_poc`,
      `PoC Slot (Lines)`, and version `0.0.0` after Stake Engine supplies/approves the
      final identifiers.

## P1 — create production math

- [x] Install and verify Python 3.12+, project dependencies, Rust, and Cargo in a
      project-local environment. `math/.venv` (3.12.10) is local-only. Optimizer
      `cargo build --release` succeeded.
- [x] Run a small uncompressed batch for both modes and inspect books/events manually.
      100+100 sims on 2026-09-14. See `docs/MATH_RUN.md`.
- [x] Verify every event type against frontend handlers on that debug batch
      (`wincap`, `freeSpinRetrigger` included). Amounts are bet-units × 100.
- [x] Add automated consistency checks for frontend/Python symbols, paytable, mode
      costs, RTP, and max win (`math/tests/test_config_parity_poc.py`). Event-contract
      parity is still manual.
- [x] Run production-scale compressed simulations. Use at least 100k outcomes per
      mode; increase the count when repeat diversity or distribution quality demands
      it. 100k/mode on 2026-09-14 — see `docs/MATH_RUN.md`.
- [x] Optimize lookup weights to the approved RTP and volatility profile.
      LUT RTP 0.97 both modes. Bonus CVaR still above the sample 3-star 800 cap
      (warning only).
- [x] Generate and review PAR/stat analysis: RTP split, hit rate, bonus frequency,
      average bonus value, payout distribution, volatility, and max-win probability.
- [x] Run all RGS verification/format checks. Asserts passed; 3-star helper warns
      on RTP 0.97 and bonus CVaR.
- [x] Inspect `library/publish_files/`: `index.json`, one optimized lookup CSV and one
      `.jsonl.zst` book per mode, matching IDs/payouts, valid hashes, and correct
      mode costs. Pack is gitignored; hashes are in `docs/MATH_RUN.md`.

## P1 — Stake Engine developer integration

- [ ] Obtain/confirm Stake Engine ACP access, team/provider assignment, game ID, and
      developer environment. These are external prerequisites.
- [ ] Upload the math publish package and static frontend build to the ACP.
- [ ] Launch through a real developer session and verify URL-provided `sessionID`,
      `lang`, `device`, and dynamic `rgs_url`.
- [ ] Test authenticate, balance, bet levels, min/max/step/default bet, currencies,
      base play, Buy Bonus, payout settlement, and `end-round`.
- [ ] Test refresh/close during an active round, resume, replay, duplicate action
      prevention, network errors, maintenance/error modals, and insufficient balance.
- [ ] Test jurisdiction flags: autoplay, turbo/super-turbo, slam stop, spacebar,
      fullscreen, Buy Bonus, RTP display, net position, timer, and minimum round
      duration.
- [ ] Test desktop/mobile Stake iframe sizes, focus/visibility, audio lifecycle, and
      performance on representative low-end devices.

## P2 — release package and review

- [ ] Remove dev-only routes and diagnostics from the uploaded production package, or
      verify they are unreachable from the release entry point.
- [ ] Produce release notes, final asset provenance/licensing record, final PAR sheet,
      QA evidence, known limitations, and rollback version.
- [ ] Confirm repository license and third-party attribution obligations.
- [ ] Submit the game for Stake review and address ACP/RGS validation findings.
- [ ] Promote only the exact reviewed frontend and math versions to production.

## Definition of ready for Stake review

- [ ] No unchecked P0/P1 item remains.
- [ ] Frontend and math configurations are mechanically identical where required.
- [ ] Production build and RGS format checks pass from a clean checkout.
- [ ] All real-session rounds settle exactly once and recover after interruption.
- [ ] Desktop and portrait QA pass without critical defects.
- [ ] Every shipped visual/audio asset has documented commercial rights.
- [ ] ACP identifiers, uploaded hashes, release version, and rollback artifact are
      recorded.

## Handoff log

- 2026-07-27: Pushed `feat/garden-reskin` and opened draft PR #2 against `main`:
  `https://github.com/ProDruk3D/slot_v1/pull/2`.
- 2026-07-27: Created the production-readiness checklist after completing the Garden
  Bounty visual/UI pass. Immediate next action is the full desktop/portrait regression,
  followed by final spec lock and production math generation.
- 2026-09-14: Phase 1 debug math. `math/.venv` + `POC_DEBUG_BATCH=1` produced 100
  uncompressed books per mode; every event type maps to a frontend handler
  (`docs/MATH_RUN.md`). Next: production-scale compressed 100k/mode + optimizer.
- 2026-09-14: Phase 1 10k compressed smoke + Rust optimizer. LUT RTP 0.97,
  publish zst hashes match `config.json`. SDK 3-star helper warns on RTP
  0.97>0.967 and bonus cvar. 100k/mode started.
- 2026-09-14: Phase 1 100k/mode complete (~4 min). Publish zst+LUT hashes
  recorded in `docs/MATH_RUN.md`. Next: leftover Phase 2 desktop/portrait
  `/dev-preview` regression, then audio/licensing and ACP.
- 2026-09-14: Desktop `/dev-preview` on 4010 (real window, not headless):
  idle HUD, paytable Gardener/Wild 10/20/50 + Harvest Badge, real BET
  `$1000 → $1001` after a $1 win and back to `Machine idle`, bonus chrome
  (THE GARDEN BLOOMS → FREE SPINS 10 AWARDED → TOTAL WIN $12.34 + sunflower
  tokens). Portrait HUD reflow still shows WIN on top and BALANCE/BET at
  the bottom. H1 lamp badge remains. Auto Spin, real Buy Bonus, loader,
  and anticipation were not fully re-run this pass.
- 2026-09-15: Menu flyout is vertically centered on the left rail. H1 miner
  headlamp later removed with local ComfyUI Qwen Image Edit (see below).
- 2026-09-14: Local Buy Bonus is no longer a 1-spin $0 stub. It plays a
  compact 3-FS book with wild 2×, retrigger chrome, and a 20× credit.
  Tester chrome on `/dev-preview` is a compact overlay so the board stays
  clickable. Next manual pass: BET, Auto Spin, Buy Bonus, FS continue.
- 2026-09-14: Garden HUD/modals no longer use the thick gold/white “flash
  game” chrome. Pixi buttons have thinner timber-gold rims, hover lift,
  and press-in; Turbo/Auto active is sunflower-green, not a white stroke.
  Auto-spin counts, bet chips, and sound ON use a gold fill + leaf-green
  pip. Verified on `/dev-preview` (4010): idle HUD, Auto Spin `10`→`100`,
  running auto badge `96`, Bet Menu `$1.00` selected, gold Confirm/Start
  CTAs. Next: remaining P0 desktop/portrait regression, then audio/ACP.
- 2026-09-14: HUD/modal buttons are now timber plaques (ink outline, brass
  bolts, painted leaf face) matching the reel frame — not flat gold-stroke
  pills. Verified idle HUD + Auto Spin chips on `/dev-preview` (4010).
  Next: remaining P0 desktop/portrait regression, then audio/ACP.
- 2026-09-14: Garden HUD no longer overlays the reel frame. Board nudged
  up slightly; meters + controls sit in a dock under the timber (desktop)
  and drop below the frame in portrait. Verified `/dev-preview` 4010
  desktop and 480×900. Next: remaining P0 regression, then audio/ACP.
- 2026-09-15: H1 miner headlamp outline removed with local ComfyUI Qwen Image
  Edit (seed `9302105`, denoise 0.7) and BiRefNet; atlas H1 cell replaced.
  Next: remaining P0 desktop/portrait regression, licensed audio, ACP.
