<script lang="ts">
	import { stateBet, stateBetDerived, stateModal } from 'state-shared';
	import { writeDevFixtureSelection } from '../../game/skyjump_v2/devSession';
	import { bonusHud } from '../../game/skyjump_v2/bonusHud.svelte';
	import { V2_PHASE6_SAMPLES } from '../../game/skyjump_v2/bonusSamples';
	import { V2_WR_SAMPLES } from '../../game/skyjump_v2/wrSamples';
	import { gameActor } from '../../game/actor';
	import { isV2PresentationLocked } from '../../game/skyjump_v2/presentationLock';
	import SkyJumpV2AssetGallery from './SkyJumpV2AssetGallery.svelte';
	import SkyJumpV2UiPackShowcase from './SkyJumpV2UiPackShowcase.svelte';

	const bonusIds = Array.from({ length: 24 }, (_, index) => String(index + 1).padStart(2, '0'));
	const mathIds = ['01', '02', '03', '04', '05', '06', '07', '08'];
	const featureIds = Array.from({ length: 17 }, (_, index) => String(index + 1).padStart(2, '0'));
	const fixtureIds = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'];
	const phase6Ids = V2_PHASE6_SAMPLES.map((sample) => sample.id);
	const wrIds = V2_WR_SAMPLES.map((sample) => sample.id);

	/** Named presentation shortcuts — DEV fixtures only, no math changes. */
	const SCENARIOS = [
		{ label: 'UI PACK SHOWCASE', sel: 'ui:showcase' },
		{ label: 'BIG WIN (full round)', sel: 'ui:big' },
		{ label: 'MEGA WIN (full round)', sel: 'ui:mega' },
		{ label: 'SUPER WIN (full round)', sel: 'ui:super' },
		{ label: 'MAX WIN (full round)', sel: 'ui:max' },
		{ label: 'ROYAL WIN (full round)', sel: 'ui:worldRecord' },
		{ label: 'FREE SPINS title (showcase)', sel: 'ui:fs' },
		{ label: 'RETRIGGER title (showcase)', sel: 'ui:retrigger' },
		{ label: 'TIER UPGRADE title (showcase)', sel: 'ui:tierUpgrade' },
		{ label: 'MODE Velvet Room (showcase)', sel: 'ui:modeLH' },
		{ label: 'MODE Gold Room (showcase)', sel: 'ui:modeSF' },
		{ label: 'MODE Diamond Lounge (showcase)', sel: 'ui:modeWC' },
		{ label: 'MODE Midnight Suite (showcase)', sel: 'ui:modePV' },
		{ label: 'Scatter → FS Start', sel: 'bonus-01' },
		{ label: 'FS Retrigger / tier up', sel: 'bonus-05' },
		{ label: 'Tier Upgrade path', sel: 'bonus-06' },
		{ label: 'Mystery / Coach', sel: 'feature-14' },
		{ label: 'Token (no collector)', sel: 'feature-01' },
		{ label: 'Thermal', sel: 'feature-08' },
		{ label: 'Gate', sel: 'feature-11' },
		{ label: 'Judge', sel: 'feature-03' },
		{ label: 'Head Judge', sel: 'feature-05' },
		{ label: 'Rejump', sel: 'phase6-10_rejump' },
		{ label: 'Wind Charge', sel: 'phase6-01_wind_charge' },
		{ label: 'Wind Upgrade', sel: 'phase6-02_wind_upgrade' },
		{ label: 'World Record (book)', sel: 'wr-01' },
		{ label: 'Max Win / Cap (book)', sel: 'feature-17' },
		{ label: 'Bonus End (WR settle)', sel: 'wr-12' },
		{ label: 'Paytable (decorated)', sel: 'modal:paytable' },
		{ label: 'Info / Rules (decorated)', sel: 'modal:rules' },
	] as const;

	let sourcePick = $state('fixtures');
	let fixturePick = $state('cycle');
	let scenarioPick = $state('');
	let showGallery = $state(false);
	let showShowcase = $state(false);
	let showcaseFocus = $state('');

	const idsForSource = () => {
		if (sourcePick === 'bonus') return bonusIds;
		if (sourcePick === 'math') return mathIds;
		if (sourcePick === 'feature') return featureIds;
		if (sourcePick === 'phase6') return phase6Ids;
		if (sourcePick === 'wr') return wrIds;
		return fixtureIds;
	};

	const writePick = (value: string) => {
		fixturePick = value;
		if (sourcePick === 'bonus') {
			writeDevFixtureSelection(value === 'bonus' ? 'bonus' : `bonus-${value}`);
			return;
		}
		if (sourcePick === 'math') {
			writeDevFixtureSelection(value === 'math' ? 'math' : `math-${value}`);
			return;
		}
		if (sourcePick === 'feature') {
			writeDevFixtureSelection(value === 'feature' ? 'feature' : `feature-${value}`);
			return;
		}
		if (sourcePick === 'phase6') {
			writeDevFixtureSelection(value === 'phase6' ? 'phase6' : `phase6-${value}`);
			return;
		}
		if (sourcePick === 'wr') {
			writeDevFixtureSelection(value === 'wr' ? 'wr' : `wr-${value}`);
			return;
		}
		writeDevFixtureSelection(value === 'cycle' ? null : value);
	};

	const onSourcePick = (event: Event) => {
		sourcePick = (event.currentTarget as HTMLSelectElement).value;
		scenarioPick = '';
		if (sourcePick === 'bonus') writePick('01');
		else if (sourcePick === 'math') writePick('math');
		else if (sourcePick === 'feature') writePick('feature');
		else if (sourcePick === 'phase6') writePick(phase6Ids[0] ?? 'phase6');
		else if (sourcePick === 'wr') writePick(wrIds[0] ?? 'wr');
		else writePick('cycle');
	};

	/**
	 * Win cards play a real book in that tier, not a detached overlay.
	 * feature-09 is 43× (big), 10 is 58× (mega), 15 is 1094× (super), 17 is the cap.
	 */
	const WIN_ROUND: Record<string, string> = {
		'ui:big': 'feature-09',
		'ui:mega': 'feature-10',
		'ui:super': 'feature-15',
		'ui:max': 'feature-17',
		'ui:worldRecord': 'wr-01',
	};

	const playArmedRound = () => {
		if (isV2PresentationLocked()) return;
		gameActor.send({ type: 'BET' });
	};

	const armBook = (sel: string) => {
		writeDevFixtureSelection(sel);
		if (sel.startsWith('bonus-')) {
			sourcePick = 'bonus';
			fixturePick = sel.replace(/^bonus-/, '');
		} else if (sel.startsWith('feature-')) {
			sourcePick = 'feature';
			fixturePick = sel.replace(/^feature-/, '');
		} else if (sel.startsWith('phase6-')) {
			sourcePick = 'phase6';
			fixturePick = sel.replace(/^phase6-/, '');
		} else if (sel.startsWith('wr-')) {
			sourcePick = 'wr';
			fixturePick = sel.replace(/^wr-/, '');
		}
	};

	const applyScenario = (sel: string) => {
		scenarioPick = sel;
		if (sel === 'modal:paytable') {
			stateModal.modal = { name: 'payTable' };
			return;
		}
		if (sel === 'modal:rules') {
			stateModal.modal = { name: 'gameRules' };
			return;
		}
		if (sel === 'ui:showcase') {
			showShowcase = true;
			showcaseFocus = '';
			return;
		}
		const winBook = WIN_ROUND[sel];
		if (winBook) {
			showShowcase = false;
			showcaseFocus = '';
			armBook(winBook);
			playArmedRound();
			return;
		}
		if (sel.startsWith('ui:')) {
			showShowcase = true;
			showcaseFocus = sel.slice(3);
			return;
		}
		armBook(sel);
		playArmedRound();
	};

	const step = (direction: number) => {
		const ids = idsForSource();
		if (!ids.length) return;
		const current = ids.indexOf(fixturePick);
		const next = ids[(current + direction + ids.length) % ids.length];
		writePick(next);
	};

	const replay = () => {
		gameActor.send({ type: 'BET' });
	};

	const toggleTurbo = () => {
		stateBetDerived.updateIsTurbo(!stateBet.isTurbo, { persistent: true });
	};
</script>

<div class="dev-source" data-test="skyjump-v2-dev-source">
	<label>
		Scenario
		<select
			value={scenarioPick}
			onchange={(event) => applyScenario((event.currentTarget as HTMLSelectElement).value)}
		>
			<option value="">— pick feature —</option>
			{#each SCENARIOS as s}
				<option value={s.sel}>{s.label}</option>
			{/each}
		</select>
	</label>
	<label>
		Source
		<select value={sourcePick} onchange={onSourcePick}>
			<option value="fixtures">FIXTURES</option>
			<option value="math">MATH SAMPLE</option>
			<option value="feature">FEATURE SAMPLE</option>
			<option value="bonus">BONUS SAMPLE</option>
			<option value="phase6">PHASE 6 SAMPLE</option>
			<option value="wr">ROYAL WIN</option>
		</select>
	</label>
	<label>
		Pick
		<select
			value={fixturePick}
			onchange={(event) => writePick((event.currentTarget as HTMLSelectElement).value)}
		>
			{#if sourcePick === 'bonus'}
				<option value="bonus">cycle 01–24</option>
				{#each bonusIds as id}
					<option value={id}>{id}</option>
				{/each}
			{:else if sourcePick === 'math'}
				<option value="math">cycle samples</option>
				{#each mathIds as id}
					<option value={id}>{id}</option>
				{/each}
			{:else if sourcePick === 'feature'}
				<option value="feature">cycle features</option>
				{#each featureIds as id}
					<option value={id}>{id}</option>
				{/each}
			{:else if sourcePick === 'phase6'}
				<option value="phase6">cycle phase6</option>
				{#each phase6Ids as id}
					<option value={id}>{id}</option>
				{/each}
			{:else if sourcePick === 'wr'}
				<option value="wr">cycle WR 01–14</option>
				{#each wrIds as id}
					<option value={id}>{id}</option>
				{/each}
			{:else}
				<option value="cycle">cycle 01–10</option>
				{#each fixtureIds as id}
					<option value={id}>{id}</option>
				{/each}
			{/if}
		</select>
	</label>
	<button type="button" onclick={() => step(-1)}>Previous</button>
	<button type="button" onclick={() => step(1)}>Next</button>
	<button type="button" onclick={replay}>Replay</button>
	<button type="button" data-test="dev-turbo" onclick={toggleTurbo}>
		Turbo {stateBet.isTurbo ? 'on' : 'off'}
	</button>
	<button type="button" data-test="dev-asset-gallery" onclick={() => (showGallery = !showGallery)}>
		Assets {showGallery ? '▾' : '▸'}
	</button>
	<button type="button" data-test="dev-ui-showcase" onclick={() => (showShowcase = !showShowcase)}>
		UI Showcase {showShowcase ? '▾' : '▸'}
	</button>
	<p data-test="dev-bonus-flag">bonus active {bonusHud.active ? 'true' : 'false'}</p>
	{#if showShowcase}
		<SkyJumpV2UiPackShowcase focus={showcaseFocus} />
	{/if}
	{#if showGallery}
		<SkyJumpV2AssetGallery />
	{/if}
</div>

<style>
	.dev-source {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		align-items: center;
		margin-top: 6px;
	}

	button,
	select {
		color: #f4faff;
		background: #10283d;
		border: 1px solid rgba(101, 200, 255, 0.45);
		border-radius: 6px;
	}

	button {
		padding: 2px 6px;
		cursor: pointer;
	}

	p {
		width: 100%;
		margin: 0;
	}
</style>
