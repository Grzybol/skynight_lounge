/**
 * SkyJump BetUI face art — keys match `frontend/apps/poc/src/game/assets.ts`.
 * Circle frac = main SPIN disc diameter / asset size (spikes ignored).
 */
export const SKYJUMP_BETUI_ART = {
	spin: 'betuiSpin',
	buyBonus: 'betuiBuyBonus',
	auto: 'betuiAuto',
	turbo: 'betuiTurbo',
	menu: 'betuiMenu',
	tile: 'betuiTile',
	plus: 'betuiPlus',
	minus: 'betuiMinus',
	stop: 'betuiStop',
	language: 'betuiLanguage',
	soundOff: 'betuiSoundOff',
	soundOn: 'betuiSoundOn',
	info: 'betuiInfo',
	paytable: 'betuiPaytable',
	settings: 'betuiSettings',
	menuExit: 'betuiMenuExit',
} as const;

/** `betui_language_button.png` is 1024×512. The flyout hit box keeps that ratio. */
export const SKYJUMP_LANGUAGE_ASPECT = 1024 / 512;

/** Square menu faces fill the side hit box (PNG keeps a transparent matte). */
export const SKYJUMP_MENU_ICON_FIT = 1.18;

/** `betui_menu_exit_button.png` is 1024×682. The face keeps that ratio. */
export const SKYJUMP_MENU_EXIT_ASPECT = 1024 / 682;

const FLYOUT_ART = {
	payTable: SKYJUMP_BETUI_ART.paytable,
	info: SKYJUMP_BETUI_ART.info,
	settings: SKYJUMP_BETUI_ART.settings,
	soundOn: SKYJUMP_BETUI_ART.soundOn,
	soundOff: SKYJUMP_BETUI_ART.soundOff,
	menuExit: SKYJUMP_BETUI_ART.menuExit,
	language: SKYJUMP_BETUI_ART.language,
} as const;

export const skyjumpFlyoutArtKey = (icon: string) =>
	icon in FLYOUT_ART ? FLYOUT_ART[icon as keyof typeof FLYOUT_ART] : null;

/** Main circular SPIN body diameter as a fraction of the square asset. */
export const SKYJUMP_SPIN_CIRCLE_FRAC = 0.9043;

/**
 * Extra visual scale on the fitted face (1280 polish).
 * SPIN 1.2075×1.05. BUY/AUTO 1.2×1.05. TURBO width 1.15×1.05 and height +5%. MENU 1.17×1.05.
 */
export const SKYJUMP_BETUI_FACE_SCALE = {
	spin: 1.267875,
	buy: 1.26,
	auto: 1.26,
	turboW: 1.2075,
	turboH: 1.05,
	menu: 1.2285,
} as const;

/** Portrait/banner fit before the polish scale (chrome overhang vs hit box). */
export const SKYJUMP_BETUI_FACE_FIT = {
	buyW: 1.08,
	buyH: 1.35,
	modeW: 1.12,
	modeH: 1.42,
} as const;

/** Opaque pill fills the cluster box (asset keeps vertical transparent matte). */
export const SKYJUMP_BETUI_TILE_FIT = { w: 1.034, h: 1.712 } as const;

/** Balance/Win tile wider left-right only. Extra width goes left so the BET gap stays. */
export const SKYJUMP_INFO_TILE_WIDTH_SCALE = 1.07;

/** Crystal +/- frame fills the square hit box. */
export const SKYJUMP_BETUI_GLYPH_FIT = 1.44;

/**
 * Shift BUY so its opaque edge sits the same distance from AUTO as AUTO/TURBO/MENU
 * sit from each other (~23 layout px / ~15 CSS px). Negative = left of the packed slot.
 */
export const SKYJUMP_BUY_NUDGE_X = -19;

/** Drop BUY / AUTO / TURBO / MENU ~5 CSS px at 1280 (scale 2/3 → 7.5 layout). */
export const SKYJUMP_SIDE_NUDGE_Y = 7.5;

/** Scale the full spin asset so its circle matches the layout SPIN diameter, then +15%. */
export const skyjumpSpinArtSize = (spinDiameter: number) =>
	(spinDiameter / SKYJUMP_SPIN_CIRCLE_FRAC) * SKYJUMP_BETUI_FACE_SCALE.spin;
