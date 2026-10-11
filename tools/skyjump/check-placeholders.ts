/**
 * Warn when Stake ACP placeholders are still in the canonical identity.
 * Local development must stay unblocked. Pass --strict to fail (release packaging).
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const canonical = JSON.parse(
	readFileSync(resolve(root, 'math/games/0_0_poc/skyjump_config.json'), 'utf8'),
) as {
	meta: { gameID: string; gameIdRenameTodo?: string };
};

const strict = process.argv.includes('--strict');
const placeholders: string[] = [];

if (canonical.meta.gameID === '0_0_poc') {
	placeholders.push('meta.gameID is still 0_0_poc');
}

const feConfig = readFileSync(resolve(root, 'frontend/apps/poc/src/game/config.ts'), 'utf8');
if (feConfig.includes("providerName: 'poc_studio'")) {
	placeholders.push('frontend providerName is still poc_studio');
}

const pythonConfig = readFileSync(resolve(root, 'math/games/0_0_poc/game_config.py'), 'utf8');
if (pythonConfig.includes('provider_number = 0') || pythonConfig.includes('poc_studio')) {
	placeholders.push('Python GameConfig still uses poc_studio / provider_number 0');
}

if (placeholders.length === 0) {
	console.log('Stake ACP identity placeholders have been replaced.');
	process.exit(0);
}

console.warn('WARNING: Stake ACP placeholders remain (do not invent values):');
for (const row of placeholders) console.warn(`  - ${row}`);
if (canonical.meta.gameIdRenameTodo) console.warn(`  - ${canonical.meta.gameIdRenameTodo}`);

if (strict) {
	console.error('Refusing to package a release while ACP placeholders remain. Pass after Stake IDs exist.');
	process.exit(1);
}

process.exit(0);
