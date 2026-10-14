<script lang="ts">
	import { page } from '$app/state';
	import { type Snippet } from 'svelte';
	import { GlobalStyle } from 'components-ui-html';
	import { Authenticate, LoaderExample, LoadI18n } from 'components-shared';
	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';

	import messagesMap from '../i18n/messagesMap';

	type Props = { children: Snippet };

	const props: Props = $props();

	const isLocalHarness = $derived(
		page.url.pathname.startsWith('/dev-preview') || page.url.pathname.startsWith('/live-preview'),
	);

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

	<!-- Our own loader only: no platform loader at any point (guideline 275). -->
	<LoaderExample src={loaderUrl} maxWidth={720} label="" />

	{@render props.children()}
{/if}
