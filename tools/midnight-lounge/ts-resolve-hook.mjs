// Lets node (--experimental-strip-types) import the app's extensionless TS modules.
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export async function resolve(specifier, context, nextResolve) {
	if (specifier.startsWith('.') && !/\.[cm]?[jt]s$/.test(specifier) && context.parentURL) {
		const base = new URL(specifier, context.parentURL);
		for (const ext of ['.ts', '/index.ts']) {
			const candidate = new URL(base.href + ext);
			if (existsSync(fileURLToPath(candidate))) return nextResolve(candidate.href, context);
		}
	}
	return nextResolve(specifier, context);
}
