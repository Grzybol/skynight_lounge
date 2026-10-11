import { API_AMOUNT_MULTIPLIER } from 'constants-shared/bet';
import { stateBet, stateBetDerived, stateUi } from 'state-shared';

import { V2_FIXTURES, resolveDevFixtureId } from './skyjump_v2/fixtures';
import { v2FixtureToBet } from './skyjump_v2/toBookEvents';
import { readDevFixtureSelection } from './skyjump_v2/devSession';
import {
	V2_MATH_SAMPLES,
	parseV2MathSampleQuery,
	v2MathSampleToBet,
} from './skyjump_v2/mathSamples';
import {
	V2_FEATURE_SAMPLES,
	parseV2FeatureSampleQuery,
	v2FeatureSampleToBet,
} from './skyjump_v2/featureSamples';
import {
	V2_BONUS_SAMPLES,
	V2_PHASE6_SAMPLES,
	parseV2BonusSampleQuery,
	v2BonusSampleToBet,
	v2Phase6SampleToBet,
} from './skyjump_v2/bonusSamples';
import {
	V2_WR_SAMPLES,
	parseV2WrSampleQuery,
	v2WrSampleToBet,
} from './skyjump_v2/wrSamples';
import { checkIsBonusGame } from './skyjump_v2/checkIsBonusGame';
import {
	isLiveMathQuery,
	livePlayToBet,
	requestLiveMathPlay,
} from './skyjump_v2/liveMath';
import type { Bet } from './typesBookEvent';

export const LOCAL_DEMO_BALANCE = 1000;
export const LOCAL_DEMO_BET_OPTIONS = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100];

let pendingEndRoundBalance: number | null = null;
let fixtureCursor = 0;
let mathCursor = 0;
let featureCursor = 0;
let bonusCursor = 0;
let phase6Cursor = 0;
let wrCursor = 0;
let playRequestCount = 0;

const localDemoAllowed = () => {
	if (!import.meta.env.DEV) return false;
	if (!stateUi.config.localDemo) return false;
	if (typeof location !== 'undefined' && !/^(localhost|127\.0\.0\.1)$/i.test(location.hostname)) {
		return false;
	}
	return true;
};

const liveMathActive = () => localDemoAllowed() && (stateUi.config.liveMath || isLiveMathQuery());

const selectedReplayKey = () => {
	const search = typeof location !== 'undefined' ? location.search : '';
	const params = new URLSearchParams(search);
	return (
		params.get('bonusSample') ??
		params.get('featureSample') ??
		params.get('mathSample') ??
		params.get('source') ??
		readDevFixtureSelection(search)
	);
};

const nextFixtureBet = (): Bet => {
	const selected = resolveDevFixtureId(selectedReplayKey());
	const fixture = selected ?? V2_FIXTURES[fixtureCursor % V2_FIXTURES.length];
	if (!selected) fixtureCursor += 1;
	return v2FixtureToBet(fixture, fixtureCursor) as Bet;
};

const nextMathSampleBet = (): Bet => {
	const parsed = parseV2MathSampleQuery(selectedReplayKey());
	if (parsed && parsed !== 'cycle') {
		return v2MathSampleToBet(parsed, Number(parsed.id)) as Bet;
	}
	const sample = V2_MATH_SAMPLES[mathCursor % V2_MATH_SAMPLES.length];
	mathCursor += 1;
	return v2MathSampleToBet(sample, mathCursor) as Bet;
};

const nextFeatureSampleBet = (): Bet => {
	const parsed = parseV2FeatureSampleQuery(selectedReplayKey());
	if (parsed && parsed !== 'cycle') {
		return v2FeatureSampleToBet(parsed, Number(parsed.id)) as Bet;
	}
	const sample = V2_FEATURE_SAMPLES[featureCursor % V2_FEATURE_SAMPLES.length];
	featureCursor += 1;
	return v2FeatureSampleToBet(sample, featureCursor) as Bet;
};

const nextBonusBet = (): Bet => {
	const parsed = parseV2BonusSampleQuery(selectedReplayKey());
	if (parsed && parsed !== 'cycle' && parsed !== 'cycle-phase6') {
		if ('roundWinXCapped' in parsed) {
			return v2Phase6SampleToBet(parsed, Number(parsed.seed ?? 0)) as Bet;
		}
		return v2BonusSampleToBet(parsed, Number(parsed.id)) as Bet;
	}
	if (parsed === 'cycle-phase6' || (selectedReplayKey() ?? '').startsWith('phase6')) {
		if (!V2_PHASE6_SAMPLES.length) {
			return nextFixtureBet();
		}
		const sample = V2_PHASE6_SAMPLES[phase6Cursor % V2_PHASE6_SAMPLES.length];
		phase6Cursor += 1;
		return v2Phase6SampleToBet(sample, phase6Cursor) as Bet;
	}
	const sample = V2_BONUS_SAMPLES[bonusCursor % V2_BONUS_SAMPLES.length];
	bonusCursor += 1;
	return v2BonusSampleToBet(sample, bonusCursor) as Bet;
};

const nextWrBet = (): Bet => {
	const parsed = parseV2WrSampleQuery(selectedReplayKey());
	if (parsed && parsed !== 'cycle-wr') {
		return v2WrSampleToBet(parsed, Number(parsed.id)) as Bet;
	}
	if (!V2_WR_SAMPLES.length) {
		return nextFixtureBet();
	}
	const sample = V2_WR_SAMPLES[wrCursor % V2_WR_SAMPLES.length];
	wrCursor += 1;
	return v2WrSampleToBet(sample, wrCursor) as Bet;
};

const nextDemoBet = (): Bet => {
	const key = selectedReplayKey() ?? '';
	if (key === 'wr' || key.startsWith('wr')) {
		return nextWrBet();
	}
	if (key === 'phase6' || key.startsWith('phase6')) {
		return nextBonusBet();
	}
	if (key === 'bonus' || key.startsWith('bonus')) {
		return nextBonusBet();
	}
	if (key === 'feature' || key.startsWith('feature') || key === 'cycle-feature') {
		return nextFeatureSampleBet();
	}
	if (key === 'math' || key.startsWith('math') || key === 'cycle-math') {
		return nextMathSampleBet();
	}
	return nextFixtureBet();
};

export const createLocalDemoBet = ({
	payoutMultiplier: _ignored = 0,
}: { payoutMultiplier?: number } = {}): Bet => nextDemoBet();

export const createLocalDemoBonusBet = (): Bet => nextDemoBet();

const creditFromBet = (credited: Bet) => {
	const activeMode = stateBetDerived.activeBetMode();
	const costMultiplier = activeMode?.type === 'buy' ? activeMode.costMultiplier : 1;
	const balanceAfterCost = Math.max(
		0,
		stateBet.balanceAmount - stateBet.betAmount * costMultiplier,
	);

	pendingEndRoundBalance =
		credited.payoutMultiplier > 0
			? balanceAfterCost + stateBet.betAmount * credited.payoutMultiplier
			: null;

	return {
		balance: {
			amount: balanceAfterCost * API_AMOUNT_MULTIPLIER,
		},
		round: credited,
	};
};

export const requestLocalDemoBet = () => {
	if (!localDemoAllowed()) return null;
	playRequestCount += 1;

	if (liveMathActive()) {
		const modeKey = String(stateBet.activeBetModeKey || 'BASE');
		return requestLiveMathPlay(modeKey)
			.then((play) => {
				const credited = livePlayToBet(play) as Bet;
				console.info(
					'[skyjump-v2 live] play',
					playRequestCount,
					modeKey,
					'winX',
					play.roundWinXCapped,
					'sessionRtp%',
					play.session.sessionRtpPct,
					'checkIsBonusGame',
					checkIsBonusGame(credited),
				);
				return creditFromBet(credited);
			})
			.catch((err: unknown) => {
				const message = err instanceof Error ? err.message : String(err);
				console.error('[skyjump-v2 live] play failed', message);
				throw err;
			});
	}

	const credited = nextDemoBet();
	console.info(
		'[skyjump-v2 dev] play',
		playRequestCount,
		'checkIsBonusGame',
		checkIsBonusGame(credited),
		'criteria',
		credited.criteria,
	);
	return Promise.resolve(creditFromBet(credited));
};

export const requestLocalDemoEndRound = () => {
	if (!localDemoAllowed()) return null;

	const balanceAmount = pendingEndRoundBalance ?? stateBet.balanceAmount;
	pendingEndRoundBalance = null;
	console.info(liveMathActive() ? '[skyjump-v2 live] end-round' : '[skyjump-v2 dev] end-round');

	return Promise.resolve({
		balance: {
			amount: balanceAmount * API_AMOUNT_MULTIPLIER,
		},
	});
};
