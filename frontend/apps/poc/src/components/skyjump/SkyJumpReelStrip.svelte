<script lang="ts">
	import { onDestroy } from 'svelte';
	import { stateBet } from 'state-shared';
	import { waitForTimeout } from 'utils-shared/wait';

	import { getContext } from '../../game/context';
	import {
		BET_MODE_TO_TABLES,
		HILL_TABLE,
		MULTIPLIER_TABLES,
		SLOT_ROLES,
		paylineDistance,
	} from '../../game/skyjump/config';
	import { parseDistanceTick, slotHeatFor } from '../../game/skyjump/slotHeat';
	import type { BetModeKey, HillId, TimingProfile } from '../../game/skyjump/types';
	import { payoutBandAt } from '../../game/skyjump/resolveRound';
	import { roleIconSrc, weatherIconSrc } from './skyjumpArt';
	import { t } from '../../game/skyjump/copy';
	import type { SkyJumpWeatherCandidate } from './skyjumpEvents';

	const context = getContext();
	const TICK = 48;
	const FINAL_TICK = 68;
	const SPIN_PX_MS = 0.2;
	const FINAL_SPIN_PX_MS = 0.38;
	const TAPE_CYCLES = 24;
	const STOP_MIN_TICKS = 1.15;
	const STOP_MAX_TICKS = 3.2;
	const STOP_PLACE_TICKS = 2.35;
	const isFinalIndex = (index: number) => index === 5;
	const tickPx = (index: number) => (isFinalIndex(index) ? FINAL_TICK : TICK);
	const visibleTicks = (index: number) => (isFinalIndex(index) ? 1 : 3);
	const windowPad = (index: number) => Math.floor((visibleTicks(index) - 1) / 2);

	const formatDistance = (value: number) => `${value > 0 ? '+' : ''}${value}m`;
	const formatMetres = (value: number, signed = false) => {
		const rounded = Math.round(value * 10) / 10;
		if (signed) {
			if (rounded > 0) return `+${rounded.toFixed(1)} m`;
			if (rounded < 0) return `−${Math.abs(rounded).toFixed(1)} m`;
		}
		return `${rounded.toFixed(1)} m`;
	};
	const formatBaseX = (value: number) => {
		if (!Number.isFinite(value) || value <= 0) return '0.00x';
		return `${value.toFixed(2)}x`;
	};
	const formatBand = (min: number, max: number) => {
		if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) return '—';
		if (max >= 900) return `${min} m ${t('AND UP')}`;
		return `${min}–${max} m`;
	};
	const formatMult = (value: number) => {
		if (!Number.isFinite(value) || value <= 0) return 'x1';
		const rounded = Math.round(value * 100) / 100;
		if (Number.isInteger(rounded)) return `x${rounded}`;
		return `x${String(rounded.toFixed(2)).replace(/0+$/, '').replace(/\.$/, '')}`;
	};
	const waitFrames = (count = 2) =>
		new Promise<void>((resolve) => {
			let left = count;
			let done = false;
			const finish = () => {
				if (done) return;
				done = true;
				resolve();
			};
			const failSafe = setTimeout(finish, 90);
			const step = () => {
				left -= 1;
				if (left <= 0) {
					clearTimeout(failSafe);
					finish();
					return;
				}
				requestAnimationFrame(step);
			};
			requestAnimationFrame(step);
		});
	const shuffle = (items: string[]) => {
		const next = [...items];
		for (let i = next.length - 1; i > 0; i -= 1) {
			const j = Math.floor(Math.random() * (i + 1));
			[next[i], next[j]] = [next[j], next[i]];
		}
		return next;
	};
	const SPARK_BOLTS = [
		{ a: -8, len: 72, dist: 54, d: 0, jagged: true },
		{ a: 22, len: 64, dist: 48, d: 0.04, jagged: false },
		{ a: -38, len: 56, dist: 42, d: 0.1, jagged: true },
		{ a: 52, len: 80, dist: 60, d: 0.07, jagged: false },
		{ a: -72, len: 48, dist: 36, d: 0.16, jagged: false },
		{ a: 88, len: 60, dist: 46, d: 0.2, jagged: true },
		{ a: -118, len: 70, dist: 52, d: 0.05, jagged: false },
		{ a: 138, len: 52, dist: 40, d: 0.14, jagged: true },
		{ a: -162, len: 76, dist: 58, d: 0.22, jagged: false },
		{ a: 176, len: 44, dist: 34, d: 0.28, jagged: false },
		{ a: -198, len: 62, dist: 47, d: 0.11, jagged: true },
		{ a: 214, len: 74, dist: 56, d: 0.18, jagged: false },
		{ a: -242, len: 50, dist: 38, d: 0.32, jagged: false },
		{ a: 268, len: 68, dist: 50, d: 0.08, jagged: true },
		{ a: -292, len: 42, dist: 32, d: 0.26, jagged: false },
		{ a: 312, len: 78, dist: 58, d: 0.13, jagged: true },
		{ a: -330, len: 58, dist: 44, d: 0.35, jagged: false },
		{ a: 6, len: 36, dist: 28, d: 0.4, jagged: false },
	];
	const SPARK_POPS = [
		{ x: '28%', y: '-36%', s: 1.15, d: 0.05 },
		{ x: '-32%', y: '-22%', s: 0.9, d: 0.12 },
		{ x: '8%', y: '34%', s: 1, d: 0.18 },
		{ x: '-18%', y: '28%', s: 0.8, d: 0.08 },
		{ x: '36%', y: '6%', s: 1.25, d: 0.24 },
		{ x: '-40%', y: '-4%', s: 0.85, d: 0.3 },
		{ x: '16%', y: '-44%', s: 1.05, d: 0.16 },
		{ x: '-6%', y: '42%', s: 0.75, d: 0.36 },
	];
	const sparkWorthy = (heat: { id: string } | null | undefined) =>
		!!heat && (heat.id === 'pos-hi' || heat.id === 'pos-max');
	const sadHeat = (heat: { id: string } | null | undefined) => !!heat && heat.id.startsWith('neg');

	const poolFor = (index: number) => {
		if (index === 5) {
			const labels = new Set<string>(['x0.25', 'x0.5', 'x0.75']);
			for (const table of Object.values(MULTIPLIER_TABLES)) {
				for (const row of table) {
					if (row.multiplier > 0) labels.add(row.label);
				}
			}
			return [...labels];
		}
		const values = SLOT_ROLES[index]?.symbols.map((symbol) => formatDistance(symbol.distanceValue));
		return values?.length ? values : ['+2m', '+4m', '0m', '-2m'];
	};

	const makeCycle = (index: number) => {
		const pool = poolFor(index);
		return shuffle(pool.length ? pool : ['—']);
	};

	const makeTape = (cycle: string[]) => {
		const n = Math.max(1, cycle.length);
		return Array.from({ length: n * TAPE_CYCLES }, (_, step) => cycle[step % n]);
	};

	const sameTick = (value: string, landed: string) =>
		value === landed || value.toLowerCase() === landed.toLowerCase();

	const wrapOffset = (offset: number, cycleLen: number, tick: number) => {
		const cyclePx = Math.max(tick, cycleLen * tick);
		const wrapped = ((offset % cyclePx) + cyclePx) % cyclePx;
		return wrapped + cyclePx * 2;
	};

	const planStop = (
		offset: number,
		tape: string[],
		cycle: string[],
		landed: string,
		tick: number,
		pad: number,
	) => {
		const n = Math.max(1, cycle.length);
		const frozen = wrapOffset(offset, n, tick);
		const centerFloat = frozen / tick + pad;
		const from = Math.ceil(centerFloat + STOP_MIN_TICKS - 0.001);
		const to = Math.floor(centerFloat + STOP_MAX_TICKS + 0.001);
		for (let index = from; index <= to; index += 1) {
			if (index >= 0 && index < tape.length && sameTick(tape[index], landed)) {
				return { frozen, targetOffset: (index - pad) * tick };
			}
		}
		const place = Math.min(
			tape.length - 1,
			Math.max(0, Math.round(centerFloat + STOP_PLACE_TICKS)),
		);
		tape[place] = landed;
		return { frozen, targetOffset: (place - pad) * tick };
	};

	type SlotView = {
		label: string;
		distanceValue: number | null;
		localMultiplier: number;
		spinning: boolean;
		stopping: boolean;
		revealed: boolean;
		impact: boolean;
		locked: boolean;
		unlocking: boolean;
		cycle: string[];
		tape: string[];
		offset: number;
		motionMs: number;
		rarity?: string;
	};

	const emptySlots = (): SlotView[] =>
		SLOT_ROLES.map((role, index) => ({
			label: role.shortLabel,
			distanceValue: null,
			localMultiplier: 1,
			spinning: false,
			stopping: false,
			revealed: false,
			impact: false,
			locked: index === 5,
			unlocking: false,
			cycle: poolFor(index),
			tape: ['—'],
			offset: 0,
			motionMs: 0,
		}));

	let slots = $state(emptySlots());
	let revealGen = 0;
	let weatherDrawOpen = $state(false);
	let weatherClosing = $state(false);
	let weatherTurbo = $state(false);
	let weatherCandidates = $state<SkyJumpWeatherCandidate[]>([]);
	let weatherHighlightId = $state<string | null>(null);
	let weatherGen = 0;
	const weatherSign = (delta: number) => (delta > 0.05 ? 'pos' : delta < -0.05 ? 'neg' : 'neu');
	const weatherHero = $derived(
		weatherCandidates.find((candidate) => candidate.id === weatherHighlightId) ??
			weatherCandidates[0] ??
			null,
	);
	const weatherHeroDelta = $derived(weatherHero?.distanceDelta ?? 0);
	let spinRaf = 0;
	let jumperRaf = 0;
	let lastSpinTs = 0;
	let spinClock = $state(0);
	let baseRaf = 0;
	type BaseTile = {
		locked: boolean;
		unlocking: boolean;
		counting: boolean;
		revealed: boolean;
		step: 0 | 1 | 2 | 3 | 4 | 5;
		hillM: number;
		weatherM: number;
		flightM: number;
		distanceM: number;
		baseX: number;
		shownHill: number;
		shownWeather: number;
		shownFlight: number;
		shownDistance: number;
		shownX: number;
		bandMin: number;
		bandMax: number;
		hillId: HillId;
	};
	const idleBase = (): BaseTile => ({
		locked: true,
		unlocking: false,
		counting: false,
		revealed: false,
		step: 0,
		hillM: 0,
		weatherM: 0,
		flightM: 0,
		distanceM: 0,
		baseX: 0,
		shownHill: 0,
		shownWeather: 0,
		shownFlight: 0,
		shownDistance: 0,
		shownX: 0,
		bandMin: 0,
		bandMax: 0,
		hillId: 'normal',
	});
	let baseTile = $state(idleBase());
	let jumper = $state({
		on: false,
		x: 0.1,
		y: 0.52,
		u: 0,
		ys: [] as number[],
	});
	let flightPlan = { ys: [] as number[], ms: 1 };
	let flightStart = 0;

	const yFromMetres = (value: number, lane: number) => {
		const lift = 0.52 - Math.max(-1, Math.min(1, value / 22)) * 0.3;
		const arc = 0.1 * Math.sin((Math.max(0, Math.min(4, lane)) / 4) * Math.PI);
		return Math.max(0.14, Math.min(0.86, lift - arc));
	};
	const laneX = (lane: number) => (lane + 0.5) / 5;
	const catmull = (p0: number, p1: number, p2: number, p3: number, t: number) => {
		const t2 = t * t;
		const t3 = t2 * t;
		return (
			0.5 *
			(2 * p1 +
				(-p0 + p2) * t +
				(2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
				(-p0 + 3 * p1 - 3 * p2 + p3) * t3)
		);
	};
	const flightAt = (u: number, ys: number[]) => {
		if (!ys.length) return { x: laneX(0), y: 0.52 };
		if (ys.length === 1) return { x: laneX(0), y: ys[0] };
		const maxU = ys.length - 1;
		const clamped = Math.max(0, Math.min(maxU, u));
		const i = Math.min(maxU - 1, Math.floor(clamped));
		const t = clamped - i;
		const y0 = ys[Math.max(0, i - 1)];
		const y1 = ys[i];
		const y2 = ys[Math.min(maxU, i + 1)];
		const y3 = ys[Math.min(maxU, i + 2)];
		return { x: laneX(clamped), y: Math.max(0.12, Math.min(0.88, catmull(y0, y1, y2, y3, t))) };
	};
	const xy = (point: { x: number; y: number }) => `${point.x * 1000},${point.y * 400}`;
	const splinePath = (samples: { x: number; y: number }[]) => {
		if (samples.length < 2) return '';
		let d = `M${xy(samples[0])}`;
		for (let i = 0; i < samples.length - 1; i += 1) {
			const p0 = samples[Math.max(0, i - 1)];
			const p1 = samples[i];
			const p2 = samples[i + 1];
			const p3 = samples[Math.min(samples.length - 1, i + 2)];
			const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
			const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
			d += ` C${xy(c1)} ${xy(c2)} ${xy(p2)}`;
		}
		return d;
	};

	const stopJumperLoop = () => {
		if (jumperRaf) {
			cancelAnimationFrame(jumperRaf);
			jumperRaf = 0;
		}
	};

	const runJumperLoop = () => {
		if (jumperRaf) return;
		const loop = (now: number) => {
			if (!jumper.on) {
				jumperRaf = 0;
				return;
			}
			const t = Math.min(1, (now - flightStart) / Math.max(16, flightPlan.ms));
			const u = t * Math.max(1, jumper.ys.length - 1);
			const point = flightAt(u, jumper.ys);
			jumper.x = point.x;
			jumper.y = point.y;
			jumper.u = u;
			jumperRaf = t < 1 ? requestAnimationFrame(loop) : 0;
		};
		jumperRaf = requestAnimationFrame(loop);
	};

	const spawnJumper = () => {
		if (flightPlan.ys.length < 2) return;
		stopJumperLoop();
		const point = flightAt(0, flightPlan.ys);
		flightStart = performance.now();
		jumper = { on: true, x: point.x, y: point.y, u: 0, ys: flightPlan.ys };
		runJumperLoop();
	};

	const jumperPath = $derived.by(() => {
		if (!jumper.on || jumper.ys.length < 2) return '';
		const steps = Math.max(10, Math.ceil(jumper.u * 22));
		const samples = Array.from({ length: steps + 1 }, (_, i) =>
			flightAt((i / steps) * jumper.u, jumper.ys),
		);
		return splinePath(samples);
	});

	const stopSpinLoop = () => {
		if (spinRaf) {
			cancelAnimationFrame(spinRaf);
			spinRaf = 0;
		}
	};

	const ensureSpinLoop = () => {
		if (spinRaf) return;
		lastSpinTs = performance.now();
		const loop = (now: number) => {
			const dt = Math.min(48, now - lastSpinTs);
			lastSpinTs = now;
			let any = false;
			for (let index = 0; index < slots.length; index += 1) {
				const slot = slots[index];
				if (slot.spinning && !slot.stopping) {
					const tick = tickPx(index);
					slot.offset += dt * (isFinalIndex(index) ? FINAL_SPIN_PX_MS : SPIN_PX_MS);
					const cyclePx = Math.max(tick, slot.cycle.length * tick);
					if (slot.offset > cyclePx * 12) slot.offset -= cyclePx * 6;
					any = true;
				}
			}
			if (any) spinClock += 1;
			spinRaf = any ? requestAnimationFrame(loop) : 0;
		};
		spinRaf = requestAnimationFrame(loop);
	};

	const stopBaseCount = () => {
		if (baseRaf) {
			cancelAnimationFrame(baseRaf);
			baseRaf = 0;
		}
	};

	const snapBase = (payload: {
		hillId: HillId;
		hillMetres: number;
		weatherMetres: number;
		flightMetres: number;
		distanceTotal: number;
		baseWinX: number;
	}) => {
		stopBaseCount();
		const band = payoutBandAt(HILL_TABLE[payload.hillId]?.payoutCurve ?? [], payload.distanceTotal);
		baseTile = {
			locked: false,
			unlocking: false,
			counting: false,
			revealed: true,
			step: 5,
			hillM: payload.hillMetres,
			weatherM: payload.weatherMetres,
			flightM: payload.flightMetres,
			distanceM: payload.distanceTotal,
			baseX: payload.baseWinX,
			shownHill: payload.hillMetres,
			shownWeather: payload.weatherMetres,
			shownFlight: payload.flightMetres,
			shownDistance: payload.distanceTotal,
			shownX: payload.baseWinX,
			bandMin: band.minDistance,
			bandMax: band.maxDistance,
			hillId: payload.hillId,
		};
	};

	const animateBaseX = (to: number, duration: number, gen: number) =>
		new Promise<void>((resolve) => {
			stopBaseCount();
			const start = performance.now();
			let done = false;
			const finish = () => {
				if (done) return;
				done = true;
				if (baseRaf) {
					cancelAnimationFrame(baseRaf);
					baseRaf = 0;
				}
				clearTimeout(failSafe);
				if (gen === revealGen) baseTile.shownX = to;
				resolve();
			};
			const failSafe = setTimeout(finish, duration + 140);
			const tick = (now: number) => {
				if (done || gen !== revealGen) {
					finish();
					return;
				}
				const t = Math.min(1, (now - start) / Math.max(16, duration));
				const eased = 1 - (1 - t) ** 3;
				baseTile.shownX = to * eased;
				if (t < 1) {
					baseRaf = requestAnimationFrame(tick);
					return;
				}
				finish();
			};
			baseRaf = requestAnimationFrame(tick);
		});

	const runBaseCount = async (
		payload: {
			hillId: HillId;
			hillMetres: number;
			weatherMetres: number;
			flightMetres: number;
			distanceTotal: number;
			baseWinX: number;
		},
		timings: TimingProfile,
		gen: number,
	) => {
		const live = () => gen === revealGen;
		const term = timings.baseTermMs;
		const band = payoutBandAt(HILL_TABLE[payload.hillId]?.payoutCurve ?? [], payload.distanceTotal);
		baseTile = {
			...idleBase(),
			locked: false,
			unlocking: false,
			counting: true,
			step: 0,
			hillM: payload.hillMetres,
			weatherM: payload.weatherMetres,
			flightM: payload.flightMetres,
			distanceM: payload.distanceTotal,
			baseX: payload.baseWinX,
			bandMin: band.minDistance,
			bandMax: band.maxDistance,
			hillId: payload.hillId,
		};
		await waitForTimeout(term);
		if (!live()) return;
		baseTile = { ...baseTile, step: 1, shownHill: payload.hillMetres };
		await waitForTimeout(term);
		if (!live()) return;
		baseTile = { ...baseTile, step: 2, shownWeather: payload.weatherMetres };
		await waitForTimeout(term);
		if (!live()) return;
		baseTile = { ...baseTile, step: 3, shownFlight: payload.flightMetres };
		await waitForTimeout(term);
		if (!live()) return;
		baseTile = { ...baseTile, step: 4, shownDistance: payload.distanceTotal };
		await waitForTimeout(Math.round(term * 0.7));
		if (!live()) return;
		baseTile = { ...baseTile, step: 5 };
		await animateBaseX(payload.baseWinX, timings.baseCountMs, gen);
		if (live()) snapBase(payload);
	};

	onDestroy(() => {
		stopSpinLoop();
		stopJumperLoop();
		stopBaseCount();
	});

	const hill = $derived(
		HILL_TABLE[
			BET_MODE_TO_TABLES[(stateBet.activeBetModeKey as BetModeKey) ?? 'BASE']?.hillId ?? 'normal'
		],
	);
	const payline = $derived(paylineDistance(hill.id));
	const weatherDelta = $derived(context.stateGame.lastWeather?.distanceDelta ?? 0);
	const startDistance = $derived(Math.round((hill.baseDistance + weatherDelta) * 10) / 10);
	const liveDistance = $derived.by(() => {
		const extras = slots
			.slice(0, 5)
			.reduce(
				(sum, slot) => sum + (slot.revealed && slot.distanceValue != null ? slot.distanceValue : 0),
				0,
			);
		return Math.round((startDistance + extras) * 10) / 10;
	});
	const qualified = $derived(liveDistance >= payline);
	const jumpState = $derived.by(() => {
		if (!qualified) return { id: 'below', label: t('BELOW PAYLINE') };
		const over = liveDistance - payline;
		if (over >= 40) return { id: 'great', label: t('GREAT JUMP') };
		if (over >= 16) return { id: 'good', label: t('GOOD JUMP') };
		return { id: 'ok', label: t('QUALIFIED') };
	});

	const snapSlot = (index: number, landed: string, patch: Partial<SlotView>) => {
		slots[index] = {
			...slots[index],
			...patch,
			tape: [landed],
			cycle: slots[index].cycle.length ? slots[index].cycle : poolFor(index),
			offset: 0,
			motionMs: 0,
			spinning: false,
			stopping: false,
			revealed: true,
			impact: false,
			locked: false,
			unlocking: false,
		};
	};

	const idleJumper = () => ({
		on: false,
		x: 0.1,
		y: 0.52,
		u: 0,
		ys: [] as number[],
	});

	const startAll = () => {
		stopJumperLoop();
		jumper = idleJumper();
		slots = slots.map((slot, index) => {
			if (index === 5) {
				return {
					...slot,
					spinning: false,
					stopping: false,
					revealed: false,
					impact: false,
					locked: true,
					unlocking: false,
					tape: ['—'],
					offset: 0,
					motionMs: 0,
				};
			}
			const cycle = makeCycle(index);
			return {
				...slot,
				spinning: true,
				stopping: false,
				revealed: false,
				impact: false,
				locked: false,
				unlocking: false,
				cycle,
				tape: makeTape(cycle),
				offset: Math.floor(Math.random() * cycle.length) * tickPx(index),
				motionMs: 0,
			};
		});
		ensureSpinLoop();
	};

	const startFinalSpin = () => {
		const cycle = makeCycle(5);
		slots[5] = {
			...slots[5],
			locked: false,
			unlocking: false,
			spinning: true,
			stopping: false,
			revealed: false,
			impact: false,
			cycle,
			tape: makeTape(cycle),
			offset: Math.floor(Math.random() * cycle.length) * tickPx(5),
			motionMs: 0,
		};
		ensureSpinLoop();
	};

	const stopSlot = async (
		index: number,
		landed: string,
		stopMs: number,
		catchUp: boolean,
		patch: Partial<SlotView>,
	) => {
		const gen = revealGen;
		if (catchUp) {
			snapSlot(index, landed, patch);
			return;
		}
		if (!slots[index].spinning) {
			const cycle = slots[index].cycle.length ? slots[index].cycle : makeCycle(index);
			slots[index] = {
				...slots[index],
				spinning: true,
				stopping: false,
				revealed: false,
				cycle,
				tape: slots[index].tape.length > 8 ? slots[index].tape : makeTape(cycle),
				offset: slots[index].offset,
				motionMs: 0,
			};
			ensureSpinLoop();
			await waitFrames(2);
			if (gen !== revealGen) return;
		}
		slots[index].stopping = true;
		const cycle = slots[index].cycle.length ? slots[index].cycle : poolFor(index);
		const tape = slots[index].tape.length > 8 ? slots[index].tape : makeTape(cycle);
		const tick = tickPx(index);
		const pad = windowPad(index);
		const planned = planStop(slots[index].offset, tape, cycle, landed, tick, pad);
		const distance = Math.max(tick * STOP_MIN_TICKS, planned.targetOffset - planned.frozen);
		const travelMs = distance / ((isFinalIndex(index) ? FINAL_SPIN_PX_MS : SPIN_PX_MS) * 0.58);
		const motionMs = Math.min(
			880,
			Math.max(
				220,
				Number.isFinite(travelMs) && Number.isFinite(stopMs)
					? Math.round(Math.min(stopMs * 1.15, Math.max(stopMs * 0.8, travelMs)))
					: 420,
			),
		);
		slots[index] = {
			...slots[index],
			spinning: false,
			stopping: true,
			revealed: false,
			impact: false,
			cycle,
			tape,
			offset: planned.frozen,
			motionMs: 0,
		};
		await waitFrames(2);
		if (gen !== revealGen) return;
		slots[index] = {
			...slots[index],
			offset: planned.targetOffset,
			motionMs,
		};
		await waitForTimeout(motionMs);
		if (gen !== revealGen) return;
		slots[index] = {
			...slots[index],
			...patch,
			tape,
			offset: planned.targetOffset,
			motionMs: 0,
			spinning: false,
			stopping: false,
			revealed: true,
			impact: true,
		};
		await waitForTimeout(stopMs < 180 ? 50 : 160);
		if (gen === revealGen) slots[index] = { ...slots[index], impact: false };
	};

	context.eventEmitter.subscribeOnMount({
		skyjumpWeatherShow: async (event) => {
			const gen = ++weatherGen;
			weatherCandidates = event.candidates ?? [];
			weatherTurbo = event.timings.id === 'turbo';
			weatherClosing = false;
			if (event.catchUp) {
				weatherDrawOpen = false;
				context.stateGame.weatherDrawing = false;
				weatherHighlightId = event.winnerId;
				return;
			}
			weatherDrawOpen = true;
			context.stateGame.weatherDrawing = true;
			weatherHighlightId = null;
			await waitFrames(2);
			if (gen !== weatherGen) return;
			const passes = event.timings.id === 'turbo' ? 1 : 2;
			for (let pass = 0; pass < passes; pass += 1) {
				for (const candidate of weatherCandidates) {
					if (gen !== weatherGen) return;
					weatherHighlightId = candidate.id;
					await waitForTimeout(event.timings.weatherCycleMs);
				}
			}
			if (gen !== weatherGen) return;
			weatherHighlightId = event.winnerId;
			await waitForTimeout(event.timings.weatherHoldMs);
			if (gen !== weatherGen) return;
			weatherClosing = true;
			context.stateGame.weatherDrawing = false;
			await waitForTimeout(event.timings.weatherStatsMs);
			if (gen !== weatherGen) return;
			weatherDrawOpen = false;
			weatherClosing = false;
		},
		skyjumpResetBoard: () => {
			weatherGen += 1;
			weatherDrawOpen = false;
			weatherClosing = false;
			weatherHighlightId = null;
			revealGen += 1;
			stopSpinLoop();
			stopJumperLoop();
			stopBaseCount();
			flightPlan = { ys: [], ms: 1 };
			jumper = idleJumper();
			baseTile = idleBase();
			slots = emptySlots();
		},
		skyjumpSlotsPrepare: () => {
			revealGen += 1;
			stopSpinLoop();
			stopJumperLoop();
			stopBaseCount();
			flightPlan = { ys: [], ms: 1 };
			jumper = idleJumper();
			baseTile = idleBase();
			slots = emptySlots();
		},
		skyjumpReelsSpinAll: async ({ timings, flightMetres }) => {
			flightPlan = {
				ys: (flightMetres ?? []).map((value, index) => yFromMetres(value, index)),
				ms: 4 * (timings.reelGapMs + timings.reelStopMs),
			};
			startAll();
		},
		skyjumpSlotReveal: async ({ slot, timings, catchUp }) => {
			await stopSlot(
				slot.reelIndex,
				formatDistance(slot.distanceValue),
				timings.reelStopMs,
				!!catchUp,
				{
					label: slot.label,
					distanceValue: slot.distanceValue,
					localMultiplier: slot.localMultiplier,
					rarity: slot.rarity,
				},
			);
			if (catchUp) return;
			if (slot.reelIndex === 0) spawnJumper();
		},
		skyjumpBaseLocked: () => {
			stopBaseCount();
			baseTile = idleBase();
		},
		skyjumpBaseCount: async ({
			hillId,
			hillMetres,
			weatherMetres,
			flightMetres,
			distanceTotal,
			baseWinX,
			timings,
			catchUp,
		}) => {
			const payload = {
				hillId,
				hillMetres,
				weatherMetres,
				flightMetres,
				distanceTotal,
				baseWinX,
			};
			if (catchUp) {
				snapBase(payload);
				return;
			}
			const gen = revealGen;
			baseTile = {
				...idleBase(),
				locked: false,
				unlocking: true,
				counting: true,
				hillM: hillMetres,
				weatherM: weatherMetres,
				flightM: flightMetres,
				distanceM: distanceTotal,
				baseX: baseWinX,
				hillId,
			};
			await waitForTimeout(timings.id === 'turbo' ? 60 : 160);
			if (gen !== revealGen) return;
			await runBaseCount(payload, timings, gen);
		},
		skyjumpFinalUnlock: async ({ timings, catchUp }) => {
			if (catchUp) {
				slots[5] = { ...slots[5], locked: false, unlocking: false };
				return;
			}
			slots[5] = { ...slots[5], locked: false, unlocking: true };
			await waitForTimeout(timings.id === 'turbo' ? 180 : 520);
			startFinalSpin();
			await waitForTimeout(timings.id === 'turbo' ? 80 : 180);
		},
		skyjumpFinalLocked: () => {
			slots[5] = {
				...slots[5],
				locked: true,
				unlocking: false,
				spinning: false,
				stopping: false,
				revealed: false,
				tape: ['—'],
				offset: 0,
			};
		},
		skyjumpFinalMultiplierReveal: async ({ finalMultiplier, timings, catchUp }) => {
			const locals = slots
				.slice(0, 5)
				.reduce((product, slot) => product * Math.max(1, slot.localMultiplier || 1), 1);
			const combined = locals * (finalMultiplier.multiplier || 0);
			const label = formatMult(combined);
			await stopSlot(
				5,
				label,
				timings.reelStopMs + (timings.id === 'turbo' ? 40 : 160),
				!!catchUp,
				{
					label,
					distanceValue: null,
					localMultiplier: combined,
				},
			);
		},
	});
</script>

{#snippet sparksOn(sparkHeat: { id: string; pulse: number })}
	{@const boltCount = 8 + sparkHeat.pulse * 3}
	{@const popCount = 3 + sparkHeat.pulse * 2}
	<span class="sparks {sparkHeat.id}" class:hot-burst={sparkHeat.pulse >= 2} aria-hidden="true">
		<b class="core"></b>
		{#each SPARK_BOLTS.slice(0, boltCount) as spark}
			<i
				class="bolt"
				class:jagged={spark.jagged}
				style:--a={`${spark.a}deg`}
				style:--len={`${spark.len}px`}
				style:--dist={`${spark.dist}px`}
				style:--d={`${spark.d}s`}
			></i>
		{/each}
		{#each SPARK_POPS.slice(0, popCount) as pop}
			<i class="pop" style:--x={pop.x} style:--y={pop.y} style:--s={pop.s} style:--d={`${pop.d}s`}
			></i>
		{/each}
	</span>
{/snippet}

{#snippet reelFace(index: number, isFinal: boolean)}
	{@const role = SLOT_ROLES[index]}
	{@const cell = slots[index]}
	{@const heat = !isFinal ? slotHeatFor(index, cell.distanceValue, cell.localMultiplier) : null}
	{@const sparkHeat = isFinal
		? cell.revealed && cell.localMultiplier >= 2
			? {
					id: cell.localMultiplier >= 5 ? 'pos-max' : 'pos-hi',
					pulse: (cell.localMultiplier >= 5 ? 3 : 2) as 2 | 3,
				}
			: null
		: heat && cell.revealed && sparkWorthy(heat)
			? { id: heat.id, pulse: (heat.pulse === 0 ? 1 : heat.pulse) as 1 | 2 | 3 }
			: null}
	{@const sad = !isFinal && heat && cell.revealed && sadHeat(heat)}
	{@const hot = cell.revealed && !isFinal && cell.localMultiplier > 1}
	{@const live = cell.spinning || cell.stopping}
	{@const rolling = isFinal || live || cell.tape.length > 1}
	{@const tick = tickPx(index)}
	{@const pad = windowPad(index)}
	{@const shown = cell.revealed
		? (cell.tape[Math.round(cell.offset / tick) + pad] ?? cell.tape[0] ?? '—')
		: (cell.tape[0] ?? '—')}
	{@const landedIndex = Math.round(cell.offset / tick) + pad}
	{@const xl = isFinal && shown.length >= 4}
	<img src={roleIconSrc[role.iconKey] ?? roleIconSrc.speed} alt="" />
	<span class="role">{isFinal ? t(role.label) : t(role.shortLabel)}</span>
	<div class="value">
		{#if rolling}
			<div class="window" class:horiz={isFinal}>
				<div
					class="tape"
					style:transform={isFinal
						? `translateX(-${cell.offset + tick / 2}px)`
						: `translateY(-${cell.offset}px)`}
					style:transition={cell.stopping && cell.motionMs
						? `transform ${cell.motionMs}ms cubic-bezier(0.16, 0.84, 0.32, 1)`
						: 'none'}
				>
					{#each cell.tape as tick, tickIndex}
						{@const tickValue = parseDistanceTick(tick)}
						{@const tickHeat = !isFinal ? slotHeatFor(index, tickValue) : null}
						{@const landed = cell.revealed && tickIndex === landedIndex}
						<span class="tick {tickHeat?.id ?? ''}" class:landed>
							{tick}
							{#if landed && sparkHeat}
								{@render sparksOn(sparkHeat)}
							{/if}
							{#if landed && sad}
								<span class="sad" aria-hidden="true">😞</span>
							{/if}
						</span>
					{/each}
				</div>
			</div>
		{:else}
			<p
				class="result {heat?.id ?? ''}"
				class:xl
				class:pulse-1={heat?.pulse === 1}
				class:pulse-2={heat?.pulse === 2}
				class:pulse-3={heat?.pulse === 3}
			>
				{shown}
				{#if sparkHeat}
					{@render sparksOn(sparkHeat)}
				{/if}
				{#if sad}
					<span class="sad" aria-hidden="true">😞</span>
				{/if}
			</p>
		{/if}
		{#if !isFinal && hot}
			<span class="badge">x{cell.localMultiplier}</span>
		{:else if !isFinal}
			<span class="badge ghost">&nbsp;</span>
		{/if}
	</div>
{/snippet}

{#if context.stateGame.screen === 'play'}
	<div class="strip" aria-hidden="true" data-clock={spinClock}>
		<div
			class="meter"
			class:ok={qualified}
			class:below={!qualified}
			class:great={jumpState.id === 'great'}
		>
			<strong>{liveDistance.toFixed(1)} m</strong>
			<span class="base-chip">{t('BASE')} {startDistance.toFixed(1)} m</span>
			<span>{t('PAYLINE')} {payline} m</span>
			<span class="state">{jumpState.label}</span>
		</div>
		<div
			class="flight-board"
			class:weather-mode={weatherDrawOpen && !weatherClosing}
			class:drawing={weatherDrawOpen}
		>
			<svg class="jumper-layer" viewBox="0 0 1000 400" preserveAspectRatio="none">
				<defs>
					<linearGradient id="sj-jumper-trail" x1="0" y1="0" x2="1" y2="0">
						<stop offset="0%" stop-color="#65c8ff" stop-opacity="0.05" />
						<stop offset="55%" stop-color="#7cffb2" stop-opacity="0.55" />
						<stop offset="100%" stop-color="#ffc940" stop-opacity="0.95" />
					</linearGradient>
				</defs>
				{#if jumper.on && jumper.u > 0.02}
					<path class="ribbon-glow" d={jumperPath} />
					<path class="ribbon" d={jumperPath} />
				{/if}
				{#if jumper.on}
					<circle class="jumper-glow" cx={jumper.x * 1000} cy={jumper.y * 400} r="16" />
					<circle class="jumper-dot" cx={jumper.x * 1000} cy={jumper.y * 400} r="7" />
				{/if}
			</svg>
			{#if weatherDrawOpen && weatherHero}
				<div class="weather-lottery" class:turbo={weatherTurbo} class:closing={weatherClosing}>
					<p class="weather-kicker">{t('HILL CONDITIONS')}</p>
					<div class="weather-hero {weatherSign(weatherHeroDelta)}">
						<div class="weather-icon">
							<img src={weatherIconSrc[weatherHero.iconKey] ?? weatherIconSrc.sunny} alt="" />
						</div>
						<div class="weather-copy">
							<strong>{t(weatherHero.label)}</strong>
							<span class={weatherSign(weatherHeroDelta)}>
								{weatherHeroDelta > 0 ? '+' : ''}{weatherHeroDelta.toFixed(1)} m
							</span>
						</div>
					</div>
					<div class="weather-grid">
						{#each weatherCandidates as candidate}
							{@const sign = weatherSign(candidate.distanceDelta)}
							<div class="weather-chip {sign}" class:on={candidate.id === weatherHighlightId}>
								<img src={weatherIconSrc[candidate.iconKey] ?? weatherIconSrc.sunny} alt="" />
								<em>{candidate.distanceDelta > 0 ? '+' : ''}{candidate.distanceDelta.toFixed(1)}</em>
							</div>
						{/each}
					</div>
				</div>
			{/if}
			<div class="lanes">
				{#each SLOT_ROLES.slice(0, 5) as role, index (role.shortLabel)}
					{@const cell = slots[index]}
					{@const heat = slotHeatFor(index, cell.distanceValue, cell.localMultiplier)}
					<div
						class="cell lane {heat && cell.revealed ? heat.id : ''}"
						class:spinning={cell.spinning}
						class:stopping={cell.stopping}
						class:revealed={cell.revealed}
						class:impact={cell.impact}
						class:hot={cell.revealed && cell.localMultiplier > 1}
						class:pulse-1={cell.revealed && heat?.pulse === 1}
						class:pulse-2={cell.revealed && heat?.pulse === 2}
						class:pulse-3={cell.revealed && heat?.pulse === 3}
					>
						{@render reelFace(index, false)}
					</div>
				{/each}
			</div>
		</div>
		<div
			class="base-rail"
			class:locked={baseTile.locked}
			class:unlocking={baseTile.unlocking}
			class:counting={baseTile.counting}
			class:revealed={baseTile.revealed}
		>
			{#if !baseTile.locked}
				<p class="base-kicker">{t('BASE MULTIPLIER')}</p>
				<div class="eq">
					<div class="term" class:on={baseTile.step >= 1}>
						<strong>{t('BASE FORMULA HILL')}</strong>
					</div>
					<span class="op" class:on={baseTile.step >= 2}>+</span>
					<div class="term" class:on={baseTile.step >= 2}>
						<strong>{t('BASE FORMULA WEATHER')}</strong>
					</div>
					<span class="op" class:on={baseTile.step >= 3}>+</span>
					<div class="term" class:on={baseTile.step >= 3}>
						<strong>{t('BASE FORMULA SLOTS')}</strong>
					</div>
					<span class="op" class:on={baseTile.step >= 4}>→</span>
					<div class="term total" class:on={baseTile.step >= 4}>
						<strong>{t('BASE FORMULA TABLE')}</strong>
					</div>
				</div>
				<p class="base-formula">
					{t('BASE MULTIPLIER EQ')}
				</p>
				<p class="base-map" class:on={baseTile.step >= 5}>
					{baseTile.step >= 5
						? `${formatMetres(baseTile.shownDistance)} ${t('SITS IN')} ${formatBand(baseTile.bandMin, baseTile.bandMax)} — ${t('PAYS')} ${formatBaseX(baseTile.baseX)}`
						: t('BASE CURVE EQ')}
				</p>
				<p class="base-x" class:on={baseTile.step >= 5}>
					{baseTile.step >= 5 ? formatBaseX(baseTile.shownX) : '—'}
				</p>
			{/if}
			{#if baseTile.locked || baseTile.unlocking}
				<div class="lock-veil" class:unlocking={baseTile.unlocking}>
					<span class="lock-mark">🔒</span>
					<strong>{t('LOCKED')}</strong>
					<em>{t('REACH PAYLINE')}</em>
				</div>
			{/if}
		</div>
		<div
			class="cell final-rail final"
			class:spinning={slots[5].spinning}
			class:stopping={slots[5].stopping}
			class:revealed={slots[5].revealed}
			class:impact={slots[5].impact}
			class:locked={slots[5].locked}
			class:unlocking={slots[5].unlocking}
		>
			{#if !slots[5].locked || slots[5].unlocking}
				{@render reelFace(5, true)}
			{/if}
			{#if slots[5].locked || slots[5].unlocking}
				<div class="lock-veil" class:unlocking={slots[5].unlocking}>
					<span class="lock-mark">🔒</span>
					<strong>{t('LOCKED')}</strong>
					<em>{t('REACH PAYLINE')}</em>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.strip {
		--tick: 48px;
		--final-tick: 68px;
		--visible-ticks: 3;
		--ease-stop: cubic-bezier(0.16, 0.84, 0.32, 1);
		--ease-pop: cubic-bezier(0.2, 1.35, 0.4, 1);
		position: absolute;
		z-index: 20;
		top: 12vh;
		left: 50%;
		bottom: auto;
		display: grid;
		gap: 0.55rem;
		width: min(86vw, 1450px);
		transform: translateX(-50%);
		pointer-events: none;
	}

	.meter {
		display: flex;
		gap: 1.1rem;
		align-items: baseline;
		justify-content: center;
		width: min(62vw, 880px);
		min-height: 48px;
		margin: 0 auto;
		padding: 0.35rem 1.1rem;
		color: #9bb4c8;
		background: rgba(5, 22, 43, 0.88);
		border: 1px solid rgba(101, 200, 255, 0.55);
		border-radius: 999px;
		font-size: clamp(12px, 1.15vw, 16px);
		font-weight: 800;
		letter-spacing: 0.08em;
	}

	.meter strong {
		color: #f4faff;
		font-size: clamp(22px, 2.1vw, 34px);
		letter-spacing: 0.02em;
	}

	.meter .base-chip {
		padding: 0.12rem 0.55rem;
		color: #07182f;
		background: #65c8ff;
		border-radius: 999px;
		letter-spacing: 0.08em;
	}

	.meter.ok {
		border-color: #65c8ff;
		color: #a8e6ff;
	}

	.meter.ok strong {
		color: #a8e6ff;
	}

	.meter.great {
		border-color: #ffc940;
		color: #ffe083;
	}

	.meter.great strong {
		color: #ffe083;
	}

	.meter.below .state {
		color: #ffc940;
		animation: below-pulse 1.15s ease-in-out infinite;
	}

	.flight-board {
		position: relative;
		display: grid;
		min-height: min(24vh, 230px);
		overflow: hidden;
		color: #f4faff;
		background:
			linear-gradient(180deg, rgba(16, 48, 82, 0.62), rgba(4, 18, 36, 0.94) 58%),
			rgba(5, 22, 43, 0.92);
		border: 2px solid rgba(126, 214, 255, 0.95);
		border-radius: 18px;
		box-shadow:
			inset 0 1px 0 rgba(168, 230, 255, 0.34),
			0 14px 28px rgba(3, 14, 29, 0.28);
	}

	.flight-board.drawing {
		border-color: rgba(168, 230, 255, 1);
		box-shadow:
			inset 0 1px 0 rgba(168, 230, 255, 0.42),
			0 14px 28px rgba(3, 14, 29, 0.28),
			0 0 28px rgba(101, 200, 255, 0.22);
	}

	.flight-board.weather-mode .lanes,
	.flight-board.weather-mode .jumper-layer {
		opacity: 0;
		pointer-events: none;
	}

	.weather-lottery {
		position: absolute;
		inset: 0;
		z-index: 8;
		display: grid;
		align-content: center;
		gap: 0.55rem;
		padding: 0.7rem 1rem 0.85rem;
		background:
			radial-gradient(circle at 20% 20%, rgba(101, 200, 255, 0.18), transparent 48%),
			linear-gradient(180deg, rgba(10, 36, 64, 0.96), rgba(4, 16, 32, 0.98));
		animation: weather-in 0.42s cubic-bezier(0.2, 0.8, 0.2, 1);
	}

	.weather-lottery.turbo {
		animation-duration: 0.18s;
	}

	.weather-lottery.closing {
		animation: weather-out 0.4s ease-in forwards;
	}

	.weather-kicker {
		margin: 0;
		color: #a8e6ff;
		font-size: clamp(11px, 1.05vw, 15px);
		font-weight: 800;
		letter-spacing: 0.18em;
		text-align: center;
	}

	.weather-hero {
		display: flex;
		gap: 0.7rem;
		align-items: center;
		justify-content: center;
		min-height: 4.2rem;
	}

	.weather-icon {
		display: grid;
		place-items: center;
		width: 4.2rem;
		height: 4.2rem;
		background: rgba(7, 24, 46, 0.8);
		border: 1px solid rgba(101, 200, 255, 0.4);
		border-radius: 14px;
	}

	.weather-hero.pos .weather-icon {
		border-color: rgba(124, 255, 178, 0.9);
		box-shadow: 0 0 18px rgba(124, 255, 178, 0.28);
	}

	.weather-hero.neg .weather-icon {
		border-color: rgba(255, 107, 107, 0.9);
		box-shadow: 0 0 18px rgba(255, 107, 107, 0.25);
	}

	.weather-icon img {
		width: 44px;
		height: 44px;
	}

	.weather-copy {
		display: grid;
		gap: 0.18rem;
		min-width: 0;
	}

	.weather-copy strong {
		font-size: clamp(18px, 2vw, 28px);
		font-weight: 800;
		letter-spacing: 0.04em;
	}

	.weather-copy span {
		font-size: clamp(14px, 1.4vw, 20px);
		font-weight: 800;
		letter-spacing: 0.06em;
	}

	.weather-copy span.pos,
	.weather-chip.pos em {
		color: #7cffb2;
	}

	.weather-copy span.neg,
	.weather-chip.neg em {
		color: #ff8a8a;
	}

	.weather-copy span.neu,
	.weather-chip.neu em {
		color: #c5d6e4;
	}

	.weather-grid {
		display: grid;
		grid-template-columns: repeat(6, minmax(0, 1fr));
		gap: 0.4rem;
	}

	.weather-chip {
		display: grid;
		justify-items: center;
		gap: 0.18rem;
		min-height: 4.6rem;
		padding: 0.35rem 0.2rem 0.4rem;
		background: rgba(8, 24, 44, 0.78);
		border: 1px solid rgba(42, 74, 102, 0.9);
		border-radius: 12px;
		opacity: 0.42;
		transition:
			opacity 180ms ease,
			border-color 180ms ease,
			transform 180ms ease,
			box-shadow 180ms ease;
	}

	.weather-chip.on {
		opacity: 1;
		transform: translateY(-3px) scale(1.04);
	}

	.weather-chip.pos.on {
		border-color: #7cffb2;
		box-shadow: 0 0 16px rgba(124, 255, 178, 0.28);
	}

	.weather-chip.neg.on {
		border-color: #ff6b6b;
		box-shadow: 0 0 16px rgba(255, 107, 107, 0.25);
	}

	.weather-chip.neu.on {
		border-color: #65c8ff;
		box-shadow: 0 0 16px rgba(101, 200, 255, 0.25);
	}

	.weather-chip img {
		width: 28px;
		height: 28px;
	}

	.weather-chip em {
		font-size: clamp(11px, 1.05vw, 14px);
		font-style: normal;
		font-weight: 800;
		letter-spacing: 0.04em;
	}

	@keyframes weather-in {
		from {
			opacity: 0.2;
			transform: scale(0.98);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	@keyframes weather-out {
		from {
			opacity: 1;
		}
		to {
			opacity: 0;
		}
	}

	.lanes {
		position: relative;
		z-index: 1;
		display: grid;
		grid-template-columns: repeat(5, minmax(0, 1fr));
		min-height: min(24vh, 230px);
	}

	.jumper-layer {
		position: absolute;
		inset: 0;
		z-index: 6;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	.ribbon-glow {
		fill: none;
		stroke: rgba(168, 230, 255, 0.4);
		stroke-width: 22;
		stroke-linecap: round;
		stroke-linejoin: round;
		filter: blur(3px);
	}

	.ribbon {
		fill: none;
		stroke: url(#sj-jumper-trail);
		stroke-width: 10;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.jumper-glow {
		fill: rgba(255, 201, 64, 0.28);
	}

	.jumper-dot {
		fill: #fff;
		stroke: #ffc940;
		stroke-width: 4;
		filter: drop-shadow(0 0 10px #65c8ff);
	}

	.cell {
		position: relative;
		display: grid;
		grid-template-rows: auto auto minmax(0, 1fr);
		justify-items: center;
		align-content: stretch;
		min-height: min(24vh, 230px);
		padding: 0.65rem 0.3rem 0.85rem;
		color: #f4faff;
		background: transparent;
		border: 0;
		border-radius: 0;
		box-shadow: none;
		overflow: hidden;
	}

	.cell.lane + .cell.lane {
		box-shadow: inset 1px 0 0 rgba(126, 214, 255, 0.28);
	}

	.final-rail {
		display: grid;
		grid-template-columns: minmax(7.2rem, 20%) minmax(0, 80%);
		grid-template-rows: auto auto;
		align-items: center;
		justify-items: stretch;
		gap: 0.15rem 0.55rem;
		min-height: min(10vh, 92px);
		padding: 0.35rem 0.7rem 0.35rem 0.85rem;
		overflow: hidden;
		background:
			radial-gradient(circle at 8% 50%, rgba(255, 201, 64, 0.18), transparent 42%),
			linear-gradient(180deg, rgba(32, 38, 16, 0.94), rgba(10, 16, 8, 0.96));
		border: 2px solid #ffc940;
		border-radius: 16px;
		box-shadow:
			inset 0 1px 0 rgba(255, 224, 131, 0.28),
			0 0 22px rgba(255, 201, 64, 0.18);
	}

	.final-rail img {
		grid-column: 1;
		grid-row: 1;
		justify-self: start;
		align-self: end;
		margin-top: 0;
		filter: none;
	}

	.final-rail .role {
		grid-column: 1;
		grid-row: 2;
		justify-self: start;
		align-self: start;
		max-width: none;
	}

	.final-rail .value {
		grid-column: 2;
		grid-row: 1 / span 2;
		width: 100%;
		min-width: 0;
		align-items: stretch;
		overflow: hidden;
	}

	.final-rail .result,
	.final-rail .badge {
		display: none;
	}

	.final-rail.locked {
		border-color: rgba(201, 162, 77, 0.45);
		filter: saturate(0.55);
	}

	.base-rail {
		position: relative;
		display: grid;
		grid-template-columns: minmax(0, 1.55fr) auto;
		grid-template-rows: auto auto auto auto;
		align-items: center;
		gap: 0.18rem 1rem;
		min-height: min(17vh, 158px);
		padding: 0.5rem 1.1rem 0.55rem;
		overflow: hidden;
		color: #ffe9a8;
		background:
			radial-gradient(circle at 12% 40%, rgba(255, 201, 64, 0.28), transparent 46%),
			linear-gradient(180deg, rgba(48, 38, 10, 0.96), rgba(14, 12, 4, 0.97));
		border: 2px solid #ffc940;
		border-radius: 16px;
		box-shadow:
			inset 0 1px 0 rgba(255, 224, 131, 0.38),
			0 0 28px rgba(255, 201, 64, 0.28);
	}

	.base-rail.locked {
		border-color: rgba(201, 162, 77, 0.45);
		filter: saturate(0.55);
		box-shadow: inset 0 1px 0 rgba(255, 224, 131, 0.12);
	}

	.base-rail.counting,
	.base-rail.revealed {
		filter: none;
		box-shadow:
			inset 0 1px 0 rgba(255, 248, 210, 0.45),
			0 0 36px rgba(255, 201, 64, 0.48);
	}

	.base-kicker {
		grid-column: 1 / -1;
		grid-row: 1;
		margin: 0;
		color: #ffc940;
		font-size: clamp(11px, 1.05vw, 15px);
		font-weight: 800;
		letter-spacing: 0.18em;
	}

	.eq {
		grid-column: 1;
		grid-row: 2;
		display: flex;
		flex-wrap: wrap;
		gap: 0.2rem 0.45rem;
		align-items: end;
	}

	.eq .term {
		display: grid;
		gap: 0.08rem;
		min-width: 0;
		opacity: 0.28;
		transform: translateY(4px);
		transition:
			opacity 220ms ease,
			transform 220ms ease;
	}

	.eq .term.on {
		opacity: 1;
		transform: translateY(0);
	}

	.eq .term.on strong {
		animation: term-pop 0.32s var(--ease-pop);
	}

	.eq strong {
		color: #fff6d6;
		font-size: clamp(15px, 1.7vw, 28px);
		font-weight: 800;
		letter-spacing: 0.04em;
		line-height: 1.05;
	}

	.eq .total strong {
		color: #ffe083;
	}

	.eq .op {
		padding-bottom: 0.12rem;
		color: #c9a44d;
		font-size: clamp(18px, 1.8vw, 26px);
		font-weight: 800;
		opacity: 0.25;
		transition: opacity 200ms ease;
	}

	.eq .op.on {
		opacity: 1;
		color: #ffc940;
	}

	.base-formula {
		grid-column: 1;
		grid-row: 3;
		margin: 0;
		color: #d7b45a;
		font-size: clamp(9px, 0.82vw, 12px);
		font-weight: 800;
		letter-spacing: 0.06em;
	}

	.base-formula span {
		margin: 0 0.35rem;
		opacity: 0.55;
	}

	.base-map {
		grid-column: 1;
		grid-row: 4;
		margin: 0;
		color: #c9a44d;
		font-size: clamp(9px, 0.8vw, 12px);
		font-weight: 800;
		letter-spacing: 0.12em;
		opacity: 0.45;
	}

	.base-map.on {
		opacity: 1;
		color: #ffe083;
	}

	.base-x {
		grid-column: 2;
		grid-row: 2 / span 3;
		margin: 0;
		color: #ffd24a;
		font-size: clamp(32px, 4.2vw, 64px);
		font-weight: 900;
		letter-spacing: 0.02em;
		line-height: 0.92;
		text-shadow: 0 0 22px rgba(255, 201, 64, 0.55);
		font-variant-numeric: tabular-nums;
		opacity: 0.22;
		transition:
			opacity 280ms ease,
			transform 280ms ease;
	}

	.base-x.on {
		opacity: 1;
		transform: scale(1.04);
	}

	.lock-veil {
		position: absolute;
		inset: 0;
		z-index: 12;
		display: grid;
		align-content: center;
		justify-items: center;
		gap: 0.15rem;
		color: #ffe083;
		background: linear-gradient(
			90deg,
			rgba(8, 12, 6, 0.97),
			rgba(16, 14, 6, 0.98) 50%,
			rgba(8, 12, 6, 0.97)
		);
		letter-spacing: 0.14em;
	}

	.lock-veil strong {
		font-size: clamp(16px, 1.6vw, 24px);
	}

	.lock-veil em {
		color: #9bb4c8;
		font-size: clamp(11px, 1.05vw, 14px);
		font-style: normal;
		letter-spacing: 0.16em;
	}

	.lock-mark {
		font-size: 1.4rem;
		filter: grayscale(0.2);
	}

	.lock-veil.unlocking {
		animation: unlock-flash 0.52s ease-out forwards;
	}

	.cell.final {
		background:
			radial-gradient(circle at 50% 16%, rgba(255, 201, 64, 0.2), transparent 48%),
			linear-gradient(180deg, rgba(32, 38, 16, 0.94), rgba(10, 16, 8, 0.96));
		border-color: #ffc940;
		box-shadow:
			inset 0 1px 0 rgba(255, 224, 131, 0.28),
			0 0 22px rgba(255, 201, 64, 0.18);
	}

	.cell.spinning {
		border-color: #a8e6ff;
	}

	.cell.lane.spinning,
	.cell.lane.stopping {
		background: rgba(168, 230, 255, 0.08);
	}

	.final-rail .window {
		width: 100%;
		height: 64px;
		overflow: hidden;
	}

	.final-rail .window.horiz {
		position: relative;
		overflow: hidden;
		flex-wrap: nowrap;
		-webkit-mask-image: linear-gradient(90deg, transparent, #000 7%, #000 93%, transparent);
		mask-image: linear-gradient(90deg, transparent, #000 7%, #000 93%, transparent);
	}

	.final-rail .window.horiz::after {
		content: '';
		position: absolute;
		left: 50%;
		top: 3px;
		bottom: 3px;
		z-index: 3;
		width: var(--final-tick);
		border: 1px solid rgba(255, 201, 64, 0.55);
		border-radius: 10px;
		box-shadow: inset 0 0 12px rgba(255, 201, 64, 0.12);
		transform: translateX(-50%);
		pointer-events: none;
	}

	.final-rail .tape {
		position: absolute;
		left: 50%;
		top: 0;
		display: flex;
		flex-direction: row;
		flex-wrap: nowrap;
		width: max-content;
		height: 100%;
		white-space: nowrap;
	}

	.final-rail .tick {
		flex: 0 0 var(--final-tick);
		width: var(--final-tick);
		height: 100%;
		font-size: clamp(16px, 1.5vw, 24px);
	}

	.final-rail.spinning,
	.final-rail.stopping {
		border-color: #ffe083;
	}

	.cell.stopping:not(.final) {
		border-color: #a8e6ff;
	}

	.cell.impact .tick.landed {
		animation: stop-hit 0.28s var(--ease-pop);
	}

	.cell.final.impact .tick.landed {
		animation: slot6-hit 0.42s var(--ease-pop);
	}

	.cell.hot {
		box-shadow:
			inset 0 1px 0 rgba(168, 230, 255, 0.28),
			0 0 0 1px rgba(255, 201, 64, 0.7);
	}

	.cell.hot::after {
		content: '';
		position: absolute;
		inset: 0;
		z-index: 0;
		background: linear-gradient(180deg, rgba(255, 201, 64, 0.16), transparent 48%);
		animation: flash 0.45s ease-out;
		pointer-events: none;
	}

	.sparks {
		position: absolute;
		left: 50%;
		top: 50%;
		z-index: 8;
		width: 220%;
		height: 220%;
		overflow: visible;
		transform: translate(-50%, -50%);
		pointer-events: none;
		mix-blend-mode: screen;
		filter: drop-shadow(0 0 10px currentColor);
	}

	.sparks .core {
		position: absolute;
		left: 50%;
		top: 50%;
		width: 12px;
		height: 12px;
		border-radius: 999px;
		background: #fff;
		box-shadow:
			0 0 16px 6px #fff,
			0 0 28px 12px currentColor,
			0 0 52px 18px currentColor;
		transform: translate(-50%, -50%);
		opacity: 0.9;
		animation: spark-core 0.55s ease-in-out infinite;
	}

	.sparks .bolt {
		position: absolute;
		left: 50%;
		top: 50%;
		width: 5px;
		height: var(--len);
		border-radius: 2px;
		background: linear-gradient(to top, transparent 0%, currentColor 22%, #fff 72%, #fff 100%);
		box-shadow:
			0 0 8px 2px #fff,
			0 0 14px 4px currentColor,
			0 0 26px 8px currentColor;
		opacity: 0;
		transform-origin: center bottom;
		animation: spark-bolt 0.7s ease-out infinite;
		animation-delay: var(--d);
	}

	.sparks .bolt.jagged {
		width: 6px;
		clip-path: polygon(45% 0, 100% 16%, 30% 38%, 95% 58%, 20% 100%, 0 60%, 62% 38%, 8% 16%);
	}

	.sparks .bolt::after {
		content: '';
		position: absolute;
		left: 50%;
		top: 18%;
		width: 14px;
		height: 3px;
		border-radius: 1px;
		background: #fff;
		box-shadow: 0 0 10px 2px currentColor;
		transform: translateX(-35%) rotate(38deg);
	}

	.sparks .pop {
		position: absolute;
		left: 50%;
		top: 50%;
		width: 16px;
		height: 16px;
		background: #fff;
		clip-path: polygon(50% 0, 62% 38%, 100% 50%, 62% 62%, 50% 100%, 38% 62%, 0 50%, 38% 38%);
		box-shadow:
			0 0 10px 3px #fff,
			0 0 18px 6px currentColor,
			0 0 32px 10px currentColor;
		opacity: 0;
		animation: spark-pop 0.75s ease-out infinite;
		animation-delay: var(--d);
	}

	.sparks.hot-burst .core {
		width: 18px;
		height: 18px;
		animation-duration: 0.48s;
	}

	.sparks.hot-burst .bolt,
	.sparks.hot-burst .pop {
		animation-duration: 0.52s;
	}

	.sparks.pos-lo,
	.sparks.pos-mid {
		color: #65c8ff;
	}

	.sparks.pos-hi {
		color: #7cffb2;
	}

	.sparks.pos-max {
		color: #ffe083;
	}

	.sparks.neg-lo,
	.sparks.neg-mid {
		color: #ff8a5b;
	}

	.sparks.neg-hi {
		color: #ff6b6b;
	}

	img {
		width: clamp(26px, 2.6vw, 40px);
		height: clamp(26px, 2.6vw, 40px);
		margin-top: 0.1rem;
		opacity: 0.95;
	}

	.final img {
		filter: sepia(0.45) saturate(1.4) hue-rotate(-8deg) brightness(1.15);
	}

	.role {
		color: #9ecff0;
		font-size: clamp(11px, 1.05vw, 16px);
		font-weight: 800;
		letter-spacing: 0.14em;
	}

	.final .role {
		color: #ffc940;
		max-width: none;
		font-size: clamp(11px, 1.05vw, 15px);
		letter-spacing: 0.08em;
		line-height: 1.15;
		text-align: left;
		text-transform: uppercase;
	}

	.window,
	.result {
		position: relative;
		z-index: 2;
		width: 100%;
	}

	.value {
		position: relative;
		grid-row: 3;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.28rem;
		width: 100%;
		min-height: 0;
		z-index: 2;
	}

	.window {
		height: calc(var(--tick) * var(--visible-ticks));
		align-self: stretch;
		overflow: hidden;
		-webkit-mask-image: none;
		mask-image: none;
	}

	.cell.spinning .window:not(.horiz),
	.cell.stopping .window:not(.horiz) {
		-webkit-mask-image: linear-gradient(transparent, #000 14%, #000 86%, transparent);
		mask-image: linear-gradient(transparent, #000 14%, #000 86%, transparent);
	}

	.cell.revealed .window:not(.horiz) {
		overflow: visible;
		-webkit-mask-image: linear-gradient(transparent, #000 28%, #000 72%, transparent);
		mask-image: linear-gradient(transparent, #000 28%, #000 72%, transparent);
	}

	.cell.final.revealed .window.horiz {
		overflow: hidden;
		-webkit-mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
		mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
	}

	.cell.revealed .tick {
		opacity: 0.28;
		transition: opacity 160ms ease;
	}

	.cell.final.revealed .tick {
		opacity: 0.42;
	}

	.cell.revealed .tick.landed {
		z-index: 2;
		opacity: 1;
		transform: scale(1.62);
		font-size: clamp(22px, 2.2vw, 36px);
		text-shadow: 0 2px 14px rgba(3, 14, 29, 0.88);
	}

	.cell.final.revealed .tick.landed {
		transform: scale(1.18);
		color: #ffe083;
	}

	.tape {
		display: flex;
		flex-direction: column;
		will-change: transform;
	}

	.tick {
		position: relative;
		display: grid;
		place-items: center;
		height: var(--tick);
		color: #d7e7f4;
		font-size: clamp(18px, 2.05vw, 34px);
		font-weight: 800;
		letter-spacing: 0.02em;
		line-height: 1;
		transform-origin: center center;
		text-shadow: 0 1px 10px rgba(3, 14, 29, 0.82);
	}

	.sad {
		position: absolute;
		left: 50%;
		top: 50%;
		z-index: 9;
		font-size: 1.35em;
		line-height: 1;
		filter: drop-shadow(0 0 8px rgba(255, 80, 80, 0.85));
		transform: translate(70%, -10%);
		pointer-events: none;
	}

	.result .sad {
		transform: translate(80%, -40%);
	}

	.tick.neg-hi,
	.result.neg-hi {
		color: #ff6b6b;
	}

	.tick.neg-mid,
	.result.neg-mid {
		color: #ff8a5b;
	}

	.tick.neg-lo,
	.result.neg-lo {
		color: #ffc940;
	}

	.tick.neutral,
	.result.neutral {
		color: #c5d6e4;
	}

	.tick.pos-lo,
	.result.pos-lo {
		color: #9ecff0;
	}

	.tick.pos-mid,
	.result.pos-mid {
		color: #65c8ff;
	}

	.tick.pos-hi,
	.result.pos-hi {
		color: #7cffb2;
	}

	.tick.pos-max,
	.result.pos-max {
		color: #ffe083;
	}

	.final .tick {
		color: #ffe083;
	}

	.result {
		align-self: center;
		margin: 0;
		padding: 0.12em 0.1em 0.08em;
		color: #f4faff;
		font-size: clamp(42px, 3.2vw, 64px);
		font-weight: 800;
		letter-spacing: -0.03em;
		line-height: 0.98;
		text-align: center;
		white-space: nowrap;
		opacity: 1;
		filter: none;
		text-shadow: 0 2px 14px rgba(3, 14, 29, 0.88);
		-webkit-font-smoothing: antialiased;
	}

	.final .result {
		color: #ffe083;
		font-size: clamp(52px, 4vw, 78px);
		text-shadow: 0 2px 16px rgba(40, 24, 0, 0.72);
	}

	.result.xl {
		font-size: clamp(40px, 3vw, 58px);
	}

	.cell.neg-hi {
		border-color: #ff6b6b;
	}

	.cell.neg-mid {
		border-color: #ff8a5b;
	}

	.cell.pos-hi {
		border-color: #7cffb2;
	}

	.cell.pos-max {
		border-color: #ffe083;
	}

	.cell.pulse-1 .result,
	.result.pulse-1 {
		animation: heat-pulse 1.15s ease-in-out infinite;
	}

	.cell.pulse-2 .result,
	.result.pulse-2 {
		animation: heat-pulse 0.85s ease-in-out infinite;
	}

	.cell.pulse-3 .result,
	.result.pulse-3 {
		animation: heat-pulse 0.58s ease-in-out infinite;
	}

	.final .result.xl {
		font-size: clamp(42px, 3.3vw, 62px);
	}

	.badge {
		position: relative;
		z-index: 1;
		min-height: 1.05rem;
		margin: 0;
		padding: 0 0.4rem;
		border-radius: 999px;
		color: #ffc940;
		font-size: clamp(12px, 1.05vw, 16px);
		font-weight: 800;
		letter-spacing: 0.08em;
		text-shadow: 0 1px 8px rgba(3, 14, 29, 0.7);
	}

	.cell.hot .badge {
		min-height: 2.15rem;
		margin-top: 0.15rem;
		padding: 0.18rem 0.85rem;
		color: #07182f;
		background: #ffc940;
		border: 2px solid #ffe083;
		font-size: clamp(28px, 2.8vw, 48px);
		font-weight: 900;
		letter-spacing: 0.04em;
		line-height: 1;
		text-shadow: none;
		box-shadow:
			0 0 18px rgba(255, 201, 64, 0.85),
			0 0 36px rgba(255, 201, 64, 0.35);
		animation: badge-pulse 0.72s ease-in-out infinite;
	}

	.final-badge {
		color: #c9a24d;
	}

	.badge.ghost {
		opacity: 0;
	}

	@keyframes spark-bolt {
		0% {
			transform: rotate(var(--a)) translateY(0) scaleY(0.2);
			opacity: 0;
		}
		8% {
			opacity: 1;
		}
		58% {
			transform: rotate(var(--a)) translateY(calc(-1 * var(--dist))) scaleY(1);
			opacity: 1;
		}
		100% {
			transform: rotate(var(--a)) translateY(calc(-1.4 * var(--dist))) scaleY(0.25);
			opacity: 0;
		}
	}

	@keyframes spark-pop {
		0% {
			transform: translate(-50%, -50%) translate(var(--x), var(--y)) scale(0.15);
			opacity: 0;
		}
		16% {
			opacity: 1;
			transform: translate(-50%, -50%) translate(var(--x), var(--y)) scale(var(--s));
		}
		100% {
			opacity: 0;
			transform: translate(-50%, -50%) translate(var(--x), var(--y)) scale(0.35);
		}
	}

	@keyframes spark-core {
		0%,
		100% {
			opacity: 0.2;
			transform: translate(-50%, -50%) scale(0.7);
		}
		40% {
			opacity: 0.7;
			transform: translate(-50%, -50%) scale(1.15);
		}
	}

	@keyframes heat-pulse {
		0%,
		100% {
			transform: scale(1);
			filter: brightness(1);
		}
		50% {
			transform: scale(var(--heat-scale, 1.08));
			filter: brightness(1.18);
		}
	}

	@keyframes badge-pulse {
		0%,
		100% {
			transform: scale(1);
			box-shadow:
				0 0 14px rgba(255, 201, 64, 0.7),
				0 0 28px rgba(255, 201, 64, 0.28);
		}
		50% {
			transform: scale(1.12);
			box-shadow:
				0 0 26px rgba(255, 224, 131, 1),
				0 0 48px rgba(255, 201, 64, 0.55);
		}
	}

	.pulse-1 {
		--heat-scale: 1.05;
	}

	.pulse-2 {
		--heat-scale: 1.1;
	}

	.pulse-3 {
		--heat-scale: 1.16;
	}

	@keyframes reel-roll {
		from {
			transform: translateY(0);
		}
		to {
			transform: translateY(calc(var(--tick) * -1));
		}
	}

	@keyframes stop-hit {
		0% {
			transform: translateY(7px) scale(0.96);
		}
		55% {
			transform: translateY(-3px) scale(1.04);
		}
		100% {
			transform: translateY(0) scale(1);
		}
	}

	@keyframes slot6-hit {
		0% {
			transform: translateY(8px) scale(0.94);
			box-shadow: 0 0 0 0 rgba(255, 201, 64, 0.5);
		}
		50% {
			transform: translateY(-4px) scale(1.06);
			box-shadow: 0 0 22px 2px rgba(255, 201, 64, 0.42);
		}
		100% {
			transform: translateY(0) scale(1);
		}
	}

	@keyframes term-pop {
		0% {
			transform: scale(0.72);
			opacity: 0.2;
		}
		70% {
			transform: scale(1.08);
		}
		100% {
			transform: scale(1);
			opacity: 1;
		}
	}

	@keyframes unlock-flash {
		0% {
			opacity: 1;
			filter: brightness(1);
		}
		40% {
			opacity: 1;
			filter: brightness(1.8);
			background: linear-gradient(90deg, rgba(255, 201, 64, 0.35), rgba(18, 16, 8, 0.55));
		}
		100% {
			opacity: 0;
			filter: brightness(2);
		}
	}

	@keyframes flash {
		from {
			opacity: 1;
		}
		to {
			opacity: 0;
		}
	}

	@keyframes below-pulse {
		0%,
		100% {
			opacity: 0.72;
			transform: scale(1);
		}
		50% {
			opacity: 1;
			transform: scale(1.04);
		}
	}

	@media (max-width: 720px) {
		.strip {
			top: 11vh;
			width: min(96vw, 720px);
			gap: 8px;
			--visible-ticks: 3;
		}

		.meter {
			width: min(94vw, 520px);
			min-height: 34px;
			font-size: 10px;
			gap: 6px;
			padding: 4px 10px;
		}

		.meter strong {
			font-size: 16px;
		}

		.meter .base-chip {
			padding: 1px 6px;
			font-size: 10px;
		}

		.flight-board,
		.lanes,
		.cell.lane {
			min-height: 220px;
		}

		.weather-lottery {
			gap: 8px;
			padding: 8px 8px 10px;
		}

		.weather-grid {
			gap: 4px;
		}

		.weather-chip {
			min-height: 58px;
			padding: 4px 2px 6px;
		}

		.weather-chip img {
			width: 20px;
			height: 20px;
		}

		.weather-copy strong {
			font-size: 16px;
		}

		.cell {
			padding: 8px 2px 6px;
		}

		.final-rail {
			min-height: 92px;
			padding: 6px 8px;
			gap: 4px 8px;
		}

		.base-rail {
			min-height: 122px;
			padding: 8px 10px;
			gap: 4px 10px;
		}

		.base-kicker {
			font-size: 10px;
		}

		.eq strong {
			font-size: 13px;
		}

		.eq .op {
			font-size: 16px;
		}

		.base-x {
			font-size: 28px;
		}

		.base-formula,
		.base-map {
			font-size: 8px;
		}

		img {
			width: 22px;
			height: 22px;
		}

		.role {
			font-size: 9px;
		}

		.tick {
			font-size: 16px;
		}

		.final .tick {
			font-size: 18px;
		}

		.result {
			font-size: clamp(20px, 5.4vw, 32px);
		}

		.final .result {
			font-size: clamp(22px, 6vw, 36px);
		}

		.result.xl {
			font-size: clamp(16px, 4.4vw, 26px);
		}

		.badge {
			font-size: 10px;
		}

		.cell.hot .badge {
			font-size: clamp(22px, 7vw, 36px);
			min-height: 1.7rem;
		}
	}

	@media (max-width: 420px) {
		.strip {
			top: 10vh;
			gap: 6px;
		}

		.flight-board,
		.lanes,
		.cell.lane {
			min-height: 196px;
		}

		.final-rail {
			min-height: 84px;
		}

		.base-rail {
			min-height: 132px;
			grid-template-columns: 1fr;
			grid-template-rows: auto auto auto auto auto;
		}

		.base-kicker,
		.eq,
		.base-formula,
		.base-map,
		.base-x {
			grid-column: 1;
			grid-row: auto;
		}

		.base-x {
			justify-self: center;
			font-size: 32px;
		}

		.tick {
			font-size: 14px;
		}

		.result {
			font-size: 18px;
		}

		.final .result {
			font-size: 20px;
		}

		.result.xl {
			font-size: 15px;
		}
	}
</style>
