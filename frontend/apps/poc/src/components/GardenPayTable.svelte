<script lang="ts">
	const symbols = [
		{ key: 'h1', name: 'Gardener', pays: [10, 20, 50] },
		{ key: 'h2', name: 'Wheelbarrow', pays: [3, 5, 15] },
		{ key: 'h3', name: 'Watering Can', pays: [2, 3, 10] },
		{ key: 'h4', name: 'Shovel', pays: [1, 2, 8] },
		{ key: 'l1', name: 'Tomato', pays: [0.5, 1, 5] },
		{ key: 'l2', name: 'Aubergine', pays: [0.3, 0.7, 3] },
		{ key: 'l3', name: 'Broccoli', pays: [0.3, 0.7, 3] },
		{ key: 'l4', name: 'Blueberries', pays: [0.2, 0.5, 2] },
		{ key: 'l5', name: 'Harvest Badge', pays: [0.1, 0.3, 1] },
	];

	const positions: Record<string, string> = {
		h1: '0 0',
		h2: '-64px 0',
		h3: '-128px 0',
		h4: '-192px 0',
		l1: '-64px -64px',
		l2: '-128px -64px',
		l3: '-192px -64px',
		l4: '0 -128px',
		l5: '0 -192px',
		w: '-64px -128px',
		s: '-192px -128px',
	};
</script>

<section class="paytable">
	<header>
		<span class="kicker">GARDEN BOUNTY</span>
		<h2>PAYTABLE</h2>
		<p>All prizes are shown as multipliers of the current bet.</p>
	</header>

	<div class="grid">
		{#each symbols as symbol}
			<article>
				<div
					class="symbol"
					aria-label={symbol.name}
					style:background-position={positions[symbol.key]}
				></div>
				<strong>{symbol.name}</strong>
				<div class="pays">
					<span>3× <b>{symbol.pays[0]}</b></span>
					<span>4× <b>{symbol.pays[1]}</b></span>
					<span>5× <b>{symbol.pays[2]}</b></span>
				</div>
			</article>
		{/each}
	</div>

	<div class="specials">
		<div>
			<div class="symbol" aria-label="Wild" style:background-position={positions.w}></div>
			<p>
				<strong>WILD</strong> substitutes for regular symbols and may carry a multiplier. Pays 10 / 20
				/ 50 for 3 / 4 / 5.
			</p>
		</div>
		<div>
			<div class="symbol" aria-label="Scatter" style:background-position={positions.s}></div>
			<p><strong>SCATTER</strong> awards the Free Spins feature.</p>
		</div>
	</div>
</section>

<style>
	.paytable {
		width: min(100%, 780px);
	}

	header {
		margin-bottom: 1.25rem;
		text-align: center;
	}

	.kicker {
		color: #a9d85b;
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.25em;
	}

	h2 {
		margin: 0.15rem 0;
		color: #ffd36b;
		font-size: clamp(1.8rem, 5vw, 3rem);
		letter-spacing: 0.08em;
		text-shadow: 0 3px #315028;
	}

	header p {
		margin: 0;
		color: #eef0d5;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(120px, 1fr));
		gap: 0.65rem;
	}

	article {
		display: grid;
		justify-items: center;
		padding: 0.65rem;
		background: rgba(18, 47, 28, 0.72);
		border: 2px solid #5f8749;
		border-radius: 18px;
	}

	.symbol {
		width: 64px;
		height: 64px;
		background-image: url('/assets/sprites/symbolsGardenCandidate/symbolsGarden.webp');
		background-repeat: no-repeat;
		background-size: 256px 320px;
	}

	article strong,
	.specials strong {
		color: #ffd36b;
	}

	.pays {
		display: flex;
		gap: 0.45rem;
		margin-top: 0.35rem;
		font-size: 0.78rem;
	}

	.pays b {
		color: #fff0d0;
	}

	.specials {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
		margin-top: 0.75rem;
	}

	.specials > div {
		display: flex;
		align-items: center;
		gap: 0.7rem;
		padding: 0.65rem 0.85rem;
		background: rgba(41, 86, 49, 0.72);
		border: 2px solid #e9c75a;
		border-radius: 18px;
		text-align: left;
	}

	.specials p {
		margin: 0;
		font-size: 0.84rem;
	}

	@media (max-width: 720px) {
		.grid {
			grid-template-columns: repeat(2, 1fr);
		}

		.specials {
			grid-template-columns: 1fr;
		}
	}
</style>
