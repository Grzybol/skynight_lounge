import { CHARACTER_TUNING, OLD_VERSION_CLIPS, type CharacterId } from './config';
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
	const store = new FramePackStore(
		tuning.maxPacks,
		() => controller?.pinnedIds() ?? new Set(),
		// The characters stand behind the start screen: their clips load after its own pieces.
		'low',
	);
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

if (import.meta.env.DEV && OLD_VERSION_CLIPS.length) {
	console.info(
		'[lounge-characters] woman clips still on the ORIGINAL (old, 562x748) export:',
		OLD_VERSION_CLIPS.join(', '),
	);
}
