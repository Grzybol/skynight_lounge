/**
 * Second background plane (the houses): a pool of equally framed images. Every 10-20 s one random
 * other image is cross-faded in; all share the same placement, so only the artwork changes.
 * State is shared by every mounted scene (the room and the lifted win plate).
 */
import { resolveGameAsset } from '../resolveGameAsset';

/** Frame 1 is the original `background_2_static.png`; 2..14 are the extra frames. */
const EXTRA_FRAMES = 13;
export const BUILDINGS_POOL: string[] = [
	resolveGameAsset('assets/midnight-lounge/scene/background_2_static.png'),
	...Array.from({ length: EXTRA_FRAMES }, (_, i) =>
		resolveGameAsset(`assets/midnight-lounge/scene/background_2_static_frame_${i + 2}.png`),
	),
];

export const BUILDINGS_MIN_MS = 10_000;
export const BUILDINGS_MAX_MS = 20_000;
export const BUILDINGS_FADE_MS = 1_200;

/** Two stacked layers; `front` says which one is visible. */
export const buildingsState = $state<{ a: string; b: string; front: 'a' | 'b' }>({
	a: BUILDINGS_POOL[0],
	b: BUILDINGS_POOL[0],
	front: 'a',
});

let users = 0;
let timer: ReturnType<typeof setTimeout> | null = null;

const wait = (ms: number, fn: () => void) => {
	timer = setTimeout(fn, ms);
};

const pickNext = () => {
	const current = buildingsState[buildingsState.front];
	const others = BUILDINGS_POOL.filter((url) => url !== current);
	return others[Math.floor(Math.random() * others.length)];
};

const step = () => {
	const next = pickNext();
	const img = new Image();
	img.src = next;
	const flip = () => {
		const hidden = buildingsState.front === 'a' ? 'b' : 'a';
		buildingsState[hidden] = next;
		buildingsState.front = hidden;
		wait(BUILDINGS_MIN_MS + Math.random() * (BUILDINGS_MAX_MS - BUILDINGS_MIN_MS), step);
	};
	// Decode first, so the fade never shows a half-loaded image.
	void img.decode().then(flip, flip);
};

export const acquireBuildings = () => {
	users += 1;
	if (users === 1) {
		wait(BUILDINGS_MIN_MS + Math.random() * (BUILDINGS_MAX_MS - BUILDINGS_MIN_MS), step);
	}
	return () => {
		users -= 1;
		if (users === 0 && timer) {
			clearTimeout(timer);
			timer = null;
		}
	};
};
