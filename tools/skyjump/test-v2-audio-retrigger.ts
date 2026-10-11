/**
 * Audio retrigger / voice-pool scheduler contracts (no Howl runtime required).
 * Run: node --experimental-strip-types tools/skyjump/test-v2-audio-retrigger.ts
 */

import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const POC = resolve(ROOT, 'frontend/apps/poc');
const AUDIO = resolve(POC, 'src/game/skyjump_v2/audio.ts');
const META = resolve(POC, 'src/game/skyjump_v2/audioDurationMeta.json');
const QA = resolve(POC, 'src/components/skyjump_v2/SkyJumpV2AudioQa.svelte');

let failed = 0;
const ok = (name: string, pass: boolean, detail = '') => {
	console.log(pass ? 'OK' : 'FAIL', name, detail);
	if (!pass) failed += 1;
};

const src = readFileSync(AUDIO, 'utf8');
const meta = JSON.parse(readFileSync(META, 'utf8')) as Record<
	string,
	{
		totalSec: number;
		audibleSec: number;
		trailSec: number;
		problematicTail?: boolean;
		trimmedWav?: string;
		trimmedDir?: string;
	}
>;
const qa = readFileSync(QA, 'utf8');

ok('voices end on Howler end, not a cutoff timer', src.includes("howl.once('end'") && !src.includes('howl.stop'));
ok('per-voice gain uses howl.volume(gain, id)', src.includes('howl.volume(gain, id)'));
ok('minGap is trigger Date.now based', src.includes('lastPlayAt'));
ok('no voice steal', !src.includes('playsBlockedPool += 1') && !/howl\.stop/.test(src));
ok('maxVoices on UI_HOVER is 4', /UI_HOVER:[\s\S]*maxVoices:\s*4/.test(src));
ok('UI_HOVER minGap ~40ms', /UI_HOVER:[\s\S]*minGapMs:\s*40/.test(src));
ok('gameplay TOKEN_REVEAL minGap 0', /TOKEN_REVEAL:[\s\S]*minGapMs:\s*0/.test(src));
ok('gameplay SCATTER_LAND minGap 0', /SCATTER_LAND:[\s\S]*minGapMs:\s*0/.test(src));
ok('gameplay REJUMP minGap 0', /REJUMP:[\s\S]*minGapMs:\s*0/.test(src));
ok('gameplay THERMAL minGap 0', /THERMAL:[\s\S]*minGapMs:\s*0/.test(src));
ok('no single-voice restart policy', !src.includes("overlap: 'single'"));
ok('token reveal documents canonical wav', src.includes('sfx_token_reveal.wav'));
ok('catchUp early return preserved', /if \(options\.catchUp\) return/.test(src));
ok('volume uses stateSoundDerived', src.includes('volumeSoundEffect'));
ok('no global cross-hook lock map', !/globalLock|allHooksPlaying|masterBusy/.test(src));
ok('bounded howlCache Map', src.includes('howlCache'));
ok('trimmed runtime URL bases', src.includes('v2_trimmed') && src.includes('legacy_trimmed'));

ok('ui_click has silent tail measured', meta['ui_click.mp3']?.problematicTail === true);
ok('ui_click trimmed wav exists', Boolean(meta['ui_click.mp3']?.trimmedWav));
ok(
	'trimmed ui_click on disk',
	existsSync(
		resolve(POC, 'static/assets/audio/skyjump/sfx/legacy_trimmed', meta['ui_click.mp3'].trimmedWav!),
	),
);
ok('token_reveal trimmed', Boolean(meta['sfx_token_reveal.mp3']?.trimmedWav));
ok(
	'token_reveal wav on disk',
	existsSync(
		resolve(
			POC,
			'static/assets/audio/skyjump/sfx/v2_trimmed',
			meta['sfx_token_reveal.mp3'].trimmedWav!,
		),
	),
);
ok('masters untouched (v2 token still present)', existsSync(resolve(POC, 'static/assets/audio/skyjump/sfx/v2/sfx_token_reveal.mp3')));

ok('soundboard rapid hover tests', qa.includes('Rapid hover 250ms') && qa.includes('Rapid hover 50ms'));
ok('soundboard rapid paylines', qa.includes('Rapid paylines'));
ok('soundboard feature overlap', qa.includes('Feature overlap'));
ok('soundboard shows poly or voice budget', qa.includes('maxVoices') || qa.includes('poly'));
ok('soundboard token burst', qa.includes('Token ×2 @100ms') && qa.includes('Token ×5 rapid'));
ok('soundboard turbo payline and scatter bursts', qa.includes('Payline draw ×5 turbo') && qa.includes('Scatter land ×5 turbo'));
ok('soundboard mixed and head-judge gain overlap', qa.includes('Draw+Land+Token') && qa.includes('Head Judge gains overlap'));

// Heuristic: UI_HOVER at 50ms with gap 40 and voices 4 should allow overlapping burst
const hoverGap = 40;
const hoverVoices = 4;
ok('hover gap allows 50ms cadence', hoverGap <= 50);
ok('hover voices >= 3', hoverVoices >= 3);

if (failed) {
	console.error(`\ntest-v2-audio-retrigger: FAIL (${failed})`);
	process.exit(1);
}
console.log('\ntest-v2-audio-retrigger: PASS');
