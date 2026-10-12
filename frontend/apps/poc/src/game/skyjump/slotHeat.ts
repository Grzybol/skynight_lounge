import { SLOT_ROLES } from './config.ts';

export type SlotHeatId =
	| 'neg-hi'
	| 'neg-mid'
	| 'neg-lo'
	| 'neutral'
	| 'pos-lo'
	| 'pos-mid'
	| 'pos-hi'
	| 'pos-max';

export type SlotHeat = {
	id: SlotHeatId;
	pulse: 0 | 1 | 2 | 3;
};

const heatForShare = (share: number, negative: boolean): SlotHeat => {
	if (negative) {
		if (share >= 0.72) return { id: 'neg-hi', pulse: 2 };
		if (share >= 0.42) return { id: 'neg-mid', pulse: 1 };
		return { id: 'neg-lo', pulse: 0 };
	}
	if (share >= 0.9) return { id: 'pos-max', pulse: 3 };
	if (share >= 0.72) return { id: 'pos-hi', pulse: 2 };
	if (share >= 0.5) return { id: 'pos-mid', pulse: 1 };
	return { id: 'pos-lo', pulse: 0 };
};

export const slotHeatFor = (
	reelIndex: number,
	distanceValue: number | null | undefined,
	localMultiplier = 1,
): SlotHeat => {
	if (distanceValue == null || reelIndex < 0 || reelIndex > 4) {
		return { id: 'neutral', pulse: 0 };
	}
	const values = (SLOT_ROLES[reelIndex]?.symbols ?? []).map((symbol) => symbol.distanceValue);
	const max = Math.max(0, ...values);
	const min = Math.min(0, ...values);
	let heat: SlotHeat;
	if (distanceValue < 0 && min < 0) {
		heat = heatForShare(distanceValue / min, true);
	} else if (distanceValue > 0 && max > 0) {
		heat = heatForShare(distanceValue / max, false);
	} else {
		heat = { id: 'neutral', pulse: 0 };
	}
	if (localMultiplier >= 3 && heat.pulse < 3) return { id: 'pos-max', pulse: 3 };
	if (localMultiplier >= 2 && heat.pulse < 2) {
		return heat.id.startsWith('neg') ? heat : { id: 'pos-hi', pulse: 2 };
	}
	return heat;
};

export const parseDistanceTick = (tick: string) => {
	if (!tick || tick === '—' || tick.startsWith('x')) return null;
	const value = Number.parseInt(tick, 10);
	return Number.isFinite(value) ? value : null;
};
