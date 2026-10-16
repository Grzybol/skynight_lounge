import type { BookEventOfType, SkyJumpMysteryResultType } from '../../game/typesBookEvent';
import type { HillId, TimingProfile, WeatherId } from '../../game/skyjump/types';

export type SkyJumpWeatherCandidate = {
	id: WeatherId;
	label: string;
	iconKey: string;
	distanceDelta: number;
};

export type EmitterEventSkyJump =
	| {
			type: 'skyjumpWeatherShow';
			weather: BookEventOfType<'skyjumpWeather'>['weather'];
			winnerId: WeatherId;
			candidates: SkyJumpWeatherCandidate[];
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpSlotsPrepare';
	  }
	| {
			type: 'skyjumpReelsSpinAll';
			timings: TimingProfile;
			flightMetres?: number[];
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpSlotReveal';
			slot: {
				reelIndex: number;
				label: string;
				distanceValue: number;
				localMultiplier: number;
				rarity?: string;
			};
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpFinalMultiplierReveal';
			finalMultiplier: {
				id: string;
				label: string;
				multiplier: number;
			};
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpFinalUnlock';
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| { type: 'skyjumpFinalLocked' }
	| {
			type: 'skyjumpBaseCount';
			hillId: HillId;
			hillMetres: number;
			weatherMetres: number;
			flightMetres: number;
			distanceTotal: number;
			baseWinX: number;
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| { type: 'skyjumpBaseLocked' }
	| {
			type: 'skyjumpTakeoffShow';
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpOverlayShow';
			result: Extract<BookEventOfType<'skyjumpResult'>, { distanceTotal: number }>;
			weather?: BookEventOfType<'skyjumpWeather'>['weather'] | null;
			timings: TimingProfile;
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpPresentation';
			phase: 'idle' | 'weather' | 'reels' | 'slot6' | 'takeoff' | 'result';
	  }
	| { type: 'skyjumpResetBoard' }
	| { type: 'skyjumpV2Reset' }
	| {
			type: 'skyjumpV2Prepare';
			timings: { reelSpinMs: number; reelStopMs: number; reelGapMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2BoardReveal';
			board: string[][];
			/** Tier of the round's final win (known from the book before the reels roll): big wins roll with wider gaps and a slow zoom. */
			bigWinTier?: 'none' | 'big' | 'mega' | 'super' | 'max' | 'worldRecord';
			timings: {
				reelSpinMs: number;
				reelStopMs: number;
				reelGapMs: number;
				reelStartStaggerMs: number;
				reelStopStaggerMs: number;
				reelTravelMs: number;
				reelTravelSlots: number;
				reelSettleMs: number;
			};
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2LineWins';
			wins: BookEventOfType<'skyjumpLineWins'>['wins'];
			lineWinX: number;
			timings: { winHoldMs: number; lineCycleMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2Result';
			totalLineWinX: number;
			totalFeatureWinX: number;
			totalWinX: number;
			amount: number;
			capHit?: boolean;
			timings?: { settlementHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2ScatterResult';
			count: number;
			perfectV: boolean;
			positions: Array<{ reel: number; row: number }>;
			timings?: { scatterHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2CoachSignal';
			coachPosition: { reel: number; row: number };
			selectedSymbolId: string | null;
			selectedPositions: Array<{ reel: number; row: number }>;
			noOp: boolean;
			timings: { coachHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2MysteryTransform';
			sourceSymbolId: string;
			positions: Array<{ reel: number; row: number }>;
			timings: { mysteryHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2MysteryResolve';
			position: { reel: number; row: number };
			resultType: SkyJumpMysteryResultType;
			tokenId?: string;
			tokenTier?: number;
			tokenValueX?: number;
			thermalMult?: number;
			timings: { mysteryHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2GateUpgrade';
			position: { reel: number; row: number };
			floorBefore: number;
			floorAfter: number;
			replacements: BookEventOfType<'skyjumpGateUpgrade'>['replacements'];
			timings: { gateHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2ThermalLift';
			position: { reel: number; row: number };
			thermalMult: number;
			affectedTokens: BookEventOfType<'skyjumpThermalLift'>['affectedTokens'];
			timings: { thermalHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2JudgeCollect';
			position: { reel: number; row: number };
			passIndex: number;
			collectedX: number;
			effectiveTokenSumX: number;
			tokenContributions: BookEventOfType<'skyjumpJudgeCollect'>['tokenContributions'];
			batchIndex?: number;
			flightMultiplierX?: number;
			timings: { collectHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2HeadJudgeCollect';
			position: { reel: number; row: number };
			passIndex: number;
			collectedX: number;
			effectiveTokenSumX: number;
			tokenContributions: BookEventOfType<'skyjumpHeadJudgeCollect'>['tokenContributions'];
			batchIndex?: number;
			flightMultiplierX?: number;
			timings: { collectHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2WindKey';
			position: { reel: number; row: number };
			selectedStage: BookEventOfType<'skyjumpWindKey'>['selectedStage'];
			action: BookEventOfType<'skyjumpWindKey'>['action'];
			oldStageValue: number | null;
			newStageValue: number | null;
			oldCharge: number | null;
			newCharge: number | null;
			oldGlobalMultiplier: number;
			newGlobalMultiplier: number;
			windKeysCollected: number;
			timings: { windHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2RejumpStart';
			chainIndex: number;
			preservedPositions: Array<{ reel: number; row: number }>;
			redroppedPositions: Array<{ reel: number; row: number }>;
			rejumpsThisSpin: number;
			timings: { rejumpHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2RejumpBoard';
			chainIndex: number;
			board?: string[][];
			changedCells?: Array<{ reel: number; row: number; symbolId: string }>;
			timings: { rejumpHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2RejumpLineWins';
			chainIndex: number;
			lineWins: BookEventOfType<'skyjumpRejumpLineWins'>['lineWins'];
			lineWinX: number;
			timings: { winHoldMs: number; lineCycleMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2RejumpEnd';
			chainIndex: number;
			applied: boolean;
			truncated: boolean;
			reason: string | null;
			timings: { rejumpHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2CapReached';
			rawTotalWinX: number;
			cappedTotalWinX: number;
			capDragX: number;
			maxWinX: number;
			terminated?: boolean;
			timings: { capHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2WorldRecord';
			position: { reel: number; row: number };
			bonusTier: string;
			freeSpinIndex: number;
			accruedRoundWinXBefore: number;
			worldRecordIncrementX: number;
			maxWinX: number;
			finalRoundWinX: number;
			remainingFreeSpinsCancelled: number;
			symbolId: string;
			timings: { capHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			type: 'skyjumpV2PersistentApply';
			positions: Array<{ reel: number; row: number; symbolId?: string }>;
			timings: { mysteryHoldMs: number };
			catchUp?: boolean;
	  }
	| {
			/** Sequenced bonus title banners (FS start / retrigger / tier upgrade). One at a time. */
			type: 'skyjumpV2BonusTitles';
			kind: 'fsStart' | 'retrigger' | 'tierUpgrade';
			tier: string | null;
			timings: {
				fsBannerMs: number;
				retriggerBannerMs: number;
				tierUpgradeMs: number;
				modeTitleMs: number;
			};
			catchUp?: boolean;
	  };
