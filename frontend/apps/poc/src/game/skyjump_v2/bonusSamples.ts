import rawSamples from '../../../../../../math/games/0_0_poc/skyjump_v2_bonus_samples.json' with { type: 'json' };
import rawPhase6Samples from '../../../../../../math/games/0_0_poc/skyjump_v2_phase6_samples.json' with { type: 'json' };

import { resumeBookEvents } from './snapshotResume.ts';
import type { BookEvent } from '../typesBookEvent.ts';

if (rawSamples.nonProduction !== true) {
	throw new Error('V2 bonus samples must be marked nonProduction');
}

export type V2BonusSample = {
	id: string;
	title: string;
	resumeIndex: number | null;
	expect: {
		startTier: string;
		finalTier: string;
		spinsPlayed: number;
		totalAwarded: number;
		roundWinX: number;
		maxWinReached: boolean;
		[key: string]: unknown;
	};
	events: BookEvent[];
};

export const V2_BONUS_SAMPLES = rawSamples.samples as V2BonusSample[];

if (V2_BONUS_SAMPLES.length !== 24) {
	throw new Error('Phase 5C requires 24 bonus samples');
}

export type V2Phase6Sample = {
	id: string;
	title: string;
	seed: number;
	resumeIndex: number | null;
	flags: Record<string, unknown>;
	eventCount: number;
	events: BookEvent[];
	roundWinXCapped: number;
};

export const V2_PHASE6_SAMPLES = ((rawPhase6Samples as { samples?: V2Phase6Sample[] }).samples ||
	[]) as V2Phase6Sample[];

export const v2BonusSampleById = (id: string) =>
	V2_BONUS_SAMPLES.find((row) => row.id === id || row.id === String(Number(id)).padStart(2, '0'));

export const v2Phase6SampleById = (id: string) =>
	V2_PHASE6_SAMPLES.find((row) => row.id === id || row.id.includes(id));

export const v2BonusSampleToBet = (sample: V2BonusSample, spinIndex: number) => {
	const events =
		sample.resumeIndex == null
			? sample.events
			: resumeBookEvents(sample.events, sample.resumeIndex);
	const amountEvent = [...events].reverse().find((event) => event.type === 'finalWin');
	const amount = amountEvent && 'amount' in amountEvent ? amountEvent.amount : 0;
	return {
		id: 80_000 + spinIndex,
		active: sample.resumeIndex != null,
		event: sample.resumeIndex == null ? '' : '0',
		payoutMultiplier: sample.expect.roundWinX,
		events,
		state: events,
		criteria: `phase5c-bonus:${sample.id}`,
		baseGameWins: 0,
		freeGameWins: sample.expect.roundWinX,
		amount,
	};
};

export const v2Phase6SampleToBet = (sample: V2Phase6Sample, spinIndex: number) => {
	const events =
		sample.resumeIndex == null
			? sample.events
			: resumeBookEvents(sample.events, sample.resumeIndex);
	const amountEvent = [...events].reverse().find((event) => event.type === 'finalWin');
	const amount = amountEvent && 'amount' in amountEvent ? amountEvent.amount : 0;
	return {
		id: 90_000 + spinIndex,
		active: sample.resumeIndex != null,
		event: sample.resumeIndex == null ? '' : '0',
		payoutMultiplier: sample.roundWinXCapped,
		events,
		state: events,
		criteria: `phase6b-sample:${sample.id}`,
		baseGameWins: 0,
		freeGameWins: sample.roundWinXCapped,
		amount,
	};
};

export const parseV2BonusSampleQuery = (raw: string | null | undefined) => {
	if (!raw) return null;
	if (raw === 'bonus' || raw === 'cycle-bonus') return 'cycle' as const;
	if (raw === 'phase6' || raw === 'cycle-phase6') return 'cycle-phase6' as const;
	const phase6 = raw.match(/phase6[-_]?([a-z0-9_]+)/i);
	if (phase6) {
		return v2Phase6SampleById(phase6[1]) ?? null;
	}
	const match = raw.match(/bonus-?(\d+)/i);
	if (!match) return null;
	return v2BonusSampleById(match[1]) ?? null;
};
