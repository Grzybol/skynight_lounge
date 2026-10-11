/** Pure playback math, no DOM. Kept separate so it can be unit tested in node. */

/** Frame index for `elapsedMs` at `fps`. Loops wrap; one-shots return `frames` once finished. */
export const frameAt = (elapsedMs: number, fps: number, frames: number, loop: boolean): number => {
	if (!(elapsedMs > 0)) return 0;
	const idx = Math.floor((elapsedMs * fps) / 1000);
	return loop ? idx % frames : Math.min(idx, frames);
};

/** True when a one-shot has shown every frame. */
export const isFinished = (elapsedMs: number, fps: number, frames: number): boolean =>
	Math.floor((Math.max(0, elapsedMs) * fps) / 1000) >= frames;

/**
 * Clock correction for a frame gap that is really a stall (hidden tab, long
 * main-thread block). Returns how far to push the clip start forward so the
 * clip resumes where it was instead of fast-forwarding or finishing instantly.
 */
export const stallShiftMs = (gapMs: number, fps: number, stallGapMs = 250): number =>
	gapMs > stallGapMs ? gapMs - 1000 / fps : 0;
