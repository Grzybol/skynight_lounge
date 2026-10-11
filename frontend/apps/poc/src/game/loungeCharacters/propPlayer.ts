import { PROP_ANIMATION, PROP_TUNING, type PropId } from './config';
import { CharacterAnimationPlayer } from './CharacterAnimationPlayer';
import { FramePackStore } from './framePackStore';

/**
 * One compressed-pack cache for every prop instance: the two plants on the start screen and the
 * two in the room decode their frames separately but download the pack once.
 */
const store = new FramePackStore(3, () => new Set(Object.values(PROP_ANIMATION)));

export const createPropPlayer = (id: PropId, canvas: HTMLCanvasElement, rate = 1) => {
	const player = new CharacterAnimationPlayer(canvas, store, PROP_TUNING[id]);
	return {
		player,
		start: () => player.play(PROP_ANIMATION[id], { loop: true, rate }),
	};
};
