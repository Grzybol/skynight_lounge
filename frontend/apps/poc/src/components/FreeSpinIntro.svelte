<script lang="ts" module>
	export type EmitterEventFreeSpinIntro =
		| { type: 'freeSpinIntroShow' }
		| { type: 'freeSpinIntroHide' }
		| { type: 'freeSpinIntroUpdate'; totalFreeSpins: number };
</script>

<script lang="ts">
	import { Container, Text } from 'pixi-svelte';
	import { CanvasSizeRectangle } from 'components-layout';
	import { FadeContainer } from 'components-pixi';
	import { waitForResolve } from 'utils-shared/wait';

	import { getContext } from '../game/context';
	import PressToContinue from './PressToContinue.svelte';
	import FreeSpinAnimation from './FreeSpinAnimation.svelte';
	import { gardenGoldTextStyle } from '../game/gardenTextStyle';

	const context = getContext();

	let show = $state(false);
	let freeSpinsFromEvent = $state(0);
	let oncomplete = $state(() => {});

	context.eventEmitter.subscribeOnMount({
		freeSpinIntroShow: () => (show = true),
		freeSpinIntroHide: () => (show = false),
		freeSpinIntroUpdate: async (emitterEvent) => {
			freeSpinsFromEvent = emitterEvent.totalFreeSpins;
			await waitForResolve((resolve) => (oncomplete = resolve));
		},
	});
</script>

<FadeContainer {show}>
	<CanvasSizeRectangle backgroundColor={0x0d1e13} backgroundAlpha={0.72} />

	<FreeSpinAnimation>
		{#snippet children({ sizes })}
			<Container>
				<Text
					y={-125}
					anchor={0.5}
					text="FREE SPINS"
					style={gardenGoldTextStyle({
						fontSize: sizes.width * 0.12,
						letterSpacing: 2,
						display: true,
					})}
				/>
				<Text
					y={15}
					anchor={0.5}
					text={freeSpinsFromEvent}
					style={gardenGoldTextStyle({ fontSize: sizes.width * 0.22 })}
				/>
				<Text
					y={145}
					anchor={0.5}
					text="AWARDED"
					style={gardenGoldTextStyle({
						fontSize: sizes.width * 0.07,
						letterSpacing: 3,
						display: true,
					})}
				/>
			</Container>
		{/snippet}
	</FreeSpinAnimation>

	<PressToContinue onpress={() => oncomplete()} />
</FadeContainer>
