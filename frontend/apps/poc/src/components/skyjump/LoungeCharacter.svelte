<script lang="ts">
	import {
		CHARACTER_FRAME,
		CHARACTER_PLACEMENT,
		type CharacterId,
		type WinCategory,
	} from '../../game/loungeCharacters/config';
	import { createCharacter, devRegistry } from '../../game/loungeCharacters/createCharacter';
	import { onLoungeWin } from '../../game/loungeCharacters/loungeWinCue';

	let { character, onwin }: { character: CharacterId; onwin?: (c: WinCategory | null) => void } =
		$props();

	/** Matched to the bartender's upper body (the trousers skew his whole-figure mean): luminance mean ~60, spread ~46. */
	const WOMAN_TONE = 'brightness(0.66) contrast(1.05)';

	const ASPECT = CHARACTER_FRAME[character].w / CHARACTER_FRAME[character].h;

	let canvas = $state<HTMLCanvasElement | null>(null);
	let box = $state({ left: '0px', top: '0px', width: '0px', height: '0px' });

	$effect(() => {
		const el = canvas;
		if (!el) return;
		const handle = createCharacter(character, el, {
			onState: (state) => onwin?.(state.mode === 'win' ? state.winCategory : null),
		});
		handle.controller.start();
		const unsubscribe = onLoungeWin((event) =>
			handle.controller.requestWin(event.category, { turbo: event.turbo }),
		);
		if (import.meta.env.DEV) devRegistry.set(character, handle);
		return () => {
			unsubscribe();
			if (import.meta.env.DEV && devRegistry.get(character) === handle) {
				devRegistry.delete(character);
			}
			handle.destroy();
			onwin?.(null);
		};
	});

	$effect(() => {
		const el = canvas;
		if (!el) return;
		const viewport = el.closest('.skyjump-viewport');
		if (!(viewport instanceof HTMLElement)) return;

		const place = () => {
			const css = getComputedStyle(viewport);
			const read = (name: string) => parseFloat(css.getPropertyValue(name));
			const playLeft = read('--play-left');
			const playTop = read('--play-top');
			const playW = read('--play-width');
			const playH = read('--play-height');
			if (![playLeft, playTop, playW, playH].every(Number.isFinite) || playW <= 0 || playH <= 0) {
				return;
			}
			const p = CHARACTER_PLACEMENT[character];
			const h = playH * p.heightFrac;
			const w = h * ASPECT;
			box = {
				left: `${playLeft + playW * p.centerXFrac - w / 2}px`,
				top: `${playTop + playH * p.bottomFrac - h}px`,
				width: `${w}px`,
				height: `${h}px`,
			};
		};

		place();
		const observer = new ResizeObserver(place);
		observer.observe(viewport);
		const kick = requestAnimationFrame(place);
		return () => {
			cancelAnimationFrame(kick);
			observer.disconnect();
		};
	});
</script>

<!-- width/height attrs are replaced by the player once the manifest is known. -->
<canvas
	bind:this={canvas}
	class="figure lounge-character"
	data-lounge-character={character}
	data-lounge-figure
	width={CHARACTER_FRAME[character].w}
	height={CHARACTER_FRAME[character].h}
	style:left={box.left}
	style:top={box.top}
	style:width={box.width}
	style:height={box.height}
	style:filter={character === 'woman' ? WOMAN_TONE : undefined}
	style:clip-path={CHARACTER_PLACEMENT[character].clipBottomFrac
		? `inset(0 0 ${CHARACTER_PLACEMENT[character].clipBottomFrac! * 100}% 0)`
		: undefined}
></canvas>

<style>
	/* Beats Game.svelte's `.skyjump-viewport canvas` (z-index 19, position relative). */
	:global(.skyjump-viewport canvas.lounge-character.figure) {
		position: absolute;
		/* Above the slot (board z 16, Pixi canvas z 19), below the BetUI (z 21) and every overlay. */
		z-index: 20;
		pointer-events: none;
		opacity: 0;
		transition: opacity 350ms ease-out;
	}

	:global(.skyjump-viewport canvas.lounge-character.figure[data-ready='1']) {
		opacity: 1;
	}
</style>
