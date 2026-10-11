# SKYJUMP V2 — Phase 8F.1 Final BET HUD Redesign

**Branch:** `feat/skyjump-v2-5x5`  
**Date:** 2026-09-26  
**Scope:** Bottom bet / control HUD visual layout + style only  
**Primary verify:** `http://localhost:3011/live-preview` @ 1280×720  

Math / RGS / handlers / RTP / books / LUTs / mathVersion: **unchanged**.

---

## Before architecture

Phase 8F claimed a HUD redesign, but live QA still read as Stake/prototype chrome:

* Each Pixi control self-positioned along the bottom strip
* Compact layout incorrectly triggered at 1280 (`width < 1400`)
* Skin-only changes (fonts, SPIN label, opacity, weak glass)
* Individual button plates still competed with any new dock frame
* BET − / value / + read as three unrelated controls

---

## Final layout (1280×720 desktop tokens)

Centered cohesive dock driven by `getSkyJumpHudLayout()`:

| Token | Value |
| --- | --- |
| Dock width | **960px** |
| Dock height | **98px** |
| Bottom pad | **16px** |
| Horizontal pad | **22px** |
| Group gap | **18px** |
| Cluster gap | **8px** |

Hierarchy (left → right):

```
LEFT INFO (BALANCE | WIN)
  → BET CLUSTER [ − | VALUE | + ]
  → PRIMARY SPIN / STOP (88×88 circle)
  → BUY BONUS (138×50)
  → AUTO / TURBO (54×54 each)
  → MENU (48×48, dock edge)
```

Compact two-row fallback only when `ratio < 1.35` or `width < 900` — **not** at 1280×720.

---

## Control groups

### Dock frame (`SkyJumpHudFrame`)

* Dark navy translucent glass gradient
* Icy pale-blue edge + restrained gold top rail
* Inner highlight / sheen / soft outer shadow
* Sized via `getSkyJumpHudCssDock` to match Pixi dock bounds
* Mounted in production `Game.svelte` (same path as `/live-preview` / `/dev-preview`)

### LEFT INFO

* Shared navy info plate behind BALANCE + WIN
* Quiet `SkyjumpUI` labels, strong `SkyjumpDisplay` values
* Not styled as buttons

### BET CLUSTER

* One outer glass/metal plate with icy edge ring
* Internal separators between − / value / +
* Minus **48**, value **102**, plus **48**, height **~50–64** (cluster plate)
* ± use flat cluster glyphs (no second floating plates)

### SPIN / STOP (`ButtonBet`, skyjump only)

* Circular premium gold-metal control, **88px**
* Outer glow + crystalline inner ring
* Hover scale ≤ 1.03, pressed inset ~0.95
* STOP: warmer deeper gold fill + STOP copy (behavior unchanged)

### BUY BONUS

* **138×50**, dark icy fill, gold edge, subordinate to SPIN
* Hover / pressed / active / disabled states
* Opens existing buyBonus modal (no hardcoded costs)

### AUTO / TURBO

* Compact **54×54** mode controls
* Inactive: quiet navy + muted border
* Active: illuminated icy-blue (AUTO) / green-gold pulse (TURBO) — obvious at a glance

### Utilities

* MENU on dock right edge; flyout still hosts Paytable / Info / Settings / Sound / Language
* Smaller / quieter than SPIN

---

## Active-state styling

| Control | Inactive | Active |
| --- | --- | --- |
| AUTO | navy fill, muted ice border | bright ice fill + soft outer glow |
| TURBO | quiet navy, muted border | green fill + pulse sparks |
| BUY | dark gold fill | brighter gold edge / fill |
| SPIN→STOP | gold circular SPIN | deeper warm-gold STOP |

---

## SkyJump-only theme gating

All chrome branches gate on `stateUi.config.theme === 'skyjump'` (or SkyJump-only layout components: `SkyJumpHud`, `SkyJumpHudFrame`). Garden / miner paths unchanged.

---

## Old generic visual chrome removed

* SkyJump no longer draws `base_ticker` plates under meters (`UiLabel` skips tiled sprite when skyjump)
* BET ± no longer draw full independent navy plates inside the cluster (flat glyphs)
* BUY gift mark removed so secondary-primary button stays clean
* Dock frame is the primary grouping surface; cluster/info plates are intentional inner regions

---

## Behavior regression

| Control | Result |
| --- | --- |
| SPIN | handlers untouched (`ButtonBetProvider.bet`) |
| STOP | still clears `autoSpinsCounter` under `overlayOpen` |
| BET ± | same `setBetAmount` options walk |
| BUY | same `buyBonus` modal / disable path |
| AUTO | same autoSpin modal / counter stop |
| TURBO | same `updateIsTurbo` |
| Settings / Info / Sound | menu flyout unchanged |

Tests:

* `tools/skyjump/test-v2-phase8a-autoplay-stop.ts`
* `tools/skyjump/test-v2-phase8f.ts`
* `tools/skyjump/test-v2-phase8f1.ts`

---

## Visual acceptance (1280)

| Check | Expected |
| --- | --- |
| A SPIN primary | YES — largest circular CTA |
| B BET as one group | YES — shared cluster plate |
| C BUY own role | YES — secondary gold pill |
| D AUTO/TURBO on/off | YES — illuminated vs quiet |
| E BALANCE/WIN info | YES — info plate, not buttons |
| F One cohesive dock | YES — centered glass dock |

---

## Files touched

* `frontend/packages/components-ui-pixi/src/skyjumpHud.ts`
* `frontend/packages/components-ui-pixi/src/components/SkyJumpHud.svelte`
* `frontend/packages/components-ui-pixi/src/components/ButtonBet.svelte`
* `frontend/packages/components-ui-pixi/src/components/UiButton.svelte`
* `frontend/packages/components-ui-pixi/src/components/ButtonBuyBonus.svelte`
* `frontend/packages/components-ui-pixi/src/components/LabelBet.svelte`
* `frontend/packages/components-ui-pixi/src/components/UiLabel.svelte`
* `frontend/apps/poc/src/components/skyjump/SkyJumpHudFrame.svelte`
* `tools/skyjump/test-v2-phase8f1.ts`
* `docs/skyjump-v2/40_FINAL_BET_HUD_REDESIGN.md`
