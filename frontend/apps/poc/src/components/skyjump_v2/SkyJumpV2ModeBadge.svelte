<script lang="ts">
	import { SKYJUMP_UI_STACK } from '../../game/skyjump_v2/fonts';

	type Props = {
		label: string;
	};

	const props: Props = $props();
</script>

{#if props.label}
	<div class="mode-badge" data-test="skyjump-v2-mode-badge">
		<span style:font-family={SKYJUMP_UI_STACK}>{props.label}</span>
	</div>
{/if}

<style>
	.mode-badge {
		box-sizing: border-box;
		display: inline-grid;
		place-items: center;
		max-width: 100%;
		padding: 0;
		pointer-events: none;
	}

	span {
		max-width: 100%;
		overflow: hidden;
		color: #f6ead0;
		font-size: 0.95rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		line-height: 1.15;
		text-align: center;
		text-overflow: ellipsis;
		text-transform: uppercase;
		white-space: normal;
		pointer-events: none;
	}
</style>
