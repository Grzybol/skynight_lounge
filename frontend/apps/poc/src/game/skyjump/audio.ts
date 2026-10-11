import type { SoundEffectName } from '../sound';

export const SKYJUMP_SFX = {
	button: 'sfx_btn_general',
	weatherReveal: 'sfx_anticipation_start',
	weatherLock: 'sfx_reel_stop_1',
	reelStart: 'sfx_btn_spin',
	reelSpin: 'sfx_anticipation',
	localMultiplier: 'sfx_multiplier_up',
	rareSymbol: 'sfx_scatter_reveal',
	slot6Suspense: 'sfx_anticipation',
	slot6Land: 'sfx_multiplier_landing',
	takeoff: 'sfx_fs_respins',
	windFlight: 'sfx_anticipation',
	distanceCount: 'tumble_win_1',
	payoutCount: 'tumble_win_2',
	profit: 'sfx_winlevel_standard',
	bigWin: 'sfx_youwon_panel',
	resultClose: 'sfx_winlevel_end',
	neutralStop: 'sfx_reel_stop_1',
} as const;

export const reelStopSfx = (reelIndex: number): SoundEffectName =>
	`sfx_reel_stop_${((reelIndex % 5) + 1) as 1 | 2 | 3 | 4 | 5}`;
