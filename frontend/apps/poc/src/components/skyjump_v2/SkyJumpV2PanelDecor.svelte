<script lang="ts">
	type Props = {
		showTopper?: boolean;
		showCorners?: boolean;
		showDivider?: boolean;
		/** Kept so existing callers still compile. Corners are code strokes now. */
		compact?: boolean;
	};

	const props: Props = $props();
</script>

<div class="panel-decor" class:compact={props.compact} aria-hidden="true">
	{#if props.showTopper !== false}
		<span class="top-rule"></span>
	{/if}
	{#if props.showCorners !== false}
		<span class="corner tl"></span>
		<span class="corner tr"></span>
		<span class="corner bl"></span>
		<span class="corner br"></span>
	{/if}
	{#if props.showDivider !== false}
		<span class="divider"><i></i></span>
	{/if}
</div>

<style>
	.panel-decor {
		position: absolute;
		inset: 0;
		pointer-events: none;
		overflow: visible;
	}

	.top-rule {
		position: absolute;
		top: 10px;
		left: 18%;
		right: 18%;
		height: 1px;
		background: linear-gradient(90deg, transparent, rgba(228, 197, 122, 0.7), transparent);
	}

	.corner {
		position: absolute;
		width: 14px;
		height: 14px;
		border: 1.5px solid rgba(228, 197, 122, 0.85);
	}

	.corner.tl {
		top: 8px;
		left: 8px;
		border-right: 0;
		border-bottom: 0;
	}

	.corner.tr {
		top: 8px;
		right: 8px;
		border-left: 0;
		border-bottom: 0;
	}

	.corner.bl {
		bottom: 8px;
		left: 8px;
		border-right: 0;
		border-top: 0;
	}

	.corner.br {
		right: 8px;
		bottom: 8px;
		border-left: 0;
		border-top: 0;
	}

	.divider {
		position: absolute;
		top: 8px;
		left: 12%;
		right: 12%;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 8px;
	}

	.divider::before,
	.divider::after {
		content: '';
		flex: 1 1 auto;
		height: 1px;
		background: rgba(228, 197, 122, 0.55);
	}

	.divider i {
		width: 5px;
		height: 5px;
		margin: 0 6px;
		background: #e4c57a;
		transform: rotate(45deg);
	}
</style>
