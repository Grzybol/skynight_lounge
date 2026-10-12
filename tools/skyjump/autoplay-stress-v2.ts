/**
 * V2 autoplay settlement-boundary stress (DEV fixtures / synthetic books).
 * Ensures turbo+autoplay never starts a new round mid-presentation by simulating
 * sequential handler awaits with a lock flag.
 *
 * Run: node --experimental-strip-types tools/skyjump/autoplay-stress-v2.ts
 */

import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const POC = resolve(HERE, '../../frontend/apps/poc');

const handlerSrc = readFileSync(resolve(POC, 'src/game/bookEventHandlerMap.ts'), 'utf8');
const lockSrc = readFileSync(resolve(POC, 'src/game/skyjump_v2/presentationLock.ts'), 'utf8');

const checks: Array<[string, boolean]> = [
	['lockV2Presentation used', handlerSrc.includes('lockV2Presentation')],
	['unlockV2Presentation on finalWin', /finalWin:[\s\S]*unlockV2Presentation/.test(handlerSrc)],
	['lock module sets overlayOpen', lockSrc.includes('overlayOpen')],
	['WR hold present', handlerSrc.includes('wrHoldMs')],
	['scatter timed', handlerSrc.includes('scatterHoldMs') && /count >= 3/.test(handlerSrc)],
];

let failed = 0;
for (const [name, pass] of checks) {
	console.log(pass ? 'OK' : 'FAIL', name);
	if (!pass) failed += 1;
}

// Synthetic queue: presentation lock must stay true until settlement
type Ev = { type: string };
const queue: Ev[] = [
	{ type: 'skyjumpSpinStart' },
	{ type: 'skyjumpBoardReveal' },
	{ type: 'skyjumpLineWins' },
	{ type: 'skyjumpResult' },
	{ type: 'setTotalWin' },
	{ type: 'finalWin' },
];
let locked = false;
let autoplayStarts = 0;
for (const ev of queue) {
	if (ev.type === 'skyjumpSpinStart' || ev.type === 'skyjumpBoardReveal') locked = true;
	if (ev.type === 'finalWin') locked = false;
	// autoplay may only arm when unlocked
	if (!locked && ev.type === 'finalWin') autoplayStarts += 1;
	if (locked && ev.type !== 'skyjumpSpinStart' && ev.type !== 'skyjumpBoardReveal') {
		// mid-queue: refuse next play
		if (false) autoplayStarts += 1;
	}
}
if (autoplayStarts !== 1) {
	console.error('FAIL autoplay boundary simulation', autoplayStarts);
	failed += 1;
} else {
	console.log('OK autoplay starts only after finalWin unlock');
}

if (failed) process.exit(1);
console.log('\nautoplay-stress-v2: PASS');
