import rawSamples from '../../../../../../math/games/0_0_poc/skyjump_v2_math_samples.json' with { type: 'json' };

import { validatePhase2Events } from './validateEvents.ts';
import type { BookEvent } from '../typesBookEvent.ts';

if (rawSamples.nonProduction !== true) {
	throw new Error('V2 math samples must be marked nonProduction');
}

export type V2MathSample = {
	id: string;
	title: string;
	stops: number[];
	board: string[][];
	lineWinX: number;
	totalFeatureWinX: number;
	totalWinX: number;
	scatterCount: number;
	perfectV: boolean;
	events: BookEvent[];
};

export const V2_MATH_SAMPLES: V2MathSample[] = rawSamples.samples as V2MathSample[];

if (V2_MATH_SAMPLES.length < 1) {
	throw new Error('Phase 2 requires at least one math sample');
}

export const v2MathSampleById = (id: string) =>
	V2_MATH_SAMPLES.find((row) => row.id === id || row.id === String(Number(id)).padStart(2, '0'));

export const v2MathSampleToBet = (sample: V2MathSample, spinIndex: number) => {
	validatePhase2Events(sample.events as Array<Record<string, unknown>>);
	const amountEvent = sample.events.find((event) => event.type === 'setTotalWin');
	const amount = amountEvent && 'amount' in amountEvent ? amountEvent.amount : 0;
	return {
		id: 50_000 + spinIndex,
		active: false,
		payoutMultiplier: sample.totalWinX,
		events: sample.events,
		state: sample.events,
		criteria: `phase2-math:${sample.id}`,
		baseGameWins: sample.totalWinX,
		freeGameWins: 0,
		amount,
	};
};

export const parseV2MathSampleQuery = (raw: string | null | undefined) => {
	if (!raw) return null;
	if (raw === 'math' || raw === 'cycle-math') return 'cycle' as const;
	const match = raw.match(/math-?(\d+)/i);
	if (!match) return null;
	return v2MathSampleById(match[1]) ?? null;
};
