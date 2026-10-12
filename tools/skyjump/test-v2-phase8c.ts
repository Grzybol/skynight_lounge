/**
 * Phase 8C.1 — assert 29-asset UI pack is PNG RGBA with alpha (no JPEG runtime).
 */
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const POC = resolve(ROOT, 'frontend/apps/poc');
const STATIC = resolve(POC, 'static/assets/skyjump_v2');
const REGISTRY = resolve(POC, 'src/game/skyjump_v2/uiAssetRegistry.ts');
const WIN_PRES = resolve(POC, 'src/game/skyjump_v2/winPresentation.ts');
const FONTS_CSS = resolve(POC, 'static/assets/fonts/skyjump/skyjump-fonts.css');
const GALLERY = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2AssetGallery.svelte');
const SHOWCASE = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2UiPackShowcase.svelte');
const GAME = resolve(POC, 'src/components/Game.svelte');

const fail = (msg: string): never => {
	console.error(`FAIL: ${msg}`);
	process.exit(1);
};
const ok = (msg: string) => console.log(`OK  ${msg}`);

const EXPECTED_FILES = [
	'ui/wins/ui_win_big.png',
	'ui/wins/ui_win_mega.png',
	'ui/wins/ui_win_super.png',
	'ui/wins/ui_win_max.png',
	'ui/wins/ui_win_world_record.png',
	'ui/bonus/ui_bonus_free_spins.png',
	'ui/bonus/ui_bonus_retrigger.png',
	'ui/bonus/ui_bonus_tier_upgrade.png',
	'ui/bonus/ui_mode_large_hill.png',
	'ui/bonus/ui_mode_ski_flying.png',
	'ui/bonus/ui_mode_world_cup.png',
	'ui/bonus/ui_mode_perfect_v.png',
	'ui/headers/ui_header_paytable.png',
	'ui/headers/ui_header_info.png',
	'ui/headers/ui_header_features.png',
	'ui/headers/ui_header_how_to_play.png',
	'fx/fx_payline_spark_head.png',
	'fx/fx_payline_end_glint.png',
	'fx/fx_ice_glint.png',
	'fx/fx_snow_burst.png',
	'fx/fx_win_glow_ring.png',
	'fx/fx_screen_flash_accent.png',
	'fx/fx_small_sparkle.png',
	'fx/fx_coin_sparkle.png',
	'ui/decor/ui_divider_ice.png',
	'ui/decor/ui_corner_ornament.png',
	'ui/decor/ui_status_plate.png',
	'ui/decor/ui_mode_badge_plate.png',
	'ui/decor/ui_panel_topper.png',
] as const;

if (EXPECTED_FILES.length !== 29) fail(`expected 29 paths, got ${EXPECTED_FILES.length}`);

const missing = EXPECTED_FILES.filter((f) => !existsSync(resolve(STATIC, f)));
if (missing.length) fail(`missing runtime assets:\n  ${missing.join('\n  ')}`);
ok(`phase8c assets present ${EXPECTED_FILES.length}/29`);

for (const f of EXPECTED_FILES) {
	const jpg = resolve(STATIC, f.replace(/\.png$/i, '.jpg'));
	if (existsSync(jpg)) fail(`stale JPEG still present: ${jpg}`);
}
ok('no stale .jpg siblings for pack files');

for (const f of EXPECTED_FILES) {
	const buf = readFileSync(resolve(STATIC, f));
	if (!(buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47)) {
		fail(`${f} is not PNG magic`);
	}
}
ok('all 29 files have PNG magic bytes');

const py = `
from pathlib import Path
from PIL import Image
root = Path(r'''${STATIC.replace(/\\/g, '/')}''')
files = ${JSON.stringify(EXPECTED_FILES)}
bad = []
okn = 0
for f in files:
    im = Image.open(root / f)
    if im.format != 'PNG':
        bad.append(f'{f} format={im.format}')
        continue
    rgba = im.convert('RGBA')
    a = list(rgba.getchannel('A').getdata())
    amin, amax = min(a), max(a)
    if amin > 0 or amax < 1:
        bad.append(f'{f} mode={im.mode} amin={amin} amax={amax}')
    else:
        okn += 1
print(f'PNG_RGBA={okn}')
if bad:
    print('BAD')
    for b in bad: print(b)
    raise SystemExit(1)
print('ALPHA_OK')
`;
const probe = spawnSync('python', ['-c', py], { encoding: 'utf8' });
if (probe.status !== 0) {
	fail(`alpha probe failed:\n${probe.stdout}\n${probe.stderr}`);
}
if (!probe.stdout.includes('ALPHA_OK')) fail(`alpha probe unexpected:\n${probe.stdout}`);
ok(probe.stdout.trim().split('\n').find((l) => l.startsWith('PNG_RGBA=')) ?? 'PNG RGBA ok');

const hashes = new Map<string, string[]>();
for (const f of EXPECTED_FILES) {
	const buf = readFileSync(resolve(STATIC, f));
	const h = createHash('sha256').update(buf).digest('hex');
	const list = hashes.get(h) ?? [];
	list.push(f);
	hashes.set(h, list);
}
const dupes = [...hashes.values()].filter((g) => g.length > 1);
if (dupes.length) fail(`byte-identical phase8c assets: ${dupes.map((g) => g.join(' ≡ ')).join('; ')}`);
ok('no byte-identical duplicates among 29');

const reg = readFileSync(REGISTRY, 'utf8');
for (const needle of [
	'v2FxAssetUrl',
	'v2ModeTitleUrl',
	'V2_WIN_TITLE_URLS',
	'V2_PHASE8C_EXPECTED_KEYS',
	'winWorldRecord',
	'paylineSparkHead',
]) {
	if (!reg.includes(needle)) fail(`registry missing ${needle}`);
}
if (/\.jpg'|\.jpeg'|\.jpg"|\.jpeg"/.test(reg)) fail('registry still references .jpg for UI pack');
ok('uiAssetRegistry is PNG-only for pack paths');

if (/https?:\/\/(?!localhost)/.test(reg)) fail('registry contains remote http URL');
ok('registry has no remote asset URLs');

const wp = readFileSync(WIN_PRES, 'utf8');
for (const needle of [
	'classifyV2WinCelebration',
	'V2_WIN_CELEBRATION_THRESHOLDS',
	'worldRecord',
	'capHit',
	'PRESENTATION-ONLY',
	'iceGlint',
]) {
	if (!wp.includes(needle)) fail(`winPresentation missing ${needle}`);
}
ok('winPresentation authority + iceGlint present');

if (!existsSync(FONTS_CSS)) fail('missing skyjump-fonts.css');
const fontCss = readFileSync(FONTS_CSS, 'utf8');
if (/fonts\.googleapis|typekit\.net|fonts\.gstatic/.test(fontCss)) {
	fail('font CSS references remote hosts');
}
ok('local font CSS has no remote hosts');

const appHtml = readFileSync(resolve(POC, 'src/app.html'), 'utf8');
if (/typekit\.net|fonts\.googleapis/.test(appHtml)) fail('app.html still loads remote fonts');
ok('app.html has no remote font links');

if (!existsSync(GALLERY)) fail('missing asset gallery');
const gallery = readFileSync(GALLERY, 'utf8');
if (!gallery.includes('checker') || !gallery.includes('bg-white') || !gallery.includes('bg-navy')) {
	fail('gallery missing checkerboard/white/navy backgrounds');
}
ok('gallery has transparency backgrounds');

if (!existsSync(SHOWCASE)) fail('missing UI pack showcase');
ok('UI pack showcase component present');

if (existsSync(GAME)) {
	const game = readFileSync(GAME, 'utf8');
	if (game.includes('SkyJumpV2AssetGallery') || game.includes('SkyJumpV2UiPackShowcase')) {
		fail('gallery/showcase imported in production Game tree');
	}
}
ok('asset gallery / showcase not in production Game tree');

const lh = resolve(STATIC, 'ui/ui_tier_large_hill.png');
const sf = resolve(STATIC, 'ui/ui_tier_ski_flying.png');
if (existsSync(lh) && existsSync(sf)) {
	const a = readFileSync(lh);
	const b = readFileSync(sf);
	if (Buffer.compare(a, b) === 0) {
		ok('NOTE art debt: ui_tier_large_hill ≡ ui_tier_ski_flying (STILL PRESENT)');
	} else {
		ok('tier emblems Large Hill ≠ Ski Flying');
	}
}

const celebration = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2WinCelebration.svelte');
if (!existsSync(celebration)) fail('missing SkyJumpV2WinCelebration.svelte');
if (!readFileSync(celebration, 'utf8').includes('iceGlintSrc')) {
	fail('celebration missing ice glint wiring');
}
ok('win celebration includes ice glint');

const board = readFileSync(resolve(POC, 'src/components/skyjump_v2/SkyJumpV2Board.svelte'), 'utf8');
for (const needle of [
	'SkyJumpV2WinCelebration',
	'SkyJumpV2StatusPlate',
	'SkyJumpV2ModeBadge',
	'SkyJumpV2TitleBanner',
	'paylineSparkSrc',
	'paylineGlintSrc',
	'skyjumpV2BonusTitles',
]) {
	if (!board.includes(needle)) fail(`board missing consumer ${needle}`);
}
ok('board wires celebration / plates / banners / payline FX');

console.log('PASS phase8c.1 UI pack alpha + wiring checks');
