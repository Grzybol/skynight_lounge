# Demo visual-asset audit

Audio is intentionally excluded from this audit.

## Replaced in the active runtime

| Area                           | Replacement                                         |
| ------------------------------ | --------------------------------------------------- |
| Static symbols                 | Local ComfyUI-generated `symbolsStatic` atlas       |
| L5 multiplier badge            | Local 2x badge + `SymbolSpriteAnimated.svelte`      |
| Symbol wins/lands/explosions   | `SymbolSpriteAnimated.svelte`                       |
| Symbol win frame               | `SymbolWinFrame.svelte` Pixi rectangles             |
| Base background                | `mine_base_drawn.webp`                              |
| Foreground dust                | `MineAmbience.svelte` Pixi motes                    |
| Feature background treatment   | Pixi tint, glow, and motes                          |
| Board feature glow             | Code-native rectangles in `BoardFrame.svelte`       |
| Reel-frame geometry            | Responsive timber/steel Pixi construction           |
| BIG WIN                        | Code-native Pixi panel and count-up                 |
| Free Spins intro/outro/counter | Code-native Pixi                                    |
| Anticipation                   | Code-native Pixi                                    |
| Scene transition               | Code-native Pixi                                    |
| Win coin particles             | Local 12-frame `minerCoin` atlas                    |
| Loader/progress/continue       | `LoaderArtwork.svelte` and `PressToContinue.svelte` |
| Display typography             | Shared Pixi `minerGoldTextStyle`                    |
| HUD and modals                 | Scoped `miner` theme                                |
| Paytable and rules             | Miner's Fortune-specific HTML content               |

## Still active from the demo

1. **Proxima Nova UI font** — inherited platform typography; acceptable as functional
   UI unless a fully custom type system is requested.

## Unregistered demo assets retained on disk

The following registrations have been removed from the active `poc` registry after
source search, runtime scenario checks, and production builds. Their source files
remain on disk and must not be deleted without an explicit cleanup decision:

- Old Spine symbol assets for H1-H5, L1-L4, S, and W.
- Old `M`, `explosion`, `payFrame`, and `anticipation` assets.
- The inherited `goldFont` and `goldBlur` registrations were removed after all
  active display text was migrated to the shared Pixi miner text style; source
  files remain on disk.
- The inherited `SD2_Coin` atlas was replaced by the deterministic local
  `minerCoin` atlas. The old source atlas remains on disk as a comparison/reference.
- The old `reelsFrame` registration was removed after desktop and 480×900 runtime
  verification; `frame_bg.png`, `frame_edge.png`, and the atlas remain on disk.
- `silverFont`, `purpleFont`, `bigwin`, `globalMultiplier`, `fsIntro`,
  `fsIntroNumber`, `fsOutroNumber`, `tumble_multiplier`, `tumble_win`, `freeSpins`,
  `winSmall`, `clusterWin`, and `transition`.
- The unused `GlobalMultiplier.svelte` component.
- Old loader, press-to-continue, foreground-animation, feature-foreground,
  reelhouse-glow, and progress-bar source files remain on disk but their active
  registrations were removed.

Before deleting anything, search dynamic asset keys, replay paths, and Storybook
stories, then build and exercise all `/dev-preview` scenarios.

## Not visual-reskin scope

- Audio files and sound mapping.
- Math, reel strips, RTP, payouts, and book generation.
- Stake Engine authentication/RGS behavior.
