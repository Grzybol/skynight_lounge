import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
	V2_BOARD_REELS,
	V2_BOARD_ROWS,
	V2_CONFIG,
	V2_DESKTOP_LOGICAL,
	V2_EVENT_SCHEMA_VERSION,
	V2_LINEAGE,
	V2_MATH_VERSION,
	V2_MAX_FEATURE_CHAIN_DEPTH,
	V2_PAYLINE_IDS,
	V2_PAYLINES,
	V2_REGULAR_IDS,
	V2_SCATTER_ID,
} from '../../frontend/apps/poc/src/game/skyjump_v2/config.ts';
import { V2_DEV_PAYTABLE, V2_DEV_PAYTABLE_META } from '../../frontend/apps/poc/src/game/skyjump_v2/devPaytable.ts';
import { evaluatePaylines } from '../../frontend/apps/poc/src/game/skyjump_v2/evaluatePaylines.ts';
import { V2_FIXTURES, v2FixtureById } from '../../frontend/apps/poc/src/game/skyjump_v2/fixtures.ts';
import { v2FixtureToBookEvents } from '../../frontend/apps/poc/src/game/skyjump_v2/toBookEvents.ts';
import { validatePhase1Events } from '../../frontend/apps/poc/src/game/skyjump_v2/validateEvents.ts';

const assert = (condition: unknown, message: string) => {
	if (!condition) throw new Error(message);
};

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const canonical = JSON.parse(
	readFileSync(resolve(root, 'math/games/0_0_poc/skyjump_v2_config.json'), 'utf8'),
);
const fill = (symbol: string) =>
	Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => symbol));
const paint = (board: string[][], cells: Array<[number, number, string]>) => {
	const next = board.map((col) => [...col]);
	for (const [reel, row, id] of cells) next[reel][row] = id;
	return next;
};

assert(V2_LINEAGE === 'skyjump-v2', 'lineage');
assert(V2_MATH_VERSION === 1, 'mathVersion');
assert(V2_EVENT_SCHEMA_VERSION === 2, 'eventSchemaVersion');
assert(V2_BOARD_REELS === 5 && V2_BOARD_ROWS === 5, '5×5 board');
assert(V2_MAX_FEATURE_CHAIN_DEPTH === 8, 'maxFeatureChainDepth');
assert(V2_DESKTOP_LOGICAL.width === 1280 && V2_DESKTOP_LOGICAL.height === 720, '1280×720 logical');
assert(V2_REGULAR_IDS.size === 9, '9 regulars');
assert(V2_SCATTER_ID === 'S', 'scatter id');
assert(!('weights' in V2_CONFIG), 'no production weights');
assert(V2_CONFIG.paytable.status === 'PHASE 2 PROVISIONAL BASE MATH', 'provisional paytable labelled');
assert(V2_CONFIG.paytable.nonFinal === true, 'paytable is not final production');
assert(V2_PAYLINE_IDS.length === 28, 'exactly 28 paylines');
assert(new Set(V2_PAYLINE_IDS).size === 28, 'unique payline ids');
assert(V2_PAYLINE_IDS[0] === 1 && V2_PAYLINE_IDS[27] === 28, 'ids 1–28');

for (const id of V2_PAYLINE_IDS) {
	const rows = V2_PAYLINES[id];
	assert(rows.length === 5, `payline ${id} has 5 rows`);
	assert(rows.every((row) => row >= 0 && row <= 4), `payline ${id} rows in 0–4`);
}

assert(JSON.stringify(canonical.paylines) === JSON.stringify(V2_CONFIG.paylines), 'JSON → TS payline parity');
assert(V2_DEV_PAYTABLE_META.nonProduction === true, 'dev paytable labelled non-production');
assert(V2_DEV_PAYTABLE_META.usage === 'FIXTURE/TEST ONLY', 'dev paytable usage');

const three = evaluatePaylines(
	paint(fill('S'), [
		[0, 2, 'P1'],
		[1, 2, 'P1'],
		[2, 2, 'P1'],
	]),
	V2_DEV_PAYTABLE,
);
assert(three.wins.length === 1 && three.wins[0].matchCount === 3, '3-match');
assert(three.wins[0].payoutX === 2.5, '3-match P1 pay');

const four = evaluatePaylines(
	paint(fill('S'), [
		[0, 2, 'P2'],
		[1, 2, 'P2'],
		[2, 2, 'P2'],
		[3, 2, 'P2'],
	]),
	V2_DEV_PAYTABLE,
);
assert(four.wins[0]?.matchCount === 4, '4-match');

const five = evaluatePaylines(
	paint(fill('S'), [
		[0, 2, 'P1'],
		[1, 2, 'P1'],
		[2, 2, 'P1'],
		[3, 2, 'P1'],
		[4, 2, 'P1'],
	]),
	V2_DEV_PAYTABLE,
);
assert(five.wins[0]?.matchCount === 5 && five.lineWinX === 25, '5-match');

const startsLate = evaluatePaylines(
	fill('P1').map((col, reel) => (reel === 0 ? col.map(() => 'S') : col)),
	V2_DEV_PAYTABLE,
);
assert(startsLate.wins.length === 0, 'must start reel 1');

const gapped = evaluatePaylines(
	paint(fill('S'), [
		[0, 2, 'P1'],
		[1, 2, 'P1'],
		[2, 2, 'L3'],
		[3, 2, 'P1'],
		[4, 2, 'P1'],
	]),
	V2_DEV_PAYTABLE,
);
assert(gapped.wins.length === 0, 'gap breaks adjacency');

const scatterLine = evaluatePaylines(fill('S'), V2_DEV_PAYTABLE);
assert(scatterLine.wins.length === 0, 'scatter excluded');

assert(V2_FIXTURES.length === 10, '10 fixtures');
assert(v2FixtureById('01')?.expected.wins.length === 0, 'fixture 01 no win');
assert(v2FixtureById('02')?.expected.wins[0]?.matchCount === 3, 'fixture 02');
assert(v2FixtureById('03')?.expected.wins[0]?.matchCount === 4, 'fixture 03');
assert(v2FixtureById('04')?.expected.wins[0]?.matchCount === 5, 'fixture 04');
assert((v2FixtureById('05')?.expected.wins.length ?? 0) >= 2, 'fixture 05 multi');
assert((v2FixtureById('06')?.expected.wins.length ?? 0) >= 2, 'fixture 06 overlap');
assert(v2FixtureById('07')?.expected.wins.length === 0, 'fixture 07');
assert(v2FixtureById('08')?.expected.wins.length === 0, 'fixture 08');
assert(v2FixtureById('09')?.expected.wins.length === 0, 'fixture 09 scatter');
assert((v2FixtureById('10')?.expected.wins.length ?? 0) >= 2, 'fixture 10 shared cells');

const shared = new Set(
	(v2FixtureById('10')?.expected.wins ?? []).flatMap((win) =>
		win.positions.map((pos) => `${pos.reel}:${pos.row}`),
	),
);
assert(shared.has('0:0') && shared.has('1:0'), 'shared cells participate in multiple lines');

for (const fixture of V2_FIXTURES) {
	const replay = evaluatePaylines(fixture.board, V2_DEV_PAYTABLE);
	assert(replay.lineWinX === fixture.expected.lineWinX, `replay ${fixture.id} lineWinX`);
	assert(replay.wins.length === fixture.expected.wins.length, `replay ${fixture.id} wins`);
	const events = v2FixtureToBookEvents(fixture);
	validatePhase1Events(events as Array<Record<string, unknown>>);
	const reveal = events.find((event) => event.type === 'skyjumpBoardReveal');
	const lines = events.find((event) => event.type === 'skyjumpLineWins');
	assert(reveal && 'board' in reveal, `reveal ${fixture.id}`);
	assert(JSON.stringify(reveal.board) === JSON.stringify(fixture.board), `board event ${fixture.id}`);
	assert(lines && 'lineWinX' in lines && lines.lineWinX === fixture.expected.lineWinX, `line event ${fixture.id}`);
	const result = events.find((event) => event.type === 'skyjumpResult');
	assert(result && 'totalFeatureWinX' in result && result.totalFeatureWinX === 0, `feature win ${fixture.id}`);
}

const productionSources = [
	'frontend/apps/poc/src/components/Game.svelte',
	'frontend/apps/poc/src/components/skyjump_v2/SkyJumpV2Board.svelte',
	'frontend/apps/poc/src/game/bookEventHandlerMap.ts',
	'frontend/apps/poc/src/game/actor.ts',
	'frontend/apps/poc/src/game/utils.ts',
];
for (const rel of productionSources) {
	const text = readFileSync(resolve(root, rel), 'utf8');
	assert(!text.includes('evaluatePaylines'), `${rel} must not evaluate paylines`);
	assert(!text.includes('V2_DEV_PAYTABLE'), `${rel} must not import the test paytable`);
	assert(!text.includes('skyjump_v2/fixtures'), `${rel} must not import fixtures`);
	assert(!text.includes('Math.random'), `${rel} must not use Math.random`);
}

const v1Frozen = readFileSync(resolve(root, 'math/games/0_0_poc/skyjump_config.json'), 'utf8');
assert(v1Frozen.includes('"mathVersion": 3'), 'V1 frozen config remains');
assert(!v1Frozen.includes('skyjump-v2'), 'V1 config is not V2');

console.log('V2 Phase 1 tests PASS');
