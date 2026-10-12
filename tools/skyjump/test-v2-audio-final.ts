/**
 * Final custom V2 SFX pack — catalog, files on disk, safety contracts.
 * Run: node --experimental-strip-types tools/skyjump/test-v2-audio-final.ts
 */

import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync, existsSync, readdirSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const POC = resolve(ROOT, 'frontend/apps/poc');
const AUDIO = resolve(POC, 'src/game/skyjump_v2/audio.ts');
const HANDLERS = resolve(POC, 'src/game/bookEventHandlerMap.ts');
const BOARD = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2Board.svelte');
const V2_DIR = resolve(POC, 'static/assets/audio/skyjump/sfx/v2');
const LEGACY_DIR = resolve(POC, 'static/assets/audio/skyjump/sfx/legacy_v1');
const SKYJUMP_AUDIO = resolve(POC, 'src/game/skyjump/skyjumpAudio.ts');

let failed = 0;
const ok = (name: string, pass: boolean, detail = '') => {
	console.log(pass ? 'OK' : 'FAIL', name, detail);
	if (!pass) failed += 1;
};

const expectedCustom = [
	'sfx_payline_draw.mp3',
	'sfx_payline_complete.mp3',
	'sfx_scatter_land.mp3',
	'sfx_scatter_trigger.mp3',
	'sfx_free_spins_start.mp3',
	'sfx_free_spins_retrigger.mp3',
	'sfx_tier_upgrade.mp3',
	'sfx_mystery_open.mp3',
	'sfx_token_reveal.mp3',
	'sfx_thermal_lift.mp3',
	'sfx_gate_upgrade.mp3',
	'sfx_judge_collect.mp3',
	'sfx_head_judge_collect.mp3',
	'sfx_rejump.mp3',
	'sfx_wind_charge.mp3',
	'sfx_wind_upgrade.mp3',
	'sfx_wind_transition.mp3',
	'sfx_world_record.mp3',
	'sfx_max_win.mp3',
	'sfx_bonus_end.mp3',
	'sfx_bad_miss.mp3',
	// Midnight Lounge win reactions (mini / big / mega).
	'sfx_win_mini.mp3',
	'sfx_win_big.mp3',
	'sfx_win_mega.mp3',
];

const onDisk = existsSync(V2_DIR) ? readdirSync(V2_DIR).filter((f) => f.endsWith('.mp3')) : [];
ok('v2 sfx directory exists', existsSync(V2_DIR));
ok('custom attachment count 24', onDisk.length === 24, `got ${onDisk.length}`);
for (const f of expectedCustom) {
	ok(`file on disk ${f}`, existsSync(resolve(V2_DIR, f)));
}
const unexpected = onDisk.filter((f) => !expectedCustom.includes(f));
ok('no unexpected v2 files', unexpected.length === 0, unexpected.join(','));

const audioSrc = readFileSync(AUDIO, 'utf8');
const handlersSrc = readFileSync(HANDLERS, 'utf8');
const boardSrc = readFileSync(BOARD, 'utf8');
const skyAudioSrc = readFileSync(SKYJUMP_AUDIO, 'utf8');

ok('catalog exports V2_AUDIO_CATALOG', audioSrc.includes('export const V2_AUDIO_CATALOG'));
ok('playV2AudioHook catchUp early return', /if \(options\.catchUp\) return/.test(audioSrc));
ok('no external http(s) URLs in audio.ts', !/https?:\/\//.test(audioSrc));
ok('volume uses stateSoundDerived.volumeSoundEffect', audioSrc.includes('volumeSoundEffect'));
ok('softDuckSkyJumpBgm used', audioSrc.includes('softDuckSkyJumpBgm'));
ok('softDuck helper exists', skyAudioSrc.includes('export const softDuckSkyJumpBgm'));
ok('missing/silent fail safe try/catch', audioSrc.includes('never crash') || /catch \{\s*\/\* never/.test(audioSrc));
ok('Coach is SILENT', /COACH:\s*\{[\s\S]*kind: 'silent'/.test(audioSrc));
ok('BAD_MISS is OPTIONAL not wired in handlers', /BAD_MISS:[\s\S]*status: 'OPTIONAL'/.test(audioSrc) && !handlersSrc.includes("playV2AudioHook('BAD_MISS'"));
ok('no frontend Math.random in audio.ts', !/Math\.random/.test(audioSrc));

const hookFilePairs: [string, string][] = [
	['PAYLINE_DRAW', 'sfx_payline_draw.mp3'],
	['PAYLINE_COMPLETE', 'sfx_payline_complete.mp3'],
	['SCATTER_LAND', 'sfx_scatter_land.mp3'],
	['SCATTER_TRIGGER', 'sfx_scatter_trigger.mp3'],
	['FS_START', 'sfx_free_spins_start.mp3'],
	['FS_RETRIGGER', 'sfx_free_spins_retrigger.mp3'],
	['TIER_UPGRADE', 'sfx_tier_upgrade.mp3'],
	['MYSTERY_TRANSFORM', 'sfx_mystery_open.mp3'],
	['TOKEN_REVEAL', 'sfx_token_reveal.mp3'],
	['THERMAL', 'sfx_thermal_lift.mp3'],
	['GATE_UPGRADE', 'sfx_gate_upgrade.mp3'],
	['JUDGE_COLLECT', 'sfx_judge_collect.mp3'],
	['HEAD_JUDGE_COLLECT', 'sfx_head_judge_collect.mp3'],
	['REJUMP', 'sfx_rejump.mp3'],
	['WIND_CHARGE', 'sfx_wind_charge.mp3'],
	['WIND_UPGRADE', 'sfx_wind_upgrade.mp3'],
	['WIND_TRANSITION', 'sfx_wind_transition.mp3'],
	['WORLD_RECORD', 'sfx_world_record.mp3'],
	['MAX_WIN', 'sfx_max_win.mp3'],
	['BONUS_END', 'sfx_bonus_end.mp3'],
];

for (const [hook, file] of hookFilePairs) {
	const re = new RegExp(`${hook}:\\s*\\{[\\s\\S]*?file:\\s*'${file.replace('.', '\\.')}'`);
	ok(`hook ${hook} → ${file}`, re.test(audioSrc));
}

ok('handlers use FS_START', handlersSrc.includes("playV2AudioHook('FS_START'"));
ok('handlers use WORLD_RECORD before presentation wait', /WORLD_RECORD[\s\S]*wrHoldMs/.test(handlersSrc));
ok('handlers use MAX_WIN on CapReached', /skyjumpCapReached[\s\S]*MAX_WIN/.test(handlersSrc));
ok('Head Judge pass2 gainScale 0.7', /HEAD_JUDGE_COLLECT[\s\S]*gainScale: bookEvent\.passIndex === 2 \? 0\.7/.test(handlersSrc));
ok('handlers pass audioOpts catchUp', handlersSrc.includes('audioOpts') && handlersSrc.includes('resumeCatchUp'));
ok('payline draw synced in board', boardSrc.includes("playV2AudioHook('PAYLINE_DRAW'") && boardSrc.includes("playV2AudioHook('PAYLINE_COMPLETE'"));
ok('scatter land on reel stop', boardSrc.includes("playV2AudioHook('SCATTER_LAND'"));
ok('board catchUp skips reveal animation (no historical land SFX)', /skyjumpV2BoardReveal:[\s\S]*if \(catchUp\) \{[\s\S]*return;/.test(boardSrc));
ok('no audio-driven gameplay in audio.ts (no stateGame writes)', !/stateGame\./.test(audioSrc));

// Resolve every kind:v2 file from catalog text
const v2FileRe = /kind: 'v2',\s*file: '([^']+)'/g;
let m: RegExpExecArray | null;
const catalogV2 = new Set<string>();
while ((m = v2FileRe.exec(audioSrc))) catalogV2.add(m[1]);
for (const file of catalogV2) {
	ok(`catalog v2 file exists ${file}`, existsSync(resolve(V2_DIR, file)));
}

const legacyUi = ['ui_click.mp3', 'button_hover_sound.mp3', 'bet_button_sound.mp3', 'bet_increase_sound.mp3', 'bet_decrease_sound.mp3'];
for (const f of legacyUi) {
	ok(`preserved UI ${f}`, existsSync(resolve(LEGACY_DIR, f)));
}

// Semantic ordering contract: WR and MAX_WIN are distinct hooks
ok('WR ≠ MAX_WIN files', audioSrc.includes('sfx_world_record.mp3') && audioSrc.includes('sfx_max_win.mp3'));

if (failed) {
	console.error(`\ntest-v2-audio-final: FAIL (${failed})`);
	process.exit(1);
}
console.log('\ntest-v2-audio-final: PASS');
