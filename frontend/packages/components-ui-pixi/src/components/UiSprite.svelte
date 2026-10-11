<script lang="ts" module>
	import { Rectangle, type RectangleProps } from 'pixi-svelte';

	import type { GardenTone } from './GardenPlate.svelte';

	export type Props = RectangleProps & {
		gardenTone?: GardenTone;
		hovered?: boolean;
		pressed?: boolean;
	};
</script>

<script lang="ts">
	import { stateUi } from 'state-shared';

	import GardenPlate from './GardenPlate.svelte';

	const { gardenTone, hovered = false, pressed = false, ...rectProps }: Props = $props();

	const minerTheme = $derived(stateUi.config.theme === 'miner');
	const gardenTheme = $derived(stateUi.config.theme === 'garden');
	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');
	const useGardenPlate = $derived(gardenTheme && (rectProps.borderWidth ?? 3) !== 0);
</script>

{#if useGardenPlate}
	<GardenPlate
		x={rectProps.x}
		y={rectProps.y}
		width={rectProps.width}
		height={rectProps.height}
		anchor={rectProps.anchor}
		alpha={rectProps.alpha}
		zIndex={rectProps.zIndex}
		tone={gardenTone ?? 'leaf'}
		{hovered}
		{pressed}
	/>
{:else}
	<Rectangle
		borderRadius={skyjumpTheme ? 18 : gardenTheme ? 16 : minerTheme ? 28 : 50}
		backgroundColor={skyjumpTheme
			? 0x05162b
			: gardenTheme
				? 0x2a4f35
				: minerTheme
					? 0x321b39
					: undefined}
		borderColor={skyjumpTheme
			? 0x65c8ff
			: gardenTheme
				? 0xc9a24d
				: minerTheme
					? 0xe7a64b
					: undefined}
		borderWidth={skyjumpTheme ? 2 : gardenTheme ? 3 : minerTheme ? 6 : undefined}
		{...rectProps}
	/>
{/if}
