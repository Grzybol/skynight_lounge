/**
 * Read-only SkyJump math/economics audit. Does not mutate tables.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
	BUY_MODES,
	HILL_TABLE,
	MATH_VERSION,
	MULTIPLIER_TABLES,
	SLOT_ROLES,
	TARGET_RTP,
	WEATHER_TABLE,
} from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import { applyVolatilityBias, finalsForPayState, lookupPayout } from '../../frontend/apps/poc/src/game/skyjump/resolveRound.ts';
import { clamp, createMulberry32, roundTo } from '../../frontend/apps/poc/src/game/skyjump/rng.ts';
import { resolveRound } from '../../frontend/apps/poc/src/game/skyjump/resolveRound.ts';
import type { CanonicalBuyMode } from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import type { HillId, MultiplierTableId, SlotSymbol } from '../../frontend/apps/poc/src/game/skyjump/types.ts';
import { publishedModes } from './exactEv.ts';

const CONFIG_PATH = resolve(
	dirname(fileURLToPath(import.meta.url)),
	'../../math/games/0_0_poc/skyjump_config.json',
);

type Weighted<T> = T & { p: number };
const withProb = <T extends { weight: number }>(items: readonly T[]): Weighted<T>[] => {
	const total = items.reduce((sum, item) => sum + Math.max(0, item.weight), 0);
	return items.map((item) => ({ ...item, p: total > 0 ? Math.max(0, item.weight) / total : 0 }));
};

const settle = (
	hillId: HillId,
	weatherDelta: number,
	distanceSum: number,
	localMultiplier: number,
	finalMultiplier: number,
	maxWin: number,
) => {
	const hill = HILL_TABLE[hillId];
	const distanceTotal = roundTo(Math.max(0, hill.baseDistance + weatherDelta + distanceSum), 1);
	const baseWinX = lookupPayout(hill.payoutCurve, distanceTotal);
	const uncapped = roundTo(baseWinX * localMultiplier * finalMultiplier, 4);
	const capped = uncapped > maxWin;
	const finalWinX = roundTo(Math.min(uncapped, maxWin), 4);
	return { distanceTotal, baseWinX, uncapped, capped, finalWinX };
};

const add = (map: Map<number, number>, key: number, mass: number) => {
	map.set(key, (map.get(key) ?? 0) + mass);
};

const percentile = (map: Map<number, number>, p: number, massTotal: number) => {
	if (massTotal <= 0 || map.size === 0) return 0;
	const entries = [...map.entries()].sort((a, b) => a[0] - b[0]);
	const target = Math.min(massTotal, Math.max(0, p * massTotal));
	let acc = 0;
	for (const [value, mass] of entries) {
		acc += mass;
		if (acc >= target) return value;
	}
	return entries[entries.length - 1][0];
};

const meanStd = (sum: number, sumSq: number, mass: number) => {
	const mean = mass > 0 ? sum / mass : 0;
	const variance = mass > 0 ? Math.max(0, sumSq / mass - mean * mean) : 0;
	return { mean, variance, std: Math.sqrt(variance), cv: mean !== 0 ? Math.sqrt(variance) / mean : 0 };
};

export const auditMode = (mode: CanonicalBuyMode) => {
	const hill = HILL_TABLE[mode.hillProfile];
	const weathers = withProb(WEATHER_TABLE);
	const payFinals = withProb(MULTIPLIER_TABLES[mode.multiplierProfile as MultiplierTableId]);
	const missFinals = withProb(finalsForPayState(mode.multiplierProfile as MultiplierTableId, 0));
	const roles = SLOT_ROLES.slice(0, 5);
	const cost = mode.costMultiplier;
	const maxWin = mode.maxWin;

	let mass = 0;
	let ev = 0;
	let raw = 0;
	let capMass = 0;
	let capOvershoot = 0;
	let capOvershootSq = 0;
	const capOvershoots = new Map<number, number>();
	let maxRaw = 0;
	let vD = 0;
	let vDL = 0;
	let vDF = 0;
	let vDLF = 0;
	let payHit = 0;
	let breakeven = 0;
	let profit = 0;
	let localAny = 0;
	let localAnyWin = 0;
	let localAnyLose = 0;
	let localGe4 = 0;
	let localGe6 = 0;
	let localGe10 = 0;
	let localCount0 = 0;
	let localCount1 = 0;
	let localCount2 = 0;
	let localCount3 = 0;
	let sumSqNominal = 0;
	let sumWager = 0;
	let sumSqWager = 0;
	let high10 = 0;
	let high50 = 0;
	let high100 = 0;
	let high250 = 0;
	let high500 = 0;
	const slotLocalEvDrop = [0, 0, 0, 0, 0];
	const slotLocalEvent = [0, 0, 0, 0, 0];
	const slotHighProduct = [0, 0, 0, 0, 0];

	const weatherStats = Object.fromEntries(
		weathers.map((weather) => [
			weather.id,
			{
				p: weather.p,
			ev: 0,
			hit: 0,
			zero: 0,
			breakeven: 0,
			gt10: 0,
				gt50: 0,
				distance: 0,
				payouts: new Map<number, number>(),
			},
		]),
	) as Record<
		string,
		{
			p: number;
			ev: number;
			hit: number;
			zero: number;
			breakeven: number;
			gt10: number;
			gt50: number;
			distance: number;
			payouts: Map<number, number>;
		}
	>;

	const finalStats: Record<
		string,
		{ p: number; multiplier: number; withWin: number; withZero: number }
	> = {};
	let expectedFinalAcc = 0;

	const wagerPayouts = new Map<number, number>();
	const returnBuckets = {
		loss: 0,
		lt025: 0,
		lt05: 0,
		lt1: 0,
		ge1: 0,
		ge2: 0,
		ge5: 0,
		ge10: 0,
		ge50: 0,
	};

	const rec = (
		weather: Weighted<(typeof WEATHER_TABLE)[number]>,
		slotTables: Weighted<SlotSymbol>[][],
		index: number,
		pSlots: number,
		dist: number,
		local: number,
		localHits: number,
		localMask: number[],
	) => {
		if (index === 5) {
			const preview = settle(mode.hillProfile, weather.distanceDelta, dist, 1, 1, maxWin);
			const finals = preview.baseWinX > 0 ? payFinals : missFinals;
			for (const final of finals) {
				const massCombo = pSlots * final.p * weather.p;
				if (massCombo <= 0) continue;
				mass += massCombo;
				const full = settle(mode.hillProfile, weather.distanceDelta, dist, local, final.multiplier, maxWin);
				const onlyD = settle(mode.hillProfile, weather.distanceDelta, dist, 1, 1, maxWin);
				const dL = settle(mode.hillProfile, weather.distanceDelta, dist, local, 1, maxWin);
				const dF = settle(mode.hillProfile, weather.distanceDelta, dist, 1, final.multiplier, maxWin);
				ev += massCombo * full.finalWinX;
				raw += massCombo * full.uncapped;
				vD += massCombo * onlyD.finalWinX;
				vDL += massCombo * dL.finalWinX;
				vDF += massCombo * dF.finalWinX;
				vDLF += massCombo * full.finalWinX;
				sumSqNominal += massCombo * full.finalWinX * full.finalWinX;
				const vsWager = full.finalWinX / cost;
				sumWager += massCombo * vsWager;
				sumSqWager += massCombo * vsWager * vsWager;
				add(wagerPayouts, vsWager, massCombo);
				if (full.uncapped > maxRaw) maxRaw = full.uncapped;
				if (full.capped) {
					capMass += massCombo;
					const over = full.uncapped - maxWin;
					capOvershoot += massCombo * over;
					capOvershootSq += massCombo * over * over;
					add(capOvershoots, over, massCombo);
				}
				if (full.finalWinX > 0) payHit += massCombo;
				if (full.finalWinX >= cost) breakeven += massCombo;
				if (full.finalWinX > cost) profit += massCombo;
				if (vsWager > 10) high10 += massCombo;
				if (vsWager > 50) high50 += massCombo;
				if (vsWager > 100) high100 += massCombo;
				if (vsWager > 250) high250 += massCombo;
				if (vsWager > 500) high500 += massCombo;
				if (vsWager < 1) returnBuckets.loss += massCombo;
				if (vsWager < 0.25) returnBuckets.lt025 += massCombo;
				if (vsWager < 0.5) returnBuckets.lt05 += massCombo;
				if (vsWager < 1) returnBuckets.lt1 += massCombo;
				if (vsWager >= 1) returnBuckets.ge1 += massCombo;
				if (vsWager >= 2) returnBuckets.ge2 += massCombo;
				if (vsWager >= 5) returnBuckets.ge5 += massCombo;
				if (vsWager >= 10) returnBuckets.ge10 += massCombo;
				if (vsWager >= 50) returnBuckets.ge50 += massCombo;

				const ws = weatherStats[weather.id];
				ws.ev += massCombo * full.finalWinX;
				ws.distance += massCombo * full.distanceTotal;
				add(ws.payouts, vsWager, massCombo);
				if (full.finalWinX > 0) ws.hit += massCombo;
				else ws.zero += massCombo;
				if (full.finalWinX >= cost) ws.breakeven += massCombo;
				if (vsWager > 10) ws.gt10 += massCombo;
				if (vsWager > 50) ws.gt50 += massCombo;

				if (local > 1) {
					localAny += massCombo;
					if (full.finalWinX > 0) localAnyWin += massCombo;
					else localAnyLose += massCombo;
				}
				if (local >= 4) localGe4 += massCombo;
				if (local >= 6) localGe6 += massCombo;
				if (local >= 10) localGe10 += massCombo;
				if (localHits === 0) localCount0 += massCombo;
				else if (localHits === 1) localCount1 += massCombo;
				else if (localHits === 2) localCount2 += massCombo;
				else localCount3 += massCombo;

				const fs = (finalStats[final.label] ??= {
					p: 0,
					multiplier: final.multiplier,
					withWin: 0,
					withZero: 0,
				});
				fs.p += massCombo;
				expectedFinalAcc += massCombo * final.multiplier;
				if (full.finalWinX > 0) fs.withWin += massCombo;
				else fs.withZero += massCombo;

				for (let slot = 0; slot < 5; slot += 1) {
					if (localMask[slot] > 1) {
						slotLocalEvent[slot] += massCombo;
						const dropped = settle(
							mode.hillProfile,
							weather.distanceDelta,
							dist,
							local / localMask[slot],
							final.multiplier,
							maxWin,
						);
						slotLocalEvDrop[slot] += massCombo * (full.finalWinX - dropped.finalWinX);
						if (local >= 6) slotHighProduct[slot] += massCombo;
					}
				}
			}
			return;
		}
		for (const symbol of slotTables[index]) {
			rec(
				weather,
				slotTables,
				index + 1,
				pSlots * symbol.p,
				dist + symbol.distanceValue,
				local * Math.max(1, symbol.localMultiplier),
				localHits + (symbol.localMultiplier > 1 ? 1 : 0),
				[...localMask, Math.max(1, symbol.localMultiplier)],
			);
		}
	};

	const slotDistMaps = roles.map(() => new Map<number, number>());
	const slotMoments = roles.map(() => ({ sum: 0, sumSq: 0, neg: 0, local: 0, min: Infinity, max: -Infinity }));

	for (const weather of weathers) {
		const bias = clamp(weather.volatilityBias + hill.volatilityProfile, 0, 1.8);
		const slotTables = roles.map((role) =>
			withProb(applyVolatilityBias(role.symbols as SlotSymbol[], bias)),
		);
		slotTables.forEach((table, index) => {
			for (const symbol of table) {
				const massSlot = weather.p * symbol.p;
				add(slotDistMaps[index], symbol.distanceValue, massSlot);
				slotMoments[index].sum += massSlot * symbol.distanceValue;
				slotMoments[index].sumSq += massSlot * symbol.distanceValue * symbol.distanceValue;
				if (symbol.distanceValue < 0) slotMoments[index].neg += massSlot;
				if (symbol.localMultiplier > 1) slotMoments[index].local += massSlot;
				slotMoments[index].min = Math.min(slotMoments[index].min, symbol.distanceValue);
				slotMoments[index].max = Math.max(slotMoments[index].max, symbol.distanceValue);
			}
		});
		rec(weather, slotTables, 0, 1, 0, 1, 0, []);
	}

	const phiD = (1 / 3) * vD + (1 / 6) * vDL + (1 / 6) * vDF + (1 / 3) * vDLF;
	const phiL = (1 / 6) * (vDL - vD) + (1 / 3) * (vDLF - vDF);
	const phiF = (1 / 6) * (vDF - vD) + (1 / 3) * (vDLF - vDL);
	const interaction = vDLF - vDL - vDF + vD;
	const wagerMoments = meanStd(sumWager, sumSqWager, mass);

	const weatherReport = Object.fromEntries(
		Object.entries(weatherStats).map(([id, row]) => [
			id,
			{
				probability: row.p,
				conditionalEvNominal: row.p > 0 ? row.ev / row.p : 0,
				conditionalRtp: row.p > 0 ? row.ev / row.p / cost : 0,
				evShareOfTotal: ev > 0 ? row.ev / ev : 0,
				rtpContribution: row.ev / cost,
				hitRate: row.p > 0 ? row.hit / row.p : 0,
				breakevenRate: row.p > 0 ? row.breakeven / row.p : 0,
				zeroRate: row.p > 0 ? row.zero / row.p : 0,
				pGt10xWager: row.p > 0 ? row.gt10 / row.p : 0,
				pGt50xWager: row.p > 0 ? row.gt50 / row.p : 0,
				averageDistance: row.p > 0 ? row.distance / row.p : 0,
				p50: percentile(row.payouts, 0.5, row.p),
				p90: percentile(row.payouts, 0.9, row.p),
				p99: percentile(row.payouts, 0.99, row.p),
			},
		]),
	);

	const x10 = ['x10', 'x15', 'x20', 'x25', 'x40', 'x50', 'x100', 'x200'];
	const x20 = ['x20', 'x25', 'x40', 'x50', 'x100', 'x200'];
	const sumLabels = (labels: string[], field: 'p' | 'withWin' | 'withZero') =>
		labels.reduce((sum, label) => sum + (finalStats[label]?.[field] ?? 0), 0);

	return {
		id: mode.id,
		rgsKey: mode.rgsKey,
		costMultiplier: cost,
		maxWinNominal: maxWin,
		maxWinVsWager: maxWin / cost,
		probabilityMass: mass,
		rawEvNominal: raw,
		cappedEvNominal: ev,
		rtp: ev / cost,
		expectedLossVsWager: 1 - ev / cost,
		capDragNominal: raw - ev,
		capDragShareOfRaw: raw > 0 ? (raw - ev) / raw : 0,
		capFrequency: capMass,
		avgOvershootWhenCapped: capMass > 0 ? capOvershoot / capMass : 0,
		p99OvershootWhenCapped: percentile(capOvershoots, 0.99, capMass),
		maxOvershootWhenCapped: capOvershoots.size
			? Math.max(...capOvershoots.keys())
			: 0,
		maxRawUncappedNominal: maxRaw,
		expectedFinalMultiplier: expectedFinalAcc,
		payHit: payHit,
		zero: 1 - payHit,
		breakeven: breakeven,
		profit: profit,
		shapleyNominal: {
			distance: phiD,
			locals: phiL,
			final: phiF,
			sum: phiD + phiL + phiF,
			shares: {
				distance: vDLF > 0 ? phiD / vDLF : 0,
				locals: vDLF > 0 ? phiL / vDLF : 0,
				final: vDLF > 0 ? phiF / vDLF : 0,
			},
			subsets: { vD, vDL, vDF, vDLF, interaction },
			orderDLF: { d: vD, plusL: vDL - vD, plusF: vDLF - vDL },
			orderDFL: { d: vD, plusF: vDF - vD, plusL: vDLF - vDF },
		},
		wagerMoments,
		percentilesVsWager: {
			p50: percentile(wagerPayouts, 0.5, mass),
			p90: percentile(wagerPayouts, 0.9, mass),
			p95: percentile(wagerPayouts, 0.95, mass),
			p99: percentile(wagerPayouts, 0.99, mass),
			p99_9: percentile(wagerPayouts, 0.999, mass),
			p99_99: percentile(wagerPayouts, 0.9999, mass),
		},
		tailVsWager: { gt10: high10, gt50: high50, gt100: high100, gt250: high250, gt500: high500 },
		returnVsWager: returnBuckets,
		weather: weatherReport,
		locals: {
			any: localAny,
			givenWin: payHit > 0 ? localAnyWin / payHit : 0,
			givenLose: 1 - payHit > 0 ? localAnyLose / (1 - payHit) : 0,
			productGe4: localGe4,
			productGe6: localGe6,
			productGe10: localGe10,
			counts: { none: localCount0, one: localCount1, two: localCount2, threePlus: localCount3 },
			evShareShapley: vDLF > 0 ? phiL / vDLF : 0,
			perSlot: roles.map((role, index) => ({
				role: role.id,
				pLocal: slotLocalEvent[index],
				evRemovedIfForcedTo1: slotLocalEvDrop[index],
				pInHighProduct6: slotHighProduct[index],
			})),
		},
		finals: {
			table: Object.fromEntries(
				Object.entries(finalStats).map(([label, row]) => [
					label,
					{
						p: row.p,
						pWin: row.withWin,
						pZero: row.withZero,
					},
				]),
			),
			pX10plus: sumLabels(x10, 'p'),
			pX10plusAndWin: sumLabels(x10, 'withWin'),
			pX10plusAndZero: sumLabels(x10, 'withZero'),
			pX20plusAndWin: sumLabels(x20, 'withWin'),
			pX20plusAndZero: sumLabels(x20, 'withZero'),
			pX50AndWin: (finalStats.x50?.withWin ?? 0) + (finalStats.x100?.withWin ?? 0) + (finalStats.x200?.withWin ?? 0),
			pX50AndZero: (finalStats.x50?.withZero ?? 0) + (finalStats.x100?.withZero ?? 0) + (finalStats.x200?.withZero ?? 0),
		},
		slots: roles.map((role, index) => {
			const moments = meanStd(slotMoments[index].sum, slotMoments[index].sumSq, 1);
			return {
				role: role.id,
				mean: moments.mean,
				std: moments.std,
				min: slotMoments[index].min,
				max: slotMoments[index].max,
				pNegative: slotMoments[index].neg,
				pLocal: slotMoments[index].local,
				p10: percentile(slotDistMaps[index], 0.1, 1),
				p50: percentile(slotDistMaps[index], 0.5, 1),
				p90: percentile(slotDistMaps[index], 0.9, 1),
				metreShare:
					slotMoments.reduce((sum, row) => sum + row.sum, 0) === 0
						? 0
						: slotMoments[index].sum / slotMoments.reduce((sum, row) => sum + row.sum, 0),
			};
		}),
	};
};

const mcMode = (mode: CanonicalBuyMode, rounds: number, seed: number) => {
	const random = createMulberry32(seed);
	let sum = 0;
	let sumSq = 0;
	for (let i = 0; i < rounds; i += 1) {
		const round = resolveRound({
			bet: 1,
			hillId: mode.hillProfile,
			multiplierTableId: mode.multiplierProfile,
			maxWin: mode.maxWin,
			random,
		});
		sum += round.finalWinX;
		sumSq += round.finalWinX * round.finalWinX;
	}
	const mean = sum / rounds;
	const variance = Math.max(0, sumSq / rounds - mean * mean);
	const se = Math.sqrt(variance / rounds);
	return {
		rounds,
		seed,
		mcRtp: mean / mode.costMultiplier,
		seRtp: se / mode.costMultiplier,
		ci95: [
			(mean - 1.96 * se) / mode.costMultiplier,
			(mean + 1.96 * se) / mode.costMultiplier,
		],
	};
};

export const runMathAuditCli = () => {
	const skipMc = process.argv.includes('--skip-mc') || process.argv.includes('--exact-only');
	const rounds = Number(process.argv.find((arg) => arg.startsWith('--rounds='))?.split('=')[1] ?? 1_000_000);
	const seed = Number(process.argv.find((arg) => arg.startsWith('--seed='))?.split('=')[1] ?? 7);
	const modes = publishedModes();
	const exact = modes.map(auditMode);
	const monteCarlo = skipMc
		? modes.map(() => ({
				rounds: 0,
				seed,
				mcRtp: 0,
				seRtp: 0,
				ci95: [0, 0] as [number, number],
			}))
		: modes.map((mode) => mcMode(mode, rounds, seed));

	const report = {
		mathVersion: MATH_VERSION,
		targetRtp: TARGET_RTP,
		configSha256: createHash('sha256').update(readFileSync(CONFIG_PATH)).digest('hex'),
		enumeratorNotes: {
			includes: [
				'weather probability',
				'slots 1-5 with weather+hill volatility bias',
				'slot 6 pay-state miss table for standard (plus/max stay independent floors)',
				'payout curve',
				'local product',
				'final multiplier',
				'mode maxWin cap',
			],
			ignoresFlavorRng: 'temperature/wind/visibility do not affect settlement',
		},
		modes: exact.map((row, index) => ({
			...row,
			monteCarlo: {
				...monteCarlo[index],
				exactMinusMc: row.rtp - monteCarlo[index].mcRtp,
				exactInsideCi:
					row.rtp >= monteCarlo[index].ci95[0] && row.rtp <= monteCarlo[index].ci95[1],
			},
		})),
	};

	const out = resolve(dirname(fileURLToPath(import.meta.url)), 'math-audit.json');
	writeFileSync(out, JSON.stringify(report, null, 2));
	console.log(
		JSON.stringify(
			{
				wrote: out,
				mass: exact.map((row) => [row.rgsKey, row.probabilityMass]),
				rtp: exact.map((row) => [row.rgsKey, row.rtp, row.payHit, row.breakeven, row.profit]),
				mc: report.modes.map((row) => [
					row.rgsKey,
					row.monteCarlo.mcRtp,
					row.monteCarlo.exactInsideCi,
					row.monteCarlo.exactMinusMc,
				]),
			},
			null,
			2,
		),
	);
};

if (process.argv[1] && /mathAudit\.ts$/i.test(process.argv[1].replaceAll('\\', '/'))) {
	runMathAuditCli();
}
