import adapter from '@sveltejs/adapter-static';
import createConfig from '../../packages/config-svelte/index.js';

const base = createConfig();

export default {
	...base,
	kit: {
		...base.kit,
		// Stake's version folder is not known at build time. Relative URLs
		// stay inside that folder. A single JS file gives import.meta.url a
		// real script location so hashed media resolves under _app/.
		paths: {
			...(base.kit?.paths ?? {}),
			relative: true,
		},
		output: {
			...(base.kit?.output ?? {}),
			bundleStrategy: 'single',
		},
		adapter: adapter({
			strict: false,
		}),
	},
};
