/** DEV-only World Record samples. Do not import from production paths. */

import rawWrSamples from '../../../../../../math/games/0_0_poc/skyjump_v2_wr_samples.json' with { type: 'json' };

import { resumeBookEvents } from './snapshotResume.ts';
import type { BookEvent } from '../typesBookEvent.ts';

if (rawWrSamples.nonProduction !== true) {
	throw new Error('V2 WR samples must be marked nonProduction');
}

export type V2WrSample = {
	id: string;
	title: string;
	resumeIndex: number | null;
	flags: Record<string, unknown>;
	eventCount: number;
	wrEventIndex: number | null;
	events: BookEvent[];
	roundWinXCapped: number;
	maxWinReached?: boolean;
};

export const V2_WR_SAMPLES = (rawWrSamples.samples || []) as V2WrSample[];

export const v2WrSampleById = (id: string) =>
	V2_WR_SAMPLES.find((row) => row.id === id || row.id === String(Number(id)).padStart(2, '0'));

export const v2WrSampleToBet = (sample: V2WrSample, spinIndex: number) => {
	const events =
		sample.resumeIndex == null
			? sample.events
			: resumeBookEvents(sample.events, sample.resumeIndex);
	const amountEvent = [...events].reverse().find((event) => event.type === 'finalWin');
	const amount = amountEvent && 'amount' in amountEvent ? amountEvent.amount : 0;
	return {
		id: 95_000 + spinIndex,
		active: sample.resumeIndex != null,
		event: sample.resumeIndex == null ? '' : '0',
		payoutMultiplier: sample.roundWinXCapped,
		events,
		state: events,
		criteria: `phase7b-wr:${sample.id}`,
		baseGameWins: 0,
		freeGameWins: sample.roundWinXCapped,
		amount,
	};
};

export const parseV2WrSampleQuery = (raw: string | null | undefined) => {
	if (!raw) return null;
	if (raw === 'wr' || raw === 'cycle-wr') return 'cycle-wr' as const;
	const match = raw.match(/wr[-_]?(\d+)/i);
	if (!match) return null;
	return v2WrSampleById(match[1]) ?? null;
};
