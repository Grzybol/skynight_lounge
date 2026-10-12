<script lang="ts">
	import { onMount } from 'svelte';
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';
	import { Rectangle } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import type { Reel } from '../game/stateGame.svelte';
	import { REEL_PADDING, SYMBOL_SIZE } from '../game/constants';

	type Props = {
		reel: Reel;
		oncomplete: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	const alpha = new Tween(0);
	const scale = new Tween(0.86);
	let alive = true;
	let stopping = false;

	const x = $derived((props.reel.reelIndex + REEL_PADDING) * SYMBOL_SIZE);
	const y = 0;

	const pulse = async () => {
		while (alive && !stopping) {
			await Promise.all([
				alpha.set(0.95, { duration: 360, easing: cubicInOut }),
				scale.set(1.05, { duration: 360, easing: cubicInOut }),
			]);
			await Promise.all([
				alpha.set(0.35, { duration: 360, easing: cubicInOut }),
				scale.set(0.97, { duration: 360, easing: cubicInOut }),
			]);
		}
	};

	onMount(async () => {
		await Promise.all([
			alpha.set(0.75, { duration: 220, easing: cubicInOut }),
			scale.set(1, { duration: 260, easing: cubicInOut }),
		]);
		pulse();

		return () => {
			alive = false;
		};
	});

	$effect(() => {
		if (props.reel.reelState.motion === 'stopped' && !stopping) {
			stopping = true;
			Promise.all([
				alpha.set(0, { duration: 260, easing: cubicInOut }),
				scale.set(1.16, { duration: 260, easing: cubicInOut }),
			]).then(() => {
				if (alive) props.oncomplete();
			});
		}
	});
</script>

<Rectangle
	x={x - SYMBOL_SIZE * 0.47 * scale.current}
	y={y - SYMBOL_SIZE * 0.08}
	width={SYMBOL_SIZE * 0.94 * scale.current}
	height={context.stateGameDerived.boardLayout().height + SYMBOL_SIZE * 0.16}
	borderRadius={24}
	backgroundColor={0x68b246}
	backgroundAlpha={alpha.current * 0.12}
	borderColor={0xffc64a}
	borderAlpha={alpha.current}
	borderWidth={10}
/>
<Rectangle
	x={x - SYMBOL_SIZE * 0.39 * scale.current}
	{y}
	width={SYMBOL_SIZE * 0.78 * scale.current}
	height={context.stateGameDerived.boardLayout().height}
	borderRadius={18}
	backgroundColor={0x173522}
	backgroundAlpha={alpha.current * 0.08}
	borderColor={0x9edf69}
	borderAlpha={alpha.current * 0.7}
	borderWidth={4}
/>
