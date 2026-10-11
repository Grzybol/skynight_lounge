export type V2SymbolId = string;

export type V2Board = V2SymbolId[][];

export type V2CellPosition = {
	reel: number;
	row: number;
};

export type V2LineWin = {
	paylineId: number;
	symbolId: V2SymbolId;
	matchCount: 3 | 4 | 5;
	positions: V2CellPosition[];
	payoutX: number;
};

export type V2EvaluateResult = {
	wins: V2LineWin[];
	lineWinX: number;
};

export type V2PlaceholderShape =
	| 'triangle'
	| 'diamond'
	| 'hexagon'
	| 'parallelogram'
	| 'oval'
	| 'rounded'
	| 'chevron'
	| 'circle'
	| 'rect'
	| 'pentagon';

export type V2Placeholder = {
	id: string;
	label: string;
	fill: string;
	ink: string;
	shape: V2PlaceholderShape;
};
