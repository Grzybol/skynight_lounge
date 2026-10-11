/**
 * Win-reveal bus for the lounge characters.
 *
 * The board already classifies wins (`classifyV2WinCelebration`) when a result
 * is revealed. It reports that here; both character controllers subscribe
 * independently. This is a plain event (not state), so a subscriber that
 * mounts late never replays an old win.
 */
import type { V2WinCelebrationTier } from '../skyjump_v2/winPresentation';
import type { WinCategory } from './config';

export type LoungeWinEvent = {
	category: WinCategory;
	tier: V2WinCelebrationTier | 'small';
	seq: number;
	/** Turbo skips the reverse half of the big/mega clips. */
	turbo: boolean;
};
type Listener = (event: LoungeWinEvent) => void;

const listeners = new Set<Listener>();
let seq = 0;
let lastAnnounced: V2WinCelebrationTier | null = null;

/** Existing celebration tiers -> animation category. Mega and above share one. */
export const categoryForTier = (tier: V2WinCelebrationTier): WinCategory | null => {
	switch (tier) {
		case 'big':
			return 'big';
		case 'mega':
		case 'super':
		case 'max':
		case 'worldRecord':
			return 'mega';
		default:
			return null;
	}
};

/**
 * Category a running win counter has reached, in stake multiples. A win only counts
 * once it is above the bet (x > 1); big and mega use the existing presentation thresholds.
 */
export const categoryForWinX = (
	x: number,
	thresholds: { big: number; mega: number },
): WinCategory | null => {
	if (x >= thresholds.mega) return 'mega';
	if (x >= thresholds.big) return 'big';
	if (x > 1) return 'mini';
	return null;
};

export const onLoungeWin = (listener: Listener): (() => void) => {
	listeners.add(listener);
	return () => listeners.delete(listener);
};

export const loungeWinListenerCount = () => listeners.size;

export const emitLoungeWin = (
	category: WinCategory,
	tier: LoungeWinEvent['tier'],
	opts: { turbo?: boolean } = {},
) => {
	const event = { category, tier, seq: ++seq, turbo: Boolean(opts.turbo) };
	for (const fn of [...listeners]) fn(event);
};

/**
 * Showcase hook: announce the final category of a celebration tier at once. The real
 * board drives the characters from the win counter instead (see the win celebration).
 */
export const syncLoungeFigureWin = (show: boolean, tier: V2WinCelebrationTier) => {
	if (!show || tier === 'none') {
		lastAnnounced = null;
		return;
	}
	if (lastAnnounced === tier) return;
	lastAnnounced = tier;
	const category = categoryForTier(tier);
	if (category) emitLoungeWin(category, tier);
};

/** Board hook for a revealed win above the bet but below the celebration threshold. */
export const announceSmallWin = (opts: { turbo?: boolean } = {}) =>
	emitLoungeWin('mini', 'small', opts);
