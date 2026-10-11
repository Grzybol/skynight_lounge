import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

import { createMulberry32 } from '../../frontend/apps/poc/src/game/skyjump/rng.ts';
import { evaluateDrawnRound, resolveRound, lookupPayout } from '../../frontend/apps/poc/src/game/skyjump/resolveRound.ts';
import {
	BUY_MODES,
	ENABLED_BUY_MODES,
	ENABLED_MODES,
	HILL_TABLE,
	WEATHER_TABLE,
	EVENT_SCHEMA_VERSION,
	MATH_VERSION,
	TARGET_RTP,
} from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import { exactAllModes } from './exactEv.ts';
import { runDesignGuards } from './designGuards.ts';
import {
	FROZEN_CONFIG_SHA256,
	FROZEN_EVENT_SCHEMA_VERSION,
	FROZEN_MATH_VERSION,
	FROZEN_MODE_MAX_WIN,
	FROZEN_RTP,
	FROZEN_RTP_ABS_TOLERANCE,
} from './frozenMath.ts';
import {
	authoritativeFromEvents,
	roundToBookEvents,
	splitBookAfter,
} from '../../frontend/apps/poc/src/game/skyjump/toBookEvents.ts';
import { roundBookAmount, pythonRoundHalfEven } from '../../frontend/apps/poc/src/game/skyjump/roundBookAmount.ts';
import { getTablesForBetMode } from '../../frontend/apps/poc/src/game/skyjump/selectMode.ts';
import { economicFromPayout, winLevelForReturn } from '../../frontend/apps/poc/src/game/skyjump/economics.ts';
import { sha256NewlineStable } from './stableHash.ts';

const assert = (condition: unknown, message: string) => {
	if (!condition) throw new Error(message);
};

const seedRandom = createMulberry32(20260916);

const deterministic = resolveRound({
	bet: 2,
	hillId: 'normal',
	multiplierTableId: 'standard',
	random: createMulberry32(42),
});

const again = resolveRound({
	bet: 2,
	hillId: 'normal',
	multiplierTableId: 'standard',
	random: createMulberry32(42),
});

assert(JSON.stringify(deterministic) === JSON.stringify(again), 'seeded rounds must be deterministic');
assert(deterministic.slots.length === 5, 'five role slots');
assert(deterministic.finalMultiplier.multiplier >= 0, 'final multiplier cannot be negative');
assert(deterministic.localMultiplier >= 1, 'local multiplier >= 1');
assert(deterministic.distanceTotal >= 0, 'distance cannot be negative');
assert(deterministic.finalWinX <= HILL_TABLE.normal.maxWin, 'max win must be enforced');
assert(deterministic.capped === deterministic.isCapped, 'capped aliases must match');
assert(
	Math.abs(deterministic.moneyWin - deterministic.bet * deterministic.finalWinX) < 0.011,
	'money win must equal bet * finalWinX',
);

assert(lookupPayout(HILL_TABLE.normal.payoutCurve, 115.9) === 0, 'below first hit band is miss');
assert(lookupPayout(HILL_TABLE.normal.payoutCurve, 116) === 0.252, 'minDistance is inclusive');
assert(lookupPayout(HILL_TABLE.normal.payoutCurve, 124) === 0.588, 'next band starts inclusive');

assert(pythonRoundHalfEven(111.4) === 111, '111.4 bankers');
assert(pythonRoundHalfEven(111.5) === 112, '111.5 ties to even');
assert(pythonRoundHalfEven(112.5) === 112, '112.5 ties to even');
assert(pythonRoundHalfEven(113.5) === 114, '113.5 ties to even');
assert(roundBookAmount(1.125) === pythonRoundHalfEven(1.125 * 100), 'book amount uses platform rounding');
assert(roundBookAmount(12.075) === pythonRoundHalfEven(12.075 * 100), '12.075 uses *100 then half-even, not round(x,2)*100');
assert(roundBookAmount(12.025) === pythonRoundHalfEven(12.025 * 100), '12.025 tie path');
assert(roundBookAmount(1.005) === pythonRoundHalfEven(1.005 * 100), '1.005 tie path');
assert(roundBookAmount(0.005) === pythonRoundHalfEven(0.005 * 100), '0.005 tie path');
assert(roundBookAmount(0.252) === pythonRoundHalfEven(0.252 * 100), '0.252 curve row');

const expectedBase = lookupPayout(HILL_TABLE.normal.payoutCurve, deterministic.distanceTotal);
assert(deterministic.baseWinX === expectedBase, 'payout curve must be used instead of cash-per-metre');

const localFromSlots = deterministic.slots.reduce((product, slot) => product * slot.localMultiplier, 1);
assert(localFromSlots === deterministic.localMultiplier, 'local multiplier is the product of slots 1-5');

const events = roundToBookEvents(deterministic);
assert(events[0]?.type === 'skyjumpWeather', 'weather event first');
assert(events.slice(1, 7).every((event) => event.type === 'skyjumpSlot'), 'six per-slot events');
assert((events[1] as { slotIndex: number }).slotIndex === 1, 'slot 1');
assert((events[6] as { slotIndex: number; role: string }).slotIndex === 6, 'slot 6');
assert((events[6] as { role: string }).role === 'finalMultiplier', 'slot 6 is final multiplier');
assert(events[7]?.type === 'skyjumpResult', 'result after slots');
assert((events[0] as { schemaVersion: number }).schemaVersion === EVENT_SCHEMA_VERSION, 'schemaVersion on custom events');
assert(events.some((event) => event.type === 'setTotalWin'), 'Stake setTotalWin must remain');
assert(events.some((event) => event.type === 'finalWin'), 'Stake finalWin must remain');
assert((events[7] as { hillProfile: string }).hillProfile === deterministic.hillId, 'hillProfile on result');
assert(
	(events[7] as { multiplierProfile: string }).multiplierProfile === deterministic.multiplierTableId,
	'multiplierProfile on result',
);

const remainingAfterWeather = events.filter((_, index) => index >= 1);
assert(remainingAfterWeather[0]?.type === 'skyjumpSlot', 'resume after weather continues from slot 1');
assert(
	(remainingAfterWeather.find((event) => event.type === 'skyjumpResult') as { finalWinX: number }).finalWinX ===
		deterministic.finalWinX,
	'resume payloads stay authoritative',
);

const expectedAuth = authoritativeFromEvents(events as never);
for (const slotIndex of [1, 2, 3, 4, 5, 6]) {
	const split = splitBookAfter(events as never, 'skyjumpSlot', slotIndex);
	assert(
		JSON.stringify(authoritativeFromEvents([...split.before, ...split.after] as never)) ===
			JSON.stringify(expectedAuth),
		`resume after slot ${slotIndex} keeps authority`,
	);
}

const combined = getTablesForBetMode('BASE', { hillId: 'flying', multiplierTableId: 'max' });
assert(combined.hillId === 'flying' && combined.multiplierTableId === 'max', 'hill + multiplier can combine');
assert(getTablesForBetMode('base').id === 'base', 'lowercase mode id resolves');
assert(getTablesForBetMode('LARGE_HILL').hillId === 'large', 'rgsKey resolves');
assert(getTablesForBetMode('MULT_10_100').maxWin === FROZEN_MODE_MAX_WIN.MULT_10_100, 'MULT_10_100 mode cap');
assert(getTablesForBetMode('MULT_20_200').maxWin === FROZEN_MODE_MAX_WIN.MULT_20_200, 'MULT_20_200 mode cap');
assert(getTablesForBetMode('BASE').maxWin === FROZEN_MODE_MAX_WIN.BASE, 'BASE uses hill/mode 500');
assert(
	ENABLED_MODES.map((mode) => mode.rgsKey).join(',') ===
		'BASE,LARGE_HILL,SKI_FLYING,MULT_10_100,MULT_20_200',
	'enabled modes preserve canonical order',
);
assert(ENABLED_BUY_MODES.every((mode) => mode.type === 'buy' && mode.enabled !== false), 'buy list is enabled buys');
assert(ENABLED_BUY_MODES.length === 4, 'four published buy modes');
assert(
	Object.values(BUY_MODES)
		.filter((mode) => mode.enabled !== false)
		.map((mode) => mode.rgsKey)
		.join(',') === ENABLED_MODES.map((mode) => mode.rgsKey).join(','),
	'frontend enabled list matches canonical enabled flags',
);

const gameSvelte = readFileSync(
	resolve(dirname(fileURLToPath(import.meta.url)), '../../frontend/apps/poc/src/components/Game.svelte'),
	'utf8',
);
assert(gameSvelte.includes('ENABLED_MODES'), 'HUD derives modes from canonical config');
assert(!gameSvelte.includes("new Set(['LARGE_HILL'"), 'HUD must not hardcode a buy-mode subset');

const forcedCap = resolveRound({
	bet: 1,
	hillId: 'normal',
	multiplierTableId: 'max',
	random: () => 0.999999,
});
assert(forcedCap.finalWinX <= HILL_TABLE.normal.maxWin, 'resolver default cap is the hill when maxWin is omitted');

const modeCapRound = resolveRound({
	bet: 1,
	hillId: 'normal',
	multiplierTableId: 'max',
	maxWin: FROZEN_MODE_MAX_WIN.MULT_20_200,
	costMultiplier: 22.6,
	random: () => 0.999999,
});
assert(modeCapRound.maxWin === FROZEN_MODE_MAX_WIN.MULT_20_200, 'MULT_20_200 must pass mode maxWin');
assert(modeCapRound.finalWinX <= FROZEN_MODE_MAX_WIN.MULT_20_200, 'mode cap is enforced');

const weatherHits = Object.fromEntries(WEATHER_TABLE.map((row) => [row.id, 0])) as Record<string, number>;
const SAMPLE = 4000;
for (let i = 0; i < SAMPLE; i += 1) {
	const round = resolveRound({
		bet: 1,
		hillId: 'normal',
		multiplierTableId: 'standard',
		random: seedRandom,
	});
	weatherHits[round.weather.id] += 1;
	assert(round.slots.every((slot) => Number.isFinite(slot.distanceValue)), 'slot distance must be finite');
	assert(round.finalWinX >= 0, 'winX cannot be negative');
}

const stormShare = weatherHits.storm / SAMPLE;
assert(stormShare < 0.12, `storm should be rare, got ${stormShare}`);
assert(weatherHits.sunny > 0 && weatherHits.lightFavorableWind > 0, 'common weather must appear');

const fixturePath = resolve(
	dirname(fileURLToPath(import.meta.url)),
	'../../math/games/0_0_poc/skyjump_fixtures.json',
);
const fixtures = JSON.parse(readFileSync(fixturePath, 'utf8')) as Array<{
	id: string;
	bet: number;
	hillId: 'normal' | 'large' | 'flying';
	multiplierTableId: 'standard' | 'plus' | 'max';
	costMultiplier?: number;
	maxWin?: number;
	weatherId: string;
	temperatureC: number;
	windSpeedMs: number;
	visibilityPct: number;
	slotIds: string[];
	finalMultiplierId: string;
}>;

const fixtureSummaries = fixtures.map((fixture) => {
	const round = evaluateDrawnRound({
		bet: fixture.bet,
		hillId: fixture.hillId,
		multiplierTableId: fixture.multiplierTableId,
		costMultiplier: fixture.costMultiplier,
		maxWin: fixture.maxWin,
		weatherId: fixture.weatherId as never,
		temperatureC: fixture.temperatureC,
		windSpeedMs: fixture.windSpeedMs,
		visibilityPct: fixture.visibilityPct,
		slotIds: fixture.slotIds,
		finalMultiplierId: fixture.finalMultiplierId,
	});
	assert(round.finalWinX <= round.maxWin + 1e-9, `${fixture.id} exceeded max win`);
	return {
		id: fixture.id,
		distanceTotal: round.distanceTotal,
		baseWinX: round.baseWinX,
		localMultiplier: round.localMultiplier,
		finalMultiplier: round.finalMultiplier.multiplier,
		finalWinX: round.finalWinX,
		amount: roundBookAmount(round.finalWinX),
	};
});

const missSummary = fixtureSummaries.find((row) => row.id === 'steady-miss');
assert(missSummary?.baseWinX === 0, 'steady-miss has zero base payout');
assert(missSummary?.finalMultiplier === 0, 'distance miss presents slot 6 as x0');
assert(missSummary?.finalWinX === 0, 'distance miss pays 0');

const pythonCandidates = [
	resolve(dirname(fileURLToPath(import.meta.url)), '../../math/.venv/Scripts/python.exe'),
	resolve(dirname(fileURLToPath(import.meta.url)), '../../.venv/Scripts/python.exe'),
	resolve(dirname(fileURLToPath(import.meta.url)), '../../math/.venv/bin/python'),
	'python',
];
const pythonBin = pythonCandidates.find((candidate) => candidate === 'python' || existsSync(candidate)) ?? 'python';
const python = spawnSync(
	pythonBin,
	[
		'-c',
		'from skyjump_resolve import evaluate_drawn_round, load_fixtures, round_book_amount; import json; print(json.dumps([{ "id": f["id"], **evaluate_drawn_round(f).summary(), "amount": round_book_amount(evaluate_drawn_round(f).finalWinX) } for f in load_fixtures()]))',
	],
	{
		encoding: 'utf8',
		cwd: resolve(dirname(fileURLToPath(import.meta.url)), '../../math/games/0_0_poc'),
	},
);
assert(python.status === 0, `python fixtures failed: ${python.stderr}`);
const pythonSummaries = JSON.parse(python.stdout) as typeof fixtureSummaries;
assert(pythonSummaries.length === fixtureSummaries.length, 'fixture counts must match');
for (const tsRow of fixtureSummaries) {
	const pyRow = pythonSummaries.find((row) => row.id === tsRow.id);
	assert(pyRow, `missing python fixture ${tsRow.id}`);
	assert(pyRow.distanceTotal === tsRow.distanceTotal, `${tsRow.id} distance drift`);
	assert(pyRow.baseWinX === tsRow.baseWinX, `${tsRow.id} baseWinX drift`);
	assert(pyRow.localMultiplier === tsRow.localMultiplier, `${tsRow.id} local drift`);
	assert(pyRow.finalMultiplier === tsRow.finalMultiplier, `${tsRow.id} final multiplier drift`);
	assert(pyRow.finalWinX === tsRow.finalWinX, `${tsRow.id} finalWinX drift`);
	assert(pyRow.amount === tsRow.amount, `${tsRow.id} book amount drift`);
}

assert(MATH_VERSION === FROZEN_MATH_VERSION, 'active tables are mathVersion 3');
assert(EVENT_SCHEMA_VERSION === FROZEN_EVENT_SCHEMA_VERSION, 'event schema stays at 1');
assert(TARGET_RTP === 0.97, 'developer target RTP is 0.97 vs actual wager');

const canonicalPath = resolve(
	dirname(fileURLToPath(import.meta.url)),
	'../../math/games/0_0_poc/skyjump_config.json',
);
const canonicalHash = sha256NewlineStable(readFileSync(canonicalPath));
assert(canonicalHash === FROZEN_CONFIG_SHA256, `canonical SHA-256 drifted: ${canonicalHash}`);

const premiumLoss = economicFromPayout(11.76, 22.6);
assert(premiumLoss.isPayHit && !premiumLoss.isBreakEven && !premiumLoss.isProfit, 'buy payout below wager is not profit');
assert(winLevelForReturn(11.76, 22.6) === 2, 'sub-wager payout is not a big-win level');
assert(winLevelForReturn(50, 22.6) === 4, '50x nominal / 22.6 cost is ~2.21x wager, not a 50x celebration');
assert(winLevelForReturn(50, 1) === 8, '50x on BASE remains a high win level');

const exactRows = exactAllModes();
assert(exactRows.length === 5, 'five published modes');
for (const row of exactRows) {
	assert(row.costMultiplier > 0, `${row.rgsKey} cost`);
	assert(row.maxWin > 0, `${row.rgsKey} maxWin`);
	assert(
		Math.abs(row.rtpVsActualWager - row.expectedPayoutNominal / row.actualWagerUnit) < 1e-12,
		`${row.rgsKey} RTP must be payout / actual wager`,
	);
	assert(
		Math.abs(row.probabilityMass - 1) < 1e-12,
		`${row.rgsKey} probability mass ${row.probabilityMass}`,
	);
	assert(row.hitRate > 0.28 && row.hitRate < 0.58, `${row.rgsKey} hit ${row.hitRate}`);
	assert(row.capFrequency < 0.01, `${row.rgsKey} cap ${row.capFrequency}`);
	const frozen = FROZEN_RTP[row.rgsKey as keyof typeof FROZEN_RTP];
	assert(frozen != null, `${row.rgsKey} missing frozen RTP`);
	assert(
		Math.abs(row.rtpVsActualWager - frozen) <= FROZEN_RTP_ABS_TOLERANCE,
		`${row.rgsKey} frozen RTP drifted: ${row.rtpVsActualWager} vs ${frozen}`,
	);
	assert(
		row.maxWin === FROZEN_MODE_MAX_WIN[row.rgsKey as keyof typeof FROZEN_MODE_MAX_WIN],
		`${row.rgsKey} frozen maxWin`,
	);
}

const seedA = createMulberry32(7);
const seedB = createMulberry32(7);
let sumA = 0;
let sumB = 0;
for (let i = 0; i < 200; i += 1) {
	sumA += resolveRound({
		bet: 1,
		hillId: 'normal',
		multiplierTableId: 'standard',
		maxWin: 500,
		random: seedA,
	}).finalWinX;
	sumB += resolveRound({
		bet: 1,
		hillId: 'normal',
		multiplierTableId: 'standard',
		maxWin: 500,
		random: seedB,
	}).finalWinX;
}
assert(sumA === sumB, 'same seed + config must replay the same simulation totals');

runDesignGuards();

console.log('skyjump math tests passed');
console.log({
	sampleDistance: deterministic.distanceTotal,
	sampleWinX: deterministic.finalWinX,
	sampleAmount: roundBookAmount(deterministic.finalWinX),
	stormShare,
	fixtures: fixtureSummaries,
});
