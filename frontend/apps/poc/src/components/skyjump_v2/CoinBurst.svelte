<script lang="ts">
	import { onMount } from 'svelte';

	import { resolveGameAsset } from '../../game/resolveGameAsset';
	import { playV2AudioHook } from '../../game/skyjump_v2/audio';

	/**
	 * Win coins: `count` coins start behind the middle of the win header (under it), one after another, and are thrown
	 * alternately to the left and to the right: a little upwards first, then falling off the bottom of the screen.
	 * Each coin turns once over its flight (the 180 -> 90 degree frames and back again, 20 frames of one atlas).
	 * A sound plays when a coin appears and another when it leaves the screen.
	 */
	type Props = {
		count: number;
		/** Where the coins start, as fractions of the layer (the middle of the header). */
		originX?: number;
		originY?: number;
	};

	const { count, originX = 0.5, originY = 0.36 }: Props = $props();

	const ATLAS = resolveGameAsset('assets/midnight-lounge/fx/win_coin_atlas.png');
	const COLS = 5;
	const ROWS = 4;
	const FRAMES = COLS * ROWS;
	/** Coins start over this many ms at most (the last coin still has its whole flight). */
	const MAX_SPAWN_WINDOW_MS = 2400;

	type Coin = {
		el: HTMLDivElement | null;
		t0: number;
		x0: number;
		y0: number;
		vx: number;
		vy: number;
		g: number;
		duration: number;
		started: boolean;
		gone: boolean;
	};

	let layer = $state<HTMLDivElement | null>(null);
	const coins: Coin[] = [];
	let indices = $state<number[]>([]);

	onMount(() => {
		if (typeof window === 'undefined' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		indices = Array.from({ length: count }, (_, i) => i);
		let raf = 0;
		let stopped = false;
		const startAt = performance.now();
		let ready = false;

		const boot = () => {
			if (!layer) return;
			const box = layer.getBoundingClientRect();
			const W = box.width || 1280;
			const H = box.height || 720;
			const size = Math.max(40, Math.min(84, W * 0.1));
			const windowMs = Math.min(MAX_SPAWN_WINDOW_MS, count * 70);
			const els = layer.querySelectorAll<HTMLDivElement>('.win-coin');
			els.forEach((el, i) => {
				const side = i % 2 === 0 ? -1 : 1;
				const rnd = (a: number, b: number) => a + Math.random() * (b - a);
				const vx = side * W * rnd(0.07, 0.2);
				const vy = -H * rnd(0.55, 0.95);
				const g = H * 1.5;
				const x0 = W * originX;
				const y0 = H * originY;
				const yExit = H + size;
				// y(t) = y0 + vy t + g t^2 / 2 = yExit  ->  t = (-vy + sqrt(vy^2 - 2 g (y0 - yExit))) / g
				const t = (-vy + Math.sqrt(Math.max(0, vy * vy - 2 * g * (y0 - yExit)))) / g;
				coins[i] = {
					el,
					t0: startAt + 250 + (i * windowMs) / Math.max(1, count),
					x0,
					y0,
					vx,
					vy,
					g,
					duration: t * 1000,
					started: false,
					gone: false,
				};
				el.style.width = `${size}px`;
				el.style.height = `${size}px`;
				el.style.display = 'none';
			});
			ready = true;
		};

		const frame = (now: number) => {
			if (stopped) return;
			raf = requestAnimationFrame(frame);
			if (!ready) return boot();
			for (const coin of coins) {
				if (!coin || coin.gone || !coin.el) continue;
				if (now < coin.t0) continue;
				const age = (now - coin.t0) / 1000;
				const el = coin.el;
				if (!coin.started) {
					coin.started = true;
					el.style.display = 'block';
					playV2AudioHook('COIN_SPAWN');
				}
				const g = coin.g;
				const x = coin.x0 + coin.vx * age;
				const y = coin.y0 + coin.vy * age + 0.5 * g * age * age;
				const u = Math.min(1, age / (coin.duration / 1000));
				// one full turn: frames 0 -> 19 (180 -> 90 degrees) and back
				const phase = u * 2;
				const idx = Math.round((phase <= 1 ? phase : 2 - phase) * (FRAMES - 1));
				const col = idx % COLS;
				const row = Math.floor(idx / COLS);
				el.style.backgroundPosition = `${(col / (COLS - 1)) * 100}% ${(row / (ROWS - 1)) * 100}%`;
				el.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
				if (u >= 1) {
					coin.gone = true;
					el.style.display = 'none';
					playV2AudioHook('COIN_ESCAPE');
				}
			}
			if (coins.length === count && coins.every((c) => c?.gone)) {
				stopped = true;
				cancelAnimationFrame(raf);
			}
		};
		raf = requestAnimationFrame(frame);

		return () => {
			stopped = true;
			cancelAnimationFrame(raf);
		};
	});
</script>

<div class="coin-layer" bind:this={layer} aria-hidden="true" data-test="skyjump-v2-win-coins">
	{#each indices as i (i)}
		<div class="win-coin" style:background-image={`url(${ATLAS})`}></div>
	{/each}
</div>

<style>
	.coin-layer {
		position: absolute;
		inset: 0;
		z-index: 1;
		overflow: hidden;
		pointer-events: none;
	}

	.win-coin {
		position: absolute;
		left: 0;
		top: 0;
		display: none;
		background-size: 500% 400%;
		background-repeat: no-repeat;
		will-change: transform;
		filter: drop-shadow(0 3px 4px rgba(0, 0, 0, 0.45));
	}
</style>
