import rawPaytable from '../../../../../../math/games/0_0_poc/skyjump_v2_dev_paytable.json' with { type: 'json' };

import type { V2Paytable } from './evaluatePaylines.ts';

if (rawPaytable.nonProduction !== true) {
	throw new Error('V2 dev paytable must be marked nonProduction');
}

/** NON-PRODUCTION. Fixture and unit tests only. Never use as production math. */
export const V2_DEV_PAYTABLE_META = {
	nonProduction: true as const,
	usage: String(rawPaytable.usage),
	label: String(rawPaytable.label),
};

export const V2_DEV_PAYTABLE = rawPaytable.paytable as V2Paytable;
