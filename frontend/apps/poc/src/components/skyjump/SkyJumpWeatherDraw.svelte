<script lang="ts">
	import { getContext } from '../../game/context';
	import { weatherIconSrc } from './skyjumpArt';
	import { t } from '../../game/skyjump/copy';

	const context = getContext();

	const signFor = (delta: number) => (delta > 0.05 ? 'pos' : delta < -0.05 ? 'neg' : 'neu');

	context.eventEmitter.subscribeOnMount({
		skyjumpWeatherShow: (event) => {
			if (event.catchUp) context.stateGame.weatherDrawing = false;
		},
		skyjumpResetBoard: () => {
			context.stateGame.lastWeather = null;
		},
	});

	const shown = $derived(context.stateGame.lastWeather);
	const settled = $derived(
		Boolean(shown && context.stateGame.screen === 'play' && !context.stateGame.weatherDrawing),
	);
	const settledDelta = $derived(shown?.distanceDelta ?? 0);
	const settledSign = $derived(signFor(settledDelta));
</script>

{#if settled && shown}
	<div class="plate settled {settledSign}" aria-live="polite">
		<div class="icon-well">
			<img src={weatherIconSrc[shown.iconKey] ?? weatherIconSrc.sunny} alt="" />
		</div>
		<div class="body">
			<strong class="name">{t(shown.label)}</strong>
			<p class="delta {settledSign}">
				{settledDelta > 0 ? '+' : ''}{settledDelta.toFixed(1)} m
			</p>
			<dl>
				<div>
					<dt>{t('TEMPERATURE')}</dt>
					<dd>{shown.temperatureC.toFixed(1)}°C</dd>
				</div>
				<div>
					<dt>{t('WIND SPEED')}</dt>
					<dd>{shown.windSpeedMs.toFixed(1)} m/s</dd>
				</div>
				<div>
					<dt>{t('WIND DIRECTION')}</dt>
					<dd>{t(shown.windDirection)}</dd>
				</div>
				<div>
					<dt>{t('VISIBILITY')}</dt>
					<dd>{shown.visibilityPct}%</dd>
				</div>
			</dl>
		</div>
	</div>
{/if}

<style>
	.plate {
		position: absolute;
		z-index: 22;
		left: 50%;
		transform: translateX(-50%);
		color: #f4faff;
		pointer-events: none;
	}

	.plate.settled {
		top: 0.45rem;
		display: grid;
		grid-template-columns: 3.6rem minmax(0, 1fr);
		align-items: stretch;
		gap: 0.45rem;
		width: min(46vw, 560px);
		min-height: 3.8rem;
		padding: 0.28rem 0.7rem 0.28rem 0.28rem;
		background: linear-gradient(180deg, rgba(12, 39, 68, 0.94), rgba(5, 22, 43, 0.94));
		border: 2px solid rgba(101, 200, 255, 0.7);
		border-radius: 14px;
		box-shadow: 0 10px 24px rgba(3, 14, 29, 0.32);
	}

	.plate.settled.pos {
		border-color: rgba(124, 255, 178, 0.85);
	}

	.plate.settled.neg {
		border-color: rgba(255, 107, 107, 0.85);
	}

	.icon-well {
		display: grid;
		place-items: center;
		background: rgba(7, 24, 46, 0.72);
		border: 1px solid rgba(101, 200, 255, 0.35);
		border-radius: 10px;
		min-height: 3.2rem;
	}

	.icon-well img {
		width: 36px;
		height: 36px;
	}

	.body {
		display: grid;
		align-content: center;
		gap: 0.16rem;
		min-width: 0;
	}

	.name {
		font-size: clamp(0.92rem, 1.5vw, 1.15rem);
		font-weight: 800;
		letter-spacing: 0.04em;
		line-height: 1.1;
	}

	.delta {
		margin: 0;
		font-size: clamp(0.82rem, 1.2vw, 1rem);
		font-weight: 800;
		letter-spacing: 0.04em;
	}

	.delta.pos {
		color: #7cffb2;
	}

	.delta.neg {
		color: #ff8a8a;
	}

	.delta.neu {
		color: #c5d6e4;
	}

	dl {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.08rem 0.7rem;
		margin: 0;
	}

	dt {
		color: #d5e6f3;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		line-height: 1.1;
	}

	dd {
		margin: 0;
		color: #f4faff;
		font-size: clamp(0.82rem, 1.3vw, 1.05rem);
		font-weight: 800;
		letter-spacing: 0.02em;
		line-height: 1.05;
	}

	@media (max-width: 720px) {
		.plate.settled {
			top: 40px;
			width: min(88vw, 420px);
			grid-template-columns: 48px minmax(0, 1fr);
			min-height: 62px;
			padding: 5px 8px 5px 5px;
		}
	}
</style>
