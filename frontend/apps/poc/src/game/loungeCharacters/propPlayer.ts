import { PROP_ANIMATION, PROP_TUNING, type PropId } from './config';
import { CharacterAnimationPlayer } from './CharacterAnimationPlayer';
import { FramePackStore } from './framePackStore';

/**
 * One compressed-pack cache for every prop instance: the two plants on the start screen and the
 * two in the room decode their frames separately but download the pack once.
 */
const store = new FramePackStore(3, () => new Set(Object.values(PROP_ANIMATION)), 'high');

/** Playback speed per prop: the plants sway at half speed (5 s clip -> 10 s). */
export const PROP_RATE: Record<PropId, number> = { plant: 0.5, guard: 1 };

export const createPropPlayer = (
	id: PropId,
	canvas: HTMLCanvasElement,
	rate = PROP_RATE[id],
	startOffsetMs = 0,
) => {
	const player = new CharacterAnimationPlayer(canvas, store, PROP_TUNING[id]);
	return {
		player,
		start: () => player.play(PROP_ANIMATION[id], { loop: true, rate, startOffsetMs }),
	};
};
