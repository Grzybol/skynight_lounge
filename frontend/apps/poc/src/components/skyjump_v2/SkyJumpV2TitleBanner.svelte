<script lang="ts">
	import {
		V2_BANNER_SLOT,
		type V2BannerKind,
	} from '../../game/skyjump_v2/presentationLayout';

	type Props = {
		src: string;
		alt?: string;
		show?: boolean;
		/** Shared presentation slot — geometry from artwork intensity, not source canvas. */
		kind?: V2BannerKind;
	};

	const props: Props = $props();
	const kind = $derived(props.kind ?? 'mode');
	const slot = $derived(V2_BANNER_SLOT[kind]);
</script>

{#if props.show !== false && props.src}
	<div
		class="title-banner"
		class:kind-bonus={kind === 'bonus'}
		class:kind-retrigger={kind === 'retrigger'}
		class:kind-tier={kind === 'tierUpgrade'}
		class:kind-mode={kind === 'mode'}
		data-test="skyjump-v2-title-banner"
		data-kind={kind}
		aria-hidden="true"
		style:--banner-max-w={`${slot.maxWidth}px`}
		style:--banner-max-h={`${slot.maxHeight}px`}
	>
		<img src={props.src} alt={props.alt ?? ''} draggable="false" />
	</div>
{/if}

<style>
	.title-banner {
		position: absolute;
		left: 50%;
		top: 38%;
		z-index: 36;
		box-sizing: border-box;
		display: grid;
		place-items: center;
		width: min(90%, var(--banner-max-w, 460px));
		height: var(--banner-max-h, 124px);
		transform: translate(-50%, -50%);
		pointer-events: none;
		animation: banner-in 320ms cubic-bezier(0.22, 0.9, 0.32, 1) both;
	}

	.title-banner.kind-retrigger {
		top: 36%;
	}

	img {
		display: block;
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		object-fit: contain;
		object-position: center;
		filter: drop-shadow(0 10px 24px rgba(0, 8, 24, 0.5));
		pointer-events: none;
	}

	@keyframes banner-in {
		from {
			opacity: 0;
			transform: translate(-50%, -44%) scale(0.94);
		}
		to {
			opacity: 1;
			transform: translate(-50%, -50%) scale(1);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.title-banner {
			animation: none;
		}
	}
</style>
