/** Offline-safe display / UI fonts for Pixi + DOM (local woff2, Phase typography). */
export const SKYJUMP_DISPLAY_FONT = 'SkyjumpDisplay';
export const SKYJUMP_UI_FONT = 'SkyjumpUI';

/** @deprecated use SKYJUMP_UI_FONT — kept for garden gold helpers that still need a stack */
export const SKYJUMP_UI_FONT_STACK =
	"'SkyjumpUI', 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif";

export const gardenGoldTextStyle = ({
	fontSize,
	letterSpacing = 0,
	align = 'center',
	display = false,
}: {
	fontSize: number;
	letterSpacing?: number;
	align?: 'left' | 'center' | 'right';
	/** Use SkyjumpDisplay for large titles; keep false for numeric / body UI. */
	display?: boolean;
}) => ({
	fontFamily: display ? SKYJUMP_DISPLAY_FONT : SKYJUMP_UI_FONT,
	fontSize,
	fontWeight: '700' as const,
	letterSpacing,
	align,
	fill: 0xffd36b,
	stroke: {
		color: 0x294221,
		width: Math.max(3, fontSize * 0.075),
	},
});
