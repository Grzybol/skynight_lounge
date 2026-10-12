/**
 * Polyphonic voice scheduler. No Howl, no Svelte.
 * Run: node --experimental-strip-types tools/skyjump/test-v2-audio-polyphony.ts
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
	createVoiceLedger,
	startPolyphonicVoice,
	type PolyphonicPort,
} from '../../frontend/apps/poc/src/game/skyjump_v2/audioVoices.ts';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const audioSrc = readFileSync(
	resolve(root, 'frontend/apps/poc/src/game/skyjump_v2/audio.ts'),
	'utf8',
);

let failed = 0;
const ok = (name: string, pass: boolean, detail = '') => {
	console.log(pass ? 'OK' : 'FAIL', name, detail);
	if (!pass) failed += 1;
};

type Fake = PolyphonicPort & {
	gains: Map<number, number>;
	end: (id: number) => void;
	stopped: number[];
};

const fakePort = (): Fake => {
	const gains = new Map<number, number>();
	const ends = new Map<number, () => void>();
	const stopped: number[] = [];
	let next = 1;
	return {
		gains,
		stopped,
		play: () => next++,
		volume: (gain, id) => {
			gains.set(id, gain);
		},
		onEnd: (id, fn) => {
			ends.set(id, fn);
		},
		end: (id) => {
			ends.get(id)?.();
		},
	};
};

const burst = (hook: string, count: number, gapMs: number, minGapMs: number, gain = 1) => {
	const ledger = createVoiceLedger();
	const port = fakePort();
	const results: string[] = [];
	let now = 1_000;
	for (let i = 0; i < count; i += 1) {
		results.push(
			startPolyphonicVoice({ hook, port, gain, minGapMs, now, ledger }),
		);
		now += gapMs;
	}
	return { ledger, port, results };
};

const tokenTwice = burst('TOKEN_REVEAL', 2, 100, 0);
ok(
	'TEST 1 token reveal twice at 100ms both start',
	tokenTwice.results.every((r) => r === 'started') && tokenTwice.ledger.activeIds.get('TOKEN_REVEAL')?.length === 2,
);
ok('TEST 1 neither voice was stopped', tokenTwice.port.stopped.length === 0);

const tokenFive = burst('TOKEN_REVEAL', 5, 40, 0);
ok(
	'TEST 2 five token reveals stay active',
	tokenFive.results.every((r) => r === 'started') &&
		tokenFive.ledger.activeIds.get('TOKEN_REVEAL')?.length === 5,
);
ok('TEST 2 older copies are not stopped', tokenFive.port.stopped.length === 0);

const paylines = burst('PAYLINE_DRAW', 5, 100, 0);
ok(
	'TEST 3 five turbo payline draws stay active',
	paylines.ledger.activeIds.get('PAYLINE_DRAW')?.length === 5 && paylines.port.stopped.length === 0,
);

const scatters = burst('SCATTER_LAND', 5, 60, 0);
ok(
	'TEST 4 five turbo scatter lands stay active',
	scatters.ledger.activeIds.get('SCATTER_LAND')?.length === 5 && scatters.port.stopped.length === 0,
);

const mixedLedger = createVoiceLedger();
const mixedPorts = {
	PAYLINE_DRAW: fakePort(),
	SCATTER_LAND: fakePort(),
	TOKEN_REVEAL: fakePort(),
};
for (const hook of ['PAYLINE_DRAW', 'SCATTER_LAND', 'TOKEN_REVEAL'] as const) {
	startPolyphonicVoice({
		hook,
		port: mixedPorts[hook],
		gain: 0.5,
		minGapMs: 0,
		now: 5_000,
		ledger: mixedLedger,
	});
}
ok(
	'TEST 5 three different hooks stay active together',
	mixedLedger.activeIds.get('PAYLINE_DRAW')?.length === 1 &&
		mixedLedger.activeIds.get('SCATTER_LAND')?.length === 1 &&
		mixedLedger.activeIds.get('TOKEN_REVEAL')?.length === 1,
);

const judge = fakePort();
const judgeLedger = createVoiceLedger();
startPolyphonicVoice({
	hook: 'HEAD_JUDGE_COLLECT',
	port: judge,
	gain: 1,
	minGapMs: 0,
	now: 8_000,
	ledger: judgeLedger,
});
startPolyphonicVoice({
	hook: 'HEAD_JUDGE_COLLECT',
	port: judge,
	gain: 0.7,
	minGapMs: 0,
	now: 8_100,
	ledger: judgeLedger,
});
const [firstId, secondId] = judgeLedger.activeIds.get('HEAD_JUDGE_COLLECT') ?? [];
ok(
	'TEST 6 second gain does not change the first voice',
	judge.gains.get(firstId!) === 1 && judge.gains.get(secondId!) === 0.7,
);

ok('TEST 7 music duck remains and BGM is not stopped from the SFX player', audioSrc.includes('softDuckSkyJumpBgm') && !audioSrc.includes('stopSkyJumpBgm'));
ok('SFX player does not call howl.stop', !/howl\.stop/.test(audioSrc));
ok('SFX player sets per-id volume', audioSrc.includes('howl.volume(gain, id)'));

const ui = fakePort();
const uiLedger = createVoiceLedger();
const first = startPolyphonicVoice({
	hook: 'UI_HOVER',
	port: ui,
	gain: 0.4,
	minGapMs: 40,
	now: 10_000,
	ledger: uiLedger,
});
const second = startPolyphonicVoice({
	hook: 'UI_HOVER',
	port: ui,
	gain: 0.4,
	minGapMs: 40,
	now: 10_020,
	ledger: uiLedger,
});
ok('UI minGap drops the new tick and leaves the first voice', first === 'started' && second === 'blocked-gap' && uiLedger.activeIds.get('UI_HOVER')?.length === 1);

tokenFive.port.end(tokenFive.ledger.activeIds.get('TOKEN_REVEAL')![0]!);
ok(
	'natural end removes only that voice id',
	tokenFive.ledger.activeIds.get('TOKEN_REVEAL')?.length === 4,
);
for (const id of [...(tokenFive.ledger.activeIds.get('TOKEN_REVEAL') ?? [])]) tokenFive.port.end(id);
ok('ledger drops the hook when every voice has ended', !tokenFive.ledger.activeIds.has('TOKEN_REVEAL'));

if (failed) {
	console.error(`\ntest-v2-audio-polyphony: FAIL (${failed})`);
	process.exit(1);
}
console.log('\ntest-v2-audio-polyphony: PASS');
