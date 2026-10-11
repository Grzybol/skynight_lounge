<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicInOut } from 'svelte/easing';

	import { stateUi } from 'state-shared';
	import { BLACK } from 'constants-shared/colors';
	import { FadeContainer } from 'components-pixi';
	import { MainContainer } from 'components-layout';
	import { Container, Rectangle } from 'pixi-svelte';
	import { waitForResolve } from 'utils-shared/wait';

	import LabelFreeSpinCounter from './LabelFreeSpinCounter.svelte';
	import ButtonDrawer from './ButtonDrawer.svelte';
	import GardenHud from './GardenHud.svelte';
	import SkyJumpHud from './SkyJumpHud.svelte';
	import type { LayoutUiProps } from '../types';
	import { getContext } from '../context';

	const props: LayoutUiProps = $props();
	const context = getContext();
	const garden = $derived(stateUi.config.theme === 'garden');
	const skyjump = $derived(stateUi.config.theme === 'skyjump');
	const controlsY = 400;
	const winY = 670;
	const sideX = 440;
	const uiScale = 1;
	const centerX = $derived(context.stateLayoutDerived.mainLayoutStandard().width * 0.5);

	const DRAWER_Y = {
		unfold: 0,
		fold: 550,
	};
	const drawerTween = new Tween(stateUi.drawerFold ? DRAWER_Y.fold : DRAWER_Y.unfold, {
		easing: cubicInOut,
	});

	const DRAWER_BUTTON_Y = {
		unfold: 0,
		fold: 50,
	};
	const drawerButtonTween = new Tween(
		stateUi.drawerFold ? DRAWER_BUTTON_Y.fold : DRAWER_BUTTON_Y.unfold,
		{
			easing: cubicInOut,
		},
	);

	let drawerButtonFadeComplete = $state(() => {});

	context.eventEmitter.subscribeOnMount({
		drawerButtonShow: async () => {
			if (!stateUi.drawerButtonShow) {
				stateUi.drawerButtonShow = true;
				await waitForResolve((resolve) => (drawerButtonFadeComplete = resolve));
			}
		},
		drawerButtonHide: async () => {
			if (stateUi.drawerButtonShow) {
				stateUi.drawerButtonShow = false;
				await waitForResolve((resolve) => (drawerButtonFadeComplete = resolve));
			}
		},
		drawerUnfold: async () => {
			if (stateUi.drawerFold) {
				drawerButtonTween.set(DRAWER_BUTTON_Y.unfold);
				await drawerTween.set(DRAWER_Y.unfold);
			}
		},
		drawerFold: async () => {
			if (!stateUi.drawerFold) {
				drawerButtonTween.set(DRAWER_BUTTON_Y.fold);
				await drawerTween.set(DRAWER_Y.fold);
			}
		},
	});
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
		<Container y={drawerTween.current}>
			<Container
				x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 - sideX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - controlsY}
				scale={uiScale}
			>
				{@render props.buttonMenu({ anchor: 0.5 })}
			</Container>

			<Container
				x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 + sideX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - controlsY}
				scale={uiScale}
			>
				{@render props.buttonBuyBonus({ anchor: 0.5 })}
			</Container>

			<Container
				x={centerX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - controlsY}
				scale={uiScale}
			>
				{@render props.buttonBet({ anchor: 0.5 })}
			</Container>

			<Container
				x={centerX - 180}
				y={context.stateLayoutDerived.mainLayoutStandard().height - controlsY}
				scale={uiScale}
			>
				{@render props.buttonAutoSpin({ anchor: 0.5 })}
			</Container>

			<Container
				x={centerX + 180}
				y={context.stateLayoutDerived.mainLayoutStandard().height - controlsY}
				scale={uiScale}
			>
				{@render props.buttonTurbo({ anchor: 0.5 })}
			</Container>

			<Container
				x={centerX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 270}
				scale={uiScale}
			>
				{@render props.amountBalance({ stacked: true })}
			</Container>
		</Container>

		<Container y={Math.min(drawerTween.current, 350)}>
			<Container
				x={centerX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - winY}
				scale={uiScale}
			>
				{@render props.amountWin({ stacked: true })}
			</Container>
		</Container>
	</MainContainer>

	<MainContainer standard alignVertical="bottom">
		{#if stateUi.freeSpinCounterShow}
			<Container
				x={centerX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 130}
				scale={uiScale}
			>
				<LabelFreeSpinCounter stacked />
			</Container>
		{:else}
			<Container
				x={centerX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 130}
				scale={uiScale}
			>
				{@render props.amountBet({ stacked: true })}
			</Container>

			<Container
				x={centerX - 390}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 85}
				scale={uiScale}
			>
				{@render props.buttonDecrease({ anchor: 0.5 })}
			</Container>

			<Container
				x={centerX + 390}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 85}
				scale={uiScale}
			>
				{@render props.buttonIncrease({ anchor: 0.5 })}
			</Container>
		{/if}

		<FadeContainer
			persistent
			show={stateUi.drawerButtonShow}
			oncomplete={drawerButtonFadeComplete}
			y={drawerButtonTween.current}
		>
			<Container
				x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 + 440}
				y={context.stateLayoutDerived.mainLayoutStandard().height - 105}
			>
				<ButtonDrawer disabled={!stateUi.drawerButtonShow} anchor={0.5} />
			</Container>
		</FadeContainer>
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
				x={context.stateLayoutDerived.mainLayoutStandard().width * 0.5 - sideX}
				y={context.stateLayoutDerived.mainLayoutStandard().height - controlsY}
			>
				<Container y={-190 - 210 * 3}>
					{@render props.buttonPayTable({ anchor: 0.5 })}
				</Container>

				<Container y={-190 - 210 * 2}>
					{@render props.buttonGameRules({ anchor: 0.5 })}
				</Container>

				<Container y={-190 - 210 * 1}>
					{@render props.buttonSettings({ anchor: 0.5 })}
				</Container>

				<Container y={-190}>
					{@render props.buttonSoundSwitch({ anchor: 0.5 })}
				</Container>

				<Container>
					{@render props.buttonMenuClose({ anchor: 0.5 })}
				</Container>
			</Container>
		</MainContainer>
	{/if}
{/if}
