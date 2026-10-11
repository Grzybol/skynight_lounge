/**
 * Pure idle-variation and win-priority rules. No timers, no DOM: callers pass
 * an rng so behaviour is reproducible in tests.
 */

export type Rng = () => number;

export const nextVariationDelayMs = (minMs: number, maxMs: number, rng: Rng): number =>
	Math.round(minMs + rng() * Math.max(0, maxMs - minMs));

/** Random variation, never the one that just played (when there is a choice). */
export const pickVariation = (
	variations: readonly string[],
	last: string | null,
	rng: Rng,
	weights: Record<string, number> = {},
): string | null => {
	if (variations.length === 0) return null;
	const pool = variations.length > 1 ? variations.filter((v) => v !== last) : [...variations];
	const w = pool.map((v) => Math.max(0, weights[v] ?? 1));
	const total = w.reduce((a, b) => a + b, 0);
	if (total <= 0) return pool[Math.min(pool.length - 1, Math.floor(rng() * pool.length))] ?? null;
	let r = rng() * total;
	for (let i = 0; i < pool.length; i++) {
		r -= w[i];
		if (r < 0) return pool[i];
	}
	return pool[pool.length - 1] ?? null;
};

/**
 * Whether a win request may start. Idle/variation always yield to a win.
 * While a win is playing only a strictly higher priority interrupts it, so a
 * burst of equal wins (autoplay, turbo) does not restart the clip every spin.
 */
export const winMayStart = (activePriority: number | null, requested: number): boolean =>
	activePriority === null || requested > activePriority;
