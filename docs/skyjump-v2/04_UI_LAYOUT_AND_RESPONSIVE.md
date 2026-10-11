# SKYJUMP V2 — UI Layout and Responsive Behaviour

**Status:** Design only. No final art.  
**Primary desktop composition reference:** 1280×720 (16:9).  
**Do not** hardcode the runtime canvas to 1280×720. Scale to the actual Stake viewport.

---

## 1. Audit of the current V1 implementation

### 1.1 Pixi logical stage (`utils-layout`)

`frontend/packages/utils-layout/src/createLayout.svelte.ts` already letterboxes a **logical** size into the window:

- `scale = min(canvasW / logicalW, canvasH / logicalH)`
- main container centred
- layout type from aspect + shortest side: `desktop | landscape | tablet | portrait`

POC SkyJump overrides (`frontend/apps/poc/src/game/stateLayout.ts`):

| Layout | Logical size | Aspect |
| --- | --- | --- |
| desktop | **1422×800** | 16:9 |
| landscape | 1600×900 | 16:9 |
| tablet | 1000×1000 | 1:1 |
| portrait | 800×1422 | 9:16 |

This is **already** a design-coordinate + contain-scale system. It is not locked to 1280×720, and it should not be thrown away.

HUD Pixi controls (`SkyJumpHud.svelte`) sit in `MainContainer standard` using `mainLayoutStandard()` (1920×1080 map inside the helper) **and** a CSS glass dock (`SkyJumpHudFrame.svelte`) positioned via `getSkyJumpHudCssDock`. That dual system works on desktop; it is fragile if HTML gameplay is sized in `vw`/`vh` independently of the Pixi scale.

### 1.2 HTML gameplay is **not** in the letterbox

V1 board (`SkyJumpReelStrip.svelte`), weather, overlay, brand, menu are **HTML siblings** of the Pixi `<App>` inside `.skyjump-viewport` (`100%` × `100dvh`). They use CSS `min(86vw, …)` and `@media (max-width: 720px)`.

Consequences:

- Pixi HUD letterboxes; HTML strip scales with the **browser**, not the same logical stage
- Stake iframe sizes that are not full-window can clip or leave empty bands
- Overlay was historically `position: fixed` (later patched to the viewport container)

**V2 proposal:** do not replace `createLayout`. Put the **5×5 board and feature chrome in the same scaled stage as the HUD** (Pixi and/or a single HTML stage that uses the same `x, y, scale, width, height` as `mainLayout()`).

### 1.3 What to keep vs change

| Piece | Verdict |
| --- | --- |
| `createLayout` contain-scale | **KEEP** |
| SkyJump `mainSizesMap` | **ADAPT** — desktop logical 1280×720 (or keep 1422×800 and treat 1280×720 as a composition grid mapped into it). Prefer **1280×720 desktop** so art and layout docs share numbers |
| `layoutType` breakpoints | **KEEP** (375 / 480 / 820 / 1024, ratio 1.3 / 0.8) |
| HTML `vw` board | **REPLACE** for the 5×5 |
| Pixi SkyJump HUD dock | **KEEP** with safe-area padding |
| Farmer `Board.svelte` 5×3 `utils-slots` | **Not mounted** today; do not resurrect as V2. Optional later reuse of spin maths only |
| `Win.svelte` fullscreen | Stay unmounted; V2 uses overlay/toast |
| `env(safe-area-inset-*)` on HUD | **KEEP** and extend to portrait board |

### 1.4 Do not use browser zoom

Layout must use the layout scale. Stake zoom / OS scale is out of our control; we still contain inside the iframe client size (`innerWidth` / `innerHeight` as today).

---

## 2. One logical coordinate system

**Desktop reference canvas:** 1280×720.

Runtime:

```
stage.w = 1280
stage.h = 720
scale = min(viewW / 1280, viewH / 720)
offset = centre (letterbox bars in night navy #071526)
```

Portrait and tablet use **different logical maps** (not a rotated 1280×720 squeezed until unreadably small):

| Variant | Logical | Notes |
| --- | --- | --- |
| Desktop landscape | 1280×720 | Primary composition |
| Tablet ~square | 1000×1000 | Board centred, HUD bottom |
| Mobile landscape | 1280×720 scaled, tighter chrome | Same 16:9, smaller safe HUD |
| Mobile portrait | 720×1280 | Intentional alternate: board upper-centre, Flight Multiplier under logo, HUD bottom |
| Ultra-compact embed | 960×540 logical then scale | Hide decorative jumper; keep 5×5 readable |

Letterbox colour: existing `#071526`. No gameplay controls outside the scaled stage. Stake HUD must remain inside the iframe.

Dialogs (paytable, rules, settings, buy confirm): HTML modals already overlay the viewport. They **must scroll** (`max-height: min(90dvh, …); overflow-y: auto`) including safe-area bottom.

---

## 3. Desktop landscape composition (1280×720)

```
+------------------------------------------------------------------+
|  BG: snowy ski-jump stadium (full bleed inside stage)            |
|  [LOGO]     bonus chip / FS meters                 [G = x12]     |
|                                                                  |
|  RUN-UP  TAKEOFF  FLIGHT     +-------------------+               |
|  [ x2 ]  [ x2  ]  [ x3 ]     |                   |   jumper art  |
|                              |      5 x 5        |   (optional)  |
|                              |     reel board    |               |
|                              |                   |               |
|                              +-------------------+               |
|                                                                  |
|  [ BALANCE | WIN | TOTAL BET ]  MENU BUY AUTO  -  BET  +  TURBO  |
+------------------------------------------------------------------+
```

Hierarchy:

1. **Background** — stadium / hill (reuse V1 plates; camera crop)
2. **Top** — SkyJump logo, bonus state, global Flight Multiplier
3. **Left or top-side feature column** — RUN-UP / TAKEOFF / FLIGHT + product G
4. **Centre** — 5×5 board (largest readable grid)
5. **Bottom** — existing Stake-compatible HUD

During Free Spins, top/feature area also shows:

- bonus tier name
- spins remaining (Pixi `LabelFreeSpinCounter` already exists — **ADAPT**)
- persistent Mystery target icons (placeholder tiles)
- token floor tier
- persistent G if Perfect V

Minimum board cell size on 1280×720: **72px** logical (5×72 = 360 plus gaps ≈ 400–440). That leaves room for HUD (~90–110px) and top chrome (~80px).

---

## 4. Layout variants

### 4.1 Desktop landscape (primary)

- Board centre
- Feature column left of board (or a compact strip immediately above the grid if width is tight)
- Jumper / hill art right, **never covering cells**
- HUD one row

### 4.2 Tablet (almost square)

- Board slightly higher than geometric centre
- Feature stages as a **horizontal** strip above the grid (three pills + G)
- HUD one row if width ≥ 700 CSS px, else two compact rows (V1 portrait HUD already does two rows)

### 4.3 Mobile landscape

- Same 16:9 composition, smaller font
- Hide decorative jumper
- Feature stages as mini pills above board
- HUD stays one row; hit targets ≥ 40px CSS after scale

### 4.4 Mobile portrait (intentional alternate)

```
720x1280 logical
[ logo + G ]
[ RUN-UP | TAKEOFF | FLIGHT ]
[ 5x5 board — width min(92% of 720, cells readable) ]
[ FS chips if active ]
[ HUD two rows + safe-area ]
```

Board remains square. Extra vertical space is atmosphere, not stretched cells.

### 4.5 Ultra-compact embed (e.g. 640×360 iframe)

- Logical 1280×720 scaled (~0.5)
- Cells ~36px logical → ~18px CSS: **too small**
- Fallback: switch to “compact mode” at `min(viewW, viewH) < 400` or scale < 0.55:
  - drop atmosphere particles
  - feature stages become a single `G` badge + expandable tray
  - board uses remaining height above HUD with a **minimum 44px CSS cell**; if still impossible, letterbox the stage and allow vertical scroll **only for help modals**, never for the spin button

If a Stake embed cannot fit 5×5 + HUD, prefer shrinking chrome, not shrinking cells below readability.

---

## 5. Controls and clipping rules

- Spin / bet / turbo / auto / buy / menu: existing Pixi HUD — keep inside `MainContainer`
- No extra HTML buttons outside the stage
- Result presentation: **overlay card or toast inside the stage**, not a fullscreen route, not `position: fixed` on `document.body`
- Help / paytable: scrollable modal (`components-shared` Popup — already used)
- Space-to-spin: keep `EnableSpaceHold`; ignore Space while overlay open (V1 behaviour)
- Turbo: timing only

---

## 6. Placeholder visual language (Phase 1)

Rectangles, flat icons, text IDs. See `07_PLACEHOLDER_ASSET_LIST.md`.

- Board: dark ice panel, 1px gold hairline
- Cells: solid fill + 2–3 letter ID
- Payline highlight: cyan polyline through cell centres (data from `skyjumpLineWins`)
- Winning cells: gold stroke
- Mystery: pulsing white diamond, ID `MYST`
- Tokens: hexagon, ID `T1`…`T6` + value text from the event (never rolled)

---

## 7. Implementation notes (not this task)

- Drive HTML overlay positions from `mainLayout()` the same way `getSkyJumpHudCssDock` does, **or** move the 5×5 into Pixi
- Recommendation: **Pixi 5×5** for symbols (crisp scale) + HTML for FS chips if needed, both parented to the scaled stage
- Add `safe-area-inset-top/bottom/left/right` padding on the stage wrapper
- QA viewports: 1280×720, 1920×1080, 1366×768, 1024×768, 820×1180, 844×390, 390×844, 640×360, 480×900 (V1 already cites 480×900)
