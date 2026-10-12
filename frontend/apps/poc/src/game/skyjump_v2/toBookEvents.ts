import { V2_BOOK_AMOUNT_MULTIPLIER, V2_EVENT_SCHEMA_VERSION } from './config.ts';
import type { V2Fixture } from './fixtures.ts';
import { pythonRoundHalfEven } from '../skyjump/roundBookAmount.ts';
import { validatePhase1Events } from './validateEvents.ts';
import type { BookEvent } from '../typesBookEvent.ts';

const roundAmount = (winX: number) => pythonRoundHalfEven(winX * V2_BOOK_AMOUNT_MULTIPLIER);

export const v2FixtureToBookEvents = (fixture: V2Fixture): BookEvent[] => {
	const lineWinX = fixture.expected.lineWinX;
	const amount = roundAmount(lineWinX);
	const events = [
		{
			index: 0,
			type: 'skyjumpSpinStart' as const,
			schemaVersion: 2 as const,
			mode: 'BASE',
			isFreeSpin: false,
			fixtureId: fixture.id,
		},
		{
			index: 1,
			type: 'skyjumpBoardReveal' as const,
			schemaVersion: 2 as const,
			board: fixture.board,
		},
		{
			index: 2,
			type: 'skyjumpLineWins' as const,
			schemaVersion: 2 as const,
			wins: fixture.expected.wins,
			lineWinX,
		},
		{
			index: 3,
			type: 'skyjumpResult' as const,
			schemaVersion: 2 as const,
			totalLineWinX: lineWinX,
			totalFeatureWinX: 0,
			totalWinX: lineWinX,
			amount,
		},
		{
			index: 4,
			type: 'setTotalWin' as const,
			amount,
		},
		{
			index: 5,
			type: 'finalWin' as const,
			amount,
		},
	];
	validatePhase1Events(events);
	void V2_EVENT_SCHEMA_VERSION;
	return events;
};

export const v2FixtureToBet = (fixture: V2Fixture, spinIndex: number) => {
	const events = v2FixtureToBookEvents(fixture);
	const amountEvent = events.find((event) => event.type === 'setTotalWin');
	const amount = amountEvent && 'amount' in amountEvent ? amountEvent.amount : 0;
	return {
		id: 40_000 + spinIndex,
		active: false,
		payoutMultiplier: fixture.expected.lineWinX,
		events,
		state: events,
		criteria: `phase1-dev:${fixture.id}`,
		baseGameWins: fixture.expected.lineWinX,
		freeGameWins: 0,
		amount,
	};
};
