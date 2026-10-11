<script lang="ts">
	import { stateModal, stateBet } from 'state-shared';

	import { getContext } from '../../game/context';
	import { SKYJUMP_SFX } from '../../game/skyjump/audio';
	import { t } from '../../game/skyjump/copy';
	import {
		loungeLogoSrc,
		loungeMenuFigureSrc,
		loungeMenuPlateSrc,
	} from '../../game/midnightLoungeTheme';

	const context = getContext();
	const logoSrc = loungeLogoSrc;

	const play = async () => {
		context.eventEmitter.broadcast({ type: 'soundOnce', name: SKYJUMP_SFX.button });
		context.stateGame.screen = 'play';
		await context.eventEmitter.broadcastAsync({ type: 'uiShow' });
	};
</script>

{#if context.stateGame.screen === 'menu'}
	<div class="menu" style:background-image="url({loungeMenuPlateSrc})">
		<div class="shade"></div>
		<img class="jumper" src={loungeMenuFigureSrc} alt="" />
		<div class="panel">
			<p class="kicker">{t('WINTER SPORTS MINI-GAME')}</p>
			<img class="menu-logo" src={logoSrc} alt="Midnight Lounge" draggable="false" />
			<h1 class="visually-hidden">Midnight Lounge</h1>
			<p class="sub">{t('Ski jumping · night stadium · sequential reels')}</p>
			<button class="primary" type="button" onclick={play}>{t('PLAY')}</button>
			<div class="row">
				<button
					type="button"
					onclick={() => {
						context.eventEmitter.broadcast({ type: 'soundOnce', name: SKYJUMP_SFX.button });
						stateModal.modal = { name: 'settings' };
					}}>{t('SETTINGS')}</button
				>
				<button
					type="button"
					onclick={() => {
						context.eventEmitter.broadcast({ type: 'soundOnce', name: SKYJUMP_SFX.button });
						stateModal.modal = { name: 'gameRules' };
					}}>{t('INFO')}</button
				>
			</div>
			<p class="meta">{t('BALANCE')} {stateBet.balanceAmount.toFixed(2)} {stateBet.currency}</p>
		</div>
	</div>
{/if}

<style>
	.menu {
		position: absolute;
		inset: 0;
		z-index: 40;
		overflow: hidden;
		background: #071526 center / cover no-repeat;
	}

	.shade {
		position: absolute;
		inset: 0;
		background: linear-gradient(
			90deg,
			rgba(7, 21, 38, 0.78) 12%,
			rgba(7, 21, 38, 0.28) 52%,
			rgba(7, 21, 38, 0.08)
		);
	}

	.jumper {
		position: absolute;
		right: 4%;
		bottom: 0;
		height: min(86vh, 820px);
		pointer-events: none;
		filter: drop-shadow(0 18px 24px rgba(4, 12, 22, 0.35));
	}

	.panel {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		width: min(92vw, 440px);
		margin: 11vh 0 0 7vw;
		color: #eef4f8;
	}

	.kicker {
		margin: 0;
		letter-spacing: 0.2em;
		font-size: 0.72rem;
		font-weight: 800;
		color: #f0c14b;
	}

	.menu-logo {
		display: block;
		width: min(360px, 78%);
		height: auto;
		object-fit: contain;
		filter: drop-shadow(0 10px 22px rgba(0, 0, 0, 0.4));
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

	h1 {
		margin: 0;
		font-size: clamp(2.8rem, 8vw, 4.8rem);
		letter-spacing: 0.045em;
		text-transform: uppercase;
	}

	.sub {
		margin: 0 0 0.5rem;
		color: #e6d3b0;
	}

	button {
		border: 1px solid #7ecbff;
		border-radius: 999px;
		background: rgba(16, 36, 60, 0.78);
		color: #eef4f8;
		font-weight: 800;
		letter-spacing: 0.08em;
		padding: 0.85rem 1.2rem;
		cursor: pointer;
	}

	.primary {
		background: #f0c14b;
		color: #10243c;
		border-color: #ffe7a3;
		font-size: 1.12rem;
	}

	.row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.6rem;
	}

	.meta {
		margin: 0.4rem 0 0;
		color: #9eb7c9;
		font-size: 0.85rem;
	}

	@media (max-width: 720px) {
		.panel {
			margin: 72px auto 0;
			text-align: center;
			width: min(92vw, 440px);
		}

		.kicker {
			font-size: 11px;
		}

		h1 {
			font-size: clamp(32px, 10vw, 52px);
		}

		.sub,
		.meta {
			font-size: 13px;
		}

		button {
			font-size: 14px;
			padding: 12px 16px;
		}

		.primary {
			font-size: 16px;
		}

		.jumper {
			opacity: 0.42;
			right: -10%;
			height: min(70vh, 560px);
		}
	}
</style>
