/**
 * Metadata-driven frame player for one character canvas.
 *
 * - Time based: the frame shown is `floor(elapsed * fps)`, never "one rAF = one
 *   frame", so 60/120/144 Hz displays all play at the declared 30 fps.
 * - The canvas keeps showing the last drawn frame until a replacement clip has
 *   its first frames decoded (`play()` awaits `prepare()`), so a switch never
 *   shows an empty/black/white frame.
 * - Decoded ImageBitmaps are bounded: only a window ahead of the playhead and
 *   the warm start frames of the pending clip are kept; the rest are closed.
 * - Stale requests are dropped with a request token; completion callbacks carry
 *   the clip token so an old clip can never override a newer one.
 */
import type { FramePack, FramePackStore } from './framePackStore';
import { loadManifest } from './framePackStore';
import type { CharacterTuning } from './config';
import { frameAt, isFinished, stallShiftMs } from './timeline';

export type PlayOptions = {
	loop: boolean;
	/** Fires once when a non-looping clip has shown its last frame. */
	onComplete?: () => void;
	/** Fires once, `lead` frames before a non-looping clip ends (to pre-warm the next). */
	/** Looping clips: fires each time a full loop completes, with the loops done so far. */
	onLoop?: (loops: number) => void;
	onNearEnd?: () => void;
	nearEndFrames?: number;
	/** One-shot only: play forward, then the same frames in reverse (ends where it started). */
	pingPong?: boolean;
	/** Playback speed multiplier (0.5 = half speed, twice as long). Default 1. */
	rate?: number;
	/** Asked once at the turning point; false ends the clip there instead of reversing. */
	reverseIf?: () => boolean;
};

type Clip = {
	id: string;
	pack: FramePack;
	token: number;
	startTime: number;
	loop: boolean;
	frames: number;
	fps: number;
	onComplete?: () => void;
	onNearEnd?: () => void;
	onLoop?: (loops: number) => void;
	loops: number;
	nearEndAt: number;
	/** Length of the playback sequence: `frames`, or 2*frames-2 when ping-ponging. */
	seq: number;
	pingPong: boolean;
	reverseIf?: () => boolean;
	turnChecked: boolean;
	nearEndFired: boolean;
	/** Leading source frames skipped for this clip. */
	head: number;
	done: boolean;
};

export type PlayerStats = {
	active: string | null;
	frame: number;
	measuredFps: number;
	paused: boolean;
	state: 'empty' | 'loading' | 'playing' | 'paused' | 'error';
	decodedBitmaps: number;
	stalls: number;
	switches: number;
	lastError: string | null;
};

const MAX_CONCURRENT_DECODES = 4;

/** Leading frames dropped from a clip: the character's trim, or more for win clips. */
const headTrim = (tuning: CharacterTuning, id: string) =>
	id.endsWith('_win')
		? Math.max(tuning.trimHeadFrames, tuning.winTrimHeadFrames ?? 0)
		: tuning.trimHeadFrames;

export class CharacterAnimationPlayer {
	private ctx: CanvasRenderingContext2D | null;
	private clip: Clip | null = null;
	private bitmaps = new Map<string, ImageBitmap>();
	private inflight = new Map<string, Promise<void>>();
	private warmId: string | null = null;
	private warmFrames = 0;
	private warmHead = 0;
	private rafId = 0;
	private lastTick = 0;
	private drawnFrame = -1;
	private drawnClipToken = -1;
	private requestToken = 0;
	private clipToken = 0;
	private paused = false;
	private pausedAt = 0;
	private destroyed = false;
	private ready = false;
	private errorMsg: string | null = null;
	private loadingCount = 0;
	private fpsWindowStart = 0;
	private fpsDrawn = 0;
	private measuredFps = 0;
	private stalls = 0;
	private switches = 0;
	private onVisibility = () => {
		if (document.hidden) this.pause();
		else this.resume();
	};

	constructor(
		private readonly canvas: HTMLCanvasElement,
		private readonly store: FramePackStore,
		private readonly tuning: CharacterTuning,
	) {
		this.ctx = canvas.getContext('2d', { alpha: true });
		document.addEventListener('visibilitychange', this.onVisibility);
	}

	get activeId() {
		return this.clip?.id ?? null;
	}

	getStats(): PlayerStats {
		return {
			active: this.clip?.id ?? null,
			frame: Math.max(0, this.drawnFrame),
			measuredFps: this.measuredFps,
			paused: this.paused,
			state: this.errorMsg
				? 'error'
				: this.paused
					? 'paused'
					: this.clip
						? 'playing'
						: this.loadingCount > 0
							? 'loading'
							: 'empty',
			decodedBitmaps: this.bitmaps.size,
			stalls: this.stalls,
			switches: this.switches,
			lastError: this.errorMsg,
		};
	}

	/**
	 * Load a pack and decode its first frames so `play(id)` can swap instantly.
	 * Resolves false if the load failed or a newer prepare/play superseded it.
	 */
	async prepare(id: string, token = this.requestToken): Promise<boolean> {
		if (this.destroyed) return false;
		this.loadingCount += 1;
		try {
			const [pack, manifest] = await Promise.all([this.store.acquire(id), loadManifest()]);
			if (this.destroyed) return false;
			const base = manifest.frames?.[id.split('_')[0]] ?? manifest.frame;
			const size = { w: pack.entry.w ?? base.w, h: pack.entry.h ?? base.h };
			// The canvas only grows: clips of one character can differ in resolution (same aspect) and
			// every frame is drawn scaled to the canvas, so a switch never shrinks or clears it.
			if (size.w > this.canvas.width || size.h > this.canvas.height || this.canvas.width === 0) {
				this.canvas.width = size.w;
				this.canvas.height = size.h;
			}
			const need = Math.min(this.tuning.startBuffer, pack.entry.frames);
			this.warmId = id;
			this.warmFrames = need;
			const head = headTrim(this.tuning, id);
			this.warmHead = head;
			for (let k = head; k < head + need; k += 1) {
				while (!pack.hasFrame(k)) {
					if (pack.state === 'error') throw new Error(`pack ${id} failed`);
					await pack.nextChunk();
					if (this.destroyed) return false;
				}
				await this.decode(pack, k);
			}
			// Do not start a clip that would run out of bytes mid-play.
			const budget = (pack.entry.frames / pack.entry.fps) * 1000 * 0.8;
			while (pack.state === 'loading' && pack.etaMs > budget) {
				await pack.nextChunk();
				if (this.destroyed) return false;
			}
			if (pack.state === 'error') throw new Error(`pack ${id} failed`);
			return token === this.requestToken || token < 0;
		} catch (err) {
			this.errorMsg = String(err instanceof Error ? err.message : err);
			console.warn('[lounge-characters] prepare failed', id, err);
			return false;
		} finally {
			this.loadingCount -= 1;
		}
	}

	/**
	 * Switch to `id` once it is ready. A newer `play()` call cancels this one;
	 * the previous clip keeps rendering until the swap.
	 */
	async play(id: string, opts: PlayOptions): Promise<boolean> {
		if (this.destroyed) return false;
		const token = ++this.requestToken;
		const ok = await this.prepare(id, token);
		if (!ok || this.destroyed || token !== this.requestToken) return false;
		const pack = this.store.peek(id);
		if (!pack || pack.state === 'error') return false;
		this.errorMsg = null;
		const head = headTrim(this.tuning, id);
		const frames = pack.entry.frames - head - this.tuning.trimTailFrames;
		const now = performance.now();
		this.clipToken += 1;
		this.clip = {
			id,
			pack,
			token: this.clipToken,
			startTime: now,
			loop: opts.loop,
			frames,
			fps: pack.entry.fps * (opts.rate && opts.rate > 0 ? opts.rate : 1),
			onComplete: opts.onComplete,
			onNearEnd: opts.onNearEnd,
			onLoop: opts.onLoop,
			loops: 0,
			seq: opts.pingPong && !opts.loop ? frames * 2 - 2 : frames,
			pingPong: Boolean(opts.pingPong && !opts.loop),
			reverseIf: opts.reverseIf,
			turnChecked: false,
			nearEndAt: Math.max(
				1,
				(opts.pingPong && !opts.loop ? frames * 2 - 2 : frames) - (opts.nearEndFrames ?? 20),
			),
			nearEndFired: false,
			head,
			done: false,
		};
		this.switches += 1;
		this.lastTick = now;
		this.warmId = null;
		this.drawFrame(this.clip, 0);
		if (!this.rafId && !this.paused) this.rafId = requestAnimationFrame(this.tick);
		return true;
	}

	pause() {
		if (this.paused) return;
		this.paused = true;
		this.pausedAt = performance.now();
		cancelAnimationFrame(this.rafId);
		this.rafId = 0;
	}

	resume() {
		if (!this.paused) return;
		this.paused = false;
		const now = performance.now();
		if (this.clip) this.clip.startTime += now - this.pausedAt;
		this.lastTick = now;
		if (this.clip && !this.rafId) this.rafId = requestAnimationFrame(this.tick);
	}

	/** Cancel any pending switch and stop ticking; the last frame stays visible. */
	cancel() {
		this.requestToken += 1;
		if (this.clip) this.clip.done = true;
		cancelAnimationFrame(this.rafId);
		this.rafId = 0;
	}

	destroy() {
		this.destroyed = true;
		this.requestToken += 1;
		cancelAnimationFrame(this.rafId);
		this.rafId = 0;
		document.removeEventListener('visibilitychange', this.onVisibility);
		this.clip = null;
		for (const bmp of this.bitmaps.values()) bmp.close();
		this.bitmaps.clear();
		this.inflight.clear();
		this.ctx = null;
	}

	private key(id: string, i: number) {
		return `${id}#${i}`;
	}

	private decode(pack: FramePack, i: number): Promise<void> {
		const key = this.key(pack.id, i);
		if (this.bitmaps.has(key)) return Promise.resolve();
		const running = this.inflight.get(key);
		if (running) return running;
		const job = createImageBitmap(pack.blob(i))
			.then((bmp) => {
				if (this.destroyed) {
					bmp.close();
					return;
				}
				this.bitmaps.set(key, bmp);
			})
			.finally(() => this.inflight.delete(key));
		this.inflight.set(key, job);
		return job;
	}

	private drawFrame(clip: Clip, frame: number): boolean {
		const bmp = this.bitmaps.get(this.key(clip.id, frame + clip.head));
		if (!bmp || !this.ctx) return false;
		this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
		this.ctx.drawImage(bmp, 0, 0, this.canvas.width, this.canvas.height);
		this.drawnFrame = frame;
		this.drawnClipToken = clip.token;
		this.fpsDrawn += 1;
		if (!this.ready) {
			this.ready = true;
			this.canvas.dataset.ready = '1';
		}
		this.canvas.dataset.clip = clip.id;
		this.canvas.dataset.frame = String(frame + clip.head);
		return true;
	}

	private tick = (now: number) => {
		this.rafId = 0;
		const clip = this.clip;
		if (this.destroyed || this.paused || !clip || clip.done) return;

		const gap = now - this.lastTick;
		this.lastTick = now;
		// Throttled/hidden-then-visible: shift the clock instead of fast-forwarding.
		clip.startTime += stallShiftMs(gap, clip.fps);

		let idx = Math.floor(((now - clip.startTime) * clip.fps) / 1000);

		// Buffering: next bytes have not arrived yet. Hold the clock, do not skip.
		const probe = this.mapSeq(clip, clip.loop ? idx % clip.seq : Math.min(idx, clip.seq - 1));
		if (!clip.pack.hasFrame(probe + clip.head) && clip.pack.state !== 'ready') {
			clip.startTime += gap;
			this.stalls += 1;
			idx = Math.floor(((now - clip.startTime) * clip.fps) / 1000);
		}

		// Turning point of a ping-pong clip: end here when something is already waiting.
		if (clip.pingPong && !clip.turnChecked && idx >= clip.frames) {
			clip.turnChecked = true;
			if (clip.reverseIf && !clip.reverseIf()) {
				this.completeClip(clip, clip.frames - 1, clip.frames - 1);
				return;
			}
		}

		if (!clip.loop && isFinished(now - clip.startTime, clip.fps, clip.seq)) {
			this.completeClip(clip, this.mapSeq(clip, clip.seq - 1), clip.seq - 1);
			return;
		}

		const seqIdx = frameAt(now - clip.startTime, clip.fps, clip.seq, clip.loop);
		const frame = this.mapSeq(clip, seqIdx);
		if (clip.loop) {
			const loops = Math.floor(
				Math.floor(((now - clip.startTime) * clip.fps) / 1000) / clip.seq,
			);
			if (loops > clip.loops) {
				clip.loops = loops;
				clip.onLoop?.(loops);
				if (this.clip !== clip) return;
			}
		}
		if (!clip.nearEndFired && !clip.loop && seqIdx >= clip.nearEndAt) {
			clip.nearEndFired = true;
			clip.onNearEnd?.();
		}
		if (frame !== this.drawnFrame || this.drawnClipToken !== clip.token) {
			// Frame decoded late: keep the previous pixels rather than flashing blank.
			this.drawFrame(clip, frame);
		}
		this.decodeAhead(clip, seqIdx);
		this.sweep(clip, seqIdx);

		if (now - this.fpsWindowStart >= 1000) {
			this.measuredFps = Math.round((this.fpsDrawn * 1000) / (now - this.fpsWindowStart));
			this.fpsDrawn = 0;
			this.fpsWindowStart = now;
		}
		this.rafId = requestAnimationFrame(this.tick);
	};

	private completeClip(clip: Clip, lastFrame: number, seqIdx: number) {
		this.drawFrame(clip, lastFrame);
		clip.done = true;
		this.sweep(clip, seqIdx);
		const cb = clip.onComplete;
		if (cb) queueMicrotask(() => this.clip === clip && cb());
	}

	/** Sequence position -> source frame (reverse half when ping-ponging). */
	private mapSeq(clip: Clip, s: number) {
		if (!clip.pingPong || s < clip.frames) return s;
		return clip.frames * 2 - 2 - s;
	}

	private decodeAhead(clip: Clip, seqIdx: number) {
		for (let k = 0; k <= this.tuning.decodeAhead; k += 1) {
			if (this.inflight.size >= MAX_CONCURRENT_DECODES) return;
			let s = seqIdx + k;
			if (s >= clip.seq) {
				if (!clip.loop) return;
				s %= clip.seq;
			}
			const f = this.mapSeq(clip, s);
			const phys = f + clip.head;
			if (!clip.pack.hasFrame(phys)) return;
			if (!this.bitmaps.has(this.key(clip.id, phys))) void this.decode(clip.pack, phys);
		}
	}

	/** Close every bitmap that is neither near the playhead nor a warm start frame. */
	private sweep(clip: Clip, seqIdx: number) {
		const keep = new Set<string>();
		for (let k = -1; k <= this.tuning.decodeAhead + 1; k += 1) {
			let s = seqIdx + k;
			if (clip.loop) s = ((s % clip.seq) + clip.seq) % clip.seq;
			else if (s < 0 || s >= clip.seq) continue;
			const f = this.mapSeq(clip, s);
			keep.add(this.key(clip.id, f + clip.head));
		}
		if (this.warmId) {
			for (let k = 0; k < this.warmFrames; k += 1) {
				keep.add(this.key(this.warmId, k + this.warmHead));
			}
		}
		for (const [key, bmp] of this.bitmaps) {
			if (!keep.has(key)) {
				bmp.close();
				this.bitmaps.delete(key);
			}
		}
	}
}
