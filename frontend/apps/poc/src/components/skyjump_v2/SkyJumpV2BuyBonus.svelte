<script lang="ts">
	import { OptionsToggle } from 'components-shared';
	import { stateBonus } from '../../../../../packages/components-ui-html/src/stateBonus.svelte';
	import type { EmitterEventModal } from '../../../../../packages/components-ui-html/src/types';
	import { getContextEventEmitter } from 'utils-event-emitter';
	import { numberToCurrencyString } from 'utils-shared/amount';
	import { stateBet, stateConfig, stateMetaDerived, type BetModeData } from 'state-shared';
	import { V2_PANEL_DECOR } from '../../game/skyjump_v2/presentationLayout';
	import { v2ModeTitleUrl, v2UiAssetUrl } from '../../game/skyjump_v2/uiAssetRegistry';
	import SkyJumpV2PanelDecor from './SkyJumpV2PanelDecor.svelte';

	const { eventEmitter } = getContextEventEmitter<EmitterEventModal>();

	const headerSrc = v2UiAssetUrl('modeBadgePlate');

	const buyModes = $derived(
		stateMetaDerived.betModeMetaList().filter((item) => item.type === 'buy'),
	);

	const canBuy = (mode: BetModeData) =>
		stateBet.betAmount > 0 && stateBet.balanceAmount >= stateBet.betAmount * mode.costMultiplier;

	const confirmBuy = (mode: BetModeData) => {
		if (!canBuy(mode)) return;
		stateBonus.selectedBetModeKey = mode.mode;
		stateBonus.selectedModeArt = v2ModeTitleUrl(mode.mode);
		eventEmitter.broadcast({ type: 'buyBonusConfirm' });
		eventEmitter.broadcast({ type: 'soundPressGeneral' });
	};
</script>

<section
	class="v2-buy"
	data-test="skyjump-v2-buy-bonus"
	style:margin-top={`${V2_PANEL_DECOR.panelShiftY}px`}
	style:--header-w="620px"
>
	<div class="decor-shell">
		<SkyJumpV2PanelDecor showDivider={false} />
		<header class="hero">
			<div class="header-slot header-art" data-art-slot="buy-header">
				<img class="section-header" src={headerSrc} alt="Buy Bonus" draggable="false" />
			</div>
			<span class="kicker">SKYNIGHT LOUNGE</span>
			<p>Choose a free-spin room. The price follows your bet.</p>
		</header>

		<div class="body">
			<OptionsToggle
				value={stateBet.betAmount}
				options={stateConfig.betAmountOptions}
				onchange={(value) => {
					stateBet.betAmount = value;
					eventEmitter.broadcast({ type: 'soundPressGeneral' });
				}}
			>
				{#snippet children({ disabledDown, disabledUp, toggleDown, toggleUp })}
					<div class="bet-row">
						<button
							type="button"
							class="step"
							data-test="down-button"
							disabled={disabledDown}
							onclick={toggleDown}
							aria-label="Decrease bet"
						>
							−
						</button>
						<span class="amount">{numberToCurrencyString(stateBet.betAmount)}</span>
						<button
							type="button"
							class="step"
							data-test="up-button"
							disabled={disabledUp}
							onclick={toggleUp}
							aria-label="Increase bet"
						>
							+
						</button>
					</div>
				{/snippet}
			</OptionsToggle>

			<div class="modes">
				{#each buyModes as mode (mode.mode)}
					{@const art = v2ModeTitleUrl(mode.mode)}
					<article class="mode-card">
						{#if art}
							<img class="mode-art" src={art} alt={mode.text.title} draggable="false" />
						{:else}
							<strong class="fallback-title">{mode.text.title}</strong>
						{/if}
						<div class="price">
							{numberToCurrencyString(stateBet.betAmount * mode.costMultiplier)}
						</div>
						<div class="max-win" data-test="mode-max-win">
							MAX WIN {numberToCurrencyString(stateBet.betAmount * (mode.maxWin ?? 0))}
						</div>
						<button
							type="button"
							class="buy"
							disabled={!canBuy(mode)}
							onclick={() => confirmBuy(mode)}
						>
							{mode.text.button}
						</button>
					</article>
				{/each}
			</div>
		</div>
	</div>
</section>

<style>
	.max-win {
		color: #f8e2a0;
		font-size: 1.15rem;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-align: center;
		text-shadow: 0 2px 0 rgba(60, 10, 20, 0.85);
	}

	.v2-buy {
		--ice: #f3e2b8;
		--muted: #cbb89a;
		--gold: #e4c57a;
		--stroke: rgba(212, 168, 92, 0.32);
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: 760px;
		height: auto;
		min-height: 0;
		overflow: visible;
		margin: 0 auto;
		color: var(--ice);
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
	}

	.decor-shell {
		position: relative;
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		flex: 1 1 auto;
		min-height: 0;
		max-height: 100%;
		gap: 8px;
		padding: 5px 4.5rem 1.75rem;
		border: 1px solid rgba(212, 168, 92, 0.72);
		border-radius: 18px;
		background:
			radial-gradient(120% 70% at 50% 0%, rgba(228, 197, 122, 0.12), transparent 52%),
			linear-gradient(180deg, #4a1424, #12080c);
		box-shadow:
			0 18px 40px rgba(0, 0, 0, 0.48),
			inset 0 0 28px rgba(74, 20, 36, 0.45),
			inset 0 1px 0 rgba(243, 226, 184, 0.16);
		overflow: visible;
	}

	.hero {
		position: relative;
		z-index: 2;
		flex: 0 0 auto;
		display: grid;
		gap: 0;
		text-align: center;
		padding: 0 0.25rem;
		overflow: visible;
	}

	.header-slot {
		position: relative;
		z-index: 2;
		display: grid;
		place-items: center;
		width: min(94%, var(--header-w, 620px));
		aspect-ratio: 1024 / 341;
		height: auto;
		margin: 4px auto 10px;
	}

	.section-header {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: contain;
		pointer-events: none;
	}

	.kicker {
		position: relative;
		z-index: 2;
		color: var(--gold);
		letter-spacing: 0.18em;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 0.62rem;
		font-weight: 800;
		line-height: 1;
		text-transform: uppercase;
	}

	.hero p {
		margin: 2px 0 0;
		color: var(--muted);
		font-size: 0.74rem;
		line-height: 1.2;
	}

	.body {
		position: relative;
		z-index: 2;
		flex: 1 1 auto;
		min-height: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.7rem;
		overflow: auto;
		padding: 0.15rem 0.15rem 0.4rem;
	}

	.bet-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.65rem;
	}

	.step {
		display: grid;
		place-items: center;
		width: 46px;
		height: 46px;
		padding: 0;
		border: 1px solid rgba(212, 168, 92, 0.72);
		border-radius: 12px;
		background: linear-gradient(180deg, #4a1424, #2a0b14);
		color: #f3e2b8;
		font-size: 1.4rem;
		font-weight: 700;
		line-height: 1;
		cursor: pointer;
	}

	.step:disabled {
		opacity: 0.38;
		cursor: default;
	}

	.step:not(:disabled):hover {
		filter: brightness(1.12);
	}

	.step:focus-visible {
		outline: 2px solid #e4c57a;
		outline-offset: 2px;
	}

	.amount {
		min-width: 6.5rem;
		color: var(--gold);
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 1.35rem;
		font-weight: 800;
		text-align: center;
	}

	.modes {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.45rem;
		width: 100%;
	}

	.mode-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.28rem;
		min-width: 0;
		padding: 0.4rem 0.35rem 0.5rem;
		background: rgba(18, 8, 12, 0.72);
		border: 1px solid var(--stroke);
		border-radius: 12px;
		text-align: center;
	}

	.mode-art {
		width: 100%;
		height: 88px;
		object-fit: contain;
		pointer-events: none;
	}

	.fallback-title,
	.price {
		color: var(--gold);
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-weight: 800;
	}

	.price {
		font-size: 0.95rem;
		line-height: 1;
	}

	.buy {
		width: 100%;
		margin-top: auto;
		padding: 0.38rem 0.4rem;
		border: 1px solid rgba(212, 168, 92, 0.72);
		border-radius: 12px;
		background: linear-gradient(180deg, #4a1424, #2a0b14);
		color: #f3e2b8;
		font-family: inherit;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		cursor: pointer;
	}

	.buy:not(:disabled):hover {
		filter: brightness(1.12);
	}

	.buy:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.buy:focus-visible {
		outline: 2px solid #e4c57a;
		outline-offset: 2px;
	}

	@media (max-width: 720px) {
		.modes {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
