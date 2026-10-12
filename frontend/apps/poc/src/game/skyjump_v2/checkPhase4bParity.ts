/** Phase 4B PY/TS reducer parity check against exported Python cases. */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { boardSymbolGrid, reduceV2Events } from './reducer.ts';

const here = dirname(fileURLToPath(import.meta.url));
const casesPath = join(
	here,
	'../../../../../../math/games/0_0_poc/skyjump_v2_phase4b_parity_cases.json',
);

const payload = JSON.parse(readFileSync(casesPath, 'utf8')) as {
	nonProduction: boolean;
	cases: Array<{
		events: Array<Record<string, unknown>>;
		featureWinX: number;
		totalWinX: number;
		board: string[][];
		tokenFloorTier: number;
		capReached: boolean;
	}>;
};

if (payload.nonProduction !== true) {
	throw new Error('parity cases must be nonProduction');
}

let failures = 0;
for (const [index, row] of payload.cases.entries()) {
	const state = reduceV2Events(row.events);
	const board = boardSymbolGrid(state);
	const checks: Array<[string, boolean]> = [
		['featureWinX', Math.abs(state.featureWinX - row.featureWinX) < 1e-9],
		['totalWinX', Math.abs(state.totalWinX - row.totalWinX) < 1e-9],
		['tokenFloorTier', state.tokenFloorTier === row.tokenFloorTier],
		['capReached', state.capReached === row.capReached],
		['board', JSON.stringify(board) === JSON.stringify(row.board)],
		['capBound', state.totalWinX <= 50_000 + 1e-9],
	];
	for (const [name, ok] of checks) {
		if (!ok) {
			failures += 1;
			console.error(`case ${index} failed ${name}`, {
				ts: {
					featureWinX: state.featureWinX,
					totalWinX: state.totalWinX,
					tokenFloorTier: state.tokenFloorTier,
					capReached: state.capReached,
					board,
				},
				py: row,
			});
		}
	}
}

if (failures > 0) {
	console.error(`FAIL parity failures=${failures}`);
	process.exit(1);
}
console.log(`PASS phase4b reducer parity n=${payload.cases.length}`);
