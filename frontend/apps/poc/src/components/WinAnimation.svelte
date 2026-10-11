<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { cubicInOut, elasticOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';

	import { Container, Rectangle } from 'pixi-svelte';
	import { ResponsiveText } from 'components-pixi';
	import { gardenGoldTextStyle } from '../game/gardenTextStyle';

	type Props = {
		label: string | null;
		children: Snippet;
	};

	const props: Props = $props();

	const scale = new Tween(0.55);
	const rotation = new Tween(-0.035);
	const glow = new Tween(0.35);
	let alive = true;

	const pulse = async () => {
		while (alive) {
			await Promise.all([
				scale.set(1.035, { duration: 700, easing: cubicInOut }),
				glow.set(0.75, { duration: 700, easing: cubicInOut }),
			]);
			await Promise.all([
				scale.set(1, { duration: 700, easing: cubicInOut }),
				glow.set(0.35, { duration: 700, easing: cubicInOut }),
			]);
		}
	};

	onMount(async () => {
		await Promise.all([
			scale.set(1, { duration: 520, easing: elasticOut }),
			rotation.set(0, { duration: 320, easing: cubicInOut }),
			glow.set(0.6, { duration: 520, easing: cubicInOut }),
		]);
		pulse();

		return () => {
			alive = false;
		};
	});
</script>

<Container scale={scale.current} rotation={rotation.current}>
	<Rectangle
		x={-474}
		y={-204}
		width={948}
		height={408}
		borderRadius={76}
		backgroundColor={0x1b3c27}
		backgroundAlpha={0.82}
		borderColor={0xffc43d}
		borderAlpha={glow.current}
		borderWidth={34}
	/>
	<Rectangle
		x={-450}
		y={-180}
		width={900}
		height={360}
		borderRadius={58}
		backgroundColor={0x315b39}
		backgroundAlpha={0.96}
		borderColor={0x527844}
		borderAlpha={1}
		borderWidth={12}
	/>
	<Rectangle
		x={-420}
		y={-150}
		width={840}
		height={300}
		borderRadius={42}
		backgroundColor={0x122719}
		backgroundAlpha={0.75}
		borderColor={0xf0a43a}
		borderAlpha={0.8}
		borderWidth={5}
	/>

	{#if props.label}
		<ResponsiveText
			y={-92}
			anchor={0.5}
			maxWidth={760}
			text={props.label}
			style={gardenGoldTextStyle({ fontSize: 112, letterSpacing: 2, display: true })}
		/>
	{/if}

	<Container y={58}>
		{@render props.children()}
	</Container>
</Container>
