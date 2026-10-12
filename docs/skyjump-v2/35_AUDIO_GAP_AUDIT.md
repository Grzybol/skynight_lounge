# SkyJump V2 — Audio Gap Audit (Final custom pack + retrigger fix)

Date: 2026-09-25 (updated retrigger / silent-tail fix)  
Runtime masters: `frontend/apps/poc/static/assets/audio/skyjump/sfx/v2/`  
Runtime trims (non-destructive): `sfx/v2_trimmed/`, `sfx/legacy_trimmed/`  
Catalog: `frontend/apps/poc/src/game/skyjump_v2/audio.ts`  
Duration meta: `frontend/apps/poc/src/game/skyjump_v2/audioDurationMeta.json`

## Root cause (confirmed)

1. One Howl buffer was cached per URL; play IDs were tracked until **MP3 EOF** via `howl.playing(id)`.
2. `overlap: 'limited'` refused new plays when `active.length >= 2`.
3. Silent / near-silent tails therefore kept voices occupied long after the audible hit, suppressing UI hover and fast feature chains.
4. `minGap` was already trigger-time based — not the primary hover bug; voice-pool EOF occupancy was.

**No global cross-hook lock** was found. Unrelated hooks could overlap; same-hook pools stalled on EOF.

## Fix strategy

**COMBINATION:** per-hook Howl voice pools + audible-window release (`stop(id)` after audible ms) + non-destructive runtime WAV trims for worst silent-tail masters.

## Attachment inventory

| | Count / list |
| --- | --- |
| FOUND | **21** custom V2 masters |
| RUNTIME TRIMMED | `sfx_token_reveal.wav`, `ui_click.wav`, `bet_button_sound.wav`, `generic_panel_open_close.wav` |
| MASTERS | untouched |

## Problematic silent tails (measured −40 dB peak threshold)

| FILE | TOTAL | AUDIBLE | TRAIL | ACTION |
| --- | ---: | ---: | ---: | --- |
| ui_click.mp3 | 3.00 | 0.22 | 2.77 | runtime trim + audible release |
| bet_button_sound.mp3 | 1.00 | 0.12 | 0.88 | runtime trim + audible release |
| generic_panel_open_close.mp3 | 2.00 | 0.73 | 1.27 | runtime trim + audible release |
| sfx_token_reveal.mp3 | 2.00 | 0.80 | 1.20 | runtime trim + audible release |
| button_hover_sound.mp3 | 1.00 | 1.00 | 0.00 | no trim — fixed via maxVoices=4 |

## Hook table

| HOOK | FILE | GAIN | TOTAL | AUDIBLE | MAX_VOICES | MIN_GAP | POLICY | STATUS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| UI_CLICK | ui_click (trim) | 0.42 | 3.00 | ~0.31 | 3 | 35 | allow | REUSE |
| UI_HOVER | button_hover_sound | 0.38 | 1.00 | 1.00 | 4 | 40 | allow | REUSE |
| PANEL_* | panel (trim) | 0.36–0.40 | 2.00 | ~0.81 | 2 | 50 | allow | REUSE |
| BET_CONFIRM | bet_button (trim) | 0.48 | 1.00 | ~0.20 | 2 | 40 | allow | REUSE |
| BET_+/- | bet_increase/decrease | 0.55 | 1–2 | ~1–1.5 | 3 | 40 | allow | REUSE |
| REEL_STOP | slot reveal | 0.42 | 1.00 | 1.00 | 3 | 40 | limited | REUSE |
| PAYLINE_DRAW | sfx_payline_draw | 0.48 | 2.00 | 2.00 | 3 | 80 | limited | READY |
| PAYLINE_COMPLETE | sfx_payline_complete | 0.52 | 2.00 | 2.00 | 3 | 80 | limited | READY |
| SCATTER_LAND | sfx_scatter_land | 0.50 | 0.48 | 0.24 | 3 | 60 | limited | READY |
| SCATTER_TRIGGER | sfx_scatter_trigger | 0.68 | 1.00 | 1.00 | 1 | — | single | READY |
| FS_START | sfx_free_spins_start | 0.70 | 1.00 | 0.80 | 1 | — | single | READY |
| FS_RETRIGGER | sfx_free_spins_retrigger | 0.62 | 2.00 | 1.54 | 1 | — | single | READY |
| TIER_UPGRADE | sfx_tier_upgrade | 0.65 | 1.00 | 1.00 | 1 | — | single | READY |
| MYSTERY_* | sfx_mystery_open | 0.52–0.55 | 0.48 | 0.48 | 3 | 50 | limited | READY |
| TOKEN_REVEAL | token (trim) | 0.50 | 2.00 | ~0.88 | 3 | 50 | limited | READY |
| THERMAL | sfx_thermal_lift | 0.50 | 1.00 | 1.00 | 3 | 50 | limited | READY |
| GATE_UPGRADE | sfx_gate_upgrade | 0.55 | 1.00 | 1.00 | 1 | — | single | READY |
| JUDGE_COLLECT | sfx_judge_collect | 0.58 | 2.00 | 2.00 | 2 | 80 | limited | READY |
| HEAD_JUDGE_COLLECT | sfx_head_judge_collect | 0.62 | 2.00 | 2.00 | 2 | 80 | limited | READY |
| REJUMP | sfx_rejump | 0.58 | 2.00 | 2.00 | 2 | 120 | limited | READY |
| WIND_CHARGE | sfx_wind_charge | 0.50 | 2.00 | 1.77 | 1 | — | single | READY |
| WIND_UPGRADE | sfx_wind_upgrade | 0.58 | 2.00 | 1.46 | 1 | — | single | READY |
| WIND_TRANSITION | sfx_wind_transition | 0.35 | 2.00 | 1.65 | 2 | 80 | allow | READY |
| WORLD_RECORD | sfx_world_record | 0.72 | 2.00 | 2.00 | 1 | — | single | READY |
| MAX_WIN | sfx_max_win | 0.70 | 2.76 | 2.76 | 1 | — | single | READY |
| BONUS_END | sfx_bonus_end | 0.55 | 2.00 | 2.00 | 1 | — | single | READY |
| BAD_MISS | sfx_bad_miss | 0.35 | 0.68 | 0.68 | 1 | — | single | OPTIONAL |
| COACH | — | — | — | — | 0 | — | silent | SILENT |
| BGM | frostbet | — | — | — | — | — | playlist | REUSE |

## Decisions

- **Coach:** SILENT
- **Head Judge:** policy B; **maxVoices 2** so pass 2 is not blocked by pass 1 occupancy
- **WR → Max Win:** still sequenced by book/`wrHoldMs`; each remains `single` for its own cue only
- **Catch-up:** unchanged (`catchUp: true` no-ops)
- **Masters:** never destructively edited

## Retrigger policy summary

| Class | Behavior |
| --- | --- |
| UI frequent | allow, 3–4 voices, 35–50 ms trigger gap |
| Gameplay frequent | limited, 3 voices, steal oldest if full |
| Major exclusive | single = stop previous same-hook voice, then play |
| Occupancy | audible ms (+ pad), then `stop(id)` — silent tails do not hold the pool |
