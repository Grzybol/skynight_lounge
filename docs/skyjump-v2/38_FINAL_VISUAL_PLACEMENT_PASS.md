# SKYJUMP V2 — Phase 8E Final Visual Placement / Scale / Timing Pass

**Branch:** `feat/skyjump-v2-5x5`  
**Date:** 2026-09-26  
**Primary:** `/live-preview` logical **1280×720**  
**Scope:** placement · scale · spacing · z-order · timing · transitions only  
**Not changed:** math, RTP, books, LUTs, buy costs, PNG bytes, asset imports

---

## Visual QA matrix (internal)

| Family | Size | Seat | Clip | Weight | Z | Timing | 1280 readability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASE board | OK | center | OK | dominant | board | — | OK |
| Line / multi-line | spark/glint sized to cell | path tip | OK | line > FX | paylines | progressive | OK |
| BIG→WR titles | shared slot + mild scale ramp | above center | contain | progressive | celebration 40 | count+hold | OK |
| Count-up | display font, scale on length | under title | no overflow | high | celebration | tiered | OK |
| FS / Retrigger / Tier | shared banner kinds | mid-upper | contain | FS>Tier>retrigger | banner 36 | sequenced | OK |
| LH / SF / WC / PV | identical mode slot | same seat | contain | art only | banner 36 | modeTitleMs | OK |
| Status plate | 40–48px slot | under board | OK | compact | 8 | — | OK |
| Mode badge | ≤11.5rem, ellipsis | FS HUD | no clip | << mode banner | HUD | — | OK |
| Paytable / Info headers | max-h 44px lettering | modal hero | contain | compact | modal | — | OK |
| Panel decor | topper≤260 · corner 28 · divider thin | accents | none | decorative | 0 | — | OK |
| Payline spark | **24px** | tip | OK | small point | path | draw | OK |
| Payline end glint | **30px** | endpoint | OK | < line | path | hold | OK |

Filip hands-on approval still required — this table is engineering self-check only.

---

## Wrapper / scale rules

Constants live in `frontend/apps/poc/src/game/skyjump_v2/presentationLayout.ts`.

### Win titles (one family)

| | Value |
| --- | --- |
| Slot max width | 520px |
| Slot height | 148px |
| Fit | `object-fit: contain` |
| Scales | BIG 0.90 · MEGA 0.96 · SUPER 1.00 · MAX 1.06 · WR 1.12 |

Stack at 1280: **title → amount → FX field**, stage seated ~6% above center; celebration inset leaves bottom HUD clear.

### Bonus / mode banners

| Kind | Max W | Max H | Timing NORMAL |
| --- | --- | --- | --- |
| bonus (FS) | 480 | 132 | fsBannerMs 520 |
| retrigger | 360 | 100 | retriggerBannerMs 360 |
| tierUpgrade | 500 | 140 | tierUpgradeMs 640 |
| mode (LH/SF/WC/PV) | 460 | 124 | modeTitleMs 480 |

Never stack bonus + mode simultaneously — sequential show/hide with short gap.

### Status / mode plates

| | Value |
| --- | --- |
| Status plate | min-h 40 · max-h 48 · full board width · pointer-events none |
| Mode badge | min-w 6.5rem · max-w 11.5rem · ellipsis for PERFECT V |

### Modal headers

| | Value |
| --- | --- |
| Section header | max-w 300 · max-h **44px** · contain |
| Card header | max-w 220 · max-h 36px |

### Panel decor

| | Value |
| --- | --- |
| Topper | max-w 260 · max-h 36 |
| Corner | 28px |
| Divider | max-w 320 · max-h 10 · opacity 0.55 |
| Interaction | `pointer-events: none` on all decor |

### Payline FX

| | Visible size |
| --- | --- |
| Spark head | **24px** (target 18–28) |
| End glint | **30px** (target 24–34) |

---

## Timing rules (cosmetic)

| Event | NORMAL | TURBO |
| --- | --- | --- |
| BIG count-up | 1000ms | ×0.32 |
| MEGA count-up | 1300ms | ×0.32 |
| SUPER count-up | 1600ms | ×0.32 |
| MAX count-up | 2100ms | ×0.32 |
| WR count-up | 2400ms | ×0.32 |
| Hold after count | BIG 650 → WR 1500 | ×0.38 |
| FS banner | 520 | 140 |
| Retrigger | 360 | 90 |
| Tier upgrade | 640 | 160 |
| Mode title | 480 | 120 |

Settlement / book order unchanged.

### Transitions

- Win stage / title: opacity + slight scale (cubic-bezier premium ease)
- Banners: opacity + slight vertical settle
- No cartoon overshoot

---

## Z-order

1. Background  
2. Board surface / symbols  
3. Paylines + spark/glint  
4. Feature FX  
5. Bonus / mode banners (36)  
6. Win celebrations (40)  
7. Stake HUD / utility (controls remain usable; celebration leaves bottom clear)

All raster FX / plates / banners: `pointer-events: none` except celebration dismiss surface.

---

## Remaining human QA

- [ ] Filip: BIG≠WR intensity at 1280  
- [ ] Filip: FS → mode sequence feel  
- [ ] Filip: Paytable / Info header density in modal  
- [ ] Filip: status READY / NO WIN / WIN / long labels  
- [ ] Responsive presets only check uniform scale survivability  

### Tier emblem debt

`ui_tier_large_hill.png` ≡ `ui_tier_ski_flying.png` — **STILL PRESENT** (outside 29-pack). Do not invent art.

---

## Verification

- V2 frontend / audio / autoplay tests: **PASS**
- Production build: **PASS**
- 29/29 UI pack + 25/25 symbols intact
- Math unchanged
