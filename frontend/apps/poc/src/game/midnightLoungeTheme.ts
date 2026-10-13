/**
 * Midnight Lounge presentation index.
 *
 * Paths stay where SkyJump already loads them. This file is the drop-in list
 * for the next art pass. Entries in WAITING_FOR_REPLACEMENT must keep their
 * current file or the screen breaks. Do not retarget math, event, or RGS ids.
 *
 * `shown` is the old ski label. `lounge` is what the player sees.
 */
import { v2UiAssetUrl } from './skyjump_v2/uiAssetRegistry';
import { resolveGameAsset } from './resolveGameAsset';

export const TBD_MIDNIGHT_LOUNGE_LABEL = 'TBD_MIDNIGHT_LOUNGE_LABEL';

export const loungeLogoSrc = v2UiAssetUrl('logo');
export const loungeSlotFrameSrc = resolveGameAsset('assets/midnight-lounge/scene/slot_background_1.png');
export const loungeSlotBackSrc = resolveGameAsset('assets/midnight-lounge/scene/slot_background_2.png');

/** Internal id → ski label and the Midnight Lounge label on screen. */
export const LOUNGE_PRESENTATION = {
	BASE: { shown: 'BASE', lounge: 'MAIN LOUNGE' },
	LARGE_HILL: { shown: 'LARGE HILL', lounge: 'VELVET ROOM' },
	SKI_FLYING: { shown: 'SKI FLYING', lounge: 'GOLD ROOM' },
	WORLD_CUP: { shown: 'WORLD CUP', lounge: 'DIAMOND LOUNGE' },
	PERFECT_V: { shown: 'PERFECT V', lounge: 'MIDNIGHT SUITE' },
	RUN_UP: { shown: 'RUN-UP', lounge: 'ARRIVAL' },
	TAKEOFF: { shown: 'TAKEOFF', lounge: 'VIP ENTRY' },
	FLIGHT: { shown: 'FLIGHT', lounge: 'INNER LOUNGE' },
	WORLD_RECORD: { shown: 'WORLD RECORD', lounge: 'ROYAL WIN' },
} as const;

/** Player names for reel art. Ids stay the math symbols. */
export const LOUNGE_SYMBOL_NAMES: Record<string, string> = {
	P1: 'Champagne',
	P2: 'Crystal Cocktail',
	P3: 'Masquerade Mask',
	M1: 'Red Stiletto',
	M2: 'Gold Watch',
	M3: 'Luxury Perfume',
	L1: 'Velvet Rope',
	L2: 'Gold Lounge Key',
	L3: 'Red Rose',
	S: 'VIP Invitation',
	C: 'Concierge Bell',
	Y: 'Mystery Gift',
	THERMAL_LIFT: 'Golden Spotlight',
	GATE_UPGRADE: 'VIP Upgrade',
	JUDGE: 'Lounge Dealer',
	HEAD_JUDGE: 'Pit Boss',
	REJUMP: 'Encore',
	WIND_KEY: 'Black Access Pass',
	SPECIAL_WORLD_RECORD: 'Midnight Crown',
	T1: 'Bronze Guest',
	T2: 'Silver Member',
	T3: 'Gold VIP',
	T4: 'Platinum Elite',
	T5: 'Black Diamond',
	T6: 'Royal Ruby',
};

const SKI_DISPLAY_SWAPS: ReadonlyArray<readonly [string, string]> = [
	['Ski Flying Hill', 'GOLD ROOM'],
	['Ski Flying', 'GOLD ROOM'],
	['Normal Hill', 'MAIN LOUNGE'],
	['Large Hill', 'VELVET ROOM'],
	['World Cup', 'DIAMOND LOUNGE'],
	['Perfect V', 'MIDNIGHT SUITE'],
	['WORLD RECORD', 'ROYAL WIN'],
	['World Record', 'ROYAL WIN'],
];

export const loungeShown = (id: string, fallback = '') => {
	const row = (LOUNGE_PRESENTATION as Record<string, { shown: string; lounge: string }>)[id];
	if (!row) return fallback;
	return row.lounge === TBD_MIDNIGHT_LOUNGE_LABEL ? row.shown : row.lounge;
};

/** Swap ski display words. Does not touch math JSON. */
export const loungePhrase = (text: string) => {
	let out = text;
	for (const [from, to] of SKI_DISPLAY_SWAPS) out = out.replaceAll(from, to);
	if (out === 'Base') return 'MAIN LOUNGE';
	return out;
};

export const loungeSymbolName = (id: string, fallback = '') =>
	LOUNGE_SYMBOL_NAMES[id] ?? (fallback ? loungePhrase(fallback) : fallback);

/**
 * Characters are spritesheet packs, not single files: see
 * `game/loungeCharacters/config.ts` and docs/midnight-lounge-character-animation.md.
 */
export const LOUNGE_CHARACTER_FILES = {
	packs: 'static/assets/midnight-lounge/characters/*.pack',
	manifest: 'static/assets/midnight-lounge/characters/manifest.json',
	scene: 'static/assets/midnight-lounge/scene/*.png',
} as const;

export const WAITING_FOR_REPLACEMENT = [
	'fonts SkyjumpDisplay / SkyjumpUI',
	'bet UI C05–C15',
	'fx D16–D21',
	'modal headers E01–E09',
] as const;
