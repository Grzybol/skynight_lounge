<script lang="ts">
	import { onMount } from 'svelte';
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';
	import { Circle, Container, Rectangle } from 'pixi-svelte';

	import { getContext } from '../game/context';

	type Props = { feature?: boolean };

	const props: Props = $props();
	const context = getContext();
	const drift = new Tween(0);
	const pulse = new Tween(0.25);
	let alive = true;

	const motes = [
		{ x: 0.08, y: 0.22, size: 4, phase: 0.12 },
		{ x: 0.16, y: 0.7, size: 3, phase: 0.72 },
		{ x: 0.25, y: 0.38, size: 5, phase: 0.34 },
		{ x: 0.36, y: 0.78, size: 3, phase: 0.9 },
		{ x: 0.47, y: 0.17, size: 4, phase: 0.52 },
		{ x: 0.58, y: 0.68, size: 5, phase: 0.2 },
		{ x: 0.69, y: 0.31, size: 3, phase: 0.82 },
		{ x: 0.78, y: 0.74, size: 4, phase: 0.42 },
		{ x: 0.89, y: 0.24, size: 5, phase: 0.64 },
		{ x: 0.95, y: 0.58, size: 3, phase: 0.05 },
	];

	const animate = async () => {
		while (alive) {
			await Promise.all([
				drift.set(1, { duration: 5200, easing: cubicInOut }),
				pulse.set(0.72, { duration: 1600, easing: cubicInOut }),
			]);
			drift.set(0, { duration: 0 });
			await pulse.set(0.25, { duration: 1600, easing: cubicInOut });
		}
	};

	onMount(() => {
		animate();
		return () => {
			alive = false;
		};
	});

	const canvas = $derived(context.stateLayoutDerived.canvasSizes());
</script>

<Container zIndex={props.feature ? -0.8 : -1.8}>
	{#if props.feature}
		<Rectangle
			width={canvas.width}
			height={canvas.height}
			backgroundColor={0x315d38}
			backgroundAlpha={0.18 + pulse.current * 0.12}
		/>
		<Rectangle
			x={canvas.width * 0.14}
			y={canvas.height * 0.08}
			width={canvas.width * 0.72}
			height={canvas.height * 0.84}
			borderRadius={canvas.height * 0.18}
			backgroundColor={0x8fd45a}
			backgroundAlpha={0.035 + pulse.current * 0.035}
			borderColor={0xd8ff96}
			borderAlpha={0.08 + pulse.current * 0.08}
			borderWidth={28}
		/>
	{:else}
		<Rectangle
			width={canvas.width}
			height={canvas.height}
			backgroundColor={0xffd86b}
			backgroundAlpha={0.025 + pulse.current * 0.018}
		/>
	{/if}

	{#each motes as mote}
		<Circle
			x={canvas.width * mote.x + Math.sin((drift.current + mote.phase) * Math.PI * 2) * 16}
			y={canvas.height * mote.y - drift.current * 34}
			radius={mote.size * (props.feature ? 1.3 : 1)}
			backgroundColor={props.feature ? 0xc9ff7f : 0xfff1a6}
			backgroundAlpha={0.18 + pulse.current * 0.42}
		/>
	{/each}
</Container>
