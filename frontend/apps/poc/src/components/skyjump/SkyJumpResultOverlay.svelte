<script lang="ts">
	import { waitForTimeout } from 'utils-shared/wait';
	import { bookEventAmountToCurrencyString } from 'utils-shared/amount';
	import { OnHotkey } from 'components-shared';
	import { stateBet } from 'state-shared';

	import { getContext } from '../../game/context';
	import { stateXstateDerived } from '../../game/stateXstate';
	import { resultArtSrc, resultArtTier } from './skyjumpArt';
	import { SKYJUMP_SFX } from '../../game/skyjump/audio';
	import { stopSkyJumpRoundAudio } from '../../game/skyjump/skyjumpAudio';
	import { paylineDistance, SLOT_ROLES } from '../../game/skyjump/config';
	import { slotHeatFor } from '../../game/skyjump/slotHeat';
	import { payoutCountDurationMs } from '../../game/skyjump/timings';
	import { t } from '../../game/skyjump/copy';
	import type { BookEventOfType } from '../../game/typesBookEvent';
	import type { HillId, TimingProfile } from '../../game/skyjump/types';

	const context = getContext();

	let open = $state(false);
	let phase = $state<'intro' | 'factors' | 'distance' | 'local' | 'final' | 'payout'>('intro');
	let result = $state<Extract<BookEventOfType<'skyjumpResult'>, { distanceTotal: number }> | null>(
		null,
	);
	let weather = $state<BookEventOfType<'skyjumpWeather'>['weather'] | null>(null);
	let shownDistance = $state(0);
	let shownBase = $state(0);
	let shownAmount = $state(0);
	let shownDelta = $state(0);
	let shownTemp = $state(0);
	let shownWind = $state(0);
	let shownVis = $state(0);
	let shownSlotDeltas = $state<number[]>([]);
	let factorCount = $state(0);
	let countingPayout = $state(false);
	let awaitingContinue = $state(false);
	let overlayGen = 0;
	let continueResolver: (() => void) | null = null;

	const resolveContinue = () => {
		const resolve = continueResolver;
		continueResolver = null;
		awaitingContinue = false;
		if (resolve) {
			resolve();
			return;
		}
		overlayGen += 1;
		open = false;
	};

	const waitForNextBet = (ms: number | null, live: () => boolean) =>
		new Promise<void>((resolve) => {
			if (!live()) {
				resolve();
				return;
			}
			awaitingContinue = true;
			let timer: number | undefined;
			if (ms != null) {
				timer = window.setTimeout(() => {
					if (continueResolver) resolveContinue();
				}, ms);
			}
			continueResolver = () => {
				if (timer != null) window.clearTimeout(timer);
				resolve();
			};
		});

	const easeOut = (t: number) => 1 - (1 - t) * (1 - t);
	const overlayLive = (gen: number) => gen === overlayGen;

	const animateTo = async (
		from: number,
		to: number,
		duration: number,
		onUpdate: (value: number) => void,
		easing = (t: number) => t,
		live: () => boolean = () => true,
	) => {
		if (duration <= 0) {
			if (live()) onUpdate(to);
			return;
		}
		const start = performance.now();
		await new Promise<void>((resolve) => {
			const tick = (now: number) => {
				if (!live()) {
					resolve();
					return;
				}
				const t = Math.min(1, (now - start) / duration);
				onUpdate(from + (to - from) * easing(t));
				if (t < 1) requestAnimationFrame(tick);
				else resolve();
			};
			requestAnimationFrame(tick);
		});
	};

	const formatDeltaM = (value: number) => {
		const rounded = Math.round(value * 100) / 100;
		const text = Number.isInteger(rounded) ? `${rounded}` : rounded.toFixed(2).replace(/0+$/, '');
		return `${rounded > 0 ? '+' : ''}${text} m`;
	};
	const formatWind = (value: number) => `${(Math.round(value * 10) / 10).toFixed(1)} m/s`;

	const playOverlay = async (
		payload: BookEventOfType<'skyjumpResult'>,
		timings: TimingProfile,
		catchUp = false,
		weatherRoll: BookEventOfType<'skyjumpWeather'>['weather'] | null = null,
	) => {
		const gen = ++overlayGen;
		const live = () => overlayLive(gen);
		weather =
			weatherRoll ??
			(context.stateGame.lastWeather
				? {
						id: context.stateGame.lastWeather
							.id as BookEventOfType<'skyjumpWeather'>['weather']['id'],
						label: context.stateGame.lastWeather.label,
						iconKey: context.stateGame.lastWeather.iconKey,
						temperatureC: context.stateGame.lastWeather.temperatureC,
						windSpeedMs: context.stateGame.lastWeather.windSpeedMs,
						windDirection: context.stateGame.lastWeather.windDirection,
						visibilityPct: context.stateGame.lastWeather.visibilityPct,
						distanceDelta: context.stateGame.lastWeather.distanceDelta ?? 0,
					}
				: null);
		shownDistance = 0;
		shownBase = 0;
		shownAmount = 0;
		shownDelta = 0;
		shownTemp = 0;
		shownWind = 0;
		shownVis = 0;
		shownSlotDeltas = (payload.slots ?? []).slice(0, 5).map(() => 0);
		factorCount = 0;
		countingPayout = false;
		awaitingContinue = false;
		continueResolver = null;
		result = payload;
		phase = 'factors';
		open = true;
		stateBet.overlayOpen = true;
		stateBet.isSpaceHold = false;
		shownBase = payload.baseWinX;
		const below = payload.distanceTotal < paylineDistance((payload.hillId as HillId) ?? 'normal');
		if (below && !catchUp) {
			shownDistance = payload.distanceTotal;
			shownAmount = payload.amount;
			factorCount = 0;
			phase = 'payout';
			await waitForTimeout(Math.min(420, timings.overlayIntroMs + 180));
			if (!live()) return;
			let holdMs = timings.finalWinHoldMs;
			let auto = false;
			try {
				auto = stateXstateDerived.isAutoBetting();
			} catch {
				auto = false;
			}
			if (auto) holdMs = Math.min(420, holdMs);
			if (auto) {
				await waitForNextBet(holdMs, live);
			} else {
				await waitForNextBet(null, live);
			}
			if (live()) {
				stopSkyJumpRoundAudio();
				open = false;
			}
			return;
		}
		if (catchUp) {
			shownDistance = payload.distanceTotal;
			shownBase = payload.baseWinX;
			shownAmount = payload.amount;
			shownDelta = weather?.distanceDelta ?? 0;
			shownTemp = weather?.temperatureC ?? 0;
			shownWind = weather?.windSpeedMs ?? 0;
			shownVis = weather?.visibilityPct ?? 0;
			shownSlotDeltas = (payload.slots ?? []).slice(0, 5).map((slot) => slot.distanceValue);
			factorCount = 99;
			phase = 'payout';
			await waitForTimeout(Math.min(180, timings.finalWinHoldMs));
			if (live()) open = false;
			return;
		}
		await waitForTimeout(timings.overlayIntroMs);
		if (!live()) return;
		const stepHold = timings.id === 'turbo' ? Math.max(40, timings.weatherStatsMs) : 220;
		const stepCount = timings.id === 'turbo' ? 90 : 200;
		const bump = async () => {
			factorCount += 1;
			await waitForTimeout(stepHold);
		};
		if (weather) {
			await bump();
			if (!live()) return;
			await bump();
			if (!live()) return;
			await animateTo(
				0,
				weather.distanceDelta ?? 0,
				stepCount,
				(value) => (shownDelta = value),
				easeOut,
				live,
			);
			if (!live()) return;
			await bump();
			if (!live()) return;
			await animateTo(
				0,
				weather.temperatureC,
				stepCount,
				(value) => (shownTemp = value),
				easeOut,
				live,
			);
			if (!live()) return;
			await bump();
			if (!live()) return;
			await bump();
			if (!live()) return;
			await animateTo(
				0,
				weather.windSpeedMs,
				stepCount,
				(value) => (shownWind = value),
				easeOut,
				live,
			);
			if (!live()) return;
			await bump();
			if (!live()) return;
			await animateTo(
				0,
				weather.visibilityPct,
				stepCount,
				(value) => (shownVis = value),
				easeOut,
				live,
			);
			if (!live()) return;
		} else {
			factorCount = 6;
		}
		const slotRows = (payload.slots ?? []).slice(0, 5);
		for (let i = 0; i < slotRows.length; i += 1) {
			if (!live()) return;
			await bump();
			if (!live()) return;
			await animateTo(
				0,
				slotRows[i].distanceValue,
				stepCount,
				(value) => {
					shownSlotDeltas = shownSlotDeltas.map((current, index) =>
						index === i ? value : current,
					);
				},
				easeOut,
				live,
			);
			if (!live()) return;
		}
		phase = 'distance';
		shownBase = payload.baseWinX;
		const brakeAt = 0.75 + Math.random() * 0.15;
		const fastTarget = payload.distanceTotal * brakeAt;
		await animateTo(
			0,
			fastTarget,
			timings.countUpFastMs,
			(value) => (shownDistance = value),
			undefined,
			live,
		);
		if (!live()) return;
		await animateTo(
			fastTarget,
			payload.distanceTotal,
			timings.countUpSlowMs,
			(value) => (shownDistance = value),
			easeOut,
			live,
		);
		if (!live()) return;
		if (payload.localMultiplier > 1) {
			phase = 'local';
			await waitForTimeout(timings.localMultHoldMs);
		}
		if (!live()) return;
		phase = 'final';
		context.eventEmitter.broadcast({
			type: 'soundOnce',
			name: SKYJUMP_SFX.slot6Land,
			forcePlay: true,
		});
		await waitForTimeout(timings.finalMultHoldMs);
		if (!live()) return;
		phase = 'payout';
		countingPayout = true;
		await animateTo(
			0,
			payload.amount,
			payoutCountDurationMs(payload, timings),
			(value) => (shownAmount = value),
			easeOut,
			live,
		);
		if (live()) countingPayout = false;
		if (!live()) return;
		let holdMs = timings.finalWinHoldMs;
		let auto = false;
		try {
			auto = stateXstateDerived.isAutoBetting();
		} catch {
			auto = false;
		}
		if (auto) holdMs = Math.min(420, holdMs);
		if (auto) {
			await waitForNextBet(holdMs, live);
		} else {
			await waitForNextBet(null, live);
		}
		if (live()) {
			stopSkyJumpRoundAudio();
			open = false;
		}
	};

	context.eventEmitter.subscribeOnMount({
		skyjumpOverlayShow: async ({ result: payload, weather: weatherRoll, timings, catchUp }) => {
			await playOverlay(payload, timings, catchUp, weatherRoll ?? null);
		},
		skyjumpResetBoard: () => {
			overlayGen += 1;
			open = false;
			result = null;
			countingPayout = false;
			stopSkyJumpRoundAudio();
			resolveContinue();
		},
	});

	const localSources = $derived((result?.slots ?? []).filter((slot) => slot.localMultiplier > 1));
	const cost = $derived(result?.costMultiplier ?? 1);
	const isBuyMode = $derived(cost > 1);
	const celebrationTier = $derived(result ? resultArtTier(result) : 'tooShort');
	const resultArt = $derived(resultArtSrc[celebrationTier]);
	const payoutLabel = $derived.by(() => {
		if (!result) return 'PAYOUT';
		if (isBuyMode && result.isPayHit && !result.isBreakEven) return 'PAYOUT';
		if (result.isPayHit) return 'FINAL WIN';
		return 'PAYOUT';
	});
	const localLabel = $derived.by(() => {
		if (!result || result.localMultiplier <= 1) return '';
		const factors = result.localFactors?.length
			? result.localFactors
			: localSources.map((slot) => slot.localMultiplier);
		if (!factors.length) return `x${result.localMultiplier}`;
		if (factors.length === 1) return `x${factors[0]}`;
		return `${factors.map((value) => `x${value}`).join(' × ')} = x${result.localMultiplier}`;
	});
	const economicClass = $derived(
		result?.isProfit ? 'profit' : result?.isPayHit ? 'partial' : 'zero',
	);
	const hasBasePayout = $derived((result?.baseWinX ?? 0) > 0);
	const payline = $derived(result ? paylineDistance(result.hillId as HillId) : 0);
	const belowPayline = $derived(!!result && result.distanceTotal < payline);
	const dash = '—';
	const filled = (ready: boolean, value: string) => (ready ? value : dash);
	const kicker = $derived(phase === 'factors' ? t('JUMP FACTORS') : t('FLIGHT DISTANCE'));
	const distanceReady = $derived(phase !== 'intro' && phase !== 'factors');
	const payoutReady = $derived(phase === 'payout');
	const finalReady = $derived(phase === 'final' || phase === 'payout');
	const localReady = $derived(phase === 'local' || phase === 'final' || phase === 'payout');
	const showContinue = $derived(payoutReady && !countingPayout && open);
	const distanceSlots = $derived((result?.slots ?? []).slice(0, 5));
	let jumperFailed = $state(false);

	$effect(() => {
		resultArt;
		jumperFailed = false;
		const preload = new Image();
		preload.src = resultArt;
	});
</script>

{#if open && result}
	<div class="overlay {economicClass} {celebrationTier}">
		<article class:miss-card={belowPayline}>
			{#if !belowPayline}
				<div class="art" aria-hidden="true">
					{#if !jumperFailed}
						<img
							class="art-glow"
							src={resultArt}
							alt=""
							decoding="async"
							onerror={() => (jumperFailed = true)}
						/>
						<img class="art-main" src={resultArt} alt="" decoding="async" />
					{/if}
				</div>
			{/if}
			<p class="kicker">{belowPayline ? t('BELOW PAYLINE') : kicker}</p>
			{#if !belowPayline}
				<h2>{filled(distanceReady, `${shownDistance.toFixed(1)} m`)}</h2>
			{/if}
			<p class="payline">
				{t('PAYLINE')}
				{payline} m · {belowPayline ? t('BELOW PAYLINE') : t('QUALIFIED')}
			</p>
			{#if belowPayline}
				<div class="below-banner on">{t('BELOW PAYLINE')}</div>
			{/if}
			{#if !belowPayline}
				<div class="factors">
					<div>
						<span>{t('CONDITIONS')}</span>
						<strong
							>{filled(factorCount >= 1 && !!weather, weather ? t(weather.label) : dash)}</strong
						>
					</div>
					<div
						class:hot={factorCount >= 2 && shownDelta > 0}
						class:miss={factorCount >= 2 && shownDelta < 0}
					>
						<span>{t('WEATHER METRES')}</span>
						<strong>{filled(factorCount >= 2, formatDeltaM(shownDelta))}</strong>
					</div>
					<div>
						<span>{t('TEMPERATURE')}</span>
						<strong>{filled(factorCount >= 3, `${shownTemp.toFixed(1)}°C`)}</strong>
					</div>
					<div>
						<span>{t('WIND DIRECTION')}</span>
						<strong
							>{filled(
								factorCount >= 4 && !!weather,
								weather ? t(weather.windDirection) : dash,
							)}</strong
						>
					</div>
					<div>
						<span>{t('WIND SPEED')}</span>
						<strong>{filled(factorCount >= 5, formatWind(shownWind))}</strong>
					</div>
					<div>
						<span>{t('VISIBILITY')}</span>
						<strong>{filled(factorCount >= 6, `${Math.round(shownVis)}%`)}</strong>
					</div>
					{#each SLOT_ROLES.slice(0, 5) as role, index}
						{@const slot = distanceSlots[index]}
						{@const heat = slot
							? slotHeatFor(index, slot.distanceValue, slot.localMultiplier)
							: { id: '', pulse: 0 }}
						{@const slotReady = factorCount >= 7 + index && !!slot}
						<div
							class="slot-row {slotReady ? heat.id : ''}"
							class:pulse={slotReady && heat.pulse > 0}
						>
							<span>{t(role.shortLabel)}</span>
							<strong>
								{filled(
									slotReady,
									`${(shownSlotDeltas[index] ?? 0) > 0 ? '+' : ''}${(shownSlotDeltas[index] ?? 0).toFixed(0)} m`,
								)}
							</strong>
						</div>
					{/each}
				</div>
			{/if}
			<div class="lines">
				{#if belowPayline}
					<p class="miss-note on">{t('NO BASE PAYOUT')}</p>
				{:else if hasBasePayout}
					<div>
						<span>{t('BASE PAYOUT')}</span>
						<strong>{`${result.baseWinX.toFixed(2)}x`}</strong>
					</div>
				{:else}
					<div class="miss">
						<span>{t('BASE PAYOUT')}</span>
						<strong>—</strong>
					</div>
					<p class="miss-note on">{t('NO BASE PAYOUT')}</p>
				{/if}
				{#if !belowPayline}
					<div
						class="final"
						class:celebrate={finalReady && result.isProfit}
						class:miss={result.finalMultiplier <= 0}
					>
						<span>{t('Final Jump Multiplier')}</span>
						<strong
							>{filled(
								finalReady,
								`x${Math.round(result.localMultiplier * result.finalMultiplier * 100) / 100}`,
							)}</strong
						>
					</div>
				{/if}
				{#if !belowPayline}
					<div
						class="payout"
						class:celebrate={payoutReady && result.isProfit}
						class:soft={payoutReady && (celebrationTier === 'big' || celebrationTier === 'mega')}
						class:counting={countingPayout}
						class:hit={payoutReady && result.isPayHit}
					>
						<span>{payoutLabel}</span>
						<strong>{filled(payoutReady, bookEventAmountToCurrencyString(shownAmount))}</strong>
					</div>
				{/if}
				{#if !belowPayline && isBuyMode}
					<p class="return on">
						{result.isBreakEven ? 'RETURN' : 'RETURN VS BET'}
						{(result.returnMultiplier ?? 0).toFixed(2)}x
					</p>
				{/if}
				<p
					class="verdict"
					class:mega={celebrationTier === 'mega'}
					class:big={celebrationTier === 'big'}
					class:profit={result.isProfit && celebrationTier !== 'mega' && celebrationTier !== 'big'}
				>
					{#if belowPayline}
						{t('BELOW PAYLINE')}
					{:else if celebrationTier === 'mega'}
						MEGA WIN
					{:else if celebrationTier === 'big'}
						BIG WIN
					{:else if result.isProfit}
						PROFIT
					{:else if result.isPayHit}
						NO BIG WIN
					{:else}
						TOO SHORT
					{/if}
				</p>
			</div>
			{#if result.isCapped || result.capped}
				<p class="cap on">MAX WIN CAPPED AT {result.maxWin}x</p>
			{/if}
			<button
				class="next-bet"
				class:ready={showContinue}
				type="button"
				disabled={!showContinue}
				onclick={resolveContinue}
			>
				{t('NEXT JUMP')}
				<small>SPACE</small>
			</button>
		</article>
	</div>
	<OnHotkey
		hotkey="Space"
		disabled={!showContinue}
		onpress={() => {
			if (showContinue) resolveContinue();
		}}
	/>
{/if}

<style>
	.overlay {
		position: absolute;
		inset: 0;
		z-index: 80;
		display: grid;
		justify-items: center;
		align-content: center;
		align-items: center;
		padding: 7vh 0.75rem 16vh;
		background: rgba(7, 21, 38, 0.28);
		pointer-events: auto;
	}

	.overlay.profit {
		background: rgba(7, 21, 38, 0.12);
	}

	article {
		position: relative;
		z-index: 1;
		align-self: start;
		width: min(68vw, 1040px);
		max-height: none;
		overflow: hidden;
		isolation: isolate;
		padding: 2.7rem 1.55rem 1.35rem;
		color: #f4faff;
		text-align: center;
		background: rgba(5, 22, 43, 0.92);
		border: 2px solid rgba(101, 200, 255, 0.55);
		border-radius: 22px;
		box-shadow: 0 18px 48px rgba(3, 14, 29, 0.4);
	}

	article.miss-card {
		padding-top: 1.4rem;
	}

	.profit article {
		border-color: #ffc940;
	}

	.zero article {
		border-color: rgba(255, 201, 64, 0.55);
	}

	.art {
		position: absolute;
		z-index: 0;
		inset: -18%;
		overflow: hidden;
		pointer-events: none;
	}

	.art::after {
		content: '';
		position: absolute;
		inset: 12%;
		background:
			radial-gradient(
				ellipse 58% 48% at 50% 30%,
				rgba(8, 22, 42, 0.08) 0%,
				rgba(8, 22, 42, 0.42) 42%,
				rgba(5, 22, 43, 0.88) 74%,
				rgba(5, 22, 43, 1) 100%
			),
			linear-gradient(
				180deg,
				rgba(5, 22, 43, 0.18) 0%,
				rgba(5, 22, 43, 0.55) 38%,
				rgba(5, 22, 43, 0.96) 100%
			);
		pointer-events: none;
	}

	.art img {
		position: absolute;
		left: 50%;
		top: 8%;
		display: block;
		width: 128%;
		height: 108%;
		max-width: none;
		transform: translateX(-50%);
		object-fit: cover;
		object-position: center 22%;
	}

	.art-glow {
		width: 150%;
		height: 130%;
		top: -6%;
		filter: blur(56px) saturate(1.18);
		opacity: 0.42;
	}

	.art-main {
		opacity: 0.82;
		filter: blur(2px);
		-webkit-mask-image: radial-gradient(
			ellipse 50% 46% at 50% 32%,
			#000 8%,
			rgba(0, 0, 0, 0.55) 38%,
			transparent 74%
		);
		mask-image: radial-gradient(
			ellipse 50% 46% at 50% 32%,
			#000 8%,
			rgba(0, 0, 0, 0.55) 38%,
			transparent 74%
		);
	}

	.kicker,
	h2,
	.payline,
	.below-banner,
	.factors,
	.lines,
	.cap,
	.next-bet {
		position: relative;
		z-index: 1;
	}

	.kicker {
		margin: 0;
		min-height: 1.1em;
		color: #9bb4c8;
		letter-spacing: 0.16em;
		font-size: 0.72rem;
		font-weight: 800;
	}

	.payline {
		margin: -0.25rem 0 0.55rem;
		min-height: 1.1em;
		color: #9bb4c8;
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.1em;
	}

	.below-banner {
		margin: 0 auto 0.7rem;
		padding: 0.45rem 1.1rem;
		width: fit-content;
		min-height: 2.4rem;
		color: #ffe083;
		background: rgba(108, 75, 0, 0.45);
		border: 2px solid #ffc940;
		border-radius: 999px;
		font-size: clamp(16px, 2.2vw, 28px);
		font-weight: 900;
		letter-spacing: 0.14em;
		visibility: hidden;
	}

	.below-banner.on {
		visibility: visible;
		animation: below-pulse 1.1s ease-in-out infinite;
	}

	h2 {
		margin: 0.1rem 0 0.55rem;
		min-height: 1.15em;
		font-size: clamp(1.9rem, 5vw, 2.8rem);
		font-variant-numeric: tabular-nums;
	}

	.lines {
		display: grid;
		gap: 0.42rem;
	}

	.factors {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.22rem;
		margin: 0 0 0.7rem;
	}

	.factors > div:first-child {
		grid-column: 1 / -1;
	}

	.factors div {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.5rem;
		min-height: 2.05rem;
		padding: 0.28rem 0.55rem;
		border-radius: 10px;
		background: rgba(7, 24, 46, 0.88);
		font-size: 0.78rem;
	}

	.factors span {
		color: #9bb4c8;
		letter-spacing: 0.08em;
		font-weight: 800;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.factors strong {
		font-size: 0.92rem;
		white-space: nowrap;
	}

	.local-x {
		display: inline-block;
		margin-left: 0.35rem;
		padding: 0.08rem 0.42rem;
		border-radius: 999px;
		color: #07182f;
		background: #ffc940;
		font-size: 1.05rem;
		font-style: normal;
		font-weight: 900;
		letter-spacing: 0.04em;
		animation: badge-pulse 0.72s ease-in-out infinite;
	}

	.slot-row.neg-hi strong {
		color: #ff6b6b;
	}

	.slot-row.neg-mid strong {
		color: #ff8a5b;
	}

	.slot-row.neg-lo strong {
		color: #ffc940;
	}

	.slot-row.pos-mid strong {
		color: #65c8ff;
	}

	.slot-row.pos-hi strong {
		color: #7cffb2;
	}

	.slot-row.pos-max strong {
		color: #ffe083;
	}

	.slot-row.pulse {
		animation: factor-pulse 1.05s ease-in-out infinite;
	}

	.slot-row.pos-hi.pulse,
	.slot-row.neg-hi.pulse {
		animation-duration: 0.8s;
	}

	.slot-row.pos-max.pulse {
		animation-duration: 0.55s;
	}

	.lines div {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.5rem;
		min-height: 2.35rem;
		padding: 0.42rem 0.65rem;
		border-radius: 12px;
		background: rgba(7, 24, 46, 0.88);
		font-size: 0.92rem;
	}

	.final,
	.payout,
	.hot {
		border: 1px solid #ffc940;
	}

	.final.celebrate {
		animation: soft-glow 1.15s ease-out;
	}

	.payout.celebrate.soft,
	.final.celebrate {
		animation: soft-glow 1.35s cubic-bezier(0.22, 0.82, 0.28, 1);
	}

	.payout {
		min-height: 3.4rem;
		padding: 0.72rem 0.9rem;
		background: rgba(7, 24, 46, 0.92);
		border: 2px solid rgba(101, 200, 255, 0.55);
		color: #f4faff;
		font-size: 1.05rem;
	}

	.payout span {
		letter-spacing: 0.12em;
		font-size: 0.78rem;
		font-weight: 800;
		color: #9bb4c8;
	}

	.payout strong {
		font-size: clamp(1.45rem, 3.2vw, 2.15rem);
		font-weight: 800;
		letter-spacing: 0.02em;
		font-variant-numeric: tabular-nums;
		line-height: 1;
	}

	.payout.hit {
		border-color: #65c8ff;
	}

	.payout.counting {
		border-color: #ffe083;
		box-shadow: 0 0 0 1px rgba(255, 201, 64, 0.35);
		animation: payout-pulse 0.85s ease-in-out infinite;
	}

	.payout.celebrate {
		background: #ffc940;
		color: #07182f;
		border-color: #ffe083;
	}

	.payout.celebrate span {
		color: #6c4b00;
	}

	.cap,
	.return,
	.verdict {
		margin: 0.4rem 0 0;
		color: #9bb4c8;
		font-size: 0.76rem;
		font-weight: 800;
		letter-spacing: 0.08em;
	}

	.verdict {
		color: #a8e6ff;
		font-size: clamp(1.35rem, 3.2vw, 2.35rem);
		letter-spacing: 0.14em;
		line-height: 1.05;
		text-transform: uppercase;
	}

	.verdict.big,
	.verdict.mega {
		color: #ffe083;
		text-shadow: 0 0 18px rgba(255, 201, 64, 0.35);
	}

	.verdict.mega {
		font-size: clamp(1.55rem, 3.8vw, 2.7rem);
	}

	.verdict.profit {
		color: #7cffb2;
	}

	.zero .verdict {
		color: #ffc940;
		animation: below-pulse 1.1s ease-in-out infinite;
	}

	.cap {
		color: #ffc940;
	}

	.miss {
		opacity: 0.86;
	}

	.miss-note {
		margin: 0;
		min-height: 1.1em;
		color: #9bb4c8;
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.1em;
	}

	.next-bet {
		pointer-events: auto;
		display: grid;
		gap: 0.12rem;
		justify-items: center;
		width: min(100%, 22rem);
		min-height: 4.2rem;
		margin: 0.85rem auto 0;
		padding: 0.72rem 1.1rem 0.62rem;
		color: #07182f;
		background: #ffc940;
		border: 2px solid #ffe083;
		border-radius: 14px;
		font-size: clamp(0.95rem, 1.8vw, 1.2rem);
		font-weight: 800;
		letter-spacing: 0.14em;
		cursor: pointer;
		box-shadow: 0 10px 22px rgba(3, 14, 29, 0.28);
	}

	.next-bet:not(.ready) {
		visibility: hidden;
		pointer-events: none;
	}

	.next-bet small {
		color: #6c4b00;
		font-size: 0.68rem;
		letter-spacing: 0.18em;
	}

	.zero .next-bet {
		color: #f4faff;
		background: rgba(12, 39, 68, 0.96);
		border-color: #ffc940;
	}

	.zero .next-bet small {
		color: #ffc940;
	}

	@keyframes factor-pulse {
		0%,
		100% {
			transform: scale(1);
			filter: brightness(1);
		}
		50% {
			transform: scale(1.03);
			filter: brightness(1.16);
		}
	}

	@keyframes payout-pulse {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.035);
		}
	}

	@keyframes punch {
		from {
			transform: scale(0.92);
			opacity: 0.4;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}

	@keyframes soft-glow {
		from {
			transform: scale(0.97);
			filter: brightness(0.92);
		}
		to {
			transform: scale(1);
			filter: brightness(1);
		}
	}

	@keyframes badge-pulse {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.12);
		}
	}

	@keyframes below-pulse {
		0%,
		100% {
			opacity: 0.78;
			transform: scale(1);
		}
		50% {
			opacity: 1;
			transform: scale(1.045);
		}
	}

	@media (max-width: 720px) {
		.overlay {
			padding: 72px 8px 96px;
		}

		article {
			width: min(96vw, 460px);
			padding: 44px 12px 14px;
			border-radius: 16px;
			overflow: hidden;
		}

		.kicker {
			font-size: 11px;
		}

		h2 {
			font-size: 28px;
		}

		.factors {
			grid-template-columns: 1fr;
		}

		.below-banner {
			font-size: 16px;
			padding: 6px 12px;
		}

		.lines div {
			font-size: 13px;
		}

		.payout {
			min-height: 48px;
			padding: 10px 12px;
		}

		.payout strong {
			font-size: 22px;
		}

		.miss-note,
		.return,
		.cap,
		.verdict {
			font-size: 11px;
		}

		.next-bet {
			margin-top: 10px;
			padding: 10px 12px 8px;
			font-size: 13px;
		}
	}
</style>
