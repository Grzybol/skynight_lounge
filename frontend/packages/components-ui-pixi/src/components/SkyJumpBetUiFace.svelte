<script lang="ts">
	import { Sprite } from 'pixi-svelte';

	type Props = {
		/** Key in `game/assets.ts` (preloaded into Pixi loadedAssets). */
		assetKey: string;
		width: number;
		height: number;
		anchor?: number | { x: number; y: number };
		alpha?: number;
		tint?: number;
	};

	const {
		assetKey,
		width,
		height,
		anchor = 0.5,
		alpha = 1,
		tint = 0xffffff,
	}: Props = $props();
</script>

<Sprite key={assetKey} {width} {height} {anchor} {alpha} {tint} />
