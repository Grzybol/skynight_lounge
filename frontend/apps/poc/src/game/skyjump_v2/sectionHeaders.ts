/**
 * Image headlines for the Game Info and Paytable sections (lossless PNG, 2172x724 RGBA).
 * Runtime: static/assets/midnight-lounge/ui/headers/hdr_<key>.png
 */
import { resolveGameAsset } from '../resolveGameAsset';

export const SECTION_HEADER_KEYS = [
	'mystery_gift_concierge',
	'paylines_rules',
	'buy_bonus',
	'lounge_dealer_pit_boss',
	'features',
	'bonus_rooms',
	'regular_symbols',
	'lounge_tokens',
	'royal_win',
	'max_win',
	'spotlight_vip_upgrade',
	'payline_inspector',
	'encore',
	'paylines',
	'tokens_collectors_max_win',
] as const;

export type SectionHeaderKey = (typeof SECTION_HEADER_KEYS)[number];

export const sectionHeaderUrl = (key: SectionHeaderKey) =>
	resolveGameAsset(`assets/midnight-lounge/ui/headers/hdr_${key}.png`);

/** Game Info card title -> headline image (cards without one keep their text title). */
export const INFO_SECTION_HEADERS: Record<string, SectionHeaderKey> = {
	Paylines: 'paylines',
	'Free Spins': 'features',
	'Bonus Rooms': 'bonus_rooms',
	'Mystery Gift & Concierge': 'mystery_gift_concierge',
	'Lounge Tokens': 'lounge_tokens',
	'Spotlight & VIP Upgrade': 'spotlight_vip_upgrade',
	'Lounge Dealer & Pit Boss': 'lounge_dealer_pit_boss',
	Encore: 'encore',
	'Royal Win': 'royal_win',
	'Max Win': 'max_win',
	'Buy Bonus': 'buy_bonus',
};
