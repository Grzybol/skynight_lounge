/**
 * Polyphonic voice starts for SkyJump V2 SFX.
 * A new play never stops an older voice. Cleanup is the port's natural end.
 */

export type PolyphonicPort = {
	play: () => number;
	/** Gain for this play id only. Must not change other ids. */
	volume: (gain: number, id: number) => void;
	onEnd: (id: number, fn: () => void) => void;
};

export type VoiceLedger = {
	lastPlayAt: Map<string, number>;
	activeIds: Map<string, number[]>;
};

export const createVoiceLedger = (): VoiceLedger => ({
	lastPlayAt: new Map(),
	activeIds: new Map(),
});

export type VoiceStartResult = 'started' | 'blocked-gap' | 'failed';

/**
 * Start one more voice. minGapMs > 0 drops only an accidental near-duplicate
 * trigger; it does not stop the voice that is already playing.
 */
export const startPolyphonicVoice = (args: {
	hook: string;
	port: PolyphonicPort;
	gain: number;
	minGapMs: number;
	now: number;
	ledger: VoiceLedger;
}): VoiceStartResult => {
	const last = args.ledger.lastPlayAt.get(args.hook) ?? 0;
	if (args.minGapMs > 0 && args.now - last < args.minGapMs) return 'blocked-gap';
	args.ledger.lastPlayAt.set(args.hook, args.now);

	let id: number;
	try {
		id = args.port.play();
	} catch {
		return 'failed';
	}
	if (typeof id !== 'number') return 'failed';

	try {
		args.port.volume(args.gain, id);
	} catch {
		/* the voice still plays at the Howl default if per-id volume fails */
	}

	const list = args.ledger.activeIds.get(args.hook) ?? [];
	list.push(id);
	args.ledger.activeIds.set(args.hook, list);

	const drop = () => {
		const current = args.ledger.activeIds.get(args.hook) ?? [];
		const next = current.filter((voiceId) => voiceId !== id);
		if (next.length === 0) args.ledger.activeIds.delete(args.hook);
		else args.ledger.activeIds.set(args.hook, next);
	};
	try {
		args.port.onEnd(id, drop);
	} catch {
		/* playback already started; a missing end hook must not throw into the game */
	}
	return 'started';
};
