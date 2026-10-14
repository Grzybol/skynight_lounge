<script lang="ts">
	import { V2_FRAME_BANDS } from '../../game/skyjump_v2/presentationLayout';

	/**
	 * One layer of the slot frame art, redrawn so all five rows have the same height.
	 * The 1672x941 art is cut into a top piece, five row bands and a bottom piece; every row band is
	 * stretched vertically to the same height (the art's rows were 138 .. 127 px tall). The caller sizes
	 * this box to the whole (equalised) frame.
	 */
	type Props = {
		src: string;
		width: number;
		height: number;
		class?: string;
		testId?: string;
	};

	let { src, width, height, class: className = '', testId }: Props = $props();

	const B = V2_FRAME_BANDS;
	/** Rendered px per output art px. */
	const s = $derived(height / B.outH);
	const bands = $derived(
		B.bands.map((band) => {
			const sk = (band.outEnd - band.outStart) / (band.srcEnd - band.srcStart);
			return {
				top: band.outStart * s,
				// 0.6 px extra so rounding never leaves a hairline between neighbouring bands.
				height: (band.outEnd - band.outStart) * s + 0.6,
				bgH: B.srcH * sk * s,
				bgY: -band.srcStart * sk * s,
			};
		}),
	);
</script>

<div class={`slot-frame-layer ${className}`} style:width={`${width}px`} style:height={`${height}px`} data-test={testId} aria-hidden="true">
	{#each bands as band}
		<div
			class="band"
			style:top={`${band.top}px`}
			style:height={`${band.height}px`}
			style:background-image={`url(${src})`}
			style:background-size={`${width}px ${band.bgH}px`}
			style:background-position={`0 ${band.bgY}px`}
		></div>
	{/each}
</div>

<style>
	.slot-frame-layer {
		position: absolute;
		pointer-events: none;
		user-select: none;
	}

	.band {
		position: absolute;
		left: 0;
		right: 0;
		background-repeat: no-repeat;
	}
</style>
