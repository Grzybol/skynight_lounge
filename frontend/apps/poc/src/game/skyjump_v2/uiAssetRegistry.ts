/**
 * Canonical V2 UI / overlay / FX asset URLs.
 * Runtime: frontend/apps/poc/static/assets/skyjump_v2/{ui,overlays,fx}/…
 * Masters: assets/skyjump_v2/source/
 *
 * Phase 8C.1: all pack files are PNG RGBA (true alpha). No JPEG runtime UI pack.
 */

import { resolveGameAsset } from '../resolveGameAsset';

export const V2_UI_RUNTIME_DIR = 'assets/skyjump_v2/ui';
export const V2_OVERLAY_RUNTIME_DIR = 'assets/skyjump_v2/overlays';
export const V2_FX_RUNTIME_DIR = 'assets/skyjump_v2/fx';

/** Legacy UI root files (logo, stages, tier emblems). */
export const V2_UI_ROOT_FILENAMES = {
	logo: 'ui_logo_skyjump.png',
	stageRunUp: 'ui_stage_run_up.png',
	stageTakeoff: 'ui_stage_takeoff.png',
	stageFlight: 'ui_stage_flight.png',
	tierLargeHill: 'ui_tier_large_hill.png',
	tierSkiFlying: 'ui_tier_ski_flying.png',
	tierWorldCup: 'ui_tier_world_cup.png',
	tierPerfectV: 'ui_tier_perfect_v.png',
	overlayWorldRecord: 'ui_overlay_world_record.png',
} as const;

/** Phase 8C win title masters (baked text; amounts stay code-rendered). */
export const V2_WIN_TITLE_FILENAMES = {
	winBig: 'wins/ui_win_big.png',
	winMega: 'wins/ui_win_mega.png',
	winSuper: 'wins/ui_win_super.png',
	winMax: 'wins/ui_win_max.png',
	winWorldRecord: 'wins/ui_win_world_record.png',
} as const;

/** Bonus entry / retrigger / upgrade + mode title banners. */
export const V2_BONUS_TITLE_FILENAMES = {
	bonusFreeSpins: 'bonus/ui_bonus_free_spins.png',
	bonusRetrigger: 'bonus/ui_bonus_retrigger.png',
	bonusTierUpgrade: 'bonus/ui_bonus_tier_upgrade.png',
	modeLargeHill: 'bonus/ui_mode_large_hill.png',
	modeSkiFlying: 'bonus/ui_mode_ski_flying.png',
	modeWorldCup: 'bonus/ui_mode_world_cup.png',
	modePerfectV: 'bonus/ui_mode_perfect_v.png',
} as const;

/** Menu / panel section headers. */
export const V2_HEADER_FILENAMES = {
	headerPaytable: 'headers/ui_header_paytable.png',
	headerInfo: 'headers/ui_header_info.png',
	headerFeatures: 'headers/ui_header_features.png',
	headerHowToPlay: 'headers/ui_header_how_to_play.png',
} as const;

/** Panel decoration plates. */
export const V2_DECOR_FILENAMES = {
	dividerIce: 'decor/ui_divider_ice.png',
	cornerOrnament: 'decor/ui_corner_ornament.png',
	statusPlate: 'decor/ui_status_plate.png',
	modeBadgePlate: 'decor/ui_mode_badge_plate.png',
	panelTopper: 'decor/ui_panel_topper.png',
	/** BET HUD control faces (transparent PNG). */
	betuiSpin: 'betui/betui_spin_button.png',
	betuiBuyBonus: 'betui/betui_buy_bonus_button.png',
	betuiAuto: 'betui/betui_auto_button.png',
	betuiTurbo: 'betui/betui_turbo_button.png',
	/** Optional — wire when asset lands. */
	betuiMenu: 'betui/betui_menu_button.png',
	/** BET HUD chrome — wings + central SPIN seat (transparent PNG). */
	betHudFrame: 'decor/ui_bet_hud_frame.png',
	/** 5×5 slot board ornate ice/gold frame (transparent center). */
	slotBoardFrame: 'decor/ui_slot_board_frame.png',
} as const;

/** FX sprites (motion owned by code). */
export const V2_FX_FILENAMES = {
	paylineSparkHead: 'fx_payline_spark_head.png',
	paylineEndGlint: 'fx_payline_end_glint.png',
	iceGlint: 'fx_ice_glint.png',
	snowBurst: 'fx_snow_burst.png',
	winGlowRing: 'fx_win_glow_ring.png',
	screenFlashAccent: 'fx_screen_flash_accent.png',
	smallSparkle: 'fx_small_sparkle.png',
	coinSparkle: 'fx_coin_sparkle.png',
} as const;

export const V2_UI_FILENAMES = {
	...V2_UI_ROOT_FILENAMES,
	...V2_WIN_TITLE_FILENAMES,
	...V2_BONUS_TITLE_FILENAMES,
	...V2_HEADER_FILENAMES,
	...V2_DECOR_FILENAMES,
} as const;

export type V2UiKey = keyof typeof V2_UI_FILENAMES;
export type V2FxKey = keyof typeof V2_FX_FILENAMES;

export const V2_PHASE8C_EXPECTED_KEYS = [
	...Object.keys(V2_WIN_TITLE_FILENAMES),
	...Object.keys(V2_BONUS_TITLE_FILENAMES),
	...Object.keys(V2_HEADER_FILENAMES),
	...Object.keys(V2_DECOR_FILENAMES),
	...Object.keys(V2_FX_FILENAMES),
] as const;

const LOUNGE_UI_ROOT = 'assets/midnight-lounge';

/** Presentation overrides. Keys absent here keep the SkyJump file. */
const LOUNGE_UI_URL: Partial<Record<V2UiKey, string>> = {
	logo: `${LOUNGE_UI_ROOT}/ui/ui_logo_midnight_lounge.png`,
	slotBoardFrame: `${LOUNGE_UI_ROOT}/ui/decor/ui_slot_board_frame_midnight_lounge.png`,
	stageRunUp: `${LOUNGE_UI_ROOT}/ui/ui_stage_arrival.png`,
	stageTakeoff: `${LOUNGE_UI_ROOT}/ui/ui_stage_vip_entry.png`,
	stageFlight: `${LOUNGE_UI_ROOT}/ui/ui_stage_inner_lounge.png`,
	tierLargeHill: `${LOUNGE_UI_ROOT}/ui/ui_tier_velvet_room.png`,
	tierSkiFlying: `${LOUNGE_UI_ROOT}/ui/ui_tier_gold_room.png`,
	tierWorldCup: `${LOUNGE_UI_ROOT}/ui/ui_tier_diamond_lounge.png`,
	tierPerfectV: `${LOUNGE_UI_ROOT}/ui/ui_tier_midnight_suite.png`,
	modeLargeHill: `${LOUNGE_UI_ROOT}/ui/bonus/ui_mode_velvet_room.png`,
	modeSkiFlying: `${LOUNGE_UI_ROOT}/ui/bonus/ui_mode_gold_room.png`,
	modeWorldCup: `${LOUNGE_UI_ROOT}/ui/bonus/ui_mode_diamond_lounge.png`,
	modePerfectV: `${LOUNGE_UI_ROOT}/ui/bonus/ui_mode_midnight_suite.png`,
	winBig: `${LOUNGE_UI_ROOT}/ui/wins/ui_win_big_midnight_lounge.png`,
	winMega: `${LOUNGE_UI_ROOT}/ui/wins/ui_win_mega_midnight_lounge.png`,
	winSuper: `${LOUNGE_UI_ROOT}/ui/wins/ui_win_super_midnight_lounge.png`,
	winMax: `${LOUNGE_UI_ROOT}/ui/wins/ui_win_max_midnight_lounge.png`,
	winWorldRecord: `${LOUNGE_UI_ROOT}/ui/wins/ui_win_royal_midnight_lounge.png`,
	bonusFreeSpins: `${LOUNGE_UI_ROOT}/ui/bonus/ui_bonus_free_spins_midnight_lounge.png`,
	bonusRetrigger: `${LOUNGE_UI_ROOT}/ui/bonus/ui_bonus_retrigger_midnight_lounge.png`,
	bonusTierUpgrade: `${LOUNGE_UI_ROOT}/ui/bonus/ui_bonus_tier_upgrade_midnight_lounge.png`,
	betuiSpin: `${LOUNGE_UI_ROOT}/ui/betui/betui_spin_button_midnight_lounge.png`,
	betuiAuto: `${LOUNGE_UI_ROOT}/ui/betui/betui_auto_button_midnight_lounge.png`,
	betuiTurbo: `${LOUNGE_UI_ROOT}/ui/betui/betui_turbo_button_midnight_lounge.png`,
	modeBadgePlate: `${LOUNGE_UI_ROOT}/ui/ui_buy_bonus_badge.png`,
	// World record: the royal plate in the lounge palette (the SkyJump ice crystal plate is gone).
	overlayWorldRecord: `${LOUNGE_UI_ROOT}/overlays/ui_overlay_royal_midnight_lounge.png`,
};

export const v2UiAssetUrl = (key: V2UiKey): string => {
	const lounge = LOUNGE_UI_URL[key];
	if (lounge) return resolveGameAsset(lounge);
	const file = V2_UI_FILENAMES[key];
	if (key === 'overlayWorldRecord') {
		return resolveGameAsset(`${V2_OVERLAY_RUNTIME_DIR}/${file}`);
	}
	return resolveGameAsset(`${V2_UI_RUNTIME_DIR}/${file}`);
};

/** Lounge-palette FX. The SkyJump ice-blue sprites are gone: glints use the ruby-gold glint, bursts the gold burst. */
const LOUNGE_FX_URL: Partial<Record<V2FxKey, string>> = {
	iceGlint: `${LOUNGE_UI_ROOT}/fx/fx_glint_ruby_gold.png`,
	paylineSparkHead: `${LOUNGE_UI_ROOT}/fx/fx_glint_ruby_gold.png`,
	paylineEndGlint: `${LOUNGE_UI_ROOT}/fx/fx_glint_ruby_gold.png`,
	smallSparkle: `${LOUNGE_UI_ROOT}/fx/fx_glint_ruby_gold.png`,
	snowBurst: `${LOUNGE_UI_ROOT}/fx/fx_luxury_burst_gold.png`,
	winGlowRing: `${LOUNGE_UI_ROOT}/fx/fx_luxury_burst_gold.png`,
	screenFlashAccent: `${LOUNGE_UI_ROOT}/fx/fx_luxury_burst_gold.png`,
};

export const v2FxAssetUrl = (key: V2FxKey): string => {
	const lounge = LOUNGE_FX_URL[key];
	if (lounge) return resolveGameAsset(lounge);
	return resolveGameAsset(`${V2_FX_RUNTIME_DIR}/${V2_FX_FILENAMES[key]}`);
};

/** Shared win plates. One file per family, not one copy per tier. */
export const v2WinSceneOverlayUrl = (tier: string): string | null => {
	if (tier === 'big' || tier === 'mega') {
		return resolveGameAsset(`${LOUNGE_UI_ROOT}/overlays/ui_overlay_win_soft_midnight_lounge.png`);
	}
	if (tier === 'super' || tier === 'max') {
		return resolveGameAsset(`${LOUNGE_UI_ROOT}/overlays/ui_overlay_win_grand_midnight_lounge.png`);
	}
	if (tier === 'worldRecord') {
		return resolveGameAsset(`${LOUNGE_UI_ROOT}/overlays/ui_overlay_royal_midnight_lounge.png`);
	}
	return null;
};

/** Bonus tier → emblem art. Event tier string is authoritative; filename is never inferred for logic. */
export const v2TierEmblemUrl = (tier: string | null | undefined): string | null => {
	switch (tier) {
		case 'LARGE_HILL':
			return v2UiAssetUrl('tierLargeHill');
		case 'SKI_FLYING':
			return v2UiAssetUrl('tierSkiFlying');
		case 'WORLD_CUP':
			return v2UiAssetUrl('tierWorldCup');
		case 'PERFECT_V':
			return v2UiAssetUrl('tierPerfectV');
		default:
			return null;
	}
};

/** Mode title banner for FS entry / upgrade sequence (large titles, not HUD emblems). */
export const v2ModeTitleUrl = (tier: string | null | undefined): string | null => {
	switch (tier) {
		case 'LARGE_HILL':
			return v2UiAssetUrl('modeLargeHill');
		case 'SKI_FLYING':
			return v2UiAssetUrl('modeSkiFlying');
		case 'WORLD_CUP':
			return v2UiAssetUrl('modeWorldCup');
		case 'PERFECT_V':
			return v2UiAssetUrl('modePerfectV');
		default:
			return null;
	}
};

export const V2_STAGE_ICON_URLS = {
	RUN_UP: v2UiAssetUrl('stageRunUp'),
	TAKEOFF: v2UiAssetUrl('stageTakeoff'),
	FLIGHT: v2UiAssetUrl('stageFlight'),
} as const;

export const V2_WIN_TITLE_URLS = {
	big: v2UiAssetUrl('winBig'),
	mega: v2UiAssetUrl('winMega'),
	super: v2UiAssetUrl('winSuper'),
	max: v2UiAssetUrl('winMax'),
	worldRecord: v2UiAssetUrl('winWorldRecord'),
} as const;
