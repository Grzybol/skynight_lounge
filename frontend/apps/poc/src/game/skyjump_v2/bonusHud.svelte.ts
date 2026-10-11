/** Presentation mirror of the math-owned Free Spin book. Not a payout source. */

import { loungeShown } from '../midnightLoungeTheme';

export type FlightStageHud = { value: number; charge: number };

export type BonusHudState = {
	active: boolean;
	tier: string | null;
	spinsRemaining: number;
	spinsPlayed: number;
	bonusWinX: number;
	tokenFloorTier: number;
	persistentTargets: string[];
	guaranteedGateUsed: boolean;
	guaranteedCoach: boolean;
	upgradeNotice: string | null;
	unlockedNotice: string | null;
	totalAwarded: number;
	retriggerNote: string | null;
	floorStep: string | null;
	persistNote: string | null;
	flightRunUp: FlightStageHud;
	flightTakeoff: FlightStageHud;
	flightFlight: FlightStageHud;
	globalFlightMultiplier: number;
	windKeysCollected: number;
	rejumpsThisBonus: number;
	windToast: string | null;
};

export const bonusHud = $state<BonusHudState>({
	active: false,
	tier: null,
	spinsRemaining: 0,
	spinsPlayed: 0,
	bonusWinX: 0,
	tokenFloorTier: 1,
	persistentTargets: [],
	guaranteedGateUsed: false,
	guaranteedCoach: false,
	upgradeNotice: null,
	unlockedNotice: null,
	totalAwarded: 10,
	retriggerNote: null,
	floorStep: null,
	persistNote: null,
	flightRunUp: { value: 1, charge: 0 },
	flightTakeoff: { value: 1, charge: 0 },
	flightFlight: { value: 1, charge: 0 },
	globalFlightMultiplier: 1,
	windKeysCollected: 0,
	rejumpsThisBonus: 0,
	windToast: null,
});

const STAGE_LABEL: Record<string, string> = {
	RUN_UP: loungeShown('RUN_UP', 'RUN-UP'),
	TAKEOFF: loungeShown('TAKEOFF', 'TAKEOFF'),
	FLIGHT: loungeShown('FLIGHT', 'FLIGHT'),
};

export const tierLabel = (tier: string | null | undefined) =>
	tier ? loungeShown(tier, tier) : '';

const unlockCopy = (tier: string) => {
	if (tier === 'SKI_FLYING') return 'NEW: Persistent Mystery Targets';
	if (tier === 'WORLD_CUP') return 'NEW: Guaranteed VIP Upgrade';
	if (tier === 'PERFECT_V') return 'NEW: Concierge Every Spin';
	return '';
};

const steadyUnlock = (tier: string | null) => {
	if (tier === 'SKI_FLYING') return 'Persistent Mystery Targets';
	if (tier === 'WORLD_CUP') return 'Guaranteed VIP Upgrade';
	if (tier === 'PERFECT_V') return 'Concierge Every Spin';
	return '';
};

export const bonusShowsTargets = (tier: string | null) =>
	tier === 'SKI_FLYING' || tier === 'WORLD_CUP' || tier === 'PERFECT_V';

const resetFlightHud = () => {
	bonusHud.flightRunUp = { value: 1, charge: 0 };
	bonusHud.flightTakeoff = { value: 1, charge: 0 };
	bonusHud.flightFlight = { value: 1, charge: 0 };
	bonusHud.globalFlightMultiplier = 1;
	bonusHud.windKeysCollected = 0;
	bonusHud.rejumpsThisBonus = 0;
	bonusHud.windToast = null;
};

const syncGlobalFromStages = () => {
	bonusHud.globalFlightMultiplier =
		bonusHud.flightRunUp.value * bonusHud.flightTakeoff.value * bonusHud.flightFlight.value;
};

const applyFlightSnapshot = (event: Record<string, unknown>) => {
	const raw = event.flightMultiplier;
	if (raw && typeof raw === 'object') {
		const stages = raw as Record<string, { value?: number; charge?: number }>;
		bonusHud.flightRunUp = {
			value: Number(stages.runUp?.value ?? event.flightMultiplierRunUp ?? 1),
			charge: Number(stages.runUp?.charge ?? 0),
		};
		bonusHud.flightTakeoff = {
			value: Number(stages.takeoff?.value ?? event.flightMultiplierTakeoff ?? 1),
			charge: Number(stages.takeoff?.charge ?? 0),
		};
		bonusHud.flightFlight = {
			value: Number(stages.flight?.value ?? event.flightMultiplierFlight ?? 1),
			charge: Number(stages.flight?.charge ?? 0),
		};
	} else {
		bonusHud.flightRunUp = { value: Number(event.flightMultiplierRunUp ?? 1), charge: 0 };
		bonusHud.flightTakeoff = {
			value: Number(event.flightMultiplierTakeoff ?? 1),
			charge: 0,
		};
		bonusHud.flightFlight = {
			value: Number(event.flightMultiplierFlight ?? 1),
			charge: 0,
		};
	}
	if (event.globalFlightMultiplier !== undefined) {
		bonusHud.globalFlightMultiplier = Number(event.globalFlightMultiplier);
	} else {
		syncGlobalFromStages();
	}
	bonusHud.windKeysCollected = Number(event.windKeysCollected ?? bonusHud.windKeysCollected);
	bonusHud.rejumpsThisBonus = Number(event.rejumpsThisBonus ?? bonusHud.rejumpsThisBonus);
};

export const resetBonusHud = () => {
	bonusHud.active = false;
	bonusHud.tier = null;
	bonusHud.spinsRemaining = 0;
	bonusHud.spinsPlayed = 0;
	bonusHud.bonusWinX = 0;
	bonusHud.tokenFloorTier = 1;
	bonusHud.persistentTargets = [];
	bonusHud.guaranteedGateUsed = false;
	bonusHud.guaranteedCoach = false;
	bonusHud.upgradeNotice = null;
	bonusHud.unlockedNotice = null;
	bonusHud.totalAwarded = 0;
	bonusHud.retriggerNote = null;
	bonusHud.floorStep = null;
	bonusHud.persistNote = null;
	resetFlightHud();
};

export const applyBonusHudEvent = (event: { type?: string; [key: string]: unknown }) => {
	const type = event.type;
	if (type === 'skyjumpSpinStart' && !event.isFreeSpin) {
		resetBonusHud();
		return;
	}
	if (type === 'skyjumpFreeSpinsStart') {
		bonusHud.active = true;
		bonusHud.tier = String(event.initialTier);
		bonusHud.spinsRemaining = Number(event.spinsAwarded);
		bonusHud.spinsPlayed = 0;
		bonusHud.bonusWinX = 0;
		bonusHud.tokenFloorTier = 1;
		bonusHud.persistentTargets = [];
		bonusHud.guaranteedGateUsed = false;
		bonusHud.guaranteedCoach = event.initialTier === 'PERFECT_V';
		bonusHud.upgradeNotice = 'FREE SPINS START';
		bonusHud.unlockedNotice =
			unlockCopy(String(event.initialTier)) || steadyUnlock(String(event.initialTier));
		bonusHud.totalAwarded = Number(event.spinsAwarded);
		bonusHud.retriggerNote = null;
		bonusHud.floorStep = null;
		bonusHud.persistNote = null;
		resetFlightHud();
		return;
	}
	if (type === 'skyjumpFreeSpinStart') {
		bonusHud.active = true;
		bonusHud.tier = String(event.currentTier);
		bonusHud.spinsRemaining = Number(event.spinsRemainingBefore);
		bonusHud.guaranteedCoach = event.currentTier === 'PERFECT_V';
		bonusHud.upgradeNotice = null;
		bonusHud.persistNote = null;
		bonusHud.windToast = null;
		if (!bonusHud.unlockedNotice) bonusHud.unlockedNotice = steadyUnlock(bonusHud.tier);
		return;
	}
	if (type === 'skyjumpPersistentTargetsApply') {
		const positions = (event.positions as Array<{ symbolId?: string }>) ?? [];
		const ids = [...new Set(positions.map((pos) => pos.symbolId).filter(Boolean))];
		bonusHud.persistNote = ids.length
			? ids.map((id) => `PERSISTENT TARGET ${id} -> MYSTERY`).join(' · ')
			: 'PERSISTENT TARGET -> MYSTERY';
		return;
	}
	if (type === 'skyjumpPersistentTargetsUpdate') {
		bonusHud.persistentTargets = [...((event.persistentMysteryTargets as string[]) ?? [])];
		return;
	}
	if (type === 'skyjumpGuaranteedGate') {
		bonusHud.guaranteedGateUsed = true;
		return;
	}
	if (type === 'skyjumpGateUpgrade') {
		const before = Number(event.floorBefore ?? bonusHud.tokenFloorTier);
		const after = Number(event.floorAfter ?? bonusHud.tokenFloorTier);
		bonusHud.tokenFloorTier = after;
		if (after !== before) bonusHud.floorStep = `T${before} → T${after}`;
		return;
	}
	if (type === 'skyjumpBonusUpgrade') {
		const from = tierLabel(String(event.fromTier));
		const to = tierLabel(String(event.toTier));
		const requested = Number(event.spinsRequested ?? 0);
		const added = Number(event.spinsAdded ?? 0);
		const awarded = Number(event.totalFreeSpinsAwarded ?? bonusHud.totalAwarded);
		bonusHud.totalAwarded = awarded;
		bonusHud.retriggerNote = `requested ${requested} · actual ${added} · total awarded ${awarded}`;
		if (event.tierChanged) {
			bonusHud.upgradeNotice = `${from}  UPGRADE  ${to}`;
			bonusHud.unlockedNotice = unlockCopy(String(event.toTier));
		} else if (requested > 0) {
			bonusHud.upgradeNotice = `${to}  +SPINS`;
		}
		return;
	}
	if (type === 'skyjumpFreeSpinEnd') {
		bonusHud.spinsPlayed = Number(event.spinIndex);
		bonusHud.spinsRemaining = Number(event.spinsRemainingAfter);
		bonusHud.bonusWinX = Number(event.bonusWinRunningX);
		return;
	}
	if (type === 'skyjumpFreeSpinState') {
		bonusHud.active = true;
		bonusHud.tier = (event.bonusTier as string) ?? bonusHud.tier;
		bonusHud.spinsRemaining = Number(event.freeSpinsRemaining ?? bonusHud.spinsRemaining);
		bonusHud.spinsPlayed = Number(event.freeSpinsPlayed ?? bonusHud.spinsPlayed);
		bonusHud.bonusWinX = Number(event.bonusWinXCapped ?? bonusHud.bonusWinX);
		bonusHud.tokenFloorTier = Number(event.tokenFloorTier ?? bonusHud.tokenFloorTier);
		bonusHud.persistentTargets = [...((event.persistentMysteryTargets as string[]) ?? [])];
		bonusHud.guaranteedGateUsed = Boolean(event.guaranteedGateUsed);
		bonusHud.guaranteedCoach = event.bonusTier === 'PERFECT_V';
		bonusHud.totalAwarded = Number(event.totalFreeSpinsAwarded ?? bonusHud.totalAwarded);
		applyFlightSnapshot(event);
		return;
	}
	if (type === 'skyjumpWindKey') {
		const action = String(event.action ?? 'NO_OP');
		const stage = String(event.selectedStage ?? '');
		if (stage === 'RUN_UP' && action !== 'NO_OP') {
			bonusHud.flightRunUp = {
				value: Number(event.newStageValue ?? bonusHud.flightRunUp.value),
				charge: Number(event.newCharge ?? bonusHud.flightRunUp.charge),
			};
		} else if (stage === 'TAKEOFF' && action !== 'NO_OP') {
			bonusHud.flightTakeoff = {
				value: Number(event.newStageValue ?? bonusHud.flightTakeoff.value),
				charge: Number(event.newCharge ?? bonusHud.flightTakeoff.charge),
			};
		} else if (stage === 'FLIGHT' && action !== 'NO_OP') {
			bonusHud.flightFlight = {
				value: Number(event.newStageValue ?? bonusHud.flightFlight.value),
				charge: Number(event.newCharge ?? bonusHud.flightFlight.charge),
			};
		}
		if (event.newGlobalMultiplier !== undefined) {
			bonusHud.globalFlightMultiplier = Number(event.newGlobalMultiplier);
		} else {
			syncGlobalFromStages();
		}
		bonusHud.windKeysCollected = Number(event.windKeysCollected ?? bonusHud.windKeysCollected + 1);
		const label = STAGE_LABEL[stage] ?? (stage || 'STAGE');
		if (action === 'CHARGE') {
			bonusHud.windToast = `ACCESS PASS · ${label} CHARGE (x unchanged)`;
		} else if (action === 'UPGRADE') {
			bonusHud.windToast = `ACCESS PASS · ${label} UPGRADE x${event.oldStageValue}→x${event.newStageValue}`;
		} else {
			bonusHud.windToast = 'ACCESS PASS · NO EFFECT';
		}
		return;
	}
	if (type === 'skyjumpRejumpStart') {
		bonusHud.rejumpsThisBonus = Number(bonusHud.rejumpsThisBonus) + 1;
		return;
	}
	if (type === 'skyjumpWorldRecord') {
		bonusHud.spinsRemaining = 0;
		bonusHud.upgradeNotice = `${loungeShown('WORLD_RECORD')} · MAX WIN`;
		bonusHud.bonusWinX = Number(event.finalRoundWinX ?? bonusHud.bonusWinX);
		bonusHud.windToast = null;
		return;
	}
	if (type === 'skyjumpFreeSpinsEnd') {
		bonusHud.active = false;
		bonusHud.tier = String(event.finalTier);
		bonusHud.spinsRemaining = 0;
		bonusHud.spinsPlayed = Number(event.totalSpinsPlayed);
		bonusHud.bonusWinX = Number(event.bonusWinX);
		bonusHud.tokenFloorTier = Number(event.tokenFloorTier ?? bonusHud.tokenFloorTier);
		bonusHud.persistentTargets = [...((event.persistentMysteryTargets as string[]) ?? [])];
		bonusHud.guaranteedGateUsed = Boolean(event.guaranteedGateUsed);
		bonusHud.windToast = null;
	}
};
