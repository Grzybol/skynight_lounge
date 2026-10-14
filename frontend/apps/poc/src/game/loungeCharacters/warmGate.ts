/**
 * Background downloads (character variations, rolling symbols, tier tiles) wait for this gate, so that on a slow
 * connection the start screen (its background, bodyguard, plants and the idle clips) gets the whole line first.
 * The intro opens it when the player presses continue; a timer opens it anyway for builds without the intro.
 */
let open: () => void = () => {};
export const warmGate: Promise<void> = new Promise((resolve) => {
	open = resolve;
});
export const openWarmGate = () => open();

if (typeof window !== 'undefined') {
	// Safety net (dev routes without the intro).
	window.setTimeout(openWarmGate, 60_000);
}
