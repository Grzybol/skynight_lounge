import { CHARACTER_TUNING, type CharacterId } from './config';
import { CharacterAnimationPlayer } from './CharacterAnimationPlayer';
import { CharacterController, type ControllerOptions } from './CharacterController';
import { FramePackStore } from './framePackStore';

export type CharacterHandle = {
	id: CharacterId;
	controller: CharacterController;
	player: CharacterAnimationPlayer;
	store: FramePackStore;
	destroy: () => void;
};

/** Wire canvas -> pack store -> player -> controller for one character. */
export const createCharacter = (
	id: CharacterId,
	canvas: HTMLCanvasElement,
	opts: ControllerOptions = {},
): CharacterHandle => {
	const tuning = CHARACTER_TUNING[id];
	let controller: CharacterController | null = null;
	const store = new FramePackStore(tuning.maxPacks, () => controller?.pinnedIds() ?? new Set());
	const player = new CharacterAnimationPlayer(canvas, store, tuning);
	controller = new CharacterController(id, player, opts);
	return {
		id,
		controller,
		player,
		store,
		destroy: () => {
			controller?.destroy();
			store.dispose();
		},
	};
};

/** Dev-only registry used by the QA inspector. */
export const devRegistry = new Map<CharacterId, CharacterHandle>();
