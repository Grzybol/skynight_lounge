/**
 * Streaming, bounded store of compressed animation packs.
 *
 * A pack is 150 lossless-alpha WebP frames concatenated into one file. Bytes
 * arrive through a streamed fetch into one preallocated buffer, so frame N is
 * usable the moment its byte range has landed (playback can start on the first
 * frames while the rest downloads). Only compressed bytes live here; decoded
 * ImageBitmaps are owned by the player and are bounded separately.
 */
import { manifestUrl, packUrl, type PackManifest, type PackManifestEntry } from './config';

export type PackState = 'idle' | 'loading' | 'ready' | 'error';

export class FramePack {
	readonly id: string;
	readonly entry: PackManifestEntry;
	state: PackState = 'idle';
	/** Bytes written into `data` so far (contiguous from 0). */
	received = 0;
	readonly data: Uint8Array;
	private abort: AbortController | null = null;
	private startedAt = 0;
	private waiters: Array<() => void> = [];
	/** Bytes per ms, measured. 0 until the first chunk. */
	rate = 0;
	lastUsed = 0;

	constructor(id: string, entry: PackManifestEntry) {
		this.id = id;
		this.entry = entry;
		this.data = new Uint8Array(entry.bytes);
	}

	/** True when frame `i` bytes are fully buffered. */
	hasFrame(i: number) {
		const end = this.entry.offsets[i] + this.entry.sizes[i];
		return end <= this.received;
	}

	/** Number of leading frames that are fully available. */
	get framesAvailable() {
		const { offsets, sizes, frames } = this.entry;
		let n = 0;
		while (n < frames && offsets[n] + sizes[n] <= this.received) n += 1;
		return n;
	}

	blob(i: number): Blob {
		const { offsets, sizes } = this.entry;
		return new Blob([this.data.subarray(offsets[i], offsets[i] + sizes[i])], {
			type: 'image/webp',
		});
	}

	/** Estimated ms until every byte has arrived (0 when complete). */
	get etaMs() {
		if (this.state === 'ready') return 0;
		if (this.rate <= 0) return Number.POSITIVE_INFINITY;
		return (this.entry.bytes - this.received) / this.rate;
	}

	start() {
		if (this.state !== 'idle') return;
		this.state = 'loading';
		this.startedAt = performance.now();
		this.abort = new AbortController();
		void this.pump(this.abort.signal);
	}

	private notify() {
		const w = this.waiters;
		this.waiters = [];
		for (const fn of w) fn();
	}

	/** Resolves after the next chunk lands (or state changes). */
	nextChunk(): Promise<void> {
		if (this.state === 'ready' || this.state === 'error') return Promise.resolve();
		return new Promise((resolve) => this.waiters.push(resolve));
	}

	private async pump(signal: AbortSignal) {
		try {
			// A pack is one file, or several parts that concatenate into it (see PackManifestEntry.parts).
			const files = this.entry.parts?.map((part) => part.file) ?? [this.entry.file];
			for (const file of files) {
				const res = await fetch(packUrl(file), { signal });
				if (!res.ok || !res.body) throw new Error(`pack ${this.id}: HTTP ${res.status}`);
				const reader = res.body.getReader();
				for (;;) {
					const { done, value } = await reader.read();
					if (done) break;
					if (this.received + value.length > this.data.length) throw new Error('pack overrun');
					this.data.set(value, this.received);
					this.received += value.length;
					const dt = performance.now() - this.startedAt;
					if (dt > 0) this.rate = this.received / dt;
					this.notify();
				}
			}
			if (this.received !== this.entry.bytes) {
				throw new Error(`pack ${this.id}: got ${this.received}/${this.entry.bytes} bytes`);
			}
			this.state = 'ready';
		} catch (err) {
			if (signal.aborted) return;
			this.state = 'error';
			console.warn('[lounge-characters]', err);
		} finally {
			this.notify();
		}
	}

	dispose() {
		this.abort?.abort();
		this.abort = null;
		this.state = 'idle';
		this.received = 0;
		this.notify();
	}
}

let manifestPromise: Promise<PackManifest> | null = null;

export const loadManifest = () => {
	manifestPromise ??= fetch(manifestUrl()).then((res) => {
		if (!res.ok) throw new Error(`manifest HTTP ${res.status}`);
		return res.json() as Promise<PackManifest>;
	});
	manifestPromise.catch(() => {
		manifestPromise = null;
	});
	return manifestPromise;
};

/** Per-character LRU of packs. Pinned ids (current, idle) are never evicted. */
export class FramePackStore {
	private packs = new Map<string, FramePack>();
	private clock = 0;

	constructor(
		private readonly maxPacks: number,
		private readonly pinned: () => ReadonlySet<string>,
	) {}

	get size() {
		return this.packs.size;
	}

	/** Snapshot for the QA inspector. */
	snapshot() {
		return [...this.packs.values()].map((p) => ({
			id: p.id,
			state: p.state,
			mb: +(p.received / 1e6).toFixed(2),
			of: +(p.entry.bytes / 1e6).toFixed(2),
		}));
	}

	has(id: string) {
		return this.packs.get(id)?.state === 'ready';
	}

	peek(id: string) {
		return this.packs.get(id) ?? null;
	}

	async acquire(id: string): Promise<FramePack> {
		const existing = this.packs.get(id);
		if (existing && existing.state !== 'error') {
			existing.lastUsed = ++this.clock;
			return existing;
		}
		existing?.dispose();
		this.packs.delete(id);
		const manifest = await loadManifest();
		const entry = manifest.animations[id];
		if (!entry) throw new Error(`unknown animation ${id}`);
		// Another caller may have created it while the manifest resolved.
		const raced = this.packs.get(id);
		if (raced) {
			raced.lastUsed = ++this.clock;
			return raced;
		}
		this.evictFor(id);
		const pack = new FramePack(id, entry);
		pack.lastUsed = ++this.clock;
		this.packs.set(id, pack);
		pack.start();
		return pack;
	}

	private evictFor(incoming: string) {
		const keep = this.pinned();
		while (this.packs.size >= this.maxPacks) {
			let victim: FramePack | null = null;
			for (const p of this.packs.values()) {
				if (p.id === incoming || keep.has(p.id)) continue;
				if (!victim || p.lastUsed < victim.lastUsed) victim = p;
			}
			if (!victim) return;
			victim.dispose();
			this.packs.delete(victim.id);
		}
	}

	dispose() {
		for (const p of this.packs.values()) p.dispose();
		this.packs.clear();
	}
}
