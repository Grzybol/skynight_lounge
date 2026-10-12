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

export const reactToWin = (
	category: WinCategory,
	tier: LoungeWinEvent['tier'],
	opts: { turbo?: boolean } = {},
) => {
	emitLoungeWin(category, tier, opts);
	playV2AudioHook(SFX_HOOK[category]);
};
