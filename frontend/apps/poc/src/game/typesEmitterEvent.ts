import type { EmitterEventSound } from '../components/Sound.svelte';
import type { EmitterEventTransition } from '../components/Transition.svelte';
import type { EmitterEventSkyJump } from '../components/skyjump/skyjumpEvents';

export type EmitterEventGame = EmitterEventSound | EmitterEventTransition | EmitterEventSkyJump;
