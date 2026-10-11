import { UI_BASE_SIZE } from './constants';

/**
 * Garden HUD tokens in virtual canvas units (standard MainContainer:
 * 1920×1080 desktop/landscape, 1920×1920 tablet, 1080×1920 portrait).
 * The existing canvas scale maps these to the real viewport together, so
 * short laptops shrink the HUD instead of clipping it.
 *
 * Side rails scale harder than the bottom row so MENU / BUY / meters / +/-
 * catch up to the enlarged slot without the bottom cluster competing with it.
 */
export const HUD_SCALE = {
	side: 1.42,
	plus: 1.42,
	bottom: 1.16,
	meterWidth: 1.36,
} as const;

const px = (n: number) => Math.round(n);
const scaled = (width: number, height: number, scale: number) => ({
	width: px(width * scale),
	height: px(height * scale),
});

const meterWidth = px(268 * HUD_SCALE.meterWidth);

export const HUD = {
	gap: 16,
	gapTight: 10,
	viewportPad: 22,
	sideInset: 24,
	sideGap: 16,
	minSideGap: 10,
	fontSize: px(20 * HUD_SCALE.side),
	fontSizeWin: px(24 * HUD_SCALE.bottom),
	valueFontSize: px(24 * HUD_SCALE.side),
	valueFontSizeWin: px(30 * HUD_SCALE.bottom),
	button: scaled(110, 86, HUD_SCALE.bottom),
	sideButton: scaled(90, 74, HUD_SCALE.side),
	plusButton: {
		width: px((meterWidth - 10) / 2),
		height: px(80 * HUD_SCALE.plus),
	},
	meter: {
		width: meterWidth,
		height: px(64 * HUD_SCALE.side),
	},
	win: scaled(400, 78, HUD_SCALE.bottom),
} as const;

export const GARDEN_SLOT_BOARD_CONTEXT = 'gardenSlotBoard';

export type GardenSlotBoard = {
	x: number;
	y: number;
	width: number;
	height: number;
	scale?: number;
};

export type GardenSlotBoardApi = {
	get: () => GardenSlotBoard;
};

/** Matches BoardFrame timber + corner plates. */
export const GARDEN_SLOT_FRAME = {
	widthScale: 1.24,
	heightScale: 1.22,
	originX: 0.62,
	originY: 0.61,
	cornerWidthScale: 0.115,
	cornerHeightScale: 0.17,
	cornerOutsetX: 0.04,
	cornerOutsetY: 0.03,
	stroke: 18,
} as const;

export type HudPoint = { x: number; y: number };

type LayoutSpace = {
	x: number;
	y: number;
	width: number;
	height: number;
	scale: number;
};

export type GardenHudLayout = {
	win: HudPoint;
	auto: HudPoint;
	bet: HudPoint;
	turbo: HudPoint;
	menu: HudPoint;
	buy: HudPoint;
	balance: HudPoint;
	amountBet: HudPoint;
	dec: HudPoint;
	inc: HudPoint;
	freeSpin: HudPoint;
};

export const gardenButtonSizes = HUD.button;
export const gardenSideButtonSizes = HUD.sideButton;
export const gardenPlusButtonSizes = HUD.plusButton;

export const hudFontSize = (height: number, ratio = 0.26) => Math.round(height * ratio);

export const resolveButtonSizes = (
	sizes?: { width: number; height: number },
	fallback: { width: number; height: number } = { width: UI_BASE_SIZE, height: UI_BASE_SIZE },
) => ({
	width: sizes?.width ?? fallback.width,
	height: sizes?.height ?? fallback.height,
});

export const getGardenSlotFrameMetrics = (board: GardenSlotBoard) => {
	const frame = {
		x: board.x - board.width * GARDEN_SLOT_FRAME.originX,
		y: board.y - board.height * GARDEN_SLOT_FRAME.originY,
		width: board.width * GARDEN_SLOT_FRAME.widthScale,
		height: board.height * GARDEN_SLOT_FRAME.heightScale,
	};
	const well = {
		x: board.x - board.width * 0.5 - 8,
		y: board.y - board.height * 0.5 - 8,
		width: board.width + 16,
		height: board.height + 16,
	};
	const cornerWidth = frame.width * GARDEN_SLOT_FRAME.cornerWidthScale;
	const cornerHeight = frame.height * GARDEN_SLOT_FRAME.cornerHeightScale;
	const corners = [
		{
			x: frame.x - cornerWidth * GARDEN_SLOT_FRAME.cornerOutsetX,
			y: frame.y - cornerHeight * GARDEN_SLOT_FRAME.cornerOutsetY,
		},
		{
			x: frame.x + frame.width - cornerWidth * (1 - GARDEN_SLOT_FRAME.cornerOutsetX),
			y: frame.y - cornerHeight * GARDEN_SLOT_FRAME.cornerOutsetY,
		},
		{
			x: frame.x - cornerWidth * GARDEN_SLOT_FRAME.cornerOutsetX,
			y: frame.y + frame.height - cornerHeight * (1 - GARDEN_SLOT_FRAME.cornerOutsetY),
		},
		{
			x: frame.x + frame.width - cornerWidth * (1 - GARDEN_SLOT_FRAME.cornerOutsetX),
			y: frame.y + frame.height - cornerHeight * (1 - GARDEN_SLOT_FRAME.cornerOutsetY),
		},
	];
	const stroke = GARDEN_SLOT_FRAME.stroke * 0.5;
	const left = Math.min(frame.x, corners[0].x) - stroke;
	const top = Math.min(frame.y, corners[0].y) - stroke;
	const right = Math.max(frame.x + frame.width, corners[1].x + cornerWidth) + stroke;
	const bottom = Math.max(frame.y + frame.height, corners[2].y + cornerHeight) + stroke;

	return {
		frame: {
			...frame,
			beamX: well.x - frame.x,
			beamY: well.y - frame.y,
		},
		well,
		cornerWidth,
		cornerHeight,
		corners,
		outer: { x: left, y: top, width: right - left, height: bottom - top },
	};
};

const gameToHud = (game: LayoutSpace, hud: LayoutSpace, point: HudPoint): HudPoint => {
	const screenX = game.x + (point.x - game.width * 0.5) * game.scale;
	const screenY = game.y + (point.y - game.height * 0.5) * game.scale;
	return {
		x: hud.width * 0.5 + (screenX - hud.x) / hud.scale,
		y: hud.height * 0.5 + (screenY - hud.y) / hud.scale,
	};
};

export const getGardenHudLayout = ({
	hud: canvas,
	game,
	board,
}: {
	hud: LayoutSpace;
	game: LayoutSpace;
	board: GardenSlotBoard;
}): GardenHudLayout => {
	const { width: W, height: H } = canvas;
	const t = HUD;

	const buttonY = H - t.viewportPad - t.button.height * 0.5;
	const winY = buttonY - t.button.height * 0.5 - t.gap - t.win.height * 0.5;
	const hudTop = winY - t.win.height * 0.5;
	const pitch = t.button.width + t.gap;

	const slotScale = board.scale ?? 1;
	const slot = getGardenSlotFrameMetrics({
		x: 0,
		y: 0,
		width: board.width,
		height: board.height,
	});
	const outerLeft = gameToHud(game, canvas, {
		x: board.x + slot.outer.x * slotScale,
		y: board.y + slot.outer.y * slotScale,
	});
	const outerRight = gameToHud(game, canvas, {
		x: board.x + (slot.outer.x + slot.outer.width) * slotScale,
		y: board.y + (slot.outer.y + slot.outer.height) * slotScale,
	});
	const frameLeft = outerLeft.x;
	const frameRight = outerRight.x;
	const slotCx = (frameLeft + frameRight) * 0.5;
	const frameCenterY = (outerLeft.y + outerRight.y) * 0.5;

	const roomLeft = frameLeft - t.viewportPad;
	const roomRight = W - t.viewportPad - frameRight;
	const rightWidth = Math.max(t.meter.width, t.plusButton.width * 2 + t.gapTight);
	const maxGap = Math.min(roomLeft - t.sideButton.width, roomRight - rightWidth);
	const gap = Math.min(t.sideGap, Math.max(t.minSideGap, maxGap));
	const besideFrame = maxGap >= t.minSideGap;
	const leftPitch = t.sideButton.height + t.gapTight;
	const rightHeight = t.meter.height * 2 + t.plusButton.height + t.gapTight * 2;

	let leftX: number;
	let rightX: number;
	let railCenterY: number;

	if (besideFrame) {
		leftX = frameLeft - gap - t.sideButton.width * 0.5;
		rightX = frameRight + gap + rightWidth * 0.5;
		railCenterY = Math.min(frameCenterY, hudTop - rightHeight * 0.5 - t.gap);
	} else {
		leftX = t.sideInset + t.sideButton.width * 0.5;
		rightX = W - t.sideInset - rightWidth * 0.5;
		const boardBottomY = outerRight.y + t.gap;
		const band = Math.max(t.gap, hudTop - boardBottomY);
		railCenterY = boardBottomY + Math.min(band, rightHeight + t.gap * 2) * 0.4;
	}

	const rightTop = railCenterY - rightHeight * 0.5;
	const balanceY = rightTop + t.meter.height * 0.5;
	const amountBetY = balanceY + t.meter.height * 0.5 + t.gapTight + t.meter.height * 0.5;
	const plusRowY = amountBetY + t.meter.height * 0.5 + t.gapTight + t.plusButton.height * 0.5;
	const plusGap = t.plusButton.width * 0.5 + t.gapTight * 0.5;

	return {
		win: { x: slotCx, y: winY },
		auto: { x: slotCx - pitch, y: buttonY },
		bet: { x: slotCx, y: buttonY },
		turbo: { x: slotCx + pitch, y: buttonY },
		menu: { x: leftX, y: railCenterY - leftPitch * 0.5 },
		buy: { x: leftX, y: railCenterY + leftPitch * 0.5 },
		balance: { x: rightX, y: balanceY },
		amountBet: { x: rightX, y: amountBetY },
		dec: { x: rightX - plusGap, y: plusRowY },
		inc: { x: rightX + plusGap, y: plusRowY },
		freeSpin: { x: slotCx, y: hudTop - t.gap - t.meter.height * 0.5 },
	};
};
