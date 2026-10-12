/** Mulberry32 — deterministic [0, 1) generator for tests and simulations. */
export const createMulberry32 = (seed: number) => {
	let t = seed >>> 0;
	return () => {
		t += 0x6d2b79f5;
		let r = Math.imul(t ^ (t >>> 15), 1 | t);
		r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
		return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
	};
};

export const pickWeighted = <T extends { weight: number }>(
	items: readonly T[],
	random: () => number,
): T => {
	const total = items.reduce((sum, item) => sum + Math.max(0, item.weight), 0);
	if (total <= 0) throw new Error('Weighted table has no positive weights');
	let cursor = random() * total;
	for (const item of items) {
		cursor -= Math.max(0, item.weight);
		if (cursor <= 0) return item;
	}
	return items[items.length - 1];
};

export const lerp = (min: number, max: number, t: number) => min + (max - min) * t;

export const clamp = (value: number, min: number, max: number) =>
	Math.min(max, Math.max(min, value));

export const roundTo = (value: number, decimals: number) => {
	const factor = 10 ** decimals;
	return Math.round(value * factor) / factor;
};
