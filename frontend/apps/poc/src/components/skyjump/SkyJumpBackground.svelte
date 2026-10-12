<script lang="ts">
	import { getContext } from '../../game/context';
	import { resolveGameAsset } from '../../game/resolveGameAsset';
	import { propBox } from '../../game/loungeCharacters/propLayout';
	import { SCENE_PLANTS } from '../../game/loungeCharacters/propLayout';
	import {
		acquireBuildings,
		BUILDINGS_FADE_MS,
		buildingsState,
	} from '../../game/loungeScene/buildingsPool.svelte';
	import LoungeCharacter from './LoungeCharacter.svelte';
	import LoopingProp from './LoopingProp.svelte';
	import ChimneySmoke from './ChimneySmoke.svelte';

	const context = getContext();
	let plate = $state<HTMLDivElement | null>(null);
	/** True while a celebration (plus the plate's fade-out) runs: the lifted copy then also animates the plants. */
	let winFocus = $state(false);

	let plateFrame = $state({ left: '0px', top: '0px', width: '100%', height: '100%' });

	// Planes, back to front: 3 = static sky, 2 = buildings, 1 = balustrade and floor; plants come on top.
	const planeThree = resolveGameAsset('assets/midnight-lounge/scene/background_3_static.png');
	/** Smoke over some chimneys of the buildings: tops measured on background_2 (1672x941). */
	const CHIMNEYS = [
		{ x: 103, y: 300, h: 150 }, // left
		{ x: 665, y: 330, h: 140 }, // middle
		{ x: 1525, y: 312, h: 145 }, // right
	].map((c, i) => ({ x: c.x / 1672, y: c.y / 941, h: c.h / 941, phaseMs: i * 700 }));
	const planeOne = resolveGameAsset('assets/midnight-lounge/scene/background_1.png');
	const clouds = resolveGameAsset('assets/midnight-lounge/scene/clouds_prop.png');

	$effect(() => acquireBuildings());

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
	<img class="plane" src={planeThree} alt="" draggable="false" />
	<!-- Drifting clouds between the farthest sky and the houses, upper half only. -->
	<div class="clouds" style:background-image={`url(${clouds})`}></div>
	<!-- Second plane: buildings and the smoke over their chimneys share one raised layer. -->
	<div class="buildings-layer">
		<img
			class="plane fade"
			class:front={buildingsState.front === 'a'}
			style:--fade={`${BUILDINGS_FADE_MS}ms`}
			src={buildingsState.a}
			alt=""
			draggable="false"
		/>
		<img
			class="plane fade"
			class:front={buildingsState.front === 'b'}
			style:--fade={`${BUILDINGS_FADE_MS}ms`}
			src={buildingsState.b}
			alt=""
			draggable="false"
		/>
		{#each CHIMNEYS as chimney}
			<ChimneySmoke {...chimney} />
		{/each}
	</div>
	<img class="plane" src={planeOne} alt="" draggable="false" />
	{#if withPlants}
		{#each SCENE_PLANTS as anchor, i}
			<LoopingProp
				prop="plant"
				{...propBox('plant', anchor)}
				flip={anchor.flip}
				offsetMs={i * 2100}
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

	.plane {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: fill;
		pointer-events: none;
		user-select: none;
	}

	/* Buildings: raised so their lower line sits about two thirds up the 1280x720 window. */
	.plane.fade {
		opacity: 0;
		transition: opacity var(--fade) ease;
	}

	.plane.fade.front {
		opacity: 1;
	}

	/*
	 * Clouds: a band over the top of the scene (the lower half is hidden by the planes above anyway).
	 * One tile is 348 cqh wide (band 42 cqh tall, 6000x724 art), so the loop is seamless.
	 */
	.clouds {
		position: absolute;
		left: 0;
		right: 0;
		top: 4cqh;
		height: 42cqh;
		background-repeat: repeat-x;
		background-size: auto 100%;
		animation: clouds-drift 240s linear infinite;
		pointer-events: none;
	}

	@keyframes clouds-drift {
		to {
			background-position-x: -348cqh;
		}
	}

	.buildings-layer {
		position: absolute;
		inset: 0;
		transform: translateY(-13%);
		pointer-events: none;
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
