<script lang="ts" module>
	export type EmitterEventFreeSpinCounter =
		| { type: 'freeSpinCounterShow' }
		| { type: 'freeSpinCounterHide' }
		| { type: 'freeSpinCounterUpdate'; current?: number; total?: number };
</script>

<script lang="ts">
	import { MainContainer } from 'components-layout';
	import { FadeContainer } from 'components-pixi';

	import { getContext } from '../game/context';
	import { SYMBOL_SIZE } from '../game/constants';
	import { Container, Rectangle, Sprite, Text } from 'pixi-svelte';
	import { gardenGoldTextStyle } from '../game/gardenTextStyle';

	const context = getContext();
	const panelWidth = $derived(SYMBOL_SIZE * 1.82);
	const panelSizes = $derived({
		width: panelWidth,
		height: panelWidth * 0.72,
	});
	const board = $derived(context.stateGameDerived.boardLayout());
	const slotScale = $derived(board.scale ?? 1);
	const scale = 1;
	const position = $derived({
		x: board.x - board.width * 0.5 * slotScale - panelSizes.width - SYMBOL_SIZE * 0.7,
		y: board.y - board.height * 0.5 * slotScale,
	});

	const fontSize = SYMBOL_SIZE * 0.25;

	let show = $state(false);
	let current = $state(0);
	let total = $state(0);

	context.eventEmitter.subscribeOnMount({
		freeSpinCounterShow: () => (show = true),
		freeSpinCounterHide: () => (show = false),
		freeSpinCounterUpdate: (emitterEvent) => {
			if (emitterEvent.current !== undefined) current = emitterEvent.current;
			if (emitterEvent.total !== undefined) total = emitterEvent.total;
		},
	});
</script>

<MainContainer>
	<FadeContainer {show} {...position} {scale}>
		<Rectangle
			{...panelSizes}
			borderRadius={36}
			backgroundColor={0x183523}
			backgroundAlpha={0.96}
			borderColor={0x8fce5a}
			borderAlpha={0.55}
			borderWidth={18}
		/>
		<Rectangle
			x={12}
			y={12}
			width={panelSizes.width - 24}
			height={panelSizes.height - 24}
			borderRadius={28}
			backgroundColor={0x2d5536}
			borderColor={0xf0c85a}
			borderWidth={7}
		/>
		<Sprite
			x={panelSizes.width * 0.5}
			y={28}
			anchor={0.5}
			key="s.png"
			width={72}
			height={72}
			rotation={-0.08}
		/>
		<Container x={panelSizes.width * 0.5} y={panelSizes.height * 0.5 + 10}>
			<Text
				y={-fontSize * 0.72}
				anchor={0.5}
				text={'FREE SPIN'}
				style={gardenGoldTextStyle({ fontSize, letterSpacing: 1 })}
			/>
			<Text
				y={fontSize * 0.58}
				anchor={0.5}
				text={`${current} OF ${total}`}
				style={gardenGoldTextStyle({ fontSize: fontSize * 1.16 })}
			/>
		</Container>
	</FadeContainer>
</MainContainer>
