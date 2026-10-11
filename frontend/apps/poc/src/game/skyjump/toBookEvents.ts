import { EVENT_SCHEMA_VERSION, SLOT_ROLES } from './config.ts';
import { economicFromPayout, winLevelForReturn } from './economics.ts';
import { roundBookAmount } from './roundBookAmount.ts';
import type { SkyJumpRound } from './types.ts';

const withSchema = (index: number, type: string) => ({
	index,
	type,
	schemaVersion: EVENT_SCHEMA_VERSION,
});

export const roundToBookEvents = (round: SkyJumpRound) => {
	const amount = roundBookAmount(round.finalWinX);
	const economics = economicFromPayout(round.finalWinX, round.costMultiplier ?? 1);
	const winLevel = winLevelForReturn(round.finalWinX, round.costMultiplier ?? 1);
	const roles = SLOT_ROLES.map((role) => ({
		id: role.id,
		index: role.index,
		label: role.shortLabel,
		iconKey: role.iconKey,
	}));
	const events: Record<string, unknown>[] = [
		{
			...withSchema(0, 'skyjumpWeather'),
			weatherId: round.weather.id,
			weather: {
				id: round.weather.id,
				label: round.weather.label,
				iconKey: round.weather.iconKey,
				temperatureC: round.weather.temperatureC,
				windSpeedMs: round.weather.windSpeedMs,
				windDirection: round.weather.windDirection,
				visibilityPct: round.weather.visibilityPct,
				distanceDelta: round.weather.distanceDelta,
			},
			winnerId: round.weather.id,
		},
	];

	for (const slot of round.slots) {
		const slotIndex = slot.reelIndex + 1;
		events.push({
			...withSchema(slotIndex, 'skyjumpSlot'),
			slotIndex,
			role: slot.roleId,
			symbolId: slot.id,
			id: slot.id,
			label: slot.label,
			distanceValue: slot.distanceValue,
			localMultiplier: slot.localMultiplier,
			rarity: slot.rarity,
			artKey: slot.artKey,
			reelIndex: slot.reelIndex,
			roleId: slot.roleId,
		});
	}

	events.push({
		...withSchema(6, 'skyjumpSlot'),
		slotIndex: 6,
		role: 'finalMultiplier',
		finalMultiplier: {
			id: round.finalMultiplier.id,
			label: round.finalMultiplier.label,
			multiplier: round.finalMultiplier.multiplier,
		},
		label: round.finalMultiplier.label,
		reelIndex: 5,
		roleId: 'multiplier',
	});

	events.push({
		...withSchema(7, 'skyjumpResult'),
		hillId: round.hillId,
		hillProfile: round.hillId,
		multiplierTableId: round.multiplierTableId,
		multiplierProfile: round.multiplierTableId,
		distanceTotal: round.distanceTotal,
		baseWinX: round.baseWinX,
		localMultiplier: round.localMultiplier,
		localFactors: round.localFactors,
		finalMultiplier: round.finalMultiplier.multiplier,
		finalWinX: round.finalWinX,
		moneyWin: round.moneyWin, // debug/presentation only; settlement uses amount
		capped: round.capped,
		isCapped: round.isCapped,
		maxWin: round.maxWin,
		costMultiplier: economics.actualWagerMultiplier,
		returnMultiplier: economics.returnMultiplier,
		netMultiplier: economics.netMultiplier,
		isPayHit: economics.isPayHit,
		isBreakEven: economics.isBreakEven,
		isProfit: economics.isProfit,
		amount,
		roles,
		slots: round.slots.map((slot) => ({
			roleId: slot.roleId,
			label: slot.label,
			distanceValue: slot.distanceValue,
			localMultiplier: slot.localMultiplier,
		})),
	});

	if (round.capped) {
		events.push({ index: 8, type: 'wincap', amount });
	} else if (amount > 0) {
		events.push({
			index: 8,
			type: 'setWin',
			amount,
			winLevel,
		});
	}

	events.push({ index: events.length, type: 'setTotalWin', amount });
	events.push({ index: events.length, type: 'finalWin', amount });
	return events;
};

let spinIndex = 0;

export const roundToBet = (round: SkyJumpRound) => {
	spinIndex += 1;
	const events = roundToBookEvents(round);
	return {
		id: 30_000 + spinIndex,
		active: false,
		payoutMultiplier: round.finalWinX,
		events,
		state: events,
		criteria: `${round.hillId}:${round.multiplierTableId}`,
		baseGameWins: round.finalWinX,
		freeGameWins: 0,
	};
};

export const resetSkyJumpSpinIndex = () => {
	spinIndex = 0;
};

export const authoritativeFromEvents = (
	events: Array<{ type: string } & Record<string, unknown>>,
) => {
	const result = events.find((event) => event.type === 'skyjumpResult') as
		| {
				distanceTotal: number;
				baseWinX: number;
				localMultiplier: number;
				finalMultiplier: number;
				finalWinX: number;
		  }
		| undefined;
	const total = events.find((event) => event.type === 'setTotalWin') as
		| { amount: number }
		| undefined;
	if (!result || !total) throw new Error('Book is missing authoritative settlement events');
	return {
		distance: result.distanceTotal,
		baseWinX: result.baseWinX,
		localMultiplier: result.localMultiplier,
		finalMultiplier: result.finalMultiplier,
		finalWinX: result.finalWinX,
		amount: total.amount,
	};
};

export const splitBookAfter = (
	events: Array<{ type: string; slotIndex?: number }>,
	afterType: string,
	slotIndex?: number,
) => {
	let splitAt = 0;
	for (let i = 0; i < events.length; i += 1) {
		const event = events[i];
		if (
			afterType === 'skyjumpSlot' &&
			event.type === 'skyjumpSlot' &&
			event.slotIndex === slotIndex
		) {
			splitAt = i + 1;
			break;
		}
		if (event.type === afterType && afterType !== 'skyjumpSlot') {
			splitAt = i + 1;
			break;
		}
	}
	return { before: events.slice(0, splitAt), after: events.slice(splitAt) };
};
