<script lang="ts">
	import { onDestroy } from 'svelte';
	import { stateBet, stateUi } from 'state-shared';
	import { getSkyJumpHudLayout } from 'components-ui-pixi';
	import { waitForTimeout } from 'utils-shared/wait';

	import { getContext } from '../../game/context';
	import { loungeShown, loungeSlotFrameSrc } from '../../game/midnightLoungeTheme';
	import { V2_PAYLINES, V2_PAYLINE_IDS, V2_SCATTER_ID } from '../../game/skyjump_v2/config';
	import { bonusHud, bonusShowsTargets, tierLabel } from '../../game/skyjump_v2/bonusHud.svelte';
	import { V2_PLACEHOLDERS, reelFillerBand, v2Placeholder } from '../../game/skyjump_v2/placeholders';
	import {
		buildReelStrip,
		reelOffsetPx,
		reelTravelMs,
		reelTravelPace,
		VISIBLE_ROWS,
		type ReelPace,
	} from '../../game/skyjump_v2/reelStrip';
	import {
		markV2SymbolArtMissing,
		markV2SymbolArtReady,
		v2SymbolVisual,
	} from '../../game/skyjump_v2/symbolAssetRegistry';
	import {
		v2FxAssetUrl,
		v2ModeTitleUrl,
		v2TierEmblemUrl,
		v2UiAssetUrl,
		v2WinSceneOverlayUrl,
	} from '../../game/skyjump_v2/uiAssetRegistry';
	import {
		classifyV2WinCelebration,
		V2_WIN_BLUR_FADE_MS,
		type V2WinCelebrationTier,
	} from '../../game/skyjump_v2/winPresentation';
	import { reactToWin } from '../../game/loungeCharacters/winReaction';
	import { statusLabel as playerLabel, statusSub as playerSub } from '../../game/skyjump_v2/statusText';
	import { V2_PAYLINE_FX, V2_SLOT_BOARD_FRAME } from '../../game/skyjump_v2/presentationLayout';
	import type { V2BannerKind } from '../../game/skyjump_v2/presentationLayout';
	import { playV2AudioHook } from '../../game/skyjump_v2/audio';
	import type { SkyJumpMysteryResultType } from '../../game/typesBookEvent';
	import type { V2LineWin } from '../../game/skyjump_v2/types';
	import SkyJumpV2WinCelebration from './SkyJumpV2WinCelebration.svelte';
	import SkyJumpV2StatusPlate from './SkyJumpV2StatusPlate.svelte';
	import SkyJumpV2ModeBadge from './SkyJumpV2ModeBadge.svelte';
	import SkyJumpV2TitleBanner from './SkyJumpV2TitleBanner.svelte';

	const context = getContext();
	const emptyBoard = () => Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => 'L3'));

	let board = $state(emptyBoard());
	let spinning = $state([false, false, false, false, false]);
	let reelPace = $state<ReelPace[]>(['', '', '', '', '']);
	let landMs = $state(160);
	/** Long presentation strips. Null uses the settled board column. */
	let spinIds = $state<(string[] | null)[]>([null, null, null, null, null]);
	let spinOffset = $state([0, 0, 0, 0, 0]);
	let reelSpinToken = 0;
	let wins = $state<V2LineWin[]>([]);
	let highlightKeys = $state<Set<string>>(new Set());
	let pathPoints = $state<Array<{ x: number; y: number }>>([]);
	/** Cells popped so far by the running payline sequence (left -> right, top -> bottom). */
	let poppedKeys = $state<Set<string>>(new Set());
	let lineSeqActive = $state(false);
	let pathDraw = $state(1);
	let pathOpacity = $state(1);
	let sparkOn = $state(false);
	let sparkPos = $state<{ x: number; y: number } | null>(null);
	let pathLen = $state(0);
	let winLabel = $state('');
	let winSub = $state('');
	let showWin = $state(false);
	let inspectId = $state(0);
	let DevSource = $state<null | typeof import('./SkyJumpV2DevSource.svelte').default>(null);
	let AudioQa = $state<null | typeof import('./SkyJumpV2AudioQa.svelte').default>(null);
	let CharacterQa = $state<null | typeof import('./SkyJumpV2CharacterQa.svelte').default>(null);
	let scatterCount = $state(0);
	let scatterPerfect = $state(false);
	let tokenFaces = $state<Record<string, number>>({});
	let tokenEffective = $state<Record<string, number>>({});
	let thermalMults = $state<Record<string, number>>({});
	let featureWinX = $state(0);
	let preservedKeys = $state<Set<string>>(new Set());
	let rejumping = $state(false);
	let worldRecordActive = $state(false);
	let worldRecordPos = $state<{ reel: number; row: number } | null>(null);
	let worldRecordWinX = $state(0);
	let artReady = $state<Record<string, boolean>>({});
	let artBroken = $state<Record<string, boolean>>({});
	let celebrationShow = $state(false);
	let celebrationTier = $state<V2WinCelebrationTier>('none');
	let celebrationAmount = $state(0);
	let celebrationCatchUp = $state(false);
	let celebrationWorldRecordOverlay = $state(false);
	let pathGlintOn = $state(false);
	let pathGlintPos = $state<{ x: number; y: number } | null>(null);
	let titleBannerSrc = $state<string | null>(null);
	let titleBannerShow = $state(false);
	let titleBannerKind = $state<V2BannerKind>('mode');
	const paylineSparkSize = V2_PAYLINE_FX.sparkPx;
	const paylineGlintSize = V2_PAYLINE_FX.endGlintPx;

	const tierEmblemSrc = $derived(v2TierEmblemUrl(bonusHud.tier));
	const wrOverlaySrc = v2WinSceneOverlayUrl('worldRecord') ?? v2UiAssetUrl('overlayWorldRecord');
	const paylineSparkSrc = v2FxAssetUrl('paylineSparkHead');
	const paylineGlintSrc = v2FxAssetUrl('paylineEndGlint');
	const modeBadgeLabel = $derived(tierLabel(bonusHud.tier));

	const isDevInspector = $derived(
		Boolean(import.meta.env.DEV && stateUi.config.localDemo && !stateUi.config.liveMath),
	);

	const chargeBoxes = (charge: number) => [charge >= 1, false] as const;

	let winFocusTimer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		if (typeof document === 'undefined') return;
		const viewport = document.querySelector('.skyjump-viewport');
		if (!(viewport instanceof HTMLElement)) return;
		// Any celebration tier lifts the lounge plate and blurs the HUD. `winPlate` follows the
		// celebration exactly (CSS fades the blur and the plate in and out); `winFocus` outlives
		// it by the fade time so the characters and bar stay in front while the plate fades out.
		const active = celebrationShow && celebrationTier !== 'none';
		clearTimeout(winFocusTimer);
		if (active) {
			viewport.dataset.winPlate = celebrationTier;
			viewport.dataset.winFocus = '1';
		} else {
			delete viewport.dataset.winPlate;
			winFocusTimer = setTimeout(() => {
				delete viewport.dataset.winFocus;
			}, V2_WIN_BLUR_FADE_MS + 100);
		}
	});

	$effect(
		() => () => {
			clearTimeout(winFocusTimer);
			const viewport = document.querySelector<HTMLElement>('.skyjump-viewport');
			if (!viewport) return;
			delete viewport.dataset.winPlate;
			delete viewport.dataset.winFocus;
		},
	);

	$effect(() => {
		if (!import.meta.env.DEV || !stateUi.config.localDemo || stateUi.config.liveMath) return;
		let cancelled = false;
		void import('./SkyJumpV2DevSource.svelte').then((mod) => {
			if (!cancelled) DevSource = mod.default;
		});
		void import('./SkyJumpV2AudioQa.svelte').then((mod) => {
			if (!cancelled) AudioQa = mod.default;
		});
		void import('./SkyJumpV2CharacterQa.svelte').then((mod) => {
			if (!cancelled) CharacterQa = mod.default;
		});
		return () => {
			cancelled = true;
		};
	});
	const main = $derived(context.stateLayoutDerived.mainLayoutStandard());
	const canvas = $derived(context.stateLayoutDerived.canvasSizes());
	const hud = $derived(getSkyJumpHudLayout(main));
	const scale = $derived(main.scale);
	const originX = $derived(main.x - (main.width * scale) / 2);
	const originY = $derived(main.y - (main.height * scale) / 2);
	/** BetUI art top — summary may intentionally overlap the crest by a few px. */
	const frameTopPx = $derived(originY + hud.frame.top * scale);
	const playW = $derived(main.width * scale);
	/**
	 * Explicit 1280×720 CSS pixel contracts (scaled for other widths).
	 * Do not replace with vague grow factors.
	 */
	const px = (n: number) => n * (playW / 1280);
	/** Keep grid top near current Y; free room for +7% board scale. */
	const GRID_TOP_Y = 22;
	/**
	 * Drop the whole slot board (frame + grid) by this many CSS px @1280.
	 * Summary gap is reduced by the same amount so READY stays near its prior Y
	 * and visually meets the frame bottom.
	 */
	const BOARD_NUDGE_DOWN = 26;
	/**
	 * Shift frame + 5×5 together so the frame's bottom center spike lines up
	 * with the summary plate's center spike. Summary and BetUI stay put.
	 */
	const BOARD_NUDGE_X = 2.25;
	/** Nominal gap before nudge compensation (effective gap = this − nudge). */
	const GRID_SUMMARY_GAP = 10;
	/** Summary tile (now ~25 % narrower, ~16 % lower) and its layout box. */
	const SUMMARY_PLATE_H = 65;
	const SUMMARY_H = 71;
	/** Lowest y (1280x720 px) the summary tile may reach: ~12 px above the SPIN button (top ~593). */
	/** The tile sits this far below the grid, i.e. centred between the grid and SPIN. */
	const SUMMARY_GRID_GAP = 12;
	const SUMMARY_BOTTOM_LIMIT = 581;
	/** Visible top of the frame art (alpha bounds) as a fraction of the art height. */
	const FRAME_ART_VISIBLE_TOP = 0.0244;
	/**
	 * Summary extends this many px into the BetUI crest (intentional meet).
	 * Extra overlap frees budget for BOARD_SCALE without crowding READY.
	 */
	const SUMMARY_BETUI_OVERLAP = 48;
	/** Controlled +7% slot enlarge vs prior 1.05 pass (still capped by avail box). */
	const BOARD_SCALE = 1.12;
	const statusSlot = GRID_SUMMARY_GAP + SUMMARY_H;
	/** Sizing pin — do not include BOARD_NUDGE_DOWN so scale stays unchanged. */
	const topPinned = $derived(originY + px(GRID_TOP_Y));
	const availW = $derived(Math.max(160, playW - px(20)));
	/**
	 * Height budget: the frame art starts at the top edge of the screen (its visible crest at
	 * y = 0) and the summary tile hangs under the grid. The board is as large as that allows.
	 */
	const FRAME_GRID_BOTTOM_RATIO =
		(V2_SLOT_BOARD_FRAME.holeBottom - FRAME_ART_VISIBLE_TOP) /
		(V2_SLOT_BOARD_FRAME.holeBottom - V2_SLOT_BOARD_FRAME.holeTop);
	const maxBoardH = $derived(
		(px(SUMMARY_BOTTOM_LIMIT) - px(SUMMARY_PLATE_H) - px(SUMMARY_GRID_GAP)) / FRAME_GRID_BOTTOM_RATIO,
	);
	const availH = $derived(Math.max(120, maxBoardH + framePadEstimate * 2 + 4));
	const FRAME_BORDER = 2;
	const framePadEstimate = $derived(Math.max(12, Math.min(15, Math.round(availW * 0.013))));
	const gap = $derived(Math.max(5, Math.min(10, Math.round(availW * 0.0095))));
	const framePad = $derived(Math.max(12, Math.min(15, Math.round(availW * 0.013))));
	const BOARD_ASPECT = 1.02;
	const maxInnerW = $derived(Math.max(100, availW - framePad * 2 - FRAME_BORDER * 2));
	const maxInnerH = $derived(Math.max(80, availH - framePad * 2 - FRAME_BORDER * 2));
	const fitCellW = $derived(Math.max(22, Math.floor((maxInnerW - gap * 4) / 5)));
	const fitCellH = $derived(Math.max(22, Math.floor((maxInnerH - gap * 4) / 5)));
	const baseCellH = $derived(Math.min(fitCellW, fitCellH));
	const cellH = $derived(Math.min(fitCellH, Math.max(22, Math.round(baseCellH * BOARD_SCALE))));
	const cellW = $derived(Math.min(fitCellW, Math.max(cellH, Math.round(cellH * BOARD_ASPECT))));
	const boardW = $derived(cellW * 5 + gap * 4);
	const boardH = $derived(cellH * 5 + gap * 4);
	/** Edge-to-edge symbol pitch. The old row gutter is inside the slot, not a grid line. */
	const symbolPitch = $derived(boardH / VISIBLE_ROWS);
	const surfaceW = $derived(boardW + framePad * 2 + FRAME_BORDER * 2);
	const surfaceH = $derived(boardH + framePad * 2 + FRAME_BORDER * 2);
	const slotFrameSrc = loungeSlotFrameSrc;
	/** Art frame sized so its transparent hole stays centered on the grid, then +10%. */
	const slotFrameW = $derived(
		(boardW / (V2_SLOT_BOARD_FRAME.holeRight - V2_SLOT_BOARD_FRAME.holeLeft)) *
			V2_SLOT_BOARD_FRAME.scale,
	);
	const slotFrameH = $derived(
		(boardH / (V2_SLOT_BOARD_FRAME.holeBottom - V2_SLOT_BOARD_FRAME.holeTop)) *
			V2_SLOT_BOARD_FRAME.scale,
	);
	const slotFrameLeft = $derived(
		framePad +
			boardW / 2 -
			slotFrameW * ((V2_SLOT_BOARD_FRAME.holeLeft + V2_SLOT_BOARD_FRAME.holeRight) / 2),
	);
	const slotFrameTop = $derived(
		framePad +
			boardH / 2 -
			slotFrameH * ((V2_SLOT_BOARD_FRAME.holeTop + V2_SLOT_BOARD_FRAME.holeBottom) / 2),
	);
	/** True viewport center X = 640 at 1280. */
	const left = $derived(originX + (playW - surfaceW) / 2);
	/**
	 * Visual top = sizing pin + nudge. Clamp uses compensated summary gap so
	 * READY Y stays stable while the board sits lower.
	 */
	$effect(() => {
		if (typeof document === 'undefined') return;
		const root = document.querySelector<HTMLElement>('.skyjump-viewport');
		if (!root) return;
		const playH = main.height * scale;
		root.style.setProperty('--play-left', `${originX}px`);
		root.style.setProperty('--play-top', `${originY}px`);
		root.style.setProperty('--play-width', `${playW}px`);
		root.style.setProperty('--play-height', `${playH}px`);
		root.style.setProperty('--slot-top', `${top}px`);
		root.style.setProperty('--slot-height', `${surfaceH}px`);
		root.style.setProperty('--slot-right', `${left + px(BOARD_NUDGE_X) + surfaceW}px`);
	});
	/** Frame art's visible crest sits exactly on the top edge of the play area. */
	const top = $derived(originY - slotFrameTop - FRAME_ART_VISIBLE_TOP * slotFrameH);
	const statusLabel = $derived(winLabel || (showWin ? '—' : 'READY'));
	/** Effective gap under grid (negative = intentional frame/READY meet). */
	const summaryGapPx = $derived(-(framePad + FRAME_BORDER) + px(SUMMARY_GRID_GAP));

	const cellKey = (reel: number, row: number) => `${reel}:${row}`;

	const mysterySymbolId = (resultType: SkyJumpMysteryResultType) => {
		if (resultType === 'FLIGHT_TOKEN') return null;
		if (resultType === 'THERMAL_LIFT') return 'THERMAL';
		if (resultType === 'GATE_UPGRADE') return 'GATE';
		if (resultType === 'JUDGE') return 'JUDGE';
		if (resultType === 'REJUMP') return 'REJUMP';
		if (resultType === 'WIND_KEY') return 'WIND';
		return 'HEAD_JUDGE';
	};

	const setTokenValue = (reel: number, row: number, face: number, effective?: number) => {
		const key = cellKey(reel, row);
		tokenFaces = { ...tokenFaces, [key]: face };
		if (effective !== undefined && Math.abs(effective - face) > 1e-9) {
			tokenEffective = { ...tokenEffective, [key]: effective };
		} else {
			const next = { ...tokenEffective };
			delete next[key];
			tokenEffective = next;
		}
	};

	const dimmed = (reel: number, row: number) => {
		if (preservedKeys.size > 0) return false;
		if (highlightKeys.size === 0) return false;
		return !highlightKeys.has(cellKey(reel, row));
	};

	const inspectCells = $derived.by(() => {
		if (!inspectId) return new Set<string>();
		const rows = V2_PAYLINES[inspectId];
		if (!rows) return new Set<string>();
		return new Set(rows.map((row, reel) => cellKey(reel, row)));
	});

	onDestroy(() => {
		reelSpinToken += 1;
	});

	const setPath = (positions: Array<{ reel: number; row: number }>) => {
		pathPoints = positions.map((pos) => ({
			x: pos.reel * (cellW + gap) + cellW / 2,
			y: pos.row * symbolPitch + symbolPitch / 2,
		}));
		let len = 0;
		for (let i = 1; i < pathPoints.length; i += 1) {
			const dx = pathPoints[i].x - pathPoints[i - 1].x;
			const dy = pathPoints[i].y - pathPoints[i - 1].y;
			len += Math.hypot(dx, dy);
		}
		pathLen = len;
	};

	const pathD = $derived(
		pathPoints.length > 1 ? `M ${pathPoints.map((p) => `${p.x},${p.y}`).join(' L ')}` : '',
	);

	const pointAlong = (t: number) => {
		if (pathPoints.length === 0) return null;
		if (pathPoints.length === 1 || pathLen <= 0) return pathPoints[0];
		const target = Math.max(0, Math.min(1, t)) * pathLen;
		let walked = 0;
		for (let i = 1; i < pathPoints.length; i += 1) {
			const a = pathPoints[i - 1];
			const b = pathPoints[i];
			const seg = Math.hypot(b.x - a.x, b.y - a.y);
			if (walked + seg >= target || i === pathPoints.length - 1) {
				const u = seg <= 0 ? 1 : (target - walked) / seg;
				return { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u };
			}
			walked += seg;
		}
		return pathPoints[pathPoints.length - 1];
	};

	const prefersReducedMotion = () =>
		typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

	/** Resolves when the big/mega overlay has dismissed, so the book can return to the board. */
	let releaseCelebration: (() => void) | null = null;

	const settleCelebrationWait = () => {
		const release = releaseCelebration;
		releaseCelebration = null;
		release?.();
	};

	const clearCelebration = () => {
		celebrationShow = false;
		celebrationTier = 'none';
		celebrationAmount = 0;
		celebrationCatchUp = false;
		celebrationWorldRecordOverlay = false;
		settleCelebrationWait();
	};

	const waitForCelebration = () => {
		if (!celebrationShow) return Promise.resolve();
		return new Promise<void>((resolve) => {
			releaseCelebration = resolve;
		});
	};

	const openCelebration = (opts: {
		totalWinX: number;
		amount: number;
		worldRecord?: boolean;
		capHit?: boolean;
		catchUp?: boolean;
		worldRecordOverlay?: boolean;
	}) => {
		const tier = classifyV2WinCelebration({
			totalWinX: opts.totalWinX,
			worldRecord: opts.worldRecord,
			capHit: opts.capHit,
		});
		const shouldShow =
			tier !== 'none' || Boolean(opts.worldRecord) || (Boolean(opts.capHit) && opts.totalWinX > 0);
		if (!shouldShow) {
			clearCelebration();
			return;
		}
		celebrationTier = tier === 'none' && opts.capHit ? 'max' : tier;
		celebrationAmount = opts.amount;
		celebrationCatchUp = Boolean(opts.catchUp);
		celebrationWorldRecordOverlay = Boolean(opts.worldRecordOverlay);
		celebrationShow = celebrationTier !== 'none';
	};

	/**
	 * Payline win presentation: the winning symbols pop one after another, left to right and
	 * top to bottom, each with a warm backlight (no line is drawn). They hold, then release.
	 */
	const animateLinePop = async (
		win: V2LineWin,
		timings: { lineDrawMs: number; lineHoldMs: number; lineFadeMs: number },
		catchUp: boolean,
	) => {
		const ordered = [...win.positions].sort((a, b) => a.reel - b.reel || a.row - b.row);
		const keys = ordered.map((pos) => cellKey(pos.reel, pos.row));
		lineSeqActive = true;
		if (catchUp || prefersReducedMotion() || timings.lineDrawMs <= 0) {
			poppedKeys = new Set(keys);
			if (!catchUp && timings.lineHoldMs > 0) await waitForTimeout(timings.lineHoldMs);
			return;
		}
		playV2AudioHook('PAYLINE_DRAW', { catchUp: false });
		poppedKeys = new Set();
		const total = stateBet.isTurbo ? Math.max(120, timings.lineDrawMs) : Math.max(560, timings.lineDrawMs);
		const step = Math.max(24, Math.round(total / Math.max(1, keys.length)));
		for (const key of keys) {
			poppedKeys = new Set([...poppedKeys, key]);
			await waitForTimeout(step);
		}
		playV2AudioHook('PAYLINE_COMPLETE', { catchUp: false });
		await waitForTimeout(timings.lineHoldMs + (stateBet.isTurbo ? 0 : 140));
		poppedKeys = new Set();
		lineSeqActive = false;
		if (timings.lineFadeMs > 0) await waitForTimeout(timings.lineFadeMs);
	};

	const clearWin = () => {
		wins = [];
		poppedKeys = new Set();
		lineSeqActive = false;
		highlightKeys = new Set();
		pathPoints = [];
		pathDraw = 1;
		pathOpacity = 1;
		sparkOn = false;
		sparkPos = null;
		pathLen = 0;
		pathGlintOn = false;
		pathGlintPos = null;
		winLabel = '';
		winSub = '';
		showWin = false;
		clearCelebration();
	};

	const highlightWin = (win: V2LineWin | null, all: V2LineWin[]) => {
		if (!win) {
			const keys = new Set<string>();
			for (const row of all) {
				for (const pos of row.positions) keys.add(cellKey(pos.reel, pos.row));
			}
			highlightKeys = keys;
			pathPoints = [];
			sparkOn = false;
			sparkPos = null;
			return;
		}
		highlightKeys = new Set(win.positions.map((pos) => cellKey(pos.reel, pos.row)));
		pathPoints = [];
	};

	context.eventEmitter.subscribeOnMount({
		skyjumpV2Reset: () => {
			reelSpinToken += 1;
			// Roses are only the board before the first reveal. Later spins roll
			// the symbols already on screen; wiping them here flashed a rose grid.
			spinning = [false, false, false, false, false];
			reelPace = ['', '', '', '', ''];
			spinIds = [null, null, null, null, null];
			spinOffset = [0, 0, 0, 0, 0];
			scatterCount = 0;
			scatterPerfect = false;
			tokenFaces = {};
			tokenEffective = {};
			thermalMults = {};
			featureWinX = 0;
			preservedKeys = new Set();
			rejumping = false;
			worldRecordActive = false;
			worldRecordPos = null;
			worldRecordWinX = 0;
			clearWin();
		},
		skyjumpV2BoardReveal: async ({ board: next, timings, catchUp }) => {
			clearWin();
			tokenFaces = {};
			tokenEffective = {};
			thermalMults = {};
			featureWinX = 0;
			preservedKeys = new Set();
			rejumping = false;
			worldRecordActive = false;
			worldRecordPos = null;
			worldRecordWinX = 0;
			if (catchUp || timings.reelTravelMs <= 0) {
				board = next.map((col) => [...col]);
				spinning = [false, false, false, false, false];
				reelPace = ['', '', '', '', ''];
				spinIds = [null, null, null, null, null];
				spinOffset = [0, 0, 0, 0, 0];
				return;
			}
			const token = ++reelSpinToken;
			const reduced = prefersReducedMotion();
			const startStagger = reduced ? 40 : timings.reelStartStaggerMs;
			const stopStagger = reduced ? 30 : timings.reelStopStaggerMs;
			const baseTravel = reduced ? Math.min(280, timings.reelTravelMs) : timings.reelTravelMs;
			const settleMs = reduced ? 0 : timings.reelSettleMs;
			landMs = settleMs;
			const travelCells = reduced ? VISIBLE_ROWS : Math.max(VISIBLE_ROWS, timings.reelTravelSlots);
			const pitch = symbolPitch;
			const overshoot = reduced || settleMs === 0 ? 0 : Math.min(5, pitch * 0.045);
			const previous = board.map((col) => [...col]);
			const result = next.map((col) => [...col]);
			const started = performance.now();
			const landed = [false, false, false, false, false];
			spinning = [false, false, false, false, false];
			reelPace = ['', '', '', '', ''];
			spinIds = [null, null, null, null, null];
			spinOffset = [0, 0, 0, 0, 0];

			while (landed.some((done) => !done)) {
				if (token !== reelSpinToken) return;
				const now = await new Promise<number>((resolve) => {
					requestAnimationFrame(resolve);
				});
				if (token !== reelSpinToken) return;
				const elapsed = now - started;
				for (let reel = 0; reel < 5; reel += 1) {
					if (landed[reel]) continue;
					const travelMs = reelTravelMs(baseTravel, reel, startStagger, stopStagger);
					const startAt = reel * startStagger;
					if (elapsed < startAt) continue;
					const phaseElapsed = elapsed - startAt;
					if (!spinning[reel]) {
						spinning[reel] = true;
						reelPace[reel] = 'soft';
						spinIds[reel] = buildReelStrip({
							reel,
							previous: previous[reel],
							result: result[reel],
							travelCells,
							band: reelFillerBand(bonusHud.active ? bonusHud.tier : 'BASE'),
						});
					}
					const offset = reelOffsetPx({
						elapsedMs: phaseElapsed,
						travelMs,
						settleMs,
						travelCells,
						pitch,
						overshootPx: overshoot,
					});
					if (offset === 'done') {
						const cols = board.map((col) => [...col]);
						cols[reel] = [...result[reel]];
						board = cols;
						spinning[reel] = false;
						reelPace[reel] = '';
						spinIds[reel] = null;
						spinOffset[reel] = 0;
						landed[reel] = true;
						if (result[reel]?.some((id) => id === V2_SCATTER_ID)) {
							playV2AudioHook('SCATTER_LAND', { catchUp: false });
						}
					} else {
						spinOffset[reel] = offset;
						const nextPace = phaseElapsed >= travelMs ? 'land' : reelTravelPace(phaseElapsed, travelMs);
						if (reelPace[reel] !== nextPace) reelPace[reel] = nextPace;
					}
				}
			}
			if (token !== reelSpinToken) return;
			board = result.map((col) => [...col]);
			spinning = [false, false, false, false, false];
			reelPace = ['', '', '', '', ''];
			spinIds = [null, null, null, null, null];
			spinOffset = [0, 0, 0, 0, 0];
		},
		skyjumpV2LineWins: async ({ wins: nextWins, lineWinX, timings, catchUp }) => {
			wins = nextWins;
			if (nextWins.length === 0) {
				showWin = true;
				winLabel = 'NO WIN';
				winSub = '0.0x';
				highlightKeys = new Set();
				pathPoints = [];
				// Short banner only — do not stall next BET for ~1.5s after reels.
				if (!catchUp && timings.winHoldMs > 0) await waitForTimeout(timings.winHoldMs);
				return;
			}
			// Show summary under the board immediately, then draw lines (no pre-draw stall).
			showWin = true;
			winLabel = `${nextWins.length} LINE${nextWins.length > 1 ? 'S' : ''}`;
			winSub = `${lineWinX.toFixed(1)}x`;
			if (catchUp) {
				highlightWin(null, nextWins);
				return;
			}
			const cycle = async (win: V2LineWin) => {
				highlightWin(win, nextWins);
				winLabel = `${win.symbolId} ×${win.matchCount}`;
				winSub = `${win.payoutX.toFixed(1)}x · L${win.paylineId}`;
				await animateLinePop(win, timings, false);
			};
			if (nextWins.length > 1) {
				for (const win of nextWins) {
					await cycle(win);
				}
				highlightWin(null, nextWins);
				pathDraw = 1;
				pathOpacity = 1;
				winLabel = `${nextWins.length} LINES`;
				winSub = `${lineWinX.toFixed(1)}x`;
			} else {
				await cycle(nextWins[0]);
				pathDraw = 1;
				pathOpacity = 1;
			}
		},
		skyjumpV2Result: async ({ totalLineWinX, totalFeatureWinX, totalWinX, capHit, catchUp }) => {
			showWin = true;
			featureWinX = totalFeatureWinX;
			if (wins.length === 0 && totalWinX <= 0) {
				winLabel = 'NO WIN';
				winSub = '0.0x';
				clearCelebration();
				return;
			}
			winLabel = capHit ? 'CAPPED TOTAL' : 'TOTAL WIN';
			if (totalFeatureWinX > 0) {
				winSub = `${totalLineWinX.toFixed(1)}x line + ${totalFeatureWinX.toFixed(1)}x feature = ${totalWinX.toFixed(1)}x`;
			} else {
				winSub = `${totalWinX.toFixed(1)}x`;
			}
			highlightWin(null, wins);
			openCelebration({
				totalWinX,
				amount: totalWinX,
				worldRecord: worldRecordActive,
				capHit: Boolean(capHit),
				catchUp,
				worldRecordOverlay: worldRecordActive,
			});
			// Win above the bet but below the celebration threshold: small-win reaction.
			// Celebrations drive the characters from their win counter instead.
			if (!celebrationShow && totalWinX > 1 && !catchUp) {
				reactToWin('mini', 'small', { turbo: stateBet.isTurbo });
			}
			if (celebrationShow && !catchUp) await waitForCelebration();
		},
		skyjumpV2ScatterResult: ({ count, perfectV }) => {
			scatterCount = count;
			scatterPerfect = perfectV;
		},
		skyjumpV2CoachSignal: async ({ coachPosition, selectedPositions, noOp, timings, catchUp }) => {
			const keys = new Set<string>([cellKey(coachPosition.reel, coachPosition.row)]);
			for (const pos of selectedPositions) keys.add(cellKey(pos.reel, pos.row));
			highlightKeys = keys;
			winLabel = noOp ? 'COACH' : 'COACH SIGNAL';
			winSub = noOp ? 'no eligible symbol' : `${selectedPositions.length} cells`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.coachHoldMs);
		},
		skyjumpV2MysteryTransform: async ({ positions, timings, catchUp }) => {
			const next = board.map((col) => [...col]);
			for (const pos of positions) next[pos.reel][pos.row] = 'Y';
			board = next;
			highlightKeys = new Set(positions.map((pos) => cellKey(pos.reel, pos.row)));
			winLabel = 'SNOWBURST';
			winSub = `${positions.length} mystery`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.mysteryHoldMs);
		},
		skyjumpV2MysteryResolve: async ({
			position,
			resultType,
			tokenId,
			tokenValueX,
			thermalMult,
			timings,
			catchUp,
		}) => {
			const key = cellKey(position.reel, position.row);
			const next = board.map((col) => [...col]);
			if (resultType === 'FLIGHT_TOKEN' && tokenId && tokenValueX !== undefined) {
				next[position.reel][position.row] = tokenId;
				setTokenValue(position.reel, position.row, tokenValueX);
				highlightKeys = new Set([key]);
				winLabel = tokenId;
				winSub = `${tokenValueX}x uncollected`;
			} else {
				const symbolId = mysterySymbolId(resultType) ?? 'Y';
				next[position.reel][position.row] = symbolId;
				if (resultType === 'THERMAL_LIFT' && thermalMult !== undefined) {
					thermalMults = { ...thermalMults, [key]: thermalMult };
				}
				highlightKeys = new Set([key]);
				winLabel = v2Placeholder(symbolId).label;
				winSub =
					resultType === 'THERMAL_LIFT' && thermalMult !== undefined
						? `×${thermalMult} neighbours`
						: 'mystery resolved';
			}
			board = next;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.mysteryHoldMs);
		},
		skyjumpV2GateUpgrade: async ({
			position,
			floorBefore,
			floorAfter,
			replacements,
			timings,
			catchUp,
		}) => {
			const next = board.map((col) => [...col]);
			for (const rep of replacements) {
				const tokenId = `T${rep.after.tier}`;
				next[rep.reel][rep.row] = tokenId;
				setTokenValue(rep.reel, rep.row, rep.after.face);
			}
			board = next;
			const keys = new Set(replacements.map((rep) => cellKey(rep.reel, rep.row)));
			keys.add(cellKey(position.reel, position.row));
			highlightKeys = keys;
			winLabel = 'GATE UPGRADE';
			winSub =
				replacements.length > 0
					? `floor T${floorBefore}→T${floorAfter} · ${replacements.length} tokens`
					: `floor T${floorBefore}→T${floorAfter} · no change`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.gateHoldMs);
		},
		skyjumpV2ThermalLift: async ({ position, thermalMult, affectedTokens, timings, catchUp }) => {
			for (const token of affectedTokens) {
				setTokenValue(token.reel, token.row, token.faceValueX, token.effectiveValueX);
			}
			const keys = new Set(affectedTokens.map((token) => cellKey(token.reel, token.row)));
			keys.add(cellKey(position.reel, position.row));
			highlightKeys = keys;
			winLabel = 'THERMAL';
			winSub =
				affectedTokens.length > 0
					? `×${thermalMult} · ${affectedTokens.length} tokens lifted`
					: `×${thermalMult} · no neighbours`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.thermalHoldMs);
		},
		skyjumpV2JudgeCollect: async ({
			position,
			passIndex,
			collectedX,
			tokenContributions,
			flightMultiplierX,
			timings,
			catchUp,
		}) => {
			const keys = new Set(tokenContributions.map((token) => cellKey(token.reel, token.row)));
			keys.add(cellKey(position.reel, position.row));
			highlightKeys = keys;
			featureWinX += collectedX;
			winLabel = 'JUDGE COLLECT';
			winSub =
				flightMultiplierX && flightMultiplierX !== 1
					? `pass ${passIndex} · +${collectedX.toFixed(1)}x · flight x${flightMultiplierX} · feature ${featureWinX.toFixed(1)}x`
					: `pass ${passIndex} · +${collectedX.toFixed(1)}x · feature ${featureWinX.toFixed(1)}x`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.collectHoldMs);
		},
		skyjumpV2HeadJudgeCollect: async ({
			position,
			passIndex,
			collectedX,
			tokenContributions,
			flightMultiplierX,
			timings,
			catchUp,
		}) => {
			const keys = new Set(tokenContributions.map((token) => cellKey(token.reel, token.row)));
			keys.add(cellKey(position.reel, position.row));
			highlightKeys = keys;
			featureWinX += collectedX;
			winLabel = 'HEAD JUDGE';
			winSub =
				flightMultiplierX && flightMultiplierX !== 1
					? `pass ${passIndex}/2 · +${collectedX.toFixed(1)}x · flight x${flightMultiplierX} · feature ${featureWinX.toFixed(1)}x`
					: `pass ${passIndex}/2 · +${collectedX.toFixed(1)}x · feature ${featureWinX.toFixed(1)}x`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.collectHoldMs);
		},
		skyjumpV2CapReached: async ({
			rawTotalWinX,
			cappedTotalWinX,
			capDragX,
			maxWinX,
			terminated,
			timings,
			catchUp,
		}) => {
			highlightKeys = new Set();
			winLabel = worldRecordActive
				? `${loungeShown('WORLD_RECORD')} · MAX WIN`
				: terminated
					? 'MAX WIN · TERMINATED'
					: 'MAX WIN CAP';
			winSub = `${rawTotalWinX.toFixed(1)}x → ${cappedTotalWinX.toFixed(1)}x · terminated ${terminated ? 'true' : 'false'} · max ${maxWinX.toFixed(0)}x · drag ${capDragX.toFixed(1)}`;
			showWin = true;
			openCelebration({
				totalWinX: cappedTotalWinX,
				amount: cappedTotalWinX,
				worldRecord: worldRecordActive,
				capHit: true,
				catchUp,
				worldRecordOverlay: worldRecordActive,
			});
			if (!catchUp) await waitForTimeout(timings.capHoldMs);
		},
		skyjumpV2WorldRecord: async ({
			position,
			bonusTier,
			worldRecordIncrementX,
			finalRoundWinX,
			maxWinX,
			remainingFreeSpinsCancelled,
			symbolId,
			timings,
			catchUp,
		}) => {
			worldRecordActive = true;
			worldRecordPos = position;
			worldRecordWinX = Number(finalRoundWinX);
			const next = board.map((col) => [...col]);
			next[position.reel][position.row] = symbolId || 'SPECIAL_WORLD_RECORD';
			board = next;
			spinning = [false, false, false, false, false];
			reelPace = ['', '', '', '', ''];
			rejumping = false;
			preservedKeys = new Set();
			highlightKeys = new Set([cellKey(position.reel, position.row)]);
			wins = [];
			winLabel = loungeShown('WORLD_RECORD');
			winSub = `${loungeShown(bonusTier, bonusTier)} · +${worldRecordIncrementX.toFixed(1)}x → ${finalRoundWinX.toFixed(0)}x / ${maxWinX.toFixed(0)}x · FS cancelled ${remainingFreeSpinsCancelled}`;
			showWin = true;
			openCelebration({
				totalWinX: Number(finalRoundWinX),
				amount: Number(finalRoundWinX),
				worldRecord: true,
				capHit: true,
				catchUp,
				worldRecordOverlay: true,
			});
			if (!catchUp) await waitForTimeout(timings.capHoldMs);
		},
		skyjumpV2PersistentApply: async ({ positions, timings, catchUp }) => {
			const next = board.map((col) => [...col]);
			const labels: string[] = [];
			for (const pos of positions) {
				if (pos.reel < 0 || pos.row < 0) continue;
				const from = pos.symbolId || next[pos.reel][pos.row];
				labels.push(`${from} -> MYSTERY`);
				next[pos.reel][pos.row] = 'Y';
			}
			board = next;
			highlightKeys = new Set(positions.map((pos) => cellKey(pos.reel, pos.row)));
			winLabel = 'PERSISTENT TARGET';
			winSub = labels.join(' · ') || 'MYSTERY';
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.mysteryHoldMs);
		},
		skyjumpV2WindKey: async ({
			position,
			selectedStage,
			action,
			oldStageValue,
			newStageValue,
			newGlobalMultiplier,
			timings,
			catchUp,
		}) => {
			highlightKeys = new Set([cellKey(position.reel, position.row)]);
			showWin = true;
			if (action === 'CHARGE') {
				winLabel = 'ACCESS PASS · CHARGE';
				winSub = `${loungeShown(selectedStage ?? '', 'STAGE')} charge 1/2 · x${oldStageValue} unchanged · global x${newGlobalMultiplier} · next pass may pick any lowest-value stage`;
			} else if (action === 'UPGRADE') {
				winLabel = 'ACCESS PASS · UPGRADE';
				winSub = `${loungeShown(selectedStage ?? '', 'STAGE')} x${oldStageValue}→x${newStageValue} · global x${newGlobalMultiplier}`;
			} else {
				winLabel = 'ACCESS PASS';
				winSub = 'no effect';
			}
			if (!catchUp) await waitForTimeout(timings.windHoldMs);
		},
		skyjumpV2RejumpStart: async ({
			chainIndex,
			preservedPositions,
			redroppedPositions,
			rejumpsThisSpin,
			timings,
			catchUp,
		}) => {
			rejumping = true;
			preservedKeys = new Set(preservedPositions.map((pos) => cellKey(pos.reel, pos.row)));
			highlightKeys = new Set(preservedKeys);
			winLabel = `REJUMP ${chainIndex}`;
			winSub = `keep ${preservedPositions.length} · redrop ${redroppedPositions.length} · spin #${rejumpsThisSpin}`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.rejumpHoldMs);
		},
		skyjumpV2RejumpBoard: async ({ board: nextBoard, changedCells, timings, catchUp }) => {
			const next = board.map((col) => [...col]);
			if (nextBoard) {
				for (let reel = 0; reel < 5; reel += 1) {
					for (let row = 0; row < 5; row += 1) {
						if (preservedKeys.has(cellKey(reel, row))) continue;
						next[reel][row] = nextBoard[reel][row];
					}
				}
			} else if (changedCells) {
				for (const cell of changedCells) {
					next[cell.reel][cell.row] = cell.symbolId;
				}
			}
			board = next;
			const changed = new Set((changedCells ?? []).map((cell) => cellKey(cell.reel, cell.row)));
			highlightKeys = new Set([...preservedKeys, ...changed]);
			winLabel = 'REJUMP BOARD';
			winSub = `${changed.size || 'partial'} cells updated`;
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.rejumpHoldMs);
		},
		skyjumpV2RejumpLineWins: async ({ lineWins, lineWinX, chainIndex, timings, catchUp }) => {
			wins = lineWins;
			featureWinX += lineWinX;
			showWin = true;
			if (lineWins.length === 0) {
				winLabel = `REJUMP ${chainIndex} LINES`;
				winSub = '0.0x';
				highlightKeys = new Set(preservedKeys);
				if (!catchUp && timings.winHoldMs > 0) await waitForTimeout(timings.winHoldMs);
				return;
			}
			winLabel = `REJUMP ${chainIndex} · ${lineWins.length} LINE${lineWins.length > 1 ? 'S' : ''}`;
			winSub = `${lineWinX.toFixed(1)}x`;
			if (catchUp) {
				highlightWin(null, lineWins);
				return;
			}
			for (const win of lineWins) {
				highlightWin(win, lineWins);
				winLabel = `REJUMP ${chainIndex} · ${win.symbolId} ×${win.matchCount}`;
				winSub = `${win.payoutX.toFixed(1)}x · L${win.paylineId}`;
				await animateLinePop(win, timings, false);
			}
			highlightWin(null, lineWins);
			pathDraw = 1;
			pathOpacity = 1;
			winLabel = `REJUMP ${chainIndex} · ${lineWins.length} LINE${lineWins.length > 1 ? 'S' : ''}`;
			winSub = `${lineWinX.toFixed(1)}x`;
		},
		skyjumpV2RejumpEnd: async ({ chainIndex, applied, truncated, reason, timings, catchUp }) => {
			preservedKeys = new Set();
			rejumping = false;
			winLabel = applied ? `REJUMP ${chainIndex} DONE` : `REJUMP ${chainIndex} SKIPPED`;
			winSub = truncated
				? `truncated · ${reason ?? 'limit'}`
				: applied
					? 'applied'
					: (reason ?? 'noop');
			showWin = true;
			if (!catchUp) await waitForTimeout(timings.rejumpHoldMs);
		},
		skyjumpV2BonusTitles: async ({ kind, tier, timings, catchUp }) => {
			if (catchUp) return;
			titleBannerShow = false;
			titleBannerSrc = null;
			const showOne = async (src: string | null, ms: number, bannerKind: V2BannerKind) => {
				if (!src || ms <= 0) return;
				titleBannerKind = bannerKind;
				titleBannerSrc = src;
				titleBannerShow = true;
				await waitForTimeout(ms);
				titleBannerShow = false;
				titleBannerSrc = null;
				await waitForTimeout(stateBet.isTurbo ? 40 : 90);
			};
			if (kind === 'fsStart') {
				await showOne(v2UiAssetUrl('bonusFreeSpins'), timings.fsBannerMs, 'bonus');
				await showOne(v2ModeTitleUrl(tier), timings.modeTitleMs, 'mode');
				return;
			}
			if (kind === 'retrigger') {
				await showOne(v2UiAssetUrl('bonusRetrigger'), timings.retriggerBannerMs, 'retrigger');
				return;
			}
			// tierUpgrade: upgrade banner then mode — never stack with retrigger art
			await showOne(v2UiAssetUrl('bonusTierUpgrade'), timings.tierUpgradeMs, 'tierUpgrade');
			await showOne(v2ModeTitleUrl(tier), timings.modeTitleMs, 'mode');
		},
	});
</script>

{#if context.stateGame.screen === 'play'}
	<!-- Stage: slot frame + grid (under full-viewport light sweep). -->
	<div
		class="v2-board v2-board-stage"
		style:left={`${left + px(BOARD_NUDGE_X)}px`}
		style:top={`${top}px`}
		style:width={`${surfaceW}px`}
		style:--board-left={`${left + px(BOARD_NUDGE_X)}px`}
		style:--cell-w={`${cellW}px`}
		style:--cell-h={`${cellH}px`}
		style:--gap={`${gap}px`}
		style:--frame-pad={`${framePad}px`}
		style:--frame-left={`${slotFrameLeft}px`}
		style:--frame-top={`${slotFrameTop}px`}
		style:--frame-border={`${FRAME_BORDER}px`}
		style:--board-w={`${boardW}px`}
		style:--board-h={`${boardH}px`}
		data-test="skyjump-v2-board"
	>
		{#if bonusHud.active || bonusHud.bonusWinX > 0}
			<div
				class="fs-banner"
				data-test="skyjump-v2-free-spins"
				data-tier={bonusHud.tier ?? ''}
				data-left={bonusHud.spinsRemaining}
				data-played={bonusHud.spinsPlayed}
				data-awarded={bonusHud.totalAwarded}
				data-floor={bonusHud.tokenFloorTier}
				data-targets={bonusHud.persistentTargets.join(',')}
				data-active={bonusHud.active ? 'true' : 'false'}
			>
				<div class="hud-head">
					<p class="hud-kicker">Room</p>
					{#if modeBadgeLabel}
						<SkyJumpV2ModeBadge label={modeBadgeLabel} />
					{/if}
					{#if tierEmblemSrc}
						<img class="tier-emblem" src={tierEmblemSrc} alt="" draggable="false" />
					{/if}
				</div>
				<div class="flight-panel" data-test="skyjump-v2-flight-multiplier">
					<div class="hud-stat">
						<span class="hud-label">{loungeShown('RUN_UP')}</span>
						<strong class="hud-value">×{bonusHud.flightRunUp.value}</strong>
						<span class="charges">
							{#each chargeBoxes(bonusHud.flightRunUp.charge) as filled}
								<span class="charge" class:on={filled}></span>
							{/each}
						</span>
					</div>
					<div class="hud-stat">
						<span class="hud-label">{loungeShown('TAKEOFF')}</span>
						<strong class="hud-value">×{bonusHud.flightTakeoff.value}</strong>
						<span class="charges">
							{#each chargeBoxes(bonusHud.flightTakeoff.charge) as filled}
								<span class="charge" class:on={filled}></span>
							{/each}
						</span>
					</div>
					<div class="hud-stat">
						<span class="hud-label">{loungeShown('FLIGHT')}</span>
						<strong class="hud-value">×{bonusHud.flightFlight.value}</strong>
						<span class="charges">
							{#each chargeBoxes(bonusHud.flightFlight.charge) as filled}
								<span class="charge" class:on={filled}></span>
							{/each}
						</span>
					</div>
					<div class="hud-stat">
						<span class="hud-label">Global</span>
						<strong class="hud-value">×{bonusHud.globalFlightMultiplier}</strong>
					</div>
				</div>
				<div class="hud-split">
					<div class="hud-stat">
						<span class="hud-label">Free Spins</span>
						<strong class="hud-value">{bonusHud.spinsRemaining}</strong>
					</div>
					<p class="hud-meta">Played {bonusHud.spinsPlayed} · bonus {bonusHud.bonusWinX.toFixed(1)}x</p>
				</div>
				<div class="hud-split">
					<div class="hud-floor">
						<span class="hud-label">Token floor</span>
						{#each [1, 2, 3] as tier}
							<span class:floor-on={bonusHud.tokenFloorTier === tier}>T{tier}</span>
						{/each}
					</div>
					{#if bonusShowsTargets(bonusHud.tier) || bonusHud.persistentTargets.length}
						<div class="hud-targets">
							<span class="hud-label">Mystery targets</span>
							{#if bonusHud.persistentTargets.length}
								<span class="hud-meta">
									{#each bonusHud.persistentTargets as target}
										<span class="target-slot">{target}</span>
									{/each}
								</span>
							{/if}
						</div>
					{/if}
				</div>
				<div class="hud-notes">
					{#if bonusHud.floorStep}
						<em>{bonusHud.floorStep}</em>
					{/if}
					{#if bonusHud.guaranteedGateUsed}
						<p class="hud-meta">VIP upgrade used</p>
					{/if}
					{#if bonusHud.guaranteedCoach}
						<p class="hud-meta">Concierge guaranteed</p>
					{/if}
					{#if bonusHud.upgradeNotice}
						<em class="upgrade">{bonusHud.upgradeNotice}</em>
					{/if}
					{#if bonusHud.unlockedNotice}
						<em>{bonusHud.unlockedNotice}</em>
					{/if}
					{#if bonusHud.retriggerNote}
						<em data-test="bonus-retrigger">{bonusHud.retriggerNote}</em>
					{/if}
					{#if bonusHud.persistNote}
						<em data-test="persistent-target">{bonusHud.persistNote}</em>
					{/if}
					{#if bonusHud.windToast}
						<em data-test="wind-toast">{bonusHud.windToast}</em>
					{/if}
					{#if isDevInspector}
						<span>TOTAL AWARDED: {bonusHud.totalAwarded}</span>
						<span>keys {bonusHud.windKeysCollected} · rejumps {bonusHud.rejumpsThisBonus}</span>
					{/if}
				</div>
			</div>
		{/if}
		{#if worldRecordActive}
			<div class="wr-overlay" data-test="skyjump-v2-wr-overlay" aria-hidden="true">
				<img class="wr-art" src={wrOverlaySrc} alt="" draggable="false" />
				<div class="wr-copy">
					<strong>{loungeShown('WORLD_RECORD')}</strong>
					{#if worldRecordWinX > 0}
						<span>{worldRecordWinX.toFixed(0)}×</span>
					{/if}
				</div>
			</div>
		{/if}
		<div class="board-surface" data-test="skyjump-v2-board-surface">
			<div class="board-glass" aria-hidden="true"></div>
			<img
				class="board-art-frame"
				src={slotFrameSrc}
				alt=""
				draggable="false"
				aria-hidden="true"
				data-test="skyjump-v2-slot-frame"
				style:left={`${slotFrameLeft}px`}
				style:top={`${slotFrameTop}px`}
				style:width={`${slotFrameW}px`}
				style:height={`${slotFrameH}px`}
			/>
			<div class="grid" class:rejumping aria-hidden="true">
				{#each Array.from({ length: 5 }, (_, reel) => reel) as reel}
					{@const ids = spinIds[reel] ?? board[reel]}
					<div
						class="reel"
						class:spinning={spinning[reel]}
						class:pace-soft={reelPace[reel] === 'soft'}
						class:pace-fast={reelPace[reel] === 'fast'}
						class:landing={reelPace[reel] === 'land'}
						data-reel={reel + 1}
						style:--land-ms={`${landMs}ms`}
					>
						<div
							class="reel-strip"
							style:transform={`translate3d(0, ${spinIds[reel] ? spinOffset[reel] : 0}px, 0)`}
						>
							{#each ids as id, index (`${reel}-${index}-${id}`)}
								{@const settled = !spinning[reel] && index < VISIBLE_ROWS}
								{@const visual = v2SymbolVisual(id)}
								{@const tile = visual.placeholder}
								{@const showArt = Boolean(visual.url && artReady[id] && !artBroken[id])}
								<div
									class="symbol"
									class:filler={Boolean(spinIds[reel]) &&
										index >= VISIBLE_ROWS &&
										index < ids.length - VISIBLE_ROWS}
									class:dim={settled && dimmed(reel, index)}
									class:hit={settled &&
										(lineSeqActive
											? poppedKeys.has(cellKey(reel, index))
											: highlightKeys.has(cellKey(reel, index)))}
									class:popped={settled && poppedKeys.has(cellKey(reel, index))}
									class:preserved={settled && preservedKeys.has(cellKey(reel, index))}
									class:inspect={settled && inspectCells.has(cellKey(reel, index))}
									class:world-record={settled &&
										worldRecordActive &&
										worldRecordPos?.reel === reel &&
										worldRecordPos?.row === index}
									style:color={tile.ink}
									data-symbol={id}
									data-row={settled ? index : undefined}
									data-test={settled ? 'skyjump-v2-tile' : undefined}
								>
									<div class="content-stage">
										{#if visual.url && !artBroken[id]}
											<img
												class="sym-art"
												class:ready={showArt}
												src={visual.url}
												alt=""
												draggable="false"
												onload={() => {
													markV2SymbolArtReady(id);
													artReady = { ...artReady, [id]: true };
												}}
												onerror={() => {
													markV2SymbolArtMissing(id);
													artBroken = { ...artBroken, [id]: true };
												}}
											/>
										{/if}
										{#if !showArt}
											<span class="sym-fallback">{tile.label}</span>
										{/if}
									</div>
									{#if settled && thermalMults[cellKey(reel, index)]}
										<small>×{thermalMults[cellKey(reel, index)]}</small>
									{:else if settled && tokenEffective[cellKey(reel, index)]}
										<small
											>{tokenFaces[cellKey(reel, index)]}→{tokenEffective[cellKey(reel, index)]}x</small
										>
									{:else if settled && tokenFaces[cellKey(reel, index)]}
										<small>{tokenFaces[cellKey(reel, index)]}x</small>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/each}
				<!-- Payline FX above settled symbols, still under the slot frame. -->
				<svg
					class="paths"
					viewBox={`0 0 ${boardW} ${boardH}`}
					preserveAspectRatio="xMidYMid meet"
					data-test="skyjump-v2-payline-svg"
				>
					{#if pathD}
						<path
							class="payline-stroke"
							d={pathD}
							fill="none"
							stroke="#7ad4ff"
							stroke-width="4.5"
							stroke-linecap="round"
							stroke-linejoin="round"
							opacity={pathOpacity * 0.5}
							style:stroke-dasharray={pathLen > 0 ? pathLen : undefined}
							style:stroke-dashoffset={pathLen > 0 ? pathLen * (1 - pathDraw) : 0}
							filter="url(#paylineGlow)"
						/>
						<path
							class="payline-core"
							d={pathD}
							fill="none"
							stroke="#ffe08a"
							stroke-width="2.4"
							stroke-linecap="round"
							stroke-linejoin="round"
							opacity={pathOpacity}
							style:stroke-dasharray={pathLen > 0 ? pathLen : undefined}
							style:stroke-dashoffset={pathLen > 0 ? pathLen * (1 - pathDraw) : 0}
						/>
						{#if sparkOn && sparkPos}
							<image
								class="payline-spark"
								href={paylineSparkSrc}
								x={sparkPos.x - paylineSparkSize / 2}
								y={sparkPos.y - paylineSparkSize / 2}
								width={paylineSparkSize}
								height={paylineSparkSize}
								preserveAspectRatio="xMidYMid meet"
								opacity="1"
								data-test="skyjump-v2-payline-spark"
							/>
							<circle
								class="payline-spark-bloom"
								cx={sparkPos.x}
								cy={sparkPos.y}
								r={Math.max(5, paylineSparkSize * 0.18)}
								fill="rgba(180, 230, 255, 0.45)"
							/>
						{/if}
						{#if pathGlintOn && pathGlintPos}
							<!-- Group at endpoint so fade/scale stays centered (CSS transform on bare
							     <image> uses a weird origin and looks like it flies in from an angle). -->
							<g
								class="payline-end-glint"
								transform="translate({pathGlintPos.x} {pathGlintPos.y})"
								data-test="skyjump-v2-payline-glint"
							>
								<image
									href={paylineGlintSrc}
									x={-paylineGlintSize / 2}
									y={-paylineGlintSize / 2}
									width={paylineGlintSize}
									height={paylineGlintSize}
									preserveAspectRatio="xMidYMid meet"
									opacity="1"
								/>
							</g>
						{/if}
					{/if}
					<defs>
						<filter id="paylineGlow" x="-50%" y="-50%" width="200%" height="200%">
							<feGaussianBlur stdDeviation="2.4" result="blur" />
							<feMerge>
								<feMergeNode in="blur" />
								<feMergeNode in="SourceGraphic" />
							</feMerge>
						</filter>
					</defs>
				</svg>
			</div>
		</div>
	</div>
	<!-- Full-viewport icy sweep: over bg + slot frame; under summary + BetUI. -->
	<div
		class="viewport-light-sweep"
		aria-hidden="true"
		data-test="skyjump-v2-viewport-sweep"
		style:left="0px"
		style:top="0px"
		style:width={`${canvas.width}px`}
		style:height={`${canvas.height}px`}
	></div>
	<!-- Overlay chrome: READY summary + titles above sweep and BetUI crest. -->
	<div
		class="v2-board v2-board-overlay"
		style:left={`${left}px`}
		style:top={`${top}px`}
		style:width={`${surfaceW}px`}
		style:--summary-gap={`${summaryGapPx}px`}
	>
		<div class="board-overlay-spacer" style:height={`${surfaceH}px`} aria-hidden="true"></div>
		<div
			class="win-banner"
			class:miss={showWin && wins.length === 0}
			class:idle={!showWin && !winLabel}
			data-test="skyjump-v2-status-bar"
		>
			<SkyJumpV2StatusPlate label={playerLabel(statusLabel)} sub={showWin ? playerSub(winSub) : ''}>
				{#if showWin && featureWinX > 0}
					<em>feature {featureWinX.toFixed(1)}x</em>
				{/if}
				{#if showWin && scatterCount > 0}
					<em>{scatterCount} {scatterCount === 1 ? 'INVITATION' : 'INVITATIONS'}{scatterPerfect ? ' · V' : ''}</em>
				{/if}
			</SkyJumpV2StatusPlate>
		</div>

		{#if titleBannerShow && titleBannerSrc}
			<SkyJumpV2TitleBanner src={titleBannerSrc} show={titleBannerShow} kind={titleBannerKind} />
		{/if}

		<SkyJumpV2WinCelebration
			show={celebrationShow}
			tier={celebrationTier}
			amount={celebrationAmount}
			turbo={stateBet.isTurbo}
			catchUp={celebrationCatchUp}
			worldRecordOverlay={celebrationWorldRecordOverlay}
			oncomplete={() => {
				celebrationShow = false;
				settleCelebrationWait();
			}}
		/>
	</div>

	{#if isDevInspector}
		<div class="inspector">
			<p>DEV PAYLINE INSPECTOR</p>
			<label>
				Line
				<select bind:value={inspectId}>
					<option value={0}>off</option>
					{#each V2_PAYLINE_IDS as id}
						<option value={id}>{id}</option>
					{/each}
				</select>
			</label>
			{#if DevSource}
				<DevSource />
			{/if}
			{#if CharacterQa}
				<CharacterQa />
			{/if}
			{#if AudioQa}
				<AudioQa />
			{/if}
			<p class="hint">
				{Object.keys(V2_PLACEHOLDERS).length} tiles · turbo {stateBet.isTurbo ? 'on' : 'off'}
			</p>
		</div>
	{/if}
{/if}

<style>
	.v2-board {
		position: absolute;
		display: flex;
		flex-direction: column;
		align-items: stretch;
		gap: 0;
		pointer-events: none;
		box-sizing: border-box;
		overflow: visible;
		font-family: var(--skyjump-font-ui, 'SkyjumpUI', system-ui, sans-serif);
	}

	.v2-board-stage {
		z-index: 16;
	}

	.v2-board-overlay {
		z-index: 22;
	}

	.board-overlay-spacer {
		flex: 0 0 auto;
		width: 100%;
		pointer-events: none;
		visibility: hidden;
	}

	.fs-banner {
		position: absolute;
		z-index: 8;
		/* Right edge stays 16px clear of the frame. Left edge uses the lounge gutter. */
		top: calc(var(--frame-top, 24px) + 68px);
		left: calc(12px - var(--board-left, 0px));
		right: calc(100% - var(--frame-left, 0px) + 16px);
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		align-items: stretch;
		gap: 0.28rem;
		width: auto;
		/* Ends above the status plate. Hidden, not scroll: the rows are laid out to fit. */
		max-height: calc(100% - var(--frame-top, 24px) - 92px);
		overflow: hidden;
		padding: 0.45rem 0.7rem 0.5rem;
		color: var(--ml-gold, #f0c75a);
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		text-align: center;
		background:
			radial-gradient(120% 80% at 50% 0%, rgba(228, 197, 122, 0.14), transparent 58%),
			linear-gradient(180deg, #4a1424, #12080c);
		border: 1px solid rgba(212, 168, 92, 0.72);
		border-radius: 14px;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.04em;
		box-shadow:
			0 14px 28px rgba(0, 0, 0, 0.42),
			inset 0 1px 0 rgba(243, 226, 184, 0.18),
			inset 0 0 18px rgba(74, 20, 36, 0.4);
		pointer-events: none;
	}

	.fs-banner::before,
	.fs-banner::after {
		content: '';
		position: absolute;
		width: 12px;
		height: 12px;
		border: 1.5px solid rgba(228, 197, 122, 0.8);
		pointer-events: none;
	}

	.fs-banner::before {
		top: 6px;
		left: 6px;
		border-right: 0;
		border-bottom: 0;
	}

	.fs-banner::after {
		right: 6px;
		bottom: 6px;
		border-left: 0;
		border-top: 0;
	}

	.hud-kicker,
	.hud-label {
		margin: 0;
		color: var(--ml-gold, #f0c75a);
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		font-size: 0.62rem;
		font-weight: 800;
		letter-spacing: 0.16em;
		line-height: 1;
		text-transform: uppercase;
	}

	.hud-head {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.45rem;
		min-height: 1.2rem;
	}

	.hud-head .hud-kicker {
		flex: 0 0 auto;
	}

	.hud-stat {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.35rem;
		min-width: 0;
	}

	.hud-stat .hud-label {
		letter-spacing: 0.08em;
		text-align: left;
		white-space: nowrap;
	}

	.flight-panel .hud-value {
		font-size: 1rem;
	}

	.flight-panel .hud-stat {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto auto;
		justify-content: stretch;
	}

	.hud-value {
		color: var(--ml-gold, #f0c75a);
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		font-size: 1.15rem;
		font-weight: 800;
		line-height: 1;
	}

	.hud-meta {
		margin: 0;
		color: var(--ml-gold, #f0c75a);
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.04em;
	}

	.hud-split {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.6rem;
		min-width: 0;
	}

	.hud-split .hud-stat,
	.hud-floor,
	.hud-targets {
		flex: 1 1 auto;
		min-width: 0;
	}

	.hud-targets {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 0.35rem;
	}

	.hud-notes {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.12rem;
	}

	.hud-notes:empty {
		display: none;
	}

	.hud-floor {
		display: flex;
		flex-wrap: nowrap;
		gap: 0.25rem;
		align-items: center;
		justify-content: flex-start;
	}

	.board-surface {
		position: relative;
		z-index: 1;
		box-sizing: border-box;
		width: 100%;
		padding: var(--frame-pad);
		/* Ornate art frame provides chrome — keep only soft glass behind tiles. */
		border: none;
		border-radius: 0;
		background: transparent;
		box-shadow: none;
		overflow: visible;
	}

	.board-art-frame {
		position: absolute;
		z-index: 6;
		display: block;
		pointer-events: none;
		object-fit: fill;
		object-position: center;
		background: transparent;
		border: none;
		user-select: none;
		-webkit-user-drag: none;
		filter: drop-shadow(0 14px 28px rgba(0, 6, 18, 0.45));
	}

	.board-glass {
		position: absolute;
		top: var(--frame-pad);
		left: var(--frame-pad);
		z-index: 0;
		box-sizing: border-box;
		width: var(--board-w);
		height: var(--board-h);
		border-radius: clamp(8px, 1vw, 12px);
		pointer-events: none;
		/* Shared board glass only. Reel strips sit on top; no per-cell cards. */
		background-image:
			radial-gradient(ellipse at 50% 0%, rgba(212, 168, 92, 0.14), transparent 58%),
			linear-gradient(180deg, rgba(36, 10, 18, 0.34), rgba(6, 3, 6, 0.46));
		box-shadow:
			inset 0 0 18px rgba(0, 0, 0, 0.4),
			inset 0 0 0 1px rgba(212, 168, 92, 0.2);
		animation: board-grid-breathe 5.2s ease-in-out infinite;
	}

	/* Full 1280×720 icy light sweep — over stage/bg, under BetUI + READY. */
	.viewport-light-sweep {
		position: absolute;
		z-index: 17;
		pointer-events: none;
		background: linear-gradient(
			118deg,
			transparent 34%,
			rgba(170, 220, 255, 0.08) 42%,
			rgba(230, 245, 255, 0.28) 50%,
			rgba(170, 220, 255, 0.08) 58%,
			transparent 66%
		);
		background-size: 220% 100%;
		animation: viewport-light-sweep 5.2s linear infinite;
		mix-blend-mode: soft-light;
		opacity: 1;
	}

	/* Travelling icy highlight locked to the outer frame ring only. */
	.board-edge-ring {
		position: absolute;
		inset: 0;
		z-index: 6;
		border-radius: inherit;
		pointer-events: none;
		padding: 2.5px;
		overflow: hidden;
		box-sizing: border-box;
		-webkit-mask:
			linear-gradient(#fff 0 0) content-box,
			linear-gradient(#fff 0 0);
		-webkit-mask-composite: xor;
		mask-composite: exclude;
	}

	.board-edge-ring::before {
		content: '';
		position: absolute;
		inset: -55%;
		background: conic-gradient(
			from 0deg,
			transparent 0deg,
			transparent 240deg,
			rgba(140, 205, 255, 0.22) 270deg,
			rgba(220, 242, 255, 1) 295deg,
			rgba(160, 220, 255, 0.55) 318deg,
			transparent 340deg,
			transparent 360deg
		);
		animation: board-edge-spin 5s linear infinite;
	}

	.board-glint {
		position: absolute;
		z-index: 7;
		width: 9px;
		height: 9px;
		border-radius: 50%;
		pointer-events: none;
		background: radial-gradient(
			circle,
			rgba(255, 255, 255, 0.95) 0%,
			rgba(170, 225, 255, 0.45) 40%,
			transparent 72%
		);
		opacity: 0.62;
		animation: board-corner-glint 5s ease-in-out infinite;
	}

	.board-glint-tl {
		top: 4px;
		left: 4px;
	}

	.board-glint-tr {
		top: 4px;
		right: 4px;
		animation-delay: 1.25s;
	}

	.board-glint-bl {
		bottom: 4px;
		left: 4px;
		animation-delay: 2.5s;
	}

	.board-glint-br {
		right: 4px;
		bottom: 4px;
		animation-delay: 3.75s;
	}

	@keyframes board-frame-breathe {
		0%,
		100% {
			border-color: rgba(140, 205, 255, 0.58);
			box-shadow:
				0 0 0 1px rgba(212, 175, 92, 0.22),
				0 16px 40px rgba(0, 6, 18, 0.45),
				0 0 14px rgba(110, 190, 255, 0.12),
				inset 0 1px 0 rgba(230, 245, 255, 0.28),
				inset 0 -14px 32px rgba(0, 8, 22, 0.42);
		}
		50% {
			border-color: rgba(210, 240, 255, 0.98);
			box-shadow:
				0 0 0 1px rgba(212, 175, 92, 0.4),
				0 16px 40px rgba(0, 6, 18, 0.45),
				0 0 32px rgba(150, 220, 255, 0.42),
				inset 0 1px 0 rgba(255, 255, 255, 0.5),
				inset 0 -14px 32px rgba(0, 8, 22, 0.42);
		}
	}

	@keyframes viewport-light-sweep {
		0% {
			background-position: 120% 0;
			opacity: 0.4;
		}
		15% {
			opacity: 0.85;
		}
		50% {
			opacity: 1;
		}
		85% {
			opacity: 0.85;
		}
		100% {
			background-position: -120% 0;
			opacity: 0.4;
		}
	}

	@keyframes board-edge-spin {
		to {
			transform: rotate(360deg);
		}
	}

	@keyframes board-grid-breathe {
		0%,
		100% {
			opacity: 0.7;
			filter: brightness(0.96);
		}
		50% {
			opacity: 0.82;
			filter: brightness(1.02);
		}
	}

	@keyframes board-grid-sheen-move {
		0% {
			background-position: 120% 0;
		}
		100% {
			background-position: -120% 0;
		}
	}

	@keyframes board-corner-glint {
		0%,
		100% {
			opacity: 0.22;
			transform: scale(0.8);
		}
		40% {
			opacity: 0.95;
			transform: scale(1.35);
		}
		58% {
			opacity: 0.4;
			transform: scale(1);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.symbol.popped::before,
		.symbol.popped .content-stage {
			animation: none;
		}

		.board-surface,
		.board-glass,
		.viewport-light-sweep,
		.board-edge-ring::before,
		.board-glint,
		.symbol {
			animation: none;
		}

		.symbol,
		.reel.pace-fast .symbol,
		.reel.pace-soft .symbol,
		.reel.landing .symbol {
			filter: none;
			transform: none;
		}

		.viewport-light-sweep,
		.board-edge-ring {
			opacity: 0;
		}

		.board-glint {
			opacity: 0.35;
			transform: none;
		}

	}

	.win-banner {
		position: relative;
		z-index: 1;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		flex: 0 0 auto;
		height: 71px;
		min-height: 71px;
		max-height: 71px;
		width: 100%;
		max-width: 100%;
		/* Exact grid→summary gap from --summary-gap (10px @1280). */
		margin: var(--summary-gap, 10px) auto 0;
		padding: 0;
		overflow: hidden;
		color: #ffe083;
		background: transparent;
		border: none;
		border-radius: 0;
		font-weight: 800;
		letter-spacing: 0.06em;
		box-shadow: none;
		opacity: 1;
	}

	.win-banner.idle :global(.copy) {
		color: #f3e2b8;
		letter-spacing: 0.12em;
	}

	.win-banner.idle :global(.copy strong) {
		color: var(--ml-gold, #f0c75a);
	}

	.win-banner :global(.copy strong) {
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		font-size: 1.05rem;
	}

	.win-banner.miss :global(.copy) {
		color: var(--ml-gold, #f0c75a);
	}

	.win-banner.miss :global(.copy strong) {
		color: var(--ml-gold, #f0c75a);
	}

	.fs-banner em {
		color: #ffd36b;
		font-style: normal;
	}

	.fs-banner em.upgrade {
		display: inline-block;
		padding: 0.1rem 0.45rem;
		color: #1b1404;
		background: #ffd36b;
		border-radius: 999px;
	}

	.target-slot,
	.floor-on {
		padding: 0 0.3rem;
		border: 1px solid rgba(255, 211, 107, 0.8);
		border-radius: 6px;
		color: #ffd36b;
	}

	.flight-panel {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.28rem 0.85rem;
		width: 100%;
		padding: 0.28rem 0;
		border-top: 1px solid rgba(228, 197, 122, 0.28);
		border-bottom: 1px solid rgba(228, 197, 122, 0.28);
	}

	.charges {
		display: inline-flex;
		gap: 0.2rem;
	}

	.charge {
		width: 7px;
		height: 7px;
		border: 1px solid rgba(228, 197, 122, 0.55);
		background: transparent;
	}

	.charge.on {
		background: #e4c57a;
	}

	.tier-emblem {
		width: 22px;
		height: 22px;
		object-fit: contain;
		flex: 0 0 auto;
	}

	.wr-overlay {
		position: absolute;
		inset: -8% -4% auto;
		z-index: 9;
		display: grid;
		place-items: center;
		pointer-events: none;
		min-height: 42%;
	}

	.wr-art {
		width: min(100%, 420px);
		height: auto;
		object-fit: contain;
		filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.45));
	}

	.wr-copy {
		position: absolute;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		align-items: center;
		color: #fff6c8;
		text-shadow: 0 2px 10px rgba(0, 0, 0, 0.75);
		font-weight: 900;
		letter-spacing: 0.08em;
	}

	.wr-copy strong {
		font-size: clamp(14px, 2.2vw, 22px);
	}

	.wr-copy span {
		font-size: clamp(18px, 3vw, 28px);
		color: #ffe083;
	}

	.charge {
		display: inline-block;
		min-width: 0.85em;
		margin-left: 0.12rem;
		color: #7aa0b8;
		font-size: 0.95em;
	}

	.charge.on {
		color: #ffd36b;
	}

	.win-banner :global(em) {
		font-style: normal;
		color: #cfefff;
		opacity: 0.9;
	}

	.grid {
		position: relative;
		z-index: 1;
		box-sizing: border-box;
		display: grid;
		width: var(--board-w);
		height: var(--board-h);
		grid-template-columns: repeat(5, var(--cell-w));
		gap: var(--gap);
		min-width: 0;
		min-height: 0;
	}

	.paths {
		position: absolute;
		inset: 0;
		z-index: 12;
		width: 100%;
		height: 100%;
		overflow: visible;
		pointer-events: none;
	}

	.payline-spark,
	.payline-end-glint {
		pointer-events: none;
		filter: drop-shadow(0 0 5px rgba(160, 220, 255, 0.75));
	}

	.payline-end-glint {
		/* Opacity-only — do not CSS-transform SVG (overrides translate + wrong origin). */
		animation: glint-pop 200ms ease-out both;
	}

	@keyframes glint-pop {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.reel {
		position: relative;
		box-sizing: border-box;
		width: var(--cell-w);
		height: 100%;
		min-width: 0;
		min-height: 0;
		overflow: hidden;
	}

	.reel-strip {
		display: flex;
		flex-direction: column;
		width: 100%;
	}

	.reel.spinning .reel-strip {
		will-change: transform;
	}

	.reel.pace-soft .symbol {
		filter: blur(0.4px) brightness(1.04);
	}

	.reel.pace-fast .symbol {
		filter: blur(1.25px) brightness(1.05);
	}

	.reel.landing .symbol {
		animation: reel-land var(--land-ms, 160ms) ease-out both;
	}

	@keyframes reel-land {
		0% {
			filter: brightness(1.12) drop-shadow(0 1px 5px rgba(212, 168, 92, 0.32));
			transform: scale(1.01);
		}
		100% {
			filter: none;
			transform: none;
		}
	}

	.symbol {
		position: relative;
		z-index: 1;
		box-sizing: border-box;
		display: grid;
		place-items: center;
		width: 100%;
		/* Flush slots. Remaining air is transparent padding inside the PNGs. */
		height: calc(var(--board-h) / 5);
		flex: 0 0 calc(var(--board-h) / 5);
		overflow: hidden;
		background: transparent;
		border: 0;
		border-radius: 0;
		box-shadow: none;
		font-size: clamp(10px, calc(var(--cell-h) * 0.28), 18px);
		font-weight: 900;
		letter-spacing: 0.04em;
	}

	.content-stage {
		box-sizing: border-box;
		display: block;
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		overflow: hidden;
		pointer-events: none;
	}

	.symbol .sym-art {
		display: block;
		width: 100%;
		height: 100%;
		margin: 0;
		padding: 0;
		border: 0;
		object-fit: contain;
		object-position: center center;
		pointer-events: none;
		opacity: 0;
	}

	.symbol .sym-art.ready {
		opacity: 1;
	}

	.sym-fallback {
		display: grid;
		place-items: center;
		width: 100%;
		height: 100%;
		line-height: 1;
		text-align: center;
	}

	.symbol.world-record {
		z-index: 5;
		filter: drop-shadow(0 0 8px rgba(253, 230, 138, 0.85));
	}

	.symbol small {
		position: absolute;
		bottom: 5%;
		left: 50%;
		z-index: 2;
		transform: translateX(-50%);
		/* Marcellus, gold; 0.62em -> 0.93em (+50 %) -> 1.86em (+100 %). */
		color: var(--ml-gold, #f0c75a);
		font-family: var(--ml-font-gold, 'Marcellus', serif);
		font-size: 1.86em;
		letter-spacing: 0;
		line-height: 1;
		pointer-events: none;
	}

	.symbol.dim {
		opacity: 0.38;
	}

	/* Payline pop: the symbol swells slightly and a warm backlight blooms behind it. */
	.symbol.popped {
		z-index: 7;
		overflow: visible;
	}

	.symbol.popped::before {
		content: '';
		position: absolute;
		z-index: 0;
		inset: -22%;
		border-radius: 50%;
		background: radial-gradient(
			circle at center,
			rgba(255, 214, 110, 0.78) 0%,
			rgba(255, 150, 60, 0.42) 38%,
			rgba(214, 60, 40, 0.16) 62%,
			transparent 74%
		);
		pointer-events: none;
		animation: symbol-backlight 360ms ease-out both;
	}

	.symbol.popped .content-stage {
		position: relative;
		z-index: 1;
		overflow: visible;
		animation: symbol-pop 360ms cubic-bezier(0.2, 1.4, 0.4, 1) both;
	}

	@keyframes symbol-pop {
		0% {
			transform: scale(1);
		}
		55% {
			transform: scale(1.24);
		}
		100% {
			transform: scale(1.14);
		}
	}

	@keyframes symbol-backlight {
		from {
			opacity: 0;
			transform: scale(0.55);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	.symbol.hit {
		z-index: 5;
		filter: drop-shadow(0 0 7px rgba(255, 211, 107, 0.9)) brightness(1.08);
	}

	.symbol.preserved {
		z-index: 5;
		filter: drop-shadow(0 0 7px rgba(126, 214, 255, 0.85));
	}

	.grid.rejumping .symbol:not(.preserved) {
		opacity: 0.92;
	}

	.symbol.inspect {
		outline: 1px dashed rgba(126, 214, 255, 0.7);
		outline-offset: -2px;
	}

	.inspector {
		position: absolute;
		z-index: 40;
		top: 64px;
		right: 12px;
		bottom: auto;
		display: grid;
		gap: 6px;
		width: min(260px, 42vw);
		padding: 8px 10px;
		color: #cfe6f4;
		background: rgba(6, 18, 32, 0.86);
		border: 1px solid rgba(101, 200, 255, 0.35);
		border-radius: 10px;
		font: 700 11px/1.3 sans-serif;
		pointer-events: auto;
	}

	.inspector p {
		margin: 0;
		letter-spacing: 0.08em;
	}

	.inspector .hint {
		color: #9bb4c8;
		font-weight: 600;
		letter-spacing: 0;
	}

	.inspector select {
		width: 100%;
		margin-top: 2px;
		color: #fff;
		background: #0b1b2c;
		border: 1px solid #3e6d8f;
		border-radius: 5px;
	}

	@media (max-width: 720px) {
		.win-banner {
			font-size: 11px;
		}

		.board-surface {
			border-radius: 12px;
		}

		.inspector {
			top: 58px;
			right: 8px;
		}
	}
</style>
