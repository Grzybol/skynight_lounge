import { rmSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const poc = resolve(repoRoot, 'frontend/apps/poc');

const roots = [resolve(poc, 'build'), resolve(poc, '.svelte-kit/output/client')];

const relativeDirs = [
	'assets/spines',
	'assets/sprites',
	'assets/fonts/silverFont',
	'assets/fonts/purpleFont',
	'assets/fonts/goldFont',
	'assets/fonts/goldBlur',
	'assets/audio/skyjump/old music',
];

let removed = 0;
for (const root of roots) {
	for (const rel of relativeDirs) {
		const path = resolve(root, rel);
		if (!existsSync(path)) continue;
		rmSync(path, { recursive: true, force: true });
		removed += 1;
		console.log('stripped', path);
	}
}

console.log(`skyjump strip-legacy-static removed ${removed} directories`);
