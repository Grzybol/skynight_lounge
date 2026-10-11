<script lang="ts">
	import { Container } from 'pixi-svelte';
	import { stateBet, stateBetDerived, stateModal, stateUi } from 'state-shared';
	import { numberToCurrencyString } from 'utils-shared/amount';

	import UiLabel from './UiLabel.svelte';
	import { getContext } from '../context';
	import { i18nDerived } from '../i18n/i18nDerived';

	type Props = {
		stacked?: boolean;
	};

	const props: Props = $props();
	const context = getContext();
	const costMultiple = $derived(
		stateBet.betAmount > 0 ? stateBetDerived.betCost() / stateBet.betAmount : 1,
	);
	const label = $derived(
		stateUi.config.theme === 'skyjump'
			? 'BET'
			: costMultiple > 1.0001
				? 'TOTAL BET'
				: stateBetDerived.activeBetMode()?.text.betAmountLabel || i18nDerived.bet(),
	);
	const value = $derived(numberToCurrencyString(stateBetDerived.betCost()));
	const disabled = $derived(!context.stateXstateDerived.isIdle());

	const onpress = () => {
		if (disabled) return;
		context.eventEmitter.broadcast({ type: 'soundPressGeneral' });
		stateModal.modal = { name: 'betAmountMenu' };
	};
</script>

<Container eventMode="static" cursor={disabled ? 'not-allowed' : 'pointer'} onpointerup={onpress}>
	<UiLabel tiled {label} {value} stacked={props.stacked} />
</Container>
