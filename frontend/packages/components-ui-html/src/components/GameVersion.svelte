<script lang="ts">
	import { PUBLIC_SITE_MODE } from 'envs';

	type Props = {
		version: string; // "major.feature.patch"
	};

	const props: Props = $props();
</script>

<span class="skyjump-version">{PUBLIC_SITE_MODE}{props.version}</span>
