<script lang="ts">
	import { stateBet } from 'state-shared';

	import { getContext } from '../../game/context';
	import { loungeLogoSrc } from '../../game/midnightLoungeTheme';
	import { bonusHud } from '../../game/skyjump_v2/bonusHud.svelte';
	import { v2ModeTitleUrl, v2UiAssetUrl } from '../../game/skyjump_v2/uiAssetRegistry';

	const context = getContext();
	const logoSrc = loungeLogoSrc;
	const freeSpinsSrc = v2UiAssetUrl('bonusFreeSpins');
	/** Special room (buy mode or the room of a running bonus); the base game has no banner. */
	const mode = $derived(
		bonusHud.active && bonusHud.tier ? bonusHud.tier : String(stateBet.activeBetModeKey ?? 'BASE'),
	);
	const modeSrc = $derived(v2ModeTitleUrl(mode));
</script>

{#if context.stateGame.screen === 'play'}
	<div class="brand">
		<img class="logo" src={logoSrc} alt="SKYNIGHT LOUNGE" draggable="false" />
		<p class="mark visually-hidden">SKYNIGHT LOUNGE</p>
		{#if modeSrc}
			<img class="banner mode" src={modeSrc} alt="" draggable="false" data-test="brand-mode" />
		{/if}
		{#if bonusHud.active}
			<div class="banner fs" data-test="brand-free-spins">
				<img src={freeSpinsSrc} alt="Free spins" draggable="false" />
				<strong class="fs-count">x{bonusHud.spinsRemaining}</strong>
			</div>
		{/if}
	</div>
{/if}

<style>
	.brand {
		position: absolute;
		z-index: 20;
		top: 0.85rem;
		right: 1rem;
		max-width: min(193px, 16.5%);
		text-align: right;
		pointer-events: none;
		color: #f4faff;
	}

	.logo {
		display: block;
		margin-left: auto;
		width: min(169px, 100%);
		height: auto;
		object-fit: contain;
		filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.42));
	}

	/* Banners stack under the logo: mode first, free spins below. */
	.banner {
		display: block;
		margin: 0.1rem 0 0 auto;
		width: min(150px, 90%);
		height: auto;
		filter: drop-shadow(0 3px 8px rgba(0, 0, 0, 0.45));
	}

	.fs {
		position: relative;
	}

	.fs img {
		display: block;
		width: 100%;
		height: auto;
	}

	.fs-count {
		display: block;
		margin-top: -0.55rem;
		text-align: center;
		color: #f8e2a0;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 1.25rem;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-shadow:
			0 2px 0 rgba(60, 10, 20, 0.9),
			0 0 10px rgba(255, 200, 90, 0.55);
	}

	.visually-hidden {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	@media (max-width: 720px) {
		.brand {
			top: 2.4rem;
			right: 0.4rem;
			max-width: min(120px, 34vw);
		}

		.logo {
			width: min(110px, 100%);
		}

	}
</style>
