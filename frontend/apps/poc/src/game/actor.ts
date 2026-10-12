import _ from 'lodash';

import { stateBet } from 'state-shared';
import { createPrimaryMachines, createIntermediateMachines, createGameActor } from 'utils-xstate';

import type { Bet } from './typesBookEvent';
import { stateXstateDerived } from './stateXstate';
import { playBet, convertTorResumableBet } from './utils';
import { eventEmitter } from './eventEmitter';
import { stateGame } from './stateGame.svelte';
import { getSkyJumpTimings } from './skyjump/timings';
import { HILL_TABLE, paylineDistance } from './skyjump/config';
import { checkIsBonusGame as v2CheckIsBonusGame } from './skyjump_v2/checkIsBonusGame';

const requestLocalDemoOverrides = import.meta.env.DEV
	? {
			requestBetOverride: async () => {
				const { requestLocalDemoBet } = await import('./localDemo');
				return requestLocalDemoBet();
			},
			requestEndRoundOverride: async () => {
				const { requestLocalDemoEndRound } = await import('./localDemo');
				return requestLocalDemoEndRound();
			},
		}
	: {
			requestBetOverride: undefined,
			requestEndRoundOverride: undefined,
		};

const primaryMachines = createPrimaryMachines<Bet>({
	onResumeGameActive: (betToResume) => convertTorResumableBet(betToResume),
	onResumeGameInactive: (betToResume) => {
		const lastWeather = _.findLast(
			betToResume.state,
			(bookEvent) => bookEvent?.type === 'skyjumpWeather',
		);
		if (lastWeather && lastWeather.type === 'skyjumpWeather') {
			stateGame.lastWeather = lastWeather.weather;
			eventEmitter.broadcast({
				type: 'skyjumpWeatherShow',
				weather: lastWeather.weather,
				winnerId: lastWeather.winnerId,
				candidates: [],
				timings: getSkyJumpTimings(true),
				catchUp: true,
			});
		}
		eventEmitter.broadcast({ type: 'skyjumpSlotsPrepare' });
		const slotEvents = betToResume.state.filter((bookEvent) => bookEvent?.type === 'skyjumpSlot');
		for (const slotEvent of slotEvents) {
			if (slotEvent.type !== 'skyjumpSlot') continue;
			if (slotEvent.slotIndex === 6 && slotEvent.finalMultiplier) {
				const resultEvent = _.findLast(
					betToResume.state,
					(bookEvent) => bookEvent?.type === 'skyjumpResult',
				);
				const belowPayline =
					(resultEvent?.type === 'skyjumpResult' &&
						resultEvent.distanceTotal < paylineDistance(resultEvent.hillId)) ||
					slotEvent.finalMultiplier.multiplier <= 0;
				if (belowPayline) {
					eventEmitter.broadcast({ type: 'skyjumpBaseLocked' });
					eventEmitter.broadcast({ type: 'skyjumpFinalLocked' });
					continue;
				}
				if (resultEvent?.type === 'skyjumpResult') {
					const hillId = resultEvent.hillId as HillId;
					eventEmitter.broadcast({
						type: 'skyjumpBaseCount',
						hillId,
						hillMetres: HILL_TABLE[hillId]?.baseDistance ?? 0,
						weatherMetres:
							lastWeather?.type === 'skyjumpWeather' ? lastWeather.weather.distanceDelta : 0,
						flightMetres: resultEvent.slots.reduce(
							(sum, slot) => sum + (slot.distanceValue ?? 0),
							0,
						),
						distanceTotal: resultEvent.distanceTotal,
						baseWinX: resultEvent.baseWinX,
						timings: getSkyJumpTimings(true),
						catchUp: true,
					});
				}
				eventEmitter.broadcast({
					type: 'skyjumpFinalMultiplierReveal',
					finalMultiplier: slotEvent.finalMultiplier,
					timings: getSkyJumpTimings(true),
					catchUp: true,
				});
				continue;
			}
			eventEmitter.broadcast({
				type: 'skyjumpSlotReveal',
				slot: {
					reelIndex: slotEvent.reelIndex,
					label: slotEvent.label ?? '',
					distanceValue: slotEvent.distanceValue ?? 0,
					localMultiplier: slotEvent.localMultiplier ?? 1,
					rarity: slotEvent.rarity,
				},
				timings: getSkyJumpTimings(true),
				catchUp: true,
			});
		}
	},
	onNewGameStart: async () => {
		stateGame.resumeCatchUp = false;
		stateGame.lastWeather = null;
		stateGame.weatherDrawing = false;
		stateBet.overlayOpen = false;
		eventEmitter.broadcast({ type: 'skyjumpResetBoard' });
		eventEmitter.broadcast({ type: 'skyjumpV2Reset' });
		const autoBetting = stateXstateDerived.isAutoBetting();
		if ((stateBet.isTurbo && autoBetting) || stateBet.isSpaceHold) return;
	},
	onNewGameError: () => {
		stateBet.overlayOpen = false;
		eventEmitter.broadcast({ type: 'skyjumpResetBoard' });
		eventEmitter.broadcast({ type: 'skyjumpV2Reset' });
	},
	onPlayGame: async (bet) => await playBet(bet),
	checkIsBonusGame: (bet) => v2CheckIsBonusGame(bet),
	...requestLocalDemoOverrides,
});

const intermediateMachines = createIntermediateMachines(primaryMachines);

export const gameActor = createGameActor(intermediateMachines);
