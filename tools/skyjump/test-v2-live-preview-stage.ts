/**
 * Live-preview stage fit math — uniform 16:9 scale, no stretch.
 */
import { fitStageSize, LIVE_PREVIEW_LOGICAL } from '../../frontend/apps/poc/src/game/skyjump_v2/livePreviewStage.ts';

const assert = (cond: boolean, msg: string) => {
	if (!cond) {
		console.error(`FAIL: ${msg}`);
		process.exit(1);
	}
	console.log(`OK  ${msg}`);
};

const a = fitStageSize(1280, 720);
assert(a.width === 1280 && a.height === 720 && a.scale === 1, 'exact 1280×720 → identity');

const b = fitStageSize(640, 360);
assert(b.width === 640 && b.height === 360 && b.scale === 0.5, 'half preset scales uniformly');

const c = fitStageSize(1920, 1080);
assert(c.width === 1280 && c.height === 720 && c.scale === 1, 'larger browser still caps at logical');

const d = fitStageSize(1000, 900);
assert(d.width === 1000 && d.height === 563, 'letterbox width-limited');
assert(Math.abs(d.scale - 1000 / LIVE_PREVIEW_LOGICAL.width) < 1e-9, 'scale = w/1280');

const e = fitStageSize(500, 800);
assert(e.height === 281 || e.height === 282, 'letterbox height from width');
assert(e.width / e.height - 16 / 9 < 0.02, 'preserves ~16:9');

console.log('PASS live-preview stage fit');
