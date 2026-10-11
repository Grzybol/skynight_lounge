const EMPTY_ASSETS = {
	icon: '',
	dialogImage: '',
	dialogVolatility: '',
	volatility: '',
	button: '',
};

const EMPTY_TEXT = {
	title: '',
	dialog: '',
	button: '',
	betAmountLabel: '',
	tickerIdle: '',
	tickerSpin: '',
	bannerText: '',
};

/** SkyJump-safe placeholders. Garden/Twist/Superante copy must not ship in production. */
const DEFAULT_BET_MODE_META = {
	BASE: {
		mode: 'BASE',
		costMultiplier: 1,
		type: 'default' as const,
		parent: '',
		children: '',
		assets: EMPTY_ASSETS,
		text: EMPTY_TEXT,
		maxWin: 0,
	},
};

const DEFAULT_GAME_RULE_META = {
	payTable: [] as Array<{
		containers: unknown[];
		rows: number;
		columns: number;
		title: string;
	}>,
	gameRules: [] as Array<{
		containers: unknown[];
		rows: number;
		columns: number;
		title: string;
	}>,
	splashScreen: [] as unknown[],
};

export { DEFAULT_BET_MODE_META, DEFAULT_GAME_RULE_META };
