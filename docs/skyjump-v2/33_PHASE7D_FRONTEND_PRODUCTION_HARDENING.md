# SKYJUMP V2 — Phase 7D Frontend Production Hardening

**Status:** Complete on `feat/skyjump-v2-5x5`  
**Math:** UNCHANGED (`mathVersion: 2`, 7C.4 freeze)

## Goals delivered

1. Stale `02_MATH_SPEC` notes fixed (`checkIsBonusGame`, one-book architecture, PT2H live table).
2. Event presentation pipeline audited; all typed V2 handlers present.
3. Timing modes: **NORMAL / TURBO / CATCH_UP** (`skyjump_v2/timings.ts`).
4. Input lock via Stake `overlayOpen` + `presentationLock.ts` for V2 presentation.
5. Resume reserves include `skyjumpWorldRecord`, `skyjumpFreeSpinsEnd`, `finalWin`.
6. Buy costs config-driven only (`V2_ENABLED_MODES`).
7. Offline fonts: Typekit removed from `apps/poc`; system fallback stack.
8. Semantic audio hooks (`skyjump_v2/audio.ts`) with safe missing-file behavior.
9. Asset registry drop-in path verified; placeholders until USER_ART arrives.
10. Win presentation tiers documented as presentation-only (`winPresentation.ts`).
11. Tests: `tools/skyjump/test-v2-phase7d.ts`, `autoplay-stress-v2.ts`.
12. Manual QA checklist: `34_FRONTEND_MANUAL_QA_CHECKLIST.md`.

## Event audit (summary)

| Area | Handler | Turbo | Catch-up |
| --- | --- | --- | --- |
| Board / lines / scatter | yes | shortened | zero delay / apply state |
| Coach / Mystery / tokens / Thermal / Gate | yes | shortened | apply final state |
| Judge / Head Judge | yes (distinct events) | shortened | apply |
| Rejump batch | yes | shortened | apply |
| Wind Key / FM | yes (event-driven) | shortened | apply |
| Free Spins HUD / tier | yes | shortened | apply |
| SPECIAL World Record | yes | shortened hold | terminal state |
| Settlement / finalWin | yes | short hold | unlock input |

Optional protocol-only `skyjumpFlightMultiplier` remains unused; Wind Key carries transitions.

## Font decision

**SYSTEM_FALLBACK** — no Adobe redistribution. Phase 8 may replace with licensed face.

## Not in this phase

- Final USER_ART PNGs / USER_AUDIO masters (Phase 8)
- ACP upload / Stake session certification (Phase 9)
- Math / LUT / books / costs

## Verification commands

```
node --experimental-strip-types tools/skyjump/test-v2-phase7d.ts
node --experimental-strip-types tools/skyjump/autoplay-stress-v2.ts
# from frontend/apps/poc: npm run build
```
