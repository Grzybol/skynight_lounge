<script lang="ts">
	import { Text, Rectangle } from 'pixi-svelte';
	import { stateBet, stateUi } from 'state-shared';
	import { WHITE } from 'constants-shared/colors';

	import { UI_BASE_SIZE } from '../constants';
	import { HUD } from '../gardenHud';

	const gardenTheme = $derived(stateUi.config.theme === 'garden');
	const minerTheme = $derived(stateUi.config.theme === 'miner');
	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');
	const boxSize = $derived(
		gardenTheme ? HUD.button.width * 0.82 : skyjumpTheme ? 40 : UI_BASE_SIZE * 0.9,
	);
	const fontSizeMultiplier = $derived.by(() => {
		if (stateBet.autoSpinsCounter === Infinity) return 3;
		if (stateBet.autoSpinsCounter > 99) return 1.5;
		if (stateBet.autoSpinsCounter > 9) return 2;
		return 2.5;
	});
</script>

{#if stateBet.autoSpinsCounter > 0}
	<Rectangle
		anchor={0.5}
		width={boxSize}
		height={boxSize}
		borderRadius={50}
		backgroundColor={gardenTheme
			? 0xffe08a
			: minerTheme
				? 0xe7a64b
				: skyjumpTheme
					? 0xffc940
					: undefined}
		borderColor={gardenTheme
			? 0xfff8e0
			: minerTheme
				? 0xfff0d0
				: skyjumpTheme
					? 0xffe083
					: undefined}
		borderWidth={gardenTheme || minerTheme || skyjumpTheme ? 3 : 0}
	/>
	<Text
		anchor={0.5}
		text={stateBet.autoSpinsCounter === Infinity ? '∞' : stateBet.autoSpinsCounter}
		style={{
			fontFamily: skyjumpTheme ? 'SkyjumpUI' : 'proxima-nova',
			fill: gardenTheme ? 0x17311d : minerTheme || skyjumpTheme ? 0x29152c : WHITE,
			fontWeight: 'bold',
			fontSize:
				fontSizeMultiplier *
				(gardenTheme ? HUD.button.height * 0.22 : skyjumpTheme ? 8 : UI_BASE_SIZE * 0.2),
		}}
	/>
{/if}
