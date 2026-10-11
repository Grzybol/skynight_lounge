<script lang="ts" module>
	import { stateBet, stateBetDerived } from 'state-shared';
</script>

<script lang="ts">
	import OnHotkey from './OnHotkey.svelte';

	const locked = $derived(stateBet.overlayOpen);

	const spaceHoldOn = () => {
		if (stateBet.overlayOpen) return;
		stateBet.autoSpinsCounter = 0;
		stateBet.isSpaceHold = true;
		stateBetDerived.updateIsTurbo(true, { persistent: true });
	};

	const spaceHoldOff = () => {
		stateBet.isSpaceHold = false;
		if (stateBet.overlayOpen) return;
		stateBetDerived.updateIsTurbo(false, { persistent: true });
	};
</script>

<OnHotkey hotkey="Space" disabled={locked} onhold={spaceHoldOn} onholdend={spaceHoldOff} />
