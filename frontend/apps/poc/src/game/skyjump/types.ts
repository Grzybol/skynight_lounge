export type Rarity = 'common' | 'uncommon' | 'rare' | 'epic';

export type WeatherId =
	| 'sunny'
	| 'lightFavorableWind'
	| 'snow'
	| 'headwindLift'
	| 'crosswind'
	| 'storm';

export type SlotRoleId = 'speed' | 'takeoff' | 'flight' | 'wind' | 'landing' | 'multiplier';

export type HillId = 'normal' | 'large' | 'flying';

export type MultiplierTableId = 'standard' | 'plus' | 'max';

export type BetModeKey = 'BASE' | 'LARGE_HILL' | 'SKI_FLYING' | 'MULT_10_100' | 'MULT_20_200';

export type SlotSymbol = {
	id: string;
	label: string;
	weight: number;
	distanceValue: number;
	localMultiplier: number;
	rarity: Rarity;
	bonusFlag: boolean;
	artKey: string;
};

export type WeatherConfig = {
	id: WeatherId;
	label: string;
	weight: number;
	distanceDelta: number;
	volatilityBias: number;
	temperatureRange: [number, number];
	windSpeedRange: [number, number];
	windDirection: string;
	visibilityRange: [number, number];
	iconKey: string;
};

export type WeatherRoll = WeatherConfig & {
	temperatureC: number;
	windSpeedMs: number;
	visibilityPct: number;
};

export type PayoutBand = {
	minDistance: number;
	maxDistance: number;
	baseWinX: number;
};

export type HillConfig = {
	id: HillId;
	label: string;
	buyCost: number;
	baseDistance: number;
	maxWin: number;
	visualKey: string;
	payoutCurve: PayoutBand[];
	volatilityProfile: number;
};

export type MultiplierOutcome = {
	id: string;
	label: string;
	weight: number;
	multiplier: number;
};

export type SlotRole = {
	id: SlotRoleId;
	index: number;
	label: string;
	shortLabel: string;
	iconKey: string;
	symbols: SlotSymbol[];
};

export type TimingProfileId = 'normal' | 'turbo';

export type TimingProfile = {
	id: TimingProfileId;
	weatherCycleMs: number;
	weatherHoldMs: number;
	weatherStatsMs: number;
	reelSpinMs: number;
	reelStopMs: number;
	reelGapMs: number;
	takeoffMs: number;
	overlayIntroMs: number;
	countUpFastMs: number;
	countUpSlowMs: number;
	baseTermMs: number;
	baseCountMs: number;
	localMultHoldMs: number;
	finalMultHoldMs: number;
	finalWinHoldMs: number;
};

export type SlotRoll = SlotSymbol & {
	roleId: SlotRoleId;
	reelIndex: number;
};

export type SkyJumpRound = {
	bet: number;
	hillId: HillId;
	multiplierTableId: MultiplierTableId;
	weather: WeatherRoll;
	slots: SlotRoll[];
	finalMultiplier: MultiplierOutcome;
	distanceTotal: number;
	baseWinX: number;
	localMultiplier: number;
	localFactors: number[];
	finalWinX: number;
	capped: boolean;
	isCapped: boolean;
	maxWin: number;
	/** Debug/presentation only. Settlement uses book `amount`. */
	moneyWin: number;
	costMultiplier: number;
};

export type RoundResolveInput = {
	bet: number;
	hillId: HillId;
	multiplierTableId: MultiplierTableId;
	maxWin?: number;
	costMultiplier?: number;
	random?: () => number;
};

export type DrawnRoundInput = {
	bet: number;
	hillId: HillId;
	multiplierTableId: MultiplierTableId;
	maxWin?: number;
	costMultiplier?: number;
	weatherId: WeatherId;
	temperatureC: number;
	windSpeedMs: number;
	visibilityPct: number;
	slotIds: string[];
	finalMultiplierId: string;
};
