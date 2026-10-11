<script lang="ts">
	import { getContext } from '../../game/context';
	import { resolveGameAsset } from '../../game/resolveGameAsset';
	import { propBox } from '../../game/loungeCharacters/propLayout';
	import { SCENE_PLANTS } from '../../game/loungeCharacters/propLayout';
	import {
		acquireSky,
		skyFrameUrl,
		skyState,
		SKY_CROSSFADE_MS,
		SKY_FRAME_COUNT,
		type SkyClip,
	} from '../../game/loungeScene/skyAnimation.svelte';
	import LoungeCharacter from './LoungeCharacter.svelte';
	import LoopingProp from './LoopingProp.svelte';

	const context = getContext();
	let plate = $state<HTMLDivElement | null>(null);
	/** True while a celebration (plus the plate's fade-out) runs: the lifted copy then also animates the plants. */
	let winFocus = $state(false);

	let plateFrame = $state({ left: '0px', top: '0px', width: '100%', height: '100%' });

	// Planes, back to front: 3 = animated sky, 2 = buildings, 1 = balustrade and floor; plants come on top.
	const planeOne = resolveGameAsset('assets/midnight-lounge/scene/background_1.png');
	const planeTwo = resolveGameAsset('assets/midnight-lounge/scene/background_2_static.png');
	const clips: SkyClip[] = [1, 2];
	const frames = Array.from({ length: SKY_FRAME_COUNT }, (_, i) => i);

	$effect(() => acquireSky());

	$effect(() => {
		const el = plate;
		if (!el) return;
		const viewport = el.closest('.skyjump-viewport');
		if (!(viewport instanceof HTMLElement)) return;
		const sync = () => {
			winFocus = viewport.hasAttribute('data-win-focus');
		};
		sync();
		const observer = new MutationObserver(sync);
		observer.observe(viewport, { attributes: true, attributeFilter: ['data-win-focus'] });
		return () => observer.disconnect();
	});

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

{#snippet scene(withPlants: boolean)}
	<div class="sky" style:--sky-fade="{SKY_CROSSFADE_MS}ms">
		{#each clips as clip}
			{#each frames as frame}
				<img
					class:on={frame === 0
						? skyState.clip === clip || skyState.fading === clip
						: skyState.clip === clip && skyState.frame === frame}
					class:first={frame === 0}
					class:align={clip === 1}
					src={skyFrameUrl(clip, frame)}
					alt=""
					draggable="false"
				/>
			{/each}
		{/each}
	</div>
	<img class="plane buildings" src={planeTwo} alt="" draggable="false" />
	<img class="plane" src={planeOne} alt="" draggable="false" />
	{#if withPlants}
		{#each SCENE_PLANTS as anchor, i}
			<LoopingProp
				prop="plant"
				{...propBox('plant', anchor)}
				flip={anchor.flip}
				delayMs={i * 2100}
				z={1}
				sharp
			/>
		{/each}
	{/if}
{/snippet}

{#if context.stateGame.screen === 'play'}
	<div class="plate" data-lounge-bg bind:this={plate}>
		<div
			class="scene"
			style:left={plateFrame.left}
			style:top={plateFrame.top}
			style:width={plateFrame.width}
			style:height={plateFrame.height}
		>
			{@render scene(true)}
		</div>
	</div>
	<!-- Same scene, lifted above the board while a celebration runs: fades in and out. -->
	<div
		class="win-plate scene"
		data-lounge-win-plate
		style:left={plateFrame.left}
		style:top={plateFrame.top}
		style:width={plateFrame.width}
		style:height={plateFrame.height}
	>
		{@render scene(winFocus)}
	</div>
	<LoungeCharacter character="bartender" />
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

	/* The scene is the play area; it is a size container so props can be placed in cqw / cqh. */
	.scene {
		position: absolute;
		container-type: size;
		overflow: hidden;
		pointer-events: none;
	}

	.sky,
	.plane,
	.sky img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: fill;
		pointer-events: none;
		user-select: none;
	}

	.sky img {
		opacity: 0;
	}

	.sky img.on {
		opacity: 1;
	}

	/* Buildings: raised so their lower line sits about two thirds up the 1280x720 window. */
	.plane.buildings {
		transform: translateY(-13%);
	}

	/*
	 * Clip 2 is the same sky framed 1.155x closer (registered against clip 1: scale 1.1555, anchored at
	 * the top-left corner). Clip 1 gets the same framing so switching clips never pops a zoom.
	 */
	.sky img.align {
		transform: scale(1.1555);
		transform-origin: 0 0;
	}

	/* A clip's first frame fades in (the two clips differ slightly); later frames cut instantly. */
	.sky img.first {
		transition: opacity var(--sky-fade) linear;
	}

	/*
	 * Celebration: the scene is lifted above the board (z 20) and fades in and out over 700 ms
	 * (V2_WIN_BLUR_FADE_MS) together with the HUD blur. `data-win-focus` outlives the celebration
	 * by the fade time, so the characters (z 30) never drop behind the fading plate.
	 */
	.win-plate {
		z-index: 20;
		opacity: 0;
		transition: opacity 700ms ease;
	}

	:global(.skyjump-viewport[data-win-plate]) .win-plate {
		opacity: 1;
	}
</style>
