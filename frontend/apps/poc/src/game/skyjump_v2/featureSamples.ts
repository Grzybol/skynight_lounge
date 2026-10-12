import rawSamples from '../../../../../../math/games/0_0_poc/skyjump_v2_feature_samples.json' with { type: 'json' };

import { validatePhase4bEvents } from './validateEvents.ts';
import type { BookEvent } from '../typesBookEvent.ts';

if (rawSamples.nonProduction !== true) {
	throw new Error('V2 feature samples must be marked nonProduction');
}

export type V2FeatureSample = {
	id: string;
	title: string;
	stops: number[];
	board: string[][];
	finalBoard: string[][];
	lineWinX: number;
	totalFeatureWinX: number;
	totalWinX: number;
	latentTokenValueX: number;
	coachCount: number;
	selectedSymbolIds: string[];
	tokenTiers: number[];
	events: BookEvent[];
};

export const V2_FEATURE_SAMPLES: V2FeatureSample[] = rawSamples.samples as V2FeatureSample[];

if (V2_FEATURE_SAMPLES.length < 1) {
	throw new Error('Phase 4B requires at least one feature sample');
}

export const v2FeatureSampleById = (id: string) =>
	V2_FEATURE_SAMPLES.find((row) => row.id === id || row.id === String(Number(id)).padStart(2, '0'));

export const v2FeatureSampleToBet = (sample: V2FeatureSample, spinIndex: number) => {
	validatePhase4bEvents(sample.events as Array<Record<string, unknown>>);
	const amountEvent = sample.events.find((event) => event.type === 'setTotalWin');
	const amount = amountEvent && 'amount' in amountEvent ? amountEvent.amount : 0;
	return {
		id: 60_000 + spinIndex,
		active: false,
		payoutMultiplier: sample.totalWinX,
		events: sample.events,
		state: sample.events,
		criteria: `phase4b-feature:${sample.id}`,
		baseGameWins: sample.totalWinX,
		freeGameWins: 0,
		amount,
	};
};

export const parseV2FeatureSampleQuery = (raw: string | null | undefined) => {
	if (!raw) return null;
	if (raw === 'feature' || raw === 'cycle-feature') return 'cycle' as const;
	const match = raw.match(/feature-?(\d+)/i);
	if (!match) return null;
	return v2FeatureSampleById(match[1]) ?? null;
};
