<script lang="ts">
	import { onMount } from 'svelte';
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';
	import { Container, Rectangle, Text } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { SKYJUMP_UI_FONT } from '../game/gardenTextStyle';

	type Props = {
		oncomplete: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	const progress = new Tween(0);
	const textScale = new Tween(0.55);
	const textAlpha = new Tween(0);

	const canvas = $derived(context.stateLayoutDerived.canvasSizes());

	onMount(async () => {
		await Promise.all([
			progress.set(1, { duration: 420, easing: cubicInOut }),
			textScale.set(1, { duration: 460, easing: cubicInOut }),
			textAlpha.set(1, { duration: 300, easing: cubicInOut }),
		]);
		await new Promise((resolve) => setTimeout(resolve, 180));
		await Promise.all([
			progress.set(0, { duration: 420, easing: cubicInOut }),
			textScale.set(1.18, { duration: 420, easing: cubicInOut }),
			textAlpha.set(0, { duration: 300, easing: cubicInOut }),
		]);
		props.oncomplete();
	});
</script>

<Container zIndex={1000}>
	<Rectangle
		width={canvas.width}
		height={canvas.height}
		backgroundColor={0x071526}
		backgroundAlpha={progress.current * 0.88}
	/>
	<Rectangle
		x={-canvas.width + canvas.width * progress.current}
		width={canvas.width * 0.56}
		height={canvas.height}
		backgroundColor={0x10243c}
		backgroundAlpha={0.96}
		borderColor={0xf0c14b}
		borderWidth={12}
	/>
	<Rectangle
		x={canvas.width * 1.44 - canvas.width * progress.current}
		width={canvas.width * 0.56}
		height={canvas.height}
		backgroundColor={0x0b1b2c}
		backgroundAlpha={0.96}
		borderColor={0x7ecbff}
		borderWidth={12}
	/>

	<Container
		x={canvas.width * 0.5}
		y={canvas.height * 0.5}
		scale={textScale.current}
		alpha={textAlpha.current}
	>
		<Text
			anchor={0.5}
			text="GATES OPEN"
			style={{
				fontFamily: SKYJUMP_UI_FONT,
				fontSize: 72,
				fontWeight: '900',
				letterSpacing: 2,
				fill: 0xf0c14b,
				stroke: { color: 0x10243c, width: 7 },
			}}
		/>
	</Container>
</Container>
