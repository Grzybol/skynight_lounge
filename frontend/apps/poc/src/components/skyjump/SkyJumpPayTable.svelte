<script lang="ts">
	import {
		SLOT_ROLES,
		WEATHER_TABLE,
		HILL_TABLE,
		MULTIPLIER_TABLES,
		ENABLED_MODES,
	} from '../../game/skyjump/config';
	import { roleIconSrc } from './skyjumpArt';
	import { t } from '../../game/skyjump/copy';
</script>

<section class="paytable">
	<header>
		<span class="kicker">SKYNIGHT LOUNGE</span>
		<h2>{t('HOW A ROUND PAYS')}</h2>
		<p>{t('PAYTABLE INTRO')}</p>
	</header>

	<div class="roles">
		{#each SLOT_ROLES as role}
			<article>
				<img src={roleIconSrc[role.iconKey]} alt="" />
				<strong>{t(role.shortLabel)}</strong>
				<span>{t(role.label)}</span>
			</article>
		{/each}
	</div>

	<h3>{t('HILLS')}</h3>
	<ul>
		{#each Object.values(HILL_TABLE) as hill}
			<li>{t(hill.label)} · base {hill.baseDistance}m · hill table max {hill.maxWin}x</li>
		{/each}
	</ul>

	<h3>{t('MODES')}</h3>
	<p>{t('MODE COST HINT')}</p>
	<ul>
		{#each ENABLED_MODES as mode}
			<li>
				{mode.title} · {mode.costMultiplier}× base bet · mode max {mode.maxWin}x
			</li>
		{/each}
	</ul>

	<h3>{t('WEATHER')}</h3>
	<p>{t('WEATHER HOW')}</p>
	<p>{t('WEATHER HOW DETAIL')}</p>
	<ul>
		{#each WEATHER_TABLE as weather}
			<li>
				{t(weather.label)} · {t('WEATHER METRES')}
				{weather.distanceDelta > 0 ? '+' : ''}{weather.distanceDelta} m · {t('VOLATILITY')}
				{weather.volatilityBias}
			</li>
		{/each}
	</ul>

	<h3>{t('STANDARD FINAL MULTIPLIERS')}</h3>
	<p>{MULTIPLIER_TABLES.standard.map((row) => row.label).join(' · ')}</p>
</section>

<style>
	.paytable {
		width: min(100%, 780px);
		color: inherit;
	}

	header {
		margin-bottom: 1rem;
		text-align: center;
	}

	.kicker {
		color: #f0c14b;
		letter-spacing: 0.16em;
		font-size: 0.75rem;
		font-weight: 800;
	}

	.roles {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.7rem;
		margin: 1rem 0;
	}

	article {
		display: grid;
		justify-items: center;
		gap: 0.25rem;
		padding: 0.7rem 0.4rem;
		background: rgba(16, 36, 60, 0.55);
		border-radius: 14px;
		text-align: center;
	}

	img {
		width: 42px;
		height: 42px;
	}

	span,
	li,
	p {
		font-size: 0.85rem;
		opacity: 0.9;
	}
</style>
