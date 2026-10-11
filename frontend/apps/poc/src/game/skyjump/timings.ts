import { stateBet } from 'state-shared';

import { TIMING_PROFILES } from './config.ts';
import type { TimingProfile } from './types.ts';

export const getSkyJumpTimings = (turbo = stateBet.isTurbo): TimingProfile =>
	turbo ? TIMING_PROFILES.turbo : TIMING_PROFILES.normal;

export const payoutCountDurationMs = (
	result: {
		amount: number;
		isPayHit?: boolean;
		isProfit?: boolean;
		returnMultiplier?: number;
	},
	timings: TimingProfile,
) => {
	const turbo = timings.id === 'turbo';
	if (!result.isPayHit || result.amount <= 0) return turbo ? 360 : 560;
	if (!result.isProfit) return turbo ? 780 : 1200;
	const ret = result.returnMultiplier ?? 0;
	if (ret >= 10) return turbo ? 2400 : 3600;
	if (ret >= 2) return turbo ? 1800 : 2600;
	return turbo ? 1400 : 2000;
};
