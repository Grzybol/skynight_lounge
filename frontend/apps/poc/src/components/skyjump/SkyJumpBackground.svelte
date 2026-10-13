<script lang="ts">
	import { getContext } from '../../game/context';
	import { resolveGameAsset } from '../../game/resolveGameAsset';
	import { propBox } from '../../game/loungeCharacters/propLayout';
	import { SCENE_PLANTS } from '../../game/loungeCharacters/propLayout';
	import {
		acquireBuildings,
		BUILDINGS_FADE_MS,
		BUILDINGS_POOL,
		buildingsFilter,
		buildingsState,
	} from '../../game/loungeScene/buildingsPool.svelte';
	import LoungeCharacter from './LoungeCharacter.svelte';
	import LoopingProp from './LoopingProp.svelte';
	import ChimneySmoke from './ChimneySmoke.svelte';

	const context = getContext();
	let plate = $state<HTMLDivElement | null>(null);

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
	const planeTwoBase = BUILDINGS_POOL[0];
	const clouds = resolveGameAsset('assets/midnight-lounge/scene/clouds_prop.png');

	$effect(() => acquireBuildings());

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

{#snippet scene()}
	<img class="plane" src={planeThree} alt="" draggable="false" />
	<!-- Drifting clouds between the farthest sky and the houses, upper half only. -->
	<div class="clouds">
		{#each [0, 1, 2, 3, 4, 5] as n}
			<span class="tile" class:mirror={n % 2 === 1} style:background-image={`url(${clouds})`}></span>
		{/each}
	</div>
	<!-- Second plane: buildings and the smoke over their chimneys share one raised layer. -->
	<div class="buildings-layer">
		<!-- Always-visible base: whatever happens in the cross-fade, the houses never let the sky through. -->
		<img
			class="plane"
			src={planeTwoBase}
			style:filter={buildingsFilter(planeTwoBase)}
			alt=""
			draggable="false"
		/>
		<img
			class="plane fade"
			class:front={buildingsState.front === 'a'}
			style:--fade={`${BUILDINGS_FADE_MS}ms`}
			src={buildingsState.a}
			style:filter={buildingsFilter(buildingsState.a)}
			alt=""
			draggable="false"
		/>
		<img
			class="plane fade"
			class:front={buildingsState.front === 'b'}
			style:--fade={`${BUILDINGS_FADE_MS}ms`}
			src={buildingsState.b}
			style:filter={buildingsFilter(buildingsState.b)}
			alt=""
			draggable="false"
		/>
		{#each CHIMNEYS as chimney}
			<ChimneySmoke {...chimney} />
		{/each}
	</div>
	<img class="plane" src={planeOne} alt="" draggable="false" />
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
			{@render scene()}
		</div>
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
	/*
	 * Cross-fade without a see-through moment: the incoming image fades in on top (z 2) while the outgoing
	 * one stays opaque underneath and only switches off after the fade (delayed, instant).
	 */
	.plane.fade {
		z-index: 1;
		opacity: 0;
		transition: opacity 0s linear var(--fade);
	}

	.plane.fade.front {
		z-index: 2;
		opacity: 1;
		transition: opacity var(--fade) ease;
	}

	/*
	 * Clouds: a band raised above the top edge (lower edge at 26 cqh; the top part runs off the screen) (the planes above hide the rest). One tile
	 * is 243.6 cqh wide (band 42 cqh tall, 4200x724 art). Tiles alternate normal / mirrored, so every seam
	 * joins an image to its own mirror image and the loop never jumps; the strip drifts two tiles
	 * (694.4 cqh) per cycle, at half the earlier speed (480 s per tile).
	 */
	.clouds {
		position: absolute;
		left: 0;
		top: -16cqh;
		height: 42cqh;
		width: 1462cqh;
		display: flex;
		animation: clouds-drift 670s linear infinite;
		pointer-events: none;
	}

	.clouds .tile {
		flex: 0 0 243.6cqh;
		/* Overlap the neighbours by 0.8 cqh: every seam joins an image to its own mirror, so it stays continuous. */
		margin-left: -0.8cqh;
		height: 100%;
		background-size: 100% 100%;
		background-repeat: no-repeat;
	}

	.clouds .tile.mirror {
		transform: scaleX(-1);
	}

	@keyframes clouds-drift {
		to {
			transform: translateX(-485.6cqh);
		}
	}

	.buildings-layer {
		position: absolute;
		inset: 0;
		transform: translateY(-13%);
		pointer-events: none;
	}
</style>
