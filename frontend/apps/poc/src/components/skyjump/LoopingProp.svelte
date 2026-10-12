<script lang="ts">
	import { PROP_FRAME, type PropId } from '../../game/loungeCharacters/config';
	import { createPropPlayer } from '../../game/loungeCharacters/propPlayer';

	type Props = {
		prop: PropId;
		/** CSS box (any unit) of the whole 562x748 / 530x792 frame. */
		left: string;
		top: string;
		height: string;
		/** Mirror horizontally (the two plants and the stanchions are mirrored pairs). */
		flip?: boolean;
		/** Start this far into the loop (ms) so two copies never move in sync. */
		offsetMs?: number;
		z?: number;
		/** CSS blur in px, to match the softness of the background artwork. */
		blur?: number;
		/** Playback speed (0.5 = twice as slow). */
		rate?: number;
		/** Opt out of the celebration blur (scene plants stay crisp under the lifted plate). */
		sharp?: boolean;
		/** CSS filter (e.g. brightness) to blend the prop into its surroundings. */
		tone?: string;
		/** Fires once, when the first frame is on the canvas. */
		onready?: () => void;
	};

	let { prop, left, top, height, flip = false, offsetMs = 0, z = 1, blur = 0, rate, sharp = false, tone = '', onready }: Props = $props();

	let canvas = $state<HTMLCanvasElement | null>(null);
	const frame = $derived(PROP_FRAME[prop]);

	$effect(() => {
		const el = canvas;
		if (!el) return;
		const { player, start } = createPropPlayer(prop, el, rate, offsetMs);
		let fired = false;
		const fire = () => {
			if (fired || el.dataset.ready !== '1') return;
			fired = true;
			onready?.();
		};
		const observer = new MutationObserver(fire);
		observer.observe(el, { attributes: true, attributeFilter: ['data-ready'] });
		void start();
		return () => {
			observer.disconnect();
			player.destroy();
		};
	});
</script>

<canvas
	bind:this={canvas}
	class="looping-prop"
	class:figure={sharp}
	data-prop={prop}
	width={frame.w}
	height={frame.h}
	style:left
	style:top
	style:height
	style:aspect-ratio={`${frame.w} / ${frame.h}`}
	style:transform={flip ? 'scaleX(-1)' : undefined}
	style:z-index={z}
	style:filter={[tone, blur > 0 ? `blur(${blur}px)` : ''].filter(Boolean).join(' ') || undefined}
></canvas>

<style>
	/* Beats Game.svelte's `.skyjump-viewport canvas { position: relative; z-index: 19 }`. */
	:global(.skyjump-viewport canvas.looping-prop.looping-prop) {
		position: absolute;
		pointer-events: none;
		opacity: 0;
		transition: opacity 350ms ease-out;
	}

	:global(.skyjump-viewport canvas.looping-prop.looping-prop[data-ready='1']) {
		opacity: 1;
	}
</style>
