<script lang="ts">
	import LoaderBase from './LoaderBase.svelte';

	type Props = {
		src: string;
		maxWidth?: number;
		label?: string;
		timeout?: number;
	};

	const props: Props = $props();

	let showText = $state(true);
	const label = $derived(props.label === undefined ? 'Add Your Loader' : props.label);
</script>

<LoaderBase
	maxWidth={props.maxWidth ?? 200}
	backgroundColor={'#000000'}
	timeout={props.timeout ?? 2000}
	src={props.src}
	oncomplete={() => (showText = false)}
/>

{#if showText && label}
	<span class="add-your-loader">{label}</span>
{/if}

<style lang="scss">
	.add-your-loader {
		z-index: 999;
		color: white;
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, 10px);
	}
</style>
