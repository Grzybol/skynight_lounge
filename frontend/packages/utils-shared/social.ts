/**
 * Social casino wording (`social=true`): whole-word, case-insensitive replacement of restricted terms.
 * Longest phrases first, so "buy bonus" wins over "buy". Casing of the original is kept.
 */
const TABLE: ReadonlyArray<readonly [string, string]> = [
	["be awarded to player's accounts", "appear in player's accounts"],
	['place your bets', 'come and play'],
	['at the cost of', 'for'],
	['total bet', 'total play'],
	['win feature', 'play feature'],
	['bonus buy', 'bonus'],
	['buy bonus', 'get bonus'],
	['pay table', 'win table'],
	['paytable', 'win table'],
	['pay out', 'win'],
	['paid out', 'won'],
	['pays out', 'won'],
	['cost of', 'can be played for'],
	['bets', 'plays'],
	['bet', 'play'],
	['betting', 'playing'],
	['bought', 'instantly triggered'],
	['buy', 'play'],
	['cash', 'coins'],
	['credit', 'balance'],
	['currency', 'token'],
	['deposit', 'get coins'],
	['fund', 'balance'],
	['funds', 'balance'],
	['gamble', 'play'],
	['money', 'coins'],
	['paid', 'won'],
	['payer', 'winner'],
	['pays', 'wins'],
	['pay', 'win'],
	['purchase', 'play'],
	['rebet', 'respin'],
	['stake', 'play amount'],
	['wager', 'play'],
	['withdraw', 'redeem'],
];

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const RULES = [...TABLE]
	.sort((a, b) => b[0].length - a[0].length)
	.map(([from, to]) => ({
		to,
		re: new RegExp(
			`(?<![\\p{L}\\p{N}_])${escapeRegExp(from).replace(/ /g, '\\s+')}(?![\\p{L}\\p{N}_])`,
			'giu',
		),
	}));

const matchCase = (original: string, replacement: string) => {
	if (original === original.toUpperCase() && /[A-Z]/.test(original)) return replacement.toUpperCase();
	if (/^[A-Z]/.test(original)) return replacement.charAt(0).toUpperCase() + replacement.slice(1);
	return replacement;
};

export const socialize = (text: string): string => {
	let out = text;
	for (const { re, to } of RULES) out = out.replace(re, (m) => matchCase(m, to));
	return out;
};
