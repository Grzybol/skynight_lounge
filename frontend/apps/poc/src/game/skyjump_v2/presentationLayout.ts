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
	 * `slot_background_1/2.png` (1672x1096, 5 rows). The playfield is the 5x5 block of cell pitches:
	 * the hole union (430..1242 x 98..852) grown by half a gold line on every side
	 * (pitch 167 x 154.5), so each symbol cell is centred exactly on its frame window.
	 */
	holeLeft: 0.2507,
	holeRight: 0.7493,
	holeTop: 0.081,
	holeBottom: 0.7858,
	scale: 1,
	/** Cell pitch aspect (167 / 154.5). */
	cellAspect: 1.081,
} as const;
