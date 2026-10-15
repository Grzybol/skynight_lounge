import { BOOK_AMOUNT_MULTIPLIER } from 'constants-shared/bet';
import { stateBet } from 'state-shared';

/** Social coins: shown as `10.00 SC` / `10.00 GC` (never with a currency symbol). */
const NO_LOCALISATION_CURRENCY_MAP: Record<string, string> = {
	XGC: 'GC',
	XSC: 'SC',
	XEC: 'SC',
};

// bookEventAmount: is the amount or win numbers in the events of books, e.g. the amount in setTotalWin bookEvent
// {
// 	"index": 3,
// 	"type": "setTotalWin",
// 	"amount": 100
// },
// if betting on $1,   100 bookEventAmount equals to $1.    betAmountMultiplier is (100 / BOOK_AMOUNT_MULTIPLIER =) 1
// if betting on $1,    50 bookEventAmount equals to $0.5.  betAmountMultiplier is ( 50 / BOOK_AMOUNT_MULTIPLIER =) 0.5
// if betting on $0.5, 100 bookEventAmount equals to $0.5.  betAmountMultiplier is (100 / BOOK_AMOUNT_MULTIPLIER =) 1
// if betting on $0.5,  50 bookEventAmount equals to $0.25. betAmountMultiplier is ( 50 / BOOK_AMOUNT_MULTIPLIER =) 0.5

export const bookEventAmountToBetAmountMultiplier = (bookEventAmount: number) =>
	bookEventAmount / BOOK_AMOUNT_MULTIPLIER;

export const bookEventAmountToNormalisedAmount = (bookEventAmount: number) => {
	const betAmountMultiplier = bookEventAmountToBetAmountMultiplier(bookEventAmount);
	return stateBet.wageredBetAmount * betAmountMultiplier;
};

export const normalisedAmountToBookEventAmount = (normalisedAmount: number) => {
	if (!stateBet.wageredBetAmount) return 0;
	return (normalisedAmount / stateBet.wageredBetAmount) * BOOK_AMOUNT_MULTIPLIER;
};

export const numberToFloat = (value: number) => Number.parseFloat(`${value}`);

export const numberToCurrencyString = (value: number) => {
	if (stateBet.currency in NO_LOCALISATION_CURRENCY_MAP) {
		return `${numberToFloat(value).toFixed(2)} ${NO_LOCALISATION_CURRENCY_MAP[stateBet.currency]}`;
	}

	const currency = stateBet.currency || 'USD';
	let defaultDigits = 2;
	try {
		// JPY has 0 decimals, USD / EUR / CAD / MXN have 2.
		defaultDigits = new Intl.NumberFormat('en-US', { style: 'currency', currency }).resolvedOptions()
			.maximumFractionDigits ?? 2;
	} catch {
		/* unknown currency: keep 2 */
	}
	// Amounts are shown with the currency's own decimals (2 for USD / EUR, 0 for JPY), never more.
	const digits = defaultDigits;

	return new Intl.NumberFormat('en-US', {
		minimumFractionDigits: digits,
		maximumFractionDigits: digits,
		style: 'currency',
		currency,
	}).format(value);
};

export const bookEventAmountToCurrencyString = (bookEventAmount: number) => {
	const normalisedAmount = bookEventAmountToNormalisedAmount(bookEventAmount);
	return numberToCurrencyString(normalisedAmount);
};
