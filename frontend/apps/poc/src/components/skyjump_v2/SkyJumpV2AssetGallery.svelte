<script lang="ts">
	/**
	 * DEV-only gallery for Phase 8C UI/FX pack. Not imported from production Game tree.
	 * Shows each asset on checkerboard / white / navy so alpha is visually verifiable.
	 */
	import {
		V2_BONUS_TITLE_FILENAMES,
		V2_DECOR_FILENAMES,
		V2_FX_FILENAMES,
		V2_HEADER_FILENAMES,
		V2_WIN_TITLE_FILENAMES,
		v2FxAssetUrl,
		v2UiAssetUrl,
		type V2FxKey,
		type V2UiKey,
	} from '../../game/skyjump_v2/uiAssetRegistry';

	type Bg = 'checker' | 'white' | 'navy';

	let bg = $state<Bg>('checker');

	const sections: { title: string; items: { key: string; src: string }[] }[] = [
		{
			title: 'Win titles',
			items: (Object.keys(V2_WIN_TITLE_FILENAMES) as (keyof typeof V2_WIN_TITLE_FILENAMES)[]).map(
				(key) => ({ key, src: v2UiAssetUrl(key) }),
			),
		},
		{
			title: 'Bonus / mode',
			items: (
				Object.keys(V2_BONUS_TITLE_FILENAMES) as (keyof typeof V2_BONUS_TITLE_FILENAMES)[]
			).map((key) => ({ key, src: v2UiAssetUrl(key) })),
		},
		{
			title: 'Headers',
			items: (Object.keys(V2_HEADER_FILENAMES) as (keyof typeof V2_HEADER_FILENAMES)[]).map(
				(key) => ({ key, src: v2UiAssetUrl(key) }),
			),
		},
		{
			title: 'Decor',
			items: (Object.keys(V2_DECOR_FILENAMES) as (keyof typeof V2_DECOR_FILENAMES)[]).map(
				(key) => ({ key, src: v2UiAssetUrl(key as V2UiKey) }),
			),
		},
		{
			title: 'FX',
			items: (Object.keys(V2_FX_FILENAMES) as V2FxKey[]).map((key) => ({
				key,
				src: v2FxAssetUrl(key),
			})),
		},
	];
</script>

{#if import.meta.env.DEV}
	<section class="gallery" data-test="skyjump-v2-asset-gallery">
		<h3>Phase 8C asset gallery (DEV) — transparency check</h3>
		<div class="bg-toggle" role="group" aria-label="Gallery background">
			<button type="button" class:on={bg === 'checker'} onclick={() => (bg = 'checker')}
				>Checkerboard</button
			>
			<button type="button" class:on={bg === 'white'} onclick={() => (bg = 'white')}>White</button>
			<button type="button" class:on={bg === 'navy'} onclick={() => (bg = 'navy')}>Navy</button>
		</div>
		{#each sections as section}
			<h4>{section.title}</h4>
			<div class="grid">
				{#each section.items as item}
					<figure class:bg-checker={bg === 'checker'} class:bg-white={bg === 'white'} class:bg-navy={bg === 'navy'}>
						<img src={item.src} alt={item.key} loading="lazy" />
						<figcaption>{item.key}</figcaption>
					</figure>
				{/each}
			</div>
		{/each}
	</section>
{/if}

<style>
	.gallery {
		margin-top: 0.75rem;
		padding: 0.65rem;
		color: #d7ecf8;
		background: rgba(4, 18, 36, 0.92);
		border: 1px solid rgba(120, 200, 255, 0.35);
		border-radius: 12px;
		font: 600 11px/1.3 var(--skyjump-font-ui, system-ui, sans-serif);
		max-height: 42vh;
		overflow: auto;
	}

	h3,
	h4 {
		margin: 0 0 0.45rem;
		font-family: var(--skyjump-font-display, system-ui, sans-serif);
	}

	h4 {
		margin-top: 0.65rem;
		color: #9fd6ff;
	}

	.bg-toggle {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		margin-bottom: 0.55rem;
	}

	.bg-toggle button {
		color: #f4faff;
		background: #10283d;
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 6px;
		padding: 2px 6px;
		cursor: pointer;
	}

	.bg-toggle button.on {
		background: #1d4f72;
		border-color: #7fd0ff;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
		gap: 0.45rem;
	}

	figure {
		margin: 0;
		padding: 0.35rem;
		border-radius: 8px;
		text-align: center;
		border: 1px solid rgba(120, 200, 255, 0.2);
	}

	.bg-checker {
		background:
			linear-gradient(45deg, #bbb 25%, transparent 25%) 0 0 / 12px 12px,
			linear-gradient(-45deg, #bbb 25%, transparent 25%) 0 6px / 12px 12px,
			linear-gradient(45deg, transparent 75%, #bbb 75%) 6px -6px / 12px 12px,
			linear-gradient(-45deg, transparent 75%, #bbb 75%) -6px 0 / 12px 12px,
			#eee;
	}

	.bg-white {
		background: #ffffff;
	}

	.bg-navy {
		background: #061428;
	}

	img {
		width: 100%;
		height: 72px;
		object-fit: contain;
	}

	figcaption {
		margin-top: 0.25rem;
		font-size: 9px;
		word-break: break-all;
		opacity: 0.85;
		color: #d7ecf8;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.75);
	}

	.bg-white figcaption {
		color: #102030;
		text-shadow: none;
	}
</style>
