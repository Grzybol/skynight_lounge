import { Howl, Howler } from 'howler';
import { stateSoundDerived } from 'state-shared';

import { sound } from '../sound';
import { resolveGameAsset } from '../resolveGameAsset';

const BGM_BASE = resolveGameAsset('/assets/audio/skyjump/bgm/');
const SFX_BASE = resolveGameAsset('/assets/audio/skyjump/sfx/');

const sfx = {
	win: `${SFX_BASE}win.mp3`,
	bigWin: `${SFX_BASE}big-win.mp3`,
	skiing: `${SFX_BASE}skiing.mp3`,
	wind: `${SFX_BASE}wind.mp3`,
	lose: `${SFX_BASE}lose.mp3`,
	anticipation: `${SFX_BASE}anticipation.mp3`,
};

const BGM_GAIN = 0.72;
const ACTION_GAIN = 0.78;
const STING_GAIN = 1;
const STING_MAX_MS = 7000;
const BGM_WATCHDOG_MS = 2000;
const FALLBACK_BGM_FILES = ['relaxed_background_music1.mp3', 'relaxed_background_music2.mp3'];

let bgmTracks: string[] = FALLBACK_BGM_FILES.map((name) => `${BGM_BASE}${name}`);
let bgmEl: HTMLAudioElement | null = null;
let bgmWanted = false;
let bgmGen = 0;
let bgmBlocked = false;
let lastBgmIndex = -1;
let keepAliveBound = false;
let watchdogTimer = 0;
let skiing: Howl | null = null;
let wind: Howl | null = null;
let anticipation: Howl | null = null;
const stingers: Howl[] = [];
let tracksPromise: Promise<void> | null = null;

let stingEl: HTMLAudioElement | null = null;
let stingTimer = 0;
let stingGuard = 0;
let bgmDuck = 1;

const clampVolume = (value: number) => Math.min(1, Math.max(0, value));
const musicVolume = () => clampVolume(stateSoundDerived.volumeMusic() * BGM_GAIN);
const musicEnabled = () => stateSoundDerived.volumeMusic() > 0.001;
const sfxVolume = (gain = 1) => stateSoundDerived.volumeSoundEffect() * gain;

const unload = (howl: Howl | null) => {
	if (!howl) return;
	howl.stop();
	howl.unload();
};

const fadeOut = (howl: Howl | null, ms = 280) => {
	if (!howl) return;
	const from = howl.volume();
	if (ms <= 0 || from <= 0) {
		unload(howl);
		return;
	}
	howl.fade(from, 0, ms);
	howl.once('fade', () => unload(howl));
};

const FARMER_WIN_MUSIC = [
	'bgm_winlevel_big',
	'bgm_winlevel_superwin',
	'bgm_winlevel_mega',
	'bgm_winlevel_epic',
	'bgm_winlevel_max',
	'sfx_bigwin_coinloop',
] as const;

export const isFarmerWinSound = (name: string) =>
	(FARMER_WIN_MUSIC as readonly string[]).includes(name);

const stopFarmerWinMusic = () => {
	try {
		for (const name of FARMER_WIN_MUSIC) sound.stop({ name });
	} catch {
		/* sprite player may not be loaded yet */
	}
};

const playLoop = (src: string, volume: number) =>
	new Howl({
		src: [src],
		loop: true,
		volume,
		preload: true,
	});

const playOnce = (src: string, volume: number) => {
	const howl = new Howl({
		src: [src],
		loop: false,
		volume,
		preload: true,
	});
	stingers.push(howl);
	howl.once('end', () => {
		const index = stingers.indexOf(howl);
		if (index >= 0) stingers.splice(index, 1);
		howl.unload();
	});
	howl.play();
	return howl;
};

const toTrackUrls = (files: string[]) =>
	files
		.filter((name) => /\.(mp3|ogg|wav|m4a)$/i.test(name))
		.sort((left, right) => left.localeCompare(right))
		.map((name) => `${BGM_BASE}${name}`);

const loadBgmTracks = async () => {
	if (tracksPromise) return tracksPromise;
	tracksPromise = fetch(`${BGM_BASE}tracks.json`)
		.then((response) => (response.ok ? response.json() : []))
		.then((files: string[]) => {
			const next = toTrackUrls(Array.isArray(files) ? files : []);
			if (next.length) bgmTracks = next;
		})
		.catch(() => {
			/* keep fallback filenames so BGM can still start */
		});
	return tracksPromise;
};

const nextBgmIndex = () => {
	if (bgmTracks.length <= 1) return 0;
	let index = Math.floor(Math.random() * bgmTracks.length);
	if (index === lastBgmIndex) index = (index + 1) % bgmTracks.length;
	return index;
};

const disposeBgm = () => {
	const el = bgmEl;
	bgmEl = null;
	if (!el) return;
	el.onended = null;
	el.onerror = null;
	el.onpause = null;
	el.onstalled = null;
	try {
		el.pause();
	} catch {
		/* ignore */
	}
	el.removeAttribute('src');
	el.load();
	el.remove();
};

const bgmIsPlaying = () => !!bgmEl && !bgmEl.paused && !bgmEl.ended;

const canUseBgm = () => {
	if (!bgmWanted || !musicEnabled()) return false;
	if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return false;
	return true;
};

const applyBgmVolume = () => {
	if (bgmEl) bgmEl.volume = clampVolume(musicVolume() * bgmDuck);
	if (stingEl) stingEl.volume = musicVolume();
};

const disposeSting = () => {
	const el = stingEl;
	stingEl = null;
	bgmDuck = 1;
	if (stingTimer) {
		window.clearTimeout(stingTimer);
		stingTimer = 0;
	}
	if (stingGuard) {
		window.clearInterval(stingGuard);
		stingGuard = 0;
	}
	if (el) {
		el.onended = null;
		el.onerror = null;
		el.ontimeupdate = null;
		el.loop = false;
		try {
			el.pause();
		} catch {
			/* ignore */
		}
		el.removeAttribute('src');
		el.load();
		el.remove();
	}
	applyBgmVolume();
};

const playCelebrationSting = (src: string) => {
	disposeSting();
	stopFarmerWinMusic();
	if (!musicEnabled()) return;
	const el = new Audio();
	el.preload = 'auto';
	el.playsInline = true;
	el.loop = false;
	el.removeAttribute('loop');
	el.volume = musicVolume();
	el.src = src;
	el.setAttribute('data-skyjump-sting', 'true');
	el.style.display = 'none';
	document.body.appendChild(el);
	stingEl = el;
	bgmDuck = 0.16;
	applyBgmVolume();
	el.onended = () => {
		if (stingEl === el) disposeSting();
	};
	el.onerror = () => {
		if (stingEl === el) disposeSting();
	};
	el.ontimeupdate = () => {
		if (el.loop) el.loop = false;
	};
	stingTimer = window.setTimeout(() => {
		if (stingEl === el) disposeSting();
	}, STING_MAX_MS);
	stingGuard = window.setInterval(() => {
		stopFarmerWinMusic();
		if (el.loop) el.loop = false;
		if (stingEl === el) applyBgmVolume();
	}, 250);
	const playResult = el.play();
	if (playResult && typeof playResult.then === 'function') {
		void playResult.catch(() => {
			if (stingEl === el) disposeSting();
		});
	}
};

const playBgmElement = (el: HTMLAudioElement) => {
	applyBgmVolume();
	const playResult = el.play();
	if (playResult && typeof playResult.then === 'function') {
		void playResult
			.then(() => {
				bgmBlocked = false;
			})
			.catch((error: unknown) => {
				const name =
					error && typeof error === 'object' && 'name' in error ? String(error.name) : '';
				if (name === 'NotAllowedError') bgmBlocked = true;
			});
	}
};

const playBgmTrack = () => {
	if (!canUseBgm() || !bgmTracks.length) return;

	const gen = ++bgmGen;
	disposeBgm();
	lastBgmIndex = nextBgmIndex();

	const el = new Audio();
	el.preload = 'auto';
	el.playsInline = true;
	el.loop = bgmTracks.length === 1;
	el.volume = musicVolume();
	el.src = bgmTracks[lastBgmIndex];
	el.setAttribute('data-skyjump-bgm', 'true');
	el.style.display = 'none';
	document.body.appendChild(el);
	bgmEl = el;

	el.onended = () => {
		if (gen !== bgmGen || !bgmWanted) return;
		playBgmTrack();
	};
	el.onerror = () => {
		if (gen !== bgmGen || !bgmWanted || bgmBlocked) return;
		window.setTimeout(() => {
			if (gen === bgmGen && bgmWanted) playBgmTrack();
		}, 600);
	};

	playBgmElement(el);
};

const ensureBgmPlaying = () => {
	if (!canUseBgm()) return;
	if (!bgmTracks.length) {
		void loadBgmTracks().then(() => {
			if (canUseBgm()) ensureBgmPlaying();
		});
		return;
	}
	if (bgmBlocked) return;

	if (bgmIsPlaying()) {
		applyBgmVolume();
		return;
	}

	if (bgmEl && bgmEl.src && !bgmEl.ended && bgmEl.error == null) {
		playBgmElement(bgmEl);
		return;
	}

	playBgmTrack();
};

const resumeHowlerContext = () => {
	try {
		void Howler.ctx?.resume?.();
	} catch {
		/* Howler may not have a context yet */
	}
};

const bindBgmKeepAlive = () => {
	if (keepAliveBound || typeof window === 'undefined') return;
	keepAliveBound = true;

	const onGesture = () => {
		bgmBlocked = false;
		resumeHowlerContext();
		ensureBgmPlaying();
	};

	window.addEventListener('pointerdown', onGesture, true);
	window.addEventListener('keydown', onGesture, true);
	window.addEventListener('touchend', onGesture, true);

	document.addEventListener('visibilitychange', () => {
		if (document.visibilityState === 'visible') {
			bgmBlocked = false;
			resumeHowlerContext();
			ensureBgmPlaying();
			return;
		}
		if (bgmEl && !bgmEl.paused) {
			try {
				bgmEl.pause();
			} catch {
				/* ignore */
			}
		}
	});

	watchdogTimer = window.setInterval(() => {
		if (bgmBlocked) return;
		ensureBgmPlaying();
	}, BGM_WATCHDOG_MS);
};

export const startSkyJumpBgm = () => {
	bgmWanted = true;
	bindBgmKeepAlive();
	if (bgmTracks.length) {
		ensureBgmPlaying();
		void loadBgmTracks();
		return;
	}
	void loadBgmTracks().then(() => {
		if (bgmWanted) ensureBgmPlaying();
	});
};

export const stopSkyJumpBgm = () => {
	bgmWanted = false;
	bgmGen += 1;
	disposeBgm();
};

export const startJumpActionBed = () => {
	if (skiing?.playing() || wind?.playing()) return;
	unload(skiing);
	unload(wind);
	skiing = playLoop(sfx.skiing, sfxVolume(ACTION_GAIN));
	wind = playLoop(sfx.wind, sfxVolume(ACTION_GAIN * 0.85));
	skiing.play();
	wind.play();
};

export const stopJumpActionBed = () => {
	fadeOut(skiing, 220);
	fadeOut(wind, 220);
	skiing = null;
	wind = null;
};

export const startResultAnticipation = () => {
	if (anticipation?.playing()) return;
	unload(anticipation);
	anticipation = playLoop(sfx.anticipation, sfxVolume(0.9));
	anticipation.play();
};

export const stopResultAnticipation = () => {
	fadeOut(anticipation, 160);
	anticipation = null;
};

export const playResultSting = (result: {
	isPayHit?: boolean;
	isProfit?: boolean;
	amount?: number;
	finalMultiplier?: number;
	returnMultiplier?: number;
}) => {
	stopResultAnticipation();
	stopFarmerWinMusic();
	disposeSting();
	const miss = !result.isPayHit || (result.amount ?? 0) <= 0;
	if (miss) {
		playOnce(sfx.lose, sfxVolume(STING_GAIN));
		return;
	}
	playOnce(sfx.win, sfxVolume(STING_GAIN));
	const punch = Math.max(result.finalMultiplier ?? 0, result.returnMultiplier ?? 0);
	if (result.isProfit && punch >= 5) {
		playCelebrationSting(sfx.bigWin);
	}
};

export const stopSkyJumpRoundAudio = () => {
	stopJumpActionBed();
	stopResultAnticipation();
	stopFarmerWinMusic();
	disposeSting();
	for (const howl of stingers.splice(0)) unload(howl);
};

export const syncSkyJumpAudioVolumes = () => {
	if (!musicEnabled()) {
		if (bgmEl && !bgmEl.paused) {
			try {
				bgmEl.pause();
			} catch {
				/* ignore */
			}
		}
		if (stingEl) stingEl.volume = 0;
	} else if (bgmWanted) {
		bgmBlocked = false;
		ensureBgmPlaying();
	}
	applyBgmVolume();
	skiing?.volume(sfxVolume(ACTION_GAIN));
	wind?.volume(sfxVolume(ACTION_GAIN * 0.85));
	anticipation?.volume(sfxVolume(0.9));
	for (const howl of stingers) howl.volume(sfxVolume(STING_GAIN));
};

/** Soft temporary BGM duck for rare V2 feature/jackpot SFX (existing mixer only). */
export const softDuckSkyJumpBgm = (factor = 0.4, holdMs = 1000) => {
	if (!musicEnabled()) return;
	bgmDuck = Math.max(0.12, Math.min(1, factor));
	applyBgmVolume();
	window.setTimeout(
		() => {
			bgmDuck = 1;
			applyBgmVolume();
		},
		Math.max(200, holdMs),
	);
};

if (typeof window !== 'undefined') {
	void loadBgmTracks();
}
