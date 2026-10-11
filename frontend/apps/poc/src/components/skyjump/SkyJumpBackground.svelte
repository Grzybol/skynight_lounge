<script lang="ts">
	import { getContext } from '../../game/context';
	import { loungeBarSrc, loungePlateSrc } from '../../game/midnightLoungeTheme';
	import { LOUNGE_BAR_PLACEMENT as BAR } from '../../game/loungeCharacters/config';
	import LoungeCharacter from './LoungeCharacter.svelte';

	const context = getContext();
	let plate = $state<HTMLDivElement | null>(null);

	let plateFrame = $state({ left: '0px', top: '0px', width: '100%', height: '100%' });

	$effect(() => {
		const el = plate;
		if (!el) return;

		const place = () => {
			const viewport = el.closest('.skyjump-viewport');
			if (!viewport) return;
			const css = getComputedStyle(viewport);
			const read = (name: string) => parseFloat(css.getPropertyValue(name));
			const playLeft = read('--play-left');
			const playTop = read('--play-top');
			const playW = read('--play-width');
			const playH = read('--play-height');
			if (![playLeft, playTop, playW, playH].every((n) => Number.isFinite(n)) || playW <= 0) {
				return;
			}
			plateFrame = {
				left: `${playLeft}px`,
				top: `${playTop}px`,
				width: `${playW}px`,
				height: `${playH}px`,
			};
		};

		place();
		const observer = new ResizeObserver(place);
		observer.observe(el);
		const viewport = el.closest('.skyjump-viewport');
		if (viewport) observer.observe(viewport);
		const kick = requestAnimationFrame(place);
		return () => {
			cancelAnimationFrame(kick);
			observer.disconnect();
		};
	});
</script>

{#if context.stateGame.screen === 'play'}
	<div class="plate" data-lounge-bg bind:this={plate}>
		<img
			class="art"
			src={loungePlateSrc}
			alt=""
			style:left={plateFrame.left}
			style:top={plateFrame.top}
			style:width={plateFrame.width}
			style:height={plateFrame.height}
		/>
	</div>
	<!-- Same plate, lifted above the board while a celebration runs: fades in and out. -->
	<div
		class="win-plate"
		data-lounge-win-plate
		style:left={plateFrame.left}
		style:top={plateFrame.top}
		style:width={plateFrame.width}
		style:height={plateFrame.height}
	>
		<img class="art" src={loungePlateSrc} alt="" draggable="false" />
	</div>
	<LoungeCharacter character="bartender" />
	<!-- Bar in front of the bartender: the counter hides him from the belt down. -->
	<div
		class="bar-clip"
		data-lounge-bar
		style:left={plateFrame.left}
		style:top={plateFrame.top}
		style:width={plateFrame.width}
		style:height={plateFrame.height}
	>
		<img
			class="bar"
			src={loungeBarSrc}
			alt=""
			draggable="false"
			style:left={`${BAR.offsetX * 100}%`}
			style:top={`${BAR.offsetY * 100}%`}
			style:width={`${BAR.scale * 100}%`}
		/>
	</div>
	<LoungeCharacter character="woman" />
{/if}

<style>
	.plate {
		position: absolute;
		inset: 0;
		z-index: 0;
		overflow: hidden;
		pointer-events: none;
		background: #10080c;
	}

	.art {
		position: absolute;
		z-index: 0;
		object-fit: fill;
		pointer-events: none;
		transform-origin: center center;
	}

	.bar-clip {
		position: absolute;
		/* Above the characters (z 1), below the board and HUD. */
		z-index: 2;
		overflow: hidden;
		pointer-events: none;
	}

	.bar {
		/* Slightly soft, like the (upscaled) plate behind it. */
		filter: blur(0.315px);
		position: absolute;
		max-width: none;
		height: auto;
		pointer-events: none;
	}

	/*
	 * Celebration: the plate is lifted above the board (z 20) and fades in and out over 700 ms
	 * (V2_WIN_BLUR_FADE_MS) together with the HUD blur. `data-win-focus` outlives the celebration
	 * by the fade time, so the bar (z 31) and the characters (z 30) never drop behind the fading plate.
	 */
	.win-plate {
		position: absolute;
		z-index: 20;
		overflow: hidden;
		pointer-events: none;
		opacity: 0;
		transition: opacity 700ms ease;
	}

	.win-plate .art {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}

	:global(.skyjump-viewport[data-win-plate]) .win-plate {
		opacity: 1;
	}

	:global(.skyjump-viewport[data-win-focus]) .bar-clip {
		z-index: 31;
	}
</style>
