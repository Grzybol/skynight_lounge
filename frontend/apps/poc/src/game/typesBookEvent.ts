import type { BetType } from 'rgs-requests';

import type { Rarity, SlotRoleId, WeatherId } from './skyjump/types';
import type { V2Board, V2LineWin } from './skyjump_v2/types';

type BookEventSetTotalWin = {
	index: number;
	type: 'setTotalWin';
	amount: number;
};

type BookEventFinalWin = {
	index: number;
	type: 'finalWin';
	amount: number;
};

type BookEventSetWin = {
	index: number;
	type: 'setWin';
	amount: number;
	winLevel: number;
};

type BookEventWinCap = {
	index: number;
	type: 'wincap';
	amount: number;
};

type BookEventCreateBonusSnapshot = {
	index: number;
	type: 'createBonusSnapshot';
	bookEvents: BookEvent[];
};

type SkyJumpSchema = {
	schemaVersion: number;
};

type BookEventSkyJumpWeather = SkyJumpSchema & {
	index: number;
	type: 'skyjumpWeather';
	weatherId: WeatherId;
	weather: {
		id: WeatherId;
		label: string;
		iconKey: string;
		temperatureC: number;
		windSpeedMs: number;
		windDirection: string;
		visibilityPct: number;
		distanceDelta: number;
	};
	winnerId: WeatherId;
};

type BookEventSkyJumpSlot = SkyJumpSchema & {
	index: number;
	type: 'skyjumpSlot';
	slotIndex: number;
	role: SlotRoleId | 'finalMultiplier';
	symbolId?: string;
	id?: string;
	label?: string;
	distanceValue?: number;
	localMultiplier?: number;
	rarity?: Rarity;
	artKey?: string;
	reelIndex: number;
	roleId?: SlotRoleId;
	finalMultiplier?: {
		id: string;
		label: string;
		multiplier: number;
	};
};

export type BookEventSkyJumpResult = SkyJumpSchema & {
	index: number;
	type: 'skyjumpResult';
	hillId: string;
	hillProfile: string;
	multiplierTableId: string;
	multiplierProfile: string;
	distanceTotal: number;
	baseWinX: number;
	localMultiplier: number;
	localFactors: number[];
	finalMultiplier: number;
	finalWinX: number;
	/** Debug/presentation only. Wallet settlement uses `amount`. */
	moneyWin: number;
	capped: boolean;
	isCapped: boolean;
	maxWin: number;
	costMultiplier?: number;
	returnMultiplier?: number;
	netMultiplier?: number;
	isPayHit?: boolean;
	isBreakEven?: boolean;
	isProfit?: boolean;
	amount: number;
	roles?: {
		id: SlotRoleId;
		index: number;
		label: string;
		iconKey: string;
	}[];
	slots: {
		roleId: SlotRoleId;
		label: string;
		distanceValue: number;
		localMultiplier: number;
	}[];
};

type BookEventSkyJumpV2SpinStart = {
	index: number;
	type: 'skyjumpSpinStart';
	schemaVersion: 2;
	mode: string;
	isFreeSpin: boolean;
	fixtureId?: string;
	source?: string;
	stops?: number[];
};

type BookEventSkyJumpBoardReveal = {
	index: number;
	type: 'skyjumpBoardReveal';
	schemaVersion: 2;
	board: V2Board;
};

type BookEventSkyJumpLineWins = {
	index: number;
	type: 'skyjumpLineWins';
	schemaVersion: 2;
	wins: V2LineWin[];
	lineWinX: number;
};

type BookEventSkyJumpScatterResult = {
	index: number;
	type: 'skyjumpScatterResult';
	schemaVersion: 2;
	positions: Array<{ reel: number; row: number }>;
	count: number;
	perfectV: boolean;
	trigger: null;
	fromBoard: string;
};

type BookEventSkyJumpCoachSignal = {
	index: number;
	type: 'skyjumpCoachSignal';
	schemaVersion: 2;
	coachPosition: { reel: number; row: number };
	selectedSymbolId: string | null;
	selectedPositions: Array<{ reel: number; row: number }>;
	sequenceIndex: number;
	noOp: boolean;
	reason?: string;
};

type BookEventSkyJumpMysteryTransform = {
	index: number;
	type: 'skyjumpMysteryTransform';
	schemaVersion: 2;
	sourceSymbolId: string;
	positions: Array<{ reel: number; row: number }>;
	sequenceIndex: number;
};

export type SkyJumpMysteryResultType =
	| 'FLIGHT_TOKEN'
	| 'THERMAL_LIFT'
	| 'GATE_UPGRADE'
	| 'JUDGE'
	| 'HEAD_JUDGE'
	| 'REJUMP'
	| 'WIND_KEY';

export type SkyJumpWindStage = 'RUN_UP' | 'TAKEOFF' | 'FLIGHT';
export type SkyJumpWindKeyAction = 'CHARGE' | 'UPGRADE' | 'NO_OP';

type BookEventSkyJumpMysteryResolveBase = {
	index: number;
	type: 'skyjumpMysteryResolve';
	schemaVersion: 2;
	position: { reel: number; row: number };
};

type BookEventSkyJumpMysteryResolveFlightToken = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'FLIGHT_TOKEN';
	tokenTier: number;
	tokenId: string;
	tokenName: string;
	tokenValueX: number;
	faceValueX?: number;
	effectiveValueX?: number;
};

type BookEventSkyJumpMysteryResolveThermalLift = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'THERMAL_LIFT';
	thermalMult: number;
};

type BookEventSkyJumpMysteryResolveGateUpgrade = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'GATE_UPGRADE';
};

type BookEventSkyJumpMysteryResolveJudge = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'JUDGE';
};

type BookEventSkyJumpMysteryResolveHeadJudge = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'HEAD_JUDGE';
};

type BookEventSkyJumpMysteryResolveRejump = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'REJUMP';
};

type BookEventSkyJumpMysteryResolveWindKey = BookEventSkyJumpMysteryResolveBase & {
	resultType: 'WIND_KEY';
};

type BookEventSkyJumpMysteryResolve =
	| BookEventSkyJumpMysteryResolveFlightToken
	| BookEventSkyJumpMysteryResolveThermalLift
	| BookEventSkyJumpMysteryResolveGateUpgrade
	| BookEventSkyJumpMysteryResolveJudge
	| BookEventSkyJumpMysteryResolveHeadJudge
	| BookEventSkyJumpMysteryResolveRejump
	| BookEventSkyJumpMysteryResolveWindKey;

type BookEventSkyJumpGateUpgrade = {
	index: number;
	type: 'skyjumpGateUpgrade';
	schemaVersion: 2;
	position: { reel: number; row: number };
	floorBefore: number;
	floorAfter: number;
	replacements: Array<{
		reel: number;
		row: number;
		before: { tier: number; face: number };
		after: { tier: number; face: number };
	}>;
};

type BookEventSkyJumpThermalLift = {
	index: number;
	type: 'skyjumpThermalLift';
	schemaVersion: 2;
	position: { reel: number; row: number };
	thermalMult: number;
	affectedTokens: Array<{
		reel: number;
		row: number;
		faceValueX: number;
		effectiveValueX: number;
		appliedThermals: number[];
	}>;
};

type BookEventSkyJumpJudgeCollectBase = {
	index: number;
	schemaVersion: 2;
	position: { reel: number; row: number };
	passIndex: number;
	collectedX: number;
	effectiveTokenSumX: number;
	tokenContributions: Array<{
		reel: number;
		row: number;
		tokenTier?: number;
		tokenId?: string;
		faceValueX: number;
		effectiveValueX: number;
		appliedThermals?: number[];
	}>;
	/** Phase 6B collector settlement extras (optional for older books). */
	batchIndex?: number;
	rawTokenCollectionX?: number;
	flightMultiplierX?: number;
	paidCollectionX?: number;
	payoutSpentAfter?: boolean;
};

type BookEventSkyJumpJudgeCollect = BookEventSkyJumpJudgeCollectBase & {
	type: 'skyjumpJudgeCollect';
};

type BookEventSkyJumpHeadJudgeCollect = BookEventSkyJumpJudgeCollectBase & {
	type: 'skyjumpHeadJudgeCollect';
};

type BookEventSkyJumpWindKey = {
	index: number;
	type: 'skyjumpWindKey';
	schemaVersion: 2;
	position: { reel: number; row: number };
	selectedStage: SkyJumpWindStage | null;
	action: SkyJumpWindKeyAction;
	oldStageValue: number | null;
	newStageValue: number | null;
	oldCharge: number | null;
	newCharge: number | null;
	oldGlobalMultiplier: number;
	newGlobalMultiplier: number;
	windKeysCollected: number;
};

type BookEventSkyJumpRejumpStart = {
	index: number;
	type: 'skyjumpRejumpStart';
	schemaVersion: 2;
	chainIndex: number;
	preservedPositions: Array<{ reel: number; row: number }>;
	redroppedPositions: Array<{ reel: number; row: number }>;
	rejumpsThisSpin: number;
};

type BookEventSkyJumpRejumpBoard = {
	index: number;
	type: 'skyjumpRejumpBoard';
	schemaVersion: 2;
	chainIndex: number;
	board?: V2Board;
	changedCells?: Array<{ reel: number; row: number; symbolId: string }>;
};

type BookEventSkyJumpRejumpLineWins = {
	index: number;
	type: 'skyjumpRejumpLineWins';
	schemaVersion: 2;
	chainIndex: number;
	lineWins: V2LineWin[];
	lineWinX: number;
};

type BookEventSkyJumpRejumpEnd = {
	index: number;
	type: 'skyjumpRejumpEnd';
	schemaVersion: 2;
	chainIndex: number;
	applied: boolean;
	truncated: boolean;
	reason: string | null;
};

type BookEventSkyJumpCapReached = {
	index: number;
	type: 'skyjumpCapReached';
	schemaVersion: 2;
	rawTotalWinX: number;
	cappedTotalWinX: number;
	capDragX: number;
	maxWinX: number;
	terminated?: boolean;
	reason?: string;
};

type BookEventSkyJumpWorldRecord = {
	index: number;
	type: 'skyjumpWorldRecord';
	schemaVersion: 2;
	position: { reel: number; row: number };
	bonusTier: string;
	freeSpinIndex: number;
	accruedRoundWinXBefore: number;
	worldRecordIncrementX: number;
	maxWinX: number;
	finalRoundWinX: number;
	terminated: boolean;
	remainingFreeSpinsCancelled: number;
	pendingRejumpsCancelled: boolean;
	tierIntensity?: number;
	symbolId?: string;
	candidateOrigin?: string;
};

type BookEventSkyJumpV2Result = {
	index: number;
	type: 'skyjumpResult';
	schemaVersion: 2;
	totalLineWinX: number;
	totalFeatureWinX: number;
	totalWinX: number;
	amount: number;
	latentTokenValueX?: number;
	totalFeatureWinXRaw?: number;
	totalWinXRaw?: number;
	tokenFloorTier?: number;
	capHit?: boolean;
};

type BookEventFreeSpinsStart = {
	index: number;
	type: 'skyjumpFreeSpinsStart';
	schemaVersion: 2;
	initialTier: string;
	spinsAwarded: number;
	directTriggerType: string;
	triggeringScatterPositions: Array<{ reel: number; row: number }>;
	triggerSpinWinX?: number;
	wagerCostMultiplier?: number;
};

type BookEventFreeSpinStart = {
	index: number;
	type: 'skyjumpFreeSpinStart';
	schemaVersion: 2;
	spinIndex: number;
	currentTier: string;
	spinsRemainingBefore: number;
};

type BookEventFreeSpinState = {
	index: number;
	type: 'skyjumpFreeSpinState';
	schemaVersion: 2;
	bonusActive: boolean;
	bonusTier: string;
	freeSpinsRemaining: number;
	freeSpinsPlayed: number;
	totalFreeSpinsAwarded: number;
	tokenFloorTier: number;
	persistentMysteryTargets: string[];
	guaranteedGateUsed: boolean;
	bonusWinXCapped: number;
	roundWinXCapped: number;
	maxWinReached: boolean;
	pendingTierUpgrade: string | null;
	[key: string]: unknown;
};

type BookEventBonusUpgrade = {
	index: number;
	type: 'skyjumpBonusUpgrade';
	schemaVersion: 2;
	fromTier: string;
	toTier: string;
	triggeringScatterCount: number;
	spinsRequested: number;
	spinsAdded: number;
	activatesFromSpinIndex: number | null;
	tierChanged: boolean;
};

type BookEventFreeSpinEnd = {
	index: number;
	type: 'skyjumpFreeSpinEnd';
	schemaVersion: 2;
	spinIndex: number;
	spinWinX: number;
	bonusWinRunningX: number;
	spinsRemainingAfter: number;
};

type BookEventFreeSpinsEnd = {
	index: number;
	type: 'skyjumpFreeSpinsEnd';
	schemaVersion: 2;
	totalSpinsPlayed: number;
	finalTier: string;
	bonusWinX: number;
	upgradeCount: number;
	retriggerCount: number;
	roundWinXCapped?: number;
	triggerSpinWinX?: number;
};

type BookEventPersistentApply = {
	index: number;
	type: 'skyjumpPersistentTargetsApply';
	schemaVersion: 2;
	targets: string[];
	positions: Array<{ reel: number; row: number; symbolId: string }>;
};

type BookEventPersistentUpdate = {
	index: number;
	type: 'skyjumpPersistentTargetsUpdate';
	schemaVersion: 2;
	added: string[];
	persistentMysteryTargets: string[];
};

type BookEventGuaranteedGate = {
	index: number;
	type: 'skyjumpGuaranteedGate';
	schemaVersion: 2;
	position: { reel: number; row: number };
	replacedResultType: string | null;
	replacedTokenTier: number | null;
};

export type BookEvent =
	| BookEventSetTotalWin
	| BookEventCreateBonusSnapshot
	| BookEventFinalWin
	| BookEventSetWin
	| BookEventWinCap
	| BookEventSkyJumpWeather
	| BookEventSkyJumpSlot
	| BookEventSkyJumpResult
	| BookEventSkyJumpV2SpinStart
	| BookEventSkyJumpBoardReveal
	| BookEventSkyJumpLineWins
	| BookEventSkyJumpScatterResult
	| BookEventSkyJumpCoachSignal
	| BookEventSkyJumpMysteryTransform
	| BookEventSkyJumpMysteryResolve
	| BookEventSkyJumpGateUpgrade
	| BookEventSkyJumpThermalLift
	| BookEventSkyJumpJudgeCollect
	| BookEventSkyJumpHeadJudgeCollect
	| BookEventSkyJumpWindKey
	| BookEventSkyJumpRejumpStart
	| BookEventSkyJumpRejumpBoard
	| BookEventSkyJumpRejumpLineWins
	| BookEventSkyJumpRejumpEnd
	| BookEventSkyJumpCapReached
	| BookEventSkyJumpWorldRecord
	| BookEventSkyJumpV2Result
	| BookEventFreeSpinsStart
	| BookEventFreeSpinStart
	| BookEventFreeSpinState
	| BookEventBonusUpgrade
	| BookEventFreeSpinEnd
	| BookEventFreeSpinsEnd
	| BookEventPersistentApply
	| BookEventPersistentUpdate
	| BookEventGuaranteedGate;

export type Bet = BetType<BookEvent>;
export type BookEventOfType<T> = Extract<BookEvent, { type: T }>;
export type BookEventContext = { bookEvents: BookEvent[] };
