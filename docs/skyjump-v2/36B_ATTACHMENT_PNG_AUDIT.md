# SKYJUMP V2 — Attachment re-supply audit (2026-09-26)

**Branch:** `feat/skyjump-v2-5x5`  
**Scope:** Physical audit of the 29 UI/FX files attached in chat for Phase 8C.1 follow-up.

## Verdict

| Expectation | Result |
| --- | --- |
| 29/29 found | **PASS** |
| Magic-byte PNG | **FAIL — 0/29** |
| Alpha preserved | **FAIL — 0/29** |
| JPEG RGB (no alpha) | **29/29** |

Cursor’s chat attachment pipeline delivered **JPEG** bytes for every file in this batch
(even when the filename ends in `.png`). There is **no** recoverable embedded PNG
alpha in these attachment blobs.

Per operator instruction:

- Do **not** use workspaceStorage / prior knockout reconstructions as a substitute
  for “these attachments”
- Do **not** transcode PNG→JPEG
- Do **not** invent transparency when the supplied file has none

Therefore runtime assets were **not** overwritten with this JPEG batch (that would
reintroduce opaque black mattes on Paytable / Info / FX).

## Current runtime (unchanged by this audit)

Phase 8C.1 still ships PNG RGBA under `static/assets/skyjump_v2/` from the prior
repair (true PNG masters where available + documented black-knockout for
JPEG-only stems). That remains the best alpha-preserving pack on disk until
Filip can supply a drop of real `.png` files outside the chat JPEG flattener
(e.g. zip / direct folder copy).

## Per-file (this chat attachment batch)

All 29: magic=`JPEG`, mode=`RGB`, alpha=`NO`.

| Stem | Attachment ext | WxH | Bytes (approx) |
| --- | --- | ---: | ---: |
| ui_panel_topper | .png | 1024×341 | 44k |
| ui_corner_ornament | .png | 1024×1024 | 117k |
| fx_coin_sparkle | .png | 1024×1024 | 71k |
| fx_payline_spark_head | .png | 1024×1024 | 75k |
| ui_divider_ice | .png | 1024×341 | 19k |
| ui_win_super | .jpg | 1024×512 | 188k |
| ui_win_mega | .jpg | 1024×512 | 176k |
| ui_win_big | .jpg | 1024×512 | 150k |
| ui_header_how_to_play | .jpg | 1024×512 | 116k |
| ui_mode_badge_plate | .jpg | 1024×341 | 55k |
| ui_status_plate | .jpg | 1024×341 | 71k |
| fx_small_sparkle | .jpg | 1024×1024 | 99k |
| fx_win_glow_ring | .jpg | 1024×1024 | 180k |
| fx_ice_glint | .jpg | 1024×1024 | 92k |
| fx_snow_burst | .jpg | 1024×1024 | 190k |
| fx_payline_end_glint | .jpg | 1024×1024 | 115k |
| ui_header_features | .jpg | 1024×512 | 109k |
| ui_header_info | .jpg | 1024×512 | 98k |
| ui_header_paytable | .jpg | 1024×512 | 103k |
| ui_mode_perfect_v | .jpg | 1024×512 | 163k |
| ui_mode_large_hill | .jpg | 1024×512 | 168k |
| ui_bonus_retrigger | .jpg | 1024×512 | 148k |
| ui_bonus_free_spins | .jpg | 1024×512 | 151k |
| ui_win_world_record | .jpg | 1024×512 | 227k |
| fx_screen_flash_accent | .jpg | 1024×576 | 127k |
| ui_mode_world_cup | .jpg | 1024×512 | 202k |
| ui_bonus_tier_upgrade | .jpg | 1024×512 | 167k |
| ui_win_max | .jpg | 1024×512 | 197k |
| ui_mode_ski_flying | .jpg | 1024×512 | 177k |

## How to land true PNG masters

Drop 29 real PNG RGBA files into `assets/skyjump_v2/source/ui_pack_8c/` (or a zip)
and run `python tools/skyjump/ingest_ui_pack_8c1.py` only after updating the
ingest to accept a local folder of verified PNG magic — **not** the Cursor
`assets/` chat cache.
