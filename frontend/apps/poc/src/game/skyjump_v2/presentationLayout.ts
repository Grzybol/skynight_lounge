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
/** Row cut lines in the 1672x941 frame art (centre of the gold line between two windows), art px. */
const CUTS = [87.5, 225.5, 361.5, 495.5, 626.5, 753.5] as const;
/** Every row band is stretched to this height (mean of the five art rows 138 / 136 / 134 / 131 / 127). */
const ROW_T = (CUTS[5] - CUTS[0]) / 5;

/**
 * The frame art's rows are not equally tall, so it is redrawn as bands (see SlotFrameLayer.svelte):
 * a top piece, five row bands stretched to the same height, and a bottom piece. Output height = source height.
 */
export const V2_FRAME_BANDS = {
	srcH: 941,
	outH: 941,
	bands: [
		{ srcStart: 0, srcEnd: CUTS[0], outStart: 0, outEnd: CUTS[0] },
		...[0, 1, 2, 3, 4].map((k) => ({
			srcStart: CUTS[k],
			srcEnd: CUTS[k + 1],
			outStart: CUTS[0] + k * ROW_T,
			outEnd: CUTS[0] + (k + 1) * ROW_T,
		})),
		{ srcStart: CUTS[5], srcEnd: 941, outStart: CUTS[5], outEnd: 941 },
	],
} as const;

export const V2_SLOT_BOARD_FRAME = {
	/**
	 * `slot_background_1/2.png` (1672x941, 5x5 windows). After the row equalisation the playfield is a
	 * uniform 5x5 grid of 163.25 x 133.2 art px cells starting at (428.9, 87.5).
	 */
	holeLeft: 0.2565,
	holeRight: 0.7447,
	holeTop: 87.5 / 941,
	holeBottom: (87.5 + 5 * ROW_T) / 941,
	scale: 1,
	/** Cell pitch aspect (163.25 / 133.2). */
	cellAspect: 163.25 / ROW_T,
} as const;

/** The frame's windows in art pixels (1672x941), after the row equalisation. */
export const V2_FRAME_WINDOWS = {
	art: { w: 1672, h: 941 },
	/** Nominal grid: origin and pitch, art px. */
	origin: { x: 428.9, y: CUTS[0] },
	pitch: { w: 163.25, h: ROW_T },
	colX: [440, 600, 764, 929, 1093],
	colW: [141, 144, 145, 144, 140],
	/** Every window is this tall (the art's 121 .. 110 px windows, stretched with their bands) and centred in its cell. */
	winH: 116,
} as const;

/** Window height / cell pitch of the frame art: the symbol box is a whole cell, the visible window is smaller. */
const WINDOW_FIT = 116 / ROW_T;

/**
 * Symbol height by tier as a fraction of the frame WINDOW height (not of the cell). Each regular tier is 1.1x the
 * previous one; scatter, Concierge / Mystery and feature symbols match premium. Overall 5 % smaller than before.
 * Settled symbols are drawn above the frame, so premium may just touch the window's gold lines.
 */
export const V2_TIER_SCALE: Record<string, number> = {
	low: 0.86 * WINDOW_FIT,
	medium: 0.95 * WINDOW_FIT,
	premium: 1.04 * WINDOW_FIT,
	scatter: 1.04 * WINDOW_FIT,
	concierge_mystery: 1.04 * WINDOW_FIT,
	feature: 1.04 * WINDOW_FIT,
};
