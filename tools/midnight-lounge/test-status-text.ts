import assert from 'node:assert/strict';
import { statusLabel, statusSub } from '../../frontend/apps/poc/src/game/skyjump_v2/statusText.ts';

assert.equal(statusLabel('REJUMP 2 SKIPPED'), 'RESPIN 2');
assert.equal(statusSub('truncated · MAX_REJUMPS_PER_SPIN'), '');
assert.equal(statusLabel('REJUMP 1 · P1 ×3'), 'RESPIN 1 · P1 ×3');
assert.equal(statusLabel('JUDGE COLLECT'), 'DEALER COLLECTS');
assert.equal(statusLabel('THERMAL'), 'GOLDEN SPOTLIGHT');
assert.equal(statusSub('2.5x · L3'), '2.5x · line 3');
assert.equal(statusSub('1.0x → 2.0x · terminated true · max 50000x · drag 1.0'), '1.0x → 2.0x · max 50000x');
assert.equal(statusSub('keep 3 · redrop 2 · spin #1'), '');
assert.equal(statusLabel('TOTAL WIN'), 'TOTAL WIN');
assert.equal(statusSub('pass 1 · +3.0x · flight x2 · feature 4.0x'), 'pass 1 · +3.0x · lounge x2 · feature 4.0x');
for (const t of [statusLabel('REJUMP BOARD'), statusLabel('SNOWBURST'), statusLabel('COACH SIGNAL'), statusSub('FS cancelled 3 · world')]) {
	assert.ok(!/rejump|snow|coach|judge|thermal|ski|truncated|terminated/i.test(t), t);
}
console.log('status text: ok');
