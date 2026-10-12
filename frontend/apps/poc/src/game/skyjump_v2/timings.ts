/**
 * V2 presentation timing profiles.
 * NORMAL = full polish; TURBO = shortened delays, same order; CATCH_UP = near-instant (resume).
 * Never changes economics.
 */

export const V2_TIMING = {
	normal: {
		reelSpinMs: 420,
		reelStopMs: 180,
		reelGapMs: 90,
		/** Delay before each next reel begins moving. Reel 1 is 0. */
		reelStartStaggerMs: 300,
		/** Time from one reel landing to the next. */
		reelStopStaggerMs: 220,
		/** Reel 1 travel before the settle. Later reels are shortened in reelTravelMs(). */
		reelTravelMs: 1800,
		/** Presentation cells the strip travels. Not a math outcome. */
		reelTravelSlots: 30,
		reelSettleMs: 160,
		/** Brief banner hold after reels (no-win / summary). Not a pre-draw stall. */
		winHoldMs: 180,
		/** Progressive payline stroke draw (cosmetic only). */
		lineDrawMs: 420,
		lineHoldMs: 360,
		lineFadeMs: 160,
		/** Full per-line cycle budget used by older callers (draw+hold+fade). */
		lineCycleMs: 940,
		coachHoldMs: 520,
		mysteryHoldMs: 280,
		gateHoldMs: 280,
		thermalHoldMs: 280,
		collectHoldMs: 320,
		capHoldMs: 360,
		windHoldMs: 360,
		rejumpHoldMs: 320,
		scatterHoldMs: 360,
		wrHoldMs: 900,
		/** FREE SPINS and the room name each stay up for 0.8 s (normal speed). */
		fsBannerMs: 800,
		/** Retrigger is smaller / quicker than FS start. */
		retriggerBannerMs: 360,
		tierUpgradeMs: 640,
		modeTitleMs: 800,
		settlementHoldMs: 100,
	},
	turbo: {
		reelSpinMs: 80,
		reelStopMs: 40,
		reelGapMs: 20,
		reelStartStaggerMs: 90,
		reelStopStaggerMs: 70,
		reelTravelMs: 600,
		reelTravelSlots: 15,
		reelSettleMs: 80,
		winHoldMs: 60,
		lineDrawMs: 100,
		lineHoldMs: 100,
		lineFadeMs: 50,
		lineCycleMs: 250,
		coachHoldMs: 140,
		mysteryHoldMs: 80,
		gateHoldMs: 80,
		thermalHoldMs: 80,
		collectHoldMs: 90,
		capHoldMs: 100,
		windHoldMs: 100,
		rejumpHoldMs: 90,
		scatterHoldMs: 80,
		wrHoldMs: 220,
		fsBannerMs: 140,
		retriggerBannerMs: 90,
		tierUpgradeMs: 160,
		modeTitleMs: 120,
		settlementHoldMs: 40,
	},
	catchUp: {
		reelSpinMs: 0,
		reelStopMs: 0,
		reelGapMs: 0,
		reelStartStaggerMs: 0,
		reelStopStaggerMs: 0,
		reelTravelMs: 0,
		reelTravelSlots: 0,
		reelSettleMs: 0,
		winHoldMs: 0,
		lineDrawMs: 0,
		lineHoldMs: 0,
		lineFadeMs: 0,
		lineCycleMs: 0,
		coachHoldMs: 0,
		mysteryHoldMs: 0,
		gateHoldMs: 0,
		thermalHoldMs: 0,
		collectHoldMs: 0,
		capHoldMs: 0,
		windHoldMs: 0,
		rejumpHoldMs: 0,
		scatterHoldMs: 0,
		wrHoldMs: 0,
		fsBannerMs: 0,
		retriggerBannerMs: 0,
		tierUpgradeMs: 0,
		modeTitleMs: 0,
		settlementHoldMs: 0,
	},
} as const;

export type V2TimingProfile = (typeof V2_TIMING)[keyof typeof V2_TIMING];
export type V2PresentationMode = 'NORMAL' | 'TURBO' | 'CATCH_UP';

export const getV2PresentationMode = (opts: {
	turbo: boolean;
	catchUp: boolean;
}): V2PresentationMode => {
	if (opts.catchUp) return 'CATCH_UP';
	if (opts.turbo) return 'TURBO';
	return 'NORMAL';
};

/** Preferred: resolve NORMAL / TURBO / CATCH_UP from live flags. */
export const getV2TimingsForState = (turbo: boolean, catchUp: boolean): V2TimingProfile => {
	if (catchUp) return V2_TIMING.catchUp;
	if (turbo) return V2_TIMING.turbo;
	return V2_TIMING.normal;
};

/**
 * Legacy-compatible helper. Prefer getV2TimingsForState(turbo, catchUp).
 * When only one boolean is passed historically as (turbo || catchUp), turbo profile is used
 * (catch-up should pass catchUp=true via getV2TimingsForState).
 */
export const getV2Timings = (turbo: boolean, catchUp = false): V2TimingProfile =>
	getV2TimingsForState(turbo, catchUp);
