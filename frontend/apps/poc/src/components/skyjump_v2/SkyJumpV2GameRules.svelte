<script lang="ts">
	import {
		V2_DEFAULT_BET_MODE,
		V2_ENABLED_BUY_MODES,
		V2_PAYLINE_IDS,
	} from '../../game/skyjump_v2/config';
	import { V2_MODAL_HEADER, V2_PANEL_DECOR } from '../../game/skyjump_v2/presentationLayout';
	import { v2UiAssetUrl } from '../../game/skyjump_v2/uiAssetRegistry';
	import { INFO_SECTION_HEADERS, sectionHeaderUrl } from '../../game/skyjump_v2/sectionHeaders';
	import { loungePhrase, loungeShown } from '../../game/midnightLoungeTheme';
	import { V2_MODE_STATS } from '../../game/skyjump_v2/modeStats';
	import SkyJumpV2PanelDecor from './SkyJumpV2PanelDecor.svelte';

	const maxWinX = Number(V2_DEFAULT_BET_MODE?.maxWin ?? 50_000);
	const lineCount = V2_PAYLINE_IDS.length;
	const headerHowToPlay = v2UiAssetUrl('headerHowToPlay');
	const headerInfo = v2UiAssetUrl('headerInfo');

	const sectionHeaderSrc = (title: string) => {
		if (title === 'How to Play') return headerHowToPlay;
		const key = INFO_SECTION_HEADERS[title];
		return key ? sectionHeaderUrl(key) : null;
	};

	const sections = [
		{
			title: 'How to Play',
			body: 'Spin a 5×5 SKYNIGHT LOUNGE board. Regular symbols pay on fixed lines. VIP Invitations trigger Free Spins. The Concierge, Mystery Gifts, tokens, and collectors can chain after the lines settle.',
		},
		{
			title: 'Paylines',
			body: `${lineCount} fixed lines, left to right. Wins must start on reel 1, use at least 3 adjacent matches, and pay the highest length on that line. Multiple lines can win at once. Invitations never pay on lines.`,
		},
		{
			title: 'Free Spins',
			body: `3 invitations → ${loungeShown('LARGE_HILL')}, 4 → ${loungeShown('SKI_FLYING')}, 5 → ${loungeShown('WORLD_CUP')}. Five invitations in a V on the board start ${loungeShown('PERFECT_V')}. Each trigger awards 10 Free Spins (up to 40 in one round). During Free Spins, 3+ invitations on a spin’s opening board add +5 spins and step the room up on the next spin.`,
		},
		{
			title: 'Bonus Rooms',
			body: 'Four rooms. Intensity and persistence grow as you move deeper.',
			items: [
				`${loungeShown('LARGE_HILL')} — more Concierge action and standard features.`,
				`${loungeShown('SKI_FLYING')} — Concierge picks can stick as Mystery Gift targets for later spins.`,
				`${loungeShown('WORLD_CUP')} — same persistence, plus a guaranteed VIP Upgrade once in the bonus.`,
				`${loungeShown('PERFECT_V')} — highest intensity: Concierge every spin, a VIP Upgrade guarantee, and a lasting lounge multiplier.`,
			],
		},
		{
			title: 'Mystery Gift & Concierge',
			body: 'The Concierge Bell chooses one regular type on the board and turns every match into a Mystery Gift. The gift then opens into a token or special. In Free Spins, a gift can also become an Encore or a Black Access Pass.',
		},
		{
			title: 'Lounge Tokens',
			body: 'T1 Bronze Guest through T6 Royal Ruby carry prize values. They do not pay alone — a Lounge Dealer or Pit Boss must collect them in the same feature chain. Uncollected tokens do not bank for later spins.',
		},
		{
			title: 'Spotlight & VIP Upgrade',
			body: 'Golden Spotlight multiplies neighbouring tokens (including diagonals) for collection only. VIP Upgrade raises the token floor so lower tiers stop appearing and weak tokens on the board are upgraded.',
		},
		{
			title: 'Lounge Dealer & Pit Boss',
			body: 'The Lounge Dealer collects every token’s effective value once. The Pit Boss collects twice in a row. Tokens can stay on the board after collection unless the round removes them.',
		},
		{
			title: 'Encore',
			body: 'Free Spins only. Eligible regulars clear and redrop while tokens and invitations hold. The new board can start another feature chain. Invitations from an Encore never add a late Free Spin trigger.',
		},
		{
			title: 'Black Access Pass & Lounge Multiplier',
			body: `Free Spins only. Each Black Access Pass charges or upgrades ${loungeShown('RUN_UP')}, ${loungeShown('TAKEOFF')}, or ${loungeShown('FLIGHT')}. The lounge multiplier is their product and boosts feature collections for the rest of the bonus.`,
		},
		{
			title: 'Royal Win',
			body: 'The Midnight Crown is a rare Free Spins board special — not the T6 Royal Ruby. It fills the round to max win and ends remaining Free Spins and feature chains.',
		},
		{
			title: 'Max Win',
			body: `The round cannot exceed ${maxWinX.toLocaleString('en-US')}× your bet. Line wins, feature wins, and Royal Win all count toward the same cap.`,
		},
		{
			title: 'RTP & Max Win',
			body: 'Return to player and the maximum win of every mode. Max win is a multiple of your bet.',
			items: Object.entries(V2_MODE_STATS).map(
				([mode, stat]) =>
					`${loungeShown(mode)} — RTP ${stat.rtpPct.toFixed(2)}% · max win ${stat.maxWinX.toLocaleString('en-US')}× bet`,
			),
		},
		{
			title: 'Buy Bonus',
			body:
				V2_ENABLED_BUY_MODES.length > 0
					? 'Buy straight into a Free Spins room instead of waiting for invitations in the main lounge.'
					: 'Feature buys appear here when available.',
			items:
				V2_ENABLED_BUY_MODES.length > 0
					? V2_ENABLED_BUY_MODES.map((mode) => {
							const tier = loungeShown(
								mode.startsBonusTier ?? '',
								(mode.startsBonusTier ?? 'Free Spins').replaceAll('_', ' '),
							);
							return `${loungePhrase(mode.playerName ?? mode.label)} — ${mode.costMultiplier}× bet · starts ${tier}`;
						})
					: [],
		},
		{
			title: 'Controls',
			wide: true,
			body: 'Every button of the control bar:',
			items: [
				'Menu — opens Info, Paytable, Sound, Settings and the language switch.',
				'Balance — your current balance. Win — the win of the last round.',
				'− / + — lower or raise the bet. The bet button opens the list of bet levels.',
				'Spin — starts a round (Space bar does the same). While a round runs it becomes Stop and ends the animation early.',
				'Turbo — faster rounds.',
				'Auto Spin — opens a panel to choose the number of automatic rounds and limits; nothing starts until you confirm.',
				'Buy Bonus (the SKYNIGHT LOUNGE emblem) — choose a bonus room and confirm its cost.',
				'Sound — mutes or restores all sound. Settings — sound and display options. Info — this guide. Paytable — symbol values.',
			],
		},
		{
			title: 'Notice',
			wide: true,
			body: 'Malfunction voids all wins and plays. A consistent internet connection is required. In the event of a disconnection, reload the game to finish any uncompleted rounds. The expected return is calculated over many plays. The game display is not representative of any physical device and is for illustrative purposes only. Winnings are settled according to the amount received from the Remote Game Server and not from events within the web browser. TM and © 2026 Engine.',
		},
	];
</script>

<section
	class="v2-rules"
	style:margin-top={`${V2_PANEL_DECOR.panelShiftY}px`}
	style:height={`calc(100% - ${V2_PANEL_DECOR.panelShiftY}px)`}
	style:max-height={`calc(100% - ${V2_PANEL_DECOR.panelShiftY}px)`}
	style:--header-w={`${V2_MODAL_HEADER.maxWidth}px`}
	style:--header-h={`${V2_MODAL_HEADER.maxHeight}px`}
>
	<div class="decor-shell">
		<SkyJumpV2PanelDecor showTopper={false} showDivider={false} />
		<header class="hero">
			<div class="header-art" data-art-slot="info-header">
				<img class="section-header" src={headerInfo} alt="Game Info" draggable="false" />
			</div>
			<span class="kicker">SKYNIGHT LOUNGE</span>
			<h2>Game Info</h2>
			<p>Player guide for SKYNIGHT LOUNGE</p>
		</header>

		<div class="scroll-body" data-test="skyjump-v2-rules-scroll">
			<div class="cards">
				{#each sections as section}
					{@const headerSrc = sectionHeaderSrc(section.title)}
					<article class="card" class:wide={'wide' in section && section.wide}>
						<SkyJumpV2PanelDecor showTopper={false} showCorners={false} showDivider={false} />
						{#if headerSrc}
							<img class="card-header" src={headerSrc} alt={section.title} draggable="false" />
						{:else}
							<h3>{section.title}</h3>
						{/if}
						{#if section.body}
							<p>{section.body}</p>
						{/if}
						{#if 'items' in section && section.items.length > 0}
							<ul>
								{#each section.items as item}
									<li>{item}</li>
								{/each}
							</ul>
						{/if}
					</article>
				{/each}
			</div>
		</div>
	</div>
</section>

<style>
	.v2-rules {
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
		padding: 28px calc(1.6rem + 12px) calc(1.75rem + 12px);
		/* Window art: the supplied gold / blue panel (9-slice) drawn over the padding area. */
		border: 1px solid transparent;
		border-image: var(--ml-panel) 64 fill / 26px stretch;
		border-radius: 0;
		background: none;
		filter: drop-shadow(0 18px 28px rgba(0, 0, 0, 0.5));
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
		z-index: 1;
		width: 100%;
		height: 100%;
		object-fit: contain;
		pointer-events: none;
	}

	.kicker {
		position: relative;
		z-index: 1;
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
		z-index: 1;
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
		font-size: 1.066rem;
		color: #f6ead0;
	}

	.hero p {
		margin: -2px 0 0;
		color: var(--muted);
		font-size: 0.962rem;
		line-height: 1.2;
	}

	.scroll-body {
		position: relative;
		z-index: 2;
		flex: 1 1 auto;
		min-height: 0;
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

	.cards {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.45rem;
	}

	.card {
		position: relative;
		display: grid;
		gap: 0.3rem;
		align-content: start;
		padding: 0.55rem 0.65rem;
		background: rgba(18, 8, 12, 0.72);
		border: 1px solid var(--stroke);
		border-radius: 12px;
		overflow: hidden;
	}

	.card.wide {
		grid-column: 1 / -1;
	}

	.card-header {
		position: relative;
		z-index: 1;
		display: block;
		width: min(100%, 250px);
		height: auto;
		margin: 0 auto;
		object-fit: contain;
		pointer-events: none;
	}

	.card h3,
	.card p,
	.card ul {
		position: relative;
		z-index: 1;
	}

	.card p,
	.card li {
		margin: 0;
		color: #f3e2b8;
		font-size: 0.962rem;
		line-height: 1.4;
	}

	.card ul {
		margin: 0;
		padding-left: 0.95rem;
		display: grid;
		gap: 0.22rem;
		text-align: left;
	}
</style>
