/**
 * Player-facing description of each buy-in room, shown on the buy confirmation tile.
 * Mechanics follow the Info screen (Free Spins / Bonus Rooms) and the frozen math config.
 */
const SPINS =
	'You start with 10 Free Spins (up to 40 in one round). During the bonus, 3 or more invitations on a spin’s opening board add +5 spins and step the room up on the next spin.';

export const MODE_BLURBS: Record<string, string> = {
	LARGE_HILL: `The Velvet Room: more Concierge action and the standard feature chain on every spin. ${SPINS}`,
	SKI_FLYING: `The Gold Room: the Concierge’s picks can stick as Mystery Gift targets and carry over to later spins, on top of everything in the Velvet Room. ${SPINS}`,
	WORLD_CUP: `The Diamond Lounge: the same lasting Mystery Gift targets as the Gold Room, plus a guaranteed VIP Upgrade once during the bonus. ${SPINS}`,
	PERFECT_V: `The Midnight Suite: the highest intensity. The Concierge visits every spin, a VIP Upgrade is guaranteed and a lasting lounge multiplier builds through the bonus. ${SPINS}`,
};
