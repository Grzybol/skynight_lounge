import { cpSync, existsSync, readdirSync, rmSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const buildDir = resolve(repo, 'frontend/apps/poc/build');
const uploadRoot = resolve(repo, 'stake-upload');
const frontendOut = join(uploadRoot, 'frontend');

if (!existsSync(join(buildDir, 'index.html'))) {
	console.error('stage-stake-upload: missing frontend/apps/poc/build/index.html');
	process.exit(1);
}

rmSync(frontendOut, { recursive: true, force: true });
cpSync(buildDir, frontendOut, { recursive: true });

for (const name of readdirSync(uploadRoot)) {
	if (name.toLowerCase().endsWith('.zip')) {
		rmSync(join(uploadRoot, name), { force: true });
		console.log('removed zip', name);
	}
}

const mathDir = join(uploadRoot, 'math');
if (!existsSync(join(mathDir, 'index.json'))) {
	console.error('stage-stake-upload: stake-upload/math/index.json is missing');
	process.exit(1);
}

console.log('staged', frontendOut);
