<script lang="ts">
	import type { ButtonProps } from 'components-pixi';
	import { stateI18nDerived, stateUi } from 'state-shared';

	import UiButton from './UiButton.svelte';
	import { skyjumpLanguageMenu } from './SkyJumpLanguageMenu.svelte';
	import { getContext } from '../context';
	import { UI_BASE_SIZE } from '../constants';
	import { resolveButtonSizes } from '../gardenHud';

	const props: Partial<Omit<ButtonProps, 'children'>> = $props();
	const context = getContext();
	const sizes = $derived(
		resolveButtonSizes(props.sizes, { width: UI_BASE_SIZE * 1.3, height: UI_BASE_SIZE * 1.3 }),
	);

	const skyjumpTheme = $derived(stateUi.config.theme === 'skyjump');

	const onpress = () => {
		context.eventEmitter.broadcast({ type: 'soundPressGeneral' });
		if (skyjumpTheme) {
			skyjumpLanguageMenu.open = !skyjumpLanguageMenu.open;
			return;
		}
		stateI18nDerived.switchLanguage(stateI18nDerived.locale() === 'pl' ? 'en' : 'pl');
	};
</script>

<UiButton {...props} {sizes} {onpress} icon="language" variant="light" />
