/**
 * Checks the Stake upload directory, not the Vite dev server.
 * Usage: node tools/verify-midnight-lounge-assets.mjs
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const upload = resolve(repo, 'stake-upload/frontend');

const required = [
	'index.html',
	'assets/midnight-lounge/symbols/sym_p1_champagne.png',
	'assets/midnight-lounge/symbols_blur/sym_p1_champagne.webp',
	'assets/midnight-lounge/symbols_blur/sym_token_t6_royal_ruby.webp',
	'assets/midnight-lounge/symbols/sym_p2_crystal_cocktail.png',
	'assets/midnight-lounge/symbols/sym_p3_masquerade_mask.png',
	'assets/midnight-lounge/symbols/sym_m1_red_stiletto.png',
	'assets/midnight-lounge/symbols/sym_m2_gold_watch.png',
	'assets/midnight-lounge/symbols/sym_m3_luxury_perfume.png',
	'assets/midnight-lounge/symbols/sym_l1_velvet_rope.png',
	'assets/midnight-lounge/symbols/sym_l2_gold_lounge_key.png',
	'assets/midnight-lounge/symbols/sym_l3_red_rose.png',
	'assets/midnight-lounge/symbols/sym_s_vip_invitation.png',
	'assets/midnight-lounge/symbols/sym_c_concierge_bell.png',
	'assets/midnight-lounge/symbols/sym_y_mystery_gift.png',
	'assets/midnight-lounge/symbols/sym_feat_golden_spotlight.png',
	'assets/midnight-lounge/symbols/sym_feat_vip_upgrade_card.png',
	'assets/midnight-lounge/symbols/sym_feat_lounge_dealer.png',
	'assets/midnight-lounge/symbols/sym_feat_pit_boss.png',
	'assets/midnight-lounge/symbols/sym_feat_encore.png',
	'assets/midnight-lounge/symbols/sym_feat_black_access_pass.png',
	'assets/midnight-lounge/symbols/sym_feat_midnight_crown.png',
	'assets/midnight-lounge/symbols/sym_token_t1_bronze_guest.png',
	'assets/midnight-lounge/symbols/sym_token_t2_silver_member.png',
	'assets/midnight-lounge/symbols/sym_token_t3_gold_vip.png',
	'assets/midnight-lounge/symbols/sym_token_t4_platinum_elite.png',
	'assets/midnight-lounge/symbols/sym_token_t5_black_diamond.png',
	'assets/midnight-lounge/symbols/sym_token_t6_royal_ruby.png',
	'assets/midnight-lounge/ui/ui_logo_midnight_lounge.png',
	'assets/midnight-lounge/ui/start_screen.png',
	'assets/midnight-lounge/scene/background_1.png',
	'assets/midnight-lounge/scene/background_2_static.png',
	'assets/midnight-lounge/scene/background_3_static.png',
	'assets/midnight-lounge/scene/clouds_prop.png',
	'assets/midnight-lounge/scene/slot_background_1.png',
	'assets/midnight-lounge/scene/slot_tablet.png',
	'assets/midnight-lounge/scene/slot_tablet_wind_mask.png',
	'assets/midnight-lounge/scene/slot_column_1.png',
	'assets/midnight-lounge/scene/slot_column_2.png',
	'assets/midnight-lounge/scene/slot_column_3.png',
	'assets/midnight-lounge/scene/slot_column_4.png',
	'assets/midnight-lounge/scene/slot_column_wind_mask.png',
	'assets/midnight-lounge/scene/slot_frame_wind_mask.png',
	...['low', 'medium', 'premium', 'scatter', 'concierge_mystery', 'feature'].flatMap((tier) => [
		`assets/midnight-lounge/tiles/tile_${tier}.png`,
		`assets/midnight-lounge/tiles_blur/tile_${tier}.webp`,
	]),
	...Array.from({ length: 13 }, (_, i) => `assets/midnight-lounge/scene/background_2_static_frame_${i + 2}.png`),
	'assets/midnight-lounge/ui/intro_stanchion.png',
	'assets/midnight-lounge/ui/start_loading.png',
	'assets/midnight-lounge/ui/betui2/spin.png',
	'assets/midnight-lounge/ui/betui2/stop.png',
	'assets/fonts/skyjump/luckiest-guy-400.ttf',
	'assets/midnight-lounge/ui/headers/hdr_mystery_gift_concierge.png',
	'assets/midnight-lounge/ui/headers/hdr_paylines_rules.png',
	'assets/midnight-lounge/ui/headers/hdr_buy_bonus.png',
	'assets/midnight-lounge/ui/headers/hdr_lounge_dealer_pit_boss.png',
	'assets/midnight-lounge/ui/headers/hdr_features.png',
	'assets/midnight-lounge/ui/headers/hdr_bonus_rooms.png',
	'assets/midnight-lounge/ui/headers/hdr_regular_symbols.png',
	'assets/midnight-lounge/ui/headers/hdr_lounge_tokens.png',
	'assets/midnight-lounge/ui/headers/hdr_royal_win.png',
	'assets/midnight-lounge/ui/headers/hdr_max_win.png',
	'assets/midnight-lounge/ui/headers/hdr_spotlight_vip_upgrade.png',
	'assets/midnight-lounge/ui/headers/hdr_payline_inspector.png',
	'assets/midnight-lounge/ui/headers/hdr_encore.png',
	'assets/midnight-lounge/ui/headers/hdr_paylines.png',
	'assets/midnight-lounge/ui/headers/hdr_tokens_collectors_max_win.png',
	'assets/audio/skyjump/sfx/v2/sfx_win_mini.mp3',
	'assets/midnight-lounge/audio/sfx_win_background_sound.mp3',
	'assets/midnight-lounge/audio/slot_new_row.mp3',
	'assets/midnight-lounge/audio/win_coin_spawn.mp3',
	'assets/midnight-lounge/audio/win_coin_escape.mp3',
	'assets/midnight-lounge/fx/win_coin_atlas.png',
	'assets/midnight-lounge/ui/ui_buy_bonus_badge.png',
	'assets/midnight-lounge/ui/decor/ui_slot_board_frame_midnight_lounge.png',
	'assets/midnight-lounge/ui/wins/ui_win_big_midnight_lounge.png',
	'assets/midnight-lounge/ui/wins/ui_win_mega_midnight_lounge.png',
	'assets/midnight-lounge/ui/bonus/ui_mode_velvet_room.png',
	'assets/midnight-lounge/overlays/ui_overlay_win_soft_midnight_lounge.png',
	'assets/midnight-lounge/overlays/ui_overlay_win_grand_midnight_lounge.png',
	'assets/midnight-lounge/overlays/ui_overlay_royal_midnight_lounge.png',
	'assets/midnight-lounge/fx/fx_glint_ruby_gold.png',
	'assets/midnight-lounge/fx/fx_luxury_burst_gold.png',
	'assets/midnight-lounge/audio/sfx_scatter_land.mp3',
	'assets/midnight-lounge/audio/sfx_token_reveal.mp3',
	'assets/skyjump_v2/ui/headers/ui_header_paytable.png',
	'assets/skyjump_v2/ui/headers/ui_header_info.png',
	'assets/skyjump_v2/ui/headers/ui_header_features.png',
	'assets/skyjump_v2/ui/headers/ui_header_how_to_play.png',
	'assets/audio/skyjump/bgm/relaxed_background_music1.mp3',
	'assets/audio/skyjump/bgm/relaxed_background_music2.mp3',
	'assets/audio/skyjump/bgm/tracks.json',
	'assets/fonts/skyjump/skyjump-fonts.css',
	'assets/fonts/skyjump/oxanium-600.woff2',
	'assets/fonts/skyjump/inter-400.woff2',
	// Character animation packs (tools/midnight-lounge/build-character-anims.py).
	'assets/midnight-lounge/characters/manifest.json',
	...[
		'woman_idle',
		'woman_idle_alt',
		'woman_idle_1',
		'woman_idle_2',
		'woman_idle_3',
		'woman_idle_4',
		'woman_mini_win',
		'bartender_idle',
		'bartender_idle_1',
		'bartender_mini_win',
		'plant_loop',
		'guard_loop',
	].map((id) => `assets/midnight-lounge/characters/${id}.pack`),
];

const walk = (dir, rel = '') => {
	const found = [];
	for (const name of readdirSync(dir)) {
		const nextRel = rel ? `${rel}/${name}` : name;
		const full = join(dir, name);
		if (statSync(full).isDirectory()) found.push(...walk(full, nextRel));
		else found.push(nextRel.replaceAll('\\', '/'));
	}
	return found;
};

if (!existsSync(upload)) {
	console.error('missing', upload);
	process.exit(1);
}

const files = new Set(walk(upload));
const failures = [];

for (const rel of required) {
	if (files.has(rel)) continue;
	const folded = [...files].find((file) => file.toLowerCase() === rel.toLowerCase());
	if (folded) failures.push(`CASE ${rel} stored as ${folded}`);
	else failures.push(`MISSING ${rel}`);
}

// Every pack must be exactly the size the manifest says (truncated upload = broken clip).
const manifestPath = join(upload, 'assets/midnight-lounge/characters/manifest.json');
if (existsSync(manifestPath)) {
	const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
	for (const [id, entry] of Object.entries(manifest.animations)) {
		// Big packs are stored in parts that concatenate into the pack (manifest `parts`).
		const files = entry.parts ?? [{ file: entry.file, bytes: entry.bytes }];
		let total = 0;
		for (const part of files) {
			const partPath = join(upload, 'assets/midnight-lounge/characters', part.file);
			if (!existsSync(partPath)) {
				failures.push(`MISSING pack file ${part.file} for ${id}`);
				continue;
			}
			const size = statSync(partPath).size;
			total += size;
			if (size !== part.bytes) failures.push(`SIZE pack file ${part.file} != manifest`);
		}
		if (total !== entry.bytes) failures.push(`SIZE pack ${id} parts != manifest`);
	}
}

const html = readFileSync(join(upload, 'index.html'), 'utf8');
if (/href="\/assets|src="\/assets|url\((['"])\/assets/.test(html)) {
	failures.push('index.html still contains a root-absolute /assets URL');
}
if (!html.includes('./_app/') && !html.includes('_app/immutable/')) {
	failures.push('index.html does not reference the _app bundle');
}

const bundles = [...files].filter((file) => /_app\/immutable\/bundle\.[^/]+\.js$/.test(file));
if (!bundles.length) failures.push('MISSING _app/immutable/bundle.*.js');
for (const bundle of bundles) {
	const source = readFileSync(join(upload, bundle), 'utf8');
	if (/src:\s*["']\/assets\/|url\(\s*["']?\/assets\//.test(source)) {
		failures.push(`${bundle} stores a root-absolute /assets runtime path`);
	}
}

if (failures.length) {
	console.error(`verify-midnight-lounge-assets: FAIL (${failures.length})`);
	for (const failure of failures) console.error(' -', failure);
	process.exit(1);
}

console.log(`verify-midnight-lounge-assets: PASS (${required.length} static + character media)`);
