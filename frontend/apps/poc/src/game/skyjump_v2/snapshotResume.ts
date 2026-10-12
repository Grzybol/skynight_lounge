/** Event types kept when a resume cursor rebuilds bonus state. */

export const V2_RESUME_RESERVE_TYPES = [
	'setTotalWin',
	'skyjumpWeather',
	'skyjumpSlot',
	'skyjumpResult',
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
	'wincap',
	'finalWin',
];

type ResumeEvent = { type: string };

/** Replay prefix through the snapshot, then continue with the live tail. */
export const resumeBookEvents = <T extends ResumeEvent>(events: T[], resumeIndex: number): T[] => {
	const before = events.filter((_, index) => index < resumeIndex);
	const after = events.filter((_, index) => index >= resumeIndex);
	const snapshot = {
		index: 0,
		type: 'createBonusSnapshot',
		bookEvents: before.filter((event) => V2_RESUME_RESERVE_TYPES.includes(event.type)),
	};
	return [snapshot as T, ...after];
};
