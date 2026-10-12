/** Local SkyJump font family names for Pixi Text (must match @font-face in skyjump-fonts.css). */
export const SKYJUMP_DISPLAY_FONT = 'SkyjumpDisplay';
export const SKYJUMP_UI_FONT = 'SkyjumpUI';

export const pixiFontFamily = (theme: string | undefined) =>
	theme === 'skyjump' ? SKYJUMP_UI_FONT : 'proxima-nova';

export const pixiDisplayFontFamily = (theme: string | undefined) =>
	theme === 'skyjump' ? SKYJUMP_DISPLAY_FONT : 'proxima-nova';
