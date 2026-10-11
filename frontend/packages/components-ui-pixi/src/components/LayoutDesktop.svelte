<script lang="ts">
	import { stateUi } from 'state-shared';
	import { BLACK } from 'constants-shared/colors';
	import { MainContainer } from 'components-layout';
	import { Container, Rectangle, anchorToPivot } from 'pixi-svelte';

	import { DESKTOP_BASE_SIZE, DESKTOP_BACKGROUND_WIDTH_LIST } from '../constants';
	import { getContext } from '../context';
	import type { LayoutUiProps } from '../types';
	import GardenHud from './GardenHud.svelte';
	import SkyJumpHud from './SkyJumpHud.svelte';

	const props: LayoutUiProps = $props();
	const context = getContext();
	const garden = $derived(stateUi.config.theme === 'garden');
	const skyjump = $derived(stateUi.config.theme === 'skyjump');
	const uiScale = 0.8;
	const hudPad = 10;
	const labelY = DESKTOP_BASE_SIZE * 0.5 - 160;
	const buttonY = DESKTOP_BASE_SIZE * 0.5;
	const menuX = 220;
	const buyX = 220 + 150;
	const autoX = 160 + 150 * 4;
	const betX = 160 + 150 * 5;
	const turboX = 160 + 150 * 6;
	const winX = 900;
	const balanceX = 900 - 500;
	const amountBetX = 900 + 500;
	const decX = 1440;
	const incX = 1440 + 150;
</script>

<Container x={20}>
	{@render props.gameName()}
</Container>

<Container x={context.stateLayoutDerived.canvasSizes().width - 20}>
	{@render props.logo()}
</Container>

{#if garden}
	<GardenHud {...props} />
{:else if skyjump}
	<SkyJumpHud {...props} />
{:else}
	<MainContainer standard alignVertical="bottom">
		<Container
			x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5}
			y={context.stateLayoutDerived.mainLayoutStandard().height - DESKTOP_BASE_SIZE - hudPad}
			pivot={anchorToPivot({
				anchor: { x: 0.5, y: 0 },
				sizes: {
					height: DESKTOP_BASE_SIZE,
					width: DESKTOP_BACKGROUND_WIDTH_LIST.reduce((sum, width) => sum + width, 0),
				},
			})}
		>
			<Container y={labelY} x={balanceX} scale={uiScale}>
				{@render props.amountBalance({ stacked: true })}
			</Container>

			<Container y={labelY} x={winX} scale={uiScale}>
				{@render props.amountWin({ stacked: true })}
			</Container>

			<Container y={labelY} x={amountBetX} scale={uiScale}>
				{@render props.amountBet({ stacked: true })}
			</Container>

			<Container y={buttonY} x={menuX} scale={uiScale}>
				{@render props.buttonMenu({ anchor: 0.5 })}
			</Container>

			<Container y={buttonY} x={buyX} scale={uiScale}>
				{@render props.buttonBuyBonus({ anchor: 0.5 })}
			</Container>

			<Container y={buttonY} x={autoX} scale={uiScale}>
				{@render props.buttonAutoSpin({ anchor: 0.5 })}
			</Container>

			<Container y={buttonY} x={betX} scale={uiScale}>
				{@render props.buttonBet({ anchor: 0.5 })}
			</Container>

			<Container y={buttonY} x={turboX} scale={uiScale}>
				{@render props.buttonTurbo({ anchor: 0.5 })}
			</Container>

			<Container y={buttonY} x={decX} scale={uiScale}>
				{@render props.buttonDecrease({ anchor: 0.5 })}
			</Container>

			<Container y={buttonY} x={incX} scale={uiScale}>
				{@render props.buttonIncrease({ anchor: 0.5 })}
			</Container>
		</Container>
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

		<MainContainer standard alignVertical="bottom">
			<Container
				x={298}
				y={context.stateLayoutDerived.mainLayoutStandard().height - DESKTOP_BASE_SIZE - hudPad}
			>
				<Container scale={uiScale} y={DESKTOP_BASE_SIZE * 0.5 - 150 - 170 * 3}>
					{@render props.buttonPayTable({ anchor: 0.5 })}
				</Container>

				<Container scale={uiScale} y={DESKTOP_BASE_SIZE * 0.5 - 150 - 170 * 2}>
					{@render props.buttonGameRules({ anchor: 0.5 })}
				</Container>

				<Container scale={uiScale} y={DESKTOP_BASE_SIZE * 0.5 - 150 - 170 * 1}>
					{@render props.buttonSettings({ anchor: 0.5 })}
				</Container>

				<Container scale={uiScale} y={DESKTOP_BASE_SIZE * 0.5 - 150}>
					{@render props.buttonSoundSwitch({ anchor: 0.5 })}
				</Container>

				<Container scale={uiScale} y={DESKTOP_BASE_SIZE * 0.5}>
					{@render props.buttonMenuClose({ anchor: 0.5 })}
				</Container>
			</Container>
		</MainContainer>
	{/if}
{/if}
