<script lang="ts">
	import {
		V2_CANONICAL_PAYTABLE,
		V2_DEFAULT_BET_MODE,
		V2_PAYLINE_IDS,
		V2_PAYLINES,
		V2_REGULAR_SYMBOLS,
		V2_SCATTER_ID,
	} from '../../game/skyjump_v2/config';
	import {
		markV2SymbolArtMissing,
		markV2SymbolArtReady,
		v2SymbolVisual,
	} from '../../game/skyjump_v2/symbolAssetRegistry';
	import { V2_MODAL_HEADER, V2_PANEL_DECOR } from '../../game/skyjump_v2/presentationLayout';
	import { v2UiAssetUrl } from '../../game/skyjump_v2/uiAssetRegistry';
	import { sectionHeaderUrl } from '../../game/skyjump_v2/sectionHeaders';
	import { loungeShown, loungeSymbolName } from '../../game/midnightLoungeTheme';
	import SkyJumpV2PanelDecor from './SkyJumpV2PanelDecor.svelte';

	const paytableHeaderSrc = v2UiAssetUrl('headerPaytable');

	const REELS = 5;
	const ROWS = 5;
	const CELL = 28;
	const GAP = 6;
	const PAD = 10;
	const GRID = REELS * CELL + (REELS - 1) * GAP;
	const SVG_SIZE = GRID + PAD * 2;

	const TOKEN_TIERS = [
		{ id: 'T1', name: loungeSymbolName('T1') },
		{ id: 'T2', name: loungeSymbolName('T2') },
		{ id: 'T3', name: loungeSymbolName('T3') },
		{ id: 'T4', name: loungeSymbolName('T4') },
		{ id: 'T5', name: loungeSymbolName('T5') },
		{ id: 'T6', name: loungeSymbolName('T6') },
	] as const;

	const FEATURE_CARDS = [
		{
			id: V2_SCATTER_ID,
			title: 'VIP Invitation',
			body: 'Scatter. Counted anywhere on the board. Does not pay on lines. 3 / 4 / 5 invitations start Free Spins.',
		},
		{
			id: 'C',
			title: 'Concierge Bell',
			body: 'Picks one regular symbol type on the board and turns every match into a Mystery Gift.',
		},
		{
			id: 'Y',
			title: 'Mystery Gift',
			body: 'Opened by the Concierge. Reveals a Lounge Token, Golden Spotlight, VIP Upgrade, Lounge Dealer, or Pit Boss — or in Free Spins also an Encore or a Black Access Pass.',
		},
		{
			id: 'T1',
			title: 'Lounge Tokens T1–T6',
			body: 'Prize values sit on the board. They never pay on their own — a Lounge Dealer or Pit Boss must collect them.',
		},
		{
			id: 'THERMAL_LIFT',
			title: 'Golden Spotlight',
			body: 'Multiplies neighbouring Lounge Tokens (including diagonals). Face values stay the same; only the collected value rises.',
		},
		{
			id: 'GATE_UPGRADE',
			title: 'VIP Upgrade',
			body: 'Raises the token floor so weaker token tiers stop appearing. Tokens already below the floor are upgraded.',
		},
		{
			id: 'JUDGE',
			title: 'Lounge Dealer',
			body: 'Collects the effective value of every Lounge Token on the board into the feature win.',
		},
		{
			id: 'HEAD_JUDGE',
			title: 'Pit Boss',
			body: 'Collects twice in a row — two passes over the same token values for a double collection.',
		},
		{
			id: 'REJUMP',
			title: 'Encore',
			body: 'Free Spins only. Clears eligible regulars and redrops those cells while tokens and invitations stay put. New features can chain again.',
		},
		{
			id: 'WIND_KEY',
			title: 'Black Access Pass',
			body: `Free Spins only. Charges or upgrades ${loungeShown('RUN_UP')}, ${loungeShown('TAKEOFF')}, or ${loungeShown('FLIGHT')}. The lounge multiplier is their product and boosts feature collections.`,
		},
		{
			id: 'SPECIAL_WORLD_RECORD',
			title: 'Midnight Crown',
			body: 'Rare Free Spins board special. Not the T6 Royal Ruby. Settles the round at max win and ends the feature chain.',
		},
	] as const;

	let artReady = $state<Record<string, boolean>>({});
	let artBroken = $state<Record<string, boolean>>({});
	let selectedLineId = $state(V2_PAYLINE_IDS[0] ?? 1);

	const maxWinX = Number(V2_DEFAULT_BET_MODE?.maxWin ?? 50_000);

	const displayName = (name: string) =>
		name
			.replaceAll('_', ' ')
			.toLowerCase()
			.replace(/\b\w/g, (c) => c.toUpperCase());

	const formatAward = (value: number) => {
		if (Number.isInteger(value)) return `${value}`;
		return String(value);
	};

	const selectedRows = $derived(V2_PAYLINES[selectedLineId] ?? V2_PAYLINES[1] ?? [0, 0, 0, 0, 0]);

	const linePath = $derived(
		selectedRows
			.map((row, reel) => {
				const x = PAD + reel * (CELL + GAP) + CELL / 2;
				const y = PAD + row * (CELL + GAP) + CELL / 2;
				return `${x},${y}`;
			})
			.reduce((path, point, index) => (index === 0 ? `M ${point}` : `${path} L ${point}`), ''),
	);

	const selectPrevLine = () => {
		const idx = V2_PAYLINE_IDS.indexOf(selectedLineId);
		const prev = idx <= 0 ? V2_PAYLINE_IDS.length - 1 : idx - 1;
		selectedLineId = V2_PAYLINE_IDS[prev] ?? selectedLineId;
	};

	const selectNextLine = () => {
		const idx = V2_PAYLINE_IDS.indexOf(selectedLineId);
		const next = idx < 0 || idx >= V2_PAYLINE_IDS.length - 1 ? 0 : idx + 1;
		selectedLineId = V2_PAYLINE_IDS[next] ?? selectedLineId;
	};

	const onArtLoad = (id: string) => {
		markV2SymbolArtReady(id);
		artReady = { ...artReady, [id]: true };
	};

	const onArtError = (id: string) => {
		markV2SymbolArtMissing(id);
		artBroken = { ...artBroken, [id]: true };
	};
</script>

<section
	class="v2-pay"
	style:margin-top={`${V2_PANEL_DECOR.panelShiftY}px`}
	style:height={`calc(100% - ${V2_PANEL_DECOR.panelShiftY}px)`}
	style:max-height={`calc(100% - ${V2_PANEL_DECOR.panelShiftY}px)`}
	style:--header-w={`${V2_MODAL_HEADER.maxWidth}px`}
	style:--header-h={`${V2_MODAL_HEADER.maxHeight}px`}
>
	<div class="decor-shell">
		<SkyJumpV2PanelDecor showTopper={false} showDivider={false} />
		<header class="hero">
			<div class="header-art" data-art-slot="paytable-header">
				<img class="section-header" src={paytableHeaderSrc} alt="Paytable" draggable="false" />
			</div>
			<span class="kicker">SKYNIGHT LOUNGE</span>
			<h2>Paytable</h2>
			<p>5×5 SKYNIGHT LOUNGE slot · 28 fixed paylines · awards in bet multiples</p>
		</header>

		<div class="scroll-body" data-test="skyjump-v2-paytable-scroll">
			<section class="block">
				<img class="block-header" src={sectionHeaderUrl('regular_symbols')} alt="Regular symbols" draggable="false" />
				<p class="lede">
					Pays 3, 4, or 5 of a kind left to right on a payline. Highest length wins per line.
				</p>
				<div class="symbol-grid">
					{#each V2_REGULAR_SYMBOLS as symbol}
						{@const visual = v2SymbolVisual(symbol.id)}
						{@const tile = visual.placeholder}
						{@const awards = V2_CANONICAL_PAYTABLE.awards[symbol.id]}
						{@const showArt = Boolean(visual.url && artReady[symbol.id] && !artBroken[symbol.id])}
						<article class="symbol-card">
							<span
								class="swatch"
								style:background={showArt ? 'transparent' : tile.fill}
								style:color={tile.ink}
							>
								{#if visual.url && !artBroken[symbol.id]}
									<img
										class:ready={showArt}
										src={visual.url}
										alt=""
										onload={() => onArtLoad(symbol.id)}
										onerror={() => onArtError(symbol.id)}
									/>
								{/if}
								{#if !showArt}
									{tile.label}
								{/if}
							</span>
							<div class="symbol-copy">
								<strong>{symbol.id}</strong>
								<span class="name">{loungeSymbolName(symbol.id, displayName(symbol.name))}</span>
								{#if awards}
									<ul class="awards">
										<li><em>3</em> {formatAward(awards['3'])}×</li>
										<li><em>4</em> {formatAward(awards['4'])}×</li>
										<li><em>5</em> {formatAward(awards['5'])}×</li>
									</ul>
								{/if}
							</div>
						</article>
					{/each}
				</div>
			</section>

			<section class="block">
				<img class="block-header" src={sectionHeaderUrl('paylines_rules')} alt="Payline rules" draggable="false" />
				<ul class="rule-list">
					<li><strong>28</strong> fixed lines on every spin</li>
					<li>Wins evaluate <strong>left → right</strong></li>
					<li>A win must <strong>start on reel 1</strong> (leftmost)</li>
					<li>
						At least <strong>3 matching</strong> symbols on adjacent reels — gaps break the line
					</li>
					<li>Only the <strong>highest length</strong> pays on each line (3 / 4 / 5)</li>
					<li><strong>Multiple lines</strong> can win together; overlapping cells are fine</li>
					<li><strong>VIP Invitation</strong> (scatter) is never evaluated on lines</li>
				</ul>
			</section>

			<section class="block">
				<img class="block-header" src={sectionHeaderUrl('features')} alt="Features" draggable="false" />
				<div class="feature-grid">
					{#each FEATURE_CARDS as feature}
						{@const visual = v2SymbolVisual(feature.id)}
						{@const tile = visual.placeholder}
						{@const showArt = Boolean(visual.url && artReady[feature.id] && !artBroken[feature.id])}
						<article class="feature-card">
							<span
								class="swatch lg"
								style:background={showArt ? 'transparent' : tile.fill}
								style:color={tile.ink}
							>
								{#if visual.url && !artBroken[feature.id]}
									<img
										class:ready={showArt}
										src={visual.url}
										alt=""
										onload={() => onArtLoad(feature.id)}
										onerror={() => onArtError(feature.id)}
									/>
								{/if}
								{#if !showArt}
									{tile.label}
								{/if}
							</span>
							<div>
								<strong>{feature.title}</strong>
								<p>{feature.body}</p>
							</div>
						</article>
					{/each}
				</div>

				<div class="token-row">
					{#each TOKEN_TIERS as token}
						{@const visual = v2SymbolVisual(token.id)}
						{@const tile = visual.placeholder}
						{@const showArt = Boolean(visual.url && artReady[token.id] && !artBroken[token.id])}
						<span class="token-chip" title={token.name}>
							<span
								class="swatch sm"
								style:background={showArt ? 'transparent' : tile.fill}
								style:color={tile.ink}
							>
								{#if visual.url && !artBroken[token.id]}
									<img
										class:ready={showArt}
										src={visual.url}
										alt=""
										onload={() => onArtLoad(token.id)}
										onerror={() => onArtError(token.id)}
									/>
								{/if}
								{#if !showArt}
									{tile.label}
								{/if}
							</span>
							{token.id}
						</span>
					{/each}
				</div>
			</section>

			<section class="block callout">
				<img class="block-header" src={sectionHeaderUrl('tokens_collectors_max_win')} alt="Tokens, collectors &amp; max win" draggable="false" />
				<ul class="rule-list">
					<li>
						Lounge Tokens <strong>do not auto-pay</strong> — they wait for a Lounge Dealer or Pit Boss
					</li>
					<li>The Pit Boss runs <strong>two collection passes</strong></li>
					<li>Golden Spotlight changes a neighbour token’s <strong>effective</strong> value only</li>
					<li>
						Black Access Pass charges / upgrades
						<strong>{loungeShown('RUN_UP')} · {loungeShown('TAKEOFF')} · {loungeShown('FLIGHT')}</strong>
					</li>
					<li>
						<strong>Midnight Crown</strong> ≠ <strong>T6 Royal Ruby</strong> — different
						symbols, different outcomes
					</li>
					<li>Terminal max win: <strong>{maxWinX.toLocaleString('en-US')}×</strong> bet</li>
				</ul>
			</section>

			<section class="block inspector">
				<img class="block-header" src={sectionHeaderUrl('payline_inspector')} alt="Payline inspector" draggable="false" />
				<p class="lede">Preview any of the {V2_PAYLINE_IDS.length} fixed lines on the 5×5 grid.</p>

				<div class="inspector-controls">
					<button
						type="button"
						class="nav-btn"
						onclick={selectPrevLine}
						aria-label="Previous payline"
					>
						‹ Prev
					</button>
					<label class="line-select">
						<span>Line</span>
						<select
							value={selectedLineId}
							onchange={(event) => {
								selectedLineId = Number(event.currentTarget.value);
							}}
						>
							{#each V2_PAYLINE_IDS as id}
								<option value={id}>{id}</option>
							{/each}
						</select>
					</label>
					<button type="button" class="nav-btn" onclick={selectNextLine} aria-label="Next payline">
						Next ›
					</button>
				</div>

				<svg
					class="line-svg"
					viewBox="0 0 {SVG_SIZE} {SVG_SIZE}"
					role="img"
					aria-label="Payline {selectedLineId} path"
				>
					{#each Array(ROWS) as _, row}
						{#each Array(REELS) as _, reel}
							{@const onLine = selectedRows[reel] === row}
							<rect
								x={PAD + reel * (CELL + GAP)}
								y={PAD + row * (CELL + GAP)}
								width={CELL}
								height={CELL}
								rx="6"
								class:on={onLine}
							/>
						{/each}
					{/each}
					<path d={linePath} class="path" />
					{#each selectedRows as row, reel}
						<circle
							cx={PAD + reel * (CELL + GAP) + CELL / 2}
							cy={PAD + row * (CELL + GAP) + CELL / 2}
							r="4.5"
							class="node"
						/>
					{/each}
				</svg>
				<p class="path-note">
					Line {selectedLineId}: rows [{selectedRows.join(', ')}] · reel 1 → 5
				</p>
			</section>
		</div>
	</div>
</section>

<style>
	.v2-pay {
		--ice: #f3e2b8;
		--muted: #cbb89a;
		--gold: #e4c57a;
		--navy: rgba(42, 11, 20, 0.72);
		--stroke: rgba(212, 168, 92, 0.32);
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: none;
		height: 100%;
		max-height: 100%;
		min-height: 0;
		overflow: visible;
		margin: 0 auto;
		color: var(--ice);
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
	}

	.decor-shell {
		position: relative;
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		flex: 1 1 auto;
		min-height: 0;
		max-height: 100%;
		gap: 8px;
		padding: 5px 1.6rem 1.75rem;
		border: 1px solid rgba(212, 168, 92, 0.72);
		border-radius: 18px;
		background:
			radial-gradient(120% 70% at 50% 0%, rgba(228, 197, 122, 0.12), transparent 52%),
			linear-gradient(180deg, #4a1424, #12080c);
		box-shadow:
			0 18px 40px rgba(0, 0, 0, 0.48),
			inset 0 0 28px rgba(74, 20, 36, 0.45),
			inset 0 1px 0 rgba(243, 226, 184, 0.16);
		overflow: visible;
	}

	.hero {
		position: relative;
		z-index: 2;
		flex: 0 0 auto;
		display: grid;
		gap: 0;
		text-align: center;
		padding: 0 0.25rem;
		overflow: visible;
	}

	.header-art {
		position: relative;
		z-index: 2;
		width: min(86%, var(--header-w, 520px));
		height: var(--header-h, 88px);
		margin: 0 auto 8px;
	}

	.section-header {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		object-fit: contain;
		pointer-events: none;
	}

	.scroll-body {
		position: relative;
		z-index: 2;
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		gap: 0.55rem;
		overflow-x: hidden;
		overflow-y: auto;
		padding: 0 0.35rem 8rem;
		scrollbar-width: thin;
		scrollbar-color: rgba(228, 197, 122, 0.55) rgba(18, 8, 12, 0.45);
	}

	.scroll-body::-webkit-scrollbar {
		width: 8px;
	}

	.scroll-body::-webkit-scrollbar-thumb {
		background: rgba(228, 197, 122, 0.45);
		border-radius: 999px;
	}

	.kicker {
		position: relative;
		z-index: 2;
		color: var(--gold);
		letter-spacing: 0.18em;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 0.806rem;
		font-weight: 800;
		line-height: 1;
		text-transform: uppercase;
	}

	h2,
	h3 {
		position: relative;
		z-index: 2;
		margin: 0;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-weight: 800;
		letter-spacing: 0.02em;
	}

	h2 {
		font-size: 1.365rem;
		line-height: 1.05;
	}

	h3 {
		font-size: 1.092rem;
		color: #f6ead0;
	}

	.lede,
	.hero p,
	.path-note {
		margin: 0;
		color: var(--muted);
		font-size: 0.962rem;
		line-height: 1.35;
	}

	.hero p {
		margin-top: -2px;
		line-height: 1.2;
	}

	.block-header {
		display: block;
		width: min(100%, 300px);
		height: auto;
		margin: 0 auto;
		pointer-events: none;
	}

	.block {
		display: grid;
		gap: 0.45rem;
		padding: 0.55rem 0.65rem;
		background: rgba(18, 8, 12, 0.72);
		border: 1px solid var(--stroke);
		border-radius: 12px;
	}

	.callout {
		border-color: rgba(240, 193, 75, 0.35);
		background: linear-gradient(160deg, rgba(74, 20, 36, 0.85), rgba(18, 8, 12, 0.92));
	}

	.symbol-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 0.45rem;
	}

	.symbol-card,
	.feature-card {
		display: flex;
		gap: 0.45rem;
		align-items: flex-start;
		padding: 0.45rem;
		border-radius: 10px;
		background: rgba(18, 8, 12, 0.55);
		border: 1px solid rgba(212, 168, 92, 0.18);
	}

	.symbol-copy {
		display: grid;
		gap: 0.12rem;
		min-width: 0;
	}

	.symbol-copy strong {
		font-size: 1.014rem;
		color: var(--gold);
	}

	.name {
		font-size: 0.884rem;
		color: var(--muted);
		line-height: 1.25;
	}

	.awards {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
		margin: 0.15rem 0 0;
		padding: 0;
		list-style: none;
		font-size: 0.936rem;
		font-weight: 700;
	}

	.awards em {
		font-style: normal;
		color: var(--muted);
		font-weight: 600;
		margin-right: 0.12rem;
	}

	.feature-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 0.45rem;
	}

	.feature-card strong {
		display: block;
		margin-bottom: 0.15rem;
		font-size: 1.04rem;
	}

	.feature-card p {
		margin: 0;
		color: var(--muted);
		font-size: 0.936rem;
		line-height: 1.35;
	}

	.token-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}

	.token-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.15rem 0.4rem 0.15rem 0.15rem;
		border-radius: 999px;
		background: rgba(18, 8, 12, 0.65);
		border: 1px solid rgba(212, 168, 92, 0.22);
		font-size: 0.884rem;
		font-weight: 700;
		color: #f6ead0;
	}

	.rule-list {
		margin: 0;
		padding-left: 1rem;
		display: grid;
		gap: 0.28rem;
		color: #f3e2b8;
		font-size: 1.014rem;
		line-height: 1.35;
		text-align: left;
	}

	.swatch {
		position: relative;
		display: grid;
		width: 36px;
		height: 36px;
		flex: 0 0 auto;
		place-items: center;
		border-radius: 9px;
		font-size: 11.7px;
		font-weight: 900;
		overflow: hidden;
		box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
	}

	.swatch.lg {
		width: 40px;
		height: 40px;
	}

	.swatch.sm {
		width: 22px;
		height: 22px;
		border-radius: 6px;
		font-size: 9.1px;
	}

	.swatch img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: contain;
		opacity: 0;
	}

	.swatch img.ready {
		opacity: 1;
	}

	.inspector-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: center;
		gap: 0.45rem;
	}

	.nav-btn,
	.line-select select {
		appearance: none;
		border: 1px solid rgba(212, 168, 92, 0.45);
		background: rgba(42, 11, 20, 0.9);
		color: var(--ice);
		border-radius: 10px;
		padding: 0.4rem 0.65rem;
		font: inherit;
		font-size: 0.988rem;
		font-weight: 700;
		cursor: pointer;
	}

	.nav-btn:hover,
	.line-select select:hover,
	.nav-btn:focus-visible,
	.line-select select:focus-visible {
		border-color: rgba(228, 197, 122, 0.72);
		color: #fff8ee;
		outline: none;
	}

	.line-select {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.988rem;
		color: var(--muted);
	}

	.line-select select {
		min-width: 4.5rem;
		text-align: center;
	}

	.line-svg {
		width: min(100%, 200px);
		justify-self: center;
		aspect-ratio: 1;
	}

	.line-svg rect {
		fill: rgba(42, 11, 20, 0.92);
		stroke: rgba(212, 168, 92, 0.35);
		stroke-width: 1;
	}

	.line-svg rect.on {
		fill: rgba(74, 20, 36, 0.95);
		stroke: rgba(228, 197, 122, 0.75);
	}

	.line-svg .path {
		fill: none;
		stroke: #e4c57a;
		stroke-width: 3;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.line-svg .node {
		fill: #f8f4e8;
		stroke: #12080c;
		stroke-width: 1.5;
	}

	.path-note {
		text-align: center;
		font-size: 0.91rem;
	}
</style>
