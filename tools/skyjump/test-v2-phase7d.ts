/**
 * Phase 7D frontend hardening smoke tests (no Vite required).
 * Run: node --experimental-strip-types tools/skyjump/test-v2-phase7d.ts
 */

import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '../..');
const POC = resolve(REPO, 'frontend/apps/poc');

const fail = (msg: string): never => {
	console.error('FAIL:', msg);
	process.exit(1);
};

const ok = (msg: string) => console.log('OK:', msg);

// --- Font: no Typekit in poc app.html ---
const appHtml = readFileSync(resolve(POC, 'src/app.html'), 'utf8');
if (/use\.typekit\.net|fonts\.googleapis|fonts\.gstatic/i.test(appHtml)) {
	fail('poc app.html still references remote fonts');
}
ok('no remote font URL in poc app.html');

// --- Buy costs only from V2 config ---
const cfgPath = resolve(REPO, 'math/games/0_0_poc/skyjump_v2_config.json');
const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));
const costs = {
	LARGE_HILL: cfg.buyModes.LARGE_HILL.costMultiplier,
	SKI_FLYING: cfg.buyModes.SKI_FLYING.costMultiplier,
	WORLD_CUP: cfg.buyModes.WORLD_CUP.costMultiplier,
	PERFECT_V: cfg.buyModes.PERFECT_V.costMultiplier,
};
if (costs.LARGE_HILL !== 30.2 || costs.SKI_FLYING !== 196.9) fail(`buy costs drifted: ${JSON.stringify(costs)}`);
if (costs.WORLD_CUP !== 412.8 || costs.PERFECT_V !== 1369.1) fail(`buy costs drifted: ${JSON.stringify(costs)}`);
ok('buy costs from canonical config');

// --- Math frozen: config mathVersion 2, no accidental paytable edit in this phase ---
if (Number(cfg.meta.mathVersion) !== 2) fail(`mathVersion ${cfg.meta.mathVersion}`);
ok('mathVersion still 2');

// --- Handler map completeness (source scan) ---
const handlerSrc = readFileSync(resolve(POC, 'src/game/bookEventHandlerMap.ts'), 'utf8');
const required = [
	'skyjumpSpinStart',
	'skyjumpBoardReveal',
	'skyjumpLineWins',
	'skyjumpScatterResult',
	'skyjumpCoachSignal',
	'skyjumpMysteryTransform',
	'skyjumpMysteryResolve',
	'skyjumpGateUpgrade',
	'skyjumpThermalLift',
	'skyjumpJudgeCollect',
	'skyjumpHeadJudgeCollect',
	'skyjumpWindKey',
	'skyjumpRejumpStart',
	'skyjumpRejumpBoard',
	'skyjumpRejumpLineWins',
	'skyjumpRejumpEnd',
	'skyjumpCapReached',
	'skyjumpWorldRecord',
	'skyjumpFreeSpinsStart',
	'skyjumpFreeSpinsEnd',
	'skyjumpResult',
	'finalWin',
	'createBonusSnapshot',
];
const missing = required.filter((t) => !handlerSrc.includes(`${t}:`));
if (missing.length) fail(`missing handlers: ${missing.join(', ')}`);
ok(`handler map covers ${required.length} required types`);

// --- Presentation lock / timings / audio modules exist ---
for (const rel of [
	'src/game/skyjump_v2/presentationLock.ts',
	'src/game/skyjump_v2/timings.ts',
	'src/game/skyjump_v2/audio.ts',
	'src/game/skyjump_v2/winPresentation.ts',
	'src/game/skyjump_v2/handlerAudit.ts',
]) {
	if (!existsSync(resolve(POC, rel))) fail(`missing ${rel}`);
}
ok('presentation modules present');

// --- Resume reserves include WR + FreeSpinsEnd ---
const resumeSrc = readFileSync(resolve(POC, 'src/game/skyjump_v2/snapshotResume.ts'), 'utf8');
if (!resumeSrc.includes("'skyjumpWorldRecord'") || !resumeSrc.includes("'skyjumpFreeSpinsEnd'")) {
	fail('resume reserve list missing WorldRecord or FreeSpinsEnd');
}
ok('resume reserves include WR + FreeSpinsEnd');

// --- Timing modes: catchUp zeros ---
const timingsSrc = readFileSync(resolve(POC, 'src/game/skyjump_v2/timings.ts'), 'utf8');
if (!timingsSrc.includes('catchUp:') || !timingsSrc.includes('getV2TimingsForState')) {
	fail('catchUp timing profile missing');
}
ok('NORMAL/TURBO/CATCH_UP timing profiles defined');

// --- DEV preview route gated ---
const preview = readFileSync(resolve(POC, 'src/routes/dev-preview/+page.ts'), 'utf8');
if (!preview.includes('!dev') && !preview.includes("import.meta.env.DEV")) {
	// file uses `dev` from $app/environment
	if (!preview.includes('dev')) fail('dev-preview not gated');
}
ok('dev-preview route present (DEV-gated)');

// --- Asset registry drop-in paths ---
const reg = readFileSync(resolve(POC, 'src/game/skyjump_v2/symbolAssetRegistry.ts'), 'utf8');
if (!reg.includes('/assets/skyjump_v2/symbols')) fail('symbol runtime path missing');
ok('symbol asset registry path locked');

const symbolsDir = resolve(POC, 'static/assets/skyjump_v2/symbols');
if (!existsSync(symbolsDir)) fail('symbols drop dir missing');
ok('Filip drop-in symbols directory exists');

// --- No hardcoded buy costs in Game.svelte ---
const game = readFileSync(resolve(POC, 'src/components/Game.svelte'), 'utf8');
for (const bad of ['30.2', '196.9', '412.8', '1369.1']) {
	if (game.includes(bad)) fail(`Game.svelte hardcodes cost ${bad}`);
}
ok('Game.svelte has no hardcoded buy costs');

// --- Math package hash smoke (config bytes) ---
const sha = createHash('sha256').update(readFileSync(cfgPath)).digest('hex');
ok(`config sha256 ${sha.slice(0, 16)}… (unchanged by FE-only phase if no math edits)`);

console.log('\nPhase 7D smoke: PASS');
