<script lang="ts">
	import type { Snippet } from 'svelte';

	import ModalError from './ModalError.svelte';
	import ModalBetMenu from './ModalBetMenu.svelte';
	import ModalBuyBonus from './ModalBuyBonus.svelte';
	import ModalBuyBonusConfirm from './ModalBuyBonusConfirm.svelte';
	import ModalAutoSpin from './ModalAutoSpin.svelte';
	import ModalAutoSpinMessage from './ModalAutoSpinMessage.svelte';
	import ModalPayTable from './ModalPayTable.svelte';
	import ModalGameRules from './ModalGameRules.svelte';
	import ModalSettings from './ModalSettings.svelte';

	type Props = {
		version: Snippet;
		payTable?: Snippet;
		gameRules?: Snippet;
		buyBonus?: Snippet;
	};

	const props: Props = $props();
</script>

<ModalError />
<ModalBetMenu />
<ModalBuyBonus content={props.buyBonus} />
<ModalBuyBonusConfirm />
<ModalAutoSpin />
<ModalAutoSpinMessage />
<ModalPayTable>
	{#if props.payTable}
		{@render props.payTable()}
	{:else}
		<span>ADD YOUR PAY TABLE</span>
	{/if}
	{@render props.version()}
</ModalPayTable>
<ModalGameRules>
	{#if props.gameRules}
		{@render props.gameRules()}
	{:else}
		<span>ADD YOUR GAME RULES</span>
	{/if}
	{@render props.version()}
</ModalGameRules>
<ModalSettings />

<style lang="scss">
	:global(html) {
		font-size: 16px; /* you can chose any size here 16 is default */
		@media screen and (max-width: 500px) {
			font-size: 50%;
		}
	}
</style>
