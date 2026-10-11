/**
 * Handler completeness audit for Phase 7D.
 * Every typed V2 skyjump* / settlement event must have a bookEventHandlerMap entry.
 */

export const V2_REQUIRED_HANDLER_TYPES = [
	'skyjumpSpinStart',
	'skyjumpBoardReveal',
	'skyjumpLineWins',
	'skyjumpScatterResult',
	'skyjumpCoachSignal',
	'skyjumpMysteryTransform',
	'skyjumpMysteryResolve',
	'skyjumpGateUpgrade',
	'skyjumpThermalLift',
	'skyjumpJudgeCollect',
	'skyjumpHeadJudgeCollect',
	'skyjumpWindKey',
	'skyjumpRejumpStart',
	'skyjumpRejumpBoard',
	'skyjumpRejumpLineWins',
	'skyjumpRejumpEnd',
	'skyjumpCapReached',
	'skyjumpWorldRecord',
	'skyjumpFreeSpinsStart',
	'skyjumpFreeSpinStart',
	'skyjumpFreeSpinState',
	'skyjumpBonusUpgrade',
	'skyjumpFreeSpinEnd',
	'skyjumpFreeSpinsEnd',
	'skyjumpPersistentTargetsApply',
	'skyjumpPersistentTargetsUpdate',
	'skyjumpGuaranteedGate',
	'skyjumpResult',
	'setTotalWin',
	'setWin',
	'finalWin',
	'createBonusSnapshot',
] as const;

export type V2RequiredHandlerType = (typeof V2_REQUIRED_HANDLER_TYPES)[number];
