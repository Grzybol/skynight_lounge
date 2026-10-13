/** Social wording table (guideline 77 / 188). Run: node --experimental-strip-types tools/midnight-lounge/test-social.ts */
import assert from 'node:assert/strict';
import { socialize } from '../../frontend/packages/utils-shared/social.ts';

const cases: Array<[string, string]> = [
	['BET', 'PLAY'],
	['Total Bet 5.00', 'Total play 5.00'],
	['Buy Bonus', 'Get bonus'],
	['Paytable', 'Win table'],
	['Pays 3, 4 or 5 of a kind', 'Wins 3, 4 or 5 of a kind'],
	['INSUFFICIENT FUNDS TO PLACE THIS BET.', 'INSUFFICIENT BALANCE TO PLACE THIS PLAY.'],
	['Auto Bet', 'Auto Play'],
	['Paylines rules', 'Paylines rules'],
	['wager and stake', 'play and play amount'],
	['Spin a 5×5 board', 'Spin a 5×5 board'],
	['Bonus Buy', 'Bonus'],
];
for (const [input, expected] of cases) assert.equal(socialize(input), expected, input);
console.log(`social wording: ${cases.length} cases passed`);
