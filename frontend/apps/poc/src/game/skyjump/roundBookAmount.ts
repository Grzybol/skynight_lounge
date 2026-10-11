import { BOOK_AMOUNT_MULTIPLIER } from './config.ts';

/**
 * Stake math-sdk book amounts use Python 3 round(): nearest integer, ties to even.
 * Production setWin / setTotalWin / finalWin / wincap all go through that path.
 * localDemo must emit the same integer as the Python book writer.
 */
export const roundBookAmount = (winX: number, multiplier = BOOK_AMOUNT_MULTIPLIER): number =>
	pythonRoundHalfEven(winX * multiplier);

export const pythonRoundHalfEven = (value: number): number => {
	if (!Number.isFinite(value)) return 0;
	const sign = value < 0 ? -1 : 1;
	const abs = Math.abs(value);
	const integer = Math.trunc(abs);
	const fraction = abs - integer;
	if (fraction > 0.5) return sign * (integer + 1);
	if (fraction < 0.5) return sign * integer;
	return sign * (integer % 2 === 0 ? integer : integer + 1);
};
