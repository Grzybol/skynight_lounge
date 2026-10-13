<script lang="ts">
	import { Button, Popup } from 'components-shared';
	import { zIndex } from 'constants-shared/zIndex';
	import { stateBet, stateModal, stateUi, INFINITY_MARK } from 'state-shared';
	import { getContextEventEmitter } from 'utils-event-emitter';
	import { numberToCurrencyString } from 'utils-shared/amount';

	import BaseIcon from './BaseIcon.svelte';
	import BaseTitle from './BaseTitle.svelte';
	import BaseContent from './BaseContent.svelte';
	import BaseScrollable from './BaseScrollable.svelte';
	import BaseButtonWrap from './BaseButtonWrap.svelte';
	import BaseButtonContent from './BaseButtonContent.svelte';
	import { stateBonus, stateBonusDerived } from '../stateBonus.svelte';
	import { i18nDerived } from '../i18n/i18nDerived';
	import type { EmitterEventModal } from '../types';

	const { eventEmitter } = getContextEventEmitter<EmitterEventModal>();

	const confirm = () => {
		stateBet.activeBetModeKey = stateBonus.selectedBetModeKey;

		if (stateBonusDerived.selectedBetModeData().type === 'buy') {
			eventEmitter.broadcast({ type: 'bet' });
		}

		if (stateBonusDerived.selectedBetModeData().type === 'activate') {
			stateUi.autoSpinsLossLimitText = INFINITY_MARK;
			stateUi.autoSpinsSingleWinLimitText = INFINITY_MARK;
		}
	};
</script>

{#if stateModal.modal?.name === 'buyBonusConfirm'}
	<Popup zIndex={zIndex.dialog} onclose={() => (stateModal.modal = { name: 'buyBonus' })}>
		<BaseContent maxWidth="500px">
			{#if stateBonus.selectedModeArt}
				<img
					class="mode-art"
					src={stateBonus.selectedModeArt}
					alt={stateBonusDerived.selectedBetModeData().text.title}
					draggable="false"
				/>
			{:else}
				<BaseTitle>
					{stateBonusDerived.selectedBetModeData().text.title}
				</BaseTitle>
			{/if}
			<BaseScrollable type="column">
				<div class="mode-info">
				{#if stateUi.config.theme === 'skyjump'}
					<p class="mode-blurb" data-test="mode-blurb">
						{stateBonusDerived.selectedBetModeData().text.description}
					</p>
				{:else}
					{stateBonusDerived.selectedBetModeData().text.dialog}
				{/if}
				<p>
					TOTAL COST {numberToCurrencyString(
						stateBet.betAmount * stateBonusDerived.selectedBetModeData().costMultiplier,
					)}
				</p>
				<p class:max-win={stateUi.config.theme === 'skyjump'}>
					{#if stateUi.config.theme === 'skyjump'}
						MAX WIN {numberToCurrencyString(
							stateBet.betAmount * (stateBonusDerived.selectedBetModeData().maxWin ?? 0),
						)}
						· {Math.max(
							1,
							Math.round(
								(stateBonusDerived.selectedBetModeData().maxWin ?? 0) /
									(stateBonusDerived.selectedBetModeData().costMultiplier || 1),
							),
						)}x
					{:else}
						MAX WIN {stateBonusDerived.selectedBetModeData().maxWin ?? '—'}x
					{/if}
				</p>
				</div>
			</BaseScrollable>
			<BaseButtonWrap type="max-width">
				<Button
					primary
					data-test="confirm-button"
					onclick={() => {
						confirm();
						eventEmitter.broadcast({ type: 'soundPressGeneral' });
						stateModal.modal = null;
					}}
				>
					<BaseIcon width="100%" height="3rem" />
					<BaseButtonContent>
						<span style="font-size: 1rem;"
							>{stateUi.config.theme === 'skyjump' ? 'ENTER THE ROOM' : i18nDerived.confirm()}</span
						>
					</BaseButtonContent>
				</Button>
			</BaseButtonWrap>
		</BaseContent>
	</Popup>
{/if}

<style>
	/* Mode banner: twice the earlier size (220x110 -> 440x220), flush with the top edge of the tile. */
	.mode-art {
		display: block;
		width: min(100%, 720px);
		max-height: 220px;
		margin: 0 auto 0.5rem;
		object-fit: contain;
		pointer-events: none;
	}

	/* Tight spacing so the whole tile fits without scrolling. */
	.mode-info {
		display: grid;
		gap: 0.3rem;
		text-align: center;
	}

	.mode-info p {
		margin: 0;
	}

	.mode-blurb {
		margin: 0;
		font-size: 1.05rem;
		line-height: 1.5;
		text-align: center;
	}

	.max-win {
		margin: 0.2rem 0 0;
		color: #f8e2a0;
		font-size: 1.45rem;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-align: center;
		text-shadow: 0 2px 0 rgba(60, 10, 20, 0.85);
	}
</style>
