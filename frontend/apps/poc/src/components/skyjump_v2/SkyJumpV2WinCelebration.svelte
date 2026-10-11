<script lang="ts">
	import { BOOK_AMOUNT_MULTIPLIER } from 'constants-shared/bet';
	import { bookEventAmountToCurrencyString } from 'utils-shared/amount';

	import { MARCELLUS_STACK } from '../../game/skyjump_v2/fonts';
	import {
		V2_WIN_TITLE_SLOT,
		v2WinTitleScale,
	} from '../../game/skyjump_v2/presentationLayout';
	import { v2FxAssetUrl, v2UiAssetUrl, v2WinSceneOverlayUrl } from '../../game/skyjump_v2/uiAssetRegistry';
	import { WIN_PRIORITY, type WinCategory } from '../../game/loungeCharacters/config';
	import { categoryForTier, categoryForWinX } from '../../game/loungeCharacters/loungeWinCue';
	import { reactToWin } from '../../game/loungeCharacters/winReaction';
	import {
		type V2WinCelebrationTier,
		V2_WIN_CELEBRATION_THRESHOLDS,
		v2WinCountUpMs,
		v2WinFxIntensity,
		v2WinHoldMs,
		v2WinTitleUrlForTier,
	} from '../../game/skyjump_v2/winPresentation';

	type Props = {
		show: boolean;
		tier: V2WinCelebrationTier;
		/** Authoritative payout figure — never inferred. */
		amount: number;
		turbo?: boolean;
		catchUp?: boolean;
		/** Also layer overlayWorldRecord behind the WR title art. */
		worldRecordOverlay?: boolean;
		/**
		 * The amount is a stake multiple. Default: shown as money (multiple x the wagered bet, the
		 * same figure as the WIN panel). `false` shows the multiple with a × sign.
		 */
		formatAsCurrency?: boolean;
		oncomplete?: () => void;
	};

	const props: Props = $props();

	const reducedMotion = () =>
		typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

	const fx = $derived(v2WinFxIntensity(props.tier));
	const titleSrc = $derived(v2WinTitleUrlForTier(props.tier));
	const sceneOverlaySrc = $derived(v2WinSceneOverlayUrl(props.tier));
	const titleScale = $derived(v2WinTitleScale(props.tier));
	const wrOverlaySrc = v2UiAssetUrl('overlayWorldRecord');
	const glowSrc = v2FxAssetUrl('winGlowRing');
	const snowSrc = v2FxAssetUrl('snowBurst');
	const sparkleSrc = v2FxAssetUrl('smallSparkle');
	const coinSrc = v2FxAssetUrl('coinSparkle');
	const flashSrc = v2FxAssetUrl('screenFlashAccent');
	const iceGlintSrc = v2FxAssetUrl('iceGlint');

	let displayValue = $state(0);
	let amountDone = $state(false);
	let gen = 0;
	let finishing = false;

	const formatAmount = (value: number) => {
		if (props.formatAsCurrency ?? true) {
			return bookEventAmountToCurrencyString(value * BOOK_AMOUNT_MULTIPLIER);
		}
		const rounded = Math.round(value * 100) / 100;
		if (Number.isInteger(rounded)) return `${rounded}×`;
		return `${rounded.toFixed(2).replace(/\.?0+$/, '')}×`;
	};

	/** Deterministic edge/arc particles — keep central title + amount readable. */
	const particles = $derived.by(() => {
		const n = fx.sparkles ? fx.particleBudget : 0;
		return Array.from({ length: n }, (_, i) => {
			const angle = ((i * 137.5) % 360) * (Math.PI / 180);
			const ring = 0.38 + ((i * 17) % 26) / 100;
			const cx = 50 + Math.cos(angle) * ring * 46;
			const cy = 46 + Math.sin(angle) * ring * 38;
			return {
				left: Math.max(5, Math.min(95, cx)),
				top: Math.max(8, Math.min(92, cy)),
				delay: (i * 37) % 420,
				scale: 0.42 + ((i * 19) % 48) / 100,
				rot: (i * 23) % 360,
			};
		});
	});

	const coinParticles = $derived.by(() => {
		if (!fx.coinSparkle) return [];
		const n = Math.min(7, Math.max(3, Math.floor(fx.particleBudget / 3)));
		return Array.from({ length: n }, (_, i) => {
			const side = i % 2 === 0 ? -1 : 1;
			return {
				left: 50 + side * (24 + ((i * 11) % 16)),
				top: 62 + ((i * 19) % 24),
				delay: 80 + ((i * 55) % 360),
				scale: 0.48 + ((i * 13) % 38) / 100,
			};
		});
	});

	/** Slight ease-out so the figure still lands softly but the tiers are crossed along the way. */
	const countEase = (t: number) => 1 - (1 - t) ** 1.4;

	/**
	 * The characters follow the counter: mini above the bet, big and mega at the presentation
	 * thresholds. They queue (a clip is never cut), so asking early is safe.
	 */
	let lastCategory: WinCategory | null = null;
	const announce = (x: number) => {
		const cat = categoryForWinX(x, V2_WIN_CELEBRATION_THRESHOLDS);
		if (!cat) return;
		if (lastCategory && WIN_PRIORITY[cat] <= WIN_PRIORITY[lastCategory]) return;
		lastCategory = cat;
		reactToWin(cat, props.tier, { turbo: props.turbo });
	};

	const finish = () => {
		if (finishing) return;
		finishing = true;
		displayValue = props.amount;
		amountDone = true;
		props.oncomplete?.();
	};

	const dismiss = () => {
		gen += 1;
		finish();
	};

	const amountLen = $derived(formatAmount(props.amount).length);
	const amountScale = $derived(
		amountLen > 13 ? 0.6 : amountLen > 11 ? 0.72 : amountLen > 9 ? 0.84 : amountLen > 7 ? 0.92 : 1,
	);

	$effect(() => {
		if (!props.show || props.tier === 'none') {
			displayValue = 0;
			amountDone = false;
			finishing = false;
			return;
		}

		const myGen = ++gen;
		finishing = false;
		amountDone = false;
		lastCategory = null;
		const amount = props.amount;
		const countMs = v2WinCountUpMs({
			tier: props.tier,
			turbo: props.turbo,
			catchUp: props.catchUp,
			reducedMotion: reducedMotion(),
		});

		let raf = 0;
		let holdTimer: ReturnType<typeof setTimeout> | undefined;

		const runHold = () => {
			amountDone = true;
			// The final figure always ends on the tier's own reaction (e.g. max / world record).
			const tierCategory = categoryForTier(props.tier);
			if (tierCategory && (!lastCategory || WIN_PRIORITY[tierCategory] > WIN_PRIORITY[lastCategory])) {
				lastCategory = tierCategory;
				reactToWin(tierCategory, props.tier, { turbo: props.turbo });
			}
			const ms = v2WinHoldMs({
				tier: props.tier,
				turbo: props.turbo,
				catchUp: props.catchUp,
				reducedMotion: reducedMotion(),
			});
			if (ms <= 0) {
				if (myGen === gen) finish();
				return;
			}
			holdTimer = setTimeout(() => {
				if (myGen === gen) finish();
			}, ms);
		};

		if (countMs <= 0) {
			displayValue = amount;
			announce(amount);
			runHold();
			return () => {
				if (holdTimer) clearTimeout(holdTimer);
			};
		}

		displayValue = 0;
		const start = performance.now();
		const tick = (now: number) => {
			if (myGen !== gen) return;
			const t = Math.min(1, (now - start) / countMs);
			displayValue = amount * countEase(t);
			announce(displayValue);
			if (t < 1) {
				raf = requestAnimationFrame(tick);
			} else {
				displayValue = amount;
				announce(amount);
				runHold();
			}
		};
		raf = requestAnimationFrame(tick);

		return () => {
			cancelAnimationFrame(raf);
			if (holdTimer) clearTimeout(holdTimer);
		};
	});
</script>

{#if props.show && props.tier !== 'none'}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="celebration"
		class:flash={fx.screenFlash}
		data-test="skyjump-v2-win-celebration"
		data-tier={props.tier}
		role="presentation"
		onclick={dismiss}
	>
		<div class="backdrop" aria-hidden="true"></div>
		{#if sceneOverlaySrc}
			<img class="win-plate" src={sceneOverlaySrc} alt="" draggable="false" />
		{/if}

		{#if fx.screenFlash}
			<img class="fx flash-accent" src={flashSrc} alt="" draggable="false" />
		{/if}

		{#if fx.glowRing}
			<div class="fx-wrap glow-wrap" aria-hidden="true">
				<img class="fx glow-ring" src={glowSrc} alt="" draggable="false" />
			</div>
		{/if}

		{#if fx.iceGlint}
			<div class="fx-wrap ice-wrap" aria-hidden="true">
				<img class="fx ice-glint" src={iceGlintSrc} alt="" draggable="false" />
			</div>
		{/if}

		{#if fx.snowBurst}
			<div class="fx-wrap snow-wrap" aria-hidden="true">
				<img class="fx snow-burst" src={snowSrc} alt="" draggable="false" />
			</div>
		{/if}

		{#each particles as p}
			<img
				class="fx sparkle"
				src={sparkleSrc}
				alt=""
				draggable="false"
				style:left={`${p.left}%`}
				style:top={`${p.top}%`}
				style:--delay={`${p.delay}ms`}
				style:--scale={p.scale}
				style:--rot={`${p.rot}deg`}
			/>
		{/each}

		{#each coinParticles as p}
			<img
				class="fx coin"
				src={coinSrc}
				alt=""
				draggable="false"
				style:left={`${p.left}%`}
				style:top={`${p.top}%`}
				style:--delay={`${p.delay}ms`}
				style:--scale={p.scale}
			/>
		{/each}

		<div class="stage">
			{#if props.worldRecordOverlay && props.tier === 'worldRecord' && !sceneOverlaySrc}
				<img class="wr-under" src={wrOverlaySrc} alt="" draggable="false" />
			{/if}
			{#if titleSrc}
				<div
					class="title-slot"
					style:--title-scale={titleScale}
					style:--title-slot-h={`${V2_WIN_TITLE_SLOT.slotHeight}px`}
					style:--title-slot-w={`${V2_WIN_TITLE_SLOT.maxWidth}px`}
				>
					<img class="win-title" src={titleSrc} alt="" draggable="false" />
				</div>
			{/if}
			<div class="amount-wrap" class:pulse={amountDone}>
				<p
					class="amount"
					class:pulse={amountDone}
					data-test="skyjump-v2-win-amount"
					style:font-family={MARCELLUS_STACK}
					style:--amount-scale={amountScale}
				>
					{formatAmount(displayValue)}
				</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.celebration {
		/* Leave bottom clear so Stake HUD stays readable under the stack. */
		position: absolute;
		inset: -4% -3% 10% -3%;
		z-index: 40;
		display: grid;
		place-items: center;
		align-content: center;
		pointer-events: auto;
		cursor: pointer;
	}

	.backdrop {
		position: absolute;
		inset: 0;
		background: radial-gradient(ellipse at 50% 42%, rgba(4, 18, 40, 0.5), rgba(2, 8, 20, 0.7));
		pointer-events: none;
	}

	.celebration[data-tier='big'] .backdrop,
	.celebration[data-tier='mega'] .backdrop {
		background: radial-gradient(ellipse at 50% 42%, rgba(28, 10, 16, 0.1), rgba(8, 4, 8, 0.2));
	}

	.win-plate {
		position: absolute;
		inset: 0;
		z-index: 1;
		width: 100%;
		height: 100%;
		object-fit: contain;
		object-position: center;
		pointer-events: none;
		/*
		 * The overlay art carries gold corner brackets that read as a slot frame. Feather its edges
		 * so the corners dissolve into the room instead of drawing a rectangle.
		 */
		-webkit-mask-image: radial-gradient(ellipse 58% 64% at 50% 50%, #000 38%, transparent 100%);
		mask-image: radial-gradient(ellipse 58% 64% at 50% 50%, #000 38%, transparent 100%);
	}

	.celebration[data-tier='big'] .win-plate,
	.celebration[data-tier='mega'] .win-plate {
		opacity: 0.46;
		mix-blend-mode: soft-light;
	}

	.fx,
	.fx-wrap {
		position: absolute;
		pointer-events: none;
		user-select: none;
	}

	.fx-wrap {
		display: grid;
		place-items: center;
		top: 42%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.glow-wrap {
		width: min(72%, 500px);
		height: min(72%, 500px);
	}

	.celebration[data-tier='big'] .glow-wrap {
		width: min(62%, 420px);
		height: min(62%, 420px);
	}

	.celebration[data-tier='worldRecord'] .glow-wrap {
		width: min(78%, 560px);
		height: min(78%, 560px);
	}

	.ice-wrap {
		width: min(48%, 340px);
		height: min(48%, 340px);
	}

	.snow-wrap {
		width: min(74%, 560px);
		height: min(74%, 560px);
	}

	.celebration[data-tier='big'] .snow-wrap {
		width: min(60%, 440px);
		height: min(60%, 440px);
	}

	.celebration[data-tier='worldRecord'] .snow-wrap {
		width: min(82%, 620px);
		height: min(82%, 620px);
	}

	.flash-accent {
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		opacity: 0.22;
		animation: flash-pop 380ms ease-out both;
		pointer-events: none;
	}

	.celebration[data-tier='max'] .flash-accent,
	.celebration[data-tier='worldRecord'] .flash-accent {
		opacity: 0.32;
	}

	.glow-ring,
	.ice-glint,
	.snow-burst {
		width: 100%;
		height: 100%;
		object-fit: contain;
		pointer-events: none;
	}

	.glow-ring {
		opacity: 0.75;
		animation: glow-pulse 1.6s ease-in-out infinite;
	}

	.celebration[data-tier='big'] .glow-ring {
		opacity: 0.52;
	}

	.celebration[data-tier='mega'] .glow-ring {
		opacity: 0.68;
	}

	.celebration[data-tier='super'] .glow-ring,
	.celebration[data-tier='max'] .glow-ring {
		opacity: 0.84;
	}

	.celebration[data-tier='worldRecord'] .glow-ring {
		opacity: 0.94;
	}

	.ice-glint {
		opacity: 0.62;
		animation: burst-in 480ms ease-out both;
	}

	.snow-burst {
		opacity: 0.78;
		animation: burst-in 520ms ease-out both;
	}

	.celebration[data-tier='big'] .snow-burst {
		opacity: 0.52;
	}

	.celebration[data-tier='worldRecord'] .snow-burst {
		opacity: 0.9;
	}

	.sparkle,
	.coin {
		width: 22px;
		height: 22px;
		object-fit: contain;
		transform: translate(-50%, -50%) scale(var(--scale, 1)) rotate(var(--rot, 0deg));
		animation: sparkle-pop 900ms ease-out both;
		animation-delay: var(--delay, 0ms);
		opacity: 0;
		pointer-events: none;
	}

	.coin {
		width: 26px;
		height: 26px;
		animation-duration: 1100ms;
	}

	.stage {
		position: relative;
		z-index: 2;
		display: grid;
		justify-items: center;
		align-content: start;
		gap: 0.35rem;
		/* Seat slightly above true center so HUD stays clear. */
		transform: translateY(-6%);
		pointer-events: none;
		width: min(86%, 520px);
		max-width: 520px;
		padding: 0 0.4rem;
		animation: stage-in 340ms cubic-bezier(0.22, 0.9, 0.32, 1) both;
	}

	.wr-under {
		position: absolute;
		top: 42%;
		left: 50%;
		width: min(96%, 500px);
		max-height: 180px;
		transform: translate(-50%, -50%);
		object-fit: contain;
		opacity: 0.42;
		pointer-events: none;
		z-index: 0;
	}

	.title-slot {
		position: relative;
		z-index: 1;
		box-sizing: border-box;
		display: grid;
		place-items: center;
		width: min(100%, var(--title-slot-w, 520px));
		height: var(--title-slot-h, 148px);
		pointer-events: none;
	}

	.win-title {
		display: block;
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		object-fit: contain;
		object-position: center;
		transform: scale(var(--title-scale, 1));
		transform-origin: center;
		filter: drop-shadow(0 10px 22px rgba(0, 8, 24, 0.55));
		pointer-events: none;
		animation: title-in 360ms cubic-bezier(0.22, 0.9, 0.32, 1) both;
	}

	.amount-wrap {
		position: relative;
		z-index: 1;
		display: grid;
		place-items: center;
		/* Clear of the title's lower flourish. */
		margin-top: clamp(0.9rem, 3.2vw, 1.9rem);
		width: max-content;
		max-width: 94vw;
	}

	/* Reddish glow behind the figure so it stands out from the room. */
	.amount-wrap::before {
		content: '';
		position: absolute;
		z-index: 0;
		inset: -42% -22%;
		background: radial-gradient(
			ellipse at center,
			rgba(226, 32, 56, 0.62) 0%,
			rgba(170, 14, 36, 0.4) 38%,
			rgba(110, 6, 24, 0.14) 62%,
			transparent 76%
		);
		filter: blur(10px);
		pointer-events: none;
	}

	.amount-wrap.pulse::before {
		animation: glow-breathe 900ms ease-in-out infinite alternate;
	}

	.amount {
		position: relative;
		z-index: 1;
		margin: 0;
		padding: 0 0.2em 0.08em;
		color: #ffc83a;
		background: linear-gradient(180deg, #fff3b8 0%, #ffd34f 34%, #f2a81f 68%, #c27a0e 100%);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		font-size: clamp(3.4rem, 9.2vw, 6.2rem);
		font-weight: 800;
		letter-spacing: 0.03em;
		line-height: 1.08;
		text-align: center;
		white-space: nowrap;
		transform: scale(var(--amount-scale, 1));
		transform-origin: center;
		filter: drop-shadow(0 3px 0 rgba(74, 20, 0, 0.9)) drop-shadow(0 10px 20px rgba(0, 0, 0, 0.55));
	}

	/* The 2 s after the count: the final figure keeps pulsing. */
	.amount.pulse {
		animation: amount-pulse 900ms ease-in-out infinite alternate;
	}

	.celebration.flash .backdrop {
		animation: flash-pop 380ms ease-out both;
	}

	@keyframes glow-pulse {
		0%,
		100% {
			opacity: 0.62;
			transform: scale(0.97);
		}
		50% {
			opacity: 0.9;
			transform: scale(1.02);
		}
	}

	@keyframes burst-in {
		from {
			opacity: 0;
			transform: scale(0.78);
		}
		to {
			opacity: 0.85;
			transform: scale(1);
		}
	}

	@keyframes sparkle-pop {
		0% {
			opacity: 0;
			transform: translate(-50%, -50%) scale(0.2) rotate(var(--rot, 0deg));
		}
		35% {
			opacity: 1;
		}
		100% {
			opacity: 0.55;
			transform: translate(-50%, -50%) scale(var(--scale, 1)) rotate(var(--rot, 0deg));
		}
	}

	@keyframes flash-pop {
		0% {
			opacity: 0.48;
		}
		100% {
			opacity: 0.08;
		}
	}

	@keyframes glow-breathe {
		from {
			opacity: 0.7;
			transform: scale(0.96);
		}
		to {
			opacity: 1;
			transform: scale(1.06);
		}
	}

	@keyframes amount-pulse {
		from {
			transform: scale(calc(var(--amount-scale, 1) * 0.96));
			filter: brightness(1) drop-shadow(0 3px 0 rgba(74, 36, 0, 0.9))
				drop-shadow(0 10px 20px rgba(0, 0, 0, 0.55));
		}
		to {
			transform: scale(calc(var(--amount-scale, 1) * 1.07));
			filter: brightness(1.18) drop-shadow(0 3px 0 rgba(74, 36, 0, 0.9))
				drop-shadow(0 10px 26px rgba(255, 190, 60, 0.55));
		}
	}

	@keyframes stage-in {
		from {
			opacity: 0;
			transform: translateY(-2%) scale(0.96);
		}
		to {
			opacity: 1;
			transform: translateY(-6%) scale(1);
		}
	}

	@keyframes title-in {
		from {
			opacity: 0;
			transform: scale(calc(var(--title-scale, 1) * 0.92));
		}
		to {
			opacity: 1;
			transform: scale(var(--title-scale, 1));
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.glow-ring,
		.snow-burst,
		.sparkle,
		.coin,
		.flash-accent,
		.celebration.flash .backdrop,
		.amount.pulse,
		.amount-wrap.pulse::before,
		.stage,
		.win-title {
			animation: none;
		}

		.sparkle,
		.coin {
			opacity: 0.7;
		}

		.stage {
			transform: translateY(-6%);
		}

		.win-title {
			transform: scale(var(--title-scale, 1));
		}
	}
</style>
