<script lang="ts">
	import { stateBet, stateModal, stateUi, type BetModeData } from 'state-shared';
	import { Button } from 'components-shared';
	import { getContextEventEmitter } from 'utils-event-emitter';
	import { numberToCurrencyString } from 'utils-shared/amount';

	import BaseIcon from './BaseIcon.svelte';
	import BonusCard from './BonusCard.svelte';
	import BaseButtonContent from './BaseButtonContent.svelte';
	import { stateBonus } from '../stateBonus.svelte';
	import type { EmitterEventModal } from '../types';

	type Props = {
		list: BetModeData[];
	};

	const props: Props = $props();
	const { eventEmitter } = getContextEventEmitter<EmitterEventModal>();
	const skyjump = $derived(stateUi.config.theme === 'skyjump');
	const maxWinCash = (betModeData: BetModeData) =>
		numberToCurrencyString(stateBet.betAmount * (betModeData.maxWin ?? 0));
	const maxWinStakeX = (betModeData: BetModeData) => {
		const cost = betModeData.costMultiplier || 1;
		return Math.max(1, Math.round((betModeData.maxWin ?? 0) / cost));
	};
</script>

{#each props.list as betModeData}
	{#if betModeData.type !== 'default'}
		<BonusCard>
			{#snippet title()}
				<div class="title">
					{betModeData.text.title}
				</div>
			{/snippet}

			{#snippet description()}
				<div class="description">
					<div class="specs">
						<span>{betModeData.text.title.includes('MULTIPLIER') ? 'PROFILE' : 'HILL'}</span>
						<strong>{betModeData.text.title}</strong>
					</div>
					{#if betModeData?.text?.description}
						<p>{betModeData.text.description}</p>
					{/if}
					<div class="max">
						{#if skyjump}
							MAX WIN {maxWinCash(betModeData)} · {maxWinStakeX(betModeData)}x
						{:else}
							MAX WIN {betModeData.maxWin ?? '—'}x
						{/if}
					</div>
				</div>
			{/snippet}

			{#snippet price()}
				<div class="price">
					{`TOTAL BET ${numberToCurrencyString(stateBet.betAmount * betModeData.costMultiplier)}`}
				</div>
			{/snippet}

			{#snippet button()}
				<Button
					primary
					onclick={() => {
						stateBonus.selectedBetModeKey = betModeData.mode;
						eventEmitter.broadcast({ type: 'buyBonusConfirm' });
						eventEmitter.broadcast({ type: 'soundPressGeneral' });
					}}
					disabled={stateBet.betAmount <= 0 ||
						stateBet.balanceAmount < stateBet.betAmount * betModeData.costMultiplier}
				>
					<BaseIcon width="100%" height="2rem" />
					<BaseButtonContent>
						<span style="font-size: 1rem;">{betModeData.text.button}</span>
					</BaseButtonContent>
				</Button>
			{/snippet}
		</BonusCard>
	{/if}
{/each}

<style lang="scss">
	.title {
		font-size: 1rem;
		line-height: 1rem;
		text-align: center;
	}

	.description {
		font-size: 0.75rem;
		text-align: center;
		min-height: 4rem;
		white-space: pre-line;
		display: grid;
		gap: 0.35rem;
		align-content: center;
	}

	.description:empty {
		display: none;
	}

	.specs {
		display: grid;
		gap: 0.12rem;
		letter-spacing: 0.08em;
	}

	.specs span {
		font-size: 0.58rem;
		opacity: 0.7;
	}

	.max {
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.06em;
	}

	.price {
		font-size: 1rem;
		line-height: 1rem;
		text-align: center;
		white-space: nowrap;
	}
</style>
