/**
 * Chimney smoke: four still frames, cross-faded in a loop and drawn at 30 fps.
 *
 * One shared timer draws every registered canvas, each with its own phase so the plumes do not
 * move in sync. The frames are downscaled once (they are ~1085x1450 and shown ~150 px tall).
 */
import { resolveGameAsset } from '../resolveGameAsset';

export const SMOKE_FRAME_COUNT = 4;
/** Time one frame takes to dissolve into the next (the loop is 4 x this). */
export const SMOKE_STEP_MS = 800;
export const SMOKE_FPS = 30;
export const SMOKE_CANVAS = { w: 256, h: 342 } as const;

type Entry = { canvas: HTMLCanvasElement; ctx: CanvasRenderingContext2D; phaseMs: number };

const entries = new Set<Entry>();
let frames: ImageBitmap[] | null = null;
let loading: Promise<void> | null = null;
let timer: ReturnType<typeof setInterval> | null = null;

const smokeUrl = (n: number) =>
	resolveGameAsset(`assets/midnight-lounge/scene/smoke_frame_${n + 1}.png`);

const load = () => {
	loading ??= Promise.all(
		Array.from({ length: SMOKE_FRAME_COUNT }, async (_, i) => {
			const blob = await (await fetch(smokeUrl(i))).blob();
			return createImageBitmap(blob, {
				resizeWidth: SMOKE_CANVAS.w,
				resizeHeight: SMOKE_CANVAS.h,
				resizeQuality: 'high',
			});
		}),
	).then((list) => {
		frames = list;
	});
	return loading;
};

const smooth = (t: number) => t * t * (3 - 2 * t);

const draw = (now: number) => {
	if (!frames) return;
	for (const e of entries) {
		const t = (now + e.phaseMs) % (SMOKE_FRAME_COUNT * SMOKE_STEP_MS);
		const i = Math.floor(t / SMOKE_STEP_MS);
		const f = smooth((t % SMOKE_STEP_MS) / SMOKE_STEP_MS);
		e.ctx.clearRect(0, 0, SMOKE_CANVAS.w, SMOKE_CANVAS.h);
		e.ctx.globalAlpha = 1 - f;
		e.ctx.drawImage(frames[i], 0, 0);
		e.ctx.globalAlpha = f;
		e.ctx.drawImage(frames[(i + 1) % SMOKE_FRAME_COUNT], 0, 0);
	}
};

/** Registers a canvas for the shared loop; returns the unregister function. */
export const registerSmoke = (canvas: HTMLCanvasElement, phaseMs: number) => {
	const ctx = canvas.getContext('2d');
	if (!ctx) return () => {};
	const entry: Entry = { canvas, ctx, phaseMs };
	entries.add(entry);
	void load().then(() => {
		if (!timer && entries.size) timer = setInterval(() => draw(performance.now()), 1000 / SMOKE_FPS);
	});
	return () => {
		entries.delete(entry);
		if (!entries.size && timer) {
			clearInterval(timer);
			timer = null;
		}
	};
};
