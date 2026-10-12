# Midnight Lounge BetUI audit

Audit of the SkyJump dock before the code-rendered Midnight Lounge BetUI. This describes behavior that the new presentation must keep. It does not change math, payouts, or event contracts.

Base: `6561a9500970c1d21ca93c2b012aeaa8845e01bd` (`main`, merge of PR #3).

## Component tree

Play-screen stack in `Game.svelte`:

1. `SkyJumpHudFrame.svelte` — HTML `<img>` of `ui_bet_hud_frame.png` (ice wings). `pointer-events: none`. Position comes from `getSkyJumpHudCssDock()`.
2. Pixi `App` (`z-index: 19`) → `UI` → `UIDefault` → `LayoutDesktop` → `SkyJumpHud.svelte` when `stateUi.config.theme === 'skyjump'`.
3. `SkyJumpHud` places shared button and label snippets. It does not own the click logic.

Shared snippets are defined in `UIDefault.svelte`:

| Slot | Component | What the player sees on SkyJump |
|---|---|---|
| `amountBalance` | `LabelBalance.svelte` | Tweens `stateBet.balanceAmount`, `numberToCurrencyString` |
| `amountWin` | `LabelWin.svelte` | Tweens `stateBet.winBookEventAmount`, `bookEventAmountToCurrencyString` |
| `amountBet` | `LabelBet.svelte` | Label `BET`, value `stateBetDerived.betCost()`. Click opens the bet menu |
| `buttonDecrease` / `buttonIncrease` | `ButtonDecrease` / `ButtonIncrease` | Raster − / + |
| `buttonBet` | `ButtonBet` → `ButtonBetProvider` | Raster SPIN or STOP |
| `buttonBuyBonus` | `ButtonBuyBonus` | Raster buy face |
| `buttonAutoSpin` | `ButtonAutoSpin` | Raster auto face + counter |
| `buttonTurbo` | `ButtonTurbo` | Raster turbo face |
| `buttonMenu` / `buttonMenuClose` | `ButtonMenu` / `ButtonMenuClose` | Raster menu / exit |
| `buttonPayTable` | `ButtonPayTable` | Flyout only |
| `buttonGameRules` | `ButtonGameRules` | Flyout only. Opens rules, not a separate info modal |
| `buttonSettings` | `ButtonSettings` | Flyout only |
| `buttonSoundSwitch` | `ButtonSoundSwitch` | Flyout only |
| `buttonLanguage` | `ButtonLanguage` | Snippet exists. `SkyJumpHud` does not mount it |

`UiFadeContainer` fades the whole Pixi HUD on `uiHide` / `uiShow`. `EnableSpaceHold` (in `UIDefault`) and `OnHotkey` (inside `ButtonBet`) own the Space key. `EnableHotkey` in `Game.svelte` only runs while `screen === 'play'`.

Layout numbers live in `skyjumpHud.ts` (`SKYJUMP_HUD.desktop`). They were fitted to the ice frame (`circleMidY`, `wingMidY`, `chromeInsetX`). Compact layout is a separate path for narrow canvases and is not the 1280×720 target.

## State sources

All of these stay. The new UI only reads and calls them.

- `stateBet` — balance, bet, win book amount, auto counter, turbo, space-hold, overlay lock, active mode
- `stateBetDerived` — `setBetAmount`, `updateIsTurbo`, `betCost`, `isBetCostAvailable`, `hasAutoBetCounter`, `activeBetMode`
- `stateConfig.betAmountOptions` — ordered bet steps
- `stateUi.menuOpen`, `stateUi.freeSpinCounterShow` / current / total
- `stateModal.modal` — `autoSpin`, `buyBonus`, `betAmountMenu`, `settings`, `payTable`, `gameRules`
- `stateSound.volumeValueMaster` — `0` is muted; unmute sets `50`
- `stateI18nDerived.switchLanguage`
- `stateXstateDerived.isIdle()`
- `context.eventEmitter` — `bet`, `stopButtonClick`, `stopButtonEnable`, `soundPressBet`, `soundPressBetIncrease`, `soundPressBetDecrease`, `soundPressGeneral`, `soundUiHover`

## Control behavior to preserve

### Spin / Stop — `ButtonBetProvider`

- Idle and the bet is affordable and `overlayOpen` is false: broadcast `soundPressBet`, then `bet`. A buy-type active mode is cleared back to `BASE` before `bet`.
- Idle and the bet is not affordable, or `overlayOpen`: face is disabled. Space is locked.
- Not idle: the control shows STOP and stays clickable.
- STOP always clears `autoSpinsCounter` when an auto counter is running, including while `overlayOpen`.
- If `overlayOpen`, STOP returns after clearing auto. It does not broadcast `stopButtonClick`.
- Otherwise STOP broadcasts `stopButtonClick` unless a previous `stopButtonClick` already set the local `stopDisabled` latch. `stopButtonEnable` clears that latch.
- While spinning, turbo on, and no auto counter: the face is the muted stop key (`stop_disabled`) but the button `disabled` flag stays false. The first click can still emit `stopButtonClick`.
- Space calls the same `onpress`. It is locked only while idle and (disabled or `overlayOpen`).

### Turbo — `ButtonTurbo`

- Disabled while `isSpaceHold` or `overlayOpen`.
- Press broadcasts `soundPressGeneral` and `updateIsTurbo(!isTurbo, { persistent: true })`.
- Subscribes to `stopButtonClick` → `updateIsTurbo(true, { persistent: false })` unless `overlayOpen`.
- Subscribes to `stopButtonEnable` → `updateIsTurbo(false, { persistent: false })` unless `overlayOpen`.
- A non-persistent update does not override a persistent turbo lock (`isTurboLocked` inside `stateBetDerived`).

### Auto — `ButtonAutoSpin`

- Disabled when space is held, when the bet is not affordable, or when the game is not idle and no auto counter is running.
- If a counter is running, press sets `autoSpinsCounter` to `0`.
- Otherwise press opens `{ name: 'autoSpin' }`.
- The counter badge shows the number, or `∞` when the counter is `Infinity`.

### Buy Bonus — `ButtonBuyBonus`

- Disabled when not idle.
- If the active mode type is `activate`, press sets `activeBetModeKey` to `BASE` and the label becomes the disable string.
- Otherwise press opens `{ name: 'buyBonus' }`.
- Always broadcasts `soundPressGeneral` first.

### Bet stepper — `ButtonIncrease` / `ButtonDecrease` / `LabelBet`

- Disabled when not idle.
- Plus is also disabled when `betAmount` equals the last `betAmountOptions` entry. Minus is disabled on the first entry.
- Plus picks the next greater option (`soundPressBetIncrease`). Minus picks the next smaller (`soundPressBetDecrease`). Both call `setBetAmount`.
- The bet value itself opens `{ name: 'betAmountMenu' }` when idle (`soundPressGeneral`). The displayed number is `betCost()`, not the raw step, so feature multipliers stay visible.

### Menu / Exit

- Menu press sets `stateUi.menuOpen = true` and plays `soundPressGeneral`.
- While open, a dim full-screen hit target sets `menuOpen` false with no extra sound.
- Exit (the menu slot while open) sets `menuOpen` false and plays `soundPressGeneral`.
- Flyout contents, left to right: paytable, rules, settings, sound. Language is not in this flyout.

### Info, paytable, settings, sound

- Info button is `ButtonGameRules`. It opens `{ name: 'gameRules' }`.
- Paytable opens `{ name: 'payTable' }`.
- Settings opens `{ name: 'settings' }`.
- Sound toggles `volumeValueMaster` between `0` and `50`.
- Each plays `soundPressGeneral`. None of them close the menu.

### Language

- `ButtonLanguage` toggles `skyjumpLanguageMenu.open` on the SkyJump theme.
- `SkyJumpLanguageMenu` can switch `en` / `pl` via `stateI18nDerived.switchLanguage`, but nothing in `SkyJumpHud` renders that menu. The live dock has no language control.

### Balance, win, free spins

- Balance and win are display-only, with the tweens above.
- When `stateUi.freeSpinCounterShow` is true, `LabelFreeSpinCounter` shows `current / total` above the win cluster.

## Interaction today

- Pixi `Button` supplies hover and pressed scale on SPIN (`1.03` / `0.95`) and a hover sound (`soundUiHover`) when the SkyJump spin face is enabled.
- Utility faces are raster sprites. Disabled spin/stop tints the PNG. There is no HTML focus ring.
- Keyboard: Space (and space-hold) only. No arrow-key bet stepping.

## What the rebuild may change

- Replace raster faces and the ice frame with HTML, CSS, and inline SVG.
- Mount the language control that the SkyJump dock never showed, using `switchLanguage('en' | 'pl')`.
- Keep every state write, broadcast, disable rule, and Space binding listed above.
