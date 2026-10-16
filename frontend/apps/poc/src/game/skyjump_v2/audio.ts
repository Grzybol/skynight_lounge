/**
 * Semantic V2 audio hooks — custom sfx/v2 pack + preserved UI/legacy.
 * Never affects game state. No frontend RNG. No external URLs.
 *
 * Playback architecture (retriggers):
 * - One Howl buffer per URL (cached). Each play() id is its own voice.
 * - A new voice never stops an older voice of the same hook or any other hook.
 * - Voices leave the ledger on Howler's natural `end`, not on an audible-window timer.
 * - Gain is set with howl.volume(gain, voiceId) so a later voice cannot duck an earlier one.
 * - minGapMs is only for accidental UI repeats. Gameplay hooks use 0.
 * - No global lock, queue, or cross-hook stop.
 *
 * Not wired to gameplay (left in the catalog on purpose):
 * BAD_MISS, REEL_START, REEL_STOP, SPIN, PANEL_OPEN, PANEL_CLOSE.
 * Not in the repo: Quick_reverse_whoosh_#1-1790347183824.mp3,
 * Soft_triumphant_crys_#2-1790347362309.mp3.
 */

import { Howl } from 'howler';
import { stateSoundDerived } from 'state-shared';

import { resolveGameAsset } from '../resolveGameAsset';
import { eventEmitter } from '../eventEmitter';
import { softDuckSkyJumpBgm } from '../skyjump/skyjumpAudio';
import { SKYJUMP_SFX } from '../skyjump/audio';
import durationMetaRaw from './audioDurationMeta.json' with { type: 'json' };
import { createVoiceLedger, startPolyphonicVoice, type PolyphonicPort } from './audioVoices';

const V2_BASE = resolveGameAsset('/assets/audio/skyjump/sfx/v2/');
const V2_TRIMMED_BASE = resolveGameAsset('/assets/audio/skyjump/sfx/v2_trimmed/');
/** Same hook filenames, Midnight Lounge takes. Unmapped whoosh/cry files are not listed. */
const LOUNGE_SFX_BASE = resolveGameAsset('/assets/midnight-lounge/audio/');
const LOUNGE_SFX_FILES = new Set([
	'sfx_bad_miss.mp3',
	'sfx_bonus_end.mp3',
	'sfx_free_spins_retrigger.mp3',
	'sfx_free_spins_start.mp3',
	'sfx_gate_upgrade.mp3',
	'sfx_head_judge_collect.mp3',
	'sfx_judge_collect.mp3',
	'sfx_max_win.mp3',
	'sfx_mystery_open.mp3',
	'sfx_payline_complete.mp3',
	'sfx_payline_draw.mp3',
	'sfx_rejump.mp3',
	'sfx_scatter_land.mp3',
	'sfx_scatter_trigger.mp3',
	'sfx_thermal_lift.mp3',
	'sfx_tier_upgrade.mp3',
	'sfx_token_reveal.mp3',
	'sfx_wind_charge.mp3',
	'sfx_wind_transition.mp3',
	'sfx_wind_upgrade.mp3',
	'sfx_world_record.mp3',
	'sfx_win_background_sound.mp3',
	'slot_new_row.mp3',
	'win_coin_spawn.mp3',
	'win_coin_escape.mp3',
]);
const LEGACY_BASE = resolveGameAsset('/assets/audio/skyjump/sfx/legacy_v1/');
const LEGACY_TRIMMED_BASE = resolveGameAsset('/assets/audio/skyjump/sfx/legacy_trimmed/');
const EXISTING_SFX_BASE = resolveGameAsset('/assets/audio/skyjump/sfx/');

export type V2AudioStatus = 'READY' | 'REUSE' | 'OPTIONAL' | 'MISSING' | 'SILENT';

/** Catalog label only. Playback never stops a previous voice to honor this. */
type OverlapPolicy = 'allow';

type FileBinding = {
	kind: 'v2' | 'legacy' | 'existing';
	file: string;
	gain: number;
	status: V2AudioStatus;
	overlap?: OverlapPolicy;
	/**
	 * Unused by playback. Kept on UI rows so the dev panel can show the old
	 * click budget. Gameplay voices are not capped.
	 */
	maxVoices?: number;
	/**
	 * Drop a new trigger this soon after the previous one. Does not stop the
	 * voice already playing. Gameplay hooks use 0. UI hooks keep a short gap
	 * so hover/click spam does not stack identical ticks.
	 */
	minGapMs?: number;
	duck?: boolean;
	notes?: string;
};

type HookBinding =
	| FileBinding
	| { kind: 'sprite'; name: string; status: V2AudioStatus; notes?: string }
	| { kind: 'silent'; status: 'SILENT'; notes: string }
	| { kind: 'missing'; status: 'MISSING'; design: string };

type DurationMetaEntry = {
	totalSec: number;
	audibleSec: number;
	audibleEndSec: number;
	trailSec: number;
	problematicTail?: boolean;
	peakDbfs?: number;
	dir?: string;
	trimmedWav?: string;
	trimmedSec?: number;
	trimmedDir?: string;
};

export const V2_AUDIO_DURATION_META = durationMetaRaw as Record<string, DurationMetaEntry>;

/**
 * Gain hierarchy (perceived):
 * UI quietest → ordinary gameplay → features → rare → WR/MaxWin strongest.
 * Hot masters get lower gain to avoid clipping after MP3 decode.
 */
export const V2_AUDIO_CATALOG: Record<string, HookBinding> = {
	/* —— preserved UI / controls —— */
	UI_CLICK: {
		kind: 'legacy',
		file: 'ui_click.mp3',
		gain: 0.42,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 3,
		minGapMs: 35,
	},
	UI_HOVER: {
		kind: 'legacy',
		file: 'button_hover_sound.mp3',
		gain: 0.38,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 4,
		minGapMs: 40,
	},
	PANEL_OPEN: {
		kind: 'legacy',
		file: 'generic_panel_open_close.mp3',
		gain: 0.4,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 2,
		minGapMs: 50,
	},
	PANEL_CLOSE: {
		kind: 'legacy',
		file: 'generic_panel_open_close.mp3',
		gain: 0.36,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 2,
		minGapMs: 50,
	},
	BET_CONFIRM: {
		kind: 'legacy',
		file: 'bet_button_sound.mp3',
		gain: 0.48,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 2,
		minGapMs: 40,
	},
	SPIN: {
		kind: 'legacy',
		file: 'bet_button_sound.mp3',
		gain: 0.48,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 2,
		minGapMs: 40,
	},
	BET_INCREASE: {
		kind: 'legacy',
		file: 'bet_increase_sound.mp3',
		gain: 0.55,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 3,
		minGapMs: 40,
	},
	BET_DECREASE: {
		kind: 'legacy',
		file: 'bet_decrease_sound.mp3',
		gain: 0.55,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 3,
		minGapMs: 40,
	},
	REEL_START: {
		kind: 'legacy',
		file: 'slot1-5start_sound.mp3',
		gain: 0.4,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 2,
		minGapMs: 40,
	},
	REEL_STOP: {
		kind: 'legacy',
		file: 'slot1-5reveal_sound.mp3',
		gain: 0.42,
		status: 'REUSE',
		overlap: 'allow',
		maxVoices: 3,
		minGapMs: 40,
	},

	/* —— custom V2 gameplay. minGapMs 0: repeated events stay audible. —— */
	PAYLINE_DRAW: {
		kind: 'v2',
		file: 'sfx_payline_draw.mp3',
		gain: 0.48,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	PAYLINE_COMPLETE: {
		kind: 'v2',
		file: 'sfx_payline_complete.mp3',
		gain: 0.52,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	SCATTER_LAND: {
		kind: 'v2',
		file: 'sfx_scatter_land.mp3',
		gain: 0.5,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	SCATTER_TRIGGER: {
		kind: 'v2',
		file: 'sfx_scatter_trigger.mp3',
		gain: 0.68,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		duck: true,
	},
	FS_START: {
		kind: 'v2',
		file: 'sfx_free_spins_start.mp3',
		gain: 0.7,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		duck: true,
	},
	FS_RETRIGGER: {
		kind: 'v2',
		file: 'sfx_free_spins_retrigger.mp3',
		gain: 0.62,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	// Win reactions: play on top of the music and of each other (no duck, no stop).
	WIN_MINI: {
		kind: 'v2',
		file: 'sfx_win_mini.mp3',
		gain: 0.9,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	WIN_BIG: {
		kind: 'v2',
		file: 'sfx_win_background_sound.mp3', // one sound for every win screen (big win and every tier above)
		gain: 0.95,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	WIN_MEGA: {
		kind: 'v2',
		file: 'sfx_win_background_sound.mp3',
		gain: 1,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	// Reel rolling: one soft tick for every new row of symbols that enters at the top. Voices stack on themselves
	// (no stop, no gap) but the gain is low so they never drown the other sounds.
	ROW_SPAWN: {
		kind: 'v2',
		file: 'slot_new_row.mp3',
		gain: 0.3,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	// Win coins: one sound when a coin spawns behind the header, one when it leaves the screen.
	COIN_SPAWN: {
		kind: 'v2',
		file: 'win_coin_spawn.mp3',
		gain: 0.4,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	COIN_ESCAPE: {
		kind: 'v2',
		file: 'win_coin_escape.mp3',
		gain: 0.4,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	TIER_UPGRADE: {
		kind: 'v2',
		file: 'sfx_tier_upgrade.mp3',
		gain: 0.65,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	COACH: {
		kind: 'silent',
		status: 'SILENT',
		notes: 'No dedicated Coach SFX in final pack — visual-only',
	},
	MYSTERY_TRANSFORM: {
		kind: 'v2',
		file: 'sfx_mystery_open.mp3',
		gain: 0.52,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	MYSTERY_REVEAL: {
		kind: 'v2',
		file: 'sfx_mystery_open.mp3',
		gain: 0.55,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	TOKEN_REVEAL: {
		kind: 'v2',
		file: 'sfx_token_reveal.mp3',
		gain: 0.5,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		notes:
			'Canonical runtime file is sfx/v2_trimmed/sfx_token_reveal.wav. The v2 mp3 has a 1.2s silent tail (problematicTail) and is not played.',
	},
	THERMAL: {
		kind: 'v2',
		file: 'sfx_thermal_lift.mp3',
		gain: 0.5,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	GATE_UPGRADE: {
		kind: 'v2',
		file: 'sfx_gate_upgrade.mp3',
		gain: 0.55,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	JUDGE_COLLECT: {
		kind: 'v2',
		file: 'sfx_judge_collect.mp3',
		gain: 0.58,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	HEAD_JUDGE_COLLECT: {
		kind: 'v2',
		file: 'sfx_head_judge_collect.mp3',
		gain: 0.62,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		notes: 'Pass 2 uses gainScale 0.7 on that voice id only. Pass 1 stays at 1.0.',
	},
	REJUMP: {
		kind: 'v2',
		file: 'sfx_rejump.mp3',
		gain: 0.58,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	WIND_CHARGE: {
		kind: 'v2',
		file: 'sfx_wind_charge.mp3',
		gain: 0.5,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	WIND_UPGRADE: {
		kind: 'v2',
		file: 'sfx_wind_upgrade.mp3',
		gain: 0.58,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	WIND_TRANSITION: {
		kind: 'v2',
		file: 'sfx_wind_transition.mp3',
		gain: 0.35,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		notes: 'Short atmospheric accent after Wind upgrade only',
	},
	WORLD_RECORD: {
		kind: 'v2',
		file: 'sfx_world_record.mp3',
		gain: 0.72,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		duck: true,
	},
	MAX_WIN: {
		kind: 'v2',
		file: 'sfx_max_win.mp3',
		gain: 0.7,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
		duck: true,
		notes: 'Plays after WR presentation / on cap — not simultaneous with WR',
	},
	BONUS_END: {
		kind: 'v2',
		file: 'sfx_bonus_end.mp3',
		gain: 0.55,
		status: 'READY',
		overlap: 'allow',
		minGapMs: 0,
	},
	BAD_MISS: {
		kind: 'v2',
		file: 'sfx_bad_miss.mp3',
		gain: 0.35,
		status: 'OPTIONAL',
		overlap: 'allow',
		minGapMs: 0,
		notes: 'Registered only. Not called from a spin. Do not wire until the miss cue is chosen.',
	},
	BGM: {
		kind: 'existing',
		file: 'relaxed_background_music1.mp3',
		gain: 0.72,
		status: 'REUSE',
		notes: 'Playlist via skyjumpAudio — not played via this hook',
	},

	/* boardRevealStop is the only sprite alias still called (once per board). */
	boardRevealStop: { kind: 'sprite', name: SKYJUMP_SFX.weatherLock, status: 'REUSE' },
	settlement: {
		kind: 'silent',
		status: 'SILENT',
		notes: 'Avoid stacking with line/feature stings',
	},
};

export type V2AudioHook = keyof typeof V2_AUDIO_CATALOG;

export type PlayV2AudioOptions = {
	/** Catch-up / resume: never replay cosmetic history */
	catchUp?: boolean;
	/** Scale gain (e.g. Head Judge pass 2) */
	gainScale?: number;
	forcePlay?: boolean;
};

const ledger = createVoiceLedger();
const howlCache = new Map<string, Howl>();
/** Test/introspection counters (DEV + unit tests). playsBlockedPool stays at 0: voices are not stolen. */
export const v2AudioSchedulerStats = {
	playsAttempted: 0,
	playsStarted: 0,
	playsBlockedGap: 0,
	playsBlockedPool: 0,
	voicesReleasedEarly: 0,
};

export const resolveHookPlayUrl = (binding: FileBinding): string | null => {
	if (binding.kind === 'v2' && LOUNGE_SFX_FILES.has(binding.file)) {
		return `${LOUNGE_SFX_BASE}${binding.file}`;
	}
	const meta = V2_AUDIO_DURATION_META[binding.file];
	if (meta?.trimmedWav) {
		if (meta.trimmedDir === 'legacy_trimmed' || binding.kind === 'legacy') {
			return `${LEGACY_TRIMMED_BASE}${meta.trimmedWav}`;
		}
		return `${V2_TRIMMED_BASE}${meta.trimmedWav}`;
	}
	if (binding.kind === 'v2') return `${V2_BASE}${binding.file}`;
	if (binding.kind === 'legacy') return `${LEGACY_BASE}${binding.file}`;
	if (binding.kind === 'existing') {
		if (binding.file.startsWith('relaxed_background')) {
			return resolveGameAsset(`/assets/audio/skyjump/bgm/${binding.file}`);
		}
		return `${EXISTING_SFX_BASE}${binding.file}`;
	}
	return null;
};

/** Measured audible length for the dev panel. Playback is not cut to this window. */
export const resolveAudibleMs = (file: string): number => {
	const meta = V2_AUDIO_DURATION_META[file];
	if (!meta) return 600;
	const sec = meta.trimmedSec ?? meta.audibleSec ?? meta.totalSec ?? 0.6;
	return Math.max(80, Math.round(sec * 1000) + 40);
};

export const getV2HookPlaybackInfo = (hook: string) => {
	const binding = V2_AUDIO_CATALOG[hook];
	if (
		!binding ||
		binding.kind === 'silent' ||
		binding.kind === 'missing' ||
		binding.kind === 'sprite'
	) {
		return {
			hook,
			file: '—',
			gain: null as number | null,
			status: binding?.status ?? 'MISSING',
			maxVoices: 0,
			minGapMs: 0,
			totalSec: null as number | null,
			audibleSec: null as number | null,
			overlap: '—',
			url: null as string | null,
		};
	}
	const meta = V2_AUDIO_DURATION_META[binding.file];
	const overlap = binding.overlap ?? 'allow';
	return {
		hook,
		file: binding.file,
		gain: binding.gain,
		status: binding.status,
		maxVoices: binding.maxVoices ?? 0,
		minGapMs: binding.minGapMs ?? 0,
		totalSec: meta?.totalSec ?? null,
		audibleSec: meta?.trimmedSec ?? meta?.audibleSec ?? null,
		overlap,
		url: resolveHookPlayUrl(binding),
	};
};

const howlPort = (howl: Howl): PolyphonicPort => ({
	play: () => howl.play() as number,
	volume: (gain, id) => {
		howl.volume(gain, id);
	},
	onEnd: (id, fn) => {
		howl.once('end', () => fn(), id);
	},
});

const portForUrl = (url: string): PolyphonicPort => {
	let howl = howlCache.get(url);
	if (!howl) {
		howl = new Howl({ src: [url], preload: true, volume: 1 });
		howlCache.set(url, howl);
	}
	return howlPort(howl);
};

const playLocal = (hook: string, url: string, gain: number, minGapMs: number) => {
	v2AudioSchedulerStats.playsAttempted += 1;
	const volume = Math.max(0, Math.min(1, stateSoundDerived.volumeSoundEffect() * gain));
	if (volume <= 0.001) return false;

	const result = startPolyphonicVoice({
		hook,
		port: portForUrl(url),
		gain: volume,
		minGapMs,
		now: Date.now(),
		ledger,
	});
	if (result === 'blocked-gap') {
		v2AudioSchedulerStats.playsBlockedGap += 1;
		return false;
	}
	if (result === 'started') v2AudioSchedulerStats.playsStarted += 1;
	return result === 'started';
};

/** @deprecated alias — prefer V2_AUDIO_CATALOG */
export const V2_AUDIO_HOOKS = Object.fromEntries(
	Object.entries(V2_AUDIO_CATALOG)
		.filter(([, b]) => b.kind === 'sprite')
		.map(([k, b]) => [k, (b as Extract<HookBinding, { kind: 'sprite' }>).name]),
) as Record<string, string>;

export const playV2AudioHook = (
	hook: V2AudioHook | string,
	opts: PlayV2AudioOptions | boolean = {},
) => {
	try {
		const options: PlayV2AudioOptions =
			typeof opts === 'boolean' ? { forcePlay: opts } : (opts ?? {});
		if (options.catchUp) return;

		const binding = V2_AUDIO_CATALOG[hook];
		if (!binding || binding.kind === 'missing' || binding.kind === 'silent') return;

		if (binding.kind === 'sprite') {
			eventEmitter.broadcast({
				type: 'soundOnce',
				name: binding.name as never,
				forcePlay: options.forcePlay !== false,
			});
			return;
		}

		const url = resolveHookPlayUrl(binding);
		if (!url || url.startsWith('http:') || url.startsWith('https:')) return;

		const gain = binding.gain * (options.gainScale ?? 1);
		if (binding.duck) softDuckSkyJumpBgm(0.38, 1100);
		playLocal(hook, url, gain, binding.minGapMs ?? 0);
	} catch {
		/* never crash */
	}
};

/**
 * DEV/test helper: fire N triggers with logical interval (rewinds lastPlay clock).
 * Does not sleep — deterministic scheduler stress without wall-clock waits.
 */
export const simulateRapidHook = (hook: string, count: number, intervalMs: number) => {
	const before = v2AudioSchedulerStats.playsStarted;
	const blockedBefore =
		v2AudioSchedulerStats.playsBlockedGap + v2AudioSchedulerStats.playsBlockedPool;
	for (let i = 0; i < count; i += 1) {
		if (i > 0 && intervalMs > 0) {
			const last = ledger.lastPlayAt.get(hook) ?? Date.now();
			ledger.lastPlayAt.set(hook, last - intervalMs);
		}
		playV2AudioHook(hook, { catchUp: false });
	}
	return {
		started: v2AudioSchedulerStats.playsStarted - before,
		blocked:
			v2AudioSchedulerStats.playsBlockedGap +
			v2AudioSchedulerStats.playsBlockedPool -
			blockedBefore,
	};
};

export const resetV2AudioSchedulerForTests = () => {
	ledger.lastPlayAt.clear();
	ledger.activeIds.clear();
	v2AudioSchedulerStats.playsAttempted = 0;
	v2AudioSchedulerStats.playsStarted = 0;
	v2AudioSchedulerStats.playsBlockedGap = 0;
	v2AudioSchedulerStats.playsBlockedPool = 0;
	v2AudioSchedulerStats.voicesReleasedEarly = 0;
};

export const getActiveVoiceCount = (hook: string) => ledger.activeIds.get(hook)?.length ?? 0;

export const listMissingV2AudioHooks = () =>
	Object.entries(V2_AUDIO_CATALOG)
		.filter(([, b]) => b.kind === 'missing')
		.map(([hook, b]) => ({
			hook,
			design: (b as Extract<HookBinding, { kind: 'missing' }>).design,
		}));

export const listReadyCustomFiles = () =>
	[
		...new Set(
			Object.values(V2_AUDIO_CATALOG)
				.filter((b): b is FileBinding => b.kind === 'v2')
				.map((b) => b.file),
		),
	].sort();

export const listProblematicSilentTails = () =>
	Object.entries(V2_AUDIO_DURATION_META)
		.filter(([, m]) => m.problematicTail)
		.map(([file, m]) => ({
			file,
			totalSec: m.totalSec,
			audibleSec: m.audibleSec,
			trailSec: m.trailSec,
			trimmed: Boolean(m.trimmedWav),
		}));
