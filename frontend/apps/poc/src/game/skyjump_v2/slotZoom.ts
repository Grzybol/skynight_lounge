/**
 * Slow zoom towards the slot while a big win (big win and above) is being rolled and presented.
 *
 * The scene layers (background plate with its plants, the two characters, the slot board) are scaled about the middle of the slot
 * with the standalone `scale` / `translate` CSS properties, so their own `transform`s stay untouched. The BetUI, the
 * celebration and the modals are not zoomed. Everything is reset on `reset()`.
 */

type Target = { el: HTMLElement; cx: number; cy: number };

const SELECTOR = '[data-lounge-bg], .lounge-character, .board-surface';

let targets: Target[] = [];
let origin = { x: 0, y: 0 };
let scale = 1;
let raf = 0;
let timer: ReturnType<typeof setTimeout> | undefined;
let safety: ReturnType<typeof setTimeout> | undefined;

const apply = (s: number) => {
	scale = s;
	for (const t of targets) {
		if (Math.abs(s - 1) < 1e-4) {
			t.el.style.removeProperty('scale');
			t.el.style.removeProperty('translate');
			continue;
		}
		t.el.style.scale = String(s);
		t.el.style.translate = `${(origin.x - t.cx) * (1 - s)}px ${(origin.y - t.cy) * (1 - s)}px`;
	}
};

const measure = () => {
	const root = document.querySelector('.skyjump-viewport');
	if (!(root instanceof HTMLElement)) return false;
	// Measure at scale 1: undo any zoom for a moment.
	const wasScale = scale;
	if (wasScale !== 1) apply(1);
	const board = root.querySelector('.board-surface');
	if (!(board instanceof HTMLElement)) return false;
	const b = board.getBoundingClientRect();
	origin = { x: b.left + b.width / 2, y: b.top + b.height / 2 };
	targets = [...root.querySelectorAll<HTMLElement>(SELECTOR)].map((el) => {
		const r = el.getBoundingClientRect();
		return { el, cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
	});
	if (wasScale !== 1) apply(wasScale);
	return true;
};

const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);

const animateTo = (to: number, ms: number) => {
	cancelAnimationFrame(raf);
	const from = scale;
	if (ms <= 0 || Math.abs(to - from) < 1e-4) {
		apply(to);
		return;
	}
	const start = performance.now();
	const step = (now: number) => {
		const t = Math.min(1, (now - start) / ms);
		apply(from + (to - from) * ease(t));
		if (t < 1) raf = requestAnimationFrame(step);
	};
	raf = requestAnimationFrame(step);
};

export const slotZoom = {
	/** Zoom in slowly to `to` (e.g. 1.1) over `ms`; a safety release follows if nothing releases it. */
	zoomIn(to: number, ms: number, safetyMs = 60000) {
		if (typeof document === 'undefined') return;
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		if (scale === 1 && !measure()) return;
		clearTimeout(timer);
		clearTimeout(safety);
		animateTo(to, ms);
		safety = setTimeout(() => slotZoom.release(0, 2200), safetyMs);
	},
	/** Let the zoom go slowly: start after `delayMs`, take `ms`. */
	release(delayMs: number, ms: number) {
		if (typeof document === 'undefined' || scale === 1) return;
		clearTimeout(timer);
		clearTimeout(safety);
		timer = setTimeout(() => animateTo(1, ms), Math.max(0, delayMs));
	},
	/** Back to normal at once (new spin, unmount). */
	reset() {
		cancelAnimationFrame(raf);
		clearTimeout(timer);
		clearTimeout(safety);
		apply(1);
		targets = [];
	},
	get active() {
		return scale !== 1;
	},
};
