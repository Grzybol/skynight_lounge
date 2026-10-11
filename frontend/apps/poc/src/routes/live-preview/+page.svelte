<script lang="ts">
	import { onMount } from 'svelte';

	import { GlobalStyle } from 'components-ui-html';
	import { LoadI18n } from 'components-shared';
	import { StoryGameTemplate } from 'components-storybook';
	import { stateBet, stateConfig, stateModal, stateUi } from 'state-shared';

	import Game from '../../components/Game.svelte';
	import SkyJumpV2LivePreviewStage from '../../components/skyjump_v2/SkyJumpV2LivePreviewStage.svelte';
	import { stateGame } from '../../game/stateGame.svelte';
	import messagesMap from '../../i18n/messagesMap';
	import {
		fetchLiveMathHealth,
		getLiveMathSession,
		resetLiveMathStats,
		subscribeLiveMathSession,
		type LiveMathSession,
	} from '../../game/skyjump_v2/liveMath';

	let healthOk = $state(false);
	let healthError = $state('');
	let mathVersion = $state<number | null>(null);
	let baseLutRtp = $state<number | null>(null);
	let session = $state<LiveMathSession | null>(null);

	const connected = $derived(healthOk || (session?.spins ?? 0) > 0);

	const rtpLabel = $derived(
		!session || session.sessionRtpPct == null ? '—' : `${session.sessionRtpPct.toFixed(2)}%`,
	);

	const probeHealth = async (cancelled: () => boolean) => {
		try {
			const health = await fetchLiveMathHealth();
			if (cancelled()) return;
			healthOk = health.ok;
			mathVersion = health.mathVersion;
			baseLutRtp = health.baseLutRtpPct ?? null;
			healthError = '';
		} catch (err: unknown) {
			if (cancelled()) return;
			// Keep prior success if spins already prove the server works.
			if ((session?.spins ?? 0) === 0) {
				healthOk = false;
				healthError = err instanceof Error ? err.message : String(err);
			}
		}
	};

	onMount(() => {
		if (!import.meta.env.DEV) return;
		let cancelled = false;
		const isCancelled = () => cancelled;

		// Clear RGS auth error if the operator opened bare `/` first in this tab.
		stateModal.modal = null;
		stateUi.config.localDemo = true;
		stateUi.config.liveMath = true;
		stateUi.config.theme = 'skyjump';
		void import('../../game/localDemo').then((demo) => {
			if (cancelled) return;
			stateBet.balanceAmount = demo.LOCAL_DEMO_BALANCE;
			stateBet.betAmount = 1;
			stateBet.wageredBetAmount = 1;
			stateBet.autoSpinsCounter = 0;
			stateConfig.betAmountOptions = [...demo.LOCAL_DEMO_BET_OPTIONS];
			stateConfig.betMenuOptions = [...demo.LOCAL_DEMO_BET_OPTIONS];
			stateGame.screen = 'play';
		});

		void probeHealth(isCancelled);
		const poll = window.setInterval(() => {
			if (!healthOk) void probeHealth(isCancelled);
		}, 3000);

		const unsub = subscribeLiveMathSession((next) => {
			if (cancelled) return;
			session = next;
			if ((next?.spins ?? 0) > 0) {
				healthOk = true;
				healthError = '';
			}
		});
		session = getLiveMathSession();

		return () => {
			cancelled = true;
			window.clearInterval(poll);
			unsub();
			stateUi.config.localDemo = false;
			stateUi.config.liveMath = false;
			stateBet.autoSpinsCounter = 0;
		};
	});
</script>

<GlobalStyle>
	<LoadI18n {messagesMap}>
		<SkyJumpV2LivePreviewStage>
			{#snippet chrome()}
				<div class="live-badge" data-test="live-math-badge">
					<span class="tag">LIVE MATH</span>
					{#if connected}
						<span>
							v{mathVersion ?? '?'} · LUT BASE {baseLutRtp != null ? `${baseLutRtp}%` : '96.39%'} ·
							session {rtpLabel} · n={session?.spins ?? 0}
						</span>
						<button type="button" onclick={() => void resetLiveMathStats()}>Reset RTP</button>
					{:else}
						<span class="err">
							Math server offline — run
							<code>python tools/skyjump/live_math_server.py</code>
							{#if healthError}
								({healthError})
							{/if}
						</span>
					{/if}
				</div>
			{/snippet}

			<StoryGameTemplate skipLoadingScreen>
				<Game />
			</StoryGameTemplate>
		</SkyJumpV2LivePreviewStage>
	</LoadI18n>
</GlobalStyle>

<style>
	.live-badge {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		align-items: center;
		justify-content: center;
		width: 100%;
		padding: 8px 12px 4px;
		color: #d7ecf8;
		background: rgba(4, 22, 40, 0.92);
		border-bottom: 1px solid rgba(120, 200, 255, 0.28);
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
		font-size: 11px;
		font-weight: 600;
		line-height: 1.3;
	}

	.tag {
		padding: 2px 8px;
		color: #041018;
		background: #7ad0ff;
		border-radius: 999px;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.08em;
	}

	.err {
		color: #ffb4b4;
	}

	code {
		padding: 1px 4px;
		color: #cfeeff;
		background: rgba(255, 255, 255, 0.08);
		border-radius: 4px;
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
		font-size: 10px;
	}

	button {
		height: 22px;
		padding: 0 10px;
		color: #e8f6ff;
		background: rgba(20, 60, 96, 0.95);
		border: 1px solid rgba(120, 200, 255, 0.45);
		border-radius: 999px;
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
		font-size: 10px;
		font-weight: 700;
		cursor: pointer;
	}

	:global(.wrap:has(> .action)) {
		display: none !important;
	}
</style>
