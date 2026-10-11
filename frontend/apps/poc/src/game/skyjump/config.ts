import rawConfig from '../../../../../../math/games/0_0_poc/skyjump_config.json' with { type: 'json' };

import type {
	BetModeKey,
	HillConfig,
	HillId,
	MultiplierOutcome,
	MultiplierTableId,
	SlotRole,
	TimingProfile,
	WeatherConfig,
} from './types.ts';

export const SKYJUMP_META = rawConfig.meta;
export const BOOK_AMOUNT_MULTIPLIER = rawConfig.bookAmountMultiplier as number;
export const EVENT_SCHEMA_VERSION = rawConfig.eventSchemaVersion as number;
export const MATH_VERSION = Number((rawConfig.meta as { mathVersion?: number }).mathVersion ?? 1);
export const TARGET_RTP = Number((rawConfig.meta as { targetRtp?: number }).targetRtp ?? 0.97);
export const VOLATILITY_MODEL = rawConfig.volatilityModel as {
	epicBoost: number;
	rareBoost: number;
	uncommonBoost: number;
	commonNerf: number;
	minWeight: number;
	biasClamp: number;
};

export const WEATHER_TABLE = rawConfig.weather as WeatherConfig[];
export const HILL_TABLE = rawConfig.hills as Record<HillId, HillConfig>;
export const MULTIPLIER_TABLES = rawConfig.finalMultipliers as Record<
	MultiplierTableId,
	MultiplierOutcome[]
>;
export const MULTIPLIER_MISS_TABLES = ((
	rawConfig as { finalMultiplierMissTables?: Record<string, MultiplierOutcome[]> }
).finalMultiplierMissTables ?? {}) as Partial<Record<MultiplierTableId, MultiplierOutcome[]>>;

export type CanonicalBuyMode = {
	id: string;
	rgsKey: BetModeKey;
	label: string;
	costMultiplier: number;
	hillProfile: HillId;
	multiplierProfile: MultiplierTableId;
	maxWin: number;
	enabled: boolean;
	type: 'default' | 'buy';
	title: string;
	dialog: string;
	description: string;
	button: string;
	betAmountLabel: string;
	tickerIdle: string;
	tickerSpin: string;
};

export const BUY_MODES = rawConfig.buyModes as Record<string, CanonicalBuyMode>;

/** Canonical JSON object order. Disabled modes stay out of HUD / RGS lists. */
export const ENABLED_MODES = Object.values(BUY_MODES).filter((mode) => mode.enabled !== false);
export const ENABLED_BUY_MODES = ENABLED_MODES.filter((mode) => mode.type === 'buy');
export const DEFAULT_BET_MODE =
	ENABLED_MODES.find((mode) => mode.type === 'default') ?? BUY_MODES.base;

/** Player-facing title. Frozen JSON `meta.altTitle` is metadata debt — do not read it at runtime. */
export const PUBLIC_GAME_TITLE = 'Midnight Lounge';

export const PLACEHOLDER_IDENTITY = {
	gameID: String((rawConfig.meta as { gameID?: string }).gameID ?? '0_0_poc'),
	providerName: 'poc_studio',
	providerNumber: 0,
	version: '0.1.0-skyjump',
} as const;

export const BET_MODE_TO_TABLES = Object.fromEntries(
	Object.values(BUY_MODES).map((mode) => [
		mode.rgsKey,
		{
			hillId: mode.hillProfile,
			multiplierTableId: mode.multiplierProfile,
			costMultiplier: mode.costMultiplier,
			maxWin: mode.maxWin,
			id: mode.id,
		},
	]),
) as Record<
	BetModeKey,
	{
		hillId: HillId;
		multiplierTableId: MultiplierTableId;
		costMultiplier: number;
		maxWin: number;
		id: string;
	}
>;

const multiplierRole: SlotRole = {
	id: 'multiplier',
	index: 5,
	label: 'Final Jump Multiplier',
	shortLabel: 'MULT',
	iconKey: 'cash',
	symbols: [],
};

export const SLOT_ROLES: SlotRole[] = [...(rawConfig.slots as SlotRole[]), multiplierRole];

export const ROLE_SLOT_COUNT = 5;
export const TOTAL_SLOT_COUNT = 6;

export const MISS_FINAL_MULTIPLIER = {
	id: 'x0',
	label: 'x0',
	multiplier: 0,
} as const;

export const paylineDistance = (hillId: HillId) =>
	HILL_TABLE[hillId]?.payoutCurve.find((band) => band.baseWinX > 0)?.minDistance ?? 0;

export const TIMING_PROFILES: Record<'normal' | 'turbo', TimingProfile> = {
	normal: {
		id: 'normal',
		weatherCycleMs: 580,
		weatherHoldMs: 820,
		weatherStatsMs: 380,
		reelSpinMs: 1000,
		reelStopMs: 520,
		reelGapMs: 180,
		takeoffMs: 420,
		overlayIntroMs: 360,
		countUpFastMs: 780,
		countUpSlowMs: 720,
		baseTermMs: 420,
		baseCountMs: 1600,
		localMultHoldMs: 640,
		finalMultHoldMs: 820,
		finalWinHoldMs: 2800,
	},
	turbo: {
		id: 'turbo',
		weatherCycleMs: 220,
		weatherHoldMs: 360,
		weatherStatsMs: 200,
		reelSpinMs: 320,
		reelStopMs: 150,
		reelGapMs: 50,
		takeoffMs: 120,
		overlayIntroMs: 180,
		countUpFastMs: 220,
		countUpSlowMs: 280,
		baseTermMs: 110,
		baseCountMs: 420,
		localMultHoldMs: 280,
		finalMultHoldMs: 420,
		finalWinHoldMs: 900,
	},
};
