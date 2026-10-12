<script lang="ts">
	import { Tween } from 'svelte/motion';

	import { stateBet, stateUi } from 'state-shared';
	import { bookEventAmountToCurrencyString } from 'utils-shared/amount';

	import UiLabel from './UiLabel.svelte';
	import { i18nDerived } from '../i18n/i18nDerived';

	type Props = {
		stacked?: boolean;
	};

	const props: Props = $props();
	const winBookEventAmountTween = new Tween(stateBet.winBookEventAmount);
	const label = $derived(i18nDerived.win());
	const value = $derived(bookEventAmountToCurrencyString(winBookEventAmountTween.current));
	const emphasize = $derived(stateUi.config.theme === 'garden');

	$effect(() => {
		winBookEventAmountTween.set(stateBet.winBookEventAmount, {
			duration: stateBet.isTurbo ? 80 : 400,
		});
	});
</script>

<UiLabel tiled {label} {value} stacked={props.stacked} {emphasize} />
