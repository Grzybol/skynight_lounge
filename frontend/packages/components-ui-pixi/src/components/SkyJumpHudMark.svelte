<script lang="ts">
	import { Graphics, type GraphicsProps } from 'pixi-svelte';

	type Props = {
		kind: 'gift' | 'bolt' | 'loop' | 'flag-en' | 'flag-pl';
		color?: number;
		size?: number;
		x?: number;
		y?: number;
	};

	const { kind, color = 0xffe083, size = 18, x = 0, y = 0 }: Props = $props();

	const draw = $derived((graphics: Parameters<GraphicsProps['draw']>[0]) => {
		const s = size;
		if (kind === 'flag-pl') {
			graphics.roundRect(0, s * 0.12, s, s * 0.76, 2);
			graphics.fill({ color: 0xf4faff });
			graphics.rect(0, s * 0.5, s, s * 0.38);
			graphics.fill({ color: 0xdc1f26 });
			graphics.roundRect(0, s * 0.12, s, s * 0.76, 2);
			graphics.stroke({ color: 0x1a2740, width: 1.2, alpha: 0.55 });
			return;
		}

		if (kind === 'flag-en') {
			graphics.roundRect(0, s * 0.12, s, s * 0.76, 2);
			graphics.fill({ color: 0x1d4e89 });
			graphics.rect(s * 0.42, s * 0.12, s * 0.16, s * 0.76);
			graphics.fill({ color: 0xf4faff });
			graphics.rect(0, s * 0.42, s, s * 0.16);
			graphics.fill({ color: 0xf4faff });
			graphics.rect(s * 0.46, s * 0.12, s * 0.08, s * 0.76);
			graphics.fill({ color: 0xc8102e });
			graphics.rect(0, s * 0.46, s, s * 0.08);
			graphics.fill({ color: 0xc8102e });
			graphics.roundRect(0, s * 0.12, s, s * 0.76, 2);
			graphics.stroke({ color: 0x1a2740, width: 1.2, alpha: 0.55 });
			return;
		}

		if (kind === 'bolt') {
			graphics.moveTo(s * 0.46, 0);
			graphics.lineTo(s * 0.16, s * 0.54);
			graphics.lineTo(s * 0.46, s * 0.54);
			graphics.lineTo(s * 0.3, s);
			graphics.lineTo(s * 0.86, s * 0.4);
			graphics.lineTo(s * 0.52, s * 0.4);
			graphics.closePath();
			graphics.fill({ color });
			return;
		}

		if (kind === 'loop') {
			/** Compact autoplay / repeat mark — two circular arrows. */
			const cx = s * 0.5;
			const cy = s * 0.5;
			const r = s * 0.28;
			graphics.arc(cx, cy, r, -Math.PI * 0.85, Math.PI * 0.35);
			graphics.stroke({ color, width: Math.max(1.6, s * 0.11), cap: 'round' });
			graphics.arc(cx, cy, r, Math.PI * 0.15, Math.PI * 1.35);
			graphics.stroke({ color, width: Math.max(1.6, s * 0.11), cap: 'round' });
			// arrow heads
			graphics.moveTo(cx + r * 0.55, cy - r * 0.95);
			graphics.lineTo(cx + r * 1.05, cy - r * 0.35);
			graphics.lineTo(cx + r * 0.25, cy - r * 0.45);
			graphics.closePath();
			graphics.fill({ color });
			graphics.moveTo(cx - r * 0.55, cy + r * 0.95);
			graphics.lineTo(cx - r * 1.05, cy + r * 0.35);
			graphics.lineTo(cx - r * 0.25, cy + r * 0.45);
			graphics.closePath();
			graphics.fill({ color });
			return;
		}

		const box = s * 0.62;
		const bx = (s - box) * 0.5;
		const by = s * 0.34;
		graphics.roundRect(bx, by, box, box * 0.86, 2.4);
		graphics.fill({ color });
		graphics.rect(s * 0.46, by, s * 0.08, box * 0.86);
		graphics.fill({ color: 0x1a1208, alpha: 0.32 });
		graphics.roundRect(bx - 1, by - s * 0.06, box + 2, s * 0.16, 2);
		graphics.fill({ color });
		graphics.ellipse(s * 0.36, by, s * 0.15, s * 0.11);
		graphics.fill({ color });
		graphics.ellipse(s * 0.64, by, s * 0.15, s * 0.11);
		graphics.fill({ color });
		graphics.circle(s * 0.5, by + 1, s * 0.07);
		graphics.fill({ color: 0xfff3c8 });
	});
</script>

<Graphics {x} {y} pivot={{ x: size / 2, y: size / 2 }} {draw} />
