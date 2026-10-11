/**
 * Stake hosts the built game at /{gameId}/{version}/index.html.
 * A leading slash asks the CDN origin for /assets/... and 404s.
 * Paths without a leading slash resolve against the HTML document,
 * which is also correct on the Vite dev server (/live-preview drops
 * the route segment and still hits the site-root static files).
 */
export const resolveGameAsset = (path: string): string => path.replace(/^\/+/, '');
