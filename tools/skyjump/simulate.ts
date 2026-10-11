/**
 * SkyJump developer simulator.
 *
 * Stake wager semantics (from rgs-requests + GameConfig + book amounts):
 * - Client sends nominal `betAmount` + `mode` to /wallet/play.
 * - RGS debit = betAmount * BetMode.cost (costMultiplier).
 * - Book `amount` is vs the nominal bet: 100 = 1.0x betAmount cash.
 * - Frontend cash = wageredBetAmount * (bookAmount / 100), wageredBetAmount = betAmount.
 * Therefore RTP vs actual wager = E[finalWinX] / costMultiplier.
 *
 * Pre-certification developer math. Not a published PAR.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { createMulberry32 } from '../../frontend/apps/poc/src/game/skyjump/rng.ts';
import { resolveRound } from '../../frontend/apps/poc/src/game/skyjump/resolveRound.ts';
import {
	MATH_VERSION,
	SLOT_ROLES,
	TARGET_RTP,
	WEATHER_TABLE,
} from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import type { CanonicalBuyMode } from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import { exactModeReport, publishedModes } from './exactEv.ts';

const CONFIG_PATH = resolve(
	dirname(fileURLToPath(import.meta.url)),
	'../../math/games/0_0_poc/skyjump_config.json',
);

const argValue = (name: string) => process.argv.find((arg) => arg.startsWith(`--${name}=`))?.split('=')[1];
const hasFlag = (name: string) => process.argv.includes(`--${name}`);

const rounds = Number(argValue('rounds') ?? 200_000);
const seed = Number(argValue('seed') ?? 7);
const modeArg = (argValue('mode') ?? '').toUpperCase();
const allModes = hasFlag('all-modes') || !modeArg;
const exactOnly = hasFlag('exact-only');

const configHash = createHash('sha256').update(readFileSync(CONFIG_PATH)).digest('hex');

const percentile = (sorted: Float64Array, p: number) => {
	if (sorted.length === 0) return 0;
	const index = Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * p));
	return sorted[index];
};

const wagerBucket = (winVsWager: number) => {
	if (winVsWager <= 0) return '0x';
	if (winVsWager < 0.5) return '0–0.5x';
	if (winVsWager < 1) return '0.5–1x';
	if (winVsWager < 2) return '1–2x';
	if (winVsWager < 5) return '2–5x';
	if (winVsWager < 10) return '5–10x';
	if (winVsWager < 25) return '10–25x';
	if (winVsWager < 50) return '25–50x';
	if (winVsWager < 100) return '50–100x';
	if (winVsWager < 500) return '100–500x';
	if (winVsWager < 1000) return '500–1000x';
	return '1000x+';
};

const localProductBucket = (local: number) => {
	if (local <= 1) return 'none';
	if (local < 2.5) return 'x2–x3';
	if (local < 5.5) return 'x4–x5';
	if (local < 10.5) return 'x6–x10';
	return 'x10+';
};

const selectModes = (): CanonicalBuyMode[] => {
	const enabled = publishedModes();
	if (allModes) return enabled;
	const found = enabled.find(
		(mode) => mode.rgsKey === modeArg || mode.id.toUpperCase() === modeArg || mode.id === argValue('mode'),
	);
	if (!found) {
		throw new Error(`Unknown mode ${modeArg}. Use --mode=BASE or --all-modes`);
	}
	return [found];
};

const simulateMode = (mode: CanonicalBuyMode, random: () => number) => {
	const exact = exactModeReport(mode);
	if (exactOnly) {
		return { exact, monteCarlo: null as null };
	}

	const payouts = new Float64Array(rounds);
	const distances = new Float64Array(rounds);
	const weatherFreq: Record<string, number> = Object.fromEntries(WEATHER_TABLE.map((row) => [row.id, 0]));
	const slotFreq = SLOT_ROLES.slice(0, 5).map(() => ({} as Record<string, number>));
	const localCountFreq = { 0: 0, 1: 0, 2: 0, '3+': 0 };
	const localProductFreq: Record<string, number> = {};
	const finalFreq: Record<string, number> = {};
	const baseWinFreq: Record<string, number> = {};
	const wagerBuckets: Record<string, number> = {};
	let sum = 0;
	let sumSq = 0;
	let hits = 0;
	let capHits = 0;
	let maxPayout = 0;
	let rawSum = 0;

	for (let i = 0; i < rounds; i += 1) {
		const round = resolveRound({
			bet: 1,
			hillId: mode.hillProfile,
			multiplierTableId: mode.multiplierProfile,
			maxWin: mode.maxWin,
			random,
		});
		payouts[i] = round.finalWinX;
		distances[i] = round.distanceTotal;
		sum += round.finalWinX;
		sumSq += round.finalWinX * round.finalWinX;
		rawSum += round.baseWinX * round.localMultiplier * round.finalMultiplier.multiplier;
		if (round.finalWinX > 0) hits += 1;
		if (round.capped) capHits += 1;
		if (round.finalWinX > maxPayout) maxPayout = round.finalWinX;
		weatherFreq[round.weather.id] += 1;
		round.slots.forEach((slot, index) => {
			slotFreq[index][slot.id] = (slotFreq[index][slot.id] ?? 0) + 1;
		});
		const localHits = round.slots.filter((slot) => slot.localMultiplier > 1).length;
		if (localHits >= 3) localCountFreq['3+'] += 1;
		else localCountFreq[localHits as 0 | 1 | 2] += 1;
		const productKey = localProductBucket(round.localMultiplier);
		localProductFreq[productKey] = (localProductFreq[productKey] ?? 0) + 1;
		finalFreq[round.finalMultiplier.label] = (finalFreq[round.finalMultiplier.label] ?? 0) + 1;
		baseWinFreq[`x${round.baseWinX}`] = (baseWinFreq[`x${round.baseWinX}`] ?? 0) + 1;
		const bucket = wagerBucket(round.finalWinX / mode.costMultiplier);
		wagerBuckets[bucket] = (wagerBuckets[bucket] ?? 0) + 1;
	}

	payouts.sort();
	distances.sort();
	const mean = sum / rounds;
	const variance = Math.max(0, sumSq / rounds - mean * mean);
	const hitRate = hits / rounds;
	const toShare = (count: number) => Number((count / rounds).toFixed(6));

	return {
		exact,
		monteCarlo: {
			rounds,
			seed,
			averagePayoutNominal: mean,
			rtpVsActualWager: mean / mode.costMultiplier,
			hitRate,
			zeroWinRate: 1 - hitRate,
			avgWinOnHitNominal: hits ? sum / hits : 0,
			avgWinOnHitVsWager: hits ? sum / hits / mode.costMultiplier : 0,
			maxObservedNominal: maxPayout,
			maxWinCap: mode.maxWin,
			capHitFrequency: capHits / rounds,
			stdDevNominal: Math.sqrt(variance),
			varianceNominal: variance,
			rawAverageUncappedNominal: rawSum / rounds,
			payoutPercentilesVsWager: {
				p50: percentile(payouts, 0.5) / mode.costMultiplier,
				p75: percentile(payouts, 0.75) / mode.costMultiplier,
				p90: percentile(payouts, 0.9) / mode.costMultiplier,
				p95: percentile(payouts, 0.95) / mode.costMultiplier,
				p99: percentile(payouts, 0.99) / mode.costMultiplier,
				p99_9: percentile(payouts, 0.999) / mode.costMultiplier,
			},
			distancePercentiles: {
				p10: percentile(distances, 0.1),
				p25: percentile(distances, 0.25),
				p50: percentile(distances, 0.5),
				p75: percentile(distances, 0.75),
				p90: percentile(distances, 0.9),
				p95: percentile(distances, 0.95),
				p99: percentile(distances, 0.99),
			},
			wagerBuckets: Object.fromEntries(
				Object.entries(wagerBuckets)
					.sort(([a], [b]) => a.localeCompare(b))
					.map(([key, count]) => [key, toShare(count)]),
			),
			weatherDistribution: Object.fromEntries(
				Object.entries(weatherFreq).map(([key, count]) => [key, toShare(count)]),
			),
			slotDistributions: slotFreq.map((freq, index) => ({
				role: SLOT_ROLES[index].id,
				symbols: Object.fromEntries(
					Object.entries(freq)
						.sort((a, b) => b[1] - a[1])
						.map(([key, count]) => [key, toShare(count)]),
				),
			})),
			localMultiplierCounts: {
				none: toShare(localCountFreq[0]),
				one: toShare(localCountFreq[1]),
				two: toShare(localCountFreq[2]),
				threePlus: toShare(localCountFreq['3+']),
			},
			localProductDistribution: Object.fromEntries(
				Object.entries(localProductFreq).map(([key, count]) => [key, toShare(count)]),
			),
			finalMultiplierDistribution: Object.fromEntries(
				Object.entries(finalFreq)
					.sort((a, b) => Number(a[0].slice(1)) - Number(b[0].slice(1)))
					.map(([key, count]) => [key, toShare(count)]),
			),
			baseWinXDistribution: Object.fromEntries(
				Object.entries(baseWinFreq).map(([key, count]) => [key, toShare(count)]),
			),
		},
	};
};

const modes = selectModes();
const report = {
	note: 'Pre-certification developer math. RTP is vs actual wager = nominal bet * costMultiplier.',
	mathVersion: MATH_VERSION,
	targetRtp: TARGET_RTP,
	configPath: CONFIG_PATH,
	configSha256: configHash,
	eventSchemaVersion: 1,
	rounds: exactOnly ? 0 : rounds,
	seed,
	wagerSemantics: {
		nominalBet: 1,
		bookAmount100Means: '1.0 × nominal betAmount cash',
		actualWager: 'nominal betAmount × mode costMultiplier (RGS debit)',
		rtp: 'E[finalWinX] / costMultiplier',
	},
	modes: modes.map((mode) => simulateMode(mode, createMulberry32(seed))),
};

console.log(JSON.stringify(report, null, 2));
const outPath = argValue('out');
if (outPath) {
	writeFileSync(outPath, JSON.stringify(report, null, 2));
}
