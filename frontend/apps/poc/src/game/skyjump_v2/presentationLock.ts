import { stateBet } from 'state-shared';

import { stateGame } from '../stateGame.svelte';

/**
 * Locks SPIN / BET / turbo / Space while non-skippable V2 presentation runs.
 * Reuses Stake `overlayOpen` so existing HUD guards apply without a second lock system.
 */
export const lockV2Presentation = (reason = 'v2-presenting') => {
	stateBet.overlayOpen = true;
	stateGame.v2PresentationLocked = true;
	stateGame.v2PresentationLockReason = reason;
};

export const unlockV2Presentation = () => {
	stateBet.overlayOpen = false;
	stateGame.v2PresentationLocked = false;
	stateGame.v2PresentationLockReason = '';
};

export const isV2PresentationLocked = () =>
	Boolean(stateGame.v2PresentationLocked || stateBet.overlayOpen);
