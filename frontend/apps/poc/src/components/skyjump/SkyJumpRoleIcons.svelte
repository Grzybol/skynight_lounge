<script lang="ts">
	import { SLOT_ROLES } from '../../game/skyjump/config';
	import { roleIconSrc } from './skyjumpArt';
	import { getContext } from '../../game/context';
	import { t } from '../../game/skyjump/copy';

	const context = getContext();
</script>

{#if context.stateGame.screen === 'play'}
	<div class="roles">
		{#each SLOT_ROLES as role}
			<div class:final={role.id === 'multiplier'}>
				<img src={roleIconSrc[role.iconKey]} alt="" />
				<span>{t(role.shortLabel)}</span>
			</div>
		{/each}
	</div>
{/if}

<style>
	.roles {
		position: fixed;
		z-index: 12;
		left: 50%;
		bottom: 13.6rem;
		display: grid;
		grid-template-columns: repeat(6, minmax(0, 1fr));
		gap: 0.3rem;
		width: min(94vw, 1180px);
		transform: translateX(-50%);
		pointer-events: none;
	}

	div :global(div) {
		display: grid;
		justify-items: center;
		gap: 0.12rem;
		color: #9eb7c9;
		font-size: 0.58rem;
		font-weight: 800;
		letter-spacing: 0.04em;
	}

	.final {
		color: #f0c14b;
	}

	img {
		width: 24px;
		height: 24px;
	}

	@media (max-width: 720px) {
		.roles {
			bottom: 12.2rem;
			width: min(96vw, 520px);
		}

		span {
			font-size: 0.5rem;
		}

		img {
			width: 18px;
			height: 18px;
		}
	}
</style>
