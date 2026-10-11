<script lang="ts">
	import { stateBet } from 'state-shared';

	import { getContext } from '../../game/context';
	import { t } from '../../game/skyjump/copy';
	import { loungeLogoSrc, loungeShown } from '../../game/midnightLoungeTheme';

	const context = getContext();
	const logoSrc = loungeLogoSrc;
	const roomLabel = $derived(loungeShown(String(stateBet.activeBetModeKey ?? 'BASE'), 'MAIN LOUNGE'));
</script>

{#if context.stateGame.screen === 'play'}
	<div class="brand">
		<img class="logo" src={logoSrc} alt="Midnight Lounge" draggable="false" />
		<p class="mark visually-hidden">MIDNIGHT LOUNGE</p>
		<p class="tag">{t('Reach higher')}</p>
		<div class="hill">{roomLabel}</div>
	</div>
{/if}

<style>
	.brand {
		position: absolute;
		z-index: 20;
		top: 0.85rem;
		right: 1rem;
		max-width: min(168px, 15%);
		text-align: right;
		pointer-events: none;
		color: #f4faff;
	}

	.logo {
		display: block;
		margin-left: auto;
		width: min(152px, 100%);
		height: auto;
		object-fit: contain;
		filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.42));
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

	.tag {
		margin: 0.1rem 0 0.28rem;
		color: #e4c57a;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 0.55rem;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}

	.hill {
		display: inline-block;
		padding: 0.18rem 0.55rem;
		color: #f4faff;
		background: rgba(24, 8, 14, 0.78);
		border: 1px solid rgba(212, 168, 92, 0.55);
		border-radius: 999px;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 0.58rem;
		font-weight: 800;
		letter-spacing: 0.07em;
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

		.tag {
			display: none;
		}

		.hill {
			font-size: 9px;
			padding: 2px 7px;
		}
	}
</style>
