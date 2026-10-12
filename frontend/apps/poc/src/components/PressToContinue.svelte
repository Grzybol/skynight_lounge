<script lang="ts">
	import { onMount } from 'svelte';
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';

	import { MainContainer, OnPressFullScreen } from 'components-layout';
	import { OnHotkey } from 'components-shared';
	import { Container, Rectangle, Text } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { SKYJUMP_UI_FONT } from '../game/gardenTextStyle';

	type Props = {
		onpress: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	const glow = new Tween(0.35);
	const scale = new Tween(1);
	let alive = true;

	const pulse = async () => {
		while (alive) {
			await Promise.all([
				glow.set(0.9, { duration: 700, easing: cubicInOut }),
				scale.set(1.025, { duration: 700, easing: cubicInOut }),
			]);
			await Promise.all([
				glow.set(0.35, { duration: 700, easing: cubicInOut }),
				scale.set(1, { duration: 700, easing: cubicInOut }),
			]);
		}
	};

	onMount(() => {
		pulse();
		return () => {
			alive = false;
		};
	});
</script>

<MainContainer>
	<Container
		x={context.stateLayoutDerived.mainLayout().width * 0.5}
		y={context.stateLayoutDerived.mainLayout().height - 52}
		scale={scale.current}
	>
		<Rectangle
			x={-326}
			y={-38}
			width={652}
			height={76}
			borderRadius={38}
			backgroundColor={0x173522}
			backgroundAlpha={0.94}
			borderColor={0xe7a64b}
			borderAlpha={glow.current}
			borderWidth={8}
		/>
		<Text
			anchor={0.5}
			text="TAP OR PRESS SPACE TO CONTINUE"
			style={{
				fontFamily: SKYJUMP_UI_FONT,
				fontSize: 24,
				fontWeight: '700',
				letterSpacing: 2,
				fill: 0xffe3a0,
			}}
		/>
	</Container>
</MainContainer>
<OnHotkey hotkey="Space" onpress={() => props.onpress()} />
<OnPressFullScreen onpress={() => props.onpress()} />
