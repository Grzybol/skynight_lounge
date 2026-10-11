import rawFixtures from '../../../../../../math/games/0_0_poc/skyjump_v2_phase1_fixtures.json' with { type: 'json' };

import { V2_DEV_PAYTABLE } from './devPaytable.ts';
import { evaluatePaylines } from './evaluatePaylines.ts';
import type { V2Board, V2EvaluateResult } from './types.ts';

if (rawFixtures.nonProduction !== true) {
	throw new Error('V2 phase 1 fixtures must be marked nonProduction');
}

export type V2Fixture = {
	id: string;
	title: string;
	board: V2Board;
	expected: V2EvaluateResult;
};

const defineFixture = (id: string, title: string, board: V2Board): V2Fixture => {
	if (board.length !== 5 || board.some((col) => col.length !== 5)) {
		throw new Error(`Fixture ${id} board must be 5×5`);
	}
	return { id, title, board, expected: evaluatePaylines(board, V2_DEV_PAYTABLE) };
};

export const V2_FIXTURES: V2Fixture[] = (
	rawFixtures.fixtures as Array<{ id: string; title: string; board: V2Board }>
).map((row) => defineFixture(row.id, row.title, row.board));

if (V2_FIXTURES.length !== 10) {
	throw new Error('Phase 1 requires exactly 10 fixtures');
}

export const v2FixtureById = (id: string) => V2_FIXTURES.find((row) => row.id === id);

const normalizeFixtureId = (raw: string) => {
	const digits = raw.replace(/\D/g, '');
	if (!digits) return raw;
	return String(Number(digits)).padStart(2, '0');
};

export const parseV2FixtureQuery = (search = '') => {
	const params = new URLSearchParams(search.startsWith('?') ? search : `?${search}`);
	const raw = params.get('fixture') ?? params.get('v2Fixture');
	if (!raw) return null;
	return v2FixtureById(normalizeFixtureId(raw)) ?? v2FixtureById(raw) ?? null;
};

export const resolveDevFixtureId = (raw: string | null | undefined) => {
	if (!raw) return null;
	return v2FixtureById(normalizeFixtureId(raw)) ?? v2FixtureById(raw) ?? null;
};
