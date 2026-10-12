<script lang="ts">
	import { onMount } from 'svelte';
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';
	import { Rectangle } from 'pixi-svelte';

	import { SYMBOL_SIZE } from '../game/constants';

	type Props = {
		x?: number;
		y?: number;
	};

	const props: Props = $props();
	const alpha = new Tween(0);
	const scale = new Tween(0.82);
	let alive = true;

	const animate = async () => {
		await Promise.all([
			alpha.set(0.96, { duration: 180, easing: cubicInOut }),
			scale.set(1.04, { duration: 240, easing: cubicInOut }),
		]);

		while (alive) {
			await Promise.all([
				alpha.set(0.48, { duration: 360, easing: cubicInOut }),
				scale.set(0.96, { duration: 360, easing: cubicInOut }),
			]);
			await Promise.all([
				alpha.set(0.9, { duration: 360, easing: cubicInOut }),
				scale.set(1.03, { duration: 360, easing: cubicInOut }),
			]);
		}
	};

	onMount(() => {
		animate();
		return () => {
			alive = false;
		};
	});
</script>

<Rectangle
	x={(props.x ?? 0) - SYMBOL_SIZE * 0.47 * scale.current}
	y={(props.y ?? 0) - SYMBOL_SIZE * 0.47 * scale.current}
	width={SYMBOL_SIZE * 0.94 * scale.current}
	height={SYMBOL_SIZE * 0.94 * scale.current}
	borderRadius={24}
	backgroundColor={0x3f733c}
	backgroundAlpha={alpha.current * 0.1}
	borderColor={0xffc955}
	borderAlpha={alpha.current}
	borderWidth={7}
/>
<Rectangle
	x={(props.x ?? 0) - SYMBOL_SIZE * 0.405 * scale.current}
	y={(props.y ?? 0) - SYMBOL_SIZE * 0.405 * scale.current}
	width={SYMBOL_SIZE * 0.81 * scale.current}
	height={SYMBOL_SIZE * 0.81 * scale.current}
	borderRadius={18}
	backgroundColor={0x183523}
	backgroundAlpha={0}
	borderColor={0x91d65a}
	borderAlpha={alpha.current * 0.72}
	borderWidth={3}
/>
