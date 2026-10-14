<script lang="ts">
	import { FRAME_GEMS } from '../../game/skyjump_v2/frameGems';
	import { V2_FRAME_WINDOWS } from '../../game/skyjump_v2/presentationLayout';

	/**
	 * Red gems of the slot frame pulse: a little bigger and brighter for 0.9 s. Every 1-3 s one to three gems
	 * (never one that is still pulsing) start. The gems are cut out of the frame art, so the pulse sits exactly on them.
	 */
	type Props = { width: number; height: number };
	const { width, height }: Props = $props();

	const ART = V2_FRAME_WINDOWS.art;
	const PULSE_MS = 900;
	let active = $state<Record<number, number>>({});

	$effect(() => {
		if (typeof window === 'undefined') return;
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		const timers = new Set<ReturnType<typeof setTimeout>>();
		let stopped = false;
		const fire = () => {
			if (stopped) return;
			const count = 1 + Math.floor(Math.random() * 3);
			const free = FRAME_GEMS.map((_, i) => i).filter((i) => !(i in active));
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
			const wait = setTimeout(fire, 1000 + Math.random() * 2000);
			timers.add(wait);
		};
		const first = setTimeout(fire, 800);
		timers.add(first);
		return () => {
			stopped = true;
			for (const t of timers) clearTimeout(t);
			active = {};
		};
	});
</script>

<div class="gems" style:width={`${width}px`} style:height={`${height}px`} aria-hidden="true" data-test="skyjump-v2-frame-gems">
	{#each FRAME_GEMS as gem, i (i)}
		<img
			class="gem"
			class:pulse={i in active}
			src={gem.src}
			alt=""
			draggable="false"
			style:left={`${(gem.x / ART.w) * 100}%`}
			style:top={`${(gem.y / ART.h) * 100}%`}
			style:width={`${(gem.w / ART.w) * 100}%`}
			style:height={`${(gem.h / ART.h) * 100}%`}
			style:--pulse-ms={`${PULSE_MS}ms`}
		/>
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
			transform: scale(1.28);
			filter: brightness(1.75) saturate(1.2) drop-shadow(0 0 5px rgba(255, 110, 110, 0.95));
		}
	}
</style>
