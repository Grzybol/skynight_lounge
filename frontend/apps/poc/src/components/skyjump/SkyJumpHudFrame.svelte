<script lang="ts">
	import { getSkyJumpHudCssDock } from 'components-ui-pixi';

	import { getContext } from '../../game/context';
	import { v2UiAssetUrl } from '../../game/skyjump_v2/uiAssetRegistry';

	const context = getContext();
	const dock = $derived(getSkyJumpHudCssDock(context.stateLayoutDerived.mainLayoutStandard()));
	const frameSrc = v2UiAssetUrl('betHudFrame');
</script>

{#if context.stateGame.screen === 'play'}
	<div class="hud-root" aria-hidden="true" data-test="skyjump-hud-frame">
		<!-- Art frame: viewport-centered; SPIN dock aligns to layout spinCx. -->
		<img
			class="hud-frame-art"
			src={frameSrc}
			alt=""
			draggable="false"
			style:top={dock.frameTop}
			style:width={dock.frameWidth}
			style:height={dock.frameHeight}
		/>
	</div>
{/if}

<style>
	.hud-root {
		position: absolute;
		z-index: 18;
		inset: 0;
		isolation: isolate;
		pointer-events: none;
		overflow: visible;
	}

	.hud-frame-art {
		position: absolute;
		z-index: 0;
		/* Precise horizontal center on the gameplay viewport — not a padded child. */
		left: 50%;
		transform: translateX(-50%);
		display: block;
		pointer-events: none;
		object-fit: fill;
		object-position: center;
		background: transparent;
		border: none;
		user-select: none;
		-webkit-user-drag: none;
		filter: drop-shadow(0 18px 36px rgba(0, 6, 18, 0.55));
	}
</style>
