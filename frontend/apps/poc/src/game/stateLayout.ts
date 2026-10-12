import { createLayout } from 'utils-layout';

export const { stateLayout, stateLayoutDerived } = createLayout({
	backgroundRatio: {
		normal: 2039 / 1000,
		portrait: 1242 / 2208,
	},
	mainSizesMap: {
		// V2 design canvas (matches skyjump_v2_config.layout.desktopLogical). Still scales to any window.
		desktop: { width: 1280, height: 720 },
		tablet: { width: 1000, height: 1000 },
		landscape: { width: 1280, height: 720 },
		portrait: { width: 720, height: 1280 },
	},
});
