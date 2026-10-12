/** Pure schema-v2 feature reducer. No RNG. Replay events to rebuild state. */

export type V2CellKind =
	| 'regular'
	| 'scatter'
	| 'coach'
	| 'mystery'
	| 'token'
	| 'thermal'
	| 'gate'
	| 'judge'
	| 'head_judge'
	| 'rejump'
	| 'wind'
	| 'unknown';

export type V2FeatureCell = {
	kind: V2CellKind;
	symbolId: string;
	tokenTier: number | null;
	tokenValueX: number | null;
	faceValueX: number | null;
	effectiveValueX: number | null;
	thermalMult: number | null;
	appliedThermals: number[];
};

export type V2FlightStageState = { value: number; charge: number };

export type V2FlightMultiplierState = {
	runUp: V2FlightStageState;
	takeoff: V2FlightStageState;
	flight: V2FlightStageState;
};

export type V2FeatureState = {
	board: V2FeatureCell[][] | null;
	lineWinX: number;
	featureWinX: number;
	featureWinXRaw: number;
	totalWinX: number;
	totalWinXRaw: number;
	scatterCount: number;
	perfectV: boolean;
	featureChainStep: number;
	coachesResolved: number;
	mysteriesOpen: number;
	capReached: boolean;
	tokenFloorTier: number;
	collectorPasses: number;
	persistentMysteryTargets: string[];
	runUpMultiplier: number;
	takeoffMultiplier: number;
	flightMultiplier: number | V2FlightMultiplierState;
	freeSpinsRemaining: number;
	amount: number;
	mode?: string;
	isFreeSpin?: boolean;
	stops?: number[];
	wins?: unknown;
	scatterPositions?: unknown;
	bonusActive?: boolean;
	bonusTier?: string | null;
	freeSpinsInitial?: number;
	freeSpinsPlayed?: number;
	totalFreeSpinsAwarded?: number;
	upgradeCount?: number;
	retriggerCount?: number;
	guaranteedGateUsed?: boolean;
	bonusWinXRaw?: number;
	bonusWinXCapped?: number;
	triggerSpinWinX?: number;
	roundWinXRaw?: number;
	roundWinXCapped?: number;
	maxWinReached?: boolean;
	pendingTierUpgrade?: string | null;
	coachGuaranteeState?: Record<string, unknown> | null;
	flightMultiplierRunUp?: number;
	flightMultiplierTakeoff?: number;
	flightMultiplierFlight?: number;
	windKeysCollected?: number;
	rejumpsThisBonus?: number;
	featureBatchIndex?: number;
	globalFlightMultiplier?: number;
	rejumpState?: unknown;
	lastCoach?: { selectedSymbolId: string | null; noOp: boolean };
	lastGate?: { floorBefore: number; floorAfter: number };
	lastThermal?: { position: { reel: number; row: number }; thermalMult: number };
	lastCollection?: {
		type: string;
		passIndex?: number;
		collectedX: number;
		batchIndex?: number;
		flightMultiplierX?: number;
	};
	lastWindKey?: {
		selectedStage: string | null;
		action: string;
		oldStageValue: number | null;
		newStageValue: number | null;
		oldCharge: number | null;
		newCharge: number | null;
		oldGlobalMultiplier: number;
		newGlobalMultiplier: number;
	};
	lastRejump?: {
		chainIndex: number;
		applied?: boolean;
		truncated?: boolean;
		reason?: string | null;
	};
	capDragX?: number;
	worldRecord?: {
		position: { reel: number; row: number };
		bonusTier: string;
		freeSpinIndex: number;
		accruedRoundWinXBefore: number;
		worldRecordIncrementX: number;
		maxWinX: number;
		finalRoundWinX: number;
		remainingFreeSpinsCancelled: number;
		pendingRejumpsCancelled: boolean;
	};
};

const REGULAR = new Set(['P1', 'P2', 'P3', 'M1', 'M2', 'M3', 'L1', 'L2', 'L3']);
const TOKENS = new Set(['T1', 'T2', 'T3', 'T4', 'T5', 'T6']);

export const defaultFlightMultiplier = (): V2FlightMultiplierState => ({
	runUp: { value: 1, charge: 0 },
	takeoff: { value: 1, charge: 0 },
	flight: { value: 1, charge: 0 },
});

export const globalFromFlightStages = (stages: V2FlightMultiplierState) =>
	stages.runUp.value * stages.takeoff.value * stages.flight.value;

const parseFlightMultiplier = (event: Record<string, unknown>): V2FlightMultiplierState => {
	const raw = event.flightMultiplier;
	if (raw && typeof raw === 'object') {
		const stages = raw as Record<string, { value?: number; charge?: number }>;
		return {
			runUp: {
				value: Number(stages.runUp?.value ?? event.flightMultiplierRunUp ?? 1),
				charge: Number(stages.runUp?.charge ?? 0),
			},
			takeoff: {
				value: Number(stages.takeoff?.value ?? event.flightMultiplierTakeoff ?? 1),
				charge: Number(stages.takeoff?.charge ?? 0),
			},
			flight: {
				value: Number(stages.flight?.value ?? event.flightMultiplierFlight ?? 1),
				charge: Number(stages.flight?.charge ?? 0),
			},
		};
	}
	return {
		runUp: { value: Number(event.flightMultiplierRunUp ?? 1), charge: 0 },
		takeoff: { value: Number(event.flightMultiplierTakeoff ?? 1), charge: 0 },
		flight: { value: Number(event.flightMultiplierFlight ?? 1), charge: 0 },
	};
};

const syncFlightLegacy = (state: V2FeatureState, stages: V2FlightMultiplierState) => {
	state.flightMultiplier = stages;
	state.flightMultiplierRunUp = stages.runUp.value;
	state.flightMultiplierTakeoff = stages.takeoff.value;
	state.flightMultiplierFlight = stages.flight.value;
	state.runUpMultiplier = stages.runUp.value;
	state.takeoffMultiplier = stages.takeoff.value;
	state.globalFlightMultiplier = globalFromFlightStages(stages);
};

export const cellFromSymbol = (symbolId: string): V2FeatureCell => {
	let kind: V2CellKind = 'unknown';
	if (REGULAR.has(symbolId)) kind = 'regular';
	else if (symbolId === 'S') kind = 'scatter';
	else if (symbolId === 'C') kind = 'coach';
	else if (symbolId === 'Y') kind = 'mystery';
	else if (TOKENS.has(symbolId)) kind = 'token';
	else if (symbolId === 'THERMAL' || symbolId === 'THERMAL_LIFT') kind = 'thermal';
	else if (symbolId === 'GATE' || symbolId === 'GATE_UPGRADE') kind = 'gate';
	else if (symbolId === 'JUDGE') kind = 'judge';
	else if (symbolId === 'HEAD_JUDGE') kind = 'head_judge';
	else if (symbolId === 'REJUMP') kind = 'rejump';
	else if (symbolId === 'WIND' || symbolId === 'WIND_KEY') kind = 'wind';
	return {
		kind,
		symbolId,
		tokenTier: null,
		tokenValueX: null,
		faceValueX: null,
		effectiveValueX: null,
		thermalMult: null,
		appliedThermals: [],
	};
};

export const initialV2FeatureState = (): V2FeatureState => ({
	board: null,
	lineWinX: 0,
	featureWinX: 0,
	featureWinXRaw: 0,
	totalWinX: 0,
	totalWinXRaw: 0,
	scatterCount: 0,
	perfectV: false,
	featureChainStep: 0,
	coachesResolved: 0,
	mysteriesOpen: 0,
	capReached: false,
	tokenFloorTier: 1,
	collectorPasses: 0,
	persistentMysteryTargets: [],
	runUpMultiplier: 1,
	takeoffMultiplier: 1,
	flightMultiplier: defaultFlightMultiplier(),
	freeSpinsRemaining: 0,
	amount: 0,
	bonusActive: false,
	bonusTier: null,
	freeSpinsInitial: 0,
	freeSpinsPlayed: 0,
	totalFreeSpinsAwarded: 0,
	upgradeCount: 0,
	retriggerCount: 0,
	guaranteedGateUsed: false,
	bonusWinXRaw: 0,
	bonusWinXCapped: 0,
	triggerSpinWinX: 0,
	roundWinXRaw: 0,
	roundWinXCapped: 0,
	maxWinReached: false,
	pendingTierUpgrade: null,
	coachGuaranteeState: null,
	flightMultiplierRunUp: 1,
	flightMultiplierTakeoff: 1,
	flightMultiplierFlight: 1,
	windKeysCollected: 0,
	rejumpsThisBonus: 0,
	featureBatchIndex: 0,
	globalFlightMultiplier: 1,
	rejumpState: null,
});

const cloneBoard = (board: V2FeatureCell[][]) =>
	board.map((col) => col.map((cell) => ({ ...cell, appliedThermals: [...cell.appliedThermals] })));

const setCells = (
	state: V2FeatureState,
	positions: Array<{ reel: number; row: number }>,
	fields: Partial<V2FeatureCell>,
) => {
	if (!state.board) throw new Error('board missing');
	const board = cloneBoard(state.board);
	for (const pos of positions) {
		const cell = board[pos.reel][pos.row];
		board[pos.reel][pos.row] = {
			...cell,
			...fields,
			appliedThermals: fields.appliedThermals ?? cell.appliedThermals,
		};
	}
	state.board = board;
};

export const reduceV2Event = (
	state: V2FeatureState,
	event: Record<string, unknown>,
): V2FeatureState => {
	const next: V2FeatureState = {
		...state,
		persistentMysteryTargets: [...state.persistentMysteryTargets],
		board: state.board ? cloneBoard(state.board) : null,
	};
	const type = event.type;
	if (type === 'skyjumpSpinStart') {
		const started = initialV2FeatureState();
		started.mode = String(event.mode ?? 'BASE');
		started.isFreeSpin = Boolean(event.isFreeSpin);
		started.stops = Array.isArray(event.stops) ? [...(event.stops as number[])] : [];
		return started;
	}
	if (type === 'skyjumpBoardReveal') {
		next.board = (event.board as string[][]).map((col) =>
			col.map((symbol) => cellFromSymbol(symbol)),
		);
		return next;
	}
	if (type === 'skyjumpLineWins') {
		next.lineWinX = Number(event.lineWinX);
		next.wins = event.wins;
		return next;
	}
	if (type === 'skyjumpScatterResult') {
		next.scatterCount = Number(event.count);
		next.perfectV = Boolean(event.perfectV);
		next.scatterPositions = event.positions;
		return next;
	}
	if (type === 'skyjumpCoachSignal') {
		next.coachesResolved += 1;
		next.featureChainStep += 1;
		next.lastCoach = {
			selectedSymbolId: (event.selectedSymbolId as string | null) ?? null,
			noOp: Boolean(event.noOp),
		};
		return next;
	}
	if (type === 'skyjumpMysteryTransform') {
		const positions = event.positions as Array<{ reel: number; row: number }>;
		setCells(next, positions, {
			kind: 'mystery',
			symbolId: 'Y',
			tokenTier: null,
			tokenValueX: null,
			faceValueX: null,
			effectiveValueX: null,
			thermalMult: null,
			appliedThermals: [],
		});
		next.mysteriesOpen += positions.length;
		next.featureChainStep += 1;
		return next;
	}
	if (type === 'skyjumpMysteryResolve') {
		const resultType = String(event.resultType);
		const pos = event.position as { reel: number; row: number };
		if (resultType === 'FLIGHT_TOKEN') {
			const face = Number(event.faceValueX !== undefined ? event.faceValueX : event.tokenValueX);
			if (face < 0 || !Number.isFinite(face)) {
				throw new Error('token face value cannot be negative');
			}
			const effective = Number(event.effectiveValueX !== undefined ? event.effectiveValueX : face);
			setCells(next, [pos], {
				kind: 'token',
				symbolId: String(event.tokenId),
				tokenTier: Number(event.tokenTier),
				tokenValueX: face,
				faceValueX: face,
				effectiveValueX: effective,
				thermalMult: null,
				appliedThermals: [],
			});
		} else if (resultType === 'THERMAL_LIFT') {
			setCells(next, [pos], {
				kind: 'thermal',
				symbolId: 'THERMAL',
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: Number(event.thermalMult),
				appliedThermals: [],
			});
		} else if (resultType === 'GATE_UPGRADE') {
			setCells(next, [pos], {
				kind: 'gate',
				symbolId: 'GATE',
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: null,
				appliedThermals: [],
			});
		} else if (resultType === 'JUDGE') {
			setCells(next, [pos], {
				kind: 'judge',
				symbolId: 'JUDGE',
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: null,
				appliedThermals: [],
			});
		} else if (resultType === 'HEAD_JUDGE') {
			setCells(next, [pos], {
				kind: 'head_judge',
				symbolId: 'HEAD_JUDGE',
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: null,
				appliedThermals: [],
			});
		} else if (resultType === 'REJUMP') {
			setCells(next, [pos], {
				kind: 'rejump',
				symbolId: 'REJUMP',
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: null,
				appliedThermals: [],
			});
		} else if (resultType === 'WIND_KEY') {
			setCells(next, [pos], {
				kind: 'wind',
				symbolId: 'WIND',
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: null,
				appliedThermals: [],
			});
		} else {
			throw new Error(`unsupported mystery result ${resultType}`);
		}
		next.mysteriesOpen = Math.max(0, next.mysteriesOpen - 1);
		next.featureChainStep += 1;
		return next;
	}
	if (type === 'skyjumpGateUpgrade') {
		next.tokenFloorTier = Number(event.floorAfter);
		const replacements =
			(event.replacements as Array<{
				reel: number;
				row: number;
				after: { tier: number; face: number };
			}>) ?? [];
		for (const rep of replacements) {
			const after = rep.after;
			setCells(next, [{ reel: rep.reel, row: rep.row }], {
				kind: 'token',
				symbolId: `T${after.tier}`,
				tokenTier: after.tier,
				tokenValueX: after.face,
				faceValueX: after.face,
				effectiveValueX: after.face,
				appliedThermals: [],
			});
		}
		next.featureChainStep += 1;
		next.lastGate = {
			floorBefore: Number(event.floorBefore),
			floorAfter: Number(event.floorAfter),
		};
		return next;
	}
	if (type === 'skyjumpThermalLift') {
		const affected =
			(event.affectedTokens as Array<{
				reel: number;
				row: number;
				faceValueX: number;
				effectiveValueX: number;
				appliedThermals?: number[];
			}>) ?? [];
		if (!next.board) throw new Error('board missing');
		const board = cloneBoard(next.board);
		for (const token of affected) {
			const cell = board[token.reel][token.row];
			const face = Number(
				cell.faceValueX !== null && cell.faceValueX !== undefined
					? cell.faceValueX
					: (cell.tokenValueX ?? 0),
			);
			if (Math.abs(face - Number(token.faceValueX)) > 1e-9) {
				throw new Error('thermal event face mismatch');
			}
			board[token.reel][token.row] = {
				...cell,
				faceValueX: face,
				tokenValueX: face,
				effectiveValueX: Number(token.effectiveValueX),
				appliedThermals: [...(token.appliedThermals ?? [])],
			};
		}
		next.board = board;
		next.featureChainStep += 1;
		next.lastThermal = {
			position: event.position as { reel: number; row: number },
			thermalMult: Number(event.thermalMult),
		};
		return next;
	}
	if (type === 'skyjumpJudgeCollect' || type === 'skyjumpHeadJudgeCollect') {
		const collected = Number(event.collectedX);
		if (collected < 0 || !Number.isFinite(collected)) {
			throw new Error('collection cannot be negative');
		}
		next.featureWinX = Number(next.featureWinX) + collected;
		next.featureWinXRaw = Number(next.featureWinXRaw) + collected;
		next.collectorPasses += 1;
		next.featureChainStep += 1;
		if (event.batchIndex !== undefined) {
			next.featureBatchIndex = Number(event.batchIndex);
		}
		next.lastCollection = {
			type: String(type),
			passIndex: event.passIndex !== undefined ? Number(event.passIndex) : undefined,
			collectedX: collected,
			batchIndex: event.batchIndex !== undefined ? Number(event.batchIndex) : undefined,
			flightMultiplierX:
				event.flightMultiplierX !== undefined ? Number(event.flightMultiplierX) : undefined,
		};
		return next;
	}
	if (type === 'skyjumpWindKey') {
		const stages =
			typeof next.flightMultiplier === 'object' && next.flightMultiplier
				? {
						runUp: { ...next.flightMultiplier.runUp },
						takeoff: { ...next.flightMultiplier.takeoff },
						flight: { ...next.flightMultiplier.flight },
					}
				: defaultFlightMultiplier();
		const stageKey =
			event.selectedStage === 'RUN_UP'
				? 'runUp'
				: event.selectedStage === 'TAKEOFF'
					? 'takeoff'
					: event.selectedStage === 'FLIGHT'
						? 'flight'
						: null;
		if (stageKey && event.action !== 'NO_OP') {
			stages[stageKey] = {
				value: Number(event.newStageValue ?? stages[stageKey].value),
				charge: Number(event.newCharge ?? stages[stageKey].charge),
			};
		}
		syncFlightLegacy(next, stages);
		next.windKeysCollected = Number(event.windKeysCollected ?? (next.windKeysCollected ?? 0) + 1);
		next.featureChainStep += 1;
		next.lastWindKey = {
			selectedStage: (event.selectedStage as string | null) ?? null,
			action: String(event.action ?? 'NO_OP'),
			oldStageValue:
				event.oldStageValue === null || event.oldStageValue === undefined
					? null
					: Number(event.oldStageValue),
			newStageValue:
				event.newStageValue === null || event.newStageValue === undefined
					? null
					: Number(event.newStageValue),
			oldCharge:
				event.oldCharge === null || event.oldCharge === undefined ? null : Number(event.oldCharge),
			newCharge:
				event.newCharge === null || event.newCharge === undefined ? null : Number(event.newCharge),
			oldGlobalMultiplier: Number(event.oldGlobalMultiplier ?? next.globalFlightMultiplier ?? 1),
			newGlobalMultiplier: Number(event.newGlobalMultiplier ?? next.globalFlightMultiplier ?? 1),
		};
		return next;
	}
	if (type === 'skyjumpRejumpStart') {
		next.featureChainStep += 1;
		next.rejumpsThisBonus = Number(next.rejumpsThisBonus ?? 0) + 1;
		next.rejumpState = {
			...(typeof next.rejumpState === 'object' && next.rejumpState ? next.rejumpState : {}),
			chainIndex: Number(event.chainIndex),
			rejumpsThisSpin: Number(event.rejumpsThisSpin),
			preservedPositions: event.preservedPositions,
			redroppedPositions: event.redroppedPositions,
		};
		next.lastRejump = { chainIndex: Number(event.chainIndex) };
		return next;
	}
	if (type === 'skyjumpRejumpBoard') {
		if (Array.isArray(event.board)) {
			next.board = (event.board as string[][]).map((col) =>
				col.map((symbol) => cellFromSymbol(symbol)),
			);
		} else if (Array.isArray(event.changedCells) && next.board) {
			const board = cloneBoard(next.board);
			for (const cell of event.changedCells as Array<{
				reel: number;
				row: number;
				symbolId: string;
			}>) {
				board[cell.reel][cell.row] = cellFromSymbol(cell.symbolId);
			}
			next.board = board;
		}
		next.featureChainStep += 1;
		return next;
	}
	if (type === 'skyjumpRejumpLineWins') {
		const lineWinX = Number(event.lineWinX ?? 0);
		next.featureWinX = Number(next.featureWinX) + lineWinX;
		next.featureWinXRaw = Number(next.featureWinXRaw) + lineWinX;
		next.wins = event.lineWins ?? event.wins;
		next.featureChainStep += 1;
		return next;
	}
	if (type === 'skyjumpRejumpEnd') {
		next.featureChainStep += 1;
		next.lastRejump = {
			chainIndex: Number(event.chainIndex),
			applied: Boolean(event.applied),
			truncated: Boolean(event.truncated),
			reason: (event.reason as string | null) ?? null,
		};
		next.rejumpState = {
			...(typeof next.rejumpState === 'object' && next.rejumpState ? next.rejumpState : {}),
			chainIndex: Number(event.chainIndex),
			truncatedThisSpin: event.truncated
				? Number(
						(next.rejumpState as { truncatedThisSpin?: number } | null)?.truncatedThisSpin ?? 0,
					) + 1
				: ((next.rejumpState as { truncatedThisSpin?: number } | null)?.truncatedThisSpin ?? 0),
		};
		return next;
	}
	if (type === 'skyjumpCapReached') {
		next.capReached = true;
		next.totalWinXRaw = Number(event.rawTotalWinX);
		next.totalWinX = Number(event.cappedTotalWinX);
		next.capDragX = Number(event.capDragX);
		const line = Number(next.lineWinX);
		next.featureWinX = Math.max(0, Number(event.cappedTotalWinX) - line);
		next.featureChainStep += 1;
		return next;
	}
	if (type === 'skyjumpWorldRecord') {
		const pos = event.position as { reel: number; row: number };
		const symbolId = String(event.symbolId ?? 'SPECIAL_WORLD_RECORD');
		if (next.board && pos) {
			setCells(next, [pos], {
				kind: 'unknown',
				symbolId,
				tokenTier: null,
				tokenValueX: null,
				faceValueX: null,
				effectiveValueX: null,
				thermalMult: null,
				appliedThermals: [],
			});
		}
		next.maxWinReached = true;
		next.capReached = true;
		next.freeSpinsRemaining = 0;
		next.worldRecord = {
			position: pos,
			bonusTier: String(event.bonusTier),
			freeSpinIndex: Number(event.freeSpinIndex),
			accruedRoundWinXBefore: Number(event.accruedRoundWinXBefore),
			worldRecordIncrementX: Number(event.worldRecordIncrementX),
			maxWinX: Number(event.maxWinX),
			finalRoundWinX: Number(event.finalRoundWinX),
			remainingFreeSpinsCancelled: Number(event.remainingFreeSpinsCancelled),
			pendingRejumpsCancelled: Boolean(event.pendingRejumpsCancelled),
		};
		next.roundWinXCapped = Number(event.finalRoundWinX);
		next.totalWinX = Number(event.finalRoundWinX);
		next.featureChainStep += 1;
		return next;
	}
	if (type === 'skyjumpResult') {
		next.featureWinX = Number(event.totalFeatureWinX);
		next.featureWinXRaw = Number(
			event.totalFeatureWinXRaw !== undefined ? event.totalFeatureWinXRaw : event.totalFeatureWinX,
		);
		next.totalWinX = Number(event.totalWinX);
		next.totalWinXRaw = Number(
			event.totalWinXRaw !== undefined ? event.totalWinXRaw : event.totalWinX,
		);
		next.amount = Number(event.amount);
		next.tokenFloorTier = Number(
			event.tokenFloorTier !== undefined ? event.tokenFloorTier : next.tokenFloorTier,
		);
		next.capReached = Boolean(event.capHit !== undefined ? event.capHit : next.capReached);
		if (next.featureWinX < 0 || next.totalWinX < 0) {
			throw new Error('payout cannot be negative');
		}
		if (next.totalWinX > 50_000 + 1e-9) {
			throw new Error('capped total cannot exceed max win');
		}
		return next;
	}
	if (type === 'setTotalWin' || type === 'finalWin') {
		next.amount = Number(event.amount);
		return next;
	}
	if (type === 'skyjumpFreeSpinsStart') {
		next.bonusActive = true;
		next.bonusTier = String(event.initialTier);
		next.freeSpinsInitial = Number(event.spinsAwarded);
		next.freeSpinsRemaining = Number(event.spinsAwarded);
		next.freeSpinsPlayed = 0;
		next.totalFreeSpinsAwarded = Number(event.spinsAwarded);
		next.triggerSpinWinX = Number(event.triggerSpinWinX ?? next.totalWinX ?? 0);
		next.tokenFloorTier = 1;
		next.persistentMysteryTargets = [];
		next.guaranteedGateUsed = false;
		next.bonusWinXRaw = 0;
		next.bonusWinXCapped = 0;
		next.maxWinReached = false;
		next.pendingTierUpgrade = null;
		syncFlightLegacy(next, defaultFlightMultiplier());
		next.windKeysCollected = 0;
		next.rejumpsThisBonus = 0;
		next.featureBatchIndex = 0;
		next.rejumpState = null;
		return next;
	}
	if (type === 'skyjumpFreeSpinStart') {
		next.isFreeSpin = true;
		next.bonusActive = true;
		next.bonusTier = String(event.currentTier);
		next.freeSpinsRemaining = Number(event.spinsRemainingBefore);
		next.board = null;
		next.lineWinX = 0;
		next.featureWinX = 0;
		next.featureWinXRaw = 0;
		next.coachesResolved = 0;
		next.mysteriesOpen = 0;
		next.pendingTierUpgrade = null;
		return next;
	}
	if (type === 'skyjumpPersistentTargetsApply') {
		const positions = (event.positions as Array<{ reel: number; row: number }>) ?? [];
		setCells(next, positions, {
			kind: 'mystery',
			symbolId: 'Y',
			tokenTier: null,
			tokenValueX: null,
			faceValueX: null,
			effectiveValueX: null,
			thermalMult: null,
			appliedThermals: [],
		});
		return next;
	}
	if (type === 'skyjumpPersistentTargetsUpdate') {
		next.persistentMysteryTargets = [...((event.persistentMysteryTargets as string[]) ?? [])];
		return next;
	}
	if (type === 'skyjumpGuaranteedGate') {
		next.guaranteedGateUsed = true;
		const position = event.position as { reel: number; row: number };
		setCells(next, [position], {
			kind: 'gate',
			symbolId: 'GATE',
			tokenTier: null,
			tokenValueX: null,
			faceValueX: null,
			effectiveValueX: null,
			thermalMult: null,
			appliedThermals: [],
		});
		return next;
	}
	if (type === 'skyjumpBonusUpgrade') {
		const added = Number(event.spinsAdded ?? 0);
		next.totalFreeSpinsAwarded = Number(
			event.totalFreeSpinsAwarded ?? (next.totalFreeSpinsAwarded ?? 0) + added,
		);
		if (event.spinsRemainingAfter !== undefined) {
			next.freeSpinsRemaining = Number(event.spinsRemainingAfter);
		}
		if (added || Number(event.spinsRequested ?? 0)) {
			next.retriggerCount = (next.retriggerCount ?? 0) + 1;
		}
		if (event.tierChanged) {
			next.upgradeCount = (next.upgradeCount ?? 0) + 1;
			next.pendingTierUpgrade = String(event.toTier);
		}
		return next;
	}
	if (type === 'skyjumpFreeSpinEnd') {
		next.freeSpinsPlayed = Number(event.spinIndex);
		next.freeSpinsRemaining = Number(event.spinsRemainingAfter);
		next.bonusWinXCapped = Number(event.bonusWinRunningX);
		next.board = null;
		next.lineWinX = 0;
		next.featureWinX = 0;
		return next;
	}
	if (type === 'skyjumpFreeSpinState') {
		next.bonusActive = Boolean(event.bonusActive);
		next.bonusTier = (event.bonusTier as string) ?? null;
		next.freeSpinsInitial = Number(event.freeSpinsInitial ?? 0);
		next.freeSpinsRemaining = Number(event.freeSpinsRemaining ?? 0);
		next.freeSpinsPlayed = Number(event.freeSpinsPlayed ?? 0);
		next.totalFreeSpinsAwarded = Number(event.totalFreeSpinsAwarded ?? 0);
		next.upgradeCount = Number(event.upgradeCount ?? 0);
		next.retriggerCount = Number(event.retriggerCount ?? 0);
		next.tokenFloorTier = Number(event.tokenFloorTier ?? 1);
		next.persistentMysteryTargets = [...((event.persistentMysteryTargets as string[]) ?? [])];
		next.guaranteedGateUsed = Boolean(event.guaranteedGateUsed);
		next.bonusWinXRaw = Number(event.bonusWinXRaw ?? 0);
		next.bonusWinXCapped = Number(event.bonusWinXCapped ?? 0);
		next.triggerSpinWinX = Number(event.triggerSpinWinX ?? 0);
		next.roundWinXRaw = Number(event.roundWinXRaw ?? 0);
		next.roundWinXCapped = Number(event.roundWinXCapped ?? 0);
		next.maxWinReached = Boolean(event.maxWinReached);
		next.pendingTierUpgrade = (event.pendingTierUpgrade as string | null) ?? null;
		next.coachGuaranteeState =
			(event.coachGuaranteeState as Record<string, unknown> | null) ?? null;
		const stages = parseFlightMultiplier(event);
		syncFlightLegacy(next, stages);
		next.windKeysCollected = Number(event.windKeysCollected ?? 0);
		next.rejumpsThisBonus = Number(event.rejumpsThisBonus ?? 0);
		next.featureBatchIndex = Number(event.featureBatchIndex ?? 0);
		next.rejumpState = event.rejumpState ?? null;
		if (event.globalFlightMultiplier !== undefined) {
			next.globalFlightMultiplier = Number(event.globalFlightMultiplier);
		}
		next.board = null;
		return next;
	}
	if (type === 'skyjumpFreeSpinsEnd') {
		next.bonusActive = false;
		next.freeSpinsRemaining = 0;
		next.freeSpinsPlayed = Number(event.totalSpinsPlayed);
		next.bonusTier = String(event.finalTier);
		next.bonusWinXCapped = Number(event.bonusWinX);
		next.bonusWinXRaw = Number(event.bonusWinXRaw ?? event.bonusWinX);
		next.triggerSpinWinX = Number(event.triggerSpinWinX);
		next.roundWinXRaw = Number(event.roundWinXRaw);
		next.roundWinXCapped = Number(event.roundWinXCapped);
		next.upgradeCount = Number(event.upgradeCount);
		next.retriggerCount = Number(event.retriggerCount);
		next.maxWinReached = Boolean(event.maxWinReached);
		next.tokenFloorTier = Number(event.tokenFloorTier);
		next.persistentMysteryTargets = [...((event.persistentMysteryTargets as string[]) ?? [])];
		next.guaranteedGateUsed = Boolean(event.guaranteedGateUsed);
		next.totalWinX = Number(event.roundWinXCapped);
		next.board = null;
		if (next.roundWinXCapped > 50_000 + 1e-6) {
			throw new Error('capped round cannot exceed max win');
		}
		return next;
	}
	throw new Error(`unsupported event ${String(type)}`);
};

export const reduceV2Events = (events: Array<Record<string, unknown>>, state?: V2FeatureState) => {
	let current = state
		? { ...state, board: state.board ? cloneBoard(state.board) : null }
		: initialV2FeatureState();
	for (const event of events) current = reduceV2Event(current, event);
	return current;
};

export const boardSymbolGrid = (state: V2FeatureState) => {
	if (!state.board) return null;
	return state.board.map((col) => col.map((cell) => cell.symbolId));
};
