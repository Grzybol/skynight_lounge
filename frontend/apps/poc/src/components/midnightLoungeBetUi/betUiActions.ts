import {
	stateBet,
	stateBetDerived,
	stateConfig,
	stateI18nDerived,
	stateModal,
	stateSound,
	stateUi,
} from 'state-shared';

import type { EmitterEvent } from '../../game/eventEmitter';

type Emit = {
	broadcast: (event: EmitterEvent) => void;
};

const press = (emit: Emit) => emit.broadcast({ type: 'soundPressGeneral' });

export const betFromIdle = (emit: Emit) => {
	if (stateBet.overlayOpen) return;
	if (stateBetDerived.activeBetMode()?.type === 'buy') stateBet.activeBetModeKey = 'BASE';
	emit.broadcast({ type: 'bet' });
};

export const stopRound = (emit: Emit, stopDisabled: boolean) => {
	if (stateBetDerived.hasAutoBetCounter()) stateBet.autoSpinsCounter = 0;
	if (stateBet.overlayOpen) return;
	if (!stopDisabled) emit.broadcast({ type: 'stopButtonClick' });
};

export const pressBuy = (emit: Emit) => {
	press(emit);
	if (stateBetDerived.activeBetMode()?.type === 'activate') {
		stateBet.activeBetModeKey = 'BASE';
		return;
	}
	stateModal.modal = { name: 'buyBonus' };
};

export const pressAuto = (emit: Emit) => {
	press(emit);
	if (stateBetDerived.hasAutoBetCounter()) {
		stateBet.autoSpinsCounter = 0;
		return;
	}
	stateModal.modal = { name: 'autoSpin' };
};

export const pressTurbo = (emit: Emit) => {
	if (stateBet.overlayOpen) return;
	press(emit);
	stateBetDerived.updateIsTurbo(!stateBet.isTurbo, { persistent: true });
};

export const stepBet = (emit: Emit, direction: 1 | -1) => {
	emit.broadcast({
		type: direction > 0 ? 'soundPressBetIncrease' : 'soundPressBetDecrease',
	});
	const options = [...stateConfig.betAmountOptions].sort((a, b) => a - b);
	const biggest = options[options.length - 1];
	const smallest = options[0];
	if (direction > 0) {
		const next = options.find((option) => option > stateBet.betAmount);
		stateBetDerived.setBetAmount(next || biggest);
		return;
	}
	const next = [...options].reverse().find((option) => option < stateBet.betAmount);
	stateBetDerived.setBetAmount(next || smallest);
};

export const openBetMenu = (emit: Emit) => {
	press(emit);
	stateModal.modal = { name: 'betAmountMenu' };
};

export const openMenu = (emit: Emit) => {
	press(emit);
	stateUi.menuOpen = true;
};

export const closeMenu = (emit: Emit, withSound: boolean) => {
	if (withSound) press(emit);
	stateUi.menuOpen = false;
};

export const openPaytable = (emit: Emit) => {
	press(emit);
	stateModal.modal = { name: 'payTable' };
};

export const openRules = (emit: Emit) => {
	press(emit);
	stateModal.modal = { name: 'gameRules' };
};

export const openSettings = (emit: Emit) => {
	press(emit);
	stateModal.modal = { name: 'settings' };
};

let lastAudibleVolume = 50;

export const toggleSound = (emit: Emit) => {
	press(emit);
	if (stateSound.volumeValueMaster === 0) {
		// Unmute to what the player had, never to a fixed default.
		stateSound.volumeValueMaster = lastAudibleVolume;
		return;
	}
	lastAudibleVolume = stateSound.volumeValueMaster;
	stateSound.volumeValueMaster = 0;
};

export const pickLanguage = (emit: Emit, lang: 'en' | 'pl') => {
	press(emit);
	stateI18nDerived.switchLanguage(lang);
};
