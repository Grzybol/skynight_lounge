<script lang="ts" module>
	export type EmitterEventBoardFrame =
		| { type: 'boardFrameGlowShow' }
		| { type: 'boardFrameGlowHide' };
</script>

<script lang="ts">
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';
	import { Circle, Container, Rectangle } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { getGardenSlotFrameMetrics } from 'components-ui-pixi';

	type Props = {
		layer?: 'back' | 'front';
	};

	const props: Props = $props();
	const layer = $derived(props.layer ?? 'back');
	const context = getContext();

	const glow = new Tween(0);
	let showGlow = $state(false);

	context.eventEmitter.subscribeOnMount({
		boardFrameGlowShow: () => {
			showGlow = true;
			glow.set(0.82, { duration: 520, easing: cubicInOut });
		},
		boardFrameGlowHide: async () => {
			await glow.set(0, { duration: 420, easing: cubicInOut });
			showGlow = false;
		},
	});

	const board = $derived(context.stateGameDerived.boardLayout());
	const slot = $derived(
		getGardenSlotFrameMetrics({
			x: 0,
			y: 0,
			width: board.width,
			height: board.height,
		}),
	);
	const well = $derived(slot.well);
	const frame = $derived(slot.frame);
	const cornerWidth = $derived(slot.cornerWidth);
	const cornerHeight = $derived(slot.cornerHeight);
	const corners = $derived(slot.corners);
	const boltSize = $derived(Math.max(10, board.width * 0.018));
	const bolts = $derived(
		corners.flatMap((corner) => [
			{ x: corner.x + cornerWidth * 0.24, y: corner.y + cornerHeight * 0.28 },
			{ x: corner.x + cornerWidth * 0.72, y: corner.y + cornerHeight * 0.7 },
		]),
	);
</script>

<Container x={board.x} y={board.y} scale={board.scale ?? 1}>
	{#if layer === 'back'}
		{#if showGlow}
			<Rectangle
				zIndex={-1}
				x={frame.x - board.width * 0.04}
				y={frame.y - board.height * 0.065}
				width={frame.width + board.width * 0.08}
				height={frame.height + board.height * 0.13}
				borderRadius={54}
				backgroundColor={0x72c94a}
				backgroundAlpha={glow.current * 0.055}
				borderColor={0xb7ef72}
				borderAlpha={glow.current * 0.7}
				borderWidth={24}
			/>
		{/if}

		<!-- Timber body and the dark reel well. No gold trim. -->
		<Rectangle
			x={frame.x}
			y={frame.y}
			width={frame.width}
			height={frame.height}
			borderRadius={34}
			backgroundColor={0x0f1a10}
			backgroundAlpha={0.96}
			borderColor={0x243324}
			borderWidth={18}
		/>
		<Rectangle
			x={well.x}
			y={well.y}
			width={well.width}
			height={well.height}
			borderRadius={16}
			backgroundColor={0x080c08}
			backgroundAlpha={1}
			borderWidth={0}
		/>
	{/if}

	{#if layer === 'front'}
		<!-- Inner timber faces, same wood as the beams — not a gold inlay. -->
		<Rectangle x={well.x} y={well.y} width={well.width} height={10} backgroundColor={0x6e3426} />
		<Rectangle
			x={well.x}
			y={well.y + well.height - 10}
			width={well.width}
			height={10}
			backgroundColor={0x6e3426}
		/>
		<Rectangle x={well.x} y={well.y} width={10} height={well.height} backgroundColor={0x773a29} />
		<Rectangle
			x={well.x + well.width - 10}
			y={well.y}
			width={10}
			height={well.height}
			backgroundColor={0x773a29}
		/>

		<!-- Heavy timber beams sit above the reels so symbols cannot paint over the wood. -->
		{#each [{ x: frame.x, y: frame.y, width: frame.width, height: frame.beamY }, { x: frame.x, y: frame.y + frame.height - frame.beamY, width: frame.width, height: frame.beamY }] as beam}
			<Rectangle
				{...beam}
				borderRadius={18}
				backgroundColor={0x6e3426}
				borderColor={0x2b1518}
				borderWidth={8}
			/>
			<Rectangle
				x={beam.x + frame.width * 0.025}
				y={beam.y + beam.height * 0.2}
				width={beam.width - frame.width * 0.05}
				height={beam.height * 0.18}
				borderRadius={8}
				backgroundColor={0x8a4a32}
				backgroundAlpha={0.35}
			/>
			<Rectangle
				x={beam.x + frame.width * 0.08}
				y={beam.y + beam.height * 0.68}
				width={beam.width * 0.29}
				height={Math.max(4, beam.height * 0.07)}
				borderRadius={4}
				backgroundColor={0x32181a}
				backgroundAlpha={0.72}
			/>
			<Rectangle
				x={beam.x + frame.width * 0.57}
				y={beam.y + beam.height * 0.62}
				width={beam.width * 0.26}
				height={Math.max(4, beam.height * 0.06)}
				borderRadius={4}
				backgroundColor={0x32181a}
				backgroundAlpha={0.62}
			/>
		{/each}

		{#each [{ x: frame.x, y: frame.y, width: frame.beamX, height: frame.height }, { x: frame.x + frame.width - frame.beamX, y: frame.y, width: frame.beamX, height: frame.height }] as beam}
			<Rectangle
				{...beam}
				borderRadius={18}
				backgroundColor={0x773a29}
				borderColor={0x2b1518}
				borderWidth={8}
			/>
			<Rectangle
				x={beam.x + beam.width * 0.2}
				y={beam.y + frame.height * 0.08}
				width={beam.width * 0.17}
				height={beam.height * 0.84}
				borderRadius={6}
				backgroundColor={0x8a4a32}
				backgroundAlpha={0.32}
			/>
			<Rectangle
				x={beam.x + beam.width * 0.62}
				y={beam.y + frame.height * 0.24}
				width={Math.max(4, beam.width * 0.08)}
				height={beam.height * 0.25}
				borderRadius={4}
				backgroundColor={0x32181a}
				backgroundAlpha={0.68}
			/>
		{/each}

		{#each corners as corner}
			<Rectangle
				x={corner.x}
				y={corner.y}
				width={cornerWidth}
				height={cornerHeight}
				borderRadius={16}
				backgroundColor={0x30343b}
				borderColor={0x11151b}
				borderWidth={6}
			/>
			<Rectangle
				x={corner.x + cornerWidth * 0.12}
				y={corner.y + cornerHeight * 0.1}
				width={cornerWidth * 0.76}
				height={cornerHeight * 0.18}
				borderRadius={6}
				backgroundColor={0x87909a}
				backgroundAlpha={0.52}
			/>
		{/each}

		{#each bolts as bolt}
			<Circle
				x={bolt.x - boltSize * 0.5}
				y={bolt.y - boltSize * 0.5}
				diameter={boltSize}
				backgroundColor={0xd49a4c}
				borderColor={0x3a251e}
				borderWidth={3}
			/>
			<Rectangle
				x={bolt.x - boltSize * 0.22}
				y={bolt.y - boltSize * 0.04}
				width={boltSize * 0.44}
				height={Math.max(2, boltSize * 0.08)}
				borderRadius={2}
				backgroundColor={0x5a3825}
			/>
		{/each}
	{/if}
</Container>
