/** Independently audited mathVersion 3 freeze. Do not retune these values. */

export const FROZEN_MATH_VERSION = 3;
export const FROZEN_EVENT_SCHEMA_VERSION = 1;
export const FROZEN_CONFIG_SHA256 =
	'321dedd2d88259b37b7d779d000ddfe5a154bc1a9512a1dceb67830f91eefd33';

/** Exact enumerator RTP = E[finalWinX] / costMultiplier. */
export const FROZEN_RTP = {
	BASE: 0.96934449945,
	LARGE_HILL: 0.97086611908,
	SKI_FLYING: 0.97179578549,
	MULT_10_100: 0.96808086909,
	MULT_20_200: 0.96927221614,
} as const;

export const FROZEN_MODE_MAX_WIN = {
	BASE: 500,
	LARGE_HILL: 4000,
	SKI_FLYING: 25000,
	MULT_10_100: 6000,
	MULT_20_200: 12000,
} as const;

export const FROZEN_RTP_ABS_TOLERANCE = 5e-11;
