import { V2_PAYLINES, V2_REGULAR_IDS, V2_SCATTER_ID } from './config.ts';
import type { V2Board, V2EvaluateResult, V2LineWin } from './types.ts';

export type V2Paytable = Record<string, Partial<Record<'3' | '4' | '5', number>>>;

export const evaluatePaylines = (
	board: V2Board,
	paytable: V2Paytable,
	paylines: Record<number, number[]> = V2_PAYLINES,
	scatterId = V2_SCATTER_ID,
	regularIds = V2_REGULAR_IDS,
): V2EvaluateResult => {
	if (board.length !== 5 || board.some((col) => col.length !== 5)) {
		throw new Error('board must be 5 reels × 5 rows');
	}

	const wins: V2LineWin[] = [];
	for (const [id, rows] of Object.entries(paylines)) {
		const paylineId = Number(id);
		const first = board[0][rows[0]];
		if (first === scatterId || !regularIds.has(first)) continue;
		let matchCount = 1;
		const positions = [{ reel: 0, row: rows[0] }];
		for (let reel = 1; reel < 5; reel += 1) {
			const cell = board[reel][rows[reel]];
			if (cell !== first) break;
			matchCount += 1;
			positions.push({ reel, row: rows[reel] });
		}
		if (matchCount < 3) continue;
		const payoutX = Number(paytable[first]?.[String(matchCount) as '3' | '4' | '5'] ?? 0);
		if (payoutX <= 0) continue;
		wins.push({
			paylineId,
			symbolId: first,
			matchCount: matchCount as 3 | 4 | 5,
			positions,
			payoutX,
		});
	}

	wins.sort((a, b) => a.paylineId - b.paylineId);
	const lineWinX = wins.reduce((sum, win) => sum + win.payoutX, 0);
	return { wins, lineWinX };
};
