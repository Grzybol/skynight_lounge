import {
	BUY_MODES,
	HILL_TABLE,
	MULTIPLIER_TABLES,
	SLOT_ROLES,
	VOLATILITY_MODEL,
	WEATHER_TABLE,
} from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import { applyVolatilityBias, finalsForPayState, lookupPayout } from '../../frontend/apps/poc/src/game/skyjump/resolveRound.ts';
import { clamp, roundTo } from '../../frontend/apps/poc/src/game/skyjump/rng.ts';
import type { CanonicalBuyMode } from '../../frontend/apps/poc/src/game/skyjump/config.ts';
import type { HillId, MultiplierTableId, SlotSymbol } from '../../frontend/apps/poc/src/game/skyjump/types.ts';

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

export type ExactModeReport = {
	id: string;
	rgsKey: string;
	hillProfile: HillId;
	multiplierProfile: MultiplierTableId;
	costMultiplier: number;
	maxWin: number;
	combinations: number;
	probabilityMass: number;
	/** E[finalWinX] vs nominal bet. Book amount 100 = this 1.0. */
	expectedPayoutNominal: number;
	/** Actual Stake wager = nominal bet * costMultiplier. */
	actualWagerUnit: number;
	/** RTP = expectedPayoutNominal / costMultiplier. */
	rtpVsActualWager: number;
	rawUncappedNominal: number;
	capDragNominal: number;
	capFrequency: number;
	hitRate: number;
	zeroRate: number;
	avgWinOnHitNominal: number;
	expectedBaseWinX: number;
	expectedLocalMultiplier: number;
	expectedFinalMultiplier: number;
	expectedDistance: number;
	evDistanceOnly: number;
	evWithLocalsFinal1: number;
	evWithFinalLocals1: number;
	weatherEv: Record<string, number>;
	slotLocalHitRate: Record<string, number>;
	slotExpectedDistance: Record<string, number>;
};

const enumerateProfile = (hillId: HillId, multiplierTableId: MultiplierTableId, maxWin: number) => {
	const hill = HILL_TABLE[hillId];
	const weathers = withProb(WEATHER_TABLE);
	const payFinals = withProb(MULTIPLIER_TABLES[multiplierTableId]);
	const missRows = finalsForPayState(multiplierTableId, 0);
	const missFinals = withProb(missRows);
	const roles = SLOT_ROLES.slice(0, 5);

	let expectedPayout = 0;
	let rawUncapped = 0;
	let capMass = 0;
	let hitMass = 0;
	let expectedBase = 0;
	let expectedLocal = 0;
	let expectedFinal = 0;
	let expectedDistance = 0;
	let evDistanceOnly = 0;
	let evLocals = 0;
	let evFinals = 0;
	let combinations = 0;
	let probabilityMass = 0;
	const weatherEv: Record<string, number> = {};
	const slotLocalHit: Record<string, number> = {};
	const slotExpectedDistance: Record<string, number> = {};
	for (const role of roles) {
		slotLocalHit[role.id] = 0;
		slotExpectedDistance[role.id] = 0;
	}

	for (const weather of weathers) {
		const bias = clamp(weather.volatilityBias + hill.volatilityProfile, 0, VOLATILITY_MODEL.biasClamp);
		const slotTables = roles.map((role) => withProb(applyVolatilityBias(role.symbols as SlotSymbol[], bias)));
		let weatherPay = 0;

		const rec = (index: number, p: number, dist: number, local: number, localsHit: number[]) => {
			if (index === 5) {
				const preview = settle(hillId, weather.distanceDelta, dist, 1, 1, maxWin);
				const finals = preview.baseWinX > 0 ? payFinals : missFinals;
				for (const final of finals) {
					const mass = p * final.p * weather.p;
					if (mass <= 0) continue;
					combinations += 1;
					probabilityMass += mass;
					const full = settle(hillId, weather.distanceDelta, dist, local, final.multiplier, maxWin);
					const distanceOnly = settle(hillId, weather.distanceDelta, dist, 1, 1, maxWin);
					const localsOnly = settle(hillId, weather.distanceDelta, dist, local, 1, maxWin);
					const finalsOnly = settle(hillId, weather.distanceDelta, dist, 1, final.multiplier, maxWin);
					expectedPayout += mass * full.finalWinX;
					rawUncapped += mass * full.uncapped;
					if (full.capped) capMass += mass;
					if (full.finalWinX > 0) hitMass += mass;
					expectedBase += mass * full.baseWinX;
					expectedLocal += mass * local;
					expectedFinal += mass * final.multiplier;
					expectedDistance += mass * full.distanceTotal;
					evDistanceOnly += mass * distanceOnly.finalWinX;
					evLocals += mass * localsOnly.finalWinX;
					evFinals += mass * finalsOnly.finalWinX;
					weatherPay += mass * full.finalWinX;
				}
				return;
			}
			for (const symbol of slotTables[index]) {
				rec(
					index + 1,
					p * symbol.p,
					dist + symbol.distanceValue,
					local * Math.max(1, symbol.localMultiplier),
					[...localsHit, symbol.localMultiplier > 1 ? 1 : 0],
				);
			}
		};

		// Slot marginals under this weather (independent given bias).
		slotTables.forEach((table, index) => {
			const roleId = roles[index].id;
			for (const symbol of table) {
				slotLocalHit[roleId] += weather.p * symbol.p * (symbol.localMultiplier > 1 ? 1 : 0);
				slotExpectedDistance[roleId] += weather.p * symbol.p * symbol.distanceValue;
			}
		});

		rec(0, 1, 0, 1, []);
		weatherEv[weather.id] = weatherPay / weather.p;
	}

	return {
		combinations,
		probabilityMass,
		expectedPayout,
		rawUncapped,
		capMass,
		hitMass,
		expectedBase,
		expectedLocal,
		expectedFinal,
		expectedDistance,
		evDistanceOnly,
		evLocals,
		evFinals,
		weatherEv,
		slotLocalHit,
		slotExpectedDistance,
	};
};

export const exactModeReport = (mode: CanonicalBuyMode): ExactModeReport => {
	const stats = enumerateProfile(mode.hillProfile, mode.multiplierProfile, mode.maxWin);
	const cost = mode.costMultiplier;
	const hitRate = stats.hitMass;
	return {
		id: mode.id,
		rgsKey: mode.rgsKey,
		hillProfile: mode.hillProfile,
		multiplierProfile: mode.multiplierProfile,
		costMultiplier: cost,
		maxWin: mode.maxWin,
		combinations: stats.combinations,
		probabilityMass: stats.probabilityMass,
		expectedPayoutNominal: stats.expectedPayout,
		actualWagerUnit: cost,
		rtpVsActualWager: stats.expectedPayout / cost,
		rawUncappedNominal: stats.rawUncapped,
		capDragNominal: stats.rawUncapped - stats.expectedPayout,
		capFrequency: stats.capMass,
		hitRate,
		zeroRate: 1 - hitRate,
		avgWinOnHitNominal: hitRate > 0 ? stats.expectedPayout / hitRate : 0,
		expectedBaseWinX: stats.expectedBase,
		expectedLocalMultiplier: stats.expectedLocal,
		expectedFinalMultiplier: stats.expectedFinal,
		expectedDistance: stats.expectedDistance,
		evDistanceOnly: stats.evDistanceOnly,
		evWithLocalsFinal1: stats.evLocals,
		evWithFinalLocals1: stats.evFinals,
		weatherEv: stats.weatherEv,
		slotLocalHitRate: stats.slotLocalHit,
		slotExpectedDistance: stats.slotExpectedDistance,
	};
};

export const publishedModes = () => Object.values(BUY_MODES).filter((mode) => mode.enabled !== false);

export const exactAllModes = () => publishedModes().map(exactModeReport);
