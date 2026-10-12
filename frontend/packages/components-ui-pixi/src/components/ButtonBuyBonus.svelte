<script lang="ts">
	import { Container, Text } from 'pixi-svelte';
	import { Button, type ButtonProps } from 'components-pixi';
	import { stateModal, stateBet, stateBetDerived, stateUi } from 'state-shared';

	import UiSprite from './UiSprite.svelte';
	import SkyJumpBetUiFace from './SkyJumpBetUiFace.svelte';
	import { UI_BASE_FONT_SIZE } from '../constants';
	import { hudFontSize, resolveButtonSizes } from '../gardenHud';
	import { SKYJUMP_HUD_TONE } from '../skyjumpHud';
	import { SKYJUMP_BETUI_ART, SKYJUMP_BETUI_FACE_FIT, SKYJUMP_BETUI_FACE_SCALE } from '../skyjumpBetUiArt';
	import { getContext } from '../context';
	import { i18nDerived } from '../i18n/i18nDerived';

	const props: Partial<Omit<ButtonProps, 'children'>> = $props();
	const { stateXstateDerived, eventEmitter } = getContext();
	const sizes = $derived(resolveButtonSizes(props.sizes));
	const disabled = $derived(!stateXstateDerived.isIdle());
	const active = $derived(stateBetDerived.activeBetMode()?.type === 'activate');
	const minerTheme = $derived(stateUi.config.theme === 'miner');
	const gardenTheme = $derived(stateUi.config.theme === 'garden');
	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');
	const illustratedTheme = $derived(minerTheme || gardenTheme);

	const openModal = () => (stateModal.modal = { name: 'buyBonus' });
	const disableActiveBetMode = () => (stateBet.activeBetModeKey = 'BASE');
	const onpress = () => {
		eventEmitter.broadcast({ type: 'soundPressGeneral' });

		if (active) {
			disableActiveBetMode();
		} else {
			openModal();
		}
	};

	const buyLabel = $derived(i18nDerived.buyBonus());
	const disableLabel = $derived(i18nDerived.disable());

	const getState = (value: {
		active: boolean;
		disabled: boolean;
		hovered: boolean;
		pressed: boolean;
	}) => {
		if (value.disabled) return 'disabled' as const;
		if (value.pressed) return 'pressed' as const;
		if (value.hovered) return 'hovered' as const;
		if (value.active) return 'active' as const;
		return 'default' as const;
	};
</script>

<Button {...props} {sizes} {disabled} {onpress} alpha={skyjumpTheme && disabled ? 0.84 : undefined}>
	{#snippet children({ center, hovered, pressed })}
		{@const state = getState({
			active,
			disabled,
			hovered,
			pressed,
		})}

		{@const buyScale =
			skyjumpTheme && !disabled ? (pressed ? 0.97 : hovered ? 1.02 : 1) : 1}

		{#if skyjumpTheme}
			<Container x={center.x} y={center.y} scale={buyScale}>
				<SkyJumpBetUiFace
					assetKey={SKYJUMP_BETUI_ART.buyBonus}
					width={sizes.width * SKYJUMP_BETUI_FACE_FIT.buyW * SKYJUMP_BETUI_FACE_SCALE.buy}
					height={sizes.height * SKYJUMP_BETUI_FACE_FIT.buyH * SKYJUMP_BETUI_FACE_SCALE.buy}
					alpha={disabled ? 0.55 : 1}
					tint={disabled ? 0x8899aa : active ? 0xffe0a0 : 0xffffff}
				/>
				{#if active}
					<Text
						anchor={0.5}
						text={disableLabel}
						style={{
							align: 'center',
							fontFamily: 'SkyjumpDisplay',
							fontWeight: '800',
							fontSize: hudFontSize(sizes.height, 0.26),
							fill: SKYJUMP_HUD_TONE.goldHot,
						}}
					/>
				{/if}
			</Container>
		{:else}
			<UiSprite
				key="buyBonus"
				x={center.x}
				y={center.y}
				anchor={0.5}
				width={sizes.width * buyScale}
				height={sizes.height * buyScale}
				gardenTone={disabled ? 'disabled' : active ? 'active' : 'leaf'}
				hovered={state === 'hovered'}
				pressed={state === 'pressed'}
				backgroundColor={gardenTheme
					? undefined
					: minerTheme
						? active
							? 0x477759
							: 0x5a2c59
						: undefined}
				borderColor={minerTheme ? 0xe7a64b : undefined}
				borderWidth={minerTheme ? 6 : undefined}
				{...!gardenTheme && disabled
					? {
							backgroundColor: 0xaaaaaa,
						}
					: {}}
				{...!illustratedTheme && active
					? {
							borderWidth: 10,
							borderColor: 0xffffff,
						}
					: {}}
			/>

			<Text
				x={center.x}
				y={
					center.y +
					(gardenTheme && state === 'pressed'
						? 2
						: gardenTheme && state === 'hovered'
							? -2
							: 0)
				}
				anchor={0.5}
				text={state === 'active' ? disableLabel : buyLabel}
				style={{
					align: 'center',
					wordWrap: true,
					wordWrapWidth: gardenTheme ? sizes.width * 0.9 : 200,
					fontFamily: 'proxima-nova',
					fontWeight: gardenTheme ? '700' : '600',
					fontSize: gardenTheme ? hudFontSize(sizes.height) : UI_BASE_FONT_SIZE * 0.9,
					lineHeight: gardenTheme ? hudFontSize(sizes.height, 0.28) : undefined,
					fill: illustratedTheme ? 0xffedb0 : 0xffffff,
					...(gardenTheme
						? {
								stroke: { color: 0x1c120c, width: 3 },
							}
						: {}),
				}}
			/>
		{/if}
	{/snippet}
</Button>
