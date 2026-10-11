/** Client for tools/skyjump/live_math_server.py — natural V2 resolve, not fixtures. */

import { V2_BUY_MODES } from './config.ts';
import type { BookEvent } from '../typesBookEvent.ts';

export type LiveMathSession = {
	spins: number;
	sessionRtpPct: number | null;
	wageredCostX: number;
	returnedWinX: number;
	hits: number;
	bonuses: number;
	note?: string;
};

export type LiveMathPlayResponse = {
	id: number;
	mode: string;
	seed: number | null;
	costMultiplier: number;
	roundWinXCapped: number;
	roundWinXRaw: number;
	isBonus: boolean;
	events: BookEvent[];
	payoutMultiplier: number;
	amount: number;
	criteria: string;
	baseGameWins: number;
	freeGameWins: number;
	mathVersion: number;
	session: LiveMathSession;
};

export type LiveMathHealth = {
	ok: boolean;
	service: string;
	mathVersion: number;
	mathStatus?: string;
	baseLutRtpPct?: number;
	modes: string[];
};

const envBase =
	typeof import.meta !== 'undefined'
		? (import.meta as { env?: { VITE_LIVE_MATH_URL?: string } }).env?.VITE_LIVE_MATH_URL
		: undefined;

/** Prefer Vite proxy (same origin); fall back to direct math server. */
const LIVE_MATH_BASE = envBase || '/api/live-math';

const LIVE_MATH_FALLBACK = 'http://127.0.0.1:8765';

let lastSession: LiveMathSession | null = null;
const listeners = new Set<(session: LiveMathSession | null) => void>();

export const getLiveMathSession = () => lastSession;

export const subscribeLiveMathSession = (fn: (session: LiveMathSession | null) => void) => {
	listeners.add(fn);
	fn(lastSession);
	return () => {
		listeners.delete(fn);
	};
};

const publishSession = (session: LiveMathSession | null) => {
	lastSession = session;
	for (const fn of listeners) fn(session);
};

export const isLiveMathQuery = (search = typeof location !== 'undefined' ? location.search : '') => {
	const params = new URLSearchParams(search.startsWith('?') ? search : `?${search}`);
	const source = (params.get('source') ?? '').toLowerCase();
	const mode = (params.get('mode') ?? '').toLowerCase();
	return source === 'live' || mode === 'live' || params.get('live') === '1';
};

export const liveMathUrl = (path: string, base = LIVE_MATH_BASE) => {
	const root = base.replace(/\/$/, '');
	const suffix = path.startsWith('/') ? path : `/${path}`;
	return `${root}${suffix}`;
};

const fetchJson = async (path: string, init?: RequestInit) => {
	const tryBases = envBase
		? [envBase]
		: [LIVE_MATH_BASE, LIVE_MATH_FALLBACK];
	let lastError: Error | null = null;
	for (const base of tryBases) {
		try {
			const res = await fetch(liveMathUrl(path, base), init);
			if (!res.ok) {
				let detail = `live-math ${path} ${res.status}`;
				try {
					const err = (await res.json()) as { error?: string };
					if (err.error) detail = err.error;
				} catch {
					/* ignore */
				}
				lastError = new Error(detail);
				continue;
			}
			return (await res.json()) as unknown;
		} catch (err: unknown) {
			lastError = err instanceof Error ? err : new Error(String(err));
		}
	}
	throw lastError ?? new Error('live-math unreachable');
};

export const fetchLiveMathHealth = async (): Promise<LiveMathHealth> =>
	(await fetchJson('/health')) as LiveMathHealth;

export const resetLiveMathStats = async () => {
	await fetchJson('/reset-stats', { method: 'POST' });
	publishSession({
		spins: 0,
		sessionRtpPct: null,
		wageredCostX: 0,
		returnedWinX: 0,
		hits: 0,
		bonuses: 0,
	});
};

export const requestLiveMathPlay = async (modeKey: string, seed?: number | null) => {
	const mode = modeKey in V2_BUY_MODES ? modeKey : 'BASE';
	const payload = (await fetchJson('/play', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			mode,
			...(seed != null && Number.isFinite(seed) ? { seed } : {}),
		}),
	})) as LiveMathPlayResponse;
	publishSession(payload.session);
	return payload;
};

export const livePlayToBet = (play: LiveMathPlayResponse) => ({
	id: play.id,
	active: false,
	payoutMultiplier: play.payoutMultiplier,
	events: play.events,
	state: play.events,
	criteria: play.criteria,
	baseGameWins: play.baseGameWins,
	freeGameWins: play.freeGameWins,
	amount: play.amount,
});
