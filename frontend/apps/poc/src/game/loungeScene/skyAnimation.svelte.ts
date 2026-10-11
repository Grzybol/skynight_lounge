/**
 * Third background plane (sky): two six-frame animations that alternate.
 *
 * One animation plays forward (0.2 s), then in reverse (0.2 s), and the sky rests on its first
 * frame for 5-15 s; then the other animation does the same, and so on. The two clips are not
 * pixel-identical on their first frame, so the switch is a short cross-fade.
 * The state is shared: every mounted scene (the room and the lifted win plate) shows the same frame.
 */
import { resolveGameAsset } from '../resolveGameAsset';

export const SKY_FRAME_COUNT = 6;
export const SKY_DIRECTION_MS = 200;
export const SKY_HOLD_MIN_MS = 5_000;
export const SKY_HOLD_MAX_MS = 15_000;
export const SKY_CROSSFADE_MS = 400;
const FIRST_START_MS = 1_000;

export type SkyClip = 1 | 2;

export const skyFrameUrl = (clip: SkyClip, frame: number) =>
	resolveGameAsset(`assets/midnight-lounge/scene/background_3_animation_${clip}_frame_${frame + 1}.png`);

export const skyState = $state<{ clip: SkyClip; frame: number; fading: SkyClip | null }>({
	clip: 1,
	frame: 0,
	fading: null,
});

let users = 0;
let timer: ReturnType<typeof setTimeout> | null = null;

const wait = (ms: number, then: () => void) => {
	timer = setTimeout(then, ms);
};

const hold = () => Math.round(SKY_HOLD_MIN_MS + Math.random() * (SKY_HOLD_MAX_MS - SKY_HOLD_MIN_MS));

/** Forward 0..5, then reverse 5..0, one frame every SKY_DIRECTION_MS / 6. */
const stepMs = SKY_DIRECTION_MS / SKY_FRAME_COUNT;
const SEQUENCE = [
	...Array.from({ length: SKY_FRAME_COUNT }, (_, i) => i),
	...Array.from({ length: SKY_FRAME_COUNT }, (_, i) => SKY_FRAME_COUNT - 1 - i),
];

const playClip = (clip: SkyClip) => {
	let index = 0;
	skyState.clip = clip;
	const step = () => {
		skyState.frame = SEQUENCE[index];
		index += 1;
		if (index < SEQUENCE.length) wait(stepMs, step);
		else wait(hold(), () => switchClip(clip === 1 ? 2 : 1));
	};
	step();
};

const switchClip = (next: SkyClip) => {
	skyState.fading = skyState.clip;
	skyState.clip = next;
	skyState.frame = 0;
	wait(SKY_CROSSFADE_MS, () => {
		skyState.fading = null;
		playClip(next);
	});
};

const start = () => {
	skyState.clip = 1;
	skyState.frame = 0;
	skyState.fading = null;
	wait(FIRST_START_MS, () => playClip(1));
};

/** Starts the shared animation for the first user, stops it after the last one releases. */
export const acquireSky = () => {
	users += 1;
	if (users === 1) start();
	return () => {
		users -= 1;
		if (users === 0 && timer) {
			clearTimeout(timer);
			timer = null;
		}
	};
};
