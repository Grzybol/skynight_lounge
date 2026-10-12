/**
 * Presentation-only reel strip math.
 * Temporary symbols never enter the board result.
 */

export const REEL_COUNT = 5;
export const VISIBLE_ROWS = 5;

export const easeOutQuad = (t: number) => {
	const clamped = Math.min(1, Math.max(0, t));
	return 1 - (1 - clamped) ** 2;
};

/**
 * 20% acceleration, ~58% fast cruise, 22% deceleration.
 * Distance stays weighted toward the cruise so the reel reads as spinning.
 */
export const reelTravelEase = (t: number) => {
	const c = Math.min(1, Math.max(0, t));
	const accelEnd = 0.2;
	const cruiseEnd = 0.78;
	const dAccel = 0.12;
	const dCruise = 0.74;
	if (c <= accelEnd) {
		const u = c / accelEnd;
		return dAccel * u * u;
	}
	if (c <= cruiseEnd) {
		const u = (c - accelEnd) / (cruiseEnd - accelEnd);
		return dAccel + dCruise * u;
	}
	const u = (c - cruiseEnd) / (1 - cruiseEnd);
	const remain = 1 - dAccel - dCruise;
	return dAccel + dCruise + remain * (1 - (1 - u) * (1 - u));
};

export type ReelPace = '' | 'soft' | 'fast' | 'land';

/** Soft blur on the shoulders, stronger blur only through the fast middle. */
export const reelTravelPace = (elapsedMs: number, travelMs: number): 'soft' | 'fast' => {
	const u = travelMs <= 0 ? 1 : Math.min(1, Math.max(0, elapsedMs / travelMs));
	if (u < 0.2 || u > 0.78) return 'soft';
	return 'fast';
};

/** Later reels spin slightly less so stop stagger stays below the 300ms start stagger. */
export const reelTravelMs = (
	baseTravelMs: number,
	reel: number,
	startStaggerMs: number,
	stopStaggerMs: number,
) => {
	const shrink = Math.max(0, startStaggerMs - stopStaggerMs);
	return Math.max(stopStaggerMs, Math.round(baseTravelMs - reel * shrink));
};

/**
 * Strip top → bottom: final result, then filler, then the outgoing symbols.
 * A negative translateY shows the outgoing symbols. Animating toward 0
 * moves the strip downward until the result fills the viewport.
 */
export const buildReelStrip = (opts: {
	reel: number;
	previous: readonly string[];
	result: readonly string[];
	travelCells: number;
	band: readonly string[];
}) => {
	const travel = Math.max(VISIBLE_ROWS, opts.travelCells);
	const result = Array.from({ length: VISIBLE_ROWS }, (_, row) => opts.result[row] ?? 'L3');
	const previous = Array.from({ length: VISIBLE_ROWS }, (_, row) => opts.previous[row] ?? result[row]);
	const tempsNeeded = travel - VISIBLE_ROWS;
	const temps = Array.from(
		{ length: tempsNeeded },
		(_, index) => opts.band[(index + opts.reel * 7) % opts.band.length] ?? 'L3',
	);
	return [...result, ...temps, ...previous];
};

/** TranslateY in px. `done` means the strip is settled on the result. */
export const reelOffsetPx = (opts: {
	elapsedMs: number;
	travelMs: number;
	settleMs: number;
	travelCells: number;
	pitch: number;
	overshootPx: number;
}): number | 'done' => {
	const travelCells = Math.max(VISIBLE_ROWS, opts.travelCells);
	const start = -travelCells * opts.pitch;
	if (opts.elapsedMs <= 0) return start;
	const travelMs = Math.max(0, opts.travelMs);
	if (opts.elapsedMs < travelMs) {
		const t = travelMs === 0 ? 1 : opts.elapsedMs / travelMs;
		const u = reelTravelEase(t);
		const towardStop = start * (1 - u);
		const tailStart = 0.84;
		const tail = u <= tailStart ? 0 : easeOutQuad((u - tailStart) / (1 - tailStart));
		return towardStop + opts.overshootPx * tail;
	}
	const settleMs = Math.max(0, opts.settleMs);
	if (settleMs === 0) return 'done';
	const settleT = (opts.elapsedMs - travelMs) / settleMs;
	if (settleT >= 1) return 'done';
	return opts.overshootPx * (1 - easeOutQuad(settleT));
};
