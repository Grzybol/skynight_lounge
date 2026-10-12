import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { V2_CONFIG, V2_PAYLINES, V2_REGULAR_IDS } from '../../frontend/apps/poc/src/game/skyjump_v2/config.ts';
import { evaluatePaylines } from '../../frontend/apps/poc/src/game/skyjump_v2/evaluatePaylines.ts';
import { validatePhase1Events, validatePhase2Events, validatePhase3Events } from '../../frontend/apps/poc/src/game/skyjump_v2/validateEvents.ts';
import { V2_FIXTURES } from '../../frontend/apps/poc/src/game/skyjump_v2/fixtures.ts';
import { v2FixtureToBookEvents } from '../../frontend/apps/poc/src/game/skyjump_v2/toBookEvents.ts';
import { v2MathSampleToBet } from '../../frontend/apps/poc/src/game/skyjump_v2/mathSamples.ts';
import { V2_FEATURE_SAMPLES, v2FeatureSampleToBet } from '../../frontend/apps/poc/src/game/skyjump_v2/featureSamples.ts';
import { boardSymbolGrid, reduceV2Events } from '../../frontend/apps/poc/src/game/skyjump_v2/reducer.ts';

const assert = (condition: unknown, message: string) => {
	if (!condition) throw new Error(message);
};

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const fill = (symbol: string) => Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => symbol));
const LEGAL_VALUES: Record<number, number[]> = {
	1: [1, 2, 3, 4],
	2: [5, 10, 15],
	3: [25, 50, 100],
	4: [150, 200, 250, 500],
	5: [750, 1000, 2500, 5000],
	6: [10000, 25000, 50000],
};

assert(V2_CONFIG.meta.mathStatus === 'PHASE 3 PROVISIONAL FEATURE MATH', 'math status');
assert(V2_CONFIG.coachModel.id === 'C', 'coach id');
assert(V2_CONFIG.coachModel.paysOnLines === false, 'coach does not pay lines');
assert(JSON.stringify(V2_CONFIG.coachModel.reels) === JSON.stringify([2, 4]), 'coach reels 2+4');
assert(V2_CONFIG.symbols.mystery.initialReelSymbol === false, 'mystery not a strip symbol');
assert(V2_CONFIG.flightTokens.doNotAutoPay === true, 'tokens do not auto-pay');
assert(V2_CONFIG.flightTokens.t6Id === 'TOKEN_WORLD_RECORD', 'T6 name');
assert(V2_CONFIG.flightTokens.specialWorldRecordId === 'SPECIAL_WORLD_RECORD', 'special WR distinct');
assert(V2_CONFIG.flightTokens.t6Id !== V2_CONFIG.flightTokens.specialWorldRecordId, 'no T6/special clash');
assert(V2_CONFIG.scatterModel.perfectVRows.join(',') === '0,1,2,1,0', 'perfect V unchanged');

const strips = V2_CONFIG.reelModel.strips as string[][];
assert(strips.map((strip) => strip.filter((cell) => cell === 'C').length).join(',') === '0,1,0,1,0', 'one coach on reels 2 and 4');
assert(strips.every((strip) => !strip.includes('Y')), 'mystery not on strips');
assert(strips.every((strip) => strip.every((cell) => !/^T[1-6]$/.test(cell))), 'tokens not on strips');

const awards = V2_CONFIG.paytable.awards as Record<string, Record<string, number>>;
const coachBoard = fill('C');
const coachLines = evaluatePaylines(coachBoard, awards, V2_PAYLINES);
assert(coachLines.wins.length === 0 && coachLines.lineWinX === 0, 'coach never pays paylines');

const scatterBoard = fill('S');
assert(evaluatePaylines(scatterBoard, awards, V2_PAYLINES).wins.length === 0, 'scatter never pays');

assert(V2_FEATURE_SAMPLES.length === 7, 'seven feature samples');
const byId = Object.fromEntries(V2_FEATURE_SAMPLES.map((row) => [row.id, row]));
assert(byId['01'].selectedSymbolIds.some((id) => ['P1', 'P2', 'P3'].includes(id)), '01 premium');
assert(byId['02'].selectedSymbolIds.some((id) => ['L1', 'L2', 'L3'].includes(id)), '02 low');
assert(byId['02'].tokenTiers.length >= 3, '02 multi mystery');
assert(byId['03'].coachCount >= 2, '03 two coaches');
assert(byId['04'].tokenTiers.includes(1), '04 T1');
assert(byId['05'].tokenTiers.includes(3), '05 T3');
assert(byId['06'].tokenTiers.some((tier) => tier >= 4), '06 high tier');
assert(new Set(byId['07'].tokenTiers).size >= 2, '07 mixed tiers');

for (const sample of V2_FEATURE_SAMPLES) {
	validatePhase3Events(sample.events as Array<Record<string, unknown>>);
	assert(sample.totalFeatureWinX === 0, `feature win 0 ${sample.id}`);
	assert(sample.totalWinX === sample.lineWinX, `tokens do not award ${sample.id}`);
	const types = sample.events.map((event) => event.type);
	assert(types[0] === 'skyjumpSpinStart' && types[1] === 'skyjumpBoardReveal', `start ${sample.id}`);
	assert(types[2] === 'skyjumpLineWins' && types[3] === 'skyjumpScatterResult', `lines before features ${sample.id}`);
	assert(types.at(-3) === 'skyjumpResult' && types.at(-2) === 'setTotalWin' && types.at(-1) === 'finalWin', `settle ${sample.id}`);
	const replay = evaluatePaylines(sample.board, awards, V2_PAYLINES);
	assert(replay.lineWinX === sample.lineWinX, `initial-board lines ${sample.id}`);
	const state = reduceV2Events(sample.events as Array<Record<string, unknown>>);
	assert(JSON.stringify(boardSymbolGrid(state)) === JSON.stringify(sample.finalBoard), `reducer board ${sample.id}`);
	assert(state.featureWinX === 0, `reducer feature win ${sample.id}`);
	assert(state.totalWinX === sample.lineWinX, `reducer total ${sample.id}`);
	assert(state.mysteriesOpen === 0, `mysteries closed ${sample.id}`);
	const coaches = sample.events.filter((event) => event.type === 'skyjumpCoachSignal');
	const transforms = sample.events.filter((event) => event.type === 'skyjumpMysteryTransform');
	const resolves = sample.events.filter((event) => event.type === 'skyjumpMysteryResolve');
	const created = transforms.reduce((sum, event) => sum + event.positions.length, 0);
	assert(created === resolves.length, `mystery parity ${sample.id}`);
	for (const coach of coaches) {
		assert(coach.selectedSymbolId !== 'S', `scatter not selectable ${sample.id}`);
		assert(coach.selectedSymbolId !== 'C', `coach not selectable ${sample.id}`);
		assert(coach.selectedSymbolId !== 'Y', `mystery not selectable ${sample.id}`);
		if (coach.selectedSymbolId) {
			assert(V2_REGULAR_IDS.has(coach.selectedSymbolId), `regular only ${sample.id}`);
			const visible = sample.board.flatMap((col, reel) =>
				col.map((symbol, row) => (symbol === coach.selectedSymbolId ? { reel, row } : null)).filter(Boolean),
			);
			assert(JSON.stringify(coach.selectedPositions) === JSON.stringify(visible), `selected positions ${sample.id}`);
		}
	}
	for (const event of resolves) {
		assert(event.resultType === 'FLIGHT_TOKEN', `result type ${sample.id}`);
		assert(LEGAL_VALUES[event.tokenTier].includes(event.tokenValueX), `legal token ${sample.id}`);
		assert(Number.isFinite(event.tokenValueX) && event.tokenValueX > 0, `finite token ${sample.id}`);
		if (event.tokenTier === 6) {
			assert(event.tokenName === 'TOKEN_WORLD_RECORD', 'T6 name');
			assert(event.tokenId === 'T6', 'T6 display');
		}
	}
	const bet = v2FeatureSampleToBet(sample, Number(sample.id));
	assert(bet.criteria === `phase3-feature:${sample.id}`, `criteria ${sample.id}`);
	assert(JSON.stringify(bet.state) === JSON.stringify(sample.events), `frontend does not rebuild ${sample.id}`);
}

const samples = JSON.parse(readFileSync(resolve(root, 'math/games/0_0_poc/skyjump_v2_math_samples.json'), 'utf8'));
for (const row of samples.samples) {
	validatePhase2Events(row.events);
	const replay = evaluatePaylines(row.board, awards, V2_PAYLINES);
	assert(replay.lineWinX === row.lineWinX, `phase2 frozen board ${row.id}`);
	const bet = v2MathSampleToBet(row, Number(row.id));
	assert(bet.criteria === `phase2-math:${row.id}`, `phase2 criteria ${row.id}`);
}

for (const fixture of V2_FIXTURES) {
	validatePhase1Events(v2FixtureToBookEvents(fixture) as Array<Record<string, unknown>>);
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
	assert(!text.includes('skyjump_v2/mathSamples'), `${rel} must not import math samples`);
	assert(!text.includes('skyjump_v2/featureSamples'), `${rel} must not import feature samples`);
	assert(!text.includes('Math.random'), `${rel} must not use Math.random`);
}

const actor = readFileSync(resolve(root, 'frontend/apps/poc/src/game/actor.ts'), 'utf8');
assert(actor.includes('import.meta.env.DEV'), 'localDemo remains DEV-gated');

console.log('V2 Phase 3 tests PASS');
