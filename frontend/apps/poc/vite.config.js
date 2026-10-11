import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readdirSync, writeFileSync } from 'node:fs';

import createConfig from '../../packages/config-vite/index.js';

const mathDir = resolve(dirname(fileURLToPath(import.meta.url)), '../../../math');
const config = createConfig();
const bgmDir = resolve(dirname(fileURLToPath(import.meta.url)), 'static/assets/audio/skyjump/bgm');

const writeBgmManifest = () => {
	const files = readdirSync(bgmDir)
		.filter((name) => /\.(mp3|ogg|wav|m4a)$/i.test(name))
		.sort((left, right) => left.localeCompare(right));
	writeFileSync(join(bgmDir, 'tracks.json'), `${JSON.stringify(files, null, '\t')}\n`);
};

const skyjumpBgmManifest = () => ({
	name: 'skyjump-bgm-manifest',
	buildStart() {
		writeBgmManifest();
	},
	configureServer(server) {
		writeBgmManifest();
		server.watcher.add(bgmDir);
		server.watcher.on('all', (_event, file) => {
			if (file.includes('audio/skyjump/bgm') && !file.endsWith('tracks.json')) {
				writeBgmManifest();
			}
		});
	},
});

export default {
	...config,
	build: {
		...config.build,
		// Shared config inlines every import. The lounge figure and win clips
		// are too large for that and break the Rollup IIFE render.
		assetsInlineLimit: 1024 * 1024,
	},
	cacheDir: join(tmpdir(), 'slot-game-poc-vite-cache'),
	plugins: [...(config.plugins ?? []), skyjumpBgmManifest()],
	server: {
		...config.server,
		fs: {
			...(config.server?.fs ?? {}),
			allow: [...(config.server?.fs?.allow ?? []), mathDir],
		},
		proxy: {
			...(config.server?.proxy ?? {}),
			'/api/live-math': {
				target: 'http://127.0.0.1:8765',
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api\/live-math/, ''),
			},
		},
	},
};
