/**
 * Phase 8F — real gameplay UI hard-wiring checks (presentation only).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const board = fs.readFileSync(
	path.join(root, 'frontend/apps/poc/src/components/skyjump_v2/SkyJumpV2Board.svelte'),
	'utf8',
);
const layout = fs.readFileSync(
	path.join(root, 'frontend/apps/poc/src/game/skyjump_v2/presentationLayout.ts'),
	'utf8',
);
const betBtn = fs.readFileSync(
	path.join(root, 'frontend/packages/components-ui-pixi/src/components/ButtonBet.svelte'),
	'utf8',
);
const hud = fs.readFileSync(
	path.join(root, 'frontend/packages/components-ui-pixi/src/components/SkyJumpHud.svelte'),
	'utf8',
);
const handlers = fs.readFileSync(
	path.join(root, 'frontend/apps/poc/src/game/bookEventHandlerMap.ts'),
	'utf8',
);
const celebration = fs.readFileSync(
	path.join(root, 'frontend/apps/poc/src/components/skyjump_v2/SkyJumpV2WinCelebration.svelte'),
	'utf8',
);
const game = fs.readFileSync(path.join(root, 'frontend/apps/poc/src/components/Game.svelte'), 'utf8');

const assert = (cond: boolean, msg: string) => {
	if (!cond) {
		console.error(`FAIL ${msg}`);
		process.exit(1);
	}
	console.log(`OK  ${msg}`);
};

assert(board.includes("v2FxAssetUrl('paylineSparkHead')"), 'board wires paylineSparkHead registry URL');
assert(board.includes("v2FxAssetUrl('paylineEndGlint')"), 'board wires paylineEndGlint registry URL');
assert(board.includes('pointAlong'), 'spark uses path progress geometry');
assert(board.includes('sparkPos = pointAlong'), 'spark position updates during draw');
assert(board.includes("playV2AudioHook('PAYLINE_DRAW'"), 'PAYLINE_DRAW on draw start');
assert(board.includes("playV2AudioHook('PAYLINE_COMPLETE'"), 'PAYLINE_COMPLETE at endpoint');
assert(board.includes('data-test="skyjump-v2-payline-spark"'), 'spark has live DOM test hook');
assert(board.includes('data-test="skyjump-v2-payline-glint"'), 'glint has live DOM test hook');
assert(/z-index:\s*12/.test(board) || board.includes('z-index: 12'), 'payline SVG above tiles');
assert(board.includes('lineDrawMs > 0'), 'spark enabled for any progressive draw (incl. turbo)');
assert(board.includes('SkyJumpV2StatusPlate'), 'status plate mounted in production board');
assert(board.includes('SkyJumpV2WinCelebration'), 'win celebration mounted in production board');
assert(board.includes('SkyJumpV2TitleBanner'), 'title banners mounted in production board');
assert(board.includes('skyjumpV2BonusTitles'), 'bonus titles wired to board handler');

assert(layout.includes('sparkPx: 30'), 'spark display size modest vs stroke');
assert(layout.includes('endGlintPx: 36'), 'end glint display size modest vs stroke');

assert(betBtn.includes("'SPIN'"), 'SkyJump SPIN label on primary control');
assert(betBtn.includes("key.startsWith('stop')"), 'STOP state distinct gold styling');
assert(betBtn.includes('SKYJUMP_BETUI_ART.spin'), 'SPIN uses betui art face');
assert(hud.includes('Unified BET cluster'), 'HUD has unified bet cluster plate');
assert(hud.includes('sizes.spin.width'), 'cluster sized from spin control');

assert(handlers.includes("kind: 'fsStart'"), 'FS start emits real bonus title event');
assert(handlers.includes("kind: 'tierUpgrade'") || handlers.includes("'retrigger'"), 'upgrade/retrigger emit banners');
assert(handlers.includes('skyjumpV2Result'), 'settlement broadcasts skyjumpV2Result');
assert(celebration.includes('winGlowRing') || celebration.includes('glowSrc'), 'celebration uses glow FX');
assert(celebration.includes('snowBurst') || celebration.includes('snowSrc'), 'celebration uses snow FX');
assert(celebration.includes('coinSparkle') || celebration.includes('coinSrc'), 'celebration uses coin FX');
assert(celebration.includes('screenFlash') || celebration.includes('flashSrc'), 'celebration uses flash FX');

assert(game.includes('SkyJumpV2Board'), 'Game mounts V2 board');
assert(game.includes('SkyJumpHudFrame'), 'Game mounts HUD frame');
assert(!game.includes('SkyJumpReelStrip'), 'Game does not mount V1 reel strip');

console.log('PASS phase8f real gameplay UI hard-wiring');
