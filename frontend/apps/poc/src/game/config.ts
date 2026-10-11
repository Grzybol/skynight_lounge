import rawConfig from '../../../../../../math/games/0_0_poc/skyjump_config.json' with { type: 'json' };

type BuyMode = {
	id: string;
	rgsKey: string;
	costMultiplier: number;
	type: string;
	maxWin: number;
	enabled?: boolean;
};

const buyModes = Object.fromEntries(
	Object.values(rawConfig.buyModes as Record<string, BuyMode>)
		.filter((mode) => mode.enabled !== false)
		.map((mode) => [
			// Stake HUD / play() use rgsKey (BASE, …). Canonical id stays in JSON (base, …).
			mode.rgsKey,
			{
				cost: mode.costMultiplier,
				feature: mode.type === 'default',
				buyBonus: mode.type === 'buy',
				rtp: rawConfig.meta.targetRtpLabel,
				max_win: mode.maxWin,
			},
		]),
);

const config = {
	// PLACEHOLDER: replace poc_studio / 0 / 0_0_poc when Stake ACP issues production IDs.
	providerName: 'poc_studio',
	gameName: 'skyjump',
	// TODO: replace 0_0_poc with the Stake ACP gameID. See skyjump_config.json meta.gameIdRenameTodo.
	gameID: rawConfig.meta.gameID as string,
	rtp: rawConfig.meta.targetRtpLabel as number,
	// Sequential 6-slot SkyJump strip. Stake FE publisher still emits numReels/numRows.
	numReels: 6,
	numRows: [1, 1, 1, 1, 1, 1],
	betModes,
	// SDK compatibility placeholders — SkyJump does not publish Garden lines or fruit paytables.
	paylines: {} as Record<string, number[]>,
	symbols: {} as Record<string, { paytable?: Array<Record<string, number>> }>,
	paddingReels: {
		basegame: [] as { name: string }[][],
		freegame: [] as { name: string }[][],
	},
};

export default config;
