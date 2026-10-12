/**
 * Canonical V2 symbol → runtime asset registry.
 * Place final PNGs in: frontend/apps/poc/static/assets/skyjump_v2/symbols/
 * Source/master art may live under assets/skyjump_v2/source/ (Filip drop).
 * Runtime resolution prefers PNG when it loads; falls back to CSS placeholders.
 */

import { resolveGameAsset } from '../resolveGameAsset';
import { v2Placeholder } from './placeholders.ts';
import type { V2Placeholder } from './types.ts';

/** Midnight Lounge presentation. Symbol IDs are unchanged. Old ski PNGs stay on disk. */
export const V2_SYMBOL_RUNTIME_DIR = 'assets/midnight-lounge/symbols';
export const V2_SYMBOL_SOURCE_DIR = 'assets/skyjump_v2/source/symbols';

export const V2_SYMBOL_FILENAMES: Record<string, string> = {
	P1: 'sym_p1_champagne.png',
	P2: 'sym_p2_crystal_cocktail.png',
	P3: 'sym_p3_masquerade_mask.png',
	M1: 'sym_m1_red_stiletto.png',
	M2: 'sym_m2_gold_watch.png',
	M3: 'sym_m3_luxury_perfume.png',
	L1: 'sym_l1_velvet_rope.png',
	L2: 'sym_l2_gold_lounge_key.png',
	L3: 'sym_l3_red_rose.png',
	S: 'sym_s_vip_invitation.png',
	C: 'sym_c_concierge_bell.png',
	Y: 'sym_y_mystery_gift.png',
	THERMAL_LIFT: 'sym_feat_golden_spotlight.png',
	THERMAL: 'sym_feat_golden_spotlight.png',
	GATE_UPGRADE: 'sym_feat_vip_upgrade_card.png',
	GATE: 'sym_feat_vip_upgrade_card.png',
	JUDGE: 'sym_feat_lounge_dealer.png',
	HEAD_JUDGE: 'sym_feat_pit_boss.png',
	REJUMP: 'sym_feat_encore.png',
	WIND_KEY: 'sym_feat_black_access_pass.png',
	WIND: 'sym_feat_black_access_pass.png',
	SPECIAL_WORLD_RECORD: 'sym_feat_midnight_crown.png',
	T1: 'sym_token_t1_bronze_guest.png',
	T2: 'sym_token_t2_silver_member.png',
	T3: 'sym_token_t3_gold_vip.png',
	T4: 'sym_token_t4_platinum_elite.png',
	T5: 'sym_token_t5_black_diamond.png',
	T6: 'sym_token_t6_royal_ruby.png',
};

const missingArt = new Set<string>();
const readyArt = new Set<string>();

export const v2SymbolAssetUrl = (symbolId: string): string | null => {
	const file = V2_SYMBOL_FILENAMES[symbolId];
	if (!file) return null;
	return resolveGameAsset(`${V2_SYMBOL_RUNTIME_DIR}/${file}`);
};

/**
 * Display resolution. Always provides a CSS placeholder.
 * `url` is set when a filename is registered; callers must keep the placeholder
 * visible until `markV2SymbolArtReady` (img onload). Missing files stay placeholder.
 */
export const v2SymbolVisual = (
	symbolId: string,
): {
	placeholder: V2Placeholder;
	url: string | null;
	useArt: boolean;
} => {
	const placeholder = v2Placeholder(symbolId);
	const url = missingArt.has(symbolId) ? null : v2SymbolAssetUrl(symbolId);
	return {
		placeholder,
		url,
		useArt: Boolean(url && readyArt.has(symbolId)),
	};
};

export const markV2SymbolArtMissing = (symbolId: string) => {
	missingArt.add(symbolId);
	readyArt.delete(symbolId);
};

export const markV2SymbolArtReady = (symbolId: string) => {
	readyArt.add(symbolId);
	missingArt.delete(symbolId);
};

export const V2_REEL_SYMBOL_IDS = Object.keys(V2_SYMBOL_FILENAMES).filter(
	(id) => !['THERMAL', 'GATE', 'WIND'].includes(id),
);
