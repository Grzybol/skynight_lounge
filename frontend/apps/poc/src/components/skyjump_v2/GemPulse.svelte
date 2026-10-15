<script lang="ts">
	import { FRAME_GEMS } from '../../game/skyjump_v2/frameGems';
	import { V2_FRAME_WINDOWS } from '../../game/skyjump_v2/presentationLayout';

	/**
	 * Red gems of the slot frame pulse: a little bigger and brighter for 0.9 s. Every 1-3 s one to three of the small gems
	 * (never one that is still pulsing) start.
	 * The big crest ruby has its own, calmer controller (rare, varied length, half the growth); it rests while the reels roll.
	 */
	type Props = { width: number; height: number; rolling?: boolean };
	const { width, height, rolling = false }: Props = $props();

	const ART = V2_FRAME_WINDOWS.art;
	const PULSE_MS = 900;
	/** The crest ruby is the tallest gem. */
	const CREST = FRAME_GEMS.reduce((best, gem, i) => (gem.h > FRAME_GEMS[best].h ? i : best), 0);
	let active = $state<Record<number, number>>({});
	/** Crest pulse: run id (restarts the animation), length, peak scale and brightness. */
	let crest = $state({ run: 0, on: false, ms: 900, scale: 1.28, bright: 1.75 });

	const reduced = () =>
		typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	let crestOffTimer: ReturnType<typeof setTimeout> | undefined;
	const fireCrest = (ms: number, scale: number, bright: number) => {
		crest = { run: crest.run + 1, on: true, ms, scale, bright };
		clearTimeout(crestOffTimer);
		crestOffTimer = setTimeout(() => (crest = { ...crest, on: false }), ms + 40);
	};

	// Small gems.
	$effect(() => {
		if (typeof window === 'undefined' || reduced()) return;
		const timers = new Set<ReturnType<typeof setTimeout>>();
		let stopped = false;
		const fire = () => {
			if (stopped) return;
			const count = 1 + Math.floor(Math.random() * 3);
			const free = FRAME_GEMS.map((_, i) => i).filter((i) => i !== CREST && !(i in active));
			for (let n = 0; n < count && free.length > 0; n++) {
				const i = free.splice(Math.floor(Math.random() * free.length), 1)[0];
				active = { ...active, [i]: Date.now() };
				const done = setTimeout(() => {
					const next = { ...active };
					delete next[i];
					active = next;
					timers.delete(done);
				}, PULSE_MS + 40);
				timers.add(done);
			}
			timers.add(setTimeout(fire, 1000 + Math.random() * 2000));
		};
		timers.add(setTimeout(fire, 800));
		return () => {
			stopped = true;
			for (const t of timers) clearTimeout(t);
			active = {};
		};
	});

	// Crest ruby: rare (every 3-7 s), 0.7-1.6 s long, and only about half as much growth as the small gems.
	$effect(() => {
		if (typeof window === 'undefined' || reduced()) return;
		let stopped = false;
		let timer: ReturnType<typeof setTimeout>;
		const loop = () => {
			if (stopped) return;
			if (!rolling) fireCrest(700 + Math.random() * 900, 1.07 + Math.random() * 0.1, 1.35 + Math.random() * 0.4);
			timer = setTimeout(loop, 3000 + Math.random() * 4000);
		};
		timer = setTimeout(loop, 1500);
		return () => {
			stopped = true;
			clearTimeout(timer);
			clearTimeout(crestOffTimer);
		};
	});
</script>

<div
	class="gems"
	style:width={`${width}px`}
	style:height={`${height}px`}
	aria-hidden="true"
	data-test="skyjump-v2-frame-gems"
>
	{#each FRAME_GEMS as gem, i (i)}
		{#key i === CREST ? crest.run : 0}
			<img
				class="gem"
				class:pulse={i === CREST ? crest.on : i in active}
				src={gem.src}
				alt=""
				draggable="false"
				style:left={`${(gem.x / ART.w) * 100}%`}
				style:top={`${(gem.y / ART.h) * 100}%`}
				style:width={`${(gem.w / ART.w) * 100}%`}
				style:height={`${(gem.h / ART.h) * 100}%`}
				style:--pulse-ms={i === CREST ? `${crest.ms}ms` : `${PULSE_MS}ms`}
				style:--pulse-scale={i === CREST ? crest.scale : 1.28}
				style:--pulse-bright={i === CREST ? crest.bright : 1.75}
			/>
		{/key}
	{/each}
</div>

<style>
	.gems {
		position: absolute;
		left: 0;
		top: 0;
		pointer-events: none;
		user-select: none;
	}

	.gem {
		position: absolute;
		max-width: none;
		opacity: 0;
		transform-origin: 50% 50%;
	}

	.gem.pulse {
		animation: gem-pulse var(--pulse-ms, 900ms) ease-in-out both;
	}

	@keyframes gem-pulse {
		0%,
		100% {
			opacity: 1;
			transform: scale(1);
			filter: brightness(1);
		}
		50% {
			opacity: 1;
			transform: scale(var(--pulse-scale, 1.28));
			filter: brightness(var(--pulse-bright, 1.75)) saturate(1.2)
				drop-shadow(0 0 5px rgba(255, 110, 110, 0.95));
		}
	}
</style>
