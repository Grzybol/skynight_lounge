import _ from 'lodash';

import { recordBookEvent, type BookEventHandlerMap } from 'utils-book';
import { stateBet } from 'state-shared';
import { waitForTimeout } from 'utils-shared/wait';

import { eventEmitter } from './eventEmitter';
import { playBookEvent } from './utils';
import { stateGame } from './stateGame.svelte';
import type { BookEvent, BookEventOfType, BookEventContext } from './typesBookEvent';
import { HILL_TABLE, WEATHER_TABLE, paylineDistance } from './skyjump/config';
import type { HillId } from './skyjump/types';
import { getSkyJumpTimings } from './skyjump/timings';
import { waitForPaint } from './skyjump/paint';
import { SKYJUMP_SFX, reelStopSfx } from './skyjump/audio';
import {
	playResultSting,
	startJumpActionBed,
	startResultAnticipation,
	stopJumpActionBed,
} from './skyjump/skyjumpAudio';
import { getV2TimingsForState } from './skyjump_v2/timings';
import { applyBonusHudEvent, bonusHud } from './skyjump_v2/bonusHud.svelte';
import { lockV2Presentation, unlockV2Presentation } from './skyjump_v2/presentationLock';
import { playV2AudioHook } from './skyjump_v2/audio';

const activeTimings = () => getSkyJumpTimings(stateBet.isTurbo || stateGame.resumeCatchUp);
const v2Timings = () => getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
const audioOpts = () => ({ catchUp: stateGame.resumeCatchUp });

const resultFromBook = (bookEvents: BookEvent[] = []) =>
	bookEvents.find(
		(event): event is Extract<BookEventOfType<'skyjumpResult'>, { distanceTotal: number }> =>
			event.type === 'skyjumpResult' && 'distanceTotal' in event,
	);

const isV2Result = (
	event: BookEventOfType<'skyjumpResult'>,
): event is Extract<BookEventOfType<'skyjumpResult'>, { totalLineWinX: number }> =>
	event.schemaVersion === 2 && 'totalLineWinX' in event;

const isBelowPayline = (bookEvents: BookEvent[] = []) => {
	const result = resultFromBook(bookEvents);
	if (!result) return false;
	return result.distanceTotal < paylineDistance(result.hillId);
};

const baseCountPayload = (
	bookEvents: BookEvent[] = [],
	timings: ReturnType<typeof activeTimings>,
	catchUp: boolean,
) => {
	const result = resultFromBook(bookEvents);
	if (!result) return null;
	const hillId = result.hillId as HillId;
	const hillMetres = HILL_TABLE[hillId]?.baseDistance ?? 0;
	const flightMetres = result.slots.reduce((sum, slot) => sum + (slot.distanceValue ?? 0), 0);
	return {
		type: 'skyjumpBaseCount' as const,
		hillId,
		hillMetres,
		weatherMetres: stateGame.lastWeather?.distanceDelta ?? 0,
		flightMetres,
		distanceTotal: result.distanceTotal,
		baseWinX: result.baseWinX,
		timings,
		catchUp,
	};
};

const playRareOrLocal = (slot: { rarity?: string; localMultiplier?: number }) => {
	if ((slot.localMultiplier ?? 1) > 1) {
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: SKYJUMP_SFX.localMultiplier,
			forcePlay: true,
		});
		return;
	}
	if (slot.rarity === 'rare' || slot.rarity === 'epic') {
		eventEmitter.broadcast({ type: 'soundOnce', name: SKYJUMP_SFX.rareSymbol, forcePlay: true });
	}
};

export const bookEventHandlerMap: BookEventHandlerMap<BookEvent, BookEventContext> = {
	skyjumpWeather: async (bookEvent: BookEventOfType<'skyjumpWeather'>) => {
		const timings = activeTimings();
		const catchUp = stateGame.resumeCatchUp;
		eventEmitter.broadcast({ type: 'skyjumpResetBoard' });
		stateGame.weatherDrawing = true;
		stateGame.lastWeather = bookEvent.weather;
		stateGame.presentationPhase = 'weather';
		eventEmitter.broadcast({ type: 'skyjumpPresentation', phase: 'weather' });
		if (!catchUp) startJumpActionBed();
		await eventEmitter.broadcastAsync({
			type: 'skyjumpWeatherShow',
			weather: bookEvent.weather,
			winnerId: bookEvent.winnerId,
			candidates: WEATHER_TABLE.map((row) => ({
				id: row.id,
				label: row.label,
				iconKey: row.iconKey,
				distanceDelta: row.distanceDelta,
			})),
			timings,
			catchUp,
		});
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: SKYJUMP_SFX.weatherLock,
			forcePlay: !stateBet.isTurbo && !catchUp,
		});
	},
	skyjumpSlot: async (
		bookEvent: BookEventOfType<'skyjumpSlot'>,
		{ bookEvents } = { bookEvents: [] },
	) => {
		const timings = activeTimings();
		const catchUp = stateGame.resumeCatchUp;
		if (bookEvent.slotIndex === 1) {
			eventEmitter.broadcast({ type: 'skyjumpSlotsPrepare' });
			stateGame.presentationPhase = 'reels';
			eventEmitter.broadcast({ type: 'skyjumpPresentation', phase: 'reels' });
			if (!catchUp) {
				startJumpActionBed();
				const flightMetres = bookEvents
					.filter(
						(event): event is BookEventOfType<'skyjumpSlot'> =>
							event.type === 'skyjumpSlot' &&
							(event.slotIndex ?? 0) >= 1 &&
							(event.slotIndex ?? 0) <= 5,
					)
					.sort((a, b) => (a.slotIndex ?? 0) - (b.slotIndex ?? 0))
					.map((event) => event.distanceValue ?? 0);
				await eventEmitter.broadcastAsync({
					type: 'skyjumpReelsSpinAll',
					timings,
					flightMetres,
					catchUp,
				});
				await waitForTimeout(timings.reelSpinMs);
			}
		}
		if (bookEvent.slotIndex === 5 && !catchUp) {
			startResultAnticipation();
		}
		if (bookEvent.slotIndex === 6 && bookEvent.finalMultiplier) {
			const below = isBelowPayline(bookEvents);
			if (below) {
				eventEmitter.broadcast({ type: 'skyjumpBaseLocked' });
				eventEmitter.broadcast({ type: 'skyjumpFinalLocked' });
				return;
			}
			stateGame.presentationPhase = 'slot6';
			eventEmitter.broadcast({ type: 'skyjumpPresentation', phase: 'slot6' });
			const basePayload = baseCountPayload(bookEvents, timings, catchUp);
			if (basePayload) {
				await eventEmitter.broadcastAsync(basePayload);
			}
			if (!catchUp) {
				await eventEmitter.broadcastAsync({
					type: 'skyjumpFinalUnlock',
					timings,
					catchUp,
				});
			}
			await eventEmitter.broadcastAsync({
				type: 'skyjumpFinalMultiplierReveal',
				finalMultiplier: bookEvent.finalMultiplier,
				timings,
				catchUp,
			});
			eventEmitter.broadcast({
				type: 'soundOnce',
				name: SKYJUMP_SFX.slot6Land,
				forcePlay: true,
			});
			if (!catchUp) {
				const result = resultFromBook(bookEvents);
				if (result) playResultSting(result);
				await waitForPaint();
				await waitForTimeout(timings.reelGapMs + (timings.id === 'turbo' ? 40 : 180));
			}
			return;
		}
		await eventEmitter.broadcastAsync({
			type: 'skyjumpSlotReveal',
			slot: {
				reelIndex: bookEvent.reelIndex,
				label: bookEvent.label ?? '',
				distanceValue: bookEvent.distanceValue ?? 0,
				localMultiplier: bookEvent.localMultiplier ?? 1,
				rarity: bookEvent.rarity,
			},
			timings,
			catchUp,
		});
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: reelStopSfx(bookEvent.reelIndex),
			forcePlay: !catchUp,
		});
		playRareOrLocal(bookEvent);
		if (!catchUp) await waitForTimeout(timings.reelGapMs);
	},
	skyjumpSpinStart: async (bookEvent: BookEventOfType<'skyjumpSpinStart'>) => {
		applyBonusHudEvent(bookEvent);
		lockV2Presentation('skyjumpSpinStart');
		eventEmitter.broadcast({ type: 'skyjumpV2Reset' });
	},
	skyjumpBoardReveal: async (bookEvent: BookEventOfType<'skyjumpBoardReveal'>) => {
		lockV2Presentation('skyjumpBoardReveal');
		const timings = v2Timings();
		stateGame.presentationPhase = 'reels';
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2BoardReveal',
			board: bookEvent.board,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
		if (!stateGame.resumeCatchUp) playV2AudioHook('boardRevealStop', { forcePlay: false });
	},
	skyjumpLineWins: async (bookEvent: BookEventOfType<'skyjumpLineWins'>) => {
		const timings = v2Timings();
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2LineWins',
			wins: bookEvent.wins,
			lineWinX: bookEvent.lineWinX,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpScatterResult: async (bookEvent: BookEventOfType<'skyjumpScatterResult'>) => {
		const timings = v2Timings();
		if (bookEvent.count >= 3 || bookEvent.perfectV) {
			if (bonusHud.active) playV2AudioHook('FS_RETRIGGER', audioOpts());
			else playV2AudioHook('SCATTER_TRIGGER', audioOpts());
		}
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2ScatterResult',
			count: bookEvent.count,
			perfectV: bookEvent.perfectV,
			positions: bookEvent.positions,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
		if (!stateGame.resumeCatchUp && timings.scatterHoldMs > 0) {
			// Only pause for a real bonus/retrigger moment — not every spin with 0–2 Bibs.
			if (bookEvent.count >= 3 || bookEvent.perfectV) {
				await waitForTimeout(timings.scatterHoldMs);
			}
		}
	},
	skyjumpCoachSignal: async (bookEvent: BookEventOfType<'skyjumpCoachSignal'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('COACH', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2CoachSignal',
			coachPosition: bookEvent.coachPosition,
			selectedSymbolId: bookEvent.selectedSymbolId,
			selectedPositions: bookEvent.selectedPositions,
			noOp: bookEvent.noOp,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpMysteryTransform: async (bookEvent: BookEventOfType<'skyjumpMysteryTransform'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('MYSTERY_TRANSFORM', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2MysteryTransform',
			sourceSymbolId: bookEvent.sourceSymbolId,
			positions: bookEvent.positions,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpMysteryResolve: async (bookEvent: BookEventOfType<'skyjumpMysteryResolve'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		if (bookEvent.resultType === 'FLIGHT_TOKEN') {
			playV2AudioHook('TOKEN_REVEAL', audioOpts());
		} else {
			playV2AudioHook('MYSTERY_REVEAL', audioOpts());
		}
		const payload = {
			type: 'skyjumpV2MysteryResolve' as const,
			position: bookEvent.position,
			resultType: bookEvent.resultType,
			timings,
			catchUp: stateGame.resumeCatchUp,
		};
		if (bookEvent.resultType === 'FLIGHT_TOKEN') {
			await eventEmitter.broadcastAsync({
				...payload,
				tokenId: bookEvent.tokenId,
				tokenTier: bookEvent.tokenTier,
				tokenValueX: bookEvent.faceValueX ?? bookEvent.tokenValueX,
			});
			return;
		}
		if (bookEvent.resultType === 'THERMAL_LIFT') {
			await eventEmitter.broadcastAsync({
				...payload,
				thermalMult: bookEvent.thermalMult,
			});
			return;
		}
		await eventEmitter.broadcastAsync(payload);
	},
	skyjumpGateUpgrade: async (bookEvent: BookEventOfType<'skyjumpGateUpgrade'>) => {
		applyBonusHudEvent(bookEvent);
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('GATE_UPGRADE', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2GateUpgrade',
			position: bookEvent.position,
			floorBefore: bookEvent.floorBefore,
			floorAfter: bookEvent.floorAfter,
			replacements: bookEvent.replacements,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpThermalLift: async (bookEvent: BookEventOfType<'skyjumpThermalLift'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('THERMAL', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2ThermalLift',
			position: bookEvent.position,
			thermalMult: bookEvent.thermalMult,
			affectedTokens: bookEvent.affectedTokens,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpJudgeCollect: async (bookEvent: BookEventOfType<'skyjumpJudgeCollect'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('JUDGE_COLLECT', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2JudgeCollect',
			position: bookEvent.position,
			passIndex: bookEvent.passIndex,
			collectedX: bookEvent.collectedX,
			effectiveTokenSumX: bookEvent.effectiveTokenSumX,
			tokenContributions: bookEvent.tokenContributions,
			batchIndex: bookEvent.batchIndex,
			flightMultiplierX: bookEvent.flightMultiplierX,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpHeadJudgeCollect: async (bookEvent: BookEventOfType<'skyjumpHeadJudgeCollect'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('HEAD_JUDGE_COLLECT', {
			...audioOpts(),
			gainScale: bookEvent.passIndex === 2 ? 0.7 : 1,
		});
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2HeadJudgeCollect',
			position: bookEvent.position,
			passIndex: bookEvent.passIndex,
			collectedX: bookEvent.collectedX,
			effectiveTokenSumX: bookEvent.effectiveTokenSumX,
			tokenContributions: bookEvent.tokenContributions,
			batchIndex: bookEvent.batchIndex,
			flightMultiplierX: bookEvent.flightMultiplierX,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpWindKey: async (bookEvent: BookEventOfType<'skyjumpWindKey'>) => {
		applyBonusHudEvent(bookEvent);
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		if (bookEvent.action === 'UPGRADE') {
			playV2AudioHook('WIND_UPGRADE', audioOpts());
			playV2AudioHook('WIND_TRANSITION', audioOpts());
		} else if (bookEvent.action === 'CHARGE') {
			playV2AudioHook('WIND_CHARGE', audioOpts());
		}
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2WindKey',
			position: bookEvent.position,
			selectedStage: bookEvent.selectedStage,
			action: bookEvent.action,
			oldStageValue: bookEvent.oldStageValue,
			newStageValue: bookEvent.newStageValue,
			oldCharge: bookEvent.oldCharge,
			newCharge: bookEvent.newCharge,
			oldGlobalMultiplier: bookEvent.oldGlobalMultiplier,
			newGlobalMultiplier: bookEvent.newGlobalMultiplier,
			windKeysCollected: bookEvent.windKeysCollected,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpRejumpStart: async (bookEvent: BookEventOfType<'skyjumpRejumpStart'>) => {
		applyBonusHudEvent(bookEvent);
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		playV2AudioHook('REJUMP', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2RejumpStart',
			chainIndex: bookEvent.chainIndex,
			preservedPositions: bookEvent.preservedPositions,
			redroppedPositions: bookEvent.redroppedPositions,
			rejumpsThisSpin: bookEvent.rejumpsThisSpin,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpRejumpBoard: async (bookEvent: BookEventOfType<'skyjumpRejumpBoard'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2RejumpBoard',
			chainIndex: bookEvent.chainIndex,
			board: bookEvent.board,
			changedCells: bookEvent.changedCells,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpRejumpLineWins: async (bookEvent: BookEventOfType<'skyjumpRejumpLineWins'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2RejumpLineWins',
			chainIndex: bookEvent.chainIndex,
			lineWins: bookEvent.lineWins,
			lineWinX: bookEvent.lineWinX,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpRejumpEnd: async (bookEvent: BookEventOfType<'skyjumpRejumpEnd'>) => {
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2RejumpEnd',
			chainIndex: bookEvent.chainIndex,
			applied: bookEvent.applied,
			truncated: bookEvent.truncated,
			reason: bookEvent.reason,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpCapReached: async (bookEvent: BookEventOfType<'skyjumpCapReached'>) => {
		const timings = v2Timings();
		playV2AudioHook('MAX_WIN', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2CapReached',
			rawTotalWinX: bookEvent.rawTotalWinX,
			cappedTotalWinX: bookEvent.cappedTotalWinX,
			capDragX: bookEvent.capDragX,
			maxWinX: bookEvent.maxWinX,
			terminated: bookEvent.terminated === true,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpWorldRecord: async (bookEvent: BookEventOfType<'skyjumpWorldRecord'>) => {
		applyBonusHudEvent(bookEvent);
		const timings = v2Timings();
		playV2AudioHook('WORLD_RECORD', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2WorldRecord',
			position: bookEvent.position,
			bonusTier: bookEvent.bonusTier,
			freeSpinIndex: bookEvent.freeSpinIndex,
			accruedRoundWinXBefore: bookEvent.accruedRoundWinXBefore,
			worldRecordIncrementX: bookEvent.worldRecordIncrementX,
			maxWinX: bookEvent.maxWinX,
			finalRoundWinX: bookEvent.finalRoundWinX,
			remainingFreeSpinsCancelled: bookEvent.remainingFreeSpinsCancelled,
			symbolId: bookEvent.symbolId ?? 'SPECIAL_WORLD_RECORD',
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
		if (!stateGame.resumeCatchUp && timings.wrHoldMs > 0) {
			await waitForTimeout(timings.wrHoldMs);
		}
	},
	skyjumpResult: async (bookEvent: BookEventOfType<'skyjumpResult'>) => {
		if (isV2Result(bookEvent)) {
			const timings = v2Timings();
			playV2AudioHook('settlement', audioOpts());
			await eventEmitter.broadcastAsync({
				type: 'skyjumpV2Result',
				totalLineWinX: bookEvent.totalLineWinX,
				totalFeatureWinX: bookEvent.totalFeatureWinX,
				totalWinX: bookEvent.totalWinX,
				amount: bookEvent.amount,
				capHit: bookEvent.capHit,
				timings,
				catchUp: stateGame.resumeCatchUp,
			});
			if (!stateGame.resumeCatchUp && timings.settlementHoldMs > 0) {
				await waitForTimeout(timings.settlementHoldMs);
			}
			stateGame.presentationPhase = 'idle';
			return;
		}
		if (!('distanceTotal' in bookEvent)) return;
		const timings = activeTimings();
		const catchUp = stateGame.resumeCatchUp;
		if (catchUp) {
			recordBookEvent({ bookEvent });
			return;
		}
		stopJumpActionBed();
		const below = bookEvent.distanceTotal < paylineDistance(bookEvent.hillId);
		if (!below) {
			stateGame.presentationPhase = 'takeoff';
			eventEmitter.broadcast({ type: 'skyjumpPresentation', phase: 'takeoff' });
			await eventEmitter.broadcastAsync({
				type: 'skyjumpTakeoffShow',
				timings,
				catchUp,
			});
		}
		stateGame.presentationPhase = 'result';
		eventEmitter.broadcast({ type: 'skyjumpPresentation', phase: 'result' });
		stateBet.overlayOpen = true;
		try {
			await eventEmitter.broadcastAsync({
				type: 'skyjumpOverlayShow',
				result: bookEvent,
				weather: stateGame.lastWeather,
				timings,
				catchUp,
			});
		} finally {
			stateBet.overlayOpen = false;
		}
		stateGame.presentationPhase = 'idle';
		eventEmitter.broadcast({ type: 'skyjumpPresentation', phase: 'idle' });
	},
	setTotalWin: async (bookEvent: BookEventOfType<'setTotalWin'>) => {
		stateBet.winBookEventAmount = stateBet.winSessionBaseAmount + bookEvent.amount;
	},
	setWin: async () => {
		// SkyJump presents cash in the result overlay, not the fullscreen win screen.
	},
	wincap: async (bookEvent: BookEventOfType<'wincap'>) => {
		if (!stateGame.resumeCatchUp) {
			await waitForTimeout(activeTimings().finalMultHoldMs);
		}
		void bookEvent;
	},
	finalWin: async () => {
		stateGame.resumeCatchUp = false;
		unlockV2Presentation();
	},
	skyjumpFreeSpinsStart: async (bookEvent: BookEventOfType<'skyjumpFreeSpinsStart'>) => {
		applyBonusHudEvent(bookEvent);
		const timings = v2Timings();
		playV2AudioHook('FS_START', audioOpts());
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2BonusTitles',
			kind: 'fsStart',
			tier: String(bookEvent.initialTier ?? null),
			timings: {
				fsBannerMs: timings.fsBannerMs,
				retriggerBannerMs: timings.retriggerBannerMs,
				tierUpgradeMs: timings.tierUpgradeMs,
				modeTitleMs: timings.modeTitleMs,
			},
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpFreeSpinStart: async (bookEvent: BookEventOfType<'skyjumpFreeSpinStart'>) => {
		applyBonusHudEvent(bookEvent);
	},
	skyjumpPersistentTargetsApply: async (
		bookEvent: BookEventOfType<'skyjumpPersistentTargetsApply'>,
	) => {
		applyBonusHudEvent(bookEvent);
		const timings = getV2TimingsForState(stateBet.isTurbo, stateGame.resumeCatchUp);
		await eventEmitter.broadcastAsync({
			type: 'skyjumpV2PersistentApply',
			positions: bookEvent.positions,
			timings,
			catchUp: stateGame.resumeCatchUp,
		});
	},
	skyjumpPersistentTargetsUpdate: async (
		bookEvent: BookEventOfType<'skyjumpPersistentTargetsUpdate'>,
	) => {
		applyBonusHudEvent(bookEvent);
	},
	skyjumpGuaranteedGate: async (bookEvent: BookEventOfType<'skyjumpGuaranteedGate'>) => {
		applyBonusHudEvent(bookEvent);
	},
	skyjumpBonusUpgrade: async (bookEvent: BookEventOfType<'skyjumpBonusUpgrade'>) => {
		applyBonusHudEvent(bookEvent);
		const timings = v2Timings();
		if (bookEvent.tierChanged) {
			playV2AudioHook('TIER_UPGRADE', audioOpts());
		}
		const spinsRequested = Number(bookEvent.spinsRequested ?? 0);
		if (bookEvent.tierChanged || spinsRequested > 0) {
			await eventEmitter.broadcastAsync({
				type: 'skyjumpV2BonusTitles',
				kind: bookEvent.tierChanged ? 'tierUpgrade' : 'retrigger',
				tier: String(bookEvent.toTier ?? null),
				timings: {
					fsBannerMs: timings.fsBannerMs,
					retriggerBannerMs: timings.retriggerBannerMs,
					tierUpgradeMs: timings.tierUpgradeMs,
					modeTitleMs: timings.modeTitleMs,
				},
				catchUp: stateGame.resumeCatchUp,
			});
		}
	},
	skyjumpFreeSpinEnd: async (bookEvent: BookEventOfType<'skyjumpFreeSpinEnd'>) => {
		applyBonusHudEvent(bookEvent);
	},
	skyjumpFreeSpinState: async (bookEvent: BookEventOfType<'skyjumpFreeSpinState'>) => {
		applyBonusHudEvent(bookEvent);
	},
	skyjumpFreeSpinsEnd: async (bookEvent: BookEventOfType<'skyjumpFreeSpinsEnd'>) => {
		applyBonusHudEvent(bookEvent);
		playV2AudioHook('BONUS_END', audioOpts());
	},
	createBonusSnapshot: async (bookEvent: BookEventOfType<'createBonusSnapshot'>) => {
		const { bookEvents } = bookEvent;
		stateGame.resumeCatchUp = true;

		function findLastBookEvent<T>(type: T) {
			return _.findLast(bookEvents, (event) => event.type === type) as
				| BookEventOfType<T>
				| undefined;
		}

		const lastBoard = findLastBookEvent('skyjumpBoardReveal' as const);
		if (lastBoard) {
			const lastLines = findLastBookEvent('skyjumpLineWins' as const);
			const lastScatter = findLastBookEvent('skyjumpScatterResult' as const);
			const lastResult = findLastBookEvent('skyjumpResult' as const);
			const lastSetTotalWinEvent = findLastBookEvent('setTotalWin' as const);
			await playBookEvent(lastBoard, { bookEvents });
			if (lastLines) await playBookEvent(lastLines, { bookEvents });
			if (lastScatter) await playBookEvent(lastScatter, { bookEvents });
			const lastBoardIndex = bookEvents.reduce(
				(found, event, index) => (event.type === 'skyjumpBoardReveal' ? index : found),
				-1,
			);
			const featureEvents = bookEvents.filter(
				(event, index) =>
					index > lastBoardIndex &&
					[
						'skyjumpCoachSignal',
						'skyjumpMysteryTransform',
						'skyjumpMysteryResolve',
						'skyjumpGateUpgrade',
						'skyjumpThermalLift',
						'skyjumpJudgeCollect',
						'skyjumpHeadJudgeCollect',
						'skyjumpWindKey',
						'skyjumpRejumpStart',
						'skyjumpRejumpBoard',
						'skyjumpRejumpLineWins',
						'skyjumpRejumpEnd',
						'skyjumpWorldRecord',
						'skyjumpCapReached',
						'skyjumpPersistentTargetsApply',
						'skyjumpGuaranteedGate',
					].includes(event.type),
			);
			for (const featureEvent of featureEvents) {
				await playBookEvent(featureEvent, { bookEvents });
			}
			if (lastResult) await playBookEvent(lastResult, { bookEvents });
			if (lastSetTotalWinEvent) playBookEvent(lastSetTotalWinEvent, { bookEvents });
			for (const bonusEvent of bookEvents) {
				if (
					bonusEvent.type === 'skyjumpFreeSpinsStart' ||
					bonusEvent.type === 'skyjumpFreeSpinState' ||
					bonusEvent.type === 'skyjumpBonusUpgrade' ||
					bonusEvent.type === 'skyjumpPersistentTargetsUpdate'
				) {
					await playBookEvent(bonusEvent, { bookEvents });
				}
			}
			stateGame.resumeCatchUp = false;
			return;
		}

		const lastWeather = findLastBookEvent('skyjumpWeather' as const);
		const slotEvents = bookEvents.filter(
			(event): event is BookEventOfType<'skyjumpSlot'> => event.type === 'skyjumpSlot',
		);
		const lastResult = findLastBookEvent('skyjumpResult' as const);
		const lastWincap = findLastBookEvent('wincap' as const);
		const lastSetTotalWinEvent = findLastBookEvent('setTotalWin' as const);

		if (lastWeather) await playBookEvent(lastWeather, { bookEvents });
		for (const slotEvent of slotEvents) {
			await playBookEvent(slotEvent, { bookEvents });
		}
		if (lastResult) await playBookEvent(lastResult, { bookEvents });
		if (lastWincap) await playBookEvent(lastWincap, { bookEvents });
		if (lastSetTotalWinEvent) playBookEvent(lastSetTotalWinEvent, { bookEvents });
		stateGame.resumeCatchUp = false;
	},
};
