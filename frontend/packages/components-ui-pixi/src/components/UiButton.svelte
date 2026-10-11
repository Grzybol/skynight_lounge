<script lang="ts">
	import { Container, Graphics, Text } from 'pixi-svelte';
	import { Button, type ButtonProps } from 'components-pixi';
	import { stateI18nDerived, stateUi } from 'state-shared';

	import UiSprite from './UiSprite.svelte';
	import SkyJumpHudMark from './SkyJumpHudMark.svelte';
	import SkyJumpBetUiFace from './SkyJumpBetUiFace.svelte';
	import type { ButtonIcon } from '../types';
	import type { Snippet } from 'svelte';
	import { i18nDerived } from '../i18n/i18nDerived';
	import { UI_BASE_FONT_SIZE } from '../constants';
	import { hudFontSize } from '../gardenHud';
	import { SKYJUMP_HUD_TONE } from '../skyjumpHud';
	import {
		SKYJUMP_BETUI_ART,
		SKYJUMP_BETUI_FACE_FIT,
		SKYJUMP_BETUI_FACE_SCALE,
		SKYJUMP_BETUI_GLYPH_FIT,
		SKYJUMP_MENU_EXIT_ASPECT,
		SKYJUMP_MENU_ICON_FIT,
		skyjumpFlyoutArtKey,
	} from '../skyjumpBetUiArt';
	import { getContext } from '../context';

	type Props = Omit<ButtonProps, 'children'> & {
		icon: ButtonIcon;
		sizes: { width: number; height: number };
		active?: boolean;
		children?: Snippet;
		variant?: 'dark' | 'light';
		accent?: 'ice' | 'gold';
	};

	const {
		icon,
		active,
		variant = 'dark',
		accent = 'ice',
		children: childrenFromParent,
		...buttonProps
	}: Props = $props();

	const context = getContext();
	const minerTheme = $derived(stateUi.config.theme === 'miner');
	const gardenTheme = $derived(stateUi.config.theme === 'garden');
	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');
	const illustratedTheme = $derived(minerTheme || gardenTheme);
	/** BET ± live inside the unified cluster — no second plate chrome. */
	const clusterGlyph = $derived(skyjumpTheme && (icon === 'decrease' || icon === 'increase'));
	const modeControl = $derived(skyjumpTheme && (icon === 'autoSpin' || icon === 'turbo'));
	const flyoutArtKey = $derived(skyjumpTheme ? skyjumpFlyoutArtKey(icon) : null);
	const artFace = $derived(
		skyjumpTheme &&
			(icon === 'autoSpin' || icon === 'turbo' || icon === 'menu' || flyoutArtKey != null),
	);
	const artKey = $derived(
		flyoutArtKey ??
			(icon === 'turbo'
				? SKYJUMP_BETUI_ART.turbo
				: icon === 'autoSpin'
					? SKYJUMP_BETUI_ART.auto
					: SKYJUMP_BETUI_ART.menu),
	);
	const artSize = $derived.by(() => {
		if (flyoutArtKey) {
			if (icon === 'language') {
				return {
					width: buttonProps.sizes.width,
					height: buttonProps.sizes.height,
				};
			}
			const height = buttonProps.sizes.height * SKYJUMP_MENU_ICON_FIT;
			const width =
				icon === 'menuExit'
					? height * SKYJUMP_MENU_EXIT_ASPECT
					: buttonProps.sizes.width * SKYJUMP_MENU_ICON_FIT;
			return { width, height };
		}
		const fitW = SKYJUMP_BETUI_FACE_FIT.modeW;
		const fitH = SKYJUMP_BETUI_FACE_FIT.modeH;
		if (icon === 'turbo') {
			return {
				width: buttonProps.sizes.width * fitW * SKYJUMP_BETUI_FACE_SCALE.turboW,
				height: buttonProps.sizes.height * fitH * SKYJUMP_BETUI_FACE_SCALE.turboH,
			};
		}
		if (icon === 'autoSpin') {
			return {
				width: buttonProps.sizes.width * fitW * SKYJUMP_BETUI_FACE_SCALE.auto,
				height: buttonProps.sizes.height * fitH * SKYJUMP_BETUI_FACE_SCALE.auto,
			};
		}
		return {
			width: buttonProps.sizes.width * fitW * SKYJUMP_BETUI_FACE_SCALE.menu,
			height: buttonProps.sizes.height * fitH * SKYJUMP_BETUI_FACE_SCALE.menu,
		};
	});

	const onhover = () => {
		if (!skyjumpTheme || buttonProps.disabled) return;
		context.eventEmitter.broadcast({ type: 'soundUiHover' });
	};

	const minerFill = (hovered: boolean, pressed: boolean) => {
		if (buttonProps.disabled) return 0xaaaaaa;
		if (active) return 0x6a3568;
		if (pressed) return 0x241428;
		if (hovered) return 0x4a2854;
		return 0x321b39;
	};

	const skyjumpFill = (hovered: boolean, pressed: boolean) => {
		if (clusterGlyph) {
			if (buttonProps.disabled) return 0x061018;
			if (pressed) return SKYJUMP_HUD_TONE.navyPressed;
			if (hovered) return SKYJUMP_HUD_TONE.navyHover;
			return 0x0a1c32;
		}
		if (icon === 'turbo') {
			if (buttonProps.disabled) return SKYJUMP_HUD_TONE.navyDisabled;
			if (active) return 0x0c3a24;
			if (pressed) return 0x120808;
			if (hovered) return 0x1e1410;
			return 0x081422;
		}
		if (icon === 'autoSpin') {
			if (buttonProps.disabled) return SKYJUMP_HUD_TONE.navyDisabled;
			if (active) return 0x1a5a88;
			if (pressed) return SKYJUMP_HUD_TONE.navyPressed;
			if (hovered) return SKYJUMP_HUD_TONE.navyHover;
			return 0x081422;
		}
		if (accent === 'gold') {
			if (buttonProps.disabled) return SKYJUMP_HUD_TONE.navyDisabled;
			if (active) return SKYJUMP_HUD_TONE.goldFillActive;
			if (pressed) return SKYJUMP_HUD_TONE.goldFillPressed;
			if (hovered) return SKYJUMP_HUD_TONE.goldFillHover;
			return SKYJUMP_HUD_TONE.goldFill;
		}
		if (buttonProps.disabled) return SKYJUMP_HUD_TONE.navyDisabled;
		if (active) return SKYJUMP_HUD_TONE.navyActive;
		if (pressed) return SKYJUMP_HUD_TONE.navyPressed;
		if (hovered) return SKYJUMP_HUD_TONE.navyHover;
		return SKYJUMP_HUD_TONE.navy;
	};

	const skyjumpText = () => {
		if (buttonProps.disabled) return SKYJUMP_HUD_TONE.iceSoft;
		if (icon === 'turbo')
			return active ? SKYJUMP_HUD_TONE.turboOnSoft : SKYJUMP_HUD_TONE.turboOffSoft;
		if (icon === 'autoSpin') return active ? SKYJUMP_HUD_TONE.autoOnSoft : SKYJUMP_HUD_TONE.iceSoft;
		if (accent === 'gold') return active ? SKYJUMP_HUD_TONE.goldHot : SKYJUMP_HUD_TONE.goldText;
		if (clusterGlyph) return SKYJUMP_HUD_TONE.iceBright;
		return SKYJUMP_HUD_TONE.text;
	};

	const languageMark = $derived(skyjumpTheme && icon === 'language' && !flyoutArtKey);
	const stackedMark = $derived(
		(skyjumpTheme && icon === 'turbo') || languageMark || (skyjumpTheme && icon === 'autoSpin'),
	);
	const gardenLift = (hovered: boolean, pressed: boolean) => (pressed ? 2 : hovered ? -2 : 0);
	const caption = $derived(
		skyjumpTheme && icon === 'autoSpin'
			? 'AUTO'
			: skyjumpTheme && (icon === 'decrease' || icon === 'increase')
				? icon === 'decrease'
					? '−'
					: '+'
				: i18nDerived[icon](),
	);
	const turboSparks = [
		{ a: 0.4, r: 0.58 },
		{ a: 1.5, r: 0.62 },
		{ a: 2.6, r: 0.55 },
		{ a: 3.7, r: 0.6 },
		{ a: 4.8, r: 0.57 },
		{ a: 5.6, r: 0.63 },
	];
	/** Soft radial bloom. Outer rings are nearly clear so the glow has no hard edge. */
	const drawTurboGlow = (
		graphics: Parameters<import('pixi-svelte').GraphicsProps['draw']>[0],
		width: number,
		height: number,
		pulse: number,
	) => {
		const rings = 14;
		const rx = width * 0.98 + pulse * 5;
		const ry = height * 0.86 + pulse * 4;
		const centerAlpha = 0.13 + pulse * 0.04;
		let weightSum = 0;
		const weights: number[] = [];
		for (let i = 0; i < rings; i++) {
			const t = i / (rings - 1);
			const weight = Math.pow(t, 2.8);
			weights.push(weight);
			weightSum += weight;
		}
		for (let i = 0; i < rings; i++) {
			const t = i / (rings - 1);
			const alpha = (centerAlpha * weights[i]) / weightSum;
			if (alpha < 0.004) continue;
			const scale = 1 - t * 0.62;
			graphics.ellipse(0, 0, rx * scale, ry * scale);
			graphics.fill({ color: SKYJUMP_HUD_TONE.turboOnSoft, alpha });
		}
	};

	let turboPulse = $state(0);

	$effect(() => {
		if (!(skyjumpTheme && icon === 'turbo' && active)) {
			turboPulse = 0;
			return;
		}
		let frame = 0;
		const tick = (now: number) => {
			turboPulse = (Math.sin(now / 180) + 1) / 2;
			frame = requestAnimationFrame(tick);
		};
		frame = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(frame);
	});
</script>

<Button {...buttonProps} {onhover} alpha={skyjumpTheme && buttonProps.disabled ? 0.84 : undefined}>
	{#snippet children({ center, hovered, pressed })}
		{@const sjBorder = (() => {
			if (buttonProps.disabled) {
				return accent === 'gold' ? 0x8a7040 : 0x3e7a9a;
			}
			if (clusterGlyph) {
				return hovered || pressed ? SKYJUMP_HUD_TONE.iceBright : 0x3a6a88;
			}
			if (icon === 'turbo') {
				return active ? SKYJUMP_HUD_TONE.turboOn : 0x4a6078;
			}
			if (icon === 'autoSpin') {
				return active ? SKYJUMP_HUD_TONE.autoOn : 0x4a6078;
			}
			if (accent === 'gold') {
				return active ? SKYJUMP_HUD_TONE.goldHot : SKYJUMP_HUD_TONE.gold;
			}
			return active ? SKYJUMP_HUD_TONE.iceBright : SKYJUMP_HUD_TONE.ice;
		})()}
		{@const scale =
			skyjumpTheme && !buttonProps.disabled ? (pressed ? 0.96 : hovered ? 1.03 : 1) : 1}
		{@const radius = clusterGlyph
			? Math.round(Math.min(buttonProps.sizes.width, buttonProps.sizes.height) * 0.28)
			: modeControl
				? 16
				: 18}

		<Container {...center} {scale}>
			{#if artFace}
				{#if icon === 'turbo' && active}
					<Graphics
						draw={(graphics) =>
							drawTurboGlow(
								graphics,
								buttonProps.sizes.width,
								buttonProps.sizes.height,
								turboPulse,
							)}
					/>
				{:else if modeControl && active}
					<UiSprite
						anchor={0.5}
						width={buttonProps.sizes.width + 14}
						height={buttonProps.sizes.height + 12}
						backgroundColor={SKYJUMP_HUD_TONE.autoOnSoft}
						backgroundAlpha={0.32}
						borderWidth={0}
						borderRadius={radius + 8}
					/>
				{/if}
				<SkyJumpBetUiFace
					assetKey={artKey}
					width={artSize.width}
					height={artSize.height}
					alpha={buttonProps.disabled ? 0.55 : 1}
					tint={buttonProps.disabled
						? 0x8899aa
						: active
							? icon === 'turbo'
								? 0xc8ffe0
								: 0xc8e8ff
							: 0xffffff}
				/>
			{:else if skyjumpTheme && clusterGlyph}
				<SkyJumpBetUiFace
					assetKey={icon === 'increase' ? SKYJUMP_BETUI_ART.plus : SKYJUMP_BETUI_ART.minus}
					width={buttonProps.sizes.width * SKYJUMP_BETUI_GLYPH_FIT}
					height={buttonProps.sizes.height * SKYJUMP_BETUI_GLYPH_FIT}
					alpha={buttonProps.disabled ? 0.55 : 1}
				/>
			{:else if gardenTheme}
				<UiSprite
					anchor={0.5}
					width={buttonProps.sizes.width}
					height={buttonProps.sizes.height}
					gardenTone={buttonProps.disabled ? 'disabled' : active ? 'active' : 'leaf'}
					{hovered}
					{pressed}
				/>
			{:else}
				{#if skyjumpTheme && !clusterGlyph && accent === 'gold'}
					<UiSprite
						anchor={0.5}
						width={buttonProps.sizes.width + (active ? 10 : 8)}
						height={buttonProps.sizes.height + (active ? 10 : 6)}
						backgroundColor={SKYJUMP_HUD_TONE.goldBright}
						backgroundAlpha={active ? 0.26 : hovered ? 0.16 : 0.1}
						borderWidth={0}
						borderRadius={20}
					/>
				{/if}

				<UiSprite
					anchor={0.5}
					width={buttonProps.sizes.width}
					height={buttonProps.sizes.height}
					backgroundColor={skyjumpTheme
						? skyjumpFill(hovered, pressed)
						: minerTheme
							? minerFill(hovered, pressed)
							: variant === 'dark'
								? 0x000000
								: 0xffffff}
					borderColor={skyjumpTheme
						? sjBorder
						: minerTheme
							? active
								? 0xffd36b
								: 0xe7a64b
							: undefined}
					borderWidth={skyjumpTheme
						? clusterGlyph
							? hovered || pressed
								? 2
								: 1.5
							: active || accent === 'gold'
								? 2.5
								: 2
						: minerTheme
							? active
								? 5
								: 4
							: undefined}
					borderRadius={skyjumpTheme ? radius : undefined}
					{...buttonProps.disabled && !minerTheme && !skyjumpTheme
						? {
								backgroundColor: 0xaaaaaa,
							}
						: {}}
					{...!illustratedTheme && !skyjumpTheme && active
						? {
								borderWidth: 10,
								borderColor: variant === 'dark' ? 0xffffff : 0x000000,
							}
						: {}}
				/>
			{/if}

			{#if languageMark}
				<SkyJumpHudMark
					kind={stateI18nDerived.locale() === 'pl' ? 'flag-pl' : 'flag-en'}
					size={Math.round(buttonProps.sizes.height * 0.28)}
					x={0}
					y={-buttonProps.sizes.height * 0.16}
				/>
			{/if}

			{#if !artFace && !(skyjumpTheme && clusterGlyph)}
				{#if skyjumpTheme && icon === 'turbo'}
					<SkyJumpHudMark
						kind="bolt"
						color={skyjumpText()}
						size={Math.round(buttonProps.sizes.height * 0.28)}
						x={0}
						y={-buttonProps.sizes.height * 0.16}
					/>
				{/if}
				{#if skyjumpTheme && icon === 'autoSpin'}
					<SkyJumpHudMark
						kind="loop"
						color={skyjumpText()}
						size={Math.round(buttonProps.sizes.height * 0.26)}
						x={0}
						y={-buttonProps.sizes.height * 0.16}
					/>
				{/if}
				<Text
					x={0}
					y={stackedMark
						? buttonProps.sizes.height * 0.18
						: gardenTheme
							? gardenLift(hovered, pressed)
							: 0}
					anchor={0.5}
					text={caption}
					style={{
						align: 'center',
						wordWrap: true,
						wordWrapWidth: gardenTheme || skyjumpTheme ? buttonProps.sizes.width * 0.82 : 200,
						fontFamily: skyjumpTheme
							? clusterGlyph
								? 'SkyjumpDisplay'
								: 'SkyjumpUI'
							: 'proxima-nova',
						fontWeight: gardenTheme || skyjumpTheme ? '700' : '600',
						fontSize: gardenTheme
							? hudFontSize(buttonProps.sizes.height)
							: skyjumpTheme
								? clusterGlyph
									? hudFontSize(buttonProps.sizes.height, 0.42)
									: hudFontSize(buttonProps.sizes.height, 0.24)
								: UI_BASE_FONT_SIZE * 0.9,
						lineHeight:
							gardenTheme || skyjumpTheme ? hudFontSize(buttonProps.sizes.height, 0.3) : undefined,
						fill: gardenTheme
							? active
								? 0x17311d
								: 0xffedb0
							: skyjumpTheme
								? skyjumpText()
								: illustratedTheme
									? 0xffedb0
									: variant === 'dark'
										? 0xffffff
										: 0x000000,
						...(gardenTheme
							? {
									stroke: { color: 0x1c120c, width: 3 },
								}
							: {}),
					}}
				/>
			{/if}
		</Container>

		<!-- Keep children at button origin (auto-spin counter relies on width/2 layout). -->
		<Container y={gardenTheme ? gardenLift(hovered, pressed) : 0}>
			{@render childrenFromParent?.()}
		</Container>
	{/snippet}
</Button>
