<script lang="ts">
	import { stateBet, stateConfig } from 'state-shared';
	import { Button, OptionsToggle } from 'components-shared';
	import { getContextEventEmitter } from 'utils-event-emitter';
	import { numberToCurrencyString } from 'utils-shared/amount';

	import type { EmitterEventModal } from '../types';

	const { eventEmitter } = getContextEventEmitter<EmitterEventModal>();

</script>

<OptionsToggle
	value={stateBet.betAmount}
	options={stateConfig.betAmountOptions}
	onchange={(value) => {
		stateBet.betAmount = value;
		eventEmitter.broadcast({ type: 'soundPressGeneral' });
	}}
>
	{#snippet children({ disabledDown, disabledUp, toggleDown, toggleUp })}
		<div class="toggle-wrap">
			<Button data-test="down-button" disabled={disabledDown} onclick={toggleDown}>
				<span class="step-art minus" aria-hidden="true"></span>
			</Button>

			<span class="amount">{numberToCurrencyString(stateBet.betAmount)}</span>

			<Button data-test="up-button" disabled={disabledUp} onclick={toggleUp}>
				<span class="step-art plus" aria-hidden="true"></span>
			</Button>
		</div>
	{/snippet}
</OptionsToggle>

<style lang="scss">
	/* The same minus / plus art as the BetUI (published on <body> as --ml-minus / --ml-plus by Game.svelte). */
	.step-art {
		display: block;
		width: 3rem;
		height: 3rem;
		background-position: center;
		background-repeat: no-repeat;
		background-size: contain;
		filter: drop-shadow(0 3px 4px rgba(0, 0, 0, 0.45));
		transition: transform 0.12s ease;
	}

	.step-art.minus {
		background-image: var(--ml-minus);
	}

	.step-art.plus {
		background-image: var(--ml-plus);
	}

	:global(.button:not(.disabled):active) .step-art {
		transform: scale(0.94);
	}

	.toggle-wrap {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 0.5rem;
	}
</style>
