<script lang="ts">
	import { SKY_ART, SKY_STARS } from '../../game/loungeScene/skyStars';

	/**
	 * The sparkle stars of the farthest sky layer twinkle at random: bigger and brighter for 0.9 s, 1-3 at a time every
	 * 0.8-2.4 s. Sits directly on the sky plane (same box), under the clouds and the houses.
	 */
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
			const free = SKY_STARS.map((_, i) => i).filter((i) => !(i in active));
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
			timers.add(setTimeout(fire, 800 + Math.random() * 1600));
		};
		timers.add(setTimeout(fire, 600));
		return () => {
			stopped = true;
			for (const t of timers) clearTimeout(t);
			active = {};
		};
	});
</script>

<div class="stars" aria-hidden="true">
	{#each SKY_STARS as star, i (i)}
		<img
			class="star"
			class:pulse={i in active}
			src={star.src}
			alt=""
			draggable="false"
			style:left={`${(star.x / SKY_ART.w) * 100}%`}
			style:top={`${(star.y / SKY_ART.h) * 100}%`}
			style:width={`${(star.w / SKY_ART.w) * 100}%`}
			style:height={`${(star.h / SKY_ART.h) * 100}%`}
		/>
	{/each}
</div>

<style>
	.stars {
		position: absolute;
		inset: 0;
		pointer-events: none;
		user-select: none;
	}

	.star {
		position: absolute;
		max-width: none;
		opacity: 0;
		transform-origin: 50% 50%;
	}

	.star.pulse {
		animation: star-twinkle 900ms ease-in-out both;
	}

	@keyframes star-twinkle {
		0%,
		100% {
			opacity: 1;
			transform: scale(1);
			filter: brightness(1);
		}
		50% {
			opacity: 1;
			transform: scale(1.7);
			filter: brightness(1.9) drop-shadow(0 0 4px rgba(255, 236, 190, 0.95));
		}
	}
</style>
