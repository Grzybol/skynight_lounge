<script lang="ts">
	import { stateBet, stateModal, stateUi } from 'state-shared';

	import { getContext } from '../../game/context';
	import { t } from '../../game/skyjump/copy';

	const context = getContext();

	const backToGame = () => {
		stateModal.modal = null;
		context.stateLayout.showLoadingScreen = false;
		stateBet.autoSpinsCounter = 0;
		stateBet.activeBetModeKey = 'BASE';
		context.stateGame.screen = 'play';
		context.eventEmitter.broadcast({ type: 'uiShow' });
	};

	const showDevBack = $derived(stateUi.config.localDemo && !stateUi.config.liveMath);
</script>

{#if context.stateGame.screen === 'play' && showDevBack}
	<button class="back" type="button" onclick={backToGame}>← {t('Back to game')}</button>
{/if}

<style>
	.back {
		position: absolute;
		z-index: 21;
		top: 14px;
		left: 48px;
		height: 28px;
		padding: 0 10px;
		color: #f4faff;
		background: rgba(12, 48, 82, 0.92);
		border: 1px solid rgba(126, 214, 255, 0.85);
		border-radius: 999px;
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
		font-size: 12px;
		font-weight: 800;
		letter-spacing: 0.02em;
		cursor: pointer;
		white-space: nowrap;
	}

	@media (max-width: 720px) {
		.back {
			top: 8px;
			left: 8px;
			height: 26px;
			padding: 0 7px;
			font-size: 10px;
		}
	}
</style>
