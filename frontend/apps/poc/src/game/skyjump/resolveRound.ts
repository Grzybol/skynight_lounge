import {
	HILL_TABLE,
	MISS_FINAL_MULTIPLIER,
	MULTIPLIER_MISS_TABLES,
	MULTIPLIER_TABLES,
	ROLE_SLOT_COUNT,
	SLOT_ROLES,
	VOLATILITY_MODEL,
	WEATHER_TABLE,
} from './config.ts';
import { clamp, lerp, pickWeighted, roundTo } from './rng.ts';
import type {
	DrawnRoundInput,
	HillId,
	MultiplierOutcome,
	MultiplierTableId,
	PayoutBand,
	RoundResolveInput,
	SkyJumpRound,
	SlotRoll,
	SlotSymbol,
	WeatherConfig,
	WeatherRoll,
} from './types.ts';

export const finalsForPayState = (
	multiplierTableId: MultiplierTableId,
	baseWinX: number,
): MultiplierOutcome[] => {
	const miss = MULTIPLIER_MISS_TABLES[multiplierTableId];
	if (baseWinX <= 0 && miss && miss.length > 0) return miss;
	return MULTIPLIER_TABLES[multiplierTableId];
};

export const applyVolatilityBias = (
	symbols: SlotSymbol[],
	volatilityBias: number,
): SlotSymbol[] => {
	if (volatilityBias <= 0) return symbols;
	return symbols.map((symbol) => {
		const rareBoost =
			symbol.rarity === 'epic'
				? VOLATILITY_MODEL.epicBoost
				: symbol.rarity === 'rare'
					? VOLATILITY_MODEL.rareBoost
					: symbol.rarity === 'uncommon'
						? VOLATILITY_MODEL.uncommonBoost
						: 1;
		const commonNerf =
			symbol.rarity === 'common' ? 1 - volatilityBias * VOLATILITY_MODEL.commonNerf : 1;
		return {
			...symbol,
			weight: Math.max(
				VOLATILITY_MODEL.minWeight,
				symbol.weight * (1 + (rareBoost - 1) * volatilityBias) * commonNerf,
			),
		};
	});
};

export const lookupPayout = (curve: PayoutBand[], distance: number) => {
	const band = curve.find((entry) => distance >= entry.minDistance && distance < entry.maxDistance);
	if (band) return band.baseWinX;
	return curve[curve.length - 1]?.baseWinX ?? 0;
};

export const payoutBandAt = (curve: PayoutBand[], distance: number) => {
	const band = curve.find((entry) => distance >= entry.minDistance && distance < entry.maxDistance);
	if (band) return band;
	return (
		curve[curve.length - 1] ?? {
			minDistance: 0,
			maxDistance: 0,
			baseWinX: 0,
		}
	);
};

const rollRange = (range: [number, number], random: () => number) =>
	lerp(range[0], range[1], random());

const requireWeather = (weatherId: string): WeatherConfig => {
	const weather = WEATHER_TABLE.find((row) => row.id === weatherId);
	if (!weather) throw new Error(`Unknown weather: ${weatherId}`);
	return weather;
};

const requireSymbol = (roleIndex: number, symbolId: string): SlotSymbol => {
	const symbol = SLOT_ROLES[roleIndex]?.symbols.find((entry) => entry.id === symbolId);
	if (!symbol) throw new Error(`Unknown slot symbol: ${symbolId}`);
	return symbol;
};

const requireMultiplier = (tableId: MultiplierTableId, multiplierId: string) => {
	const row =
		MULTIPLIER_TABLES[tableId]?.find((entry) => entry.id === multiplierId) ??
		MULTIPLIER_MISS_TABLES[tableId]?.find((entry) => entry.id === multiplierId);
	if (!row) throw new Error(`Unknown final multiplier: ${multiplierId}`);
	return row;
};

export const settleRound = ({
	bet,
	hillId,
	multiplierTableId,
	weather,
	slots,
	finalMultiplier,
	maxWin,
	costMultiplier = 1,
}: {
	bet: number;
	hillId: HillId;
	multiplierTableId: MultiplierTableId;
	weather: WeatherRoll;
	slots: SlotRoll[];
	finalMultiplier: SkyJumpRound['finalMultiplier'];
	maxWin?: number;
	costMultiplier?: number;
}): SkyJumpRound => {
	const hill = HILL_TABLE[hillId];
	if (!hill) throw new Error(`Unknown hill: ${hillId}`);
	const cap = maxWin ?? hill.maxWin;
	const distanceTotal = roundTo(
		Math.max(
			0,
			hill.baseDistance +
				weather.distanceDelta +
				slots.reduce((sum, slot) => sum + slot.distanceValue, 0),
		),
		1,
	);
	const baseWinX = lookupPayout(hill.payoutCurve, distanceTotal);
	const resolvedFinal = baseWinX <= 0 ? { ...MISS_FINAL_MULTIPLIER } : finalMultiplier;
	const localFactors = slots
		.map((slot) => Math.max(1, slot.localMultiplier))
		.filter((value) => value > 1);
	const localMultiplier = slots.reduce(
		(product, slot) => product * Math.max(1, slot.localMultiplier),
		1,
	);
	const uncapped = roundTo(baseWinX * localMultiplier * resolvedFinal.multiplier, 4);
	const capped = uncapped > cap;
	const finalWinX = roundTo(Math.min(uncapped, cap), 4);
	// moneyWin is debug/presentation only. Settlement uses roundBookAmount(finalWinX).
	const moneyWin = roundTo(Math.max(0, bet) * finalWinX, 2);

	return {
		bet,
		hillId,
		multiplierTableId,
		weather,
		slots,
		finalMultiplier: resolvedFinal,
		distanceTotal,
		baseWinX,
		localMultiplier,
		localFactors,
		finalWinX,
		capped,
		isCapped: capped,
		maxWin: cap,
		moneyWin,
		costMultiplier,
	};
};

export const evaluateDrawnRound = (input: DrawnRoundInput): SkyJumpRound => {
	const weatherBase = requireWeather(input.weatherId);
	const weather: WeatherRoll = {
		...weatherBase,
		temperatureC: input.temperatureC,
		windSpeedMs: input.windSpeedMs,
		visibilityPct: input.visibilityPct,
	};
	if (input.slotIds.length !== ROLE_SLOT_COUNT) {
		throw new Error(`Expected ${ROLE_SLOT_COUNT} slot ids`);
	}
	const slots: SlotRoll[] = input.slotIds.map((symbolId, reelIndex) => {
		const symbol = requireSymbol(reelIndex, symbolId);
		return {
			...symbol,
			roleId: SLOT_ROLES[reelIndex].id,
			reelIndex,
			localMultiplier: Math.max(1, symbol.localMultiplier),
		};
	});
	return settleRound({
		bet: input.bet,
		hillId: input.hillId,
		multiplierTableId: input.multiplierTableId,
		weather,
		slots,
		finalMultiplier: requireMultiplier(input.multiplierTableId, input.finalMultiplierId),
		maxWin: input.maxWin,
		costMultiplier: input.costMultiplier,
	});
};

export const resolveRound = ({
	bet,
	hillId,
	multiplierTableId,
	maxWin,
	costMultiplier = 1,
	random = Math.random,
}: RoundResolveInput): SkyJumpRound => {
	const hill = HILL_TABLE[hillId];
	if (!hill) throw new Error(`Unknown hill: ${hillId}`);
	if (!MULTIPLIER_TABLES[multiplierTableId])
		throw new Error(`Unknown multiplier table: ${multiplierTableId}`);

	const weatherBase = pickWeighted(WEATHER_TABLE, random);
	const weather: WeatherRoll = {
		...weatherBase,
		temperatureC: roundTo(rollRange(weatherBase.temperatureRange, random), 1),
		windSpeedMs: roundTo(rollRange(weatherBase.windSpeedRange, random), 1),
		visibilityPct: Math.round(rollRange(weatherBase.visibilityRange, random)),
	};

	const combinedBias = clamp(
		weather.volatilityBias + hill.volatilityProfile,
		0,
		VOLATILITY_MODEL.biasClamp,
	);
	const slots: SlotRoll[] = SLOT_ROLES.slice(0, ROLE_SLOT_COUNT).map((role, reelIndex) => {
		const table = applyVolatilityBias(role.symbols, combinedBias);
		const symbol = pickWeighted(table, random);
		return {
			...symbol,
			roleId: role.id,
			reelIndex,
			localMultiplier: Math.max(1, symbol.localMultiplier),
		};
	});

	const distanceTotal = roundTo(
		Math.max(
			0,
			hill.baseDistance +
				weather.distanceDelta +
				slots.reduce((sum, slot) => sum + slot.distanceValue, 0),
		),
		1,
	);
	const baseWinX = lookupPayout(hill.payoutCurve, distanceTotal);
	const finalMultiplier = pickWeighted(finalsForPayState(multiplierTableId, baseWinX), random);

	return settleRound({
		bet,
		hillId,
		multiplierTableId,
		weather,
		slots,
		finalMultiplier,
		maxWin,
		costMultiplier,
	});
};

export const modeTables = (hillId: HillId, multiplierTableId: MultiplierTableId) => ({
	hill: HILL_TABLE[hillId],
	multipliers: MULTIPLIER_TABLES[multiplierTableId],
});
