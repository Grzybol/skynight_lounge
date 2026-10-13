/**
 * One call per announced win category: both characters react (queued, see CharacterController)
 * and the matching win sound plays on top of the music and of any sound still playing.
 * Kept out of loungeWinCue.ts so that file stays free of audio imports (it is unit tested in node).
 */
import { playV2AudioHook } from '../skyjump_v2/audio';
import type { WinCategory } from './config';
import { emitLoungeWin, type LoungeWinEvent } from './loungeWinCue';

const SFX_HOOK: Record<WinCategory, string> = {
	mini: 'WIN_MINI',
	big: 'WIN_BIG',
	mega: 'WIN_MEGA',
};

/**
 * Big win and every tier above share one 5 s sound. The counter announces big and then mega during
 * one celebration, so the sound starts once per window instead of stacking.
 */
const BIG_SOUND_WINDOW_MS = 5000;
let lastBigSoundAt = -Infinity;

export const reactToWin = (
	category: WinCategory,
	tier: LoungeWinEvent['tier'],
	opts: { turbo?: boolean } = {},
) => {
	emitLoungeWin(category, tier, opts);
	if (category !== 'mini') {
		const now = performance.now();
		if (now - lastBigSoundAt < BIG_SOUND_WINDOW_MS) return;
		lastBigSoundAt = now;
	}
	playV2AudioHook(SFX_HOOK[category]);
};
