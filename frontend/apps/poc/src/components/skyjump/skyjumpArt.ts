export const weatherIconSrc: Record<string, string> = {
	sunny: new URL('../../assets/skyjump/weather/sunny.svg', import.meta.url).href,
	lightFavorableWind: new URL(
		'../../assets/skyjump/weather/lightFavorableWind.svg',
		import.meta.url,
	).href,
	snow: new URL('../../assets/skyjump/weather/snow.svg', import.meta.url).href,
	headwindLift: new URL('../../assets/skyjump/weather/headwindLift.svg', import.meta.url).href,
	crosswind: new URL('../../assets/skyjump/weather/crosswind.svg', import.meta.url).href,
	storm: new URL('../../assets/skyjump/weather/storm.svg', import.meta.url).href,
};

export const roleIconSrc: Record<string, string> = {
	speed: new URL('../../assets/skyjump/reel-icons/speed.svg', import.meta.url).href,
	takeoff: new URL('../../assets/skyjump/reel-icons/takeoff.svg', import.meta.url).href,
	flight: new URL('../../assets/skyjump/reel-icons/flight.svg', import.meta.url).href,
	wind: new URL('../../assets/skyjump/reel-icons/wind.svg', import.meta.url).href,
	landing: new URL('../../assets/skyjump/reel-icons/landing.svg', import.meta.url).href,
	multiplier: new URL('../../assets/skyjump/reel-icons/multiplier.svg', import.meta.url).href,
	cash: new URL('../../assets/skyjump/reel-icons/cash.svg', import.meta.url).href,
};

export const jumperFlightSrc = new URL('../../assets/skyjump/jumper/flight.png', import.meta.url)
	.href;
export const jumperFlightWinSrc = new URL(
	'../../assets/skyjump/jumper/flight-win.png',
	import.meta.url,
).href;
export const jumperMenuSrc = new URL(
	'../../assets/skyjump/jumper/menu-foreground.webp',
	import.meta.url,
).href;
export const jumperInrunSrc = new URL('../../assets/skyjump/jumper/inrun.webp', import.meta.url)
	.href;
export const menuBgSrc = new URL('../../assets/skyjump/backgrounds/menu.webp', import.meta.url)
	.href;
export const playBgSrc = new URL(
	'../../assets/skyjump/backgrounds/lounge-bg.png',
	import.meta.url,
).href;

/** Transparent bar overlay (1672x941 canvas), drawn in front of the bartender. */
export const loungeBarSrc = new URL(
	'../../assets/skyjump/backgrounds/lounge-bar.png',
	import.meta.url,
).href;

export const resultArtSrc = {
	normal: new URL('../../assets/skyjump/result/normal-win.webp', import.meta.url).href,
	big: new URL('../../assets/skyjump/result/big-win.webp', import.meta.url).href,
	mega: new URL('../../assets/skyjump/result/mega-win.webp', import.meta.url).href,
	tooShort: new URL('../../assets/skyjump/result/too-short.webp', import.meta.url).href,
} as const;

export type ResultArtTier = keyof typeof resultArtSrc;

export const resultArtTier = (result: {
	isPayHit?: boolean;
	isProfit?: boolean;
	amount?: number;
	finalMultiplier?: number;
	returnMultiplier?: number;
}): ResultArtTier => {
	if (!result.isPayHit || (result.amount ?? 0) <= 0) return 'tooShort';
	const punch = Math.max(result.finalMultiplier ?? 0, result.returnMultiplier ?? 0);
	if (result.isProfit && punch >= 20) return 'mega';
	if (result.isProfit && punch >= 5) return 'big';
	return 'normal';
};
