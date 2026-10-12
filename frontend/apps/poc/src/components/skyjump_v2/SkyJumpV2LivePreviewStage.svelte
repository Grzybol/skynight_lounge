/**
 * DEV live-preview wrapper: Stake-like 1280×720 logical stage, letterboxed/scaled.
 * Presets CSS-scale the logical canvas — they do not redesign layout independently.
 * Does not affect production `/` embed or `/dev-preview` debug layout.
 */
<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';

	import {
		LIVE_PREVIEW_LOGICAL,
		LIVE_PREVIEW_PRESETS,
		fitStageSize,
		type LivePreviewPresetId,
	} from '../../game/skyjump_v2/livePreviewStage';

	type Props = {
		children: Snippet;
		/** Optional chrome above the stage (live-math badge, etc.). */
		chrome?: Snippet;
	};

	const props: Props = $props();

	let presetId = $state<LivePreviewPresetId>('1280x720');
	let backgroundOnly = $state(false);
	let hostEl = $state<HTMLDivElement | null>(null);
	let stageEl = $state<HTMLDivElement | null>(null);
	let hostW = $state(LIVE_PREVIEW_LOGICAL.width);
	let hostH = $state(LIVE_PREVIEW_LOGICAL.height);

	const preset = $derived(
		LIVE_PREVIEW_PRESETS.find((p) => p.id === presetId) ?? LIVE_PREVIEW_PRESETS[0]!,
	);

	const stageBox = $derived.by(() => {
		if (preset.id === 'fit') {
			return fitStageSize(hostW, hostH);
		}
		// Cap preset to available host so small windows never stretch.
		return fitStageSize(
			Math.min(hostW, preset.width),
			Math.min(hostH, preset.height),
		);
	});

	const bumpPixiResize = () => {
		// Pixi resizeTo element listens to ResizeObserver; force a paint tick.
		if (!stageEl) return;
		stageEl.dispatchEvent(new Event('resize'));
		window.dispatchEvent(new Event('resize'));
	};

	onMount(() => {
		const measure = () => {
			if (!hostEl) return;
			hostW = hostEl.clientWidth;
			hostH = hostEl.clientHeight;
			bumpPixiResize();
		};
		measure();
		const ro = new ResizeObserver(measure);
		if (hostEl) ro.observe(hostEl);
		window.addEventListener('resize', measure);
		return () => {
			ro.disconnect();
			window.removeEventListener('resize', measure);
		};
	});

	$effect(() => {
		// Touch stageBox so preset changes remeasure / resize.
		void stageBox.width;
		void stageBox.height;
		void stageBox.scale;
		queueMicrotask(bumpPixiResize);
	});
</script>

<div class="live-shell" data-test="live-preview-shell">
	{#if props.chrome}
		<div class="chrome">
			{@render props.chrome()}
		</div>
	{/if}

	{#if import.meta.env.DEV}
		<div class="presets" data-test="live-preview-presets">
			<span class="presets-label">Stage</span>
			{#each LIVE_PREVIEW_PRESETS as p}
				<button
					type="button"
					class:on={presetId === p.id}
					data-test={`live-preset-${p.id}`}
					onclick={() => (presetId = p.id)}>{p.label}</button
				>
			{/each}
			<button
				type="button"
				class:on={backgroundOnly}
				data-test="live-preset-background-only"
				onclick={() => (backgroundOnly = !backgroundOnly)}>background only</button
			>
			<span class="meta"
				>{LIVE_PREVIEW_LOGICAL.width}×{LIVE_PREVIEW_LOGICAL.height} logical · display {stageBox.width}×{stageBox.height}
				· scale {stageBox.scale.toFixed(3)}</span
			>
		</div>
	{/if}

	<div class="host" bind:this={hostEl} data-test="live-preview-host">
		<div
			class="frame"
			data-test="live-preview-stage"
			style:width={`${stageBox.width}px`}
			style:height={`${stageBox.height}px`}
		>
			<div
				class="stage"
				class:bg-only={backgroundOnly}
				bind:this={stageEl}
				data-skyjump-preview-stage
				data-test="live-preview-logical"
				style:width={`${LIVE_PREVIEW_LOGICAL.width}px`}
				style:height={`${LIVE_PREVIEW_LOGICAL.height}px`}
				style:transform={`scale(${stageBox.scale})`}
			>
				{@render props.children()}
			</div>
		</div>
	</div>
</div>

<style>
	.live-shell {
		display: flex;
		flex-direction: column;
		width: 100%;
		height: 100dvh;
		min-height: 100dvh;
		overflow: hidden;
		background: #050b14;
	}

	.chrome {
		flex: 0 0 auto;
		z-index: 1200;
	}

	.presets {
		flex: 0 0 auto;
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		align-items: center;
		justify-content: center;
		padding: 6px 10px 8px;
		color: #cfe6f8;
		background: rgba(4, 18, 36, 0.92);
		border-bottom: 1px solid rgba(120, 200, 255, 0.22);
		font: 600 10px/1.3 var(--skyjump-font-ui, system-ui, sans-serif);
	}

	.presets-label {
		margin-right: 4px;
		color: #7ad0ff;
		font-family: var(--skyjump-font-display, system-ui, sans-serif);
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.presets button {
		height: 22px;
		padding: 0 8px;
		color: #e8f6ff;
		background: rgba(20, 60, 96, 0.95);
		border: 1px solid rgba(120, 200, 255, 0.4);
		border-radius: 999px;
		font: inherit;
		cursor: pointer;
	}

	.presets button.on {
		background: #1d5f8c;
		border-color: #7fd0ff;
	}

	.meta {
		opacity: 0.75;
		margin-left: 4px;
	}

	.host {
		flex: 1 1 auto;
		display: grid;
		place-items: center;
		min-height: 0;
		padding: 8px;
		background:
			radial-gradient(ellipse at center, rgba(20, 48, 80, 0.45), transparent 65%),
			#050b14;
	}

	.frame {
		position: relative;
		overflow: hidden;
		background: #071526;
		box-shadow:
			0 0 0 1px rgba(120, 200, 255, 0.28),
			0 18px 48px rgba(0, 0, 0, 0.55);
	}

	.stage {
		position: absolute;
		top: 0;
		left: 0;
		transform-origin: top left;
	}

	.stage :global(.skyjump-viewport) {
		width: 100%;
		height: 100%;
		min-height: 0;
	}

	/* Layout still runs so the background can align to the slot. */
	.stage.bg-only :global(.skyjump-viewport > *:not([data-lounge-bg]):not([data-lounge-figure])) {
		visibility: hidden !important;
		pointer-events: none !important;
	}
</style>
