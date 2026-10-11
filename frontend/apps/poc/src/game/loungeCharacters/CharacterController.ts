/**
 * Per-character state machine: default idle loop, occasional one-shot idle
 * variations, and win clips that pre-empt both.
 *
 * Every transition bumps `epoch`; async callbacks (clip completion, deferred
 * plays, timers) compare against the epoch they were created in, so a stale
 * "animation finished" can never override a newer request.
 */
import {
	CHARACTER_ANIMATIONS,
	CHARACTER_TUNING,
	WIN_PRIORITY,
	type CharacterId,
	type WinCategory,
} from './config';
import { nextVariationDelayMs, pickVariation, winMayStart, type Rng } from './idleScheduler';
import type { PlayOptions, PlayerStats } from './CharacterAnimationPlayer';

/** The slice of the player the controller needs (lets tests inject a fake). */
export interface ClipPlayer {
	readonly activeId: string | null;
	play(id: string, opts: PlayOptions): Promise<boolean>;
	prepare(id: string): Promise<boolean>;
	pause(): void;
	resume(): void;
	destroy(): void;
	getStats(): PlayerStats;
}

export type ControllerMode = 'idle' | 'variation' | 'win' | 'manual';

export type ControllerState = {
	mode: ControllerMode;
	winCategory: WinCategory | null;
	animationId: string | null;
};

export type ControllerOptions = {
	rng?: Rng;
	onState?: (state: ControllerState) => void;
	/** Delay before warming the small-win clip once idle is running. */
	warmMiniDelayMs?: number;
};

export class CharacterController {
	private readonly set;
	private readonly tuning;
	private rng: Rng;
	private epoch = 0;
	private mode: ControllerMode = 'idle';
	private winCategory: WinCategory | null = null;
	private lastVariation: string | null = null;
	private pendingVariation: string | null = null;
	private variationTimer: ReturnType<typeof setTimeout> | null = null;
	private prefetchTimer: ReturnType<typeof setTimeout> | null = null;
	private warmTimer: ReturnType<typeof setTimeout> | null = null;
	/** Highest-priority win asked for while a win clip is still playing; starts when it ends. */
	private pendingWin: { category: WinCategory; turbo: boolean } | null = null;
	private idlePlaying = false;
	/** Whole loops of the default idle seen, and the loop count that triggers the next variation. */
	private idleLoops = 0;
	private loopBase = 0;
	private loopTarget: number | null = null;
	private destroyed = false;
	private started = false;

	constructor(
		readonly id: CharacterId,
		private readonly player: ClipPlayer,
		private readonly opts: ControllerOptions = {},
	) {
		this.set = CHARACTER_ANIMATIONS[id];
		this.tuning = CHARACTER_TUNING[id];
		this.rng = opts.rng ?? Math.random;
	}

	/** Ids that must not be evicted from the pack cache right now. */
	pinnedIds(): Set<string> {
		const keep = new Set<string>([this.set.idle]);
		if (this.player.activeId) keep.add(this.player.activeId);
		if (this.pendingVariation) keep.add(this.pendingVariation);
		return keep;
	}

	getState(): ControllerState {
		return {
			mode: this.mode,
			winCategory: this.winCategory,
			animationId: this.player.activeId,
		};
	}

	start() {
		if (this.started || this.destroyed) return;
		this.started = true;
		this.enterIdle();
		const mini = this.set.wins.mini;
		this.warmTimer = setTimeout(() => {
			this.warmTimer = null;
			if (!this.destroyed) void this.player.prepare(mini);
		}, this.opts.warmMiniDelayMs ?? 4000);
	}

	destroy() {
		this.destroyed = true;
		this.epoch += 1;
		this.clearTimers();
		this.player.destroy();
	}

	/**
	 * Called when a win is revealed, or when a running win counter crosses a tier.
	 * A win clip is never cut by another one: a higher request waits (only the highest
	 * waiting one is kept) and starts the moment the current clip has finished.
	 * Idle and variations yield immediately. Returns whether the request was accepted.
	 */
	requestWin(category: WinCategory, opts: { turbo?: boolean } = {}): boolean {
		if (this.destroyed || !this.started) return false;
		const turbo = Boolean(opts.turbo);
		if (this.mode === 'win' && this.winCategory) {
			const waiting = this.pendingWin ? WIN_PRIORITY[this.pendingWin.category] : 0;
			const active = WIN_PRIORITY[this.winCategory];
			if (!winMayStart(Math.max(active, waiting), WIN_PRIORITY[category])) return false;
			this.pendingWin = { category, turbo };
			return true;
		}
		this.beginWin(category, turbo);
		return true;
	}

	private beginWin(category: WinCategory, turbo: boolean) {
		const epoch = ++this.epoch;
		this.clearVariationTimer();
		this.pendingVariation = null;
		this.pendingWin = null;
		this.mode = 'win';
		this.winCategory = category;
		this.emit();
		// Normal speed: big/mega play forward then in reverse (10 s); turbo and mini play once (5 s).
		const pingPong = !turbo && category !== 'mini';
		void this.runClip(epoch, this.set.wins[category], 'win', pingPong);
	}

	/** QA: play any clip of this character once (idle ids loop). */
	playManual(animationId: string) {
		if (this.destroyed || !this.started) return;
		const epoch = ++this.epoch;
		this.clearVariationTimer();
		this.pendingVariation = null;
		if (animationId === this.set.idle) {
			this.enterIdle();
			return;
		}
		this.pendingWin = null;
		this.mode = 'manual';
		this.winCategory = null;
		this.emit();
		void this.runClip(epoch, animationId, 'manual');
	}

	pause() {
		this.player.pause();
	}

	resume() {
		this.player.resume();
	}

	private async runClip(
		epoch: number,
		animationId: string,
		kind: 'win' | 'variation' | 'manual',
		pingPong = false,
	) {
		const ok = await this.player.play(animationId, {
			loop: false,
			pingPong,
			// Skip the reverse half when a higher win is already waiting.
			reverseIf: () => !(epoch === this.epoch && this.pendingWin),
			onNearEnd: () => {
				if (epoch !== this.epoch) return;
				const next = this.pendingWin ? this.set.wins[this.pendingWin.category] : this.set.idle;
				void this.player.prepare(next);
			},
			onComplete: () => {
				if (epoch !== this.epoch) return;
				const next = this.pendingWin;
				if (next) this.beginWin(next.category, next.turbo);
				else this.enterIdle();
			},
		});
		if (ok || epoch !== this.epoch || this.destroyed) return;
		// Load failed (not superseded): fall back to idle and try again later.
		console.warn('[lounge-characters] clip failed, back to idle', this.id, animationId, kind);
		this.enterIdle();
	}

	private enterIdle() {
		if (this.destroyed) return;
		const epoch = ++this.epoch;
		this.mode = 'idle';
		this.winCategory = null;
		this.pendingWin = null;
		this.pendingVariation = null;
		this.emit();
		// Already looping the default idle: never restart it (spin starts, repeats).
		if (this.idlePlaying && this.player.activeId === this.set.idle) {
			this.scheduleVariation(epoch);
			return;
		}
		this.idlePlaying = false;
		this.idleLoops = 0;
		this.loopBase = 0;
		void this.player.play(this.set.idle, { loop: true, onLoop: this.onIdleLoop }).then((ok) => {
			if (epoch !== this.epoch || this.destroyed) return;
			if (ok) this.idlePlaying = true;
			this.scheduleVariation(epoch);
		});
	}

	private onIdleLoop = (loops: number) => {
		this.idleLoops = loops;
		if (this.destroyed || this.mode !== 'idle' || this.loopTarget === null) return;
		if (loops - this.loopBase < this.loopTarget || !this.pendingVariation) return;
		this.loopTarget = null;
		this.startVariation(this.pendingVariation);
	};

	private scheduleVariation(epoch: number) {
		this.clearVariationTimer();
		const variation = pickVariation(
			this.set.variations,
			this.lastVariation,
			this.rng,
			this.tuning.variationWeights,
		);
		if (!variation) return;
		const { idleLoopsMin, idleLoopsMax } = this.tuning;
		if (idleLoopsMin !== undefined && idleLoopsMax !== undefined) {
			// Loop-count mode: the default idle plays N whole times, then a variation.
			this.pendingVariation = variation;
			this.loopBase = this.idleLoops;
			this.loopTarget =
				idleLoopsMin + Math.floor(this.rng() * (idleLoopsMax - idleLoopsMin + 1));
			void this.player.prepare(variation);
			return;
		}
		const delay = nextVariationDelayMs(
			this.tuning.idleVariationMinMs,
			this.tuning.idleVariationMaxMs,
			this.rng,
		);
		this.pendingVariation = variation;
		// Start the download shortly before it is needed, not the moment it is picked.
		const prefetchIn = Math.max(0, delay - this.tuning.variationPrefetchLeadMs);
		this.prefetchTimer = setTimeout(() => {
			this.prefetchTimer = null;
			if (epoch === this.epoch && !this.destroyed) void this.player.prepare(variation);
		}, prefetchIn);
		this.variationTimer = setTimeout(() => {
			this.variationTimer = null;
			if (epoch !== this.epoch || this.destroyed) return;
			if (typeof document !== 'undefined' && document.hidden) {
				this.scheduleVariation(epoch);
				return;
			}
			this.startVariation(variation);
		}, delay);
	}

	private startVariation(variation: string) {
		const epoch = ++this.epoch;
		this.lastVariation = variation;
		this.pendingVariation = null;
		this.mode = 'variation';
		this.loopTarget = null;
		this.idlePlaying = false;
		this.emit();
		void this.runClip(epoch, variation, 'variation');
	}

	private clearVariationTimer() {
		if (this.variationTimer) clearTimeout(this.variationTimer);
		this.variationTimer = null;
		if (this.prefetchTimer) clearTimeout(this.prefetchTimer);
		this.prefetchTimer = null;
	}

	private clearTimers() {
		this.clearVariationTimer();
		if (this.warmTimer) clearTimeout(this.warmTimer);
		this.warmTimer = null;
	}

	private emit() {
		this.opts.onState?.(this.getState());
	}
}
