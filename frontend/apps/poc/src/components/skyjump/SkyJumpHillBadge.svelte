<script lang="ts">
	import { stateBet } from 'state-shared';

	import { getContext } from '../../game/context';
	import { BET_MODE_TO_TABLES, HILL_TABLE } from '../../game/skyjump/config';
	import { t } from '../../game/skyjump/copy';
	import type { BetModeKey } from '../../game/skyjump/types';

	const context = getContext();
	const hill = $derived(
		HILL_TABLE[
			BET_MODE_TO_TABLES[(stateBet.activeBetModeKey as BetModeKey) ?? 'BASE']?.hillId ?? 'normal'
		],
	);
</script>

{#if context.stateGame.screen === 'play'}
	<div class="hill">{t(hill.label)}</div>
{/if}

<style>
	.hill {
		position: absolute;
		z-index: 17;
		top: 4.4rem;
		right: 1rem;
		left: auto;
		padding: 0.28rem 0.6rem;
		color: #eef4f8;
		background: rgba(7, 21, 38, 0.72);
		border: 1px solid rgba(126, 203, 255, 0.4);
		border-radius: 999px;
		font-size: 0.68rem;
		font-weight: 800;
		letter-spacing: 0.1em;
		pointer-events: none;
	}

	@media (max-width: 720px) {
		.hill {
			top: 52px;
			bottom: auto;
			right: 8px;
			font-size: 11px;
			padding: 4px 8px;
		}
	}
</style>
