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

/** Ground point inside the frame, fractions of frame width/height. */
/**
 * `hScale` keeps the artwork the same on-screen size when a clip is re-exported with a different
 * frame: layout heights were set for the first plant/guard clips (artwork 702 / 761 px tall in
 * their frames); the current clips are 556 px (plant, 748 px frame) / 737 px (guard, 862 px frame) tall.
 */
export const PROP_GROUND: Record<
	PropId | 'stanchion',
	{ ax: number; ay: number; w: number; h: number; hScale: number }
> = {
	plant: { ax: 0.480, ay: 0.870, ...PROP_FRAME.plant, hScale: 1.2626 },
	guard: { ax: 0.510, ay: 0.9234, ...PROP_FRAME.guard, hScale: 1.1237 },
	stanchion: { ax: 0.242, ay: 0.968, w: 1158, h: 1359, hScale: 1 },
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
 * Start screen. Values were read from the previous start screen (16:9, fractions of the screen)
 * and mapped into the new 4:3 stage: at 16:9 the stage shows its middle 75 % vertically, so
 * y_stage = 0.125 + 0.75 * y_screen and h_stage = 0.75 * h_screen.
 */
const fromScreen = (x: number, y: number, h: number, flip = false): PropAnchor => ({
	x,
	y: 0.125 + 0.75 * y,
	h: 0.75 * h,
	flip,
});

/**
 * The 4:3 artwork is shown through a 16:9 window: 25 % of its height is cropped. 20 % of that crop
 * is taken at the top (5 % of the height), 80 % at the bottom, so the whole sign stays visible.
 * Props are anchored to the artwork (their y was calibrated on the previous start screen), so they
 * keep their place relative to the scene whatever the window shows.
 * Keep in sync with `.stage` in MidnightLoungeIntro.svelte.
 */
export const STAGE_TOP_CROP = 0.05; // window top, as a fraction of the artwork height
export const STAGE_TOP_SHARE = 0.2;

export const INTRO_GUARD: PropAnchor = fromScreen(0.239, 0.862, 0.678);
/**
 * Pot bases sit below the bottom edge of the screen: the window shows the artwork from
 * STAGE_TOP_CROP to STAGE_TOP_CROP + 0.75, so a base at 0.83 is ~4 % of the screen below it.
 */
const PLANT_BASE_STAGE_Y = 0.83;
export const INTRO_PLANTS: PropAnchor[] = [
	{ ...fromScreen(0.01, 0, 0.7), y: PLANT_BASE_STAGE_Y },
	{ ...fromScreen(0.983, 0, 0.66, true), y: PLANT_BASE_STAGE_Y },
];

/**
 * Only the two large stanchions remain. They are pushed outwards so the gold cap at the end of
 * each rope is past the screen edge (rope end ~ 183 px from its pole at 1280 wide), and down so
 * their bases are below the bottom edge, like the plant pots.
 */
export const INTRO_STANCHIONS: PropAnchor[] = [
	{ ...fromScreen(0.1156, 0, 0.406, true), y: PLANT_BASE_STAGE_Y },
	{ ...fromScreen(0.8844, 0, 0.406), y: PLANT_BASE_STAGE_Y },
];
