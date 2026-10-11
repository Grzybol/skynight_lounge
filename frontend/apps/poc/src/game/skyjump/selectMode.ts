import { BET_MODE_TO_TABLES, BUY_MODES } from './config.ts';
import type { BetModeKey, HillId, MultiplierTableId } from './types.ts';

const MODE_BY_KEY = new Map<string, (typeof BUY_MODES)[string]>();
for (const mode of Object.values(BUY_MODES)) {
	MODE_BY_KEY.set(mode.id, mode);
	MODE_BY_KEY.set(mode.id.toUpperCase(), mode);
	MODE_BY_KEY.set(mode.rgsKey, mode);
	MODE_BY_KEY.set(mode.rgsKey.toUpperCase(), mode);
}

export const getBuyMode = (modeKey: string) => {
	const key = modeKey.toUpperCase().replace(/-/g, '_');
	return MODE_BY_KEY.get(key) ?? MODE_BY_KEY.get(modeKey) ?? BUY_MODES.base;
};

export const getTablesForBetMode = (
	modeKey: string,
	overrides: { hillId?: HillId; multiplierTableId?: MultiplierTableId } = {},
) => {
	const mode = getBuyMode(modeKey);
	const tables = BET_MODE_TO_TABLES[mode.rgsKey as BetModeKey] ?? BET_MODE_TO_TABLES.BASE;
	return {
		...tables,
		hillId: overrides.hillId ?? tables.hillId,
		multiplierTableId: overrides.multiplierTableId ?? tables.multiplierTableId,
		hillProfile: overrides.hillId ?? tables.hillId,
		multiplierProfile: overrides.multiplierTableId ?? tables.multiplierTableId,
		maxWin: tables.maxWin,
		costMultiplier: tables.costMultiplier,
		id: mode.id,
		rgsKey: mode.rgsKey,
	};
};
