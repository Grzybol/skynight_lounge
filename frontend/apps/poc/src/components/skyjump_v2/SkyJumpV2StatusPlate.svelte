<script lang="ts">
	import type { Snippet } from 'svelte';

	import { MARCELLUS_STACK } from '../../game/skyjump_v2/fonts';

	type Props = {
		label: string;
		sub?: string;
		children?: Snippet;
	};

	const props: Props = $props();
</script>

<!-- Code lacquer plaque. Same role as the old plate: label, optional sub, feature notes. -->
<div class="status-plate" data-test="skyjump-v2-status-plate">
	<svg class="lacquer" viewBox="0 0 480 86" preserveAspectRatio="none" aria-hidden="true">
		<defs>
			<linearGradient id="ml-plate-fill" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#5a1a2c" />
				<stop offset="46%" stop-color="#2a0c14" />
				<stop offset="100%" stop-color="#12080c" />
			</linearGradient>
			<linearGradient id="ml-plate-sheen" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#f3e2b8" stop-opacity="0.28" />
				<stop offset="42%" stop-color="#f3e2b8" stop-opacity="0" />
			</linearGradient>
		</defs>
		<polygon
			points="22,1.5 458,1.5 478.5,43 458,84.5 22,84.5 1.5,43"
			fill="url(#ml-plate-fill)"
			stroke="#e4c57a"
			stroke-width="1.25"
		/>
		<polygon points="22,1.5 458,1.5 478.5,43 458,36 22,36 1.5,43" fill="url(#ml-plate-sheen)" />
		<polygon points="16,43 22,37 22,49" fill="#e4c57a" />
		<polygon points="464,43 458,37 458,49" fill="#e4c57a" />
	</svg>
	<div class="copy">
		<strong style:font-family={MARCELLUS_STACK}>{props.label}</strong>
		{#if props.sub || props.children}
			<div class="row">
				{#if props.sub}
					<span>{props.sub}</span>
				{/if}
				{#if props.children}
					{@render props.children()}
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.status-plate {
		position: relative;
		z-index: 8;
		box-sizing: border-box;
		display: grid;
		place-items: center;
		width: 65%;
		height: 65px;
		min-height: 65px;
		max-height: 65px;
		margin: 0 auto;
		padding: 0.15rem 1.8rem;
		overflow: hidden;
		pointer-events: none;
	}

	.lacquer {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
		filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.38));
	}

	.copy {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		flex-wrap: nowrap;
		gap: 4px;
		align-items: center;
		justify-content: center;
		width: 100%;
		max-width: 100%;
		min-width: 0;
		margin: 0;
		padding: 0;
		color: var(--ml-gold, #f0c75a);
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		font-weight: 800;
		letter-spacing: 0.06em;
		text-align: center;
		line-height: 1;
		text-shadow: 0 0 10px rgba(228, 197, 122, 0.28);
		pointer-events: none;
	}

	/* One line per row: long text is cut with an ellipsis instead of spilling out of the tile. */
	.copy strong {
		max-width: 100%;
		overflow: hidden;
		font-size: 0.95rem;
		line-height: 1.1;
		text-overflow: ellipsis;
		text-transform: uppercase;
		white-space: nowrap;
		color: var(--ml-gold, #f0c75a);
	}

	.row {
		display: flex;
		flex-wrap: nowrap;
		gap: 0.6rem;
		align-items: center;
		justify-content: center;
		max-width: 100%;
		min-width: 0;
		overflow: hidden;
	}

	.row span,
	.row :global(em) {
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--ml-gold, #f0c75a);
		font-size: 0.78rem;
		font-style: normal;
		font-weight: 700;
		letter-spacing: 0.03em;
		line-height: 1.1;
		text-shadow: none;
	}
</style>
