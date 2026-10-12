import type { V2Placeholder } from './types.ts';

/** Programmatic Phase 1 tiles. Swap for textures later without changing game logic. */
export const V2_PLACEHOLDERS: Record<string, V2Placeholder> = {
	P1: { id: 'P1', label: 'P1', fill: '#F4C430', ink: '#071526', shape: 'triangle' },
	P2: { id: 'P2', label: 'P2', fill: '#5EEAD4', ink: '#071526', shape: 'diamond' },
	P3: { id: 'P3', label: 'P3', fill: '#D97706', ink: '#071526', shape: 'hexagon' },
	M1: { id: 'M1', label: 'M1', fill: '#0F766E', ink: '#F4FAFF', shape: 'parallelogram' },
	M2: { id: 'M2', label: 'M2', fill: '#7C3AED', ink: '#F4FAFF', shape: 'oval' },
	M3: { id: 'M3', label: 'M3', fill: '#2563EB', ink: '#F4FAFF', shape: 'rounded' },
	L1: { id: 'L1', label: 'L1', fill: '#86EFAC', ink: '#071526', shape: 'chevron' },
	L2: { id: 'L2', label: 'L2', fill: '#F8F4E8', ink: '#071526', shape: 'circle' },
	L3: { id: 'L3', label: 'L3', fill: '#94A3B8', ink: '#071526', shape: 'rect' },
	S: { id: 'S', label: 'BIB', fill: '#F43F5E', ink: '#F4FAFF', shape: 'pentagon' },
	C: { id: 'C', label: 'COACH', fill: '#38BDF8', ink: '#071526', shape: 'hexagon' },
	Y: { id: 'Y', label: 'MYST', fill: '#E0F2FE', ink: '#0B3B6F', shape: 'diamond' },
	T1: { id: 'T1', label: 'T1', fill: '#94A3B8', ink: '#071526', shape: 'rect' },
	T2: { id: 'T2', label: 'T2', fill: '#38BDF8', ink: '#071526', shape: 'rect' },
	T3: { id: 'T3', label: 'T3', fill: '#22C55E', ink: '#071526', shape: 'rect' },
	T4: { id: 'T4', label: 'T4', fill: '#F59E0B', ink: '#071526', shape: 'rect' },
	T5: { id: 'T5', label: 'T5', fill: '#A855F7', ink: '#F4FAFF', shape: 'rect' },
	T6: { id: 'T6', label: 'T6', fill: '#F43F5E', ink: '#F4FAFF', shape: 'rect' },
	THERMAL: { id: 'THERMAL', label: 'THERMAL', fill: '#FB7185', ink: '#071526', shape: 'oval' },
	THERMAL_LIFT: {
		id: 'THERMAL_LIFT',
		label: 'THERMAL',
		fill: '#FB7185',
		ink: '#071526',
		shape: 'oval',
	},
	GATE: { id: 'GATE', label: 'UPGRADE', fill: '#FBBF24', ink: '#071526', shape: 'hexagon' },
	GATE_UPGRADE: {
		id: 'GATE_UPGRADE',
		label: 'UPGRADE',
		fill: '#FBBF24',
		ink: '#071526',
		shape: 'hexagon',
	},
	JUDGE: { id: 'JUDGE', label: 'JUDGE', fill: '#6366F1', ink: '#F4FAFF', shape: 'rounded' },
	HEAD_JUDGE: {
		id: 'HEAD_JUDGE',
		label: 'HEAD JUDGE',
		fill: '#4F46E5',
		ink: '#F4FAFF',
		shape: 'rounded',
	},
	REJUMP: { id: 'REJUMP', label: 'REJUMP', fill: '#0EA5E9', ink: '#071526', shape: 'chevron' },
	WIND: { id: 'WIND', label: 'WIND', fill: '#67E8F9', ink: '#071526', shape: 'diamond' },
	WIND_KEY: { id: 'WIND_KEY', label: 'WIND', fill: '#67E8F9', ink: '#071526', shape: 'diamond' },
	SPECIAL_WORLD_RECORD: {
		id: 'SPECIAL_WORLD_RECORD',
		label: 'WR',
		fill: '#FDE68A',
		ink: '#071526',
		shape: 'pentagon',
	},
};

export const v2Placeholder = (id: string): V2Placeholder =>
	V2_PLACEHOLDERS[id] ?? {
		id,
		label: id.slice(0, 4),
		fill: '#334155',
		ink: '#F4FAFF',
		shape: 'rect',
	};

/** Deterministic spin-band filler. Not an outcome source. */
export const V2_SPIN_BAND = [
	'P1',
	'P2',
	'P3',
	'M1',
	'M2',
	'M3',
	'L1',
	'L2',
	'L3',
	'S',
	'C',
] as const;

/**
 * Symbols that sit on the published virtual strips in skyjump_v2_config.json.
 * Audited for reelModel.strips and freeSpins.tiers LARGE_HILL, SKI_FLYING,
 * WORLD_CUP, and PERFECT_V. Every set is this same alphabet.
 * Y, T1–T6, THERMAL, GATE, JUDGE, HEAD_JUDGE, REJUMP, WIND_KEY, and
 * SPECIAL_WORLD_RECORD are applied after the stop. They are not filler.
 * This list is visual only. It is not a weight table and it is not written
 * back as a result.
 */
export const V2_REEL_FILLER = V2_SPIN_BAND;

const FILLER_BY_MODE = {
	BASE: V2_REEL_FILLER,
	LARGE_HILL: V2_REEL_FILLER,
	SKI_FLYING: V2_REEL_FILLER,
	WORLD_CUP: V2_REEL_FILLER,
	PERFECT_V: V2_REEL_FILLER,
} as const;

/** Filler for the active mode. Unknown modes use the shared strip alphabet. */
export const reelFillerBand = (modeKey?: string | null) =>
	FILLER_BY_MODE[(modeKey ?? 'BASE') as keyof typeof FILLER_BY_MODE] ?? V2_REEL_FILLER;
