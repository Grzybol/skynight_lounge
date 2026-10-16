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
 * `slot_background_1.png` (1352x1163, "Gotycka rama z różami i klejnotami"): one square frame with a single opening of
 * 823 x 738 art px (x 244, y 200). The 5x5 board fills the opening, cells are 164.6 x 147.6 art px; the stone tablet
 * (`slot_tablet.png`) sits behind the opening and the symbols (and the tier tiles of the rarer tiers) on top of it.
 */
export const V2_FRAME_ART = { w: 1352, h: 1163 } as const;
/** Visible top / bottom of the frame art (alpha bounds), art px. */
export const V2_FRAME_VISIBLE = { top: 17, bottom: 1089 } as const;

const ART = V2_FRAME_ART;
const HOLE = { x: 244, y: 200, w: 823, h: 738 };
const PITCH = { w: HOLE.w / 5, h: HOLE.h / 5 };
const GRID_ORIGIN = { x: HOLE.x, y: HOLE.y };

export const V2_SLOT_BOARD_FRAME = {
	/** Playfield: the opening of the frame, as fractions of the art. */
	holeLeft: HOLE.x / ART.w,
	holeRight: (HOLE.x + HOLE.w) / ART.w,
	holeTop: HOLE.y / ART.h,
	holeBottom: (HOLE.y + HOLE.h) / ART.h,
	scale: 1,
	cellAspect: PITCH.w / PITCH.h,
} as const;

/** The 5x5 cells in art pixels. There are no separate windows any more: a symbol is centred in its cell. */
export const V2_FRAME_WINDOWS = {
	art: ART,
	origin: GRID_ORIGIN,
	pitch: PITCH,
	colX: [0, 1, 2, 3, 4].map((i) => HOLE.x + PITCH.w * i),
	rowY: [0, 1, 2, 3, 4].map((i) => HOLE.y + PITCH.h * i),
	winW: PITCH.w,
	winH: PITCH.h,
	/** Tier tiles fill the whole cell (they touch each other). */
	tileGrow: 1,
} as const;

/** Where the stone tablet is drawn, in frame art px: the opening plus 5 % on every side (the frame hides the overlap). */
export const V2_TABLET_RECT = (() => {
	const mx = HOLE.w * 0.05;
	const my = HOLE.h * 0.05;
	const rect = { x0: HOLE.x - mx, y0: HOLE.y - my, x1: HOLE.x + HOLE.w + mx, y1: HOLE.y + HOLE.h + my };
	// The tablet image is 1254 x 1254 with its stone between (32, 46) and (1234, 1212): map that box onto the rectangle.
	const sx = (rect.x1 - rect.x0) / (1234 - 32);
	const sy = (rect.y1 - rect.y0) / (1212 - 46);
	return {
		left: rect.x0 - 32 * sx,
		top: rect.y0 - 46 * sy,
		width: 1254 * sx,
		height: 1254 * sy,
		texture: 1254,
	};
})();

/**
 * Symbol height by tier as a fraction of the CELL height (cells are 147.6 art px tall, about 99 px on the 1280x720 stage).
 * Low is 0.745; the growth over low is +11.25 % (medium) and +22.5 % (premium, scatter, Concierge / Mystery, features).
 */
export const V2_TIER_SCALE: Record<string, number> = {
	low: 0.745,
	medium: 0.829,
	premium: 0.913,
	scatter: 0.913,
	concierge_mystery: 0.913,
	feature: 0.913,
};
