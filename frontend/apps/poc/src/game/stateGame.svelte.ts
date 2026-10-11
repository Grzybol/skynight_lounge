import _ from 'lodash';
import type { Tween } from 'svelte/motion';

import { stateBet, stateUi } from 'state-shared';
import { createEnhanceBoard, createReelForSpinning } from 'utils-slots';
import { createGetWinLevelDataByWinLevelAlias } from 'utils-shared/winLevel';

import type { GameType, RawSymbol, SymbolState } from './types';
import { stateLayoutDerived } from './stateLayout';
import { winLevelMap } from './winLevelMap';
import { eventEmitter } from './eventEmitter';
import {
	SYMBOL_SIZE,
	BOARD_SIZES,
	INITIAL_BOARD,
	BOARD_DIMENSIONS,
	SPIN_OPTIONS_DEFAULT,
	SPIN_OPTIONS_FAST,
	INITIAL_SYMBOL_STATE,
	SCATTER_LAND_SOUND_MAP,
} from './constants';

const onSymbolLand = ({ rawSymbol }: { rawSymbol: RawSymbol }) => {
	if (rawSymbol.name === 'S') {
		eventEmitter.broadcast({ type: 'soundScatterCounterIncrease' });
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: SCATTER_LAND_SOUND_MAP[scatterLandIndex()],
		});
	}

	if (rawSymbol.name === 'W') {
		eventEmitter.broadcast({
			type: 'soundOnce',
			name: 'sfx_multiplier_landing',
		});
	}
};

const board = _.range(BOARD_DIMENSIONS.x).map((reelIndex) => {
	const reel = createReelForSpinning({
		reelIndex,
		symbolHeight: SYMBOL_SIZE,
		initialSymbols: INITIAL_BOARD[reelIndex],
		initialSymbolState: INITIAL_SYMBOL_STATE,
		onReelStopping: () => {
			eventEmitter.broadcast({
				type: 'soundOnce',
				name: 'sfx_reel_stop_1',
				forcePlay: !stateBet.isTurbo,
			});
		},
		onSymbolLand,
	});

	reel.reelState.spinOptions = () =>
		reel.reelState.spinType === 'fast' ? SPIN_OPTIONS_FAST : SPIN_OPTIONS_DEFAULT;

	return reel;
});

export type Reel = (typeof board)[number];
export type ReelSymbol = Reel['reelState']['symbols'][number];

export type MultiplierSymbol = {
	initX: number;
	initY: number;
	symbolX: Tween<number>;
	symbolY: Tween<number>;
	rawSymbol: RawSymbol;
	symbolState: SymbolState;
	oncomplete: () => void;
};

export const stateGame = $state({
	board,
	gameType: 'basegame' as GameType,
	multiplierBoard: [] as (MultiplierSymbol | undefined)[][],
	scatterCounter: 0,
	screen: 'menu' as 'menu' | 'play',
	resumeCatchUp: false,
	/** Phase 7D: true while V2 book presentation holds input locks. */
	v2PresentationLocked: false,
	v2PresentationLockReason: '' as string,
	lastWeather: null as null | {
		id: string;
		label: string;
		iconKey: string;
		temperatureC: number;
		windSpeedMs: number;
		windDirection: string;
		visibilityPct: number;
		distanceDelta?: number;
	},
	presentationPhase: 'idle' as 'idle' | 'weather' | 'reels' | 'slot6' | 'takeoff' | 'result',
	weatherDrawing: false,
});

const GARDEN_SLOT_SCALE = {
	desktop: 1.18,
	tablet: 1.1,
	landscape: 1.14,
	portrait: 1,
} as const;

const GARDEN_BOARD_Y_NUDGE = {
	desktop: 80,
	tablet: 42,
	landscape: 24,
	portrait: 40,
} as const;

const GARDEN_SLOT_X_NUDGE = {
	desktop: 86,
	tablet: 32,
	landscape: 40,
	portrait: 0,
} as const;

const boardLayout = () => {
	const layoutType = stateLayoutDerived.layoutType();
	const garden = stateUi.config.theme === 'garden';
	const nudge = garden ? (GARDEN_BOARD_Y_NUDGE[layoutType] ?? 0) : 0;
	const xNudge = garden ? (GARDEN_SLOT_X_NUDGE[layoutType] ?? 0) : 0;
	const scale = garden ? (GARDEN_SLOT_SCALE[layoutType] ?? 1) : 1;

	return {
		x: stateLayoutDerived.mainLayout().width * 0.5 - xNudge,
		y: stateLayoutDerived.mainLayout().height * 0.5 - nudge,
		anchor: { x: 0.5, y: 0.5 },
		pivot: { x: BOARD_SIZES.width / 2, y: BOARD_SIZES.height / 2 },
		scale,
		...BOARD_SIZES,
	};
};

const boardRaw = () =>
	board.map((reel) => reel.reelState.symbols.map((reelSymbol) => reelSymbol.rawSymbol));

const scatterLandIndex = () => {
	if (stateGame.scatterCounter > 5) return 5;
	if (stateGame.scatterCounter < 1) return 1;
	return stateGame.scatterCounter as 1 | 2 | 3 | 4 | 5;
};

const { enhanceBoard } = createEnhanceBoard();
const enhancedBoard = enhanceBoard({ board: stateGame.board });

export const { getWinLevelDataByWinLevelAlias } = createGetWinLevelDataByWinLevelAlias({
	winLevelMap,
});

export const stateGameDerived = {
	onSymbolLand,
	boardLayout,
	boardRaw,
	scatterLandIndex,
	enhancedBoard,
	getWinLevelDataByWinLevelAlias,
};
