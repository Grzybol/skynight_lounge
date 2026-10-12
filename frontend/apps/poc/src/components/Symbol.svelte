<script lang="ts">
	import SymbolSpine from './SymbolSpine.svelte';
	import SymbolSprite from './SymbolSprite.svelte';
	import SymbolSpriteAnimated from './SymbolSpriteAnimated.svelte';
	import SymbolWinFrame from './SymbolWinFrame.svelte';
	import { getSymbolInfo } from '../game/utils';
	import type { SymbolState, RawSymbol } from '../game/types';
	import { getContext } from '../game/context';
	import { Text } from 'pixi-svelte';
	import { gardenGoldTextStyle } from '../game/gardenTextStyle';

	type Props = {
		x?: number;
		y?: number;
		state: SymbolState;
		rawSymbol: RawSymbol;
		oncomplete?: () => void;
		loop?: boolean;
	};

	const props: Props = $props();
	const context = getContext();
	const symbolInfo = $derived(getSymbolInfo({ rawSymbol: props.rawSymbol, state: props.state }));
	const isSprite = $derived(symbolInfo.type === 'sprite');
	const isAnimatedSprite = $derived(symbolInfo.type === 'animatedSprite');
	const showWinFrame = $derived(
		props.state === 'win' && !['S', 'W'].includes(props.rawSymbol.name),
	);
</script>

{#if showWinFrame}
	<SymbolWinFrame x={props.x} y={props.y} />
{/if}

{#if isSprite}
	<SymbolSprite {symbolInfo} x={props.x} y={props.y} oncomplete={props.oncomplete} />
{:else if isAnimatedSprite}
	<SymbolSpriteAnimated
		{symbolInfo}
		x={props.x}
		y={props.y}
		oncomplete={props.oncomplete}
		loop={props.loop}
	/>
{:else}
	<SymbolSpine
		loop={props.loop}
		{symbolInfo}
		x={props.x}
		y={props.y}
		listener={{
			complete: props.oncomplete,
			event: (_, event) => {
				if (event.data?.name === 'wildExplode') {
					context.eventEmitter?.broadcast({ type: 'soundOnce', name: 'sfx_wild_explode' });
				}
			},
		}}
	/>
{/if}

{#if props.rawSymbol.multiplier}
	<Text
		anchor={0.5}
		x={props.x}
		y={props.y}
		text={`${props.rawSymbol.multiplier}X`}
		style={gardenGoldTextStyle({ fontSize: 50 })}
	/>
{/if}
