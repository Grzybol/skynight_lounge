import { writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

const { reduceV2Events } = await import('./reducer.ts');

const events = JSON.parse(
	process.argv[2] ? require('node:fs').readFileSync(process.argv[2], 'utf8') : '[]',
);
const state = reduceV2Events(events);
const summary = {
	bonusActive: state.bonusActive,
	bonusTier: state.bonusTier,
	freeSpinsRemaining: state.freeSpinsRemaining,
	freeSpinsPlayed: state.freeSpinsPlayed,
	bonusWinXCapped: state.bonusWinXCapped,
	roundWinXCapped: state.roundWinXCapped,
	tokenFloorTier: state.tokenFloorTier,
	persistentMysteryTargets: state.persistentMysteryTargets,
	guaranteedGateUsed: state.guaranteedGateUsed,
	maxWinReached: state.maxWinReached,
	pendingTierUpgrade: state.pendingTierUpgrade,
	coachGuaranteeState: state.coachGuaranteeState,
	flightMultiplier: state.flightMultiplier,
	flightMultiplierRunUp: state.flightMultiplierRunUp,
	flightMultiplierTakeoff: state.flightMultiplierTakeoff,
	flightMultiplierFlight: state.flightMultiplierFlight,
	windKeysCollected: state.windKeysCollected,
	rejumpsThisBonus: state.rejumpsThisBonus,
	featureBatchIndex: state.featureBatchIndex,
	globalFlightMultiplier: state.globalFlightMultiplier,
	rejumpState: state.rejumpState,
	board: state.board,
};
writeFileSync(process.argv[3], JSON.stringify(summary));
