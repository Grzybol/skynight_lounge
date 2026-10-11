<script lang="ts" module>
	import { sound, type MusicName, type SoundEffectName, type SoundName } from '../game/sound';

	export type EmitterEventSound =
		| { type: 'soundMusic'; name: MusicName }
		| { type: 'soundOnce'; name: SoundEffectName; forcePlay?: boolean }
		| { type: 'soundLoop'; name: SoundEffectName }
		| { type: 'soundStop'; name: SoundName }
		| { type: 'soundFade'; name: SoundName; from: number; to: number; duration: number }
		| { type: 'soundScatterCounterIncrease' }
		| { type: 'soundScatterCounterClear' };
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { stateSound } from 'state-shared';

	import { getContext } from '../game/context';
	import {
		isFarmerWinSound,
		startSkyJumpBgm,
		syncSkyJumpAudioVolumes,
	} from '../game/skyjump/skyjumpAudio';
	import { playV2AudioHook } from '../game/skyjump_v2/audio';

	const context = getContext();

	context.eventEmitter.subscribeOnMount({
		// ui
		soundBetMode: async () => {
			startSkyJumpBgm();
		},
		soundPressGeneral: () => {
			playV2AudioHook('UI_CLICK');
			startSkyJumpBgm();
		},
		soundPressBet: () => {
			playV2AudioHook('BET_CONFIRM');
			startSkyJumpBgm();
		},
		soundPressBetIncrease: () => {
			playV2AudioHook('BET_INCREASE');
			startSkyJumpBgm();
		},
		soundPressBetDecrease: () => {
			playV2AudioHook('BET_DECREASE');
			startSkyJumpBgm();
		},
		soundUiHover: () => {
			playV2AudioHook('UI_HOVER');
		},
		// scatterCounter
		soundScatterCounterIncrease: () => (context.stateGame.scatterCounter = context.stateGame.scatterCounter + 1), // prettier-ignore
		soundScatterCounterClear: () => (context.stateGame.scatterCounter = 0),
		// game
		soundMusic: ({ name }) => {
			if (isFarmerWinSound(name)) return;
			sound.players.music.play({ name });
		},
		soundLoop: ({ name }) => {
			if (isFarmerWinSound(name)) return;
			sound.players.loop.play({ name });
		},
		soundOnce: ({ name, forcePlay }) => sound.players.once.play({ name, forcePlay }),
		soundStop: ({ name }) => sound.stop({ name }),
		soundFade: async ({ name, duration, from, to }) => await sound.fade({ name, duration, from, to }), // prettier-ignore
	});

	onMount(() => {
		startSkyJumpBgm();
	});

	$effect(() => {
		stateSound.volumeValueMaster;
		stateSound.volumeValueMusic;
		stateSound.volumeValueSoundEffect;
		syncSkyJumpAudioVolumes();
	});
</script>
