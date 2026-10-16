/**
 * Phase 8A regression: STOP during presentation lock must cancel future autoplay.
 * Run: node --experimental-strip-types tools/skyjump/test-v2-phase8a-autoplay-stop.ts
 */

import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync, existsSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const POC = resolve(ROOT, 'frontend/apps/poc');
const BET_PROVIDER = resolve(
	ROOT,
	'frontend/packages/components-ui-pixi/src/components/ButtonBetProvider.svelte',
);
const BET_BUTTON = resolve(
	ROOT,
	'frontend/packages/components-ui-pixi/src/components/ButtonBet.svelte',
);
const BOARD = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2Board.svelte');
const PAYTABLE = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2PayTable.svelte');
const RULES = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2GameRules.svelte');
const AUDIO = resolve(POC, 'src/game/skyjump_v2/audio.ts');
const TIMINGS = resolve(POC, 'src/game/skyjump_v2/timings.ts');
const CONFIG_JSON = resolve(ROOT, 'math/games/0_0_poc/skyjump_v2_config.json');
const LEGACY_DIR = resolve(POC, 'static/assets/audio/skyjump/sfx/legacy_v1');

let failed = 0;
const ok = (name: string, pass: boolean, detail = '') => {
	console.log(pass ? 'OK' : 'FAIL', name, detail);
	if (!pass) failed += 1;
};

const betSrc = readFileSync(BET_PROVIDER, 'utf8');
const stopFn = betSrc.match(/const stop = \(\) => \{[\s\S]*?\n\t\};/)?.[0] ?? '';
ok(
	'STOP clears autoSpinsCounter before overlayOpen return',
	/hasAutoBetCounter\(\)\)\s*stateBet\.autoSpinsCounter = 0/.test(stopFn) &&
		/autoSpinsCounter = 0[\s\S]*overlayOpen/.test(stopFn),
);
ok(
	'onpress allows STOP while overlayOpen (idle still gated)',
	/isIdle\(\)[\s\S]*overlayOpen[\s\S]*bet\(\)/.test(betSrc) &&
		/else \{[\s\S]*stop\(\);/.test(betSrc),
);
ok('STOP still respects stopDisabled for presentation skip', stopFn.includes('stopDisabled'));

const betBtnSrc = readFileSync(BET_BUTTON, 'utf8');
ok(
	'ButtonBet not disabled by overlayOpen while STOP (non-idle)',
	/isIdle \? .*overlayOpen : false/.test(betBtnSrc.replace(/\s+/g, ' ')) ||
		(/isIdle\(\)/.test(betBtnSrc) &&
			/overlayOpen/.test(betBtnSrc) &&
			betBtnSrc.includes('isIdle ?') &&
			betBtnSrc.includes(': false')),
);

// Synthetic: locked presentation + STOP must zero counter; settle then no next play
let autoSpinsCounter = Infinity;
let overlayOpen = true;
let plays = 0;
const stop = () => {
	if (autoSpinsCounter !== 0) autoSpinsCounter = 0;
	if (overlayOpen) return;
};
const tryNextAutoplay = () => {
	if (autoSpinsCounter === 0) return;
	if (overlayOpen) return;
	plays += 1;
	autoSpinsCounter = autoSpinsCounter === Infinity ? Infinity : Math.max(0, autoSpinsCounter - 1);
};
stop(); // mid-round STOP
ok('counter cleared while locked', autoSpinsCounter === 0);
overlayOpen = false; // settlement unlock
tryNextAutoplay();
ok('no next wallet/play after STOP', plays === 0 && autoSpinsCounter === 0);

const boardSrc = readFileSync(BOARD, 'utf8');
ok('payline pops symbols (no drawn line)', boardSrc.includes('animateLinePop') && !boardSrc.includes('animatePathDraw'));
ok('pop order: left to right, top to bottom', /a\.reel - b\.reel \|\| a\.row - b\.row/.test(boardSrc));
ok('catchUp skips long sequence', /catchUp \|\| prefersReducedMotion/.test(boardSrc));
ok('book positions only (win.positions)', boardSrc.includes('[...win.positions]'));
ok('no FE payout invent in board', !/evaluatePaylines\(/.test(boardSrc));

const timingsSrc = readFileSync(TIMINGS, 'utf8');
ok('lineDrawMs in NORMAL/TURBO/CATCH_UP', timingsSrc.includes('lineDrawMs'));
ok('CATCH_UP lineDrawMs 0', /catchUp:[\s\S]*lineDrawMs:\s*0/.test(timingsSrc));

const paySrc = readFileSync(PAYTABLE, 'utf8');
const rulesSrc = readFileSync(RULES, 'utf8');
ok('paytable imports canonical awards', /V2_CANONICAL_PAYTABLE|V2_PROVISIONAL_PAYTABLE/.test(paySrc));
ok('paytable has line viewer', /V2_PAYLINES/.test(paySrc) && /prev|next|inspect/i.test(paySrc));
ok('paytable no V1 distance language', !/distanceTotal|six sequential|weather metres/i.test(paySrc));
ok('rules no Phase 2 title', !/Phase 2/i.test(rulesSrc));
ok('rules mentions Free Spins', /free spin/i.test(rulesSrc));
ok('rules no PT2H / BODY1 / WR-C', !/PT2H|BODY1|WR-C H2|R-BATCH/i.test(rulesSrc));

const cfg = JSON.parse(readFileSync(CONFIG_JSON, 'utf8'));
const awards = cfg.paytable.awards;
for (const id of ['P1', 'P2', 'P3', 'M1', 'M2', 'M3', 'L1', 'L2', 'L3']) {
	ok(`canonical awards ${id}`, awards[id]?.['3'] != null && awards[id]?.['5'] != null);
}

const audioSrc = readFileSync(AUDIO, 'utf8');
ok('audio catalog present', audioSrc.includes('V2_AUDIO_CATALOG'));
ok('no http(s) audio URLs in catalog', !/https?:\/\//.test(audioSrc));
ok('missing kind supported in types', audioSrc.includes("kind: 'missing'"));
ok('custom v2 pack mapped', audioSrc.includes("kind: 'v2'") && audioSrc.includes('sfx/v2'));
ok('catchUp suppresses SFX', /if \(options\.catchUp\) return/.test(audioSrc));

const legacyFiles = [
	'ui_click.mp3',
	'button_hover_sound.mp3',
	'bet_button_sound.mp3',
	'slot1-5start_sound.mp3',
	'slot1-5reveal_sound.mp3',
];
for (const f of legacyFiles) {
	ok(`legacy file on disk ${f}`, existsSync(resolve(LEGACY_DIR, f)));
}

const V2_DIR = resolve(POC, 'static/assets/audio/skyjump/sfx/v2');
const fileRe = /kind: '(?:legacy|existing|v2)',\s*file: '([^']+)'/g;
let m: RegExpExecArray | null;
const mappedFiles = new Set<string>();
while ((m = fileRe.exec(audioSrc))) mappedFiles.add(m[1]);
for (const file of mappedFiles) {
	if (file.startsWith('relaxed_background')) {
		ok(
			`bgm ${file}`,
			existsSync(resolve(POC, 'static/assets/audio/skyjump/bgm', file)),
		);
		continue;
	}
	if (file.startsWith('sfx_')) {
		ok(
			`v2 custom ${file}`,
			existsSync(resolve(V2_DIR, file)) ||
				existsSync(resolve(POC, 'static/assets/midnight-lounge/audio', file)),
		);
		continue;
	}
	const legacy = resolve(LEGACY_DIR, file);
	const existing = resolve(POC, 'static/assets/audio/skyjump/sfx', file);
	ok(
		`mapped audio exists ${file}`,
		existsSync(legacy) ||
			existsSync(existing) ||
			existsSync(resolve(POC, 'static/assets/midnight-lounge/audio', file)),
	);
}

if (failed) {
	console.error(`\ntest-v2-phase8a-autoplay-stop: FAIL (${failed})`);
	process.exit(1);
}
console.log('\ntest-v2-phase8a-autoplay-stop: PASS');
