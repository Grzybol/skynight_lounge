import { createMulberry32 } from '../../frontend/apps/poc/src/game/skyjump/rng.ts';
import { resolveRound } from '../../frontend/apps/poc/src/game/skyjump/resolveRound.ts';
import { roundToBookEvents } from '../../frontend/apps/poc/src/game/skyjump/toBookEvents.ts';
import { getTablesForBetMode } from '../../frontend/apps/poc/src/game/skyjump/selectMode.ts';

const assert = (condition: unknown, message: string) => {
	if (!condition) throw new Error(message);
};

type Player = {
	weather: string | null;
	slots: number[];
	slot6: number | null;
	overlayOpen: boolean;
	amount: number;
	finalWin: boolean;
	errors: string[];
};

const resetPlayer = (): Player => ({
	weather: null,
	slots: [],
	slot6: null,
	overlayOpen: false,
	amount: 0,
	finalWin: false,
	errors: [],
});

const playBook = (events: Array<Record<string, unknown>>, player: Player) => {
	for (const event of events) {
		if (event.type === 'skyjumpWeather') {
			player.weather = String(event.weatherId);
			player.slots = [];
			player.slot6 = null;
			player.overlayOpen = false;
			player.amount = 0;
			player.finalWin = false;
		}
		if (event.type === 'skyjumpSlot') {
			const slotIndex = Number(event.slotIndex);
			player.slots.push(slotIndex);
			if (slotIndex === 6) player.slot6 = (event.finalMultiplier as { multiplier: number }).multiplier;
		}
		if (event.type === 'skyjumpResult') {
			if (player.slots.length !== 6) player.errors.push('overlay before six slots');
			if (player.slot6 == null) player.errors.push('overlay before slot 6 multiplier');
			player.overlayOpen = true;
		}
		if (event.type === 'setTotalWin') player.amount = Number(event.amount);
		if (event.type === 'finalWin') {
			if (player.amount !== Number(event.amount)) player.errors.push('finalWin amount mismatch');
			player.finalWin = true;
			player.overlayOpen = false;
		}
	}
};

const runSession = (label: string, rounds: number, turbo: boolean, seed: number) => {
	const random = createMulberry32(seed);
	const player = resetPlayer();
	let skippedFinal = 0;
	let duplicatePlay = 0;
	let inFlight = false;
	for (let i = 0; i < rounds; i += 1) {
		if (inFlight) duplicatePlay += 1;
		inFlight = true;
		const tables = getTablesForBetMode('BASE');
		const round = resolveRound({
			bet: 1,
			hillId: tables.hillId,
			multiplierTableId: tables.multiplierTableId,
			maxWin: tables.maxWin,
			random,
		});
		const events = roundToBookEvents(round);
		playBook(events as Array<Record<string, unknown>>, player);
		if (!player.finalWin) skippedFinal += 1;
		if (player.overlayOpen) player.errors.push(`overlay stuck after round ${i}`);
		if (player.slots.join(',') !== '1,2,3,4,5,6') player.errors.push(`slot order ${player.slots}`);
		inFlight = false;
		void turbo;
	}
	assert(skippedFinal === 0, `${label}: skipped finalWin ${skippedFinal}`);
	assert(duplicatePlay === 0, `${label}: overlapping plays ${duplicatePlay}`);
	assert(player.errors.length === 0, `${label}: ${player.errors.slice(0, 5).join('; ')}`);
	return { label, rounds, turbo, ok: true };
};

const rounds = Number(process.env.SKYJUMP_STRESS_ROUNDS ?? 100);
const normal = runSession('autoplay-normal', rounds, false, 17);
const turbo = runSession('autoplay-turbo', rounds, true, 23);
console.log('skyjump autoplay stress passed');
console.log({ normal, turbo });
