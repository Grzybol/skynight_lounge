<script lang="ts">
	/**
	 * DEV-ONLY audio soundboard. Uses production playV2AudioHook — no second engine.
	 * Mounted only when import.meta.env.DEV && localDemo (see SkyJumpV2Board).
	 */
	import { stateSound } from 'state-shared';
	import { waitForTimeout } from 'utils-shared/wait';

	import {
		getV2HookPlaybackInfo,
		playV2AudioHook,
		v2AudioSchedulerStats,
	} from '../../game/skyjump_v2/audio';
	import { V2_TIMING } from '../../game/skyjump_v2/timings';

	const HOOK_ORDER = [
		'UI_CLICK',
		'UI_HOVER',
		'PANEL_OPEN',
		'PANEL_CLOSE',
		'BET_CONFIRM',
		'BET_INCREASE',
		'BET_DECREASE',
		'REEL_START',
		'REEL_STOP',
		'PAYLINE_DRAW',
		'PAYLINE_COMPLETE',
		'SCATTER_LAND',
		'SCATTER_TRIGGER',
		'FS_START',
		'FS_RETRIGGER',
		'TIER_UPGRADE',
		'MYSTERY_TRANSFORM',
		'MYSTERY_REVEAL',
		'TOKEN_REVEAL',
		'THERMAL',
		'GATE_UPGRADE',
		'JUDGE_COLLECT',
		'HEAD_JUDGE_COLLECT',
		'REJUMP',
		'WIND_CHARGE',
		'WIND_UPGRADE',
		'WIND_TRANSITION',
		'WORLD_RECORD',
		'MAX_WIN',
		'BONUS_END',
		'BAD_MISS',
		'COACH',
	] as const;

	const rows = HOOK_ORDER.map((hook) => getV2HookPlaybackInfo(hook));

	let busy = $state(false);
	let log = $state('Ready — voice-pool scheduler (audible window, not EOF)');
	let open = $state(false);

	const play = (hook: string) => {
		playV2AudioHook(hook, { catchUp: false });
		log = `played ${hook} · started ${v2AudioSchedulerStats.playsStarted}`;
	};

	const runSeq = async (name: string, steps: Array<() => void | Promise<void>>) => {
		if (busy) return;
		busy = true;
		log = `seq ${name}…`;
		try {
			for (const step of steps) await step();
			log = `seq ${name} done · started ${v2AudioSchedulerStats.playsStarted}`;
		} catch (err) {
			log = `seq ${name} error`;
			console.warn('[v2-audio-qa]', err);
		} finally {
			busy = false;
		}
	};

	const burst = (hook: string, count: number, intervalMs: number) =>
		runSeq(`rapid ${hook} @${intervalMs}ms`, async () => {
			for (let i = 0; i < count; i += 1) {
				playV2AudioHook(hook);
				if (i < count - 1) await waitForTimeout(intervalMs);
			}
		});

	const seqPayline = () =>
		runSeq('payline', [
			() => playV2AudioHook('PAYLINE_DRAW'),
			() => waitForTimeout(V2_TIMING.normal.lineDrawMs),
			() => playV2AudioHook('PAYLINE_COMPLETE'),
		]);

	const seqRapidPaylines = () =>
		runSeq('rapid-paylines', [
			() => playV2AudioHook('PAYLINE_DRAW'),
			() => waitForTimeout(90),
			() => playV2AudioHook('PAYLINE_COMPLETE'),
			() => waitForTimeout(90),
			() => playV2AudioHook('PAYLINE_DRAW'),
			() => waitForTimeout(90),
			() => playV2AudioHook('PAYLINE_COMPLETE'),
			() => waitForTimeout(90),
			() => playV2AudioHook('PAYLINE_DRAW'),
			() => waitForTimeout(90),
			() => playV2AudioHook('PAYLINE_COMPLETE'),
		]);

	const seqScatterFs = () =>
		runSeq('scatter/fs', [
			() => playV2AudioHook('SCATTER_LAND'),
			() => waitForTimeout(80),
			() => playV2AudioHook('SCATTER_LAND'),
			() => waitForTimeout(80),
			() => playV2AudioHook('SCATTER_LAND'),
			() => waitForTimeout(160),
			() => playV2AudioHook('SCATTER_TRIGGER'),
			() => waitForTimeout(280),
			() => playV2AudioHook('FS_START'),
		]);

	const seqFeatureOverlap = () =>
		runSeq('feature-overlap', [
			() => playV2AudioHook('MYSTERY_TRANSFORM'),
			() => waitForTimeout(80),
			() => playV2AudioHook('TOKEN_REVEAL'),
			() => waitForTimeout(80),
			() => playV2AudioHook('THERMAL'),
			() => waitForTimeout(80),
			() => playV2AudioHook('JUDGE_COLLECT'),
		]);

	const seqMysteryToken = () =>
		runSeq('mystery/token', [
			() => playV2AudioHook('MYSTERY_TRANSFORM'),
			() => waitForTimeout(V2_TIMING.normal.mysteryHoldMs),
			() => playV2AudioHook('TOKEN_REVEAL'),
		]);

	const seqHeadJudge = () =>
		runSeq('head-judge', [
			() => playV2AudioHook('HEAD_JUDGE_COLLECT', { gainScale: 1 }),
			() => waitForTimeout(V2_TIMING.normal.collectHoldMs),
			() => playV2AudioHook('HEAD_JUDGE_COLLECT', { gainScale: 0.7 }),
		]);

	const seqWind = () =>
		runSeq('wind', [
			() => playV2AudioHook('WIND_CHARGE'),
			() => waitForTimeout(V2_TIMING.normal.windHoldMs),
			() => playV2AudioHook('WIND_UPGRADE'),
			() => waitForTimeout(120),
			() => playV2AudioHook('WIND_TRANSITION'),
		]);

	const seqWorldRecord = () =>
		runSeq('world-record', [
			() => playV2AudioHook('WORLD_RECORD'),
			() => waitForTimeout(V2_TIMING.normal.wrHoldMs),
			() => playV2AudioHook('MAX_WIN'),
		]);

	const seqBonusEnd = () => runSeq('bonus-end', [() => playV2AudioHook('BONUS_END')]);

	const seqTurboSpam = () =>
		runSeq('turbo-chain', [
			() => playV2AudioHook('PAYLINE_DRAW'),
			() => waitForTimeout(40),
			() => playV2AudioHook('PAYLINE_DRAW'),
			() => waitForTimeout(40),
			() => playV2AudioHook('PAYLINE_COMPLETE'),
			() => waitForTimeout(40),
			() => playV2AudioHook('SCATTER_LAND'),
			() => waitForTimeout(30),
			() => playV2AudioHook('SCATTER_LAND'),
			() => waitForTimeout(30),
			() => playV2AudioHook('TOKEN_REVEAL'),
			() => waitForTimeout(30),
			() => playV2AudioHook('THERMAL'),
			() => waitForTimeout(30),
			() => playV2AudioHook('JUDGE_COLLECT'),
			() => waitForTimeout(80),
			() => playV2AudioHook('WORLD_RECORD'),
			() => waitForTimeout(V2_TIMING.turbo.wrHoldMs),
			() => playV2AudioHook('MAX_WIN'),
		]);

	const seqHeadJudgeOverlap = () =>
		runSeq('head-judge-gains', [
			() => playV2AudioHook('HEAD_JUDGE_COLLECT', { gainScale: 1 }),
			() => waitForTimeout(100),
			() => playV2AudioHook('HEAD_JUDGE_COLLECT', { gainScale: 0.7 }),
		]);

	const seqMixed = () =>
		runSeq('draw+land+token', [
			() => {
				playV2AudioHook('PAYLINE_DRAW');
				playV2AudioHook('SCATTER_LAND');
				playV2AudioHook('TOKEN_REVEAL');
			},
		]);
	const seqCatchUp = () =>
		runSeq('catch-up', [
			() => {
				playV2AudioHook('FS_START', { catchUp: true });
				playV2AudioHook('SCATTER_TRIGGER', { catchUp: true });
				playV2AudioHook('GATE_UPGRADE', { catchUp: true });
				playV2AudioHook('WIND_CHARGE', { catchUp: true });
				playV2AudioHook('REJUMP', { catchUp: true });
				playV2AudioHook('WORLD_RECORD', { catchUp: true });
				log = 'catch-up historical (silent)…';
			},
			() => waitForTimeout(200),
			() => {
				playV2AudioHook('UI_CLICK', { catchUp: false });
				log = 'catch-up: only post-resume UI_CLICK should have played';
			},
		]);
</script>

<div class="audio-qa" data-test="skyjump-v2-audio-qa">
	<button type="button" class="toggle" onclick={() => (open = !open)}>
		Audio QA {open ? '▾' : '▸'}
	</button>
	{#if open}
		<p class="hint">
			Production playV2AudioHook · polyphonic voices, natural end, per-id gain. Status: {log}
		</p>
		<p class="vols">
			Master {stateSound.volumeValueMaster}% · SFX {stateSound.volumeValueSoundEffect}% · BGM
			{stateSound.volumeValueMusic}% · started {v2AudioSchedulerStats.playsStarted} · gap-block
			{v2AudioSchedulerStats.playsBlockedGap} · pool-steal/block
			{v2AudioSchedulerStats.playsBlockedPool} (steal retired)
		</p>

		<div class="seqs">
			<span class="sec">Stress</span>
			<button type="button" disabled={busy} onclick={() => burst('UI_HOVER', 10, 250)}
				>Rapid hover 250ms</button
			>
			<button type="button" disabled={busy} onclick={() => burst('UI_HOVER', 10, 100)}
				>Rapid hover 100ms</button
			>
			<button type="button" disabled={busy} onclick={() => burst('UI_HOVER', 10, 50)}
				>Rapid hover 50ms</button
			>
			<button type="button" disabled={busy} onclick={seqRapidPaylines}>Rapid paylines</button>
			<button type="button" disabled={busy} onclick={seqFeatureOverlap}>Feature overlap</button>
			<button type="button" disabled={busy} onclick={seqScatterFs}>Scatter→FS</button>
			<button type="button" disabled={busy} onclick={() => burst('TOKEN_REVEAL', 2, 100)}
				>Token ×2 @100ms</button
			>
			<button type="button" disabled={busy} onclick={() => burst('TOKEN_REVEAL', 5, 40)}
				>Token ×5 rapid</button
			>
			<button
				type="button"
				disabled={busy}
				onclick={() => burst('PAYLINE_DRAW', 5, V2_TIMING.turbo.lineDrawMs)}
				>Payline draw ×5 turbo</button
			>
			<button
				type="button"
				disabled={busy}
				onclick={() =>
					burst('SCATTER_LAND', 5, V2_TIMING.turbo.reelStopMs + V2_TIMING.turbo.reelGapMs)}
				>Scatter land ×5 turbo</button
			>
			<button type="button" disabled={busy} onclick={seqMixed}>Draw+Land+Token</button>
			<button type="button" disabled={busy} onclick={seqHeadJudgeOverlap}
				>Head Judge gains overlap</button
			>
			<button type="button" disabled={busy} onclick={seqHeadJudge}>Head Judge ×2</button>
		</div>

		<div class="seqs">
			<span class="sec">Sequences</span>
			<button type="button" disabled={busy} onclick={seqPayline}>Payline</button>
			<button type="button" disabled={busy} onclick={seqMysteryToken}>Mystery→Token</button>
			<button type="button" disabled={busy} onclick={seqWind}>Wind</button>
			<button type="button" disabled={busy} onclick={seqWorldRecord}>WR→MaxWin</button>
			<button type="button" disabled={busy} onclick={seqBonusEnd}>Bonus End</button>
			<button type="button" disabled={busy} onclick={seqTurboSpam}>Turbo chain</button>
			<button type="button" disabled={busy} onclick={seqCatchUp}>Catch-up silence</button>
		</div>

		<div class="grid">
			{#each rows as row}
				<button
					type="button"
					class="hook"
					class:silent={row.status === 'SILENT'}
					disabled={busy || row.status === 'SILENT'}
					onclick={() => play(row.hook)}
					title={`${row.file} · voices ${row.maxVoices} · gap ${row.minGapMs}ms`}
				>
					<span class="name">{row.hook}</span>
					<span class="meta">{row.file}</span>
					<span class="meta">
						gain {row.gain ?? '—'} · {row.status} · {row.maxVoices > 0
							? `v${row.maxVoices}`
							: 'poly'} · gap {row.minGapMs}ms
					</span>
					<span class="meta">
						tot {row.totalSec ?? '—'}s · aud {row.audibleSec ?? '—'}s · {row.overlap}
					</span>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.audio-qa {
		width: 100%;
		margin-top: 6px;
		padding: 6px;
		color: #d7ecf8;
		background: rgba(6, 20, 36, 0.88);
		border: 1px solid rgba(101, 200, 255, 0.35);
		border-radius: 8px;
		font:
			600 10px/1.25 ui-sans-serif,
			system-ui,
			sans-serif;
	}

	.toggle {
		padding: 3px 8px;
		color: #9ecff0;
		background: #10283d;
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 6px;
		cursor: pointer;
		letter-spacing: 0.06em;
	}

	.hint,
	.vols {
		margin: 6px 0 4px;
		color: #9bb4c8;
		font-weight: 500;
	}

	.seqs {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		align-items: center;
		margin-bottom: 8px;
	}

	.sec {
		margin-right: 4px;
		color: #f0c14b;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.seqs button,
	.hook {
		color: #f4faff;
		background: #12324c;
		border: 1px solid rgba(101, 200, 255, 0.4);
		border-radius: 5px;
		cursor: pointer;
	}

	.seqs button {
		padding: 3px 6px;
	}

	.seqs button:disabled,
	.hook:disabled {
		opacity: 0.45;
		cursor: default;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
		gap: 4px;
		max-height: 260px;
		overflow: auto;
	}

	.hook {
		display: grid;
		gap: 2px;
		padding: 5px 6px;
		text-align: left;
	}

	.hook.silent {
		opacity: 0.55;
		border-style: dashed;
	}

	.name {
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.02em;
	}

	.meta {
		color: #8eabc0;
		font-size: 9px;
		font-weight: 500;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
