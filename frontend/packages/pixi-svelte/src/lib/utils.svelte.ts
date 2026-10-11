import type { PixiPoint, Sizes } from './types';

export const REM = 16;
export const MIN_CLICKABLE_SIZE = 3 * REM; // 44 x 44 is minimum clickable size

export const getPointValues = ({
	point,
	defaultValue,
}: {
	point: PixiPoint;
	defaultValue: number;
}) => {
	const finalDefaultValue = defaultValue === undefined ? 0 : defaultValue;
	if (typeof point === 'number') return [point, point];
	return [point?.x || finalDefaultValue, point?.y || finalDefaultValue];
};

export const anchorToPivot = ({ anchor, sizes }: { anchor: PixiPoint; sizes: Sizes }) => {
	const { width, height } = sizes;
	const [anchorX, anchorY] = getPointValues({ point: anchor, defaultValue: 0 });
	return { x: width * anchorX, y: height * anchorY };
};

/**
 * Detects if WebGL is enabled.
 * Inspired from http://www.browserleaks.com/webgl#howto-detect-webgl
 *
 * @return { number } -1 for not Supported,
 *										0 for disabled
 *										1 for enabled
 */
export function detectWebGL() {
	// Check for the WebGL rendering context
	if (window && !!window.WebGLRenderingContext) {
		let canvas = document.createElement('canvas'),
			names = ['webgl', 'experimental-webgl', 'moz-webgl', 'webkit-3d'],
			context = false;

		for (const i in names) {
			try {
				// @ts-ignore
				context = canvas.getContext(names[i]);
				// @ts-ignore
				if (context && typeof context.getParameter === 'function') {
					// WebGL is enabled.
					return 1;
				}
			} catch (e) {}
		}

		// WebGL is supported, but disabled.
		return 0;
	}

	// WebGL not supported.
	return -1;
}

const SKYJUMP_FONT_ASSETS: { family: string; weight: string; src: string }[] = [
	{ family: 'SkyjumpDisplay', weight: '600', src: 'assets/fonts/skyjump/oxanium-600.woff2' },
	{ family: 'SkyjumpDisplay', weight: '700', src: 'assets/fonts/skyjump/oxanium-700.woff2' },
	{ family: 'SkyjumpDisplay', weight: '800', src: 'assets/fonts/skyjump/oxanium-800.woff2' },
	{ family: 'SkyjumpUI', weight: '400', src: 'assets/fonts/skyjump/inter-400.woff2' },
	{ family: 'SkyjumpUI', weight: '500', src: 'assets/fonts/skyjump/inter-500.woff2' },
	{ family: 'SkyjumpUI', weight: '600', src: 'assets/fonts/skyjump/inter-600.woff2' },
	{ family: 'SkyjumpUI', weight: '700', src: 'assets/fonts/skyjump/inter-700.woff2' },
	// Map 800 → 700 file so Pixi weight "800" never falls back to Arial.
	{ family: 'SkyjumpUI', weight: '800', src: 'assets/fonts/skyjump/inter-700.woff2' },
];

const preloadSkyjumpFontFaces = async () => {
	if (typeof document === 'undefined' || !document.fonts) return;

	await Promise.all(
		SKYJUMP_FONT_ASSETS.map(async ({ family, weight, src }) => {
			const face = new FontFace(family, `url(${src})`, {
				style: 'normal',
				weight,
				display: 'swap',
			});
			await face.load();
			document.fonts.add(face);
		}),
	);

	await document.fonts.ready;
	await Promise.allSettled([
		document.fonts.load('400 16px SkyjumpUI'),
		document.fonts.load('600 16px SkyjumpUI'),
		document.fonts.load('700 16px SkyjumpUI'),
		document.fonts.load('800 16px SkyjumpUI'),
		document.fonts.load('600 24px SkyjumpDisplay'),
		document.fonts.load('700 24px SkyjumpDisplay'),
		document.fonts.load('800 24px SkyjumpDisplay'),
	]);
};

/**
 * Wait for local SkyJump FontFace registration before any Pixi Text is created.
 * CSS @font-face alone can race; Text then caches Arial and never repaints.
 */
export const preloadFont = () =>
	new Promise<void>((resolve) => {
		try {
			void preloadSkyjumpFontFaces().finally(() => resolve());
		} catch (error) {
			console.error(error);
			resolve();
		}
	});

export function propsSyncEffect<TProps extends object, TTarget>({
	props,
	target,
	ignore,
}: {
	props: TProps;
	target?: TTarget | (() => TTarget);
	ignore?: (keyof TProps)[];
}) {
	$effect(() => {
		// The whole thing is wrapped inside an $effect
		// and because of ”props[key]“，it will react with every single props updated.
		let targetInstance = target instanceof Function ? target() : target;
		if (targetInstance) {
			(Object.keys(props) as (keyof TProps)[])
				.filter((key) => (ignore ? !ignore.includes(key) : true))
				.forEach((key) => {
					if (props[key] !== undefined) {
						// @ts-ignore
						targetInstance[key] = props[key];
					}
				});
		}
	});
}
