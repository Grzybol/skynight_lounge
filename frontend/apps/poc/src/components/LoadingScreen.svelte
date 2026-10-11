<script lang="ts">
	import { FadeContainer } from 'components-pixi';

	import { getContext } from '../game/context';
	import { startSkyJumpBgm } from '../game/skyjump/skyjumpAudio';
	import LoaderArtwork from './LoaderArtwork.svelte';
	import TransitionAnimation from './TransitionAnimation.svelte';
	import PressToContinue from './PressToContinue.svelte';

	type Props = {
		onloaded: () => void;
	};

	const props: Props = $props();
	const context = getContext();

	let loadingType = $state<'start' | 'transition'>('start');
</script>

<FadeContainer show={loadingType === 'start'}>
	<LoaderArtwork
		progress={context.stateApp.loaded ? 100 : context.stateApp.loadingProgress}
		ready={context.stateApp.loaded}
	/>
</FadeContainer>

<!-- press to continue -->
<FadeContainer show={loadingType === 'start' && context.stateApp.loaded}>
	<PressToContinue
		onpress={() => {
			startSkyJumpBgm();
			loadingType = 'transition';
		}}
	/>
</FadeContainer>

<!-- transition between the loading screen and the game -->
<FadeContainer show={loadingType === 'transition'}>
	<TransitionAnimation oncomplete={props.onloaded} />
</FadeContainer>
