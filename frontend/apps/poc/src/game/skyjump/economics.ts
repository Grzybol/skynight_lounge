/** Presentation economics vs actual mode wager. Settlement still uses finalWinX. */

export const economicFromPayout = (finalWinX: number, costMultiplier: number) => {
	const cost = costMultiplier > 0 ? costMultiplier : 1;
	const returnMultiplier = finalWinX / cost;
	return {
		actualWagerMultiplier: cost,
		returnMultiplier,
		netMultiplier: (finalWinX - cost) / cost,
		isPayHit: finalWinX > 0,
		isBreakEven: finalWinX >= cost,
		isProfit: finalWinX > cost,
	};
};

/** Celebration ladder is vs actual wager, not nominal bet. */
export const winLevelForReturn = (finalWinX: number, costMultiplier: number) => {
	if (finalWinX <= 0) return 1;
	const returned = finalWinX / Math.max(costMultiplier, 1e-9);
	if (returned < 1) return 2;
	if (returned < 2) return 3;
	if (returned < 5) return 4;
	if (returned < 10) return 5;
	if (returned < 25) return 6;
	if (returned < 50) return 7;
	if (returned < 100) return 8;
	if (returned < 250) return 9;
	return 10;
};
