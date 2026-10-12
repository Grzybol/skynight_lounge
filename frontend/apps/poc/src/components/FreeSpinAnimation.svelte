<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { cubicInOut, elasticOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';

	import { Container, Rectangle, Sprite, type Sizes } from 'pixi-svelte';
	import { MainContainer } from 'components-layout';

	import { getContext } from '../game/context';

	type Props = {
		children: Snippet<[{ sizes: Sizes }]>;
	};

	const props: Props = $props();
	const context = getContext();

	const PANEL_SIZES = { width: 760, height: 500 };
	const scale = new Tween(0.45);
	const rotation = new Tween(-0.04);
	const glow = new Tween(0.3);
	const leafRotation = new Tween(-0.12);
	let alive = true;

	const pulse = async () => {
		while (alive) {
			await Promise.all([
				scale.set(1.025, { duration: 760, easing: cubicInOut }),
				glow.set(0.82, { duration: 760, easing: cubicInOut }),
				leafRotation.set(0.1, { duration: 760, easing: cubicInOut }),
			]);
			await Promise.all([
				scale.set(1, { duration: 760, easing: cubicInOut }),
				glow.set(0.35, { duration: 760, easing: cubicInOut }),
				leafRotation.set(-0.1, { duration: 760, easing: cubicInOut }),
			]);
		}
	};

	onMount(async () => {
		await Promise.all([
			scale.set(1, { duration: 560, easing: elasticOut }),
			rotation.set(0, { duration: 360, easing: cubicInOut }),
			glow.set(0.65, { duration: 560, easing: cubicInOut }),
		]);
		pulse();

		return () => {
			alive = false;
		};
	});
</script>

<MainContainer>
	<Container
		x={context.stateGameDerived.boardLayout().x}
		y={context.stateGameDerived.boardLayout().y}
		scale={scale.current}
		rotation={rotation.current}
	>
		<Rectangle
			x={-390}
			y={-280}
			width={780}
			height={560}
			borderRadius={90}
			backgroundColor={0x173522}
			backgroundAlpha={0.86}
			borderColor={0x8fce5a}
			borderAlpha={glow.current}
			borderWidth={38}
		/>
		<Rectangle
			x={-365}
			y={-252}
			width={730}
			height={504}
			borderRadius={68}
			backgroundColor={0x2f5837}
			backgroundAlpha={0.98}
			borderColor={0xf0c85a}
			borderAlpha={0.95}
			borderWidth={13}
		/>
		<Rectangle
			x={-335}
			y={-220}
			width={670}
			height={440}
			borderRadius={46}
			backgroundColor={0x102419}
			backgroundAlpha={0.82}
			borderColor={0x547a45}
			borderAlpha={1}
			borderWidth={5}
		/>

		<Sprite
			x={-300}
			y={-205}
			anchor={0.5}
			key="s.png"
			width={145}
			height={145}
			rotation={leafRotation.current}
		/>
		<Sprite
			x={300}
			y={205}
			anchor={0.5}
			key="s.png"
			width={145}
			height={145}
			rotation={-leafRotation.current}
		/>

		{@render props.children({ sizes: PANEL_SIZES })}
	</Container>
</MainContainer>
