# SKYJUMP V2 — Placeholder Asset List

**Status:** Inventory for final art. Phase 1 uses programmatic placeholders only.  
**Do not** generate final artwork in the design phase. **Do not** use cloud image APIs. Later raster work: local ComfyUI `http://127.0.0.1:8188` only.

Each Phase 1 placeholder must be distinguishable by **text ID + simple shape + temporary colour**.

---

## 1. Placeholder rules

- Tile size: square, logical ~72–96 px on 1280×720
- Font: condensed sans, high contrast
- No logos, no watermarks, no other-studio iconography, no Nordic/Odin marks
- Values on tokens come from **events**, not from art variants (one art per tier; number is text overlay)

Temporary palette (hex):

| Role | Fill | Ink |
| --- | --- | --- |
| Night panel | `#0B1C33` | |
| Gold stroke | `#E8C872` | |
| Ice | `#7ED6FF` | `#071526` |

---

## 2. Regular pay symbols

| ID | Name | Shape | Colour | Label |
| --- | --- | --- | --- | --- |
| `P1` | Flying jumper | tall triangle | `#F4C430` gold | P1 |
| `P2` | Crystal trophy | diamond | `#5EEAD4` cyan | P2 |
| `P3` | Golden helmet | hexagon | `#D97706` amber | P3 |
| `M1` | Jumping skis | parallelogram | `#0F766E` teal | M1 |
| `M2` | Flight goggles | oval | `#7C3AED` violet | M2 |
| `M3` | Ski boots | rounded square | `#2563EB` steel | M3 |
| `L1` | Wind sock | chevron | `#86EFAC` mint | L1 |
| `L2` | Snow badge | circle | `#F8F4E8` cream | L2 |
| `L3` | Start flag | rectangle | `#94A3B8` slate | L3 |

**Final art (later):** illustrated ski-jump iconography matching each name. Still 9 regulars. Register in `frontend/apps/poc/src/game/assets.ts`.

---

## 3. Flight Tokens

Hexagon tiles. Fill intensity increases with tier. Overlay `value` from the book (e.g. `25x`).

| ID | Tier name | Fill | Label |
| --- | --- | --- | --- |
| `T1` | Rookie | `#64748B` | T1 |
| `T2` | K-point | `#38BDF8` | T2 |
| `T3` | Large hill | `#2563EB` | T3 |
| `T4` | Ski flying | `#7C3AED` | T4 |
| `T5` | World cup | `#DB2777` | T5 |
| `T6` | World record | `#F59E0B` + gold stroke | T6 |

**Final art:** six distinct token medals / bibs / crystals — winter sports, not generic coin piles.

---

## 4. Specials

| ID | Name | Shape | Colour | Label |
| --- | --- | --- | --- | --- |
| `COACH` | Coach Signal | whistle / rectangle + bar | `#F97316` orange | COACH |
| `MYSTERY` | Snowburst Mystery | pulsing diamond | `#FFFFFF` / ice | MYST |
| `THERMAL` | Thermal Lift | up-arrow | `#22C55E` green | THRM |
| `UPGRADE` | Gate Upgrade | gate / arch | `#A3E635` lime | GATE |
| `REJUMP` | Rejump | circular arrows | `#38BDF8` | REJP |
| `JUDGE` | Judge | square + gavel bar | `#E5E7EB` | JUDG |
| `HEAD_JUDGE` | Head Judge | double square | `#FDE68A` | HDJ |
| `WIND_KEY` | Wind Key | key / wind barb | `#67E8F9` | WIND |
| `WORLD_RECORD` | World Record | star | `#FBBF24` | WR |
| `SCATTER` | Competition Bib | bib pentagon | `#F43F5E` red | BIB |

Mystery **resolved** cells switch to the result’s placeholder (token or special), never a random FE pick.

---

## 5. Board and chrome (UI, not pay symbols)

| Asset | Phase 1 | Final (later) |
| --- | --- | --- |
| 5×5 frame | navy panel, gold hairline | carved ice / stadium LED frame |
| Reel separators | 1px ice lines | subtle posts / banners |
| Payline flash | cyan polyline | ski-track glow |
| Win cell stroke | 2px gold | snow burst |
| Background | reuse V1 stadium still | same direction, maybe 5×5-friendly crop |
| Ski jumper | V1 art, optional, never on cells | transparent jumper if available |
| Logo | existing SkyJump brand | KEEP |
| Flight stages RUN-UP / TAKEOFF / FLIGHT | three labelled boxes + `xN` | hill-phase meters |
| Global G | large `x12` pill | floodlight type |
| FS tier chip | text `LARGE HILL` | hill-name plaque |
| Spins remaining | number | LED countdown |
| Persistent Mystery targets | mini regular tiles | framed icons |
| Token floor | `FLOOR T2` text | gate graphic |
| HUD | existing glass dock | KEEP |
| Big / mega win | V1 language, smaller toast | optional dedicated frames |
| Buy bonus cards | text + TBD cost | hill-tier art **without** inventing prices |
| Paytable / rules | scrollable text + placeholder grid | illustrated |

---

## 6. Audio (placeholders vs final)

Phase 1 may reuse V1:

- BGM playlist `frostbet-*`
- reel stop from existing sprite
- win / lose stings

Final (Phase 8) additional cues — list only:

- Coach lock
- Mystery resolve
- Token land (per tier intensity)
- Thermal apply
- Gate upgrade
- Rejump whoosh
- Judge collect
- Head Judge second pass
- Wind Key / G up
- Scatter 1 / 2 / 3+
- FS intro per tier
- World Record
- Cap

Do not pull licensed packs from other slots.

---

## 7. Registration and manifest

When real art exists:

1. Files under `assets/skyjump/v2/` (or `frontend/apps/poc/static/assets/skyjump/v2/`)
2. Register in `frontend/apps/poc/src/game/assets.ts`
3. Record prompts/seeds in `assets/skyjump/generated/assets-manifest.json` **or** mark SVG placeholders there
4. Production build must not ship Comfy work-in-progress dumps

Until then, programmatic PIXI `Graphics` / HTML canvas tiles keyed by the IDs in this file are sufficient.

---

## 8. Count (final art checklist)

| Category | Count |
| ---: | ---: |
| Regulars | 9 |
| Token tiers | 6 |
| Specials + scatter + mystery | 10 |
| Stage meters | 3 + 1 global G |
| FS chrome | tier, spins, targets, floor |
| Environment | bg, optional jumper, logo |
| HUD | reuse V1 |

Plus optional win-level frames and buy-bonus stills. No production paytable art required for Phase 1.
