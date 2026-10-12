<script lang="ts">
	import { Graphics, anchorToPivot, type GraphicsProps, type PixiPoint } from 'pixi-svelte';

	export type GardenTone = 'leaf' | 'harvest' | 'label' | 'active' | 'disabled' | 'win';

	type Props = {
		x?: number;
		y?: number;
		width: number;
		height: number;
		anchor?: PixiPoint;
		tone?: GardenTone;
		hovered?: boolean;
		pressed?: boolean;
		alpha?: number;
		zIndex?: number;
	};

	const {
		x = 0,
		y = 0,
		width,
		height,
		anchor = 0,
		tone = 'leaf',
		hovered = false,
		pressed = false,
		alpha,
		zIndex,
	}: Props = $props();

	const palette = $derived.by(() => {
		if (tone === 'disabled') {
			return {
				ink: 0x2a2c28,
				timber: 0x5c584f,
				timberHi: 0x7a756c,
				paint: 0x7d8278,
				paintHi: 0x9aa196,
				gold: 0x9a9178,
				bolt: 0xb0a88c,
				boltInk: 0x3a3832,
			};
		}
		if (tone === 'win') {
			return {
				ink: 0x1c120c,
				timber: 0x6e3426,
				timberHi: 0xa85a3c,
				paint: 0x8a5a12,
				paintHi: 0xf0c45c,
				gold: 0xffe08a,
				bolt: 0xf3cc72,
				boltInk: 0x3a251e,
			};
		}
		if (tone === 'harvest') {
			return {
				ink: 0x1c120c,
				timber: hovered ? 0x8a4a32 : 0x6e3426,
				timberHi: 0xa85a3c,
				paint: pressed ? 0x4e8a2e : hovered ? 0x8fbf4f : 0x6faf40,
				paintHi: 0xb7e06a,
				gold: hovered ? 0xffe08a : 0xe0b24a,
				bolt: 0xe4b15a,
				boltInk: 0x3a251e,
			};
		}
		if (tone === 'active') {
			return {
				ink: 0x1c120c,
				timber: 0x6e3426,
				timberHi: 0xa85a3c,
				paint: 0x7bb64b,
				paintHi: 0xc5e878,
				gold: 0xffe08a,
				bolt: 0xf0c56a,
				boltInk: 0x3a251e,
			};
		}
		return {
			ink: 0x1c120c,
			timber: hovered ? 0x7a3e2a : 0x6e3426,
			timberHi: 0x8a4a32,
			paint: pressed ? 0x1c3824 : hovered ? 0x3d6a45 : 0x2f5538,
			paintHi: 0x5a8a58,
			gold: hovered ? 0xf3d37a : 0xc9a24d,
			bolt: 0xd49a4c,
			boltInk: 0x3a251e,
		};
	});

	const lift = $derived(pressed ? 2 : hovered ? -2 : 0);
	const shadowY = $derived(pressed ? 3 : 7);

	const draw = $derived((graphics: Parameters<GraphicsProps['draw']>[0]) => {
		const w = width;
		const h = height;
		const p = palette;
		const r = Math.min(22, Math.min(w, h) * 0.2);
		const frame = Math.max(7, Math.min(w, h) * 0.075);
		const ly = lift;

		graphics.roundRect(3, shadowY, w, h, r);
		graphics.fill({ color: 0x0a120c, alpha: 0.42 });

		graphics.roundRect(0, ly, w, h, r);
		graphics.fill({ color: p.ink });

		graphics.roundRect(3, ly + 3, w - 6, h - 6, Math.max(4, r - 3));
		graphics.fill({ color: p.timber });

		graphics.roundRect(8, ly + 6, w - 16, Math.max(6, h * 0.16), 4);
		graphics.fill({ color: p.timberHi, alpha: 0.38 });

		const ix = frame;
		const iy = ly + frame;
		const iw = w - frame * 2;
		const ih = h - frame * 2;
		const ir = Math.max(6, r - 6);
		graphics.roundRect(ix, iy, iw, ih, ir);
		graphics.fill({ color: p.paint });

		graphics.roundRect(ix + 3, iy + 3, iw - 6, Math.max(5, ih * 0.34), Math.max(4, ir - 3));
		graphics.fill({ color: p.paintHi, alpha: 0.32 });

		graphics.roundRect(ix + 4, iy + ih * 0.68, iw - 8, Math.max(4, ih * 0.18), 4);
		graphics.fill({ color: 0x0c1a10, alpha: 0.22 });

		const grains = Math.max(2, Math.floor(ih / 28));
		for (let i = 0; i < grains; i += 1) {
			const gy = iy + 10 + (i * (ih - 20)) / grains;
			graphics.roundRect(ix + iw * 0.12, gy, iw * (i % 2 ? 0.46 : 0.58), 2, 1);
			graphics.fill({ color: 0x1c120c, alpha: 0.1 });
		}

		graphics.roundRect(ix + 1, iy + 1, iw - 2, ih - 2, ir);
		graphics.stroke({ color: p.gold, width: 2, alpha: 0.85 });

		if (Math.min(w, h) >= 52) {
			const d = Math.max(5, Math.min(w, h) * 0.055);
			const inset = Math.max(10, frame * 0.95);
			const bolts = [
				[inset, ly + inset],
				[w - inset, ly + inset],
				[inset, ly + h - inset],
				[w - inset, ly + h - inset],
			] as const;
			for (const [bx, by] of bolts) {
				graphics.circle(bx, by, d * 0.55);
				graphics.fill({ color: p.boltInk });
				graphics.circle(bx, by, d * 0.38);
				graphics.fill({ color: p.bolt });
				graphics.circle(bx - d * 0.12, by - d * 0.12, d * 0.12);
				graphics.fill({ color: 0xffe9a8, alpha: 0.8 });
				graphics.rect(bx - d * 0.22, by - d * 0.05, d * 0.44, Math.max(1.2, d * 0.1));
				graphics.fill({ color: 0x5a3825, alpha: 0.85 });
			}
		}
	});
</script>

<Graphics
	{x}
	{y}
	{alpha}
	{zIndex}
	pivot={anchorToPivot({ anchor, sizes: { width, height } })}
	{draw}
/>
