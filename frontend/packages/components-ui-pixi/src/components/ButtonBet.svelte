<script lang="ts">
	import { Container, Text } from 'pixi-svelte';
	import { Button, type ButtonProps } from 'components-pixi';
	import { OnHotkey } from 'components-shared';
	import { stateBet, stateBetDerived, stateUi } from 'state-shared';

	import UiSprite from './UiSprite.svelte';
	import SkyJumpBetUiFace from './SkyJumpBetUiFace.svelte';
	import ButtonBetProvider from './ButtonBetProvider.svelte';
	import { UI_BASE_FONT_SIZE } from '../constants';
	import { hudFontSize, resolveButtonSizes } from '../gardenHud';
	import { i18nDerived } from '../i18n/i18nDerived';
	import { SKYJUMP_HUD_TONE } from '../skyjumpHud';
	import { SKYJUMP_BETUI_ART, skyjumpSpinArtSize } from '../skyjumpBetUiArt';
	import { getContext } from '../context';

	const props: Partial<Omit<ButtonProps, 'children'>> = $props();
	const context = getContext();
	/**
	 * Idle SPIN stays gated by overlayOpen (presentation lock).
	 * STOP must stay clickable during overlay so autoplay can cancel —
	 * ButtonBetProvider.stop() clears autoSpinsCounter even under lock.
	 */
	const isIdle = $derived(context.stateXstateDerived.isIdle());
	const disabled = $derived(
		isIdle ? !stateBetDerived.isBetCostAvailable() || stateBet.overlayOpen : false,
	);
	const spaceLocked = $derived(isIdle && (disabled || stateBet.overlayOpen));
	const minerTheme = $derived(stateUi.config.theme === 'miner');
	const gardenTheme = $derived(stateUi.config.theme === 'garden');
	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');
	const sizes = $derived(resolveButtonSizes(props.sizes));
	const spinArt = $derived(skyjumpSpinArtSize(Math.min(sizes.width, sizes.height)));

	const gardenLift = (hovered: boolean, pressed: boolean) => (pressed ? 2 : hovered ? -2 : 0);
	const onhover = () => {
		if (!skyjumpTheme || disabled) return;
		context.eventEmitter.broadcast({ type: 'soundUiHover' });
	};
</script>

<ButtonBetProvider>
	{#snippet children({ key, onpress })}
		<OnHotkey hotkey="Space" disabled={spaceLocked} {onpress} />
		<Button {...props} {sizes} {onpress} {onhover} {disabled}>
			{#snippet children({ center, hovered, pressed })}
				{@const unavailable = disabled || ['spin_disabled', 'stop_disabled'].includes(key)}
				{@const isStop = key.startsWith('stop')}
				<Container {...center} scale={skyjumpTheme ? (pressed ? 0.95 : hovered ? 1.03 : 1) : 1}>
					{#if skyjumpTheme}
						<!-- Art face: circle diameter matches layout SPIN; spikes may overhang. -->
						<SkyJumpBetUiFace
							assetKey={isStop ? SKYJUMP_BETUI_ART.stop : SKYJUMP_BETUI_ART.spin}
							width={spinArt}
							height={spinArt}
							alpha={unavailable ? 0.55 : 1}
							tint={unavailable ? 0x8899aa : 0xffffff}
						/>
						{#if !isStop && unavailable}
							<Text
								anchor={0.5}
								text={'SPIN'}
								style={{
									align: 'center',
									wordWrap: true,
									wordWrapWidth: sizes.width * 0.78,
									fontFamily: 'SkyjumpDisplay',
									fontWeight: '800',
									fontSize: hudFontSize(sizes.height, 0.28),
									fill: unavailable ? SKYJUMP_HUD_TONE.iceSoft : SKYJUMP_HUD_TONE.goldHot,
								}}
							/>
						{/if}
					{:else}
						<UiSprite
							key="bet"
							width={sizes.width}
							height={sizes.height}
							anchor={0.5}
							gardenTone={unavailable ? 'disabled' : 'harvest'}
							{hovered}
							{pressed}
							backgroundColor={gardenTheme ? undefined : minerTheme ? 0xd58b34 : undefined}
							borderColor={minerTheme ? 0xffd36b : undefined}
							borderWidth={minerTheme ? 6 : undefined}
							{...!gardenTheme && unavailable
								? {
										backgroundColor: 0xaaaaaa,
									}
								: {}}
						/>
						<Text
							y={gardenTheme ? gardenLift(hovered, pressed) : 0}
							anchor={0.5}
							text={['spin_default', 'spin_disabled'].includes(key)
								? i18nDerived.bet()
								: i18nDerived.stop()}
							style={{
								align: 'center',
								wordWrap: true,
								wordWrapWidth: gardenTheme ? sizes.width * 0.82 : 200,
								fontFamily: 'proxima-nova',
								fontWeight: gardenTheme ? '700' : '600',
								fontSize: gardenTheme ? hudFontSize(sizes.height, 0.28) : UI_BASE_FONT_SIZE * 0.9,
								fill: gardenTheme ? 0x17311d : minerTheme ? 0x29152c : 0xffffff,
							}}
						/>
					{/if}
				</Container>
			{/snippet}
		</Button>
	{/snippet}
</ButtonBetProvider>
