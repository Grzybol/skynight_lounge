<script lang="ts">
	import { OptionsGrid } from 'components-shared';
	import { getContextLayout } from 'utils-layout';
	import { stateBet, stateBetDerived, stateConfig } from 'state-shared';

	import BaseIcon from './BaseIcon.svelte';
	import BaseButtonContent from './BaseButtonContent.svelte';
	import { i18nDerived } from '../i18n/i18nDerived';

	const { stateLayoutDerived } = getContextLayout();
	const count = $derived(stateLayoutDerived.layoutType() === 'landscape' ? 15 : 18);
	const options = $derived(
		[
			...stateConfig.betMenuOptions.slice(0, count - 1),
			...stateConfig.betMenuOptions.slice(-1),
		].filter((value, index, array) => array.indexOf(value) === index),
	); //always includes last, and without duplicate

	const isMaxValue = (value: number) => value === options[options.length - 1];

	/** Largest real bet level the balance can pay for (same levels the +/- buttons walk). */
	const maxAffordable = () => {
		const mode = stateBetDerived.activeBetMode();
		const cost = mode && (mode.type === 'activate' || mode.type === 'buy') ? mode.costMultiplier : 1;
		const affordable = stateConfig.betAmountOptions.filter(
			(level) => level * cost <= stateBet.balanceAmount,
		);
		return affordable.length ? Math.max(...affordable) : (stateConfig.betAmountOptions[0] ?? 0);
	};
	const formatValue = (value: number) => {
		if (Math.abs(value) > 999999) {
			return `${(Math.abs(value) / 1000000).toFixed(2)}M`;
		}
		if (Math.abs(value) > 999) {
			return `${(Math.abs(value) / 1000).toFixed(2)}K`;
		}
		return Math.abs(value).toFixed(2);
	};
</script>

<OptionsGrid
	value={stateBet.betAmount}
	{options}
	onchange={(value) => (stateBet.betAmount = isMaxValue(value) ? maxAffordable() : value)}
>
	{#snippet option({ option })}
		<BaseIcon width="100%" height="2rem" />
		<BaseButtonContent>
			<span style="font-size: 1rem;"
				>{isMaxValue(option) ? i18nDerived.max() : formatValue(option)}</span
			>
		</BaseButtonContent>
	{/snippet}
</OptionsGrid>
