/**
 * Phase 8B: Head Judge asset + DEV audio soundboard hygiene.
 * Run: node --experimental-strip-types tools/skyjump/test-v2-phase8b.ts
 */

import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const POC = resolve(ROOT, 'frontend/apps/poc');

let failed = 0;
const ok = (name: string, pass: boolean, detail = '') => {
	console.log(pass ? 'OK' : 'FAIL', name, detail);
	if (!pass) failed += 1;
};

const headRuntime = resolve(POC, 'static/assets/skyjump_v2/symbols/sym_feat_head_judge.png');
const headSource = resolve(ROOT, 'assets/skyjump_v2/source/symbols/sym_feat_head_judge.png');
const judgeRuntime = resolve(POC, 'static/assets/skyjump_v2/symbols/sym_feat_judge.png');
ok('Head Judge runtime PNG exists', existsSync(headRuntime));
ok('Head Judge source copy exists', existsSync(headSource));

const headBuf = readFileSync(headRuntime);
ok('Head Judge PNG magic', headBuf[0] === 0x89 && headBuf[1] === 0x50);
ok(
	'Judge ≠ Head Judge bytes',
	Buffer.compare(headBuf, readFileSync(judgeRuntime)) !== 0,
);

const reg = readFileSync(resolve(POC, 'src/game/skyjump_v2/symbolAssetRegistry.ts'), 'utf8');
ok('registry HEAD_JUDGE → sym_feat_head_judge.png', reg.includes("HEAD_JUDGE: 'sym_feat_head_judge.png'"));

const pay = readFileSync(resolve(POC, 'src/components/skyjump_v2/SkyJumpV2PayTable.svelte'), 'utf8');
ok('paytable uses registry + HEAD_JUDGE card', pay.includes('v2SymbolVisual') && pay.includes("'HEAD_JUDGE'"));
ok('paytable has P1–L3 awards from config', pay.includes('V2_CANONICAL_PAYTABLE') && pay.includes('V2_REGULAR_SYMBOLS'));
ok('paytable 28-line viewer', pay.includes('V2_PAYLINES') && pay.includes('selectPrevLine'));

const rules = readFileSync(resolve(POC, 'src/components/skyjump_v2/SkyJumpV2GameRules.svelte'), 'utf8');
ok('info has How to Play / Free Spins / World Record', /How to Play|Free Spins|World Record/.test(rules));
ok('info has no V1 distance weather language', !/distanceTotal|six sequential|weather metres|cash-per-metre/i.test(rules));

const board = readFileSync(resolve(POC, 'src/components/skyjump_v2/SkyJumpV2Board.svelte'), 'utf8');
ok('board DEV-imports AudioQa', board.includes('SkyJumpV2AudioQa') && board.includes('import.meta.env.DEV'));
ok('payline draw + complete audio', board.includes("PAYLINE_DRAW") && board.includes("PAYLINE_COMPLETE"));
ok('no Math.random in board', !/Math\.random/.test(board));

const audioQa = readFileSync(resolve(POC, 'src/components/skyjump_v2/SkyJumpV2AudioQa.svelte'), 'utf8');
ok('soundboard uses playV2AudioHook', audioQa.includes('playV2AudioHook'));
ok('soundboard has WR→MaxWin sequence', audioQa.includes('seqWorldRecord') && audioQa.includes('WORLD_RECORD'));
ok('soundboard has catch-up silence test', audioQa.includes('catchUp: true'));
ok('soundboard has turbo chain', audioQa.includes('seqTurboSpam'));
for (const hook of [
	'UI_CLICK',
	'PAYLINE_DRAW',
	'SCATTER_TRIGGER',
	'FS_START',
	'HEAD_JUDGE_COLLECT',
	'WORLD_RECORD',
	'MAX_WIN',
	'BAD_MISS',
	'COACH',
]) {
	ok(`soundboard lists ${hook}`, audioQa.includes(`'${hook}'`) || audioQa.includes(`"${hook}"`));
}

const devSrc = readFileSync(resolve(POC, 'src/components/skyjump_v2/SkyJumpV2DevSource.svelte'), 'utf8');
ok('dev scenarios include Head Judge + WR', /Head Judge/.test(devSrc) && /World Record/.test(devSrc));

const betBtn = readFileSync(
	resolve(ROOT, 'frontend/packages/components-ui-pixi/src/components/ButtonBet.svelte'),
	'utf8',
);
ok(
	'STOP clickable under overlayOpen',
	betBtn.includes('isIdle') && betBtn.includes('overlayOpen') && /:\s*false/.test(betBtn),
);

const audio = readFileSync(resolve(POC, 'src/game/skyjump_v2/audio.ts'), 'utf8');
ok('no external audio URLs', !/https?:\/\//.test(audio));

const lh = readFileSync(resolve(POC, 'static/assets/skyjump_v2/ui/ui_tier_large_hill.png'));
const sf = readFileSync(resolve(POC, 'static/assets/skyjump_v2/ui/ui_tier_ski_flying.png'));
const identical = Buffer.compare(lh, sf) === 0;
ok(
	'tier emblem duplicate reported (byte-identical expected until Filip replaces)',
	identical,
	identical
		? createHash('sha256').update(lh).digest('hex')
		: 'now distinct — update docs',
);

if (failed) {
	console.error(`\ntest-v2-phase8b: FAIL (${failed})`);
	process.exit(1);
}
console.log('\ntest-v2-phase8b: PASS');
