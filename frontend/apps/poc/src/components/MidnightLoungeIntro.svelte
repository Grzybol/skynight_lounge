<script lang="ts">
	import { onMount } from 'svelte';

	import { getContext } from '../game/context';
	import { resolveGameAsset } from '../game/resolveGameAsset';
	import { startSkyJumpBgm } from '../game/skyjump/skyjumpAudio';
	import {
		INTRO_GUARD,
		INTRO_PLANTS,
		INTRO_STANCHIONS,
		propBox,
	} from '../game/loungeCharacters/propLayout';
	import LoopingProp from './skyjump/LoopingProp.svelte';

	type Props = {
		onunlock: () => void;
		ondone: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	const startSrc = resolveGameAsset('assets/midnight-lounge/ui/start_screen.png');
	const stanchionSrc = resolveGameAsset('assets/midnight-lounge/ui/intro_stanchion.png');
	const ctaSrc = resolveGameAsset(
		'assets/midnight-lounge/ui/ui_click_anywhere_to_continue_midnight_lounge.png',
	);

	const ready = $derived(context.stateApp.loaded);
	let reduceMotion = $state(false);
	let bgIn = $state(false);
	let ctaIn = $state(false);
	let ctaIdle = $state(false);
	let veil = $state<'off' | 'in' | 'hold' | 'out'>('off');
	let revealGame = $state(false);
	let locked = false;

	const continueIn = () => {
		if (!ready || locked || veil !== 'off') return;
		locked = true;
		ctaIdle = false;
		props.onunlock();
		startSkyJumpBgm();
		// 0.9 s in total: 0.45 s to black over the start screen, 0.45 s from black to the slot.
		veil = 'in';
		window.setTimeout(() => {
			// Fully black: drop the entrance so the fade reveals the slot.
			veil = 'hold';
			revealGame = true;
			window.setTimeout(() => {
				veil = 'out';
				window.setTimeout(() => props.ondone(), 450);
			}, 16);
		}, 450);
	};

	const onKey = (event: KeyboardEvent) => {
		if (event.key !== ' ' && event.key !== 'Enter') return;
		if (event.repeat) return;
		const target = event.target;
		if (target instanceof HTMLElement && target.closest('input, textarea, select')) return;
		event.preventDefault();
		continueIn();
	};

	onMount(() => {
		const ctaPreload = new Image();
		ctaPreload.src = ctaSrc;
		const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
		reduceMotion = motion.matches;
		const onMotion = () => {
			reduceMotion = motion.matches;
		};
		motion.addEventListener('change', onMotion);
		const frame = requestAnimationFrame(() => {
			bgIn = true;
		});
		window.addEventListener('keydown', onKey);
		return () => {
			cancelAnimationFrame(frame);
			motion.removeEventListener('change', onMotion);
			window.removeEventListener('keydown', onKey);
		};
	});

	$effect(() => {
		if (!ready || veil !== 'off') return;
		const timer = window.setTimeout(() => {
			ctaIn = true;
		}, 80);
		return () => window.clearTimeout(timer);
	});
</script>

<div class="lounge-intro" class:reduce={reduceMotion} class:reveal={revealGame} data-intro-phase={veil}>
	<!-- The artwork is 4:3: the stage covers the screen like object-fit: cover, props live in it. -->
	<div class="stage">
		<img
			class="entrance"
			class:in={bgIn}
			src={startSrc}
			alt=""
			draggable="false"
		/>
		{#each INTRO_PLANTS as anchor, i}
			<LoopingProp
				prop="plant"
				{...propBox('plant', anchor)}
				flip={anchor.flip}
				delayMs={i * 2100}
				rate={0.5}
				z={1}
			/>
		{/each}
		<LoopingProp prop="guard" {...propBox('guard', INTRO_GUARD)} z={2} />
		{#each INTRO_STANCHIONS as anchor, i}
			<img
				class="stanchion"
				src={stanchionSrc}
				alt=""
				draggable="false"
				style={`left:${propBox('stanchion', anchor).left};top:${propBox('stanchion', anchor).top};height:${propBox('stanchion', anchor).height};z-index:${i < 2 ? 2 : 3};${anchor.flip ? 'transform:scaleX(-1);' : ''}`}
			/>
		{/each}
	</div>
	{#if ready}
		<button class="hit" type="button" aria-label="Click anywhere to continue" onclick={continueIn}>
			<img
				class="cta"
				class:in={ctaIn}
				class:idle={ctaIdle && !reduceMotion}
				src={ctaSrc}
				alt=""
				draggable="false"
				onanimationend={() => (ctaIdle = true)}
			/>
		</button>
	{:else}
		<div class="loading" aria-hidden="true">
			<span>LOADING</span>
			<i></i>
		</div>
	{/if}
	<div class="veil" class:in={veil === 'in' || veil === 'hold'} class:out={veil === 'out'}></div>
</div>

<style>
	.lounge-intro {
		container-type: size;
		position: absolute;
		inset: 0;
		z-index: 40;
		overflow: hidden;
		background: #000;
	}

	.lounge-intro.reveal {
		background: transparent;
		pointer-events: none;
	}

	.lounge-intro.reveal .stage,
	.lounge-intro.reveal .hit,
	.lounge-intro.reveal .loading {
		visibility: hidden;
	}

	.stage {
		position: absolute;
		width: max(100cqw, calc(100cqh * 1448 / 1086));
		height: max(100cqh, calc(100cqw * 1086 / 1448));
		/* Centred horizontally; vertically only 20 % of the crop is taken at the top (STAGE_TOP_SHARE). */
		left: calc((100cqw - max(100cqw, calc(100cqh * 1448 / 1086))) / 2);
		top: calc((100cqh - max(100cqh, calc(100cqw * 1086 / 1448))) * 0.2);
		container-type: size;
		pointer-events: none;
	}

	.stanchion {
		/* Slightly soft, like the (upscaled) artwork behind it. */
		filter: blur(0.7px);
		position: absolute;
		width: auto;
		pointer-events: none;
		user-select: none;
	}

	.entrance {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		opacity: 0.92;
		transform: scale(1.01);
		transform-origin: center center;
		transition:
			opacity 700ms ease,
			transform 700ms ease;
		pointer-events: none;
		user-select: none;
	}

	.entrance.in {
		opacity: 1;
		transform: scale(1);
	}

	.hit {
		position: absolute;
		inset: 0;
		padding: 0;
		border: 0;
		background: transparent;
		cursor: pointer;
	}

	.cta {
		position: absolute;
		left: 50%;
		top: 77%;
		width: min(600px, calc(100% - 48px));
		height: auto;
		opacity: 0;
		transform: translate(-50%, -50%) translateY(8px);
		pointer-events: none;
		user-select: none;
	}

	.cta.in {
		animation: lounge-cta-in 420ms ease forwards;
	}

	.cta.idle {
		animation: lounge-cta-breathe 2.1s ease-in-out infinite;
	}

	.loading {
		position: absolute;
		left: 50%;
		bottom: 11%;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		transform: translateX(-50%);
		pointer-events: none;
	}

	.loading span {
		font-family: SkyjumpUI, sans-serif;
		font-size: 11px;
		letter-spacing: 0.28em;
		color: rgba(232, 196, 110, 0.85);
	}

	.loading i {
		display: block;
		width: 120px;
		height: 2px;
		border-radius: 2px;
		background: linear-gradient(90deg, transparent, #e8c46e, transparent);
		opacity: 0.85;
	}

	.veil {
		position: absolute;
		inset: 0;
		background: #000;
		opacity: 0;
		pointer-events: none;
		transition: opacity 450ms linear;
	}

	.veil.in {
		opacity: 1;
	}

	.veil.out {
		opacity: 0;
		transition-duration: 450ms;
	}

	.reduce .entrance,
	.reduce .entrance.in {
		transform: none;
		transition: opacity 200ms linear;
	}

	.reduce .cta.in {
		animation: lounge-cta-in-still 300ms linear forwards;
	}

	@keyframes lounge-cta-in {
		from {
			opacity: 0;
			transform: translate(-50%, -50%) translateY(8px);
		}
		to {
			opacity: 1;
			transform: translate(-50%, -50%) translateY(0);
		}
	}

	@keyframes lounge-cta-in-still {
		from {
			opacity: 0;
			transform: translate(-50%, -50%);
		}
		to {
			opacity: 1;
			transform: translate(-50%, -50%);
		}
	}

	@keyframes lounge-cta-breathe {
		0%,
		100% {
			opacity: 0.82;
			transform: translate(-50%, -50%) scale(0.99);
			filter: drop-shadow(0 0 8px rgba(212, 175, 90, 0.28));
		}
		50% {
			opacity: 1;
			transform: translate(-50%, -50%) scale(1.015);
			filter: drop-shadow(0 0 18px rgba(232, 196, 110, 0.55));
		}
	}
</style>
