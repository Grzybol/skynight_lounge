<script lang="ts">
	import { getContext as getSvelteContext } from 'svelte';
	import { stateUi } from 'state-shared';
	import { BLACK } from 'constants-shared/colors';
	import { MainContainer } from 'components-layout';
	import { Container, Rectangle } from 'pixi-svelte';

	import { getContext } from '../context';
	import type { LayoutUiProps } from '../types';
	import {
		HUD,
		GARDEN_SLOT_BOARD_CONTEXT,
		gardenButtonSizes,
		gardenPlusButtonSizes,
		gardenSideButtonSizes,
		getGardenHudLayout,
		type GardenSlotBoardApi,
	} from '../gardenHud';
	import LabelFreeSpinCounter from './LabelFreeSpinCounter.svelte';

	const props: LayoutUiProps = $props();
	const context = getContext();
	const slotBoard = getSvelteContext<GardenSlotBoardApi>(GARDEN_SLOT_BOARD_CONTEXT);
	const layout = $derived(
		getGardenHudLayout({
			hud: context.stateLayoutDerived.mainLayoutStandard(),
			game: context.stateLayoutDerived.mainLayout(),
			board: slotBoard.get(),
		}),
	);
	const flyoutYs = $derived.by(() => {
		const pitch = gardenSideButtonSizes.height + HUD.gapTight;
		const half = gardenSideButtonSizes.height * 0.5;
		const hudHeight = context.stateLayoutDerived.mainLayoutStandard().height;
		const minStart = HUD.viewportPad + half;
		const maxStart = hudHeight - HUD.viewportPad - half - pitch * 4;
		const railMidY = (layout.menu.y + layout.buy.y) * 0.5;
		const start = Math.min(maxStart, Math.max(minStart, railMidY - pitch * 2));
		return {
			payTable: start,
			gameRules: start + pitch,
			settings: start + pitch * 2,
			sound: start + pitch * 3,
			close: start + pitch * 4,
		};
	});
</script>

<MainContainer standard>
	{#if !stateUi.menuOpen}
		<Container x={layout.menu.x} y={layout.menu.y}>
			{@render props.buttonMenu({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
		<Container x={layout.buy.x} y={layout.buy.y}>
			{@render props.buttonBuyBonus({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
	{/if}

	<Container x={layout.balance.x} y={layout.balance.y}>
		{@render props.amountBalance({ stacked: true })}
	</Container>
	<Container x={layout.amountBet.x} y={layout.amountBet.y}>
		{@render props.amountBet({ stacked: true })}
	</Container>
	<Container x={layout.dec.x} y={layout.dec.y}>
		{@render props.buttonDecrease({ anchor: 0.5, sizes: gardenPlusButtonSizes })}
	</Container>
	<Container x={layout.inc.x} y={layout.inc.y}>
		{@render props.buttonIncrease({ anchor: 0.5, sizes: gardenPlusButtonSizes })}
	</Container>

	<Container x={layout.win.x} y={layout.win.y}>
		{@render props.amountWin({ stacked: true })}
	</Container>
	<Container x={layout.auto.x} y={layout.auto.y}>
		{@render props.buttonAutoSpin({ anchor: 0.5, sizes: gardenButtonSizes })}
	</Container>
	<Container x={layout.bet.x} y={layout.bet.y}>
		{@render props.buttonBet({ anchor: 0.5, sizes: gardenButtonSizes })}
	</Container>
	<Container x={layout.turbo.x} y={layout.turbo.y}>
		{@render props.buttonTurbo({ anchor: 0.5, sizes: gardenButtonSizes })}
	</Container>

	{#if stateUi.freeSpinCounterShow}
		<Container x={layout.freeSpin.x} y={layout.freeSpin.y}>
			<LabelFreeSpinCounter stacked />
		</Container>
	{/if}
</MainContainer>

{#if stateUi.menuOpen}
	<Rectangle
		eventMode="static"
		cursor="pointer"
		alpha={0.5}
		anchor={0.5}
		backgroundColor={BLACK}
		width={context.stateLayoutDerived.canvasSizes().width}
		height={context.stateLayoutDerived.canvasSizes().height}
		x={context.stateLayoutDerived.canvasSizes().width * 0.5}
		y={context.stateLayoutDerived.canvasSizes().height * 0.5}
		onpointerup={() => (stateUi.menuOpen = false)}
	/>

	<MainContainer standard>
		<Container x={layout.menu.x} y={flyoutYs.payTable}>
			{@render props.buttonPayTable({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
		<Container x={layout.menu.x} y={flyoutYs.gameRules}>
			{@render props.buttonGameRules({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
		<Container x={layout.menu.x} y={flyoutYs.settings}>
			{@render props.buttonSettings({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
		<Container x={layout.menu.x} y={flyoutYs.sound}>
			{@render props.buttonSoundSwitch({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
		<Container x={layout.menu.x} y={flyoutYs.close}>
			{@render props.buttonMenuClose({ anchor: 0.5, sizes: gardenSideButtonSizes })}
		</Container>
	</MainContainer>
{/if}
