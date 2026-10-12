import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const buildDir = resolve(root, 'frontend/apps/poc/build');

const NEEDLES = [
	'Twist',
	'Garden',
	'Farmer',
	'staging-1-0.twist-game.app',
	'5000x',
	'SUPERANTE',
	'SkiFly Jackpot',
	'Cashout',
	'FIXTURE/TEST ONLY',
	'DEV / TEST PAYTABLE',
	'v2-fixture:',
	'phase2-math:',
	'phase3-feature:',
];

const walk = (dir: string, acc: string[] = []): string[] => {
	for (const name of readdirSync(dir)) {
		const path = join(dir, name);
		const stat = statSync(path);
		if (stat.isDirectory()) walk(path, acc);
		else acc.push(path);
	}
	return acc;
};

const matches: Array<{ needle: string; file: string; count: number }> = [];
for (const file of walk(buildDir)) {
	if (!/\.(js|css|html|json|svg|txt|map)$/i.test(file)) continue;
	const text = readFileSync(file, 'utf8');
	for (const needle of NEEDLES) {
		let count = 0;
		let from = 0;
		while (true) {
			const at = text.indexOf(needle, from);
			if (at < 0) break;
			count += 1;
			from = at + needle.length;
		}
		if (count > 0) {
			matches.push({ needle, file: file.slice(buildDir.length + 1), count });
		}
	}
}

for (const row of matches) {
	console.log(`${row.needle}\t${row.count}\t${row.file}`);
}
if (matches.length === 0) console.log('no legacy needles in text assets');
