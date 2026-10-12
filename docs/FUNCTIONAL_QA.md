# Miner's Fortune functional QA

Last updated: 2026-07-27

## Local tester behavior

`/dev-preview` runs a local demo adapter and does not require Stake Engine/RGS:

- Initial balance: `$1000.00`.
- Bet options: `$0.10`, `$0.20`, `$0.50`, `$1`, `$2`, `$5`, `$10`, `$20`, `$50`,
  and `$100`.
- The main BET button and Space use the real game actor with locally generated
  reveal books.
- Base spins use independent weighted random outcomes with `97%` theoretical RTP,
  `21.9%` hit frequency, payouts from `1x` to `100x`, and independently randomized
  visible symbol layouts.
- Auto Spin uses the real auto-bet state machine and decrements both the counter
  and balance. It uses the same random outcome table as manual BET.
- Buy Bonus costs `100x` the selected bet and plays a compact local Free Spins
  book: 3-scatter trigger, 3 free spins, a wild 2× line win, retrigger chrome,
  and a 20× credit. This is QA presentation, not production RTP.
- The production route retains the normal RGS request path.

The tester toolbar shows `Balance / Bet / Auto / Machine` diagnostics. A healthy
idle state ends with `Auto 0 · Machine idle`.

## Verified flows

- [x] BET/Space changes the board and deducts the selected bet.
- [x] Random wins animate a matching 3-, 4-, or 5-symbol combination, settle through
      the end-round path, and update the final balance.
- [x] Increase/decrease and the bet modal move through the configured bet options.
- [x] Auto Spin starts at the selected count, produces successive boards, deducts
      balance, and returns to idle.
- [x] Buy Bonus deducts `100x`, triggers Free Spins, completes the outro, and returns
      to idle.
- [x] Settings, Paytable, Game Rules, anticipation, and loader scenarios resolve.
- [x] `Back to game` restores the base-spin scenario and exits the loader/modal state.
- [x] Full Vite production build passes.

## Manual interaction notes

- Free Spins intro: press Space or click the continue prompt.
- Free Spins TOTAL WIN: press Space or click the continue prompt again.
- BIG WIN uses the same continue behavior.
- Random base-game distribution:
  `0x 78.1%`, `1x 8%`, `2x 7%`, `5x 4%`, `10x 1.9%`, `20x 0.8%`, `100x 0.2%`.
- During Auto Spin, the BET button becomes STOP and the Auto Spin button displays
  the remaining count.
