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
export const PROP_GROUND: Record<PropId, { ax: number; ay: number; w: number; h: number; hScale: number }> = {
	plant: { ax: 0.516, ay: 0.866, ...PROP_FRAME.plant, hScale: 1 },
	guard: { ax: 0.543, ay: 0.907, ...PROP_FRAME.guard, hScale: 1 },
};

export const propBox = (kind: PropId, a: PropAnchor) => {
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
export const INTRO_GUARD: PropAnchor = { x: 0.2, y: 0.77, h: 0.52 };

/**
 * The two plants in the doorway are painted into the artwork; the animated plants are drawn over
 * them (slightly larger, so the painted leaves stay hidden). Pot bases at the painted pots.
 */
export const INTRO_PLANTS: PropAnchor[] = [
	{ x: 0.381, y: 0.505, h: 0.165 },
	{ x: 0.662, y: 0.505, h: 0.165, flip: true },
];

/** Plants in the slot scene, fractions of the play area (behind the characters and the board). */
export const SCENE_PLANTS: PropAnchor[] = [
	{ x: 0.035, y: 0.86, h: 0.36 },
	{ x: 0.97, y: 0.72, h: 0.3, flip: true },
];
