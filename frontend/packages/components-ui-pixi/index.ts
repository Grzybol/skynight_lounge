import UI from './src/components/UI.svelte';
import UiGameName from './src/components/UiGameName.svelte';

import messagesMap from './src/i18n/messagesMap';
import { i18nDerived } from './src/i18n/i18nDerived';
import { GARDEN_SLOT_BOARD_CONTEXT, getGardenSlotFrameMetrics } from './src/gardenHud';
import {
	getSkyJumpHudCssDock,
	getSkyJumpHudLayout,
	SKYJUMP_BET_HUD_FRAME,
} from './src/skyjumpHud';
import { skyjumpCodeBetUi } from './src/skyjumpCodeBetUi';

export * from './src/types';

export {
	messagesMap,
	i18nDerived,
	UI,
	UiGameName,
	GARDEN_SLOT_BOARD_CONTEXT,
	getGardenSlotFrameMetrics,
	getSkyJumpHudLayout,
	getSkyJumpHudCssDock,
	SKYJUMP_BET_HUD_FRAME,
	skyjumpCodeBetUi,
};
export type { GardenSlotBoard, GardenSlotBoardApi } from './src/gardenHud';
