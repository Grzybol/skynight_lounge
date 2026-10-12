import type { Bet } from '../typesBookEvent';

type BookLike = {
	state?: Array<{ type?: string }>;
	event?: string | number | null;
	active?: boolean;
};

const hasBookType = (
	events: Array<{ type?: string; bookEvents?: Array<{ type?: string }> }>,
	type: string,
) =>
	events.some((event) => {
		if (event?.type === type) return true;
		if (event?.type !== 'createBonusSnapshot') return false;
		return (event.bookEvents ?? []).some((inner) => inner?.type === type);
	});

/** Authoritative bonus detection from the book, not a UI flag. */
export const checkIsBonusGame = (bet: BookLike | null | undefined): boolean => {
	const events = bet?.state ?? [];
	if (!hasBookType(events, 'skyjumpFreeSpinsStart')) return false;
	if (bet?.active) return true;
	const end = events.findIndex((event) => event?.type === 'skyjumpFreeSpinsEnd');
	if (end < 0) return true;
	const cursor =
		bet?.event === undefined || bet?.event === null || bet?.event === '' ? 0 : Number(bet.event);
	return cursor <= end;
};

export const bookHasFreeSpins = (bet: Pick<Bet, 'state'> | BookLike | null | undefined) =>
	(bet?.state ?? []).some((event) => event?.type === 'skyjumpFreeSpinsStart');
