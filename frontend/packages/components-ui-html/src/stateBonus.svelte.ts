import { stateMeta } from 'state-shared';

export const stateBonus = $state({
	selectedBetModeKey: 'BASE',
	/** Optional title artwork of the selected mode; the confirm dialog shows it instead of text. */
	selectedModeArt: null as string | null,
});

export const stateBonusDerived = {
	selectedBetModeData: () => stateMeta.betModeMeta[stateBonus.selectedBetModeKey],
};
