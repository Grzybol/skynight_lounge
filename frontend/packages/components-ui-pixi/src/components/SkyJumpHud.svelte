<script lang="ts">
	import { stateUi } from 'state-shared';
	import { BLACK } from 'constants-shared/colors';
	import { MainContainer } from 'components-layout';
	import { Container, Rectangle } from 'pixi-svelte';

	import { getContext } from '../context';
	import type { LayoutUiProps } from '../types';
	import LabelFreeSpinCounter from './LabelFreeSpinCounter.svelte';
	import SkyJumpBetUiFace from './SkyJumpBetUiFace.svelte';
	import { getSkyJumpHudLayout, getSkyJumpMenuFlyout } from '../skyjumpHud';
	import {
		SKYJUMP_BETUI_ART,
		SKYJUMP_BETUI_TILE_FIT,
		SKYJUMP_INFO_TILE_WIDTH_SCALE,
	} from '../skyjumpBetUiArt';
	import { skyjumpCodeBetUi } from '../skyjumpCodeBetUi';

	const props: LayoutUiProps = $props();
	const context = getContext();
	const layout = $derived(getSkyJumpHudLayout(context.stateLayoutDerived.mainLayoutStandard()));
	const sizes = $derived(layout.sizes);
	const flyout = $derived(getSkyJumpMenuFlyout(layout));
	const infoTileW = $derived(
		layout.clusters.info.w * SKYJUMP_BETUI_TILE_FIT.w * SKYJUMP_INFO_TILE_WIDTH_SCALE,
	);
	const infoTileShiftX = $derived(
		(layout.clusters.info.w * SKYJUMP_BETUI_TILE_FIT.w * (SKYJUMP_INFO_TILE_WIDTH_SCALE - 1)) / 2,
	);
</script>

{#if !skyjumpCodeBetUi.active}
<MainContainer standard>
	{#if stateUi.freeSpinCounterShow}
		<Container x={layout.win.x} y={layout.dock.y - 40}>
			<LabelFreeSpinCounter stacked />
		</Container>
	{/if}

	<!-- LEFT INFO zone — balance / win share one art tile -->
	<Container x={layout.clusters.info.x - infoTileShiftX} y={layout.clusters.info.y}>
		<SkyJumpBetUiFace
			assetKey={SKYJUMP_BETUI_ART.tile}
			width={infoTileW}
			height={layout.clusters.info.h * SKYJUMP_BETUI_TILE_FIT.h}
			anchor={0.5}
		/>
	</Container>
	<Container x={layout.balance.x} y={layout.balance.y}>
		{@render props.amountBalance({ stacked: true })}
	</Container>
	<Container x={layout.win.x} y={layout.win.y}>
		{@render props.amountWin({ stacked: true })}
	</Container>

	<!-- Unified BET cluster tile: [ − ] [ VALUE ] [ + ] -->
	<Container x={layout.clusters.bet.x} y={layout.clusters.bet.y}>
		<SkyJumpBetUiFace
			assetKey={SKYJUMP_BETUI_ART.tile}
			width={layout.clusters.bet.w * SKYJUMP_BETUI_TILE_FIT.w}
			height={layout.clusters.bet.h * SKYJUMP_BETUI_TILE_FIT.h}
			anchor={0.5}
		/>
	</Container>
	<Container x={layout.dec.x} y={layout.dec.y}>
		{@render props.buttonDecrease({ anchor: 0.5, sizes: sizes.plus })}
	</Container>
	<Container x={layout.amountBet.x} y={layout.amountBet.y}>
		{@render props.amountBet({ stacked: true })}
	</Container>
	<Container x={layout.inc.x} y={layout.inc.y}>
		{@render props.buttonIncrease({ anchor: 0.5, sizes: sizes.plus })}
	</Container>

	<!-- PRIMARY SPIN / STOP — sized from sizes.spin -->
	<Container x={layout.bet.x} y={layout.bet.y}>
		{@render props.buttonBet({
			anchor: 0.5,
			sizes: { width: sizes.spin.width, height: sizes.spin.height },
		})}
	</Container>

	<!-- BUY BONUS secondary-primary -->
	<Container x={layout.buy.x} y={layout.buy.y}>
		{@render props.buttonBuyBonus({
			anchor: 0.5,
			sizes: sizes.buy ?? { width: 138, height: 50 },
		})}
	</Container>

	<!-- AUTO / TURBO compact mode pair -->
	<Container x={layout.auto.x} y={layout.auto.y}>
		{@render props.buttonAutoSpin({
			anchor: 0.5,
			sizes: sizes.mode ?? sizes.side,
		})}
	</Container>
	<Container x={layout.turbo.x} y={layout.turbo.y}>
		{@render props.buttonTurbo({
			anchor: 0.5,
			sizes: sizes.turbo ?? sizes.mode ?? sizes.side,
		})}
	</Container>

	<!-- Secondary utility (menu) at dock edge -->
	{#if !stateUi.menuOpen}
		<Container x={layout.menu.x} y={layout.menu.y}>
			{@render props.buttonMenu({ anchor: 0.5, sizes: sizes.side })}
		</Container>
	{/if}
</MainContainer>

{#if stateUi.menuOpen}
	<Rectangle
		eventMode="static"
		cursor="pointer"
		alpha={0.45}
		anchor={0.5}
		backgroundColor={BLACK}
		width={context.stateLayoutDerived.canvasSizes().width}
		height={context.stateLayoutDerived.canvasSizes().height}
		x={context.stateLayoutDerived.canvasSizes().width * 0.5}
		y={context.stateLayoutDerived.canvasSizes().height * 0.5}
		onpointerup={() => (stateUi.menuOpen = false)}
	/>

	<MainContainer standard>
		<Container x={flyout.items.payTable.x} y={flyout.items.payTable.y}>
			{@render props.buttonPayTable({ anchor: 0.5, sizes: flyout.itemSize })}
		</Container>
		<Container x={flyout.items.gameRules.x} y={flyout.items.gameRules.y}>
			{@render props.buttonGameRules({ anchor: 0.5, sizes: flyout.itemSize })}
		</Container>
		<Container x={flyout.items.settings.x} y={flyout.items.settings.y}>
			{@render props.buttonSettings({ anchor: 0.5, sizes: flyout.itemSize })}
		</Container>
		<Container x={flyout.items.sound.x} y={flyout.items.sound.y}>
			{@render props.buttonSoundSwitch({ anchor: 0.5, sizes: flyout.itemSize })}
		</Container>
		<Container x={layout.menu.x} y={layout.menu.y}>
			{@render props.buttonMenuClose({ anchor: 0.5, sizes: sizes.side })}
		</Container>
	</MainContainer>
{/if}
{/if}
