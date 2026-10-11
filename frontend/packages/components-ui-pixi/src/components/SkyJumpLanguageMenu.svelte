<script lang="ts" module>
	export const skyjumpLanguageMenu = $state({ open: false });
</script>

<script lang="ts">
	import { Container, Text } from 'pixi-svelte';
	import { Button } from 'components-pixi';
	import { stateI18nDerived } from 'state-shared';

	import UiSprite from './UiSprite.svelte';
	import SkyJumpHudMark from './SkyJumpHudMark.svelte';
	import { getContext } from '../context';
	import { SKYJUMP_HUD_TONE } from '../skyjumpHud';
	import { hudFontSize } from '../gardenHud';

	type Lang = 'en' | 'pl';

	const {
		x,
		y,
		width,
		buttonHeight,
	}: { x: number; y: number; width: number; buttonHeight: number } = $props();
	const context = getContext();
	const chipW = 96;
	const chipH = 46;
	const gap = 8;
	const chips: { lang: Lang; label: string; kind: 'flag-en' | 'flag-pl' }[] = [
		{ lang: 'en', label: 'EN', kind: 'flag-en' },
		{ lang: 'pl', label: 'PL', kind: 'flag-pl' },
	];

	const pick = (lang: Lang) => {
		context.eventEmitter.broadcast({ type: 'soundPressGeneral' });
		stateI18nDerived.switchLanguage(lang);
		skyjumpLanguageMenu.open = false;
	};
</script>

{#each chips as chip, index}
	{@const chipX = x + width / 2 - chipW * 0.5 - (chips.length - 1 - index) * (chipW + gap)}
	{@const chipY = y - buttonHeight / 2 - chipH / 2 - 12}
	<Container x={chipX} y={chipY}>
		<Button anchor={0.5} sizes={{ width: chipW, height: chipH }} onpress={() => pick(chip.lang)}>
			{#snippet children({ center, hovered })}
				{@const selected = stateI18nDerived.locale() === chip.lang}
				<Container {...center}>
					<UiSprite
						anchor={0.5}
						width={chipW}
						height={chipH}
						backgroundColor={selected
							? SKYJUMP_HUD_TONE.goldFillActive
							: hovered
								? SKYJUMP_HUD_TONE.navyHover
								: SKYJUMP_HUD_TONE.navy}
						borderColor={selected ? SKYJUMP_HUD_TONE.goldHot : SKYJUMP_HUD_TONE.ice}
						borderWidth={selected ? 2.5 : 2}
						borderRadius={12}
					/>
					<SkyJumpHudMark kind={chip.kind} size={18} x={-34} y={-9} />
					<Text
						text={chip.label}
						x={16}
						anchor={0.5}
						style={{
							fontFamily: 'SkyjumpDisplay',
							fontWeight: '800',
							fontSize: hudFontSize(chipH, 0.4),
							fill: selected ? SKYJUMP_HUD_TONE.goldHot : SKYJUMP_HUD_TONE.text,
						}}
					/>
				</Container>
			{/snippet}
		</Button>
	</Container>
{/each}
