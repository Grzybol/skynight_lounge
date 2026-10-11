# SKYJUMP V2 — Phase 8F Real UI Implementation Matrix

**Branch:** `feat/skyjump-v2-5x5`  
**Date:** 2026-09-26  
**Primary verify:** `/live-preview` @ 1280×720  
**Rule:** “Registry ready” is not enough — status = **ACTUALLY RENDERED** in live game.

---

## Production tree (live)

```
Game.svelte
├── SkyJumpBackground / Atmosphere / Brand
├── SkyJumpHudFrame          ← restyled glass dock
├── SkyJumpUtilityBar
├── Pixi UI → SkyJumpHud     ← SPIN / ± / BUY / AUTO / TURBO (restyled)
├── SkyJumpV2Board           ← board, status plate, paylines, banners, celebrations
└── Modals → PayTable / GameRules
```

V1 `SkyJumpReelStrip` / result overlay: **not mounted**.

---

## Matrix

| UI / asset | Production component | Real game trigger | Visible in live game? | DEV scenario | Screen |
| --- | --- | --- | --- | --- | --- |
| 5×5 board + symbols | `SkyJumpV2Board` | play / spin books | YES | BASE spin | play |
| Status plate `ui_status_plate` | `SkyJumpV2StatusPlate` in board | always on play; READY / win copy | YES | idle + line win | play |
| Payline stroke | SVG `.paths` in board | `skyjumpV2LineWin` / result lines | YES | line win | play |
| Spark `fx_payline_spark_head` | SVG `<image data-test=payline-spark>` | progressive draw (`pointAlong`) | YES (above tiles, 56px box) | line / multi-line | play |
| End glint `fx_payline_end_glint` | SVG `<image data-test=payline-glint>` | draw complete | YES (64px box) | line win | play |
| PAYLINE_DRAW / COMPLETE | `playV2AudioHook` in `animatePathDraw` | draw start / endpoint | YES (audio) | line win | play |
| SPIN / STOP | `ButtonBet` (theme skyjump) | Pixi HUD | YES — label **SPIN**, gold STOP | BASE | play |
| BET − / + | `ButtonDecrease` / `Increase` + cluster plate | Pixi HUD | YES — unified cluster | BASE | play |
| BUY BONUS | `ButtonBuyBonus` | Pixi HUD | YES (gold accent) | buy modal | play |
| AUTOPLAY | `ButtonAutoSpin` | Pixi HUD | YES (active navy) | autoplay | play |
| TURBO | `ButtonTurbo` | Pixi HUD | YES (distinct on/off) | turbo | play |
| HUD glass dock | `SkyJumpHudFrame` | play | YES | BASE | play |
| FS banner `ui_bonus_free_spins` | `SkyJumpV2TitleBanner` kind=bonus | `skyjumpFreeSpinsStart` → `skyjumpV2BonusTitles` | YES | FS start | play |
| Retrigger PNG | TitleBanner kind=retrigger | `skyjumpBonusUpgrade` spins | YES | retrigger | play |
| Tier upgrade PNG | TitleBanner kind=tierUpgrade | `skyjumpBonusUpgrade` tierChanged | YES | tier upgrade | play |
| Mode LH/SF/WC/PV | TitleBanner kind=mode | after FS / tier banners | YES | FS tiers | play |
| Mode badge plate | `SkyJumpV2ModeBadge` in FS HUD | Free Spins active | YES | FS | play |
| BIG/MEGA/SUPER | `SkyJumpV2WinCelebration` | `skyjumpV2Result` classify ≥10/50/200× | YES | win scenarios | play |
| MAX | celebration | `capHit` / max path | YES | MAX | play |
| WORLD RECORD | celebration + overlay | `skyjumpWorldRecord` / WR flag | YES | WR | play |
| Win FX glow/snow/sparkle/coin/flash | celebration FX wraps | tier intensity | YES | BIG→WR | play |
| Paytable headers/decor | `SkyJumpV2PayTable` | MENU → paytable | YES | modal:paytable | modal |
| Info headers/decor | `SkyJumpV2GameRules` | MENU → rules | YES | modal:info | modal |

---

## Hard fixes in 8F

1. **Payline spark buried** — SVG was under `.tile.hit` (z-index 5 > 4). Moved SVG after tiles, `z-index: 12`.
2. **Spark tiny vs padded PNG** — display box raised to **56 / 64** so opaque core reads as target visual size.
3. **Turbo skipped spark** — threshold was `lineDrawMs > 160`; now `> 0`.
4. **HUD looked Stake-generic** — SPIN label, larger primary, STOP gold, bet cluster plate, richer dock glass.

---

## Stale paths bypassed (visual only)

| Path | Action |
| --- | --- |
| SVG paylines under tiles | Reordered / z-index raised |
| ButtonBet “BET” label on SkyJump | Forced **SPIN** for `theme === 'skyjump'` |
| V1 reel/overlay | Still not mounted (unchanged) |

---

## Remaining debt

| Item | Status |
| --- | --- |
| `ui_tier_large_hill` ≡ `ui_tier_ski_flying` | STILL PRESENT — no invented art |
| Wins &lt; 10× | Status plate only (celebration threshold by design) |

---

## Tests / build

- `tools/skyjump/test-v2-phase8f.ts` — hard-wiring assertions  
- Existing V2 / audio / autoplay suites  
- Production build  

Filip hands-on QA still required for visual approval.
