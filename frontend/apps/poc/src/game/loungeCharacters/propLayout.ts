/**
 * Where the scene props stand. Every prop is placed by the point where it touches the floor:
 * `x`/`y` = that point as a fraction of its container (the play area, or the start-screen
 * stage), `h` = frame height as a fraction of the container height. `ax`/`ay` = the same
 * ground point inside the prop's own frame (measured from the artwork's alpha bounds).
 * Containers set `container-type: size`, so the helpers return `cqw` / `cqh` CSS.
 */
import type { PropId } from './config';
import { PROP_FRAME } from './config';

export type PropAnchor = { x: number; y: number; h: number; flip?: boolean };

/**
 * Ground point inside the frame, fractions of frame width/height (measured from the artwork's alpha
 * bounds). `hScale` rescales layout heights when a clip is re-exported with a different frame.
 */
export const PROP_GROUND: Record<PropId | 'stanchion', { ax: number; ay: number; w: number; h: number; hScale: number }> = {
	plant: { ax: 0.516, ay: 0.866, ...PROP_FRAME.plant, hScale: 1 },
	guard: { ax: 0.543, ay: 0.907, ...PROP_FRAME.guard, hScale: 1 },
	stanchion: { ax: 0.215, ay: 0.976, w: 1122, h: 1402, hScale: 1 },
};

export const propBox = (kind: PropId | 'stanchion', a: PropAnchor) => {
	const g = PROP_GROUND[kind];
	const h = a.h * g.hScale;
	const wCqh = h * 100 * (g.w / g.h);
	const fx = a.flip ? 1 - g.ax : g.ax;
	return {
		left: `calc(${(a.x * 100).toFixed(3)}cqw - ${fx.toFixed(4)} * ${wCqh.toFixed(3)}cqh)`,
		top: `${((a.y - g.ay * h) * 100).toFixed(3)}cqh`,
		height: `${(h * 100).toFixed(3)}cqh`,
	};
};

/**
 * Start screen. The 4:3 artwork is shown through a 16:9 window: 25 % of its height is cropped,
 * STAGE_TOP_SHARE of that crop at the top. Props are anchored to the artwork (fractions of the
 * 4:3 stage), so they keep their place relative to the scene whatever the window shows.
 * Keep in sync with `.stage` in MidnightLoungeIntro.svelte.
 */
export const STAGE_TOP_SHARE = 0.1;

/** Bodyguard: stands on the floor left of the carpet. */
export const INTRO_GUARD: PropAnchor = { x: 0.2233, y: 0.809, h: 0.688 };

/**
 * The two animated plants stand in the foreground: the left one right behind the bodyguard, the right
 * one at the foot of the right column (the painted plants in the doorway stay as they are).
 */
export const INTRO_PLANTS: PropAnchor[] = [
	{ x: 0.205, y: 0.775, h: 0.414 },
	{ x: 0.925, y: 0.775, h: 0.414, flip: true },
];

/**
 * Velvet-rope stanchion over the right plant. Its pole passes through the pot, left of the pot's centre
 * (x = the pot's highlight); the rope runs off the right edge. The base sits below the window's bottom
 * edge (0.775), so it is cut slightly.
 */
export const INTRO_STANCHION: PropAnchor = { x: 0.9136, y: 0.825, h: 0.22 };

/** Plants in the slot scene, fractions of the play area (just in front of the balustrade, behind the characters and the board). */
export const SCENE_PLANTS: PropAnchor[] = [
	{ x: 0.113, y: 0.67, h: 0.477 },
	{ x: 0.955, y: 0.67, h: 0.477, flip: true },
	// Behind the slot, half hidden by its frame (the frame's outer edges are at about 0.242 and 0.756 of the width).
	{ x: 0.247, y: 0.64, h: 0.44 },
	{ x: 0.753, y: 0.64, h: 0.44, flip: true },
];
