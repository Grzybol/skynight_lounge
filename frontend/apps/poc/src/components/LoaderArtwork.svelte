<script lang="ts">
	import { onMount } from 'svelte';
	import { cubicInOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';

	import { Container, Rectangle, Text } from 'pixi-svelte';
	import { MainContainer } from 'components-layout';

	import { getContext } from '../game/context';
	import { SKYJUMP_DISPLAY_FONT, SKYJUMP_UI_FONT } from '../game/gardenTextStyle';

	type Props = {
		progress: number;
		ready?: boolean;
	};

	const props: Props = $props();
	const context = getContext();

	const pulse = new Tween(0.35);
	const bob = new Tween(-8);
	let alive = true;

	const clampedProgress = $derived(Math.max(0, Math.min(100, props.progress)));
	const progressWidth = $derived(520 * (clampedProgress / 100));

	const animate = async () => {
		while (alive) {
			await Promise.all([
				pulse.set(0.82, { duration: 820, easing: cubicInOut }),
				bob.set(8, { duration: 820, easing: cubicInOut }),
			]);
			await Promise.all([
				pulse.set(0.35, { duration: 820, easing: cubicInOut }),
				bob.set(-8, { duration: 820, easing: cubicInOut }),
			]);
		}
	};

	onMount(() => {
		animate();
		return () => {
			alive = false;
		};
	});
</script>

<MainContainer>
	<Container
		x={context.stateLayoutDerived.mainLayout().width * 0.5}
		y={context.stateLayoutDerived.mainLayout().height * 0.5}
	>
		<Rectangle
			x={-410}
			y={-245}
			width={820}
			height={490}
			borderRadius={76}
			backgroundColor={0x071526}
			backgroundAlpha={0.92}
			borderColor={0x7ecbff}
			borderAlpha={pulse.current}
			borderWidth={34}
		/>
		<Rectangle
			x={-388}
			y={-223}
			width={776}
			height={446}
			borderRadius={60}
			backgroundColor={0x10243c}
			backgroundAlpha={0.98}
			borderColor={0xf0c14b}
			borderWidth={12}
		/>
		<Rectangle
			x={-352}
			y={-187}
			width={704}
			height={374}
			borderRadius={42}
			backgroundColor={0x0b1b2c}
			backgroundAlpha={0.98}
			borderColor={0x7ecbff}
			borderWidth={5}
		/>

		<Container y={-105 + bob.current}>
			<Rectangle
				x={-18}
				y={-110}
				width={22}
				height={210}
				borderRadius={11}
				backgroundColor={0xe8f3ff}
				borderColor={0x7ecbff}
				borderWidth={4}
				rotation={-0.42}
			/>
			<Rectangle
				x={-18}
				y={-110}
				width={22}
				height={210}
				borderRadius={11}
				backgroundColor={0xd4e7f7}
				borderColor={0xf0c14b}
				borderWidth={4}
				rotation={0.42}
			/>
		</Container>

		<Text
			y={16}
			anchor={0.5}
			text="MIDNIGHT LOUNGE"
			style={{
				fontFamily: SKYJUMP_DISPLAY_FONT,
				fontSize: 62,
				fontWeight: '800',
				letterSpacing: 3,
				fill: 0xffd36b,
				stroke: { color: 0x10243c, width: 7 },
			}}
		/>
		<Text
			y={76}
			anchor={0.5}
			text={props.ready ? 'THE LOUNGE IS OPEN' : 'PREPARING THE ROOM'}
			style={{
				fontFamily: SKYJUMP_DISPLAY_FONT,
				fontSize: 22,
				fontWeight: '700',
				letterSpacing: 4,
				fill: 0xf2f0cf,
			}}
		/>

		<Rectangle
			x={-274}
			y={126}
			width={548}
			height={44}
			borderRadius={22}
			backgroundColor={0x071526}
			borderColor={0x7ecbff}
			borderWidth={5}
		/>
		<Rectangle
			x={-260}
			y={138}
			width={progressWidth}
			height={20}
			borderRadius={10}
			backgroundColor={props.ready ? 0x74d59b : 0xe7a64b}
		/>
		<Rectangle
			x={-252}
			y={141}
			width={Math.max(0, progressWidth - 16)}
			height={5}
			borderRadius={3}
			backgroundColor={0xffefb3}
			backgroundAlpha={0.7}
		/>
		<Text
			y={198}
			anchor={0.5}
			text={props.ready ? '100% â€¢ READY' : `${Math.round(clampedProgress)}%`}
			style={{
				fontFamily: SKYJUMP_UI_FONT,
				fontSize: 21,
				fontWeight: '700',
				letterSpacing: 2,
				fill: 0xffe3a0,
			}}
		/>
	</Container>
</MainContainer>
