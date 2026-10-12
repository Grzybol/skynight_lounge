<script lang="ts">
	import { onMount } from 'svelte';

	import { GlobalStyle } from 'components-ui-html';
	import { LoadI18n } from 'components-shared';
	import { StoryGameTemplate } from 'components-storybook';
	import { stateBet, stateConfig, stateModal, stateUi } from 'state-shared';

	import Game from '../../components/Game.svelte';
	import { playBet } from '../../game/utils';
	import { stateGame } from '../../game/stateGame.svelte';
	import { stateLayout } from '../../game/stateLayout';
	import messagesMap from '../../i18n/messagesMap';

	type TestMode =
		| 'baseSpin'
		| 'menu'
		| 'bonus'
		| 'hud'
		| 'loader'
		| 'modalAutoSpin'
		| 'modalBuyBonus'
		| 'modalBet'
		| 'modalSettings'
		| 'modalPaytable'
		| 'modalRules';

	let testMode = $state<TestMode>('baseSpin');
	let devOpen = $state(false);

	onMount(() => {
		if (!import.meta.env.DEV) return;
		let cancelled = false;
		if (import.meta.env.DEV) {
			// Clear RGS auth error if the operator opened bare `/` first in this tab.
			stateModal.modal = null;
			void import('../../game/localDemo').then((demo) => {
				if (cancelled) return;
				const live =
					new URLSearchParams(location.search).get('source') === 'live' ||
					new URLSearchParams(location.search).get('live') === '1';
				stateUi.config.localDemo = true;
				stateUi.config.liveMath = live;
				stateUi.config.theme = 'skyjump';
				// QA hook (dev route only): lets browser tests set balance/bet directly.
				(window as unknown as { __stateBet?: typeof stateBet }).__stateBet = stateBet;
				stateBet.balanceAmount = demo.LOCAL_DEMO_BALANCE;
				stateBet.betAmount = 1;
				stateBet.wageredBetAmount = 1;
				stateBet.autoSpinsCounter = 0;
				stateConfig.betAmountOptions = [...demo.LOCAL_DEMO_BET_OPTIONS];
				stateConfig.betMenuOptions = [...demo.LOCAL_DEMO_BET_OPTIONS];
				const screen = new URLSearchParams(location.search).get('screen');
				stateGame.screen = screen === 'menu' ? 'menu' : 'play';
			});
		}

		return () => {
			cancelled = true;
			stateUi.config.localDemo = false;
			stateUi.config.liveMath = false;
			stateBet.autoSpinsCounter = 0;
		};
	});

	const playBaseSpinTest = async () => {
		if (import.meta.env.DEV) {
			const { createLocalDemoBet } = await import('../../game/localDemo');
			await playBet(createLocalDemoBet());
		}
	};

	const playBonusTest = async () => {
		if (import.meta.env.DEV) {
			const { createLocalDemoBonusBet } = await import('../../game/localDemo');
			await playBet(createLocalDemoBonusBet());
		}
	};

	const playHudTest = async () => {
		stateLayout.showLoadingScreen = false;
	};

	const playLoaderTest = async () => {
		stateLayout.showLoadingScreen = true;
	};

	const showModal = (
		name: 'autoSpin' | 'buyBonus' | 'betAmountMenu' | 'settings' | 'payTable' | 'gameRules',
	) => {
		stateLayout.showLoadingScreen = false;
		stateModal.modal = { name };
	};

	const playSelectedTest = async () => {
		if (testMode === 'modalBuyBonus') return showModal('buyBonus');
		if (testMode === 'modalBet') return showModal('betAmountMenu');
		if (testMode === 'modalSettings') return showModal('settings');
		if (testMode === 'modalPaytable') return showModal('payTable');
		if (testMode === 'modalRules') return showModal('gameRules');
		if (testMode === 'modalAutoSpin') return showModal('autoSpin');
		if (testMode === 'loader') return playLoaderTest();
		if (testMode === 'baseSpin') return playBaseSpinTest();
		if (testMode === 'hud') return playHudTest();
		if (testMode === 'bonus') return playBonusTest();
		if (testMode === 'menu') {
			stateGame.screen = 'menu';
			return;
		}
		return playBaseSpinTest();
	};
</script>

<GlobalStyle>
	<LoadI18n {messagesMap}>
		<div class="dev-harness" class:open={devOpen}>
			<button class="dev-toggle" type="button" onclick={() => (devOpen = !devOpen)}> DEV </button>
			{#if devOpen}
				<label for="test-mode">Test</label>
				<select id="test-mode" bind:value={testMode}>
					<option value="baseSpin">Base spin (5×5 fixture cycle)</option>
					<option value="menu">Main menu</option>
					<option value="hud">HUD only</option>
					<option value="loader">Loader</option>
					<option value="bonus">Buy: Gold Room book</option>
					<option value="modalAutoSpin">Modal: Auto Spin</option>
					<option value="modalBuyBonus">Modal: Buy Bonus</option>
					<option value="modalBet">Modal: Bet</option>
					<option value="modalSettings">Modal: Settings</option>
					<option value="modalPaytable">Modal: Paytable</option>
					<option value="modalRules">Modal: Game Rules</option>
				</select>
				<button class="dev-run" type="button" onclick={() => playSelectedTest()}>Run</button>
			{/if}
		</div>

		<StoryGameTemplate skipLoadingScreen action={playSelectedTest}>
			<Game />
		</StoryGameTemplate>
	</LoadI18n>
</GlobalStyle>

<style>
	.dev-harness {
		position: fixed;
		z-index: 1200;
		top: 18px;
		left: 8px;
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		align-items: center;
		max-width: min(360px, calc(100vw - 16px));
		padding: 4px;
		color: #cfe6f4;
		background: rgba(6, 18, 32, 0.72);
		border: 1px solid rgba(101, 200, 255, 0.28);
		border-radius: 10px;
		font: 600 11px/1.2 sans-serif;
		pointer-events: auto;
	}

	.dev-harness.open {
		padding: 6px 8px;
	}

	.dev-toggle {
		height: 24px;
		padding: 0 8px;
		color: #9ecff0;
		background: rgba(12, 39, 68, 0.9);
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 7px;
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.12em;
		cursor: pointer;
	}

	select {
		padding: 3px 6px;
		color: #fff;
		background: #0b1b2c;
		border: 1px solid #3e6d8f;
		border-radius: 5px;
	}

	.dev-run {
		height: 24px;
		padding: 0 8px;
		color: #f4faff;
		background: #163a5e;
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 7px;
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.08em;
		cursor: pointer;
	}

	:global(.wrap:has(> .action)) {
		display: none !important;
	}
</style>
