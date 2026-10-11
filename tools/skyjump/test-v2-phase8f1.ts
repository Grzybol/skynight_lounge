/**
 * Phase 8F.1 — hard BET HUD visual redesign structure checks.
 * Visual-only; handlers / math must remain untouched.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const read = (rel: string) => fs.readFileSync(path.join(root, rel), 'utf8');

const hud = read('frontend/packages/components-ui-pixi/src/skyjumpHud.ts');
const art = read('frontend/packages/components-ui-pixi/src/skyjumpBetUiArt.ts');
const skyHud = read('frontend/packages/components-ui-pixi/src/components/SkyJumpHud.svelte');
const betBtn = read('frontend/packages/components-ui-pixi/src/components/ButtonBet.svelte');
const uiBtn = read('frontend/packages/components-ui-pixi/src/components/UiButton.svelte');
const buy = read('frontend/packages/components-ui-pixi/src/components/ButtonBuyBonus.svelte');
const labelBet = read('frontend/packages/components-ui-pixi/src/components/LabelBet.svelte');
const uiLabel = read('frontend/packages/components-ui-pixi/src/components/UiLabel.svelte');
const frame = read('frontend/apps/poc/src/components/skyjump/SkyJumpHudFrame.svelte');
const board = read('frontend/apps/poc/src/components/skyjump_v2/SkyJumpV2Board.svelte');
const pres = read('frontend/apps/poc/src/game/skyjump_v2/presentationLayout.ts');
const game = read('frontend/apps/poc/src/components/Game.svelte');
const provider = read(
	'frontend/packages/components-ui-pixi/src/components/ButtonBetProvider.svelte',
);

const assert = (cond: boolean, msg: string) => {
	if (!cond) {
		console.error(`FAIL ${msg}`);
		process.exit(1);
	}
	console.log(`OK  ${msg}`);
};

// Layout tokens — primary 1280 dock
assert(hud.includes('dockWidth: 1490'), 'desktop dock width 1490 (~993px @1280)');
assert(hud.includes('spin: 157'), 'SPIN face 157 (~+6%)');
assert(hud.includes('spinNudgeY: 18'), 'SPIN lowered ~12px CSS into dock');
assert(hud.includes('buyH: 60'), 'BUY BONUS taller (60)');
assert(hud.includes('leftGroupShiftX: -27'), 'left group shifted ~18px CSS left');
assert(hud.includes('infoCol: 129'), 'left info ~5% smaller');
assert(hud.includes('betValue: 112'), 'left bet value ~5% smaller');
assert(hud.includes('buyModesGap: 15'), 'compact right Buy↔modes gap');
assert(hud.includes('modesMenuGap: 15'), 'compact right modes↔Menu gap');
assert(hud.includes('panelPad: 22'), 'panelPad inside blue art');
assert(hud.includes('chromeInsetX'), 'art chrome inset for crystals');
assert(hud.includes('spinCx = dockX + dockW * 0.5'), 'SPIN anchored at dock center X');
assert(hud.includes('circleMidY'), 'SPIN uses art circle mid Y');
assert(hud.includes('wingMidY'), 'side controls use wing mid Y');
assert(hud.includes('ratio < 1.35 || hud.width < 900'), '1280 not forced into compact');

// Board explicit 1280 px contracts
assert(board.includes('GRID_TOP_Y = 22'), 'grid top sizing pin at 22px @1280');
assert(board.includes('BOARD_NUDGE_DOWN = 26'), 'slot board Y nudge +26px');
assert(board.includes('BOARD_NUDGE_X = 2.25'), 'slot board X nudge +2.25px');
assert(
	board.includes('style:left={`${left + px(BOARD_NUDGE_X)}px`}'),
	'slot stage uses X nudge; summary overlay stays on left',
);
assert(board.includes('BOARD_SCALE = 1.12'), 'slot grid +7% scale');
assert(board.includes('GRID_SUMMARY_GAP = 10'), 'nominal grid→summary gap 10px');
assert(board.includes('SUMMARY_BETUI_OVERLAP = 48'), 'summary overlaps BetUI crest 48px');
assert(board.includes('--summary-gap'), 'summary gap CSS var wired');

// Hierarchy regions in SkyJumpHud
assert(skyHud.includes('Unified BET cluster'), 'unified BET cluster plate');
assert(skyHud.includes('LEFT INFO zone'), 'LEFT INFO zone plate');
assert(skyHud.includes('sizes.spin.width'), 'SPIN sized from layout tokens');
assert(skyHud.includes('sizes.buy'), 'BUY sized from layout');
assert(skyHud.includes('sizes.mode'), 'AUTO sized from mode token');

// SPIN / STOP chrome — art face scaled so circle matches layout diameter
assert(betBtn.includes("'SPIN'"), 'SPIN label');
assert(betBtn.includes("key.startsWith('stop')"), 'STOP state branch');
assert(betBtn.includes('SKYJUMP_BETUI_ART.spin'), 'SPIN uses betui_spin_button art');
assert(betBtn.includes('skyjumpSpinArtSize'), 'SPIN art sized from circle diameter');
assert(art.includes('spin: 1.267875'), 'SPIN face another +5%');
assert(art.includes('buy: 1.26'), 'BUY face another +5%');
assert(art.includes('auto: 1.26'), 'AUTO face another +5%');
assert(art.includes('turboW: 1.2075'), 'TURBO another +5% width');
assert(art.includes('turboH: 1.05'), 'TURBO another +5% height');
assert(art.includes('menu: 1.2285'), 'MENU face another +5%');
assert(art.includes('SKYJUMP_SIDE_NUDGE_Y = 7.5'), 'BUY/AUTO/TURBO/MENU dropped ~5px');
assert(pres.includes('scale: 1,'), 'slot frame sized to the grid hole');
assert(art.includes('SKYJUMP_BUY_NUDGE_X = -19'), 'BUY gap matches auto/turbo/menu');
assert(skyHud.includes('SKYJUMP_INFO_TILE_WIDTH_SCALE'), 'balance tile widened, shifted left');
assert(board.includes('V2_SLOT_BOARD_FRAME.scale'), 'slot frame scaled around the grid');
assert(uiBtn.includes('SKYJUMP_BETUI_ART.plus'), 'BET plus uses betui_btn_plus art');
assert(uiBtn.includes('SKYJUMP_BETUI_ART.minus'), 'BET minus uses betui_btn_minus art');
assert(hud.includes('SKYJUMP_BUY_NUDGE_X'), 'BUY nudge applied in desktop layout');
assert(betBtn.includes('SkyJumpBetUiFace'), 'SPIN renders BetUI face sprite');

// Mode / cluster chrome
assert(uiBtn.includes("icon === 'decrease' || icon === 'increase'"), 'cluster ± without double plate');
assert(uiBtn.includes('SKYJUMP_BETUI_ART.auto'), 'AUTO uses betui_auto_button art');
assert(uiBtn.includes('SKYJUMP_BETUI_ART.turbo'), 'TURBO uses betui_turbo_button art');
assert(uiBtn.includes('SKYJUMP_BETUI_ART.menu'), 'MENU uses betui_menu_button art');
assert(uiBtn.includes('assetKey={artKey}'), 'mode buttons render preloaded Pixi sprite');
assert(uiBtn.includes('autoOn'), 'AUTO active ice tone');
assert(uiBtn.includes('turboOn'), 'TURBO active tone');
assert(buy.includes('SKYJUMP_BETUI_ART.buyBonus'), 'BUY uses betui_buy_bonus_button art');
assert(board.includes('viewport-light-sweep'), 'full-viewport light sweep mounted');
assert(board.includes('skyjump-v2-viewport-sweep'), 'viewport sweep test hook');

// Labels
assert(labelBet.includes("'BET'"), 'compact BET label in cluster');
assert(uiLabel.includes("'SkyjumpUI'"), 'quiet labels use SkyjumpUI');
assert(uiLabel.includes("'SkyjumpDisplay'"), 'values use SkyjumpDisplay');

// Frame dock — viewport-centered art + SPIN seat
assert(frame.includes('data-test="skyjump-hud-frame"'), 'HUD frame mounted hook');
assert(frame.includes('hud-frame-art'), 'HUD frame uses betui art asset');
assert(frame.includes('betHudFrame'), 'HUD frame resolves betHudFrame URL');
assert(frame.includes('translateX(-50%)'), 'HUD frame CSS viewport centering');
assert(hud.includes('SKYJUMP_BET_HUD_FRAME'), 'HUD layout exports bet frame ratios');
assert(game.includes('SkyJumpHudFrame'), 'production Game mounts HUD frame');

// Handler regression anchors (must not regress STOP / autoplay)
assert(
	provider.includes('if (stateBetDerived.hasAutoBetCounter()) stateBet.autoSpinsCounter = 0'),
	'STOP clears autoplay counter',
);
assert(provider.includes('if (stateBet.overlayOpen) return'), 'STOP still respects overlay after cancel');
assert(buy.includes("stateModal.modal = { name: 'buyBonus' }"), 'BUY opens buyBonus modal');
assert(!hud.includes('mathVersion'), 'layout file does not touch mathVersion');

assert(betBtn.includes('SKYJUMP_BETUI_ART.stop'), 'STOP uses betui_stop_button art');
assert(art.includes("stop: 'betuiStop'"), 'stop art key registered');
assert(uiBtn.includes('skyjumpFlyoutArtKey'), 'menu flyout faces use betui art');
assert(!skyHud.includes('buttonLanguage'), 'language button is hidden; English only');
assert(!skyHud.includes('SkyJumpLanguageMenu'), 'language submenu is not mounted');
assert(!hud.includes("'language'"), 'menu flyout has no language slot');
assert(art.includes("settings: 'betuiSettings'"), 'settings art key registered');
assert(
	hud.includes('layout.auto.x - layout.sizes.mode.width * 0.5'),
	'flyout starts at the auto button left edge',
);
assert(uiBtn.includes('drawTurboGlow'), 'turbo glow fades from the center');
assert(uiBtn.includes('centerAlpha = 0.13'), 'turbo glow stays faint');
assert(hud.includes('flyScale = 1.25'), 'menu flyout buttons +25%');
assert(skyHud.includes('flyout.itemSize'), 'flyout faces use the enlarged hit box');

console.log('PASS phase8f1 hard BET HUD redesign structure');
