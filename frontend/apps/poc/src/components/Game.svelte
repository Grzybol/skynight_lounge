<script lang="ts">
	import { onMount } from 'svelte';

	import { EnablePixiExtension } from 'components-pixi';
	import { EnableHotkey } from 'components-shared';
	import { App, Text } from 'pixi-svelte';
	import { stateMeta, stateModal, stateUi, stateUrlDerived } from 'state-shared';
	import {
		PLACEHOLDER_IDENTITY,
		PUBLIC_GAME_TITLE,
		ENABLED_MODES as V1_ENABLED_MODES,
	} from '../game/skyjump/config';
	import { V2_ENABLED_MODES } from '../game/skyjump_v2/config';
	import { MODE_BLURBS } from '../game/skyjump_v2/modeBlurbs';

	import { skyjumpCodeBetUi, UI } from 'components-ui-pixi';
	import { GameVersion, Modals } from 'components-ui-html';

	import { getContext } from '../game/context';
	import { installSocialWording } from '../game/socialWording';
	import { loungePhrase, loungeUiArt } from '../game/midnightLoungeTheme';
	import EnableSound from './EnableSound.svelte';
	import EnableGameActor from './EnableGameActor.svelte';
	import ResumeBet from './ResumeBet.svelte';
	import Sound from './Sound.svelte';
	import MidnightLoungeIntro from './MidnightLoungeIntro.svelte';
	import SkyJumpBackground from './skyjump/SkyJumpBackground.svelte';
	import SkyJumpAtmosphere from './skyjump/SkyJumpAtmosphere.svelte';
	import SkyJumpV2Board from './skyjump_v2/SkyJumpV2Board.svelte';
	import SkyJumpV2BuyBonus from './skyjump_v2/SkyJumpV2BuyBonus.svelte';
	import SkyJumpV2PayTable from './skyjump_v2/SkyJumpV2PayTable.svelte';
	import SkyJumpBrand from './skyjump/SkyJumpBrand.svelte';
	import MidnightLoungeBetUI from './midnightLoungeBetUi/MidnightLoungeBetUI.svelte';
	import SkyJumpUtilityBar from './skyjump/SkyJumpUtilityBar.svelte';
	import SkyJumpV2GameRules from './skyjump_v2/SkyJumpV2GameRules.svelte';

	const ENABLED_MODES = V2_ENABLED_MODES.length > 0 ? V2_ENABLED_MODES : V1_ENABLED_MODES;
	const context = getContext();
	stateUi.config.theme = 'skyjump';
	skyjumpCodeBetUi.active = true;
	// Stake auth and the studio loader stay in the root layout. The blue
	// lounge card is not mounted. The entrance screen covers the slot until
	// the player continues.
	context.stateLayout.showLoadingScreen = false;
	context.stateGame.screen = 'play';
	let introAudio = $state(false);
	let introOpen = $state(true);

	const nextMeta: typeof stateMeta.betModeMeta = {};
	for (const mode of ENABLED_MODES) {
		const label = ('label' in mode && mode.label) || ('title' in mode && mode.title) || mode.rgsKey;
		const rawTitle = ('title' in mode && mode.title) || label;
		const present = (value: string) => loungePhrase(value).replaceAll('SkyJump', 'SKYNIGHT LOUNGE');
		const title = present(String(rawTitle));
		nextMeta[mode.rgsKey] = {
			mode: mode.rgsKey,
			costMultiplier: mode.costMultiplier,
			type: mode.type,
			parent: '',
			children: '',
			assets: {
				icon: '',
				volatility: '',
				button: '',
				dialogImage: '',
				dialogVolatility: '',
			},
			maxWin: mode.maxWin,
			text: {
				title,
				dialog: present(('dialog' in mode && mode.dialog) || `${title} feature buy`),
				description: present(MODE_BLURBS[mode.rgsKey] ?? (('description' in mode && mode.description) || title)),
				button: present(('button' in mode && mode.button) || title),
				betAmountLabel: present(
					('betAmountLabel' in mode && mode.betAmountLabel) || `${title} bet`,
				),
				tickerIdle: present(('tickerIdle' in mode && mode.tickerIdle) || title),
				tickerSpin: present(('tickerSpin' in mode && mode.tickerSpin) || title),
				bannerText: '',
			},
		};
	}
	stateMeta.betModeMeta = nextMeta;
	stateMeta.gameRuleMeta = { payTable: [], gameRules: [], splashScreen: [] };

	onMount(() => {
		document.body.classList.add('theme-skyjump');
		// A url() inside a custom property resolves against the stylesheet that uses it (/_app/immutable/assets/ in the
		// build), so the paths must be absolute.
		const abs = (path: string) => `url("${new URL(path, document.baseURI).href}")`;
		document.body.style.setProperty('--ml-panel', abs(loungeUiArt.panel));
		document.body.style.setProperty('--ml-button', abs(loungeUiArt.button));
		document.body.style.setProperty('--ml-square', abs(loungeUiArt.square));
		document.body.style.setProperty('--ml-minus', abs(loungeUiArt.minus));
		document.body.style.setProperty('--ml-plus', abs(loungeUiArt.plus));
		// social=true: restricted words are replaced everywhere the player can read them.
		const stopSocial = stateUrlDerived.social() ? installSocialWording() : undefined;

		return () => {
			stopSocial?.();
			document.body.classList.remove('theme-skyjump');
			for (const name of ['--ml-panel', '--ml-button', '--ml-square', '--ml-minus', '--ml-plus']) document.body.style.removeProperty(name);
		};
	});

	context.eventEmitter.subscribeOnMount({
		buyBonusConfirm: () => {
			stateModal.modal = { name: 'buyBonusConfirm' };
		},
	});
</script>

<svelte:head>
	<title>{PUBLIC_GAME_TITLE}</title>
</svelte:head>

<div class="skyjump-viewport" data-phase={context.stateGame.presentationPhase}>
	<SkyJumpBackground />
	<MidnightLoungeBetUI />
	<SkyJumpUtilityBar />
	<div class="win-dim" aria-hidden="true"></div>
	<App>
		{#if introAudio}
			<EnableSound />
		{/if}
		{#if context.stateGame.screen === 'play' && !introOpen}
			<EnableHotkey />
		{/if}
		<EnableGameActor />
		<EnablePixiExtension />

		<ResumeBet />
		<Sound />
		<UI>
			{#snippet gameName()}
				<Text text="" style={{ fontSize: 1, fill: 0x000000 }} />
			{/snippet}
			{#snippet logo()}
				<Text text="" style={{ fontSize: 1, fill: 0x000000 }} />
			{/snippet}
		</UI>
	</App>

	{#if introOpen}
		<MidnightLoungeIntro
			onunlock={() => (introAudio = true)}
			ondone={() => {
				introOpen = false;
				context.eventEmitter.broadcast({ type: 'uiShow' });
			}}
		/>
	{/if}

	<SkyJumpAtmosphere />
	<SkyJumpBrand />
	<SkyJumpV2Board />

	<Modals>
		{#snippet version()}
			<GameVersion version={`SKYNIGHT LOUNGE ${PLACEHOLDER_IDENTITY.version.replace('-skyjump', '')}`} />
		{/snippet}
		{#snippet payTable()}
			<SkyJumpV2PayTable />
		{/snippet}
		{#snippet gameRules()}
			<SkyJumpV2GameRules />
		{/snippet}
		{#snippet buyBonus()}
			<SkyJumpV2BuyBonus />
		{/snippet}
	</Modals>
</div>

<style>
	.skyjump-viewport {
		position: relative;
		isolation: isolate;
		width: 100%;
		height: 100%;
		min-height: 100dvh;
		overflow: hidden;
		background: #071526;
	}

	.skyjump-viewport :global(canvas) {
		position: relative;
		z-index: 19;
	}

	.skyjump-viewport :global(.pop-up-wrap) {
		z-index: 200 !important;
	}

	/*
	 * Info, paytable, settings, bet menu and buy bonus: Luckiest Guy (one weight, bold by design). The white bold captions under the section headers (h2/h3) keep theirs.
	 */
	.skyjump-viewport :global(.pop-up-wrap) {
		--skyjump-font-display: 'Luckiest Guy', 'Cinzel', Georgia, 'Times New Roman', serif;
		--skyjump-font-ui: 'Luckiest Guy', 'Cinzel', Georgia, 'Times New Roman', serif;
		--skyjump-font-sans: 'Luckiest Guy', 'Cinzel', Georgia, 'Times New Roman', serif;
	}

	.skyjump-viewport :global(.pop-up-wrap *:not(h2):not(h3)) {
		font-family: 'Luckiest Guy', 'Cinzel', Georgia, 'Times New Roman', serif;
		font-weight: 700;
	}

	/*
	 * Big win and above: no blur. A light dimming layer fades in over the whole screen (scene, slot,
	 * characters and BetUI) while the celebration, which sits above it, plays. `data-win-plate` is set
	 * for the whole celebration. The BetUI is inert meanwhile (see MidnightLoungeBetUI).
	 */
	.win-dim {
		position: absolute;
		inset: 0;
		z-index: 21;
		background: rgba(6, 2, 8, 0.38);
		opacity: 0;
		pointer-events: none;
		transition: opacity 700ms ease;
	}

	:global(.skyjump-viewport[data-win-plate]) .win-dim {
		opacity: 1;
	}
</style>
