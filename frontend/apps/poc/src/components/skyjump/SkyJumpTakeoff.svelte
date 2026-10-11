<script lang="ts">
	import { waitForTimeout } from 'utils-shared/wait';

	import { getContext } from '../../game/context';

	const context = getContext();
	let active = $state(false);
	let turbo = $state(false);
	let gen = 0;

	context.eventEmitter.subscribeOnMount({
		skyjumpTakeoffShow: async ({ timings, catchUp }) => {
			const token = ++gen;
			if (catchUp) return;
			turbo = timings.id === 'turbo';
			active = true;
			await waitForTimeout(timings.takeoffMs);
			if (token === gen) active = false;
		},
		skyjumpResetBoard: () => {
			gen += 1;
			active = false;
		},
	});
</script>

{#if active && context.stateGame.screen === 'play'}
	<div class="takeoff" class:turbo>
		<div class="push"></div>
		<div class="whoosh"></div>
		<div class="whoosh late"></div>
	</div>
{/if}

<style>
	.takeoff {
		position: absolute;
		inset: 0;
		z-index: 12;
		pointer-events: none;
		overflow: hidden;
	}

	.push {
		position: absolute;
		inset: 0;
		background: radial-gradient(ellipse at 50% 62%, rgba(168, 230, 255, 0.12), transparent 52%);
		animation: push 0.45s cubic-bezier(0.16, 0.84, 0.32, 1);
	}

	.takeoff.turbo .push,
	.takeoff.turbo .whoosh {
		animation-duration: 0.12s;
	}

	.whoosh {
		position: absolute;
		inset: 18% 0 38%;
		background: linear-gradient(90deg, transparent, rgba(158, 225, 255, 0.2), transparent);
		transform: skewX(-18deg);
		animation: streak 0.45s ease-out;
	}

	.whoosh.late {
		inset: 28% 0 32%;
		animation-delay: 0.05s;
		opacity: 0.7;
	}

	@keyframes push {
		from {
			transform: scale(1);
			opacity: 0.25;
		}
		to {
			transform: scale(1.14);
			opacity: 0;
		}
	}

	@keyframes streak {
		from {
			opacity: 0;
			transform: translateX(-18%) skewX(-18deg);
		}
		to {
			opacity: 0.85;
			transform: translateX(22%) skewX(-18deg);
		}
	}
</style>
