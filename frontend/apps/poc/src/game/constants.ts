import _ from 'lodash';

import type { RawSymbol, SymbolState } from './types';

export const SYMBOL_SIZE = 132;

export const REEL_PADDING = 0.53;

// initial board (padded top and bottom)
export const INITIAL_BOARD: RawSymbol[][] = [
	[
		{
			name: 'L2',
		},
		{
			name: 'L1',
		},
		{
			name: 'L4',
		},
		{
			name: 'H2',
		},
		{
			name: 'L1',
		},
	],
	[
		{
			name: 'H1',
		},
		{
			name: 'L5',
		},
		{
			name: 'L2',
		},
		{
			name: 'H3',
		},
		{
			name: 'L4',
		},
	],
	[
		{
			name: 'L3',
		},
		{
			name: 'L5',
		},
		{
			name: 'L3',
		},
		{
			name: 'H4',
		},
		{
			name: 'L4',
		},
	],
	[
		{
			name: 'H4',
		},
		{
			name: 'H3',
		},
		{
			name: 'L4',
		},
		{
			name: 'L5',
		},
		{
			name: 'L1',
		},
	],
	[
		{
			name: 'H3',
		},
		{
			name: 'L3',
		},
		{
			name: 'L3',
		},
		{
			name: 'H1',
		},
		{
			name: 'H1',
		},
	],
];

export const BOARD_DIMENSIONS = { x: INITIAL_BOARD.length, y: INITIAL_BOARD[0].length - 2 };

export const BOARD_SIZES = {
	width: SYMBOL_SIZE * BOARD_DIMENSIONS.x,
	height: SYMBOL_SIZE * BOARD_DIMENSIONS.y,
};

export const BACKGROUND_RATIO = 2039 / 1000;
export const PORTRAIT_BACKGROUND_RATIO = 1242 / 2208;
const PORTRAIT_RATIO = 800 / 1422;
const LANDSCAPE_RATIO = 1600 / 900;
const DESKTOP_RATIO = 1422 / 800;

const DESKTOP_HEIGHT = 800;
const LANDSCAPE_HEIGHT = 900;
const PORTRAIT_HEIGHT = 1422;
export const DESKTOP_MAIN_SIZES = { width: DESKTOP_HEIGHT * DESKTOP_RATIO, height: DESKTOP_HEIGHT };
export const LANDSCAPE_MAIN_SIZES = {
	width: LANDSCAPE_HEIGHT * LANDSCAPE_RATIO,
	height: LANDSCAPE_HEIGHT,
};
export const PORTRAIT_MAIN_SIZES = {
	width: PORTRAIT_HEIGHT * PORTRAIT_RATIO,
	height: PORTRAIT_HEIGHT,
};

export const HIGH_SYMBOLS = ['H1', 'H2', 'H3', 'H4', 'H5'];

export const INITIAL_SYMBOL_STATE: SymbolState = 'static';

const SPIN_OPTIONS_SHARED = {
	reelBounceBackSpeed: 0.15,
	reelSpinSpeedBeforeBounce: 4,
	reelPaddingMultiplierNormal: 1.2,
	reelPaddingMultiplierAnticipated: 10,
	reelSpinDelay: 145,
};

export const SPIN_OPTIONS_DEFAULT = {
	...SPIN_OPTIONS_SHARED,
	reelPreSpinSpeed: 2,
	reelSpinSpeed: 3,
	reelBounceSizeMulti: 0.3,
};

export const SPIN_OPTIONS_FAST = {
	...SPIN_OPTIONS_SHARED,
	reelPreSpinSpeed: 5,
	reelSpinSpeed: 5,
	reelBounceSizeMulti: 0.05,
};

export const MOTION_BLUR_VELOCITY = 31;

export const zIndexes = {
	background: {
		backdrop: -3,
		normal: -2,
		feature: -1,
	},
};

const h1Static = { type: 'sprite', assetKey: 'h1.webp', sizeRatios: { width: 1, height: 1 } };
const h2Static = { type: 'sprite', assetKey: 'h2.webp', sizeRatios: { width: 1, height: 1 } };
const h3Static = { type: 'sprite', assetKey: 'h3.webp', sizeRatios: { width: 1, height: 1 } };
const h4Static = { type: 'sprite', assetKey: 'h4.webp', sizeRatios: { width: 1, height: 1 } };
const h5Static = { type: 'sprite', assetKey: 'h5.webp', sizeRatios: { width: 1, height: 1 } };

const l1Static = { type: 'sprite', assetKey: 'l1.webp', sizeRatios: { width: 1, height: 1 } };
const l2Static = { type: 'sprite', assetKey: 'l2.webp', sizeRatios: { width: 1, height: 1 } };
const l3Static = { type: 'sprite', assetKey: 'l3.webp', sizeRatios: { width: 1, height: 1 } };
const l4Static = { type: 'sprite', assetKey: 'l4.webp', sizeRatios: { width: 1, height: 1 } };
const l5Static = {
	type: 'sprite',
	assetKey: 'm1_2x.png',
	sizeRatios: { width: 0.88, height: 0.88 },
};

const sStatic = { type: 'sprite', assetKey: 's.png', sizeRatios: { width: 1.04, height: 1.04 } };
const wStatic = { type: 'sprite', assetKey: 'w.png', sizeRatios: { width: 1.02, height: 1.02 } };
const animated = <T extends { assetKey: string; sizeRatios: { width: number; height: number } }>(
	symbol: T,
	animation: 'win' | 'land' | 'wildWin' | 'wildLand' | 'scatterWin' | 'scatterLand' | 'explosion',
) => ({ ...symbol, type: 'animatedSprite', animation });

export const SYMBOL_INFO_MAP = {
	H1: {
		explosion: animated(h1Static, 'explosion'),
		win: animated(h1Static, 'win'),
		postWinStatic: h1Static,
		static: h1Static,
		spin: h1Static,
		land: animated(h1Static, 'land'),
	},
	H2: {
		explosion: animated(h2Static, 'explosion'),
		win: animated(h2Static, 'win'),
		postWinStatic: h2Static,
		static: h2Static,
		spin: h2Static,
		land: animated(h2Static, 'land'),
	},
	H3: {
		explosion: animated(h3Static, 'explosion'),
		win: animated(h3Static, 'win'),
		postWinStatic: h3Static,
		static: h3Static,
		spin: h3Static,
		land: animated(h3Static, 'land'),
	},
	H4: {
		explosion: animated(h4Static, 'explosion'),
		win: animated(h4Static, 'win'),
		postWinStatic: h4Static,
		static: h4Static,
		spin: h4Static,
		land: animated(h4Static, 'land'),
	},
	H5: {
		explosion: animated(h5Static, 'explosion'),
		win: animated(h5Static, 'win'),
		postWinStatic: h5Static,
		static: h5Static,
		spin: h5Static,
		land: animated(h5Static, 'land'),
	},
	L1: {
		explosion: animated(l1Static, 'explosion'),
		win: animated(l1Static, 'win'),
		postWinStatic: l1Static,
		static: l1Static,
		spin: l1Static,
		land: animated(l1Static, 'land'),
	},
	L2: {
		explosion: animated(l2Static, 'explosion'),
		win: animated(l2Static, 'win'),
		postWinStatic: l2Static,
		static: l2Static,
		spin: l2Static,
		land: animated(l2Static, 'land'),
	},
	L3: {
		explosion: animated(l3Static, 'explosion'),
		win: animated(l3Static, 'win'),
		postWinStatic: l3Static,
		static: l3Static,
		spin: l3Static,
		land: animated(l3Static, 'land'),
	},
	L4: {
		explosion: animated(l4Static, 'explosion'),
		win: animated(l4Static, 'win'),
		postWinStatic: l4Static,
		static: l4Static,
		spin: l4Static,
		land: animated(l4Static, 'land'),
	},
	L5: {
		explosion: animated(l5Static, 'explosion'),
		win: animated(l5Static, 'win'),
		postWinStatic: l5Static,
		static: l5Static,
		spin: l5Static,
		land: animated(l5Static, 'land'),
	},
	W: {
		explosion: animated(wStatic, 'explosion'),
		postWinStatic: {
			type: 'sprite',
			assetKey: 'explodedW.png',
			sizeRatios: { width: 0.85, height: 0.85 },
		},
		static: wStatic,
		spin: wStatic,
		win: animated(wStatic, 'wildWin'),
		land: animated(wStatic, 'wildLand'),
	},
	S: {
		explosion: animated(sStatic, 'explosion'),
		postWinStatic: sStatic,
		static: sStatic,
		spin: sStatic,
		win: animated(sStatic, 'scatterWin'),
		land: animated(sStatic, 'scatterLand'),
	},
} as const;

export const SCATTER_LAND_SOUND_MAP = {
	1: 'sfx_scatter_stop_1',
	2: 'sfx_scatter_stop_2',
	3: 'sfx_scatter_stop_3',
	4: 'sfx_scatter_stop_4',
	5: 'sfx_scatter_stop_5',
} as const;
