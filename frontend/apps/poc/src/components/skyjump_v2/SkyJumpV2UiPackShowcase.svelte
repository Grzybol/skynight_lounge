<script lang="ts">
	/**
	 * DEV-only: mounts real Phase 8C production components with forced props.
	 * Not a static <img> dump — uses WinCelebration / TitleBanner / StatusPlate / ModeBadge / PanelDecor.
	 */
	import { v2ModeTitleUrl, v2UiAssetUrl } from '../../game/skyjump_v2/uiAssetRegistry';
	import type { V2WinCelebrationTier } from '../../game/skyjump_v2/winPresentation';
	import SkyJumpV2ModeBadge from './SkyJumpV2ModeBadge.svelte';
	import SkyJumpV2PanelDecor from './SkyJumpV2PanelDecor.svelte';
	import SkyJumpV2StatusPlate from './SkyJumpV2StatusPlate.svelte';
	import SkyJumpV2TitleBanner from './SkyJumpV2TitleBanner.svelte';
	import SkyJumpV2WinCelebration from './SkyJumpV2WinCelebration.svelte';
	import { syncLoungeFigureWin } from '../../game/loungeCharacters/loungeWinCue';

	type ShowcaseId =
		| 'big'
		| 'mega'
		| 'super'
		| 'max'
		| 'worldRecord'
		| 'fs'
		| 'retrigger'
		| 'tierUpgrade'
		| 'modeLH'
		| 'modeSF'
		| 'modeWC'
		| 'modePV'
		| 'status'
		| 'modeBadge'
		| 'decor';

	type Props = {
		focus?: ShowcaseId | '';
	};

	const props: Props = $props();

	const CELEBRATIONS: { id: ShowcaseId; tier: V2WinCelebrationTier; amount: number; wr?: boolean }[] =
		[
			{ id: 'big', tier: 'big', amount: 12.5 },
			{ id: 'mega', tier: 'mega', amount: 64 },
			{ id: 'super', tier: 'super', amount: 220 },
			{ id: 'max', tier: 'max', amount: 50000 },
			{ id: 'worldRecord', tier: 'worldRecord', amount: 50000, wr: true },
		];

	const BANNERS: { id: ShowcaseId; src: string; label: string }[] = [
		{ id: 'fs', src: v2UiAssetUrl('bonusFreeSpins'), label: 'FREE SPINS' },
		{ id: 'retrigger', src: v2UiAssetUrl('bonusRetrigger'), label: 'RETRIGGER' },
		{ id: 'tierUpgrade', src: v2UiAssetUrl('bonusTierUpgrade'), label: 'TIER UPGRADE' },
		{ id: 'modeLH', src: v2ModeTitleUrl('LARGE_HILL')!, label: 'VELVET ROOM' },
		{ id: 'modeSF', src: v2ModeTitleUrl('SKI_FLYING')!, label: 'GOLD ROOM' },
		{ id: 'modeWC', src: v2ModeTitleUrl('WORLD_CUP')!, label: 'DIAMOND LOUNGE' },
		{ id: 'modePV', src: v2ModeTitleUrl('PERFECT_V')!, label: 'MIDNIGHT SUITE' },
	];

	let activeCelebration = $state<ShowcaseId>('big');
	let activeBanner = $state<ShowcaseId>('fs');
	let bannerShow = $state(true);

	$effect(() => {
		const focus = props.focus ?? '';
		if (!focus) return;
		if (CELEBRATIONS.some((c) => c.id === focus)) activeCelebration = focus;
		if (BANNERS.some((b) => b.id === focus)) {
			activeBanner = focus;
			bannerShow = true;
		}
	});

	const celebration = $derived(
		CELEBRATIONS.find((c) => c.id === activeCelebration) ?? CELEBRATIONS[0]!,
	);

	$effect(() => {
		syncLoungeFigureWin(true, celebration.tier);
		return () => {
			syncLoungeFigureWin(false, celebration.tier);
		};
	});
	const banner = $derived(BANNERS.find((b) => b.id === activeBanner) ?? BANNERS[0]!);
</script>

{#if import.meta.env.DEV}
	<section class="showcase" data-test="skyjump-v2-ui-pack-showcase">
		<h3>UI PACK SHOWCASE (production components)</h3>

		<div class="row">
			<span>Win celebration</span>
			{#each CELEBRATIONS as c}
				<button
					type="button"
					class:on={activeCelebration === c.id}
					onclick={() => (activeCelebration = c.id)}>{c.id}</button
				>
			{/each}
		</div>

		<div class="stage celebration-stage">
			<SkyJumpV2WinCelebration
				show={true}
				tier={celebration.tier}
				amount={celebration.amount}
				worldRecordOverlay={Boolean(celebration.wr)}
				turbo={true}
			/>
		</div>

		<div class="row">
			<span>Title banner</span>
			{#each BANNERS as b}
				<button
					type="button"
					class:on={activeBanner === b.id}
					onclick={() => {
						activeBanner = b.id;
						bannerShow = true;
					}}>{b.label}</button
				>
			{/each}
		</div>

		<div class="stage banner-stage">
			<SkyJumpV2TitleBanner src={banner.src} show={bannerShow} />
		</div>

		<div class="row plates">
			<div class="plate-demo">
				<p>Status plate</p>
				<SkyJumpV2StatusPlate label="TOTAL WIN" sub="12.5x" />
			</div>
			<div class="plate-demo">
				<p>Mode badge</p>
				<SkyJumpV2ModeBadge label="LARGE HILL" />
			</div>
			<div class="plate-demo decor-demo">
				<p>Panel decor</p>
				<div class="decor-box">
					<SkyJumpV2PanelDecor />
					<span>checker sample</span>
				</div>
			</div>
		</div>
	</section>
{/if}

<style>
	.showcase {
		margin-top: 0.75rem;
		padding: 0.65rem;
		color: #d7ecf8;
		background: rgba(4, 18, 36, 0.94);
		border: 1px solid rgba(120, 200, 255, 0.35);
		border-radius: 12px;
		font: 600 11px/1.3 var(--skyjump-font-ui, system-ui, sans-serif);
		max-height: 55vh;
		overflow: auto;
	}

	h3 {
		margin: 0 0 0.5rem;
		font-family: var(--skyjump-font-display, system-ui, sans-serif);
	}

	.row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		align-items: center;
		margin-bottom: 0.45rem;
	}

	button {
		color: #f4faff;
		background: #10283d;
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 6px;
		padding: 2px 6px;
		cursor: pointer;
	}

	button.on {
		background: #1d4f72;
		border-color: #7fd0ff;
	}

	.stage {
		position: relative;
		min-height: 160px;
		margin-bottom: 0.65rem;
		border-radius: 10px;
		overflow: hidden;
		background:
			linear-gradient(45deg, #0a1c30 25%, transparent 25%) 0 0 / 16px 16px,
			linear-gradient(-45deg, #0a1c30 25%, transparent 25%) 0 8px / 16px 16px,
			linear-gradient(45deg, transparent 75%, #0a1c30 75%) 8px -8px / 16px 16px,
			linear-gradient(-45deg, transparent 75%, #0a1c30 75%) -8px 0 / 16px 16px,
			#14324c;
	}

	.celebration-stage {
		min-height: 220px;
	}

	.banner-stage {
		min-height: 120px;
	}

	.plates {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 0.55rem;
	}

	.plate-demo p {
		margin: 0 0 0.35rem;
		color: #9fd6ff;
	}

	.decor-box {
		position: relative;
		min-height: 110px;
		padding: 1.5rem 0.75rem;
		border: 1px solid rgba(120, 200, 255, 0.3);
		border-radius: 10px;
		overflow: hidden;
		background: #0c2238;
		text-align: center;
	}

	.decor-box span {
		position: relative;
		z-index: 1;
	}
</style>
