<script lang="ts">
	import type { ButtonProps } from 'components-pixi';
	import { stateBet, stateBetDerived } from 'state-shared';

	import UiButton from './UiButton.svelte';
	import { resolveButtonSizes } from '../gardenHud';
	import { getContext } from '../context';

	const props: Partial<Omit<ButtonProps, 'children'>> = $props();
	const context = getContext();
	const sizes = $derived(resolveButtonSizes(props.sizes));
	const active = $derived(stateBet.isTurbo);
	const disabled = $derived(stateBet.isSpaceHold || stateBet.overlayOpen);

	const onpress = () => {
		if (stateBet.overlayOpen) return;
		context.eventEmitter.broadcast({ type: 'soundPressGeneral' });
		stateBetDerived.updateIsTurbo(!stateBet.isTurbo, { persistent: true });
	};

	context.eventEmitter.subscribeOnMount({
		stopButtonClick: () => {
			if (stateBet.overlayOpen) return;
			stateBetDerived.updateIsTurbo(true, { persistent: false });
		},
		stopButtonEnable: () => {
			if (stateBet.overlayOpen) return;
			stateBetDerived.updateIsTurbo(false, { persistent: false });
		},
	});
</script>

<UiButton {...props} {sizes} {active} {onpress} {disabled} icon="turbo" accent="gold" />
