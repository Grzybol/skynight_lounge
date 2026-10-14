<script lang="ts">
	import { onMount } from 'svelte';

	import { getContext } from '../game/context';
	import { resolveGameAsset } from '../game/resolveGameAsset';
	import { startSkyJumpBgm } from '../game/skyjump/skyjumpAudio';
	import {
		INTRO_GUARD,
		INTRO_PLANTS,
			INTRO_STANCHION,
		propBox,
	} from '../game/loungeCharacters/propLayout';
	import { loungeLogoSrc } from '../game/midnightLoungeTheme';
	import { openWarmGate } from '../game/loungeCharacters/warmGate';
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

	const loadingSrc = resolveGameAsset('assets/midnight-lounge/ui/start_loading.png');
	const logoSrc = loungeLogoSrc;

	// The start screen is shown only when every piece of it is ready: background, stanchion, the
	// bodyguard and both plants (first frame on canvas) and the game itself. Until then a still of the
	// finished scene is shown, so the pieces never pop in one after another.
	const INTRO_PROPS = INTRO_PLANTS.length + 1;
	let bgLoaded = $state(false);
	let stanchionLoaded = $state(false);
	let propsReady = $state(0);
	const markReady = () => {
		propsReady += 1;
	};
	const gameLoaded = $derived(context.stateApp.loaded);
	const ready = $derived(gameLoaded && bgLoaded && stanchionLoaded && propsReady >= INTRO_PROPS);
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
		// The player is in: the rest of the downloads (variations, symbols, tiles) may start now.
		openWarmGate();
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
			onload={() => (bgLoaded = true)}
		/>
		<div class="props" class:gone={veil !== 'off'}>
		{#each INTRO_PLANTS as anchor, i}
			<LoopingProp
				prop="plant"
				{...propBox('plant', anchor)}
				flip={anchor.flip}
				offsetMs={i * 2100}
				onready={markReady}
				z={1}
				sharp
			/>
		{/each}
		<LoopingProp prop="guard" {...propBox('guard', INTRO_GUARD)} z={2} sharp onready={markReady} />
		<img
			class="stanchion"
			src={stanchionSrc}
			alt=""
			draggable="false"
			onload={() => (stanchionLoaded = true)}
			style={`left:${stanchionBox.left};top:${stanchionBox.top};height:${stanchionBox.height};${INTRO_STANCHION.flip ? 'transform:scaleX(-1);' : ''}`}
		/>
		</div>
	</div>
	<img class="logo" class:gone={veil !== 'off'} src={logoSrc} alt="SKYNIGHT LOUNGE" draggable="false" />
	<img class="placeholder" class:hide={ready} src={loadingSrc} alt="" draggable="false" />
	{#if ready}
		<button class="hit" type="button" aria-label="Click anywhere to continue" onclick={continueIn}>
			<span
				class="cta"
				class:in={ctaIn}
				class:idle={ctaIdle && !reduceMotion}
				class:gone={veil !== 'off'}
				aria-hidden="true"
				onanimationend={() => (ctaIdle = true)}>CLICK ANYWHERE TO CONTINUE</span
			>
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
		/* Own stacking context: the figures always stay under the CTA button. */
		isolation: isolate;
		z-index: 0;
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

	/* Still of the finished scene, covering the screen until every piece is ready. */
	.placeholder {
		position: absolute;
		inset: 0;
		z-index: 4;
		width: 100%;
		height: 100%;
		object-fit: cover;
		/* The still is framed ~5 % wider than the live start screen: zoom in from the top-left corner to match. */
		transform: scale(1.05);
		transform-origin: 0 0;
		pointer-events: none;
		user-select: none;
		transition: opacity 350ms ease;
	}

	.placeholder.hide {
		opacity: 0;
	}

	/* Same place and size as the brand logo in the slot screen (169 px at 1280 wide). */
	.logo {
		position: absolute;
		z-index: 6;
		top: 0.85rem;
		right: 1rem;
		width: 13.2cqw;
		height: auto;
		filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.42));
		pointer-events: none;
		user-select: none;
		transition: opacity 300ms linear;
	}

	.logo.gone {
		opacity: 0;
	}

	.hit {
		position: absolute;
		z-index: 5;
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
		width: max-content;
		max-width: calc(100% - 48px);
		color: #fff;
		font-family: var(--ml-font-gold, 'Luckiest Guy', serif);
		font-size: clamp(22px, 3.3vw, 44px);
		letter-spacing: 0.05em;
		line-height: 1.1;
		text-align: center;
		white-space: nowrap;
		/* White lettering with a black outline. */
		-webkit-text-stroke: 0.11em #000;
		paint-order: stroke fill;
		text-shadow: 0 0.06em 0 #000;
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
		z-index: 7;
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

	/* Idle: the text floats a few pixels up and down. */
	@keyframes lounge-cta-breathe {
		0%,
		100% {
			opacity: 1;
			transform: translate(-50%, -50%) translateY(-6px);
		}
		50% {
			opacity: 1;
			transform: translate(-50%, -50%) translateY(6px);
		}
	}
</style>
