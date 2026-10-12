/**
 * SkyJump HUD layout tokens + positioning (theme-only visual structure).
 * Handlers / economics live in button components — do not change those here.
 */

import { SKYJUMP_BUY_NUDGE_X, SKYJUMP_SIDE_NUDGE_Y } from './skyjumpBetUiArt';

export const SKYJUMP_HUD_TONE = {
	ice: 0x65c8ff,
	iceBright: 0x7ed6ff,
	iceSoft: 0xb7d3e6,
	label: 0xc5dcea,
	navy: 0x071a32,
	navyHover: 0x0e2f52,
	navyPressed: 0x04101c,
	navyActive: 0x1a4a78,
	navyDisabled: 0x0a2038,
	text: 0xf4faff,
	gold: 0xe6b84a,
	goldBright: 0xffd36b,
	goldHot: 0xffe083,
	goldFill: 0x1a1408,
	goldFillHover: 0x2a1e0c,
	goldFillPressed: 0x0e0a04,
	goldFillActive: 0x3a2a10,
	goldFillBuy: 0x2a220e,
	goldFillBuyHover: 0x3c3014,
	goldFillBuyActive: 0x4a3a18,
	goldText: 0xffe9b0,
	spinFill: 0x2a220c,
	spinFillHover: 0x3c3014,
	spinFillPressed: 0x181208,
	spinBorder: 0xffd36b,
	stopFill: 0x3a1a0c,
	stopFillHover: 0x4c2410,
	stopBorder: 0xffb060,
	turboOn: 0x3ee08a,
	turboOnSoft: 0x7cffb2,
	turboOff: 0x8aa0b4,
	turboOffSoft: 0xb7d3e6,
	autoOn: 0x7ed6ff,
	autoOnSoft: 0xb7e8ff,
} as const;

/** Fixed presentation sizes for primary 1280×720 SkyJump dock. */
export const SKYJUMP_HUD = {
	desktop: {
		/**
		 * Control + art dock width in layout units (1920×1080 virtual).
		 * At 1280×720 (scale 2/3) → 993 CSS px.
		 */
		dockWidth: 1490,
		dockHeight: 160,
		padBottom: 6,
		/**
		 * Extra inset inside art blue panels after crystal chrome (~81/1024).
		 * ~15 CSS px at 1280 (layout 22).
		 */
		panelPad: 22,
		/**
		 * Shift entire left control block leftward (~18 CSS px @1280).
		 * Layout units: 18 / (2/3) ≈ 27.
		 */
		leftGroupShiftX: -27,
		/** Gap Balance/Win ↔ bet stepper (~14 CSS). */
		infoClusterGap: 20,
		/** Gap SPIN edge ↔ Buy Bonus (~14 CSS); right block packs from Menu. */
		spinSideGap: 22,
		/** Compact right-block gaps (~10–11 CSS). */
		buyModesGap: 15,
		modesMenuGap: 15,
		clusterGap: 8,
		/** Left group ~5% smaller so it clears gold chrome. */
		infoCol: 129,
		betMinus: 49,
		betValue: 112,
		betPlus: 49,
		/**
		 * SPIN face ~+6% vs 148; glow still clears neighbouring controls.
		 * Vertical seat nudge applied in layout (spinNudgeY).
		 */
		spin: 157,
		/** Lower SPIN into the circular dock (~12 CSS px @1280 → layout 18). */
		spinNudgeY: 18,
		buyW: 156,
		/** Slightly taller BUY for presence; still centered on wingY. */
		buyH: 60,
		mode: 72,
		menu: 64,
		clusterH: 51,
	},
	compact: {
		dockWidth: 0,
		dockHeight: 210,
		padBottom: 18,
		panelPad: 16,
		leftGroupShiftX: 0,
		infoClusterGap: 12,
		spinSideGap: 12,
		buyModesGap: 10,
		modesMenuGap: 10,
		clusterGap: 6,
		infoCol: 100,
		betMinus: 44,
		betValue: 90,
		betPlus: 44,
		spin: 78,
		spinNudgeY: 0,
		buyW: 120,
		buyH: 46,
		mode: 50,
		menu: 46,
		clusterH: 46,
	},
} as const;

type Space = { width: number; height: number };
type Point = { x: number; y: number };

/** Compact only for narrow / near-square canvases — NOT for 1280×720 primary. */
export const isSkyJumpCompactHud = (hud: Space) => {
	const ratio = hud.width / Math.max(1, hud.height);
	return ratio < 1.35 || hud.width < 900;
};

export const getSkyJumpHudSizes = (hud: Space) =>
	isSkyJumpCompactHud(hud) ? SKYJUMP_HUD.compact : SKYJUMP_HUD.desktop;

/**
 * Art-space ratios for `ui_bet_hud_frame.png` (cropped 1024×217).
 * Circle mid = SPIN seat; wing mid = Balance / bet / menu row.
 */
export const SKYJUMP_BET_HUD_FRAME = {
	width: 1024,
	height: 217,
	circleMidY: 108 / 217,
	wingMidY: 143 / 217,
	/** End crystal / outer chrome — controls stay inside this inset. */
	chromeInsetX: 81 / 1024,
} as const;

export const getSkyJumpHudLayout = (hud: Space) => {
	const compact = isSkyJumpCompactHud(hud);
	const t = getSkyJumpHudSizes(hud);

	const dockW = compact
		? Math.max(320, hud.width - t.panelPad * 2)
		: Math.min(t.dockWidth, hud.width - 40);
	const frameH = dockW * (SKYJUMP_BET_HUD_FRAME.height / SKYJUMP_BET_HUD_FRAME.width);
	const circleOfs = frameH * SKYJUMP_BET_HUD_FRAME.circleMidY;
	const wingOfs = frameH * SKYJUMP_BET_HUD_FRAME.wingMidY;

	const sizes = {
		side: { width: t.menu, height: t.menu },
		plus: { width: t.betMinus, height: t.betMinus },
		betValue: { width: t.betValue, height: t.clusterH },
		spin: { width: t.spin, height: t.spin },
		buy: { width: t.buyW, height: t.buyH },
		mode: { width: t.mode, height: t.mode },
		turbo: { width: t.mode, height: t.mode },
		clusterH: t.clusterH,
		infoCol: t.infoCol,
	};

	if (compact) {
		const dockH = t.dockHeight;
		const dockX = Math.round((hud.width - dockW) * 0.5);
		const dockY = hud.height - dockH - t.padBottom;
		const row1 = dockY + Math.round(dockH * 0.28);
		const row2 = dockY + Math.round(dockH * 0.72);
		const col = dockW / 3;
		const balance = { x: dockX + col * 0.5, y: row1 };
		const win = { x: dockX + col * 1.5, y: row1 };
		const menu = { x: dockX + col * 2.5, y: row1 };

		const clusterW = t.betMinus + t.clusterGap + t.betValue + t.clusterGap + t.betPlus;
		const row2Items = [
			clusterW,
			t.spinSideGap,
			t.spin,
			t.spinSideGap,
			t.buyW,
			t.buyModesGap,
			t.mode,
			t.clusterGap,
			t.mode,
		];
		const row2W = row2Items.reduce((a, b) => a + b, 0);
		let x = dockX + (dockW - row2W) * 0.5;
		const dec = { x: x + t.betMinus * 0.5, y: row2 };
		x += t.betMinus + t.clusterGap;
		const amountBet = { x: x + t.betValue * 0.5, y: row2 };
		x += t.betValue + t.clusterGap;
		const inc = { x: x + t.betPlus * 0.5, y: row2 };
		x += t.betPlus + t.spinSideGap;
		const bet = { x: x + t.spin * 0.5, y: row2 };
		x += t.spin + t.spinSideGap;
		const buy = { x: x + t.buyW * 0.5, y: row2 };
		x += t.buyW + t.buyModesGap;
		const auto = { x: x + t.mode * 0.5, y: row2 };
		x += t.mode + t.clusterGap;
		const turbo = { x: x + t.mode * 0.5, y: row2 };

		return {
			compact,
			sizes,
			dock: { x: dockX, y: dockY, width: dockW, height: dockH },
			frame: { width: dockW, height: frameH, top: dockY },
			clusters: {
				info: { x: balance.x, y: row1, w: col * 2, h: 44 },
				bet: {
					x: (dec.x + inc.x) * 0.5,
					y: row2,
					w: clusterW + 16,
					h: t.clusterH + 12,
				},
			},
			separatorHeight: 40,
			balance,
			win,
			amountBet,
			sepA: { x: (balance.x + win.x) * 0.5, y: row1 },
			sepB: { x: win.x, y: row1 },
			menu,
			buy,
			auto,
			dec,
			bet,
			inc,
			turbo,
		};
	}

	// —— Primary 1280 landscape: art frame is master geometry ——
	const dockX = Math.round((hud.width - dockW) * 0.5);
	const spinCx = dockX + dockW * 0.5;

	/** Keep BetUI low (bottom crop intentional). Wing row + SPIN from art ratios. */
	const wingY = hud.height - t.padBottom - Math.max(t.clusterH, t.menu) * 0.5 - 10;
	/** Circle center, then nudge SPIN down into the dock socket. */
	const spinY = wingY - (wingOfs - circleOfs) + t.spinNudgeY;
	const frameTop = spinY - circleOfs - t.spinNudgeY;

	const dockTop = Math.min(spinY - t.spin * 0.5, wingY - t.clusterH * 0.5) - 6;
	const dockBottom = Math.max(spinY + t.spin * 0.5, wingY + t.clusterH * 0.5) + 6;
	const dockH = Math.max(t.dockHeight, dockBottom - dockTop);
	const dockY = hud.height - dockH - t.padBottom;

	const chrome = dockW * SKYJUMP_BET_HUD_FRAME.chromeInsetX;
	const leftEdge = dockX + chrome + t.panelPad + t.leftGroupShiftX;
	const rightEdge = dockX + dockW - chrome - t.panelPad;

	const infoW = t.infoCol * 1.7;
	const clusterW = t.betMinus + t.clusterGap + t.betValue + t.clusterGap + t.betPlus;

	/** SPIN: dock center X, nudged circle-center Y. */
	const bet = { x: spinCx, y: spinY };

	// LEFT: smaller group, shifted left into blue panel (clear of gold chrome)
	let x = leftEdge;
	const balance = { x: x + infoW * 0.32, y: wingY };
	const win = { x: x + infoW * 0.72, y: wingY };
	const sepA = { x: (balance.x + win.x) * 0.5, y: wingY };
	x += infoW + t.infoClusterGap;
	const clusterCx = x + clusterW * 0.5;
	const dec = { x: x + t.betMinus * 0.5, y: wingY };
	x += t.betMinus + t.clusterGap;
	const amountBet = { x: x + t.betValue * 0.5, y: wingY };
	x += t.betValue + t.clusterGap;
	const inc = { x: x + t.betPlus * 0.5, y: wingY };

	// RIGHT: one compact block packed from Menu (far right) inward, dropped ~5 CSS px
	const sideY = wingY + SKYJUMP_SIDE_NUDGE_Y;
	let rx = rightEdge;
	const menu = { x: rx - t.menu * 0.5, y: sideY };
	rx -= t.menu + t.modesMenuGap;
	const turbo = { x: rx - t.mode * 0.5, y: sideY };
	rx -= t.mode + t.clusterGap;
	const auto = { x: rx - t.mode * 0.5, y: sideY };
	rx -= t.mode + t.buyModesGap;
	const buy = { x: rx - t.buyW * 0.5 + SKYJUMP_BUY_NUDGE_X, y: sideY };

	return {
		compact,
		sizes,
		dock: { x: dockX, y: dockY, width: dockW, height: dockH },
		frame: { width: dockW, height: frameH, top: frameTop },
		clusters: {
			info: {
				x: (balance.x + win.x) * 0.5,
				y: wingY,
				w: infoW,
				h: t.clusterH + 16,
			},
			bet: {
				x: clusterCx,
				y: wingY,
				w: clusterW + 18,
				h: t.clusterH + 12,
			},
		},
		separatorHeight: 40,
		balance,
		win,
		amountBet,
		sepA,
		sepB: { x: win.x + infoW * 0.2, y: wingY },
		menu,
		buy,
		auto,
		dec,
		bet,
		inc,
		turbo,
	};
};

export const getSkyJumpHudCssDock = (main: Space & { x: number; y: number; scale: number }) => {
	const layout = getSkyJumpHudLayout(main);
	const scale = main.scale;
	const originX = main.x - (main.width * scale) / 2;
	const originY = main.y - (main.height * scale) / 2;
	const dockW = layout.dock.width * scale;
	const dockH = layout.dock.height * scale;
	const dockLeft = originX + layout.dock.x * scale;
	const dockTop = originY + layout.dock.y * scale;
	const frameW = layout.frame.width * scale;
	const frameH = layout.frame.height * scale;
	const frameTop = originY + layout.frame.top * scale;
	return {
		left: `${dockLeft}px`,
		top: `${dockTop}px`,
		width: `${dockW}px`,
		height: `${dockH}px`,
		borderRadius: layout.compact ? '22px' : '28px',
		spinLeft: `${originX + layout.bet.x * scale}px`,
		spinTop: `${originY + layout.bet.y * scale}px`,
		frameTop: `${frameTop}px`,
		frameWidth: `${frameW}px`,
		frameHeight: `${frameH}px`,
	};
};

export const getSkyJumpMenuFlyout = (layout: ReturnType<typeof getSkyJumpHudLayout>) => {
	const side = layout.sizes.side.width;
	const sideH = layout.sizes.side.height;
	const gap = 10;
	/** Flyout faces only — dock Menu / Exit stay on the side token. */
	const flyScale = 1.25;
	const itemW = side * flyScale;
	const itemH = sideH * flyScale;
	const keys = ['payTable', 'gameRules', 'settings', 'sound'] as const;
	const lift = layout.compact ? itemH + 8 : 14;
	const y = layout.dock.y - lift - itemH * 0.5;
	const items = {} as Record<(typeof keys)[number], Point>;
	// Leftmost flyout button shares the Auto button's left edge; the row grows right.
	let left = layout.auto.x - layout.sizes.mode.width * 0.5;
	for (const key of keys) {
		items[key] = { x: left + itemW * 0.5, y };
		left += itemW + gap;
	}
	return {
		y,
		items,
		itemSize: { width: itemW, height: itemH },
	};
};
