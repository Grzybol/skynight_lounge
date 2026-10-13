/**
 * Presentation-only win celebration tiers for SkyJump V2 Phase 8C.
 *
 * Authority:
 * - Numeric target always comes from book/event amount (never inferred payout).
 * - WORLD_RECORD title requires explicit `skyjumpWorldRecord` / board WR flag.
 * - MAX_WIN title requires terminal cap / max-win semantics (`capHit` / cap event).
 * - BIG / MEGA / SUPER thresholds are PRESENTATION-ONLY stake multiples.
 *   They must never alter RTP, settlement, books, or event economics.
 *
 * Mapping (presentation config — visual only):
 *   SUPER  ≥ 200× stake
 *   MEGA   ≥ 50× stake
 *   BIG    ≥ 10× stake
 *   (below BIG → no title celebration; board status bar still shows TOTAL WIN)
 */

import { V2_WIN_TITLE_URLS } from './uiAssetRegistry';

export type V2WinCelebrationTier = 'none' | 'big' | 'mega' | 'super' | 'max' | 'worldRecord';

/** Multiples of stake (×). Documented as presentation-only. */
export const V2_WIN_CELEBRATION_THRESHOLDS = {
	big: 10,
	mega: 50,
	super: 200,
} as const;

/** @deprecated Prefer V2_WIN_CELEBRATION_THRESHOLDS — kept for older tests. */
export const V2_WIN_PRESENTATION_THRESHOLDS = {
	good: V2_WIN_CELEBRATION_THRESHOLDS.big,
	big: V2_WIN_CELEBRATION_THRESHOLDS.mega,
	max: 50_000,
} as const;

export type V2WinPresentationTier = 'none' | 'normal' | 'good' | 'big' | 'max';

export const classifyV2WinPresentation = (totalWinX: number): V2WinPresentationTier => {
	if (!(totalWinX > 0)) return 'none';
	if (totalWinX >= V2_WIN_PRESENTATION_THRESHOLDS.max) return 'max';
	if (totalWinX >= V2_WIN_PRESENTATION_THRESHOLDS.big) return 'big';
	if (totalWinX >= V2_WIN_PRESENTATION_THRESHOLDS.good) return 'good';
	return 'normal';
};

export type ClassifyV2WinCelebrationInput = {
	/** Stake-multiple total win (presentation readout). */
	totalWinX: number;
	/** Explicit World Record event / board flag. */
	worldRecord?: boolean;
	/** Terminal max-win / cap reached (economic flag from books). */
	capHit?: boolean;
};

/**
 * Resolve celebration title tier.
 * WR beats MAX beats SUPER/MEGA/BIG thresholds.
 */
export const classifyV2WinCelebration = ({
	totalWinX,
	worldRecord = false,
	capHit = false,
}: ClassifyV2WinCelebrationInput): V2WinCelebrationTier => {
	if (worldRecord) return 'worldRecord';
	if (capHit) return 'max';
	if (!(totalWinX > 0)) return 'none';
	if (totalWinX >= V2_WIN_CELEBRATION_THRESHOLDS.super) return 'super';
	if (totalWinX >= V2_WIN_CELEBRATION_THRESHOLDS.mega) return 'mega';
	if (totalWinX >= V2_WIN_CELEBRATION_THRESHOLDS.big) return 'big';
	return 'none';
};

export const v2WinTitleUrlForTier = (tier: V2WinCelebrationTier): string | null => {
	switch (tier) {
		case 'big':
			return V2_WIN_TITLE_URLS.big;
		case 'mega':
			return V2_WIN_TITLE_URLS.mega;
		case 'super':
			return V2_WIN_TITLE_URLS.super;
		case 'max':
			return V2_WIN_TITLE_URLS.max;
		case 'worldRecord':
			return V2_WIN_TITLE_URLS.worldRecord;
		default:
			return null;
	}
};

export type V2WinFxIntensity = {
	glowRing: boolean;
	snowBurst: boolean;
	sparkles: boolean;
	screenFlash: boolean;
	coinSparkle: boolean;
	iceGlint: boolean;
	particleBudget: number;
};

export const v2WinFxIntensity = (tier: V2WinCelebrationTier): V2WinFxIntensity => {
	// The ice glow ring is the leftover SkyJump plate. Lounge win overlays are the frame.
	const glowRing = false;
	switch (tier) {
		case 'big':
			return {
				glowRing,
				snowBurst: true,
				sparkles: true,
				screenFlash: false,
				coinSparkle: false,
				iceGlint: true,
				particleBudget: 5,
			};
		case 'mega':
			return {
				glowRing,
				snowBurst: true,
				sparkles: true,
				screenFlash: false,
				coinSparkle: true,
				iceGlint: true,
				particleBudget: 9,
			};
		case 'super':
			return {
				glowRing,
				snowBurst: true,
				sparkles: true,
				screenFlash: true,
				coinSparkle: true,
				iceGlint: true,
				particleBudget: 13,
			};
		case 'max':
			return {
				glowRing,
				snowBurst: true,
				sparkles: true,
				screenFlash: true,
				coinSparkle: true,
				iceGlint: true,
				particleBudget: 17,
			};
		case 'worldRecord':
			return {
				glowRing,
				snowBurst: true,
				sparkles: true,
				screenFlash: true,
				coinSparkle: true,
				iceGlint: true,
				particleBudget: 24,
			};
		default:
			return {
				glowRing: false,
				snowBurst: false,
				sparkles: false,
				screenFlash: false,
				coinSparkle: false,
				iceGlint: false,
				particleBudget: 0,
			};
	}
};

/**
 * Celebration timing (ms). Cosmetic only.
 * Big and above: count 4 s, pulse the final figure 1 s (5 s, matching the big-win sound). Turbo: 3.4 s + 1.5 s (4.9 s).
 */
/** Fade of the room blur / lifted plate in and out. Keep in sync with the CSS transitions (700 ms). */
export const V2_WIN_BLUR_FADE_MS = 700;

export const V2_WIN_CELEBRATION_TIMING = {
	/** Big: 4 s count + 1 s pulse = 5 s, the length of the universal big-win sound. */
	normal: { countMs: 4000, holdMs: 1000 },
	/** Mega, super, max, world record: the same 5 s. */
	normalMega: { countMs: 4000, holdMs: 1000 },
	turbo: { countMs: 3400, holdMs: 1500 },
} as const;

const isMegaPlus = (tier: V2WinCelebrationTier) => tier !== 'big' && tier !== 'none';

/** Count-up duration (ms). Cosmetic only. */
export const v2WinCountUpMs = (opts: {
	tier: V2WinCelebrationTier;
	turbo?: boolean;
	catchUp?: boolean;
	reducedMotion?: boolean;
}): number => {
	if (opts.catchUp || opts.reducedMotion || opts.tier === 'none') return 0;
	if (opts.turbo) return V2_WIN_CELEBRATION_TIMING.turbo.countMs;
	return isMegaPlus(opts.tier)
		? V2_WIN_CELEBRATION_TIMING.normalMega.countMs
		: V2_WIN_CELEBRATION_TIMING.normal.countMs;
};

/** Post-count-up hold (ms) while the final figure pulses, before auto-dismiss. */
export const v2WinHoldMs = (opts: {
	tier: V2WinCelebrationTier;
	turbo?: boolean;
	catchUp?: boolean;
	reducedMotion?: boolean;
}): number => {
	if (opts.catchUp || opts.reducedMotion || opts.tier === 'none') return 0;
	if (opts.turbo) return V2_WIN_CELEBRATION_TIMING.turbo.holdMs;
	return isMegaPlus(opts.tier)
		? V2_WIN_CELEBRATION_TIMING.normalMega.holdMs
		: V2_WIN_CELEBRATION_TIMING.normal.holdMs;
};
