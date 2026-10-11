/**
 * Assert final V2 visual pack is present under static/ (25/25 reel symbols).
 */
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const POC = resolve(ROOT, 'frontend/apps/poc');
const SYM = resolve(POC, 'static/assets/skyjump_v2/symbols');
const UI = resolve(POC, 'static/assets/skyjump_v2/ui');
const OV = resolve(POC, 'static/assets/skyjump_v2/overlays');
const CFG = resolve(ROOT, 'math/games/0_0_poc/skyjump_v2_config.json');

const fail = (msg: string): never => {
	console.error(`FAIL: ${msg}`);
	process.exit(1);
};
const ok = (msg: string) => console.log(`OK  ${msg}`);

const SYMBOLS = [
	'sym_p1_flying_jumper.png',
	'sym_p2_crystal_trophy.png',
	'sym_p3_golden_helmet.png',
	'sym_m1_jumping_skis.png',
	'sym_m2_flight_goggles.png',
	'sym_m3_ski_boots.png',
	'sym_l1_wind_sock.png',
	'sym_l2_snow_badge.png',
	'sym_l3_start_flag.png',
	'sym_s_competition_bib.png',
	'sym_c_coach_signal.png',
	'sym_y_snowburst_mystery.png',
	'sym_feat_thermal_lift.png',
	'sym_feat_gate_upgrade.png',
	'sym_feat_judge.png',
	'sym_feat_head_judge.png',
	'sym_feat_rejump.png',
	'sym_feat_wind_key.png',
	'sym_feat_special_world_record.png',
	'sym_token_t1_rookie.png',
	'sym_token_t2_k_point.png',
	'sym_token_t3_large_hill.png',
	'sym_token_t4_ski_flying.png',
	'sym_token_t5_world_cup.png',
	'sym_token_t6_token_world_record.png',
];

const UI_FILES = [
	'ui_logo_skyjump.png',
	'ui_stage_run_up.png',
	'ui_stage_takeoff.png',
	'ui_stage_flight.png',
	'ui_tier_large_hill.png',
	'ui_tier_ski_flying.png',
	'ui_tier_world_cup.png',
	'ui_tier_perfect_v.png',
];

const missingSym = SYMBOLS.filter((f) => !existsSync(resolve(SYM, f)));
if (missingSym.length) fail(`missing symbols: ${missingSym.join(', ')}`);
ok(`symbols present ${SYMBOLS.length}/${SYMBOLS.length}`);

const missingUi = UI_FILES.filter((f) => !existsSync(resolve(UI, f)));
if (missingUi.length) fail(`missing UI: ${missingUi.join(', ')}`);
ok(`UI art ${UI_FILES.length}/${UI_FILES.length}`);

if (!existsSync(resolve(OV, 'ui_overlay_world_record.png'))) fail('missing WR overlay');
ok('WR overlay present');

const t6 = readFileSync(resolve(SYM, 'sym_token_t6_token_world_record.png'));
const wr = readFileSync(resolve(SYM, 'sym_feat_special_world_record.png'));
if (Buffer.compare(t6, wr) === 0) fail('T6 and SPECIAL_WR are identical bytes');
ok('T6 ≠ SPECIAL_WR');

const judge = readFileSync(resolve(SYM, 'sym_feat_judge.png'));
const head = readFileSync(resolve(SYM, 'sym_feat_head_judge.png'));
if (Buffer.compare(judge, head) === 0) fail('JUDGE and HEAD_JUDGE are identical bytes');
ok('JUDGE ≠ HEAD_JUDGE');

const lh = readFileSync(resolve(UI, 'ui_tier_large_hill.png'));
const sf = readFileSync(resolve(UI, 'ui_tier_ski_flying.png'));
if (Buffer.compare(lh, sf) === 0) {
	const h = createHash('sha256').update(lh).digest('hex');
	console.warn(
		`WARN: ui_tier_large_hill.png and ui_tier_ski_flying.png are byte-identical (${h}) — Filip replace needed`,
	);
} else {
	ok('Large Hill ≠ Ski Flying emblems');
}

const reg = readFileSync(resolve(POC, 'src/game/skyjump_v2/symbolAssetRegistry.ts'), 'utf8');
if (!reg.includes("HEAD_JUDGE: 'sym_feat_head_judge.png'")) fail('HEAD_JUDGE registry missing');
if (!reg.includes("T6: 'sym_token_t6_token_world_record.png'")) fail('T6 registry missing');
if (!reg.includes("SPECIAL_WORLD_RECORD: 'sym_feat_special_world_record.png'")) fail('SPECIAL_WR registry missing');
ok('symbolAssetRegistry keys locked');

const uiReg = readFileSync(resolve(POC, 'src/game/skyjump_v2/uiAssetRegistry.ts'), 'utf8');
if (!uiReg.includes('/assets/skyjump_v2/ui')) fail('ui registry path');
if (!uiReg.includes('/assets/skyjump_v2/overlays')) fail('overlay registry path');
ok('uiAssetRegistry paths locked');

const pngs = readdirSync(SYM).filter((n) => n.endsWith('.png'));
for (const name of pngs) {
	const buf = readFileSync(resolve(SYM, name));
	if (buf[0] !== 0x89 || buf[1] !== 0x50) fail(`${name} is not PNG`);
}
ok(`${pngs.length} symbol files are PNG`);

const sha = createHash('sha256').update(readFileSync(CFG)).digest('hex');
ok(`math config sha256 ${sha.slice(0, 16)}… (visual-only task)`);

console.log('\nV2 visual pack smoke: PASS');
