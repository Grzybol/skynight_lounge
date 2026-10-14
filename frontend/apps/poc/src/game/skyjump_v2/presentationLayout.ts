/**
 * Phase 8E — presentation placement / scale constants for 1280×720 primary.
 * Visual only. Does not change math, assets, or economics.
 */

import type { V2WinCelebrationTier } from './winPresentation';

/** Shared win-title family wrapper (px at logical 1280×720). */
export const V2_WIN_TITLE_SLOT = {
	maxWidth: 520,
	/** Fixed slot height — contain lettering, ignore source canvas padding. */
	slotHeight: 148,
} as const;

/** Mild intensity scale — no huge jumps between tiers. */
export const v2WinTitleScale = (tier: V2WinCelebrationTier): number => {
	switch (tier) {
		case 'big':
			return 0.9;
		case 'mega':
			return 0.96;
		case 'super':
			return 1;
		case 'max':
			return 1.06;
		case 'worldRecord':
			return 1.12;
		default:
			return 1;
	}
};

/** Bonus / mode banner presentation slots (shared geometry per kind). */
export const V2_BANNER_SLOT = {
	bonus: { maxWidth: 480, maxHeight: 132 },
	retrigger: { maxWidth: 360, maxHeight: 100 },
	tierUpgrade: { maxWidth: 500, maxHeight: 140 },
	mode: { maxWidth: 460, maxHeight: 124 },
} as const;

export type V2BannerKind = keyof typeof V2_BANNER_SLOT;

/** Payline FX visible display sizes at 1280 (source canvases ~1254² — padded). */
export const V2_PAYLINE_FX = {
	/** Keep spark modest vs ~2.4–4.5px stroke. */
	sparkPx: 30,
	/** End glint sits on the last node — slightly larger than spark, not a giant icon. */
	endGlintPx: 36,
} as const;

/** Status plate under board — substantial banner (~2× prior thin strip). */
export const V2_STATUS_PLATE = {
	minHeight: 100,
	maxHeight: 112,
} as const;

/**
 * Drop-in slot for later Midnight Lounge header art (E01–E04).
 * The image is object-fit contain inside this box. Slot is 460×74 so the plaque clears the line under it.
 */
export const V2_MODAL_HEADER = {
	maxWidth: 460,
	maxHeight: 74,
} as const;

/**
 * Panel decoration. Corner master is the full 1254² L-frame
 * (diamond at the top-left, arms running right and down).
 */
export const V2_PANEL_DECOR = {
	topperMaxWidth: 640,
	topperMaxHeight: 72,
	/**
	 * Shaft center of the topper's left/right spikes, in the 72px-tall face,
	 * plus half the 1.5px panel stroke. Parks those spikes on the top border.
	 */
	topperOutY: 45,
	/** 70% of the previous 188px face. Full 1254² L-frame, not a crop. */
	cornerHeight: 132,
	cornerAspect: 1,
	/**
	 * Shaft centerlines of the 132px L-frame (horiz ~37px, vert ~32px)
	 * plus half the 1.5px panel stroke, so each arm sits on the border.
	 */
	cornerOutX: 33,
	cornerOutY: 38,
	dividerMaxWidth: 320,
	/** Shift the paytable/info card down without growing it downward. */
	panelShiftY: 28,
	/** Extra panel height, applied downward at the fixed 720 stage. */
	panelExtraDown: 56,
} as const;

/**
 * Closed slot-board frame (`ui_slot_board_frame.png`). Hole fractions are the
 * innermost colored pixels so side diamonds and crests stay outside the 5×5.
 * Scale 1 keeps that hole on the grid — about 6% tighter than the previous 1.078.
 */
/**
 * `slot_background_1.png` (1448x1086, "Gotycka rama inwentarza z różami"): 25 hand-drawn windows of about 133 x 128 art px.
 * Their measured centres deviate from an even 167 x 162.4 pitch by at most ~3 px, so the grid is snapped to an even one (a tile
 * then has the same offset in every cell and nothing shifts when a reel stops). Drawn as one piece (SlotFrameLayer, one band).
 */
export const V2_FRAME_BANDS = {
	srcH: 1086,
	outH: 1086,
	bands: [{ srcStart: 0, srcEnd: 1086, outStart: 0, outEnd: 1086 }],
} as const;

const ART = { w: 1448, h: 1086 };
const PITCH = { w: 167, h: 162.4 };
const WIN = { w: 133, h: 128 };
/** First window's top-left corner in the art. */
const FIRST = { x: 389.1 - WIN.w / 2, y: 258.9 - WIN.h / 2 };
const GRID_ORIGIN = { x: FIRST.x - (PITCH.w - WIN.w) / 2, y: FIRST.y - (PITCH.h - WIN.h) / 2 };

export const V2_SLOT_BOARD_FRAME = {
	/** Playfield: the 5x5 block of pitches around the windows, as fractions of the art. */
	holeLeft: GRID_ORIGIN.x / ART.w,
	holeRight: (GRID_ORIGIN.x + 5 * PITCH.w) / ART.w,
	holeTop: GRID_ORIGIN.y / ART.h,
	holeBottom: (GRID_ORIGIN.y + 5 * PITCH.h) / ART.h,
	scale: 1,
	cellAspect: PITCH.w / PITCH.h,
} as const;

/** The frame's windows in art pixels. */
export const V2_FRAME_WINDOWS = {
	art: ART,
	origin: GRID_ORIGIN,
	pitch: PITCH,
	colX: [0, 1, 2, 3, 4].map((i) => FIRST.x + PITCH.w * i),
	rowY: [0, 1, 2, 3, 4].map((i) => FIRST.y + PITCH.h * i),
	/** Window size, art px. */
	winW: WIN.w,
	winH: WIN.h,
	/** Tier tiles and the default window background are drawn this much larger than the window, under the frame lattice. */
	tileGrow: 1.14,
} as const;

/** Window height / cell height: the symbol box is a whole cell, the visible window is smaller. */
const WINDOW_FIT = WIN.h / PITCH.h;

/**
 * Symbol height by tier as a fraction of the frame WINDOW height. Steps between regular tiers are 5 %
 * (low -> medium -> premium), all +5 % on the previous pass; scatter, Concierge / Mystery and feature symbols match premium.
 */
export const V2_TIER_SCALE: Record<string, number> = {
	low: 0.84 * WINDOW_FIT,
	medium: 0.882 * WINDOW_FIT,
	premium: 0.924 * WINDOW_FIT,
	scatter: 0.924 * WINDOW_FIT,
	concierge_mystery: 0.924 * WINDOW_FIT,
	feature: 0.924 * WINDOW_FIT,
};
