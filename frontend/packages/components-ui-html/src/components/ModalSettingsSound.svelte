<script lang="ts">
	import type { Snippet } from 'svelte';

	import { getContextEventEmitter } from 'utils-event-emitter';
	import { Button } from 'components-shared';

	import BaseButtonContent from './BaseButtonContent.svelte';
	import type { EmitterEventModal } from '../types';

	type Props = {
		value: number;
		children: Snippet;
	};

	let { value = $bindable(), children }: Props = $props();
	const { eventEmitter } = getContextEventEmitter<EmitterEventModal>();
</script>

<div class="col">
	<span>{@render children()}</span>
	<div class="row">
		<!-- button -->
		<div class="button-wrap">
			<Button
				selected={value > 0}
				onclick={() => {
					eventEmitter.broadcast({ type: 'soundPressGeneral' });
					if (value === 0) {
						value = 50;
					} else {
						value = 0;
					}
				}}
			>
				<BaseButtonContent>
					<span>{value > 0 ? 'ON' : 'OFF'}</span>
				</BaseButtonContent>
			</Button>
		</div>

		<!-- range -->
		<input bind:value type="range" min="0" max="100" class="range" />

		<!-- value -->
		<div class="value">
			<span>{value}</span>
		</div>
	</div>
</div>

<style lang="scss">
	.col {
		display: flex;
		flex-direction: column;
	}

	.row {
		display: flex;
		flex-direction: row;
		gap: 0.5rem;
	}

	.button-wrap {
		width: 3.4rem;
		flex: 0 0 3.4rem;
		display: flex;
		align-items: center;
	}

	.range {
		width: 70%;
		display: flex;
		align-items: center;
		accent-color: #e4c57a;
	}

	.col > span {
		color: #cbb89a;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}

	.row {
		margin-top: 0.35rem;
		padding-top: 0.45rem;
		border-top: 1px solid rgba(212, 168, 92, 0.28);
	}

	.value span {
		color: #e4c57a;
		font-weight: 800;
	}

	.button-wrap :global(button) {
		width: 3.4rem;
		height: 2.1rem;
		border: 1px solid rgba(212, 168, 92, 0.55);
		border-radius: 10px;
		background: transparent;
		color: #f3e2b8;
		transition:
			transform 120ms ease,
			border-color 120ms ease,
			background 120ms ease,
			box-shadow 120ms ease,
			color 120ms ease;
	}

	.button-wrap :global(button:hover) {
		transform: translateY(-1px);
		color: #fff6df;
		border-color: #f3e2b8;
		background: rgba(228, 197, 122, 0.14);
		box-shadow: 0 0 0 1px rgba(212, 168, 92, 0.35);
	}

	.button-wrap :global(button:active) {
		transform: translateY(1px);
		background: rgba(228, 197, 122, 0.08);
	}

	.button-wrap :global(.base-button-content) {
		position: static;
		width: auto;
		height: auto;
	}

	.button-wrap :global(button:focus-visible) {
		outline: 2px solid #e4c57a;
		outline-offset: 2px;
	}

	.value {
		width: 15%;
		display: flex;
		justify-content: center;
		align-items: center;
	}
</style>
