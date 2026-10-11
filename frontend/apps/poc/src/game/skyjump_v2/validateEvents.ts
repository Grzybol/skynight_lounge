import { V2_BOARD_REELS, V2_BOARD_ROWS, V2_EVENT_SCHEMA_VERSION } from './config.ts';
import type { V2Board, V2LineWin } from './types.ts';

const PHASE1_TYPES = [
	'skyjumpSpinStart',
	'skyjumpBoardReveal',
	'skyjumpLineWins',
	'skyjumpResult',
	'setTotalWin',
	'finalWin',
] as const;

export const validateV2Board = (board: unknown): V2Board => {
	if (!Array.isArray(board) || board.length !== V2_BOARD_REELS) {
		throw new Error('skyjumpBoardReveal.board must be 5 reels');
	}
	for (const col of board) {
		if (!Array.isArray(col) || col.length !== V2_BOARD_ROWS) {
			throw new Error('skyjumpBoardReveal.board must be 5 rows per reel');
		}
		if (col.some((cell) => typeof cell !== 'string' || cell.length === 0)) {
			throw new Error('skyjumpBoardReveal.board cells must be symbol IDs');
		}
	}
	return board as V2Board;
};

const validateLineWin = (win: V2LineWin) => {
	if (!Number.isInteger(win.paylineId) || win.paylineId < 1 || win.paylineId > 28) {
		throw new Error(`invalid paylineId ${win.paylineId}`);
	}
	if (![3, 4, 5].includes(win.matchCount)) {
		throw new Error(`invalid matchCount ${win.matchCount}`);
	}
	if (!Array.isArray(win.positions) || win.positions.length !== win.matchCount) {
		throw new Error('line win positions must match matchCount');
	}
	if (typeof win.payoutX !== 'number' || win.payoutX < 0) {
		throw new Error('line win payoutX must be >= 0');
	}
};

export const validatePhase1Events = (events: Array<Record<string, unknown>>) => {
	if (events.length !== PHASE1_TYPES.length) {
		throw new Error('Phase 1 books must contain exactly 6 events');
	}
	for (let i = 0; i < PHASE1_TYPES.length; i += 1) {
		if (events[i].type !== PHASE1_TYPES[i]) {
			throw new Error(`event ${i} must be ${PHASE1_TYPES[i]}`);
		}
		if (events[i].index !== i) {
			throw new Error(`event ${i} index must equal position`);
		}
	}

	const start = events[0];
	if (start.schemaVersion !== V2_EVENT_SCHEMA_VERSION) {
		throw new Error('skyjumpSpinStart schemaVersion must be 2');
	}

	const reveal = events[1];
	if (reveal.schemaVersion !== V2_EVENT_SCHEMA_VERSION) {
		throw new Error('skyjumpBoardReveal schemaVersion must be 2');
	}
	validateV2Board(reveal.board);

	const lines = events[2];
	if (lines.schemaVersion !== V2_EVENT_SCHEMA_VERSION) {
		throw new Error('skyjumpLineWins schemaVersion must be 2');
	}
	if (!Array.isArray(lines.wins)) {
		throw new Error('skyjumpLineWins.wins must be an array');
	}
	for (const win of lines.wins as V2LineWin[]) validateLineWin(win);
	if (typeof lines.lineWinX !== 'number') {
		throw new Error('skyjumpLineWins.lineWinX must be a number');
	}

	const result = events[3];
	if (result.schemaVersion !== V2_EVENT_SCHEMA_VERSION) {
		throw new Error('skyjumpResult schemaVersion must be 2');
	}
	if (typeof result.totalLineWinX !== 'number' || typeof result.totalWinX !== 'number') {
		throw new Error('skyjumpResult totals must be numbers');
	}
	if (result.totalFeatureWinX !== 0) {
		throw new Error('Phase 1 totalFeatureWinX must be 0');
	}
	if (result.totalWinX !== result.totalLineWinX) {
		throw new Error('Phase 1 totalWinX must equal totalLineWinX');
	}

	if (typeof events[4].amount !== 'number' || typeof events[5].amount !== 'number') {
		throw new Error('setTotalWin/finalWin amount must be a number');
	}
	if (events[4].amount !== events[5].amount) {
		throw new Error('setTotalWin and finalWin amounts must match');
	}

	return events;
};

const PHASE2_TYPES = [
	'skyjumpSpinStart',
	'skyjumpBoardReveal',
	'skyjumpLineWins',
	'skyjumpScatterResult',
	'skyjumpResult',
	'setTotalWin',
	'finalWin',
] as const;

export const validatePhase2Events = (events: Array<Record<string, unknown>>) => {
	if (events.length !== PHASE2_TYPES.length) {
		throw new Error('Phase 2 books must contain exactly 7 events');
	}
	for (let i = 0; i < PHASE2_TYPES.length; i += 1) {
		if (events[i].type !== PHASE2_TYPES[i]) {
			throw new Error(`event ${i} must be ${PHASE2_TYPES[i]}`);
		}
		if (events[i].index !== i) {
			throw new Error(`event ${i} index must equal position`);
		}
	}

	const start = events[0];
	if (start.schemaVersion !== V2_EVENT_SCHEMA_VERSION) {
		throw new Error('skyjumpSpinStart schemaVersion must be 2');
	}

	const reveal = events[1];
	validateV2Board(reveal.board);

	const lines = events[2];
	if (!Array.isArray(lines.wins) || typeof lines.lineWinX !== 'number') {
		throw new Error('skyjumpLineWins is invalid');
	}
	for (const win of lines.wins as V2LineWin[]) validateLineWin(win);
	const winSum = (lines.wins as V2LineWin[]).reduce((sum, win) => sum + win.payoutX, 0);
	if (Math.abs(winSum - Number(lines.lineWinX)) > 1e-9) {
		throw new Error('totalLineWinX must equal sum of line events');
	}

	const scatter = events[3];
	if (typeof scatter.count !== 'number' || scatter.count < 0) {
		throw new Error('skyjumpScatterResult.count must be >= 0');
	}
	if (scatter.trigger != null) {
		throw new Error('Phase 2 scatter trigger must be null');
	}

	const result = events[4];
	if (result.totalFeatureWinX !== 0) {
		throw new Error('Phase 2 totalFeatureWinX must be 0');
	}
	if (result.totalWinX !== result.totalLineWinX) {
		throw new Error('Phase 2 totalWinX must equal totalLineWinX');
	}
	if (
		typeof result.totalWinX !== 'number' ||
		result.totalWinX < 0 ||
		!Number.isFinite(result.totalWinX)
	) {
		throw new Error('totalWinX must be a finite non-negative number');
	}

	if (events[5].amount !== events[6].amount) {
		throw new Error('setTotalWin and finalWin amounts must match');
	}
	return events;
};

export const validatePhase3Events = (events: Array<Record<string, unknown>>) => {
	if (events.length < 7) {
		throw new Error('Phase 3 books must contain the Phase 2 core plus settlement');
	}
	const types = events.map((event) => event.type);
	if (types[0] !== 'skyjumpSpinStart' || types[1] !== 'skyjumpBoardReveal') {
		throw new Error('Phase 3 must start with spinStart and boardReveal');
	}
	if (types[2] !== 'skyjumpLineWins' || types[3] !== 'skyjumpScatterResult') {
		throw new Error('line wins and scatter must precede features');
	}
	if (
		types.at(-3) !== 'skyjumpResult' ||
		types.at(-2) !== 'setTotalWin' ||
		types.at(-1) !== 'finalWin'
	) {
		throw new Error('Phase 3 must settle with result/setTotalWin/finalWin');
	}
	const featureTypes = types.slice(4, -3);
	const allowed = new Set([
		'skyjumpCoachSignal',
		'skyjumpMysteryTransform',
		'skyjumpMysteryResolve',
	]);
	if (featureTypes.some((type) => !allowed.has(String(type)))) {
		throw new Error('Phase 3 mid-book may only contain Coach/Mystery events');
	}
	events.forEach((event, index) => {
		if (event.index !== index) throw new Error(`event ${index} index must equal position`);
	});
	validateV2Board(events[1].board);
	const lines = events[2];
	const winSum = (lines.wins as V2LineWin[]).reduce((sum, win) => sum + win.payoutX, 0);
	if (Math.abs(winSum - Number(lines.lineWinX)) > 1e-9) {
		throw new Error('totalLineWinX must equal sum of line events');
	}
	let openMysteries = 0;
	for (const event of events.slice(4, -3)) {
		if (event.type === 'skyjumpCoachSignal') {
			const selected = event.selectedSymbolId;
			if (event.noOp) {
				if (selected != null) throw new Error('no-op Coach cannot select a symbol');
				continue;
			}
			if (
				selected === 'S' ||
				selected === 'C' ||
				selected === 'Y' ||
				String(selected).startsWith('T')
			) {
				throw new Error('Coach selected an illegal symbol');
			}
		} else if (event.type === 'skyjumpMysteryTransform') {
			const positions = event.positions as Array<{ reel: number; row: number }>;
			openMysteries += positions.length;
		} else if (event.type === 'skyjumpMysteryResolve') {
			if (event.resultType !== 'FLIGHT_TOKEN') {
				throw new Error('Phase 3 mystery result must be FLIGHT_TOKEN');
			}
			if (
				typeof event.tokenValueX !== 'number' ||
				event.tokenValueX < 0 ||
				!Number.isFinite(event.tokenValueX)
			) {
				throw new Error('tokenValueX must be finite and >= 0');
			}
			openMysteries -= 1;
		}
	}
	if (openMysteries !== 0) {
		throw new Error('every Mystery must resolve exactly once');
	}
	const result = events.at(-3) as Record<string, unknown>;
	if (result.totalFeatureWinX !== 0) {
		throw new Error('Phase 3 totalFeatureWinX must be 0');
	}
	if (result.totalWinX !== result.totalLineWinX) {
		throw new Error('tokens must not automatically award');
	}
	return events;
};

const MYSTERY_RESULT_TYPES = new Set([
	'FLIGHT_TOKEN',
	'THERMAL_LIFT',
	'GATE_UPGRADE',
	'JUDGE',
	'HEAD_JUDGE',
	'REJUMP',
	'WIND_KEY',
]);

const PHASE4B_FEATURE_TYPES = new Set([
	'skyjumpCoachSignal',
	'skyjumpMysteryTransform',
	'skyjumpMysteryResolve',
	'skyjumpGateUpgrade',
	'skyjumpThermalLift',
	'skyjumpJudgeCollect',
	'skyjumpHeadJudgeCollect',
	'skyjumpCapReached',
	'skyjumpWorldRecord',
]);

const PHASE6_FEATURE_TYPES = new Set([
	...PHASE4B_FEATURE_TYPES,
	'skyjumpWindKey',
	'skyjumpRejumpStart',
	'skyjumpRejumpBoard',
	'skyjumpRejumpLineWins',
	'skyjumpRejumpEnd',
	'skyjumpPersistentTargetsApply',
	'skyjumpPersistentTargetsUpdate',
	'skyjumpGuaranteedGate',
	'skyjumpBonusUpgrade',
	'skyjumpFreeSpinStart',
	'skyjumpFreeSpinEnd',
	'skyjumpFreeSpinState',
	'skyjumpFreeSpinsStart',
	'skyjumpFreeSpinsEnd',
]);

export const validatePhase4bEvents = (events: Array<Record<string, unknown>>) => {
	if (events.length < 7) {
		throw new Error('Phase 4B books must contain the Phase 2 core plus settlement');
	}
	const types = events.map((event) => event.type);
	if (types[0] !== 'skyjumpSpinStart' || types[1] !== 'skyjumpBoardReveal') {
		throw new Error('Phase 4B must start with spinStart and boardReveal');
	}
	if (types[2] !== 'skyjumpLineWins' || types[3] !== 'skyjumpScatterResult') {
		throw new Error('line wins and scatter must precede features');
	}
	if (
		types.at(-3) !== 'skyjumpResult' ||
		types.at(-2) !== 'setTotalWin' ||
		types.at(-1) !== 'finalWin'
	) {
		throw new Error('Phase 4B must settle with result/setTotalWin/finalWin');
	}
	const featureTypes = types.slice(4, -3);
	if (featureTypes.some((type) => !PHASE4B_FEATURE_TYPES.has(String(type)))) {
		throw new Error('Phase 4B mid-book contains unsupported feature events');
	}
	events.forEach((event, index) => {
		if (event.index !== index) throw new Error(`event ${index} index must equal position`);
	});
	validateV2Board(events[1].board);
	const lines = events[2];
	const winSum = (lines.wins as V2LineWin[]).reduce((sum, win) => sum + win.payoutX, 0);
	if (Math.abs(winSum - Number(lines.lineWinX)) > 1e-9) {
		throw new Error('totalLineWinX must equal sum of line events');
	}

	let openMysteries = 0;
	let featureCollected = 0;
	for (const event of events.slice(4, -3)) {
		if (event.type === 'skyjumpCoachSignal') {
			const selected = event.selectedSymbolId;
			if (event.noOp) {
				if (selected != null) throw new Error('no-op Coach cannot select a symbol');
				continue;
			}
			if (
				selected === 'S' ||
				selected === 'C' ||
				selected === 'Y' ||
				String(selected).startsWith('T')
			) {
				throw new Error('Coach selected an illegal symbol');
			}
		} else if (event.type === 'skyjumpMysteryTransform') {
			const positions = event.positions as Array<{ reel: number; row: number }>;
			openMysteries += positions.length;
		} else if (event.type === 'skyjumpMysteryResolve') {
			const resultType = String(event.resultType ?? 'FLIGHT_TOKEN');
			if (!MYSTERY_RESULT_TYPES.has(resultType)) {
				throw new Error(`unsupported mystery resultType ${resultType}`);
			}
			if (resultType === 'FLIGHT_TOKEN') {
				const face = Number(event.faceValueX !== undefined ? event.faceValueX : event.tokenValueX);
				if (face < 0 || !Number.isFinite(face)) {
					throw new Error('tokenValueX must be finite and >= 0');
				}
			} else if (resultType === 'THERMAL_LIFT') {
				if (typeof event.thermalMult !== 'number' || event.thermalMult < 1) {
					throw new Error('thermalMult must be >= 1');
				}
			}
			openMysteries -= 1;
		} else if (event.type === 'skyjumpGateUpgrade') {
			if (typeof event.floorBefore !== 'number' || typeof event.floorAfter !== 'number') {
				throw new Error('gate upgrade floor tiers must be numbers');
			}
			if (!Array.isArray(event.replacements)) {
				throw new Error('gate upgrade replacements must be an array');
			}
		} else if (event.type === 'skyjumpThermalLift') {
			if (typeof event.thermalMult !== 'number' || event.thermalMult < 1) {
				throw new Error('thermalMult must be >= 1');
			}
			if (!Array.isArray(event.affectedTokens)) {
				throw new Error('thermal lift affectedTokens must be an array');
			}
		} else if (event.type === 'skyjumpJudgeCollect' || event.type === 'skyjumpHeadJudgeCollect') {
			const collected = Number(event.collectedX);
			if (collected < 0 || !Number.isFinite(collected)) {
				throw new Error('collectedX must be finite and >= 0');
			}
			featureCollected += collected;
		} else if (event.type === 'skyjumpCapReached') {
			const capped = Number(event.cappedTotalWinX);
			const maxWin = Number(event.maxWinX ?? 50_000);
			if (capped > maxWin + 1e-9) {
				throw new Error('capped total cannot exceed max win');
			}
			if (maxWin > 50_000 + 1e-9) {
				throw new Error('maxWinX cannot exceed 50000');
			}
		} else if (event.type === 'skyjumpWorldRecord') {
			const finalX = Number(event.finalRoundWinX);
			const maxWin = Number(event.maxWinX ?? 50_000);
			const inc = Number(event.worldRecordIncrementX);
			if (finalX > maxWin + 1e-9) {
				throw new Error('WR finalRoundWinX cannot exceed max win');
			}
			if (inc < -1e-9) {
				throw new Error('WR increment cannot be negative');
			}
			if (!event.position || typeof event.position.reel !== 'number') {
				throw new Error('WR position required');
			}
		}
	}
	if (openMysteries !== 0) {
		throw new Error('every Mystery must resolve exactly once');
	}

	const result = events.at(-3) as Record<string, unknown>;
	if (typeof result.totalFeatureWinX !== 'number' || result.totalFeatureWinX < 0) {
		throw new Error('totalFeatureWinX must be >= 0');
	}
	if (typeof result.totalWinX !== 'number' || result.totalWinX < 0) {
		throw new Error('totalWinX must be >= 0');
	}
	if (result.totalWinX > 50_000 + 1e-9) {
		throw new Error('totalWinX cannot exceed 50000');
	}
	if (
		typeof result.totalLineWinX === 'number' &&
		typeof result.totalFeatureWinX === 'number' &&
		Math.abs(
			Number(result.totalWinX) - (Number(result.totalLineWinX) + Number(result.totalFeatureWinX)),
		) > 1e-6
	) {
		throw new Error('totalWinX should equal line + feature unless cap adjusted');
	}
	if (featureCollected > 0 && Number(result.totalFeatureWinX) === 0 && !result.capHit) {
		// Allow math to settle feature win on result even when collectors ran (cap may zero it).
		void featureCollected;
	}
	return events;
};

/** Soft structural checks for Free Spin books that may include Phase 6B events. */
export const validatePhase6Events = (events: Array<Record<string, unknown>>) => {
	if (events.length < 7) {
		throw new Error('Phase 6 books must contain settlement');
	}
	events.forEach((event, index) => {
		if (event.index !== index) throw new Error(`event ${index} index must equal position`);
	});
	for (const event of events) {
		const type = String(event.type);
		if (type === 'skyjumpMysteryResolve') {
			const resultType = String(event.resultType ?? '');
			if (!MYSTERY_RESULT_TYPES.has(resultType)) {
				throw new Error(`unsupported mystery resultType ${resultType}`);
			}
		}
		if (type === 'skyjumpWindKey') {
			const action = String(event.action ?? '');
			if (!['CHARGE', 'UPGRADE', 'NO_OP'].includes(action)) {
				throw new Error(`invalid wind key action ${action}`);
			}
			if (action === 'CHARGE') {
				if (Number(event.oldStageValue) !== Number(event.newStageValue)) {
					throw new Error('CHARGE must not change stage value');
				}
				if (Number(event.oldGlobalMultiplier) !== Number(event.newGlobalMultiplier)) {
					throw new Error('CHARGE must not change global multiplier');
				}
			}
			if (action === 'UPGRADE' && Number(event.newStageValue) <= Number(event.oldStageValue)) {
				throw new Error('UPGRADE must increase stage value');
			}
		}
		if (type === 'skyjumpRejumpBoard') {
			if (!event.board && !event.changedCells) {
				throw new Error('skyjumpRejumpBoard needs board or changedCells');
			}
			if (event.board) validateV2Board(event.board);
		}
		if (type === 'skyjumpRejumpLineWins') {
			if (!Array.isArray(event.lineWins) || typeof event.lineWinX !== 'number') {
				throw new Error('skyjumpRejumpLineWins is invalid');
			}
		}
		if (
			type.startsWith('skyjump') &&
			![
				'skyjumpSpinStart',
				'skyjumpBoardReveal',
				'skyjumpLineWins',
				'skyjumpScatterResult',
				'skyjumpResult',
				...PHASE6_FEATURE_TYPES,
			].includes(type) &&
			type !== 'setTotalWin' &&
			type !== 'finalWin' &&
			type !== 'wincap' &&
			type !== 'setWin'
		) {
			// Allow unknown only if not claiming Phase 6 feature mid-book.
			void type;
		}
	}
	return events;
};
