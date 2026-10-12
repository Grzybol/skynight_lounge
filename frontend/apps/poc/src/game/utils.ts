import { stateBet, stateBetDerived } from 'state-shared';
import { createPlayBookUtils } from 'utils-book';
import { createGetEmptyPaddedBoard } from 'utils-slots';

import { SYMBOL_SIZE, REEL_PADDING, SYMBOL_INFO_MAP, BOARD_DIMENSIONS } from './constants';
import { eventEmitter } from './eventEmitter';
import type { Bet } from './typesBookEvent';
import { bookEventHandlerMap } from './bookEventHandlerMap';
import { resumeBookEvents } from './skyjump_v2/snapshotResume';
import type { RawSymbol, SymbolState } from './types';

export const { getEmptyBoard } = createGetEmptyPaddedBoard({ reelsDimensions: BOARD_DIMENSIONS });
export const { playBookEvent, playBookEvents } = createPlayBookUtils({ bookEventHandlerMap });
export const playBet = async (bet: Bet) => {
	// WIN shows what this round paid (gross), not a running net of bets and wins.
	stateBet.winBookEventAmount = 0;
	stateBet.winSessionBaseAmount = 0;
	try {
		await playBookEvents(bet.state);
	} catch (error) {
		console.error(error);
	} finally {
		stateBet.overlayOpen = false;
		// A bought bonus is a one-off: the next spin is a normal bet, and BET must say so.
		if (stateBetDerived.activeBetMode()?.type === 'buy') stateBet.activeBetModeKey = 'BASE';
		eventEmitter.broadcast({ type: 'stopButtonEnable' });
	}
};

export const convertTorResumableBet = (betToResume: Bet) => {
	const stateToResume = resumeBookEvents(betToResume.state, Number(betToResume.event));
	return { ...betToResume, state: stateToResume };
};

export const getSymbolX = (reelIndex: number) => SYMBOL_SIZE * (reelIndex + REEL_PADDING);
export const getSymbolY = (symbolIndexOfBoard: number) => (symbolIndexOfBoard + 0.5) * SYMBOL_SIZE;

export const getSymbolInfo = ({
	rawSymbol,
	state,
}: {
	rawSymbol: RawSymbol;
	state: SymbolState;
}) => {
	const map = SYMBOL_INFO_MAP as Record<string, Record<string, unknown>>;
	return map[rawSymbol.name]?.[state];
};
