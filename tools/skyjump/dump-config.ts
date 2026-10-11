import { writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
	BET_MODE_TO_TABLES,
	HILL_TABLE,
	MULTIPLIER_TABLES,
	SLOT_ROLES,
	SKYJUMP_META,
	WEATHER_TABLE,
} from '../../frontend/apps/poc/src/game/skyjump/config.ts';

const payload = {
	meta: SKYJUMP_META,
	bookAmountMultiplier: 100,
	weather: WEATHER_TABLE,
	hills: HILL_TABLE,
	slots: SLOT_ROLES.filter((role) => role.id !== 'multiplier').map((role) => ({
		id: role.id,
		index: role.index,
		label: role.label,
		shortLabel: role.shortLabel,
		iconKey: role.iconKey,
		symbols: role.symbols,
	})),
	finalMultipliers: MULTIPLIER_TABLES,
	buyModes: BET_MODE_TO_TABLES,
};

const out = resolve(dirname(fileURLToPath(import.meta.url)), '../../math/games/0_0_poc/skyjump_config.json');
writeFileSync(out, `${JSON.stringify(payload, null, 2)}\n`);
console.log(out);
