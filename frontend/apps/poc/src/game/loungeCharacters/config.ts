/**
 * Midnight Lounge character animation V2: ids, mapping and tuning.
 *
 * Source packages are the 14 spritesheet ZIPs (kept outside the repo). They are
 * converted by `tools/midnight-lounge/build-character-anims.py` into one
 * `<id>.pack` per animation plus `manifest.json`. Nothing here is derived from
 * game math: win categories come from the existing celebration tiers.
 */
import { resolveGameAsset } from '../resolveGameAsset';

export type CharacterId = 'woman' | 'bartender';
export type WinCategory = 'mini' | 'big' | 'mega';

/** Higher wins pre-empt lower ones. Equal or lower while a win plays is ignored. */
export const WIN_PRIORITY: Record<WinCategory, number> = { mini: 1, big: 2, mega: 3 };

export type CharacterAnimationSet = {
	idle: string;
	variations: string[];
	wins: Record<WinCategory, string>;
};

export const CHARACTER_ANIMATIONS: Record<CharacterId, CharacterAnimationSet> = {
	woman: {
		idle: 'woman_idle',
		// `woman_idle_4` (extra interruption) is switched off: its pack stays in the repo and the manifest,
		// add it back here to play it again.
		variations: ['woman_idle_alt', 'woman_idle_1', 'woman_idle_2', 'woman_idle_3'],
		// No separate big-win clips: every win category plays the win clip.
			wins: { mini: 'woman_mini_win', big: 'woman_mini_win', mega: 'woman_mini_win' },
	},
	bartender: {
		idle: 'bartender_idle',
		// One interruption (a one-shot that returns to the main idle).
		variations: ['bartender_idle_1'],
		// No separate big-win clips: every win category plays the win clip.
		wins: { mini: 'bartender_mini_win', big: 'bartender_mini_win', mega: 'bartender_mini_win' },
	},
};

/**
 * OLD VERSION clips: the woman's clips that still come from the original 562x748 export because no
 * upscaled (1108x1480) source exists yet. Listed so they are easy to find during manual tests and to
 * drop or replace later (swap the zip in tools/midnight-lounge/build-character-anims.py `MAP`, then
 * delete the id here). Nothing reads this at runtime except the dev warning in `createCharacter`.
 */
export const OLD_VERSION_CLIPS: readonly string[] = [];

/** Playback speed per clip (default 1): the woman's extra interruption runs 33 % faster. */
export const CLIP_RATE: Record<string, number> = { woman_idle_4: 1.33 };

/** Every id this character can ever play. */
export const animationIdsFor = (id: CharacterId): string[] => {
	const set = CHARACTER_ANIMATIONS[id];
	return [...new Set([set.idle, ...set.variations, ...Object.values(set.wins)])];
};

export type CharacterTuning = {
	/** Random gap between idle variations (ms). Timing is data, not code. */
	idleVariationMinMs: number;
	idleVariationMaxMs: number;
	/**
	 * When set, the default idle loops this many whole times (random in range)
	 * before a variation, instead of using the time window above.
	 */
	idleLoopsMin?: number;
	idleLoopsMax?: number;
	/** Frames dropped from the start / end of every clip (30 fps: 3 frames = 0.1 s). */
	trimHeadFrames: number;
	trimTailFrames: number;
	/** Win clips (`*_win`) drop at least this many leading frames (3 = 0.1 s at 30 fps). */
	winTrimHeadFrames?: number;
	/** Relative pick weight per variation id (default 1). Lets one variation be rarer. */
	variationWeights?: Record<string, number>;
	/** The next variation's pack is fetched this long before it plays. */
	variationPrefetchLeadMs: number;
	/**
	 * Max compressed packs kept in memory per character (idle + next variation +
	 * the win clips that were used). Each is 5-12 MB; decoded frames are separate.
	 */
	maxPacks: number;
	/** Decoded ImageBitmaps kept ahead of the playhead. */
	decodeAhead: number;
	/** Frames decoded before a clip may start (first-frame guarantee). */
	startBuffer: number;
};

export const CHARACTER_TUNING: Record<CharacterId, CharacterTuning> = {
	woman: {
		idleVariationMinMs: 15_000,
		idleVariationMaxMs: 30_000,
		variationPrefetchLeadMs: 10_000,
		idleLoopsMin: 1,
		idleLoopsMax: 4,
		// 0.2 s off each end (30 fps): 0.1 s from the earlier pass plus 0.1 s more.
		trimHeadFrames: 6,
		trimTailFrames: 6,
		winTrimHeadFrames: 6,
		// All six woman packs stay in memory (9 MB each): an evicted pack would be downloaded again.
		maxPacks: 7,
		decodeAhead: 18,
		startBuffer: 6,
	},
	bartender: {
		// Main idle plays 1-2 whole loops (5-10 s), then a variation: interruptions are frequent.
		// The time window below is only the fallback when no loop counts are set.
		idleLoopsMin: 1,
		idleLoopsMax: 2,
		idleVariationMinMs: 15_000,
		idleVariationMaxMs: 30_000,
		variationPrefetchLeadMs: 10_000,
		// 0.1 s off each end of every bartender clip.
		trimHeadFrames: 3,
		trimTailFrames: 3,
		winTrimHeadFrames: 3,
		maxPacks: 4,
		decodeAhead: 18,
		startBuffer: 6,
	},
};

/**
 * Where each character stands on the 1280x720 scene. Values are fractions of
 * the play area so the existing responsive scaling is kept.
 * - `heightFrac`: character frame height / play height.
 * - `centerXFrac`: frame center X / play width.
 * - `bottomFrac`: frame bottom Y / play height (may exceed 1 to bleed off-screen;
 *   the frames carry transparent padding under the feet).
 */
export type CharacterPlacement = {
	heightFrac: number;
	centerXFrac: number;
	bottomFrac: number;
	/** Hide this fraction of the frame at the bottom (legs behind furniture). */
	clipBottomFrac?: number;
};

export const CHARACTER_PLACEMENT: Record<CharacterId, CharacterPlacement> = {
	woman: { heightFrac: 0.606, centerXFrac: 0.8815, bottomFrac: 0.995 },
	// Placed from the first animation frame: the bartender's drink stops at the slot's left edge (his
	// tray may reach over it); the woman's foot may reach over the slot's right edge, her face never.
	bartender: { heightFrac: 0.731, centerXFrac: 0.143, bottomFrac: 0.97 },
};

/** Source frame size per character (bartender V3 is 562x748, woman 554x740). */
export const CHARACTER_FRAME: Record<CharacterId, { w: number; h: number }> = {
	woman: { w: 554, h: 740 },
	bartender: { w: 562, h: 748 },
};

export const CHARACTER_BASE_URL = 'assets/midnight-lounge/characters';
export const manifestUrl = () => resolveGameAsset(`${CHARACTER_BASE_URL}/manifest.json`);
export const packUrl = (file: string) => resolveGameAsset(`${CHARACTER_BASE_URL}/${file}`);

export type PackManifestEntry = {
	file: string;
	frames: number;
	/** Frame size of this clip (clips of one character may differ; all share the 3:4 aspect). */
	w?: number;
	h?: number;
	fps: number;
	durationMs: number;
	loop: boolean;
	offsets: number[];
	sizes: number[];
	bytes: number;
	/** Packs above ~90 MB are stored as several files (GitHub's 100 MiB limit); concatenated they are `file`. */
	parts?: { file: string; bytes: number }[];
};

export type PackManifest = {
	version: number;
	frame: { w: number; h: number };
	/** Per character frame size (bartender V3 differs from the woman). */
	frames?: Record<string, { w: number; h: number }>;
	animations: Record<string, PackManifestEntry>;
};

/**
 * Looping scene props that reuse the character player (animated plants, the bodyguard).
 * `bodyguard`: 0.1 s trimmed from the start and the end of the loop.
 */
export type PropId = 'plant' | 'guard';
export const PROP_ANIMATION: Record<PropId, string> = { plant: 'plant_loop', guard: 'guard_loop' };
export const PROP_FRAME: Record<PropId, { w: number; h: number }> = {
	plant: { w: 562, h: 748 },
	guard: { w: 488, h: 862 },
};
export const PROP_TUNING: Record<PropId, CharacterTuning> = {
	plant: {
		idleVariationMinMs: 0,
		idleVariationMaxMs: 0,
		variationPrefetchLeadMs: 0,
		trimHeadFrames: 0,
		trimTailFrames: 0,
		maxPacks: 2,
		decodeAhead: 14,
		startBuffer: 4,
	},
	guard: {
		idleVariationMinMs: 0,
		idleVariationMaxMs: 0,
		variationPrefetchLeadMs: 0,
		trimHeadFrames: 3,
		trimTailFrames: 3,
		maxPacks: 2,
		decodeAhead: 14,
		startBuffer: 4,
	},
};
