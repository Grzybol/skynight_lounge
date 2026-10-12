<script lang="ts">
	import { Container, Sprite } from 'pixi-svelte';
	import { backOut, cubicIn, cubicInOut, elasticOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';

	import { SYMBOL_SIZE } from '../game/constants';
	import { getSymbolInfo } from '../game/utils';

	type Props = {
		x?: number;
		y?: number;
		symbolInfo: ReturnType<typeof getSymbolInfo>;
		oncomplete?: () => void;
		loop?: boolean;
	};

	const props: Props = $props();

	const scaleX = new Tween(1);
	const scaleY = new Tween(1);
	const rotation = new Tween(0);
	const alpha = new Tween(1);
	const glowAlpha = new Tween(0);
	const glowScale = new Tween(1);

	let runID = 0;

	const setScale = async (x: number, y: number, options: Parameters<typeof scaleX.set>[1] = {}) => {
		await Promise.all([scaleX.set(x, options), scaleY.set(y, options)]);
	};

	const reset = async () => {
		await Promise.all([
			setScale(1, 1, { duration: 0 }),
			rotation.set(0, { duration: 0 }),
			alpha.set(1, { duration: 0 }),
			glowAlpha.set(0, { duration: 0 }),
			glowScale.set(1, { duration: 0 }),
		]);
	};

	const animateWin = async (id: number) => {
		do {
			await Promise.all([
				setScale(0.72, 0.72, { duration: 0 }),
				rotation.set(-0.08, { duration: 0 }),
				glowAlpha.set(0.8, { duration: 0 }),
				glowScale.set(0.9, { duration: 0 }),
			]);
			await Promise.all([
				setScale(1.18, 1.18, { duration: 280, easing: elasticOut }),
				rotation.set(0.06, { duration: 220, easing: backOut }),
				glowScale.set(1.3, { duration: 320, easing: cubicInOut }),
			]);
			await Promise.all([
				setScale(1, 1, { duration: 180, easing: cubicInOut }),
				rotation.set(0, { duration: 180, easing: cubicInOut }),
				glowAlpha.set(0.2, { duration: 180, easing: cubicInOut }),
			]);
			if (props.loop && id === runID) {
				await Promise.all([
					setScale(1.07, 1.07, { duration: 360, easing: cubicInOut }),
					glowAlpha.set(0.65, { duration: 360, easing: cubicInOut }),
				]);
				await Promise.all([
					setScale(1, 1, { duration: 360, easing: cubicInOut }),
					glowAlpha.set(0.2, { duration: 360, easing: cubicInOut }),
				]);
			}
		} while (props.loop && id === runID);
	};

	const animateLand = async () => {
		await Promise.all([
			setScale(1.14, 0.72, { duration: 0 }),
			rotation.set(-0.045, { duration: 0 }),
			glowAlpha.set(0.65, { duration: 0 }),
			glowScale.set(1.16, { duration: 0 }),
		]);
		await Promise.all([
			setScale(0.92, 1.12, { duration: 120, easing: cubicInOut }),
			rotation.set(0.03, { duration: 120, easing: cubicInOut }),
		]);
		await Promise.all([
			setScale(1, 1, { duration: 220, easing: elasticOut }),
			rotation.set(0, { duration: 180, easing: cubicInOut }),
			glowAlpha.set(0, { duration: 260, easing: cubicInOut }),
		]);
	};

	const animateWild = async (id: number) => {
		await animateLand();
		if (id !== runID) return;
		await Promise.all([
			setScale(1.22, 1.22, { duration: 180, easing: backOut }),
			glowAlpha.set(0.9, { duration: 180 }),
			glowScale.set(1.38, { duration: 260 }),
		]);
		await Promise.all([
			setScale(1, 1, { duration: 220, easing: cubicInOut }),
			glowAlpha.set(0.15, { duration: 240 }),
		]);
	};

	const animateScatter = async (id: number) => {
		await animateWin(id);
		if (id !== runID || props.loop) return;
		await Promise.all([
			rotation.set(Math.PI * 2, { duration: 420, easing: cubicInOut }),
			glowScale.set(1.5, { duration: 420 }),
			glowAlpha.set(0, { duration: 420 }),
		]);
		rotation.set(0, { duration: 0 });
	};

	const animateExplosion = async () => {
		await Promise.all([
			setScale(1, 1, { duration: 0 }),
			glowAlpha.set(1, { duration: 0 }),
			glowScale.set(0.8, { duration: 0 }),
		]);
		await Promise.all([
			setScale(1.52, 1.52, { duration: 360, easing: cubicIn }),
			rotation.set(0.2, { duration: 360, easing: cubicIn }),
			alpha.set(0, { duration: 360, easing: cubicIn }),
			glowScale.set(1.8, { duration: 360, easing: cubicIn }),
			glowAlpha.set(0, { duration: 360, easing: cubicIn }),
		]);
	};

	const play = async (id: number, animation: string) => {
		await reset();
		if (id !== runID) return;

		if (animation === 'land') await animateLand();
		else if (animation === 'wildLand' || animation === 'wildWin') await animateWild(id);
		else if (animation === 'scatterLand' || animation === 'scatterWin') await animateScatter(id);
		else if (animation === 'explosion') await animateExplosion();
		else await animateWin(id);

		if (id === runID && !props.loop) props.oncomplete?.();
	};

	$effect(() => {
		const animation = 'animation' in props.symbolInfo ? props.symbolInfo.animation : 'win';
		props.loop;
		const id = ++runID;
		play(id, animation);
		return () => {
			runID += 1;
		};
	});
</script>

<Container
	x={props.x}
	y={props.y}
	rotation={rotation.current}
	scale={{ x: scaleX.current, y: scaleY.current }}
	alpha={alpha.current}
>
	<Sprite
		anchor={0.5}
		key={props.symbolInfo.assetKey}
		width={SYMBOL_SIZE * props.symbolInfo.sizeRatios.width * glowScale.current}
		height={SYMBOL_SIZE * props.symbolInfo.sizeRatios.height * glowScale.current}
		tint={0xffc928}
		alpha={glowAlpha.current}
	/>
	<Sprite
		anchor={0.5}
		key={props.symbolInfo.assetKey}
		width={SYMBOL_SIZE * props.symbolInfo.sizeRatios.width}
		height={SYMBOL_SIZE * props.symbolInfo.sizeRatios.height}
	/>
</Container>
