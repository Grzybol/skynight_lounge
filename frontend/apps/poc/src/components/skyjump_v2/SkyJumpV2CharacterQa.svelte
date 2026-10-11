<script lang="ts">
	/**
	 * DEV-ONLY character animation inspector. Mounted only when
	 * import.meta.env.DEV && localDemo (see SkyJumpV2Board). Drives the same
	 * controllers the game uses; nothing here exists in a production build.
	 */
	import {
		animationIdsFor,
		CHARACTER_ANIMATIONS,
		type CharacterId,
		type WinCategory,
	} from '../../game/loungeCharacters/config';
	import { devRegistry } from '../../game/loungeCharacters/createCharacter';
	import {
		emitLoungeWin,
		loungeWinListenerCount,
		onLoungeWin,
	} from '../../game/loungeCharacters/loungeWinCue';

	let open = $state(false);
	let who = $state<CharacterId>('woman');
	let tick = $state(0);
	let stats = $state<{
		mode: string;
		win: string;
		active: string;
		frame: number;
		fps: number;
		state: string;
		bitmaps: number;
		stalls: number;
		switches: number;
		packs: Array<{ id: string; state: string; mb: number; of: number }>;
		listeners: number;
		error: string;
	} | null>(null);

	const read = () => {
		const h = devRegistry.get(who);
		if (!h) {
			stats = null;
			return;
		}
		const s = h.player.getStats();
		const c = h.controller.getState();
		stats = {
			mode: c.mode,
			win: c.winCategory ?? '-',
			active: s.active ?? '-',
			frame: s.frame,
			fps: s.measuredFps,
			state: s.state,
			bitmaps: s.decodedBitmaps,
			stalls: s.stalls,
			switches: s.switches,
			packs: h.store.snapshot(),
			listeners: loungeWinListenerCount(),
			error: s.lastError ?? '',
		};
	};

	$effect(() => {
		if (!open) return;
		read();
		const timer = setInterval(() => {
			tick += 1;
			read();
		}, 200);
		return () => clearInterval(timer);
	});

	const ctl = () => devRegistry.get(who)?.controller;
	const wins: WinCategory[] = ['mini', 'big', 'mega'];

	const rapid = () => {
		const seq: WinCategory[] = [
			'mini',
			'mini',
			'big',
			'mini',
			'mega',
			'big',
			'mini',
			'mega',
			'mini',
		];
		seq.forEach((c, i) => setTimeout(() => emitLoungeWin(c, 'small'), i * 150));
	};

	/** Every win the board announced, for the automated QA script. */
	const events: Array<{ category: string; tier: string; seq: number; at: number }> = [];

	$effect(() => {
		if (!import.meta.env.DEV) return;
		(window as unknown as { __loungeQa?: unknown }).__loungeQa = {
			registry: devRegistry,
			emit: emitLoungeWin,
			events,
			listeners: loungeWinListenerCount,
		};
		return onLoungeWin((e) => events.push({ ...e, at: performance.now() }));
	});
</script>

<div class="char-qa" data-test="lounge-character-qa">
	<button class="toggle" onclick={() => (open = !open)}>CHARACTERS {open ? '▾' : '▸'}</button>
	{#if open}
		<div class="row">
			{#each ['woman', 'bartender'] as id}
				<button class:on={who === id} onclick={() => (who = id as CharacterId)}>
					{id.toUpperCase()}
				</button>
			{/each}
		</div>
		<div class="row">
			<button onclick={() => ctl()?.playManual(CHARACTER_ANIMATIONS[who].idle)}>idle</button>
			{#each CHARACTER_ANIMATIONS[who].variations as v, i}
				<button onclick={() => ctl()?.playManual(v)}>idle {i + 1}</button>
			{/each}
		</div>
		<div class="row">
			{#each wins as w}
				<button onclick={() => ctl()?.requestWin(w)}>{w} win</button>
			{/each}
			<button onclick={() => emitLoungeWin('mega', 'mega')}>bus: mega (both)</button>
			<button onclick={rapid}>rapid x9</button>
		</div>
		<div class="row">
			{#each animationIdsFor(who) as id}
				<button class="tiny" onclick={() => ctl()?.playManual(id)}
					>{id.replace(`${who}_`, '')}</button
				>
			{/each}
		</div>
		{#if stats}
			<pre>{`mode   ${stats.mode} (${stats.win})
anim   ${stats.active}
frame  ${stats.frame}/149  ${stats.fps} fps  ${stats.state}
cache  ${stats.bitmaps} bitmaps · stalls ${stats.stalls} · switches ${stats.switches}
bus listeners ${stats.listeners}${stats.error ? `\nERR ${stats.error}` : ''}
${stats.packs.map((p) => `${p.id} ${p.state} ${p.mb}/${p.of} MB`).join('\n')}`}</pre>
		{:else}
			<p class="hint">character not mounted</p>
		{/if}
		<span hidden>{tick}</span>
	{/if}
</div>

<style>
	.char-qa {
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

	.row {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-top: 4px;
	}

	button {
		padding: 3px 7px;
		color: #9ecff0;
		background: #10283d;
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 6px;
		cursor: pointer;
	}

	button.on {
		color: #fff;
		background: #1d5a8a;
	}

	button.tiny {
		padding: 1px 5px;
		font-size: 9px;
	}

	pre {
		margin: 6px 0 0;
		font:
			500 9px/1.3 ui-monospace,
			monospace;
		white-space: pre-wrap;
	}

	.hint {
		margin: 4px 0 0;
		opacity: 0.7;
	}
</style>
