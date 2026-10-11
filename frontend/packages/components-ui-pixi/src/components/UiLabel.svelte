<script lang="ts">
	import { Text } from 'pixi-svelte';
	import { WHITE } from 'constants-shared/colors';
	import { stateUi } from 'state-shared';

	import UiSprite from './UiSprite.svelte';
	import { UI_BASE_FONT_SIZE } from '../constants';
	import { HUD } from '../gardenHud';

	type Props = {
		label: string;
		value: string;
		hint?: string;
		tiled?: boolean;
		stacked?: boolean;
		emphasize?: boolean;
	};

	const props: Props = $props();
	const minerTheme = $derived(stateUi.config.theme === 'miner');
	const gardenTheme = $derived(stateUi.config.theme === 'garden');
	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');
	const illustratedTheme = $derived(minerTheme || gardenTheme || skyjumpTheme);
	const emphasize = $derived(Boolean(props.emphasize && gardenTheme));
	const panel = $derived(gardenTheme && props.stacked ? (emphasize ? HUD.win : HUD.meter) : null);
	const fontSize = $derived(
		skyjumpTheme && props.stacked
			? 11
			: panel
				? emphasize
					? HUD.fontSizeWin
					: HUD.fontSize
				: UI_BASE_FONT_SIZE,
	);
	const valueFontSize = $derived(
		skyjumpTheme && props.stacked
			? props.label === 'BET'
				? 24
				: 20
			: panel
				? emphasize
					? HUD.valueFontSizeWin
					: HUD.valueFontSize
				: fontSize,
	);
	const plateWidth = $derived(
		panel ? panel.width : UI_BASE_FONT_SIZE * 3 * (326 / 73) * (emphasize ? 1.12 : 1),
	);
	const plateHeight = $derived(panel ? panel.height : UI_BASE_FONT_SIZE * 3);
	const lineGap = $derived(skyjumpTheme && props.stacked ? 16 : fontSize * 1.06);

	const labelStyle = $derived({
		fontFamily: skyjumpTheme ? 'SkyjumpUI' : 'proxima-nova',
		fontSize,
		fontWeight: illustratedTheme ? (skyjumpTheme ? '600' : '800') : '400',
		letterSpacing: gardenTheme && props.stacked ? 0 : skyjumpTheme ? 1.2 : illustratedTheme ? 2 : 0,
		align: 'center' as const,
		fill: gardenTheme ? 0xffdf78 : minerTheme ? 0xffd36b : skyjumpTheme ? 0xa8c4d8 : WHITE,
		...(gardenTheme ? { stroke: { color: 0x1c120c, width: emphasize ? 4 : 3 } } : {}),
	});

	const valueStyle = $derived({
		fontFamily: skyjumpTheme ? 'SkyjumpDisplay' : 'proxima-nova',
		fontSize: valueFontSize,
		fontWeight: illustratedTheme ? (skyjumpTheme ? '800' : '700') : '400',
		letterSpacing: 0,
		align: 'center' as const,
		fill: gardenTheme ? 0xfff4d1 : minerTheme ? 0xfff0d0 : skyjumpTheme ? 0xf4faff : WHITE,
		...(gardenTheme ? { stroke: { color: 0x1c120c, width: 3 } } : {}),
	});
	const hintStyle = $derived({
		fontFamily: skyjumpTheme ? 'SkyjumpUI' : 'proxima-nova',
		fontSize: 12,
		fontWeight: '600' as const,
		letterSpacing: 0.4,
		align: 'center' as const,
		fill: 0x9ecff0,
	});</script>

{#if props.stacked}
	{#if props.tiled && !skyjumpTheme}
		<UiSprite
			y={gardenTheme ? 0 : -20}
			anchor={gardenTheme ? 0.5 : { x: 0.5, y: 0 }}
			key="base_ticker"
			width={plateWidth}
			height={plateHeight}
			gardenTone={emphasize ? 'win' : 'label'}
			borderRadius={35}
		/>
	{/if}
	<Text
		anchor={gardenTheme || skyjumpTheme ? 0.5 : { x: 0.5, y: 0 }}
		text={props.label}
		style={labelStyle}
		y={skyjumpTheme ? (props.hint ? -18 : -12) : gardenTheme ? -lineGap * 0.42 : 0}
	/>
	<Text
		anchor={gardenTheme || skyjumpTheme ? 0.5 : { x: 0.5, y: 0 }}
		text={props.value}
		style={valueStyle}
		y={skyjumpTheme ? (props.hint ? 4 : 10) : gardenTheme ? lineGap * 0.42 : fontSize}
	/>
	{#if skyjumpTheme && props.hint}
		<Text anchor={0.5} text={props.hint} style={hintStyle} y={24} />
	{/if}
{:else}
	{#if props.tiled}
		<UiSprite
			x={-90}
			anchor={{ x: 0, y: 0.5 }}
			key="base_ticker"
			width={UI_BASE_FONT_SIZE * 3 * (326 / 73)}
			height={UI_BASE_FONT_SIZE * 3}
			gardenTone="label"
			borderRadius={35}
		/>
	{/if}
	<Text anchor={{ x: 0, y: 0.5 }} text={props.label} style={labelStyle} />
	<Text
		anchor={{ x: 1, y: 0.5 }}
		text={props.value}
		style={valueStyle}
		x={UI_BASE_FONT_SIZE * 10}
	/>
{/if}
