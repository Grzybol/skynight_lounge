/** Live-preview Stake-like stage constants (DEV presentation QA only). */

export const LIVE_PREVIEW_LOGICAL = { width: 1280, height: 720 } as const;

export const LIVE_PREVIEW_PRESETS = [
	{ id: '1280x720', width: 1280, height: 720, label: '1280×720 (primary)' },
	{ id: '768x432', width: 768, height: 432, label: '768×432' },
	{ id: '640x360', width: 640, height: 360, label: '640×360' },
	{ id: '480x270', width: 480, height: 270, label: '480×270' },
	{ id: '400x225', width: 400, height: 225, label: '400×225' },
	{ id: 'fit', width: 0, height: 0, label: 'Fit browser' },
] as const;

export type LivePreviewPresetId = (typeof LIVE_PREVIEW_PRESETS)[number]['id'];

export const LIVE_PREVIEW_STAGE_ATTR = 'data-skyjump-preview-stage';

/** Largest 16:9 box that fits inside availW×availH (no stretch). Never upscales past 1:1. */
export const fitStageSize = (
	availW: number,
	availH: number,
	logicalW = LIVE_PREVIEW_LOGICAL.width,
	logicalH = LIVE_PREVIEW_LOGICAL.height,
): { width: number; height: number; scale: number } => {
	const aw = Math.max(1, availW);
	const ah = Math.max(1, availH);
	const scale = Math.min(1, aw / logicalW, ah / logicalH);
	return {
		width: Math.round(logicalW * scale),
		height: Math.round(logicalH * scale),
		scale,
	};
};
