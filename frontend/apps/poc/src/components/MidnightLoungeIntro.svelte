<script lang="ts">
	import { onMount } from 'svelte';

	import { getContext } from '../game/context';
	import { resolveGameAsset } from '../game/resolveGameAsset';
	import { startSkyJumpBgm } from '../game/skyjump/skyjumpAudio';
	import {
		INTRO_GUARD,
		INTRO_PLANTS,
		INTRO_PLANT_TONE,
		INTRO_STANCHION,
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
	const stanchionBox = propBox('stanchion', INTRO_STANCHION);
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
		// 0.9 s in total: 0.45 s of growing blur over the start screen's background (the figures
		// fade out instead of blurring), 0.45 s of the blur clearing over the whole slot screen.
		veil = 'in';
		window.setTimeout(() => {
			// Fully blurred: drop the entrance so the blur clears over the slot.
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
			class:blur={veil !== 'off'}
			src={startSrc}
			alt=""
			draggable="false"
		/>
		<div class="props" class:gone={veil !== 'off'}>
		{#each INTRO_PLANTS as anchor, i}
			<LoopingProp
				prop="plant"
				{...propBox('plant', anchor)}
				flip={anchor.flip}
				delayMs={i * 2100}
				rate={0.5}
				z={1}
				sharp
				tone={INTRO_PLANT_TONE}
			/>
		{/each}
		<LoopingProp prop="guard" {...propBox('guard', INTRO_GUARD)} z={2} sharp />
		<img
			class="stanchion"
			src={stanchionSrc}
			alt=""
			draggable="false"
			style={`left:${stanchionBox.left};top:${stanchionBox.top};height:${stanchionBox.height};${INTRO_STANCHION.flip ? 'transform:scaleX(-1);' : ''}`}
		/>
		</div>
	</div>
	{#if ready}
		<button class="hit" type="button" aria-label="Click anywhere to continue" onclick={continueIn}>
			<img
				class="cta"
				class:in={ctaIn}
				class:idle={ctaIdle && !reduceMotion}
				class:gone={veil !== 'off'}
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
		/* Centred horizontally; vertically only 10 % of the crop is taken at the top (STAGE_TOP_SHARE). */
		left: calc((100cqw - max(100cqw, calc(100cqh * 1448 / 1086))) / 2);
		top: calc((100cqh - max(100cqh, calc(100cqw * 1086 / 1448))) * 0.1);
		container-type: size;
		pointer-events: none;
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

	.props {
		position: absolute;
		inset: 0;
		transition: opacity 450ms linear;
		pointer-events: none;
	}

	.props.gone {
		opacity: 0;
	}

	.stanchion {
		position: absolute;
		z-index: 3;
		width: auto;
		pointer-events: none;
		user-select: none;
	}

	/* Scaled so the blurred border never shows the black behind the artwork. */
	.entrance.in.blur,
	.entrance.blur {
		filter: blur(36px);
		opacity: 1;
		transform: scale(1.12);
		transition:
			filter 450ms linear,
			transform 450ms linear;
	}

	.lounge-intro .cta.gone {
		animation: none;
		opacity: 0;
		transition: opacity 300ms linear;
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

	/*
	 * Blur transition: a backdrop blur over everything below it. It reaches past the edges so the
	 * blurred border does not fade to transparent at the screen edge.
	 */
	.veil {
		position: absolute;
		inset: -80px;
		backdrop-filter: blur(0px);
		-webkit-backdrop-filter: blur(0px);
		pointer-events: none;
		transition:
			backdrop-filter 450ms linear,
			-webkit-backdrop-filter 450ms linear;
	}

	.veil.in {
		backdrop-filter: blur(36px);
		-webkit-backdrop-filter: blur(36px);
	}

	.veil.out {
		backdrop-filter: blur(0px);
		-webkit-backdrop-filter: blur(0px);
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
