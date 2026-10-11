<script lang="ts">
	import { page } from '$app/state';
	import { type Snippet } from 'svelte';
	import { GlobalStyle } from 'components-ui-html';
	import { Authenticate, LoaderStakeEngine, LoaderExample, LoadI18n } from 'components-shared';
	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';

	import messagesMap from '../i18n/messagesMap';

	type Props = { children: Snippet };

	const props: Props = $props();

	let showYourLoader = $state(false);
	const isLocalHarness = $derived(
		page.url.pathname.startsWith('/dev-preview') || page.url.pathname.startsWith('/live-preview'),
	);

	const loaderUrlStakeEngine = new URL('../../stake-engine-loader.gif', import.meta.url).href;
	const loaderUrl = new URL('../../skyhighfly-studios.png', import.meta.url).href;

	setContext();
</script>

{#if isLocalHarness}
	{@render props.children()}
{:else}
	<GlobalStyle>
		<Authenticate>
			<LoadI18n {messagesMap}>
				<Game />
			</LoadI18n>
		</Authenticate>
	</GlobalStyle>

	<LoaderStakeEngine src={loaderUrlStakeEngine} oncomplete={() => (showYourLoader = true)} />

	{#if showYourLoader}
		<LoaderExample src={loaderUrl} maxWidth={720} label="" />
	{/if}

	{@render props.children()}
{/if}
