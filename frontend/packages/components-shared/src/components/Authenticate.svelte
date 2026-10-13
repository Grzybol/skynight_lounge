<script lang="ts">
	import { onMount, type Snippet } from 'svelte';

	import { requestAuthenticate, requestReplay } from 'rgs-requests';
	import { stateUrlDerived, stateBet, stateConfig, stateModal, stateUi } from 'state-shared';
	import { API_AMOUNT_MULTIPLIER, MOST_USED_BET_INDEXES } from 'constants-shared/bet';

	type Props = { children: Snippet };

	const props: Props = $props();

	let authenticated = $state(false);
	/** Set when authenticate (or the replay fetch) fails: the game is not started, a clear message is shown. */
	let failure = $state<string | null>(null);

	const authenticate = async (): Promise<boolean> => {
		try {
			if (!stateUrlDerived.rgsUrl()) throw { error: 'ERR_VAL', message: 'rgs_url is missing' };
			const authenticateData = await requestAuthenticate({
				rgsUrl: stateUrlDerived.rgsUrl(),
				sessionID: stateUrlDerived.sessionID(),
				language: stateUrlDerived.lang(),
			});

			// error
			if (authenticateData?.error) throw authenticateData;

			// balance
			if (authenticateData?.balance) {
				// Example of authenticateData.balance
				// {
				// 		"amount": 10000000000000000,
				// 		"currency": "USD"
				// },
				stateBet.currency = authenticateData.balance.currency;
				stateBet.balanceAmount = authenticateData.balance.amount / API_AMOUNT_MULTIPLIER;
			}

			// config
			if (authenticateData?.config) {
				// Example of authenticateData.config
				// {
				// 	"gameID": "37_test-lines",
				// 	"minBet": 100000,
				// 	"maxBet": 1000000000,
				// 	"stepBet": 10000,
				// 	"defaultBetLevel": 1000000,
				// 	"betLevels": [100000, 200000, ..., 1000000000],
				// 	"betModes": {},
				// 	"jurisdiction": {
				// 			"socialCasino": false,
				// 			"disabledFullscreen": false,
				// 			"disabledTurbo": false,
				// 			"disabledSuperTurbo": false,
				// 			"disabledAutoplay": false,
				// 			"disabledSlamstop": false,
				// 			"disabledSpacebar": false,
				// 			"disabledBuyFeature": false,
				// 			"displayNetPosition": false,
				// 			"displayRTP": false,
				// 			"displaySessionTimer": false,
				// 			"minimumRoundDuration": 0
				// 	}
				// }
				stateConfig.jurisdiction = authenticateData?.config?.jurisdiction;
				stateConfig.betAmountOptions = (authenticateData.config?.betLevels || []).map(
					(level) => level / API_AMOUNT_MULTIPLIER,
				);
				stateConfig.betMenuOptions = stateConfig.betAmountOptions.filter((_, index) =>
					MOST_USED_BET_INDEXES.includes(index),
				);

				// The game opens on defaultBetLevel (an active round below overrides it with round.amount).
				const defaultLevel = authenticateData.config?.defaultBetLevel;
				if (typeof defaultLevel === 'number' && stateConfig.betAmountOptions.length > 0) {
					const wanted = defaultLevel / API_AMOUNT_MULTIPLIER;
					const options = stateConfig.betAmountOptions;
					const start = options.includes(wanted)
						? wanted
						: options.reduce((best, o) => (Math.abs(o - wanted) < Math.abs(best - wanted) ? o : best));
					stateBet.betAmount = start;
					stateBet.wageredBetAmount = start;
				}
			}

			// round
			if (authenticateData?.round) {
				// Example of authenticateData.round 
				// {
				// 	"betID": 62277967,
				// 	"amount": 1000000,
				// 	"payout": 33400000,
				// 	"payoutMultiplier": 33.4,
				// 	"active": true,
				// 	"state": [...],
				// 	"mode": "BONUS",
				// 	"event": null
				// }

				if(authenticateData.round?.state) {
					// @ts-ignore
					stateBet.betToResume =  authenticateData.round;
				}

				if(authenticateData.round?.amount) {
					const betAmountValue =
						authenticateData.round.amount > 0
							? authenticateData.round.amount / API_AMOUNT_MULTIPLIER
							: 0;
					stateBet.betAmount = betAmountValue;
					stateBet.wageredBetAmount = betAmountValue;
				}

				if (authenticateData.round?.mode) {
					stateBet.activeBetModeKey = authenticateData.round.mode;
				};
			}
			return true;
		} catch (error) {
			console.error(error);
			stateModal.modal = { name: 'error', error };
			failure = 'Could not connect to the game server or authenticate your session. Please check your link and reload.';
			return false;
		}
	};

	const handleReplay = async (): Promise<boolean> => {
		// Invalid or missing params must not break the replay.
		const currency = stateUrlDerived.currency();
		if (currency) {
			try {
				new Intl.NumberFormat('en-US', { style: 'currency', currency });
				stateBet.currency = currency;
			} catch {
				if (['XSC', 'XGC', 'XEC'].includes(currency)) stateBet.currency = currency;
			}
		}
		const amount = stateUrlDerived.amount() / API_AMOUNT_MULTIPLIER || 0;
		stateBet.betAmount = amount;
		stateBet.wageredBetAmount = amount;
		stateBet.activeBetModeKey = stateUrlDerived.mode();

		try {
			const data = await requestReplay({
				rgsUrl: stateUrlDerived.rgsUrl(),
				game: stateUrlDerived.game(),
				mode: stateUrlDerived.mode(),
				version: stateUrlDerived.version(),
				event: stateUrlDerived.event(),
			});

			// @ts-ignore
			if (!data || data.error || !data.state) throw data ?? { error: 'ERR_GEN' };

			// @ts-ignore
			stateBet.replayCostMultiplier = Number(data.costMultiplier) > 0 ? Number(data.costMultiplier) : 1;
			// @ts-ignore
			stateBet.betToResume = {
				...data,
				event: '0',
				active: true,
				mode: stateUrlDerived.mode(),
			};
			return true;
		} catch (error) {
			console.error(error);
			failure = 'This replay could not be loaded. Please check the link and try again.';
			return false;
		}
	};

	onMount(async () => {
		let ok: boolean;
		if (stateUrlDerived.replay()) {
			stateUi.config.mode = 'replay';
			ok = await handleReplay();
		} else {
			stateUi.config.mode = 'default';
			ok = await authenticate();
		}

		if (ok) authenticated = true;
	});
</script>

{#if authenticated}
	{@render props.children()}
{:else if failure}
	<div class="auth-failure" role="alert" data-test="auth-failure">
		<p>{failure}</p>
	</div>
{/if}

<style>
	.auth-failure {
		position: fixed;
		inset: 0;
		z-index: 9999;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
		box-sizing: border-box;
		background: #12060b;
		color: #f3e2b8;
		font-family: 'Luckiest Guy', Georgia, serif;
		font-size: 1.1rem;
		text-align: center;
	}

	.auth-failure p {
		max-width: 520px;
		margin: 0;
		line-height: 1.5;
	}
</style>
