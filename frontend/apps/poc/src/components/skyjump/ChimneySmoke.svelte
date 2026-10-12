<script lang="ts">
	import { registerSmoke, SMOKE_CANVAS } from '../../game/loungeScene/chimneySmoke';

	type Props = {
		/** Chimney top in the 1672x941 buildings plane, as fractions of that plane. */
		x: number;
		y: number;
		/** Plume height as a fraction of the plane height. */
		h: number;
		phaseMs?: number;
	};

	let { x, y, h, phaseMs = 0 }: Props = $props();
	let canvas = $state<HTMLCanvasElement | null>(null);

	$effect(() => {
		const el = canvas;
		if (!el) return;
		return registerSmoke(el, phaseMs);
	});
</script>

<!-- Anchored by the bottom centre of the plume (the artwork's last rows) on the chimney top. -->
<canvas
	bind:this={canvas}
	class="smoke"
	width={SMOKE_CANVAS.w}
	height={SMOKE_CANVAS.h}
	style:left={`${x * 100}%`}
	style:top={`${y * 100}%`}
	style:height={`${h * 100}%`}
></canvas>

<style>
	/* Beats Game.svelte's `.skyjump-viewport canvas { position: relative; z-index: 19 }`. */
	:global(.skyjump-viewport canvas.smoke.smoke) {
		position: absolute;
		z-index: auto;
		aspect-ratio: 256 / 342;
		/* Plume sits above its anchor: bottom centre on (x, y). */
		transform: translate(-50%, -99%);
		opacity: 0.3;
		pointer-events: none;
	}
</style>
