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
export const V2_SLOT_BOARD_FRAME = {
	/**
	 * `slot_background_1/2.png` (1672x941, 5x5 windows). The playfield is a 5x5 block of nominal cell pitches
	 * (166.75 x 130.25 art px) centred on the windows; per-cell offsets to the real windows are in V2_FRAME_WINDOWS.
	 */
	holeLeft: 0.251,
	holeRight: 0.7496,
	holeTop: 0.0961,
	holeBottom: 0.7882,
	scale: 1,
	/** Nominal cell pitch aspect (166.75 / 130.25). */
	cellAspect: 1.28,
} as const;

/** The frame's real windows in art pixels (1672x941). The last row is cut short by the frame's bottom bar. */
export const V2_FRAME_WINDOWS = {
	art: { w: 1672, h: 941 },
	/** Nominal grid: origin and pitch, art px. */
	origin: { x: 419.6, y: 90.4 },
	pitch: { w: 166.75, h: 130.25 },
	colX: [433, 596, 765, 932, 1100],
	colW: [140, 144, 143, 144, 139],
	rowY: [100, 232, 365, 496, 624],
	/** Visible window height per row. */
	rowH: [111, 110, 109, 105, 73],
	/** Full tile height per row (the last row's tile is cut by the frame, not squashed). */
	tileH: [111, 110, 109, 105, 105],
} as const;

/**
 * Symbol size by tier, relative to the cell height. Each regular tier is 1.5x the previous one
 * (low -> medium -> premium); scatter, Concierge / Mystery and feature symbols match premium.
 * Settled symbols are drawn above the frame, so they may grow past their window.
 */
export const V2_TIER_SCALE: Record<string, number> = {
	low: 0.6,
	medium: 0.9,
	premium: 1.35,
	scatter: 1.35,
	concierge_mystery: 1.35,
	feature: 1.35,
};
