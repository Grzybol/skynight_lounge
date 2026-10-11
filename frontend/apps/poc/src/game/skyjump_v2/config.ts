import rawConfig from '../../../../../../math/games/0_0_poc/skyjump_v2_config.json' with { type: 'json' };

export const V2_CONFIG = rawConfig;

export const V2_LINEAGE = String(rawConfig.meta.lineage);
export const V2_MATH_VERSION = Number(rawConfig.meta.mathVersion);
export const V2_EVENT_SCHEMA_VERSION = Number(rawConfig.eventSchemaVersion);
export const V2_BOARD_REELS = Number(rawConfig.board.reels);
export const V2_BOARD_ROWS = Number(rawConfig.board.rows);
export const V2_MAX_FEATURE_CHAIN_DEPTH = Number(rawConfig.maxFeatureChainDepth);
export const V2_DESKTOP_LOGICAL = rawConfig.layout.desktopLogical as {
	width: number;
	height: number;
};
export const V2_BOOK_AMOUNT_MULTIPLIER = Number(rawConfig.bookAmountMultiplier);
export const V2_SCATTER_ID = String(rawConfig.symbols.scatter.id);

export const V2_REGULAR_SYMBOLS = rawConfig.symbols.regular as Array<{
	id: string;
	name: string;
	class: string;
}>;

export const V2_REGULAR_IDS = new Set(V2_REGULAR_SYMBOLS.map((row) => row.id));

export const V2_PAYLINES = Object.fromEntries(
	Object.entries(rawConfig.paylines as Record<string, number[]>).map(([id, rows]) => [
		Number(id),
		rows,
	]),
) as Record<number, number[]>;

export const V2_PAYLINE_IDS = Object.keys(V2_PAYLINES)
	.map(Number)
	.sort((a, b) => a - b);

export const V2_CANONICAL_PAYTABLE = (
	rawConfig as {
		paytable: {
			status: string;
			nonFinal: boolean;
			candidateOrigin?: string;
			awards: Record<string, Record<string, number>>;
		};
	}
).paytable;

/** @deprecated alias — use V2_CANONICAL_PAYTABLE */
export const V2_PROVISIONAL_PAYTABLE = V2_CANONICAL_PAYTABLE;

/** Canonical V2 buy / base modes from skyjump_v2_config.json (promoted in Phase 7C.4). */
export type V2BuyMode = {
	id: string;
	rgsKey: string;
	label: string;
	playerName?: string;
	costMultiplier: number;
	maxWin: number;
	enabled: boolean;
	type: 'default' | 'buy';
	startsBonusTier?: string;
	rtp?: number;
	title?: string;
	dialog?: string;
	description?: string;
	button?: string;
	betAmountLabel?: string;
	tickerIdle?: string;
	tickerSpin?: string;
};

export const V2_BUY_MODES = ((rawConfig as { buyModes?: Record<string, V2BuyMode> }).buyModes ??
	{}) as Record<string, V2BuyMode>;

export const V2_ENABLED_MODES = Object.values(V2_BUY_MODES).filter((mode) => mode.enabled !== false);
export const V2_ENABLED_BUY_MODES = V2_ENABLED_MODES.filter((mode) => mode.type === 'buy');
export const V2_DEFAULT_BET_MODE =
	V2_ENABLED_MODES.find((mode) => mode.type === 'default') ?? V2_BUY_MODES.BASE;
