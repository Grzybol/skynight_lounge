import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
	V2_CONFIG,
	V2_EVENT_SCHEMA_VERSION,
	V2_PAYLINES,
	V2_REGULAR_IDS,
} from '../../frontend/apps/poc/src/game/skyjump_v2/config.ts';
import { evaluatePaylines } from '../../frontend/apps/poc/src/game/skyjump_v2/evaluatePaylines.ts';
import { validatePhase1Events, validatePhase2Events } from '../../frontend/apps/poc/src/game/skyjump_v2/validateEvents.ts';
import { V2_FIXTURES } from '../../frontend/apps/poc/src/game/skyjump_v2/fixtures.ts';
import { v2FixtureToBookEvents } from '../../frontend/apps/poc/src/game/skyjump_v2/toBookEvents.ts';
import { v2MathSampleToBet } from '../../frontend/apps/poc/src/game/skyjump_v2/mathSamples.ts';

const assert = (condition: unknown, message: string) => {
	if (!condition) throw new Error(message);
};

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const samples = JSON.parse(
	readFileSync(resolve(root, 'math/games/0_0_poc/skyjump_v2_math_samples.json'), 'utf8'),
);
const visibleWindow = (strip: string[], stop: number, rows = 5) => {
	if (stop < 0 || stop >= strip.length) throw new Error('stop');
	return Array.from({ length: rows }, (_, row) => strip[(stop + row) % strip.length]);
};

assert(samples.nonProduction === true, 'samples labelled non-production');
assert(V2_CONFIG.meta.mathStatus === 'PHASE 3 PROVISIONAL FEATURE MATH', 'math status');
assert(V2_CONFIG.payoutGrainX === 0.1, 'grain');
assert(V2_CONFIG.paytable.nonFinal === true, 'paytable nonFinal');
assert(!('weights' in V2_CONFIG), 'no generic weights');
assert(V2_CONFIG.reelModel.strips.length === 5, '5 strips');
assert(V2_CONFIG.scatterModel.paysOnLines === false, 'scatter not on lines');
assert(V2_CONFIG.scatterModel.perfectVRows.join(',') === '0,1,2,1,0', 'perfect V rows');

const awards = V2_CONFIG.paytable.awards as Record<string, Record<string, number>>;
for (const symbol of V2_REGULAR_IDS) {
	for (const match of ['3', '4', '5'] as const) {
		const payout = awards[symbol][match];
		assert(Number.isFinite(payout) && payout > 0, `${symbol} ${match} finite`);
		assert(Math.abs(payout * 10 - Math.round(payout * 10)) < 1e-9, `${symbol} ${match} grain`);
	}
	assert(awards[symbol]['3'] < awards[symbol]['4'], `${symbol} 3<4`);
	assert(awards[symbol]['4'] < awards[symbol]['5'], `${symbol} 4<5`);
}

const wrap = visibleWindow(['A', 'B', 'C', 'D', 'E', 'F'], 4);
assert(wrap.join('') === 'EFABC', 'wraparound window');

const strips = V2_CONFIG.reelModel.strips as string[][];
const sample = samples.samples[0];
const reconstructed = strips.map((strip: string[], reel: number) =>
	visibleWindow(strip, sample.stops[reel]),
);
assert(reconstructed.length === 5, 'five reels still reconstruct from stops');
assert(reconstructed.every((col: string[]) => col.length === 5), 'visible window is 5');

for (const row of samples.samples) {
	const replay = evaluatePaylines(row.board, awards, V2_PAYLINES);
	assert(replay.lineWinX === row.lineWinX, `parity lineWinX ${row.id}`);
	assert(replay.wins.length === row.events[2].wins.length, `parity wins ${row.id}`);
	assert(JSON.stringify(replay.wins) === JSON.stringify(row.events[2].wins), `win objects ${row.id}`);
	validatePhase2Events(row.events);
	assert(row.events[3].type === 'skyjumpScatterResult', `scatter ${row.id}`);
	assert(row.events[4].totalFeatureWinX === 0, `feature ${row.id}`);
	const sum = row.events[2].wins.reduce((total: number, win: { payoutX: number }) => total + win.payoutX, 0);
	assert(Math.abs(sum - row.events[2].lineWinX) < 1e-9, `sum lines ${row.id}`);
	assert(row.events[4].totalWinX === row.events[4].totalLineWinX, `totalWin ${row.id}`);
	assert(row.events[5].amount === row.events[6].amount, `settlement ${row.id}`);
	const bet = v2MathSampleToBet(row, Number(row.id));
	assert(bet.criteria === `phase2-math:${row.id}`, `criteria ${row.id}`);
	assert(JSON.stringify(bet.state) === JSON.stringify(row.events), `frontend does not rebuild ${row.id}`);
}

for (const fixture of V2_FIXTURES) {
	validatePhase1Events(v2FixtureToBookEvents(fixture) as Array<Record<string, unknown>>);
}

assert(V2_EVENT_SCHEMA_VERSION === 2, 'schema 2');

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
	assert(!text.includes('skyjump_v2/mathSamples'), `${rel} must not import math samples`);
	assert(!text.includes('skyjump_v2/featureSamples'), `${rel} must not import feature samples`);
	assert(!text.includes('Math.random'), `${rel} must not use Math.random`);
}

console.log('V2 Phase 2 tests PASS');
