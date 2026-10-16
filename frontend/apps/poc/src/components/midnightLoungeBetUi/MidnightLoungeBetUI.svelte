<script lang="ts">
	import { Tween } from 'svelte/motion';
	import {
		stateBet,
		stateBetDerived,
		stateConfig,
		stateModal,
		stateSound,
		stateUi,
		stateUrlDerived,
	} from 'state-shared';
	import { OnHotkey } from 'components-shared';
	import { bookEventAmountToCurrencyString, numberToCurrencyString } from 'utils-shared/amount';

	import { getContext } from '../../game/context';
	import { loungeShown } from '../../game/midnightLoungeTheme';
	import { resolveGameAsset } from '../../game/resolveGameAsset';
	import { i18nDerived } from '../../i18n/i18nDerived';
	import {
		betFromIdle,
		closeMenu,
		openBetMenu,
		openMenu,
		openPaytable,
		openRules,
		openSettings,
		pickLanguage,
		pressAuto,
		pressBuy,
		pressTurbo,
		stepBet,
		stopRound,
		toggleSound,
	} from './betUiActions';

	const context = getContext();
	const balanceTween = new Tween(stateBet.balanceAmount);
	const winTween = new Tween(stateBet.winBookEventAmount);

	let stopDisabled = $state(false);

	const idle = $derived(context.stateXstateDerived.isIdle());
	const options = $derived([...stateConfig.betAmountOptions].sort((a, b) => a - b));
	const smallest = $derived(options[0]);
	const biggest = $derived(options[options.length - 1]);
	const autoOn = $derived(stateBetDerived.hasAutoBetCounter());
	const buyActive = $derived(stateBetDerived.activeBetMode()?.type === 'activate');
	const soundOff = $derived(stateSound.volumeValueMaster === 0);
	const stopMode = $derived(!idle);
	const spinKey = $derived.by(() => {
		if (idle) return stateBetDerived.isBetCostAvailable() ? 'spin_default' : 'spin_disabled';
		if (stopDisabled) return 'stop_disabled';
		if (autoOn) return 'stop_default';
		if (stateBet.isTurbo) return 'stop_disabled';
		return 'stop_default';
	});
	const spinDisabled = $derived(idle && (!stateBetDerived.isBetCostAvailable() || stateBet.overlayOpen));
	const spaceLocked = $derived(idle && (spinDisabled || stateBet.overlayOpen));
	const autoDisabled = $derived(
		stateBet.isSpaceHold || !stateBetDerived.isBetCostAvailable() || (!idle && !autoOn),
	);
	const turboDisabled = $derived(stateBet.isSpaceHold || stateBet.overlayOpen);
	const stepLocked = $derived(!idle);
	const autoBadge = $derived(
		!autoOn ? '' : stateBet.autoSpinsCounter === Infinity ? '∞' : String(stateBet.autoSpinsCounter),
	);

	$effect(() => {
		balanceTween.set(stateBet.balanceAmount);
	});

	$effect(() => {
		winTween.set(stateBet.winBookEventAmount, { duration: stateBet.isTurbo ? 80 : 400 });
	});

	context.eventEmitter.subscribeOnMount({
		stopButtonClick: () => {
			stopDisabled = true;
			if (stateBet.overlayOpen) return;
			stateBetDerived.updateIsTurbo(true, { persistent: false });
		},
		stopButtonEnable: () => {
			stopDisabled = false;
			if (stateBet.overlayOpen) return;
			stateBetDerived.updateIsTurbo(false, { persistent: false });
		},
	});

	const onSpin = () => {
		context.eventEmitter.broadcast({ type: 'soundPressBet' });
		if (idle) {
			if (stateBet.overlayOpen) return;
			betFromIdle(context.eventEmitter);
			return;
		}
		stopRound(context.eventEmitter, stopDisabled);
	};

	/** Every BetUI button plays the hover sound on pointer enter (disabled ones stay silent). */
	const hover = (event: PointerEvent) => {
		const target = event.currentTarget as HTMLButtonElement | null;
		if (target?.disabled) return;
		context.eventEmitter.broadcast({ type: 'soundUiHover' });
	};

	/** Big win and above: the whole BetUI is unavailable (inert) until the celebration ends. */
	const celebrating = $derived(context.stateGame.celebrationActive);
	const isReplay = $derived(stateUi.config.mode === 'replay');
	const socialMode = stateUrlDerived.social();
	/** Idle, but the balance cannot cover bet x mode cost: the player is told why the spin is unavailable. */
	const insufficient = $derived(!isReplay && idle && !stateBetDerived.isBetCostAvailable());
	/**
	 * HUD artwork (betui2/*.png). `b` is the visible bounds inside the file; every control is placed by its
	 * visible rectangle on the 1280x720 stage, so the artwork keeps its aspect ratio.
	 */
	const HUD = {
		balance: { w: 2172, h: 724, b: [87, 98, 2082, 635] },
		bet_background: { w: 2172, h: 724, b: [100, 98, 2069, 623] },
		minus: { w: 1254, h: 1254, b: [51, 53, 1205, 1193] },
		plus: { w: 1254, h: 1254, b: [43, 57, 1215, 1203] },
		menu: { w: 1254, h: 1254, b: [109, 208, 1145, 1052] },
		autospin: { w: 2172, h: 724, b: [164, 80, 2005, 647] },
		turbo: { w: 2172, h: 724, b: [89, 52, 2064, 667] },
		bonus: { w: 2172, h: 724, b: [101, 102, 2066, 622] },
		spin: { w: 1254, h: 1254, b: [18, 23, 1236, 1229] },
		stop: { w: 1254, h: 1254, b: [18, 20, 1236, 1229] },
	} as const;
	type HudKey = keyof typeof HUD;
	type HudBox = { key: HudKey; x: number; y: number; w: number; h: number; kx: number; ky: number };

	/** Rect on the stage from the visible width (height by aspect, or given to stretch the art). */
	const box = (key: HudKey, x: number, y: number, w: number, h?: number): HudBox => {
		const a = HUD[key];
		const kx = w / (a.b[2] - a.b[0]);
		const ky = h === undefined ? kx : h / (a.b[3] - a.b[1]);
		return { key, x, y, w, h: (a.b[3] - a.b[1]) * ky, kx, ky };
	};
	const imgStyle = (r: HudBox) => {
		const a = HUD[r.key];
		return `left:${-a.b[0] * r.kx}px;top:${-a.b[1] * r.ky}px;width:${a.w * r.kx}px;height:${a.h * r.ky}px;`;
	};
	const boxStyle = (r: HudBox) => `left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px;`;
	/** A point of the artwork (file px) on the stage. */
	const at = (r: HudBox, fx: number, fy: number) => {
		const a = HUD[r.key];
		return `left:${r.x + (fx - a.b[0]) * r.kx}px;top:${r.y + (fy - a.b[1]) * r.ky}px;`;
	};
	/** A point of the artwork (file px) relative to the control's own box, for labels that live inside the button. */
	const inBox = (r: HudBox, fx: number, fy: number) => {
		const a = HUD[r.key];
		return `left:${(fx - a.b[0]) * r.kx}px;top:${(fy - a.b[1]) * r.ky}px;`;
	};
	const hudUrl = (key: HudKey) => resolveGameAsset(`assets/midnight-lounge/ui/betui2/${key}.png`);

	// Layout (stage px, from new_betui_preview.png): bottom-left bonus + menu/balance, bottom-right turbo, auto, bet, spin.
	const L = (() => {
		// Every control is 10 % smaller than the first pass and 5 % than the second. Each cluster shrinks towards its own
		// screen edge: bonus / balance / menu towards the bottom-left, bet / spin towards the bottom-right, the WIN plate
		// towards the bottom centre. TURBO and AUTO stand in the bottom strip, in the gaps between balance / WIN / bet.
		const K = 0.855;
		const toward = (ax: number, x: number, y: number) => [ax + (x - ax) * K, 720 + (y - 720) * K] as const;
		// Bottom line shared by the lowest opaque pixels of every plate: 719 on the 720 px stage.
		const BOTTOM = 719;
		const spin0 = box('spin', ...toward(1280, 1082, 501), 193 * K);
		const dyR = BOTTOM - (spin0.y + spin0.h);
		const spin = box('spin', spin0.x, spin0.y + dyR, 193 * K);
		/** SPIN is a disc: the BET plate keeps a few transparent pixels from its curve (measured at the closest point). */
		const spinCx = spin.x + spin.w / 2;
		const spinCy = spin.y + spin.h / 2;
		const spinR = spin.w / 2;
		const GAP = 3;
		const leftOfSpin = (w: number, y: number, h: number) => {
			const nearestY = Math.min(Math.max(spinCy, y), y + h);
			const dy = Math.abs(spinCy - nearestY);
			const right = spinCx - Math.sqrt((spinR + GAP) ** 2 - dy ** 2);
			return right - w;
		};
		// BET plate and its content 10 % smaller, twice.
		const betOld = box('bet_background', ...toward(1280, 804, 614), 286 * K);
		const betW = betOld.w * 0.9 * 0.9;
		const betH = box('bet_background', 0, 0, betW).h;
		const betY = BOTTOM - betH;
		const bet = box('bet_background', leftOfSpin(betW, betY, betH), betY, betW);
		// +/- circles: another 5 % smaller; their centres keep their distance from the plate edge.
		const d = bet.w * 0.194 * 0.95 * 0.95;
		const m = bet.w * 0.165 - d / 2;
		const cy = bet.y + (bet.h - d) / 2;
		// Left part: the balance plate's bottom is on the shared line, the bonus plate moves with it.
		const balance0 = box('balance', ...toward(0, 6, 606), 347 * K);
		const dyL = BOTTOM - (balance0.y + balance0.h);
		const lowered = (r: HudBox): HudBox => ({ ...r, y: r.y + dyL });
		const balance = lowered(balance0);
		// The menu button sits exactly on the balance plate's round left end (same centre) and covers it.
		const ended = { x: 87 + (597 - 87) / 2, y: 123 + (628 - 123) / 2 };
		const endCx = balance.x + (ended.x - HUD.balance.b[0]) * balance.kx;
		const endCy = balance.y + (ended.y - HUD.balance.b[1]) * balance.ky;
		const menuW = 78;
		const menuH = 76;
		const menu = box('menu', endCx - menuW / 2, endCy - menuH / 2, menuW, menuH);
		const bonus0 = box('bonus', ...toward(0, 9, 543), 207 * K);
		// WIN sits exactly under the middle of the slot (stage x = 640), 10 % lower and 15 % longer than the plain plate.
		const winBase = box('bet_background', 0, 0, 261 * K);
		const winW = winBase.w * 1.15;
		const winH = winBase.h * 0.9;
		const win = box('bet_background', 640 - winW / 2, BOTTOM - winH, winW, winH);
		// TURBO between balance and WIN, AUTO between WIN and BET, both on the shared bottom line.
		const turboBase = box('turbo', 0, 0, 154 * K);
		const autoBase = box('autospin', 0, 0, 152 * K);
		const turboCx = (balance.x + balance.w + win.x) / 2;
		const autoCx = (win.x + win.w + bet.x) / 2;
		return {
			bonus: lowered(bonus0),
			balance,
			menu,
			win,
			bet,
			minus: box('minus', bet.x + m, cy, d),
			plus: box('plus', bet.x + bet.w - m - d, cy, d),
			turbo: box('turbo', turboCx - turboBase.w / 2, BOTTOM - turboBase.h, 154 * K),
			auto: box('autospin', autoCx - autoBase.w / 2, BOTTOM - autoBase.h, 152 * K),
			spin,
		};
	})();
	/** The HUD is laid out on a 1280x720 stage and scaled to the play area like the rest of the scene. */
	let hudRoot = $state<HTMLDivElement | null>(null);
	let hudFrame = $state('left:0px;top:0px;transform:scale(1);');
	$effect(() => {
		const el = hudRoot;
		if (!el) return;
		const viewport = el.closest('.skyjump-viewport');
		if (!(viewport instanceof HTMLElement)) return;
		const place = () => {
			const css = getComputedStyle(viewport);
			const read = (name: string) => parseFloat(css.getPropertyValue(name));
			const left = read('--play-left');
			const top = read('--play-top');
			const width = read('--play-width');
			if (![left, top, width].every(Number.isFinite) || width <= 0) return;
			hudFrame = `left:${left}px;top:${top}px;transform:scale(${width / 1280});`;
		};
		place();
		const observer = new ResizeObserver(place);
		observer.observe(viewport);
		const kick = requestAnimationFrame(place);
		return () => {
			cancelAnimationFrame(kick);
			observer.disconnect();
		};
	});
	const autoWord = $derived(i18nDerived.autoSpin().split(' ')[0]);
	const spinBox = $derived(box(stopMode ? 'stop' : 'spin', L.spin.x, L.spin.y, L.spin.w));

	const spinLabel = $derived(stopMode ? i18nDerived.stop() : 'SPIN');
</script>

{#if context.stateGame.screen === 'play'}
	<div
		class="ml-betui"
		class:celebrating={celebrating}
		inert={celebrating}
		data-test="ml-betui"
	>
		{#if stateUi.menuOpen}
			<button
				type="button"
				class="backdrop"
				aria-label={i18nDerived.menuExit()}
				onclick={() => closeMenu(context.eventEmitter, false)}
			></button>
		{/if}

		{#if isReplay}
			<!-- Replay: no betting controls, no route into real play. Shows what was played and a way to run it again. -->
			<div class="bar replay-bar" data-test="ml-replay-bar">
				<span class="bar-line top"></span>
				<span class="bar-line bottom"></span>
				<div class="panel replay-info" data-test="ml-replay-info">
					<span class="text">
						<span class="kicker">{socialMode ? 'PLAY AMOUNT' : 'BET'}</span>
						<span class="value">{numberToCurrencyString(stateBet.betAmount)}</span>
					</span>
					{#if stateBet.replayCostMultiplier > 1}
						<span class="text">
							<span class="kicker">{loungeShown(stateBet.activeBetModeKey, stateBet.activeBetModeKey)} · REAL COST</span>
							<span class="value">
								{stateBet.replayCostMultiplier}× · {numberToCurrencyString(
									stateBet.betAmount * stateBet.replayCostMultiplier,
								)}
							</span>
						</span>
					{/if}
				</div>
				<div class="panel win replay-win" aria-label={i18nDerived.win()}>
					<span class="kicker">{i18nDerived.win()}</span>
					<span class="value big">{bookEventAmountToCurrencyString(winTween.current)}</span>
				</div>
				<button
					type="button"
					class="tile action push replay-again"
					data-test="ml-replay-again"
					onpointerenter={hover}
					onclick={() => window.location.reload()}
				>
					<span class="cap">REPLAY</span>
				</button>
			</div>
		{:else}
		<OnHotkey
				hotkey="Space"
				disabled={spaceLocked || celebrating || stateUi.menuOpen || Boolean(stateModal.modal)}
				onpress={() => {
					// Space places a bet when betting is available; mid-round it does nothing.
					if (idle) onSpin();
				}}
			/>

		<div class="hud" data-test="ml-hud" bind:this={hudRoot} style={hudFrame}>
			{#if insufficient}
				<span class="funds-note" role="status" data-test="ml-insufficient"
					>{socialMode ? 'NOT ENOUGH BALANCE FOR THIS PLAY' : 'INSUFFICIENT FUNDS FOR THIS BET'}</span
				>
			{/if}

			<!-- Bonus (buy bonus) -->
			<button
				type="button"
				class="hud-btn"
				class:active={buyActive}
				style={boxStyle(L.bonus)}
				aria-label={buyActive ? i18nDerived.disable() : i18nDerived.buyBonus()}
				aria-pressed={buyActive}
				disabled={!idle}
				onpointerenter={hover}
				onclick={() => pressBuy(context.eventEmitter)}
			>
				<img src={hudUrl('bonus')} style={imgStyle(L.bonus)} alt="" draggable="false" fetchpriority="low" />
				<span class="hud-label bonus-label" style={inBox(L.bonus, 1250, 360)}>BONUS</span>
			</button>

			<!-- Menu + balance plate -->
			<div class="hud-plate-frame" style={boxStyle(L.balance)} aria-hidden="true">
				<img src={hudUrl('balance')} style={imgStyle(L.balance)} alt="" draggable="false" fetchpriority="low" />
			</div>
			<button
				type="button"
				class="hud-btn"
				class:active={stateUi.menuOpen}
				style={boxStyle(L.menu)}
				aria-label={stateUi.menuOpen ? i18nDerived.menuExit() : i18nDerived.menu()}
				aria-pressed={stateUi.menuOpen}
				onpointerenter={hover}
				onclick={() => {
					if (stateUi.menuOpen) closeMenu(context.eventEmitter, true);
					else openMenu(context.eventEmitter);
				}}
			>
				<img src={hudUrl('menu')} style={imgStyle(L.menu)} alt="" draggable="false" fetchpriority="low" />
			</button>
			<div class="hud-text" style={at(L.balance, 1390, 366)} aria-label={i18nDerived.balance()}>
				<span class="kicker">{i18nDerived.balance()}</span>
				<span class="value">{numberToCurrencyString(balanceTween.current)}</span>
			</div>

			<!-- WIN: its own plate between balance and bet -->
			<div class="hud-plate-frame" style={boxStyle(L.win)} aria-hidden="true">
				<img src={hudUrl('bet_background')} style={imgStyle(L.win)} alt="" draggable="false" fetchpriority="low" />
			</div>
			<div class="hud-win" style={at(L.win, 1085, 360)} aria-label={i18nDerived.win()}>
				{#if stateUi.freeSpinCounterShow}
					<span class="free-spins">
						{i18nDerived.freeSpins()}
						{stateUi.freeSpinCounterCurrent} / {stateUi.freeSpinCounterTotal}
					</span>
				{/if}
				<span class="kicker win-kicker">{i18nDerived.win()}</span>
				<span class="value big">{bookEventAmountToCurrencyString(winTween.current)}</span>
			</div>

			<!-- Turbo / Auto -->
			<button
				type="button"
				class="hud-btn"
				class:active={stateBet.isTurbo}
				style={boxStyle(L.turbo)}
				aria-label={i18nDerived.turbo()}
				aria-pressed={stateBet.isTurbo}
				disabled={turboDisabled}
				onpointerenter={hover}
				onclick={() => pressTurbo(context.eventEmitter)}
			>
				<img src={hudUrl('turbo')} style={imgStyle(L.turbo)} alt="" draggable="false" fetchpriority="low" />
				<span class="hud-label" style={inBox(L.turbo, 1300, 360)}>{i18nDerived.turbo()}</span>
			</button>

			<button
				type="button"
				class="hud-btn"
				class:active={autoOn}
				style={boxStyle(L.auto)}
				aria-label={i18nDerived.autoSpin()}
				aria-pressed={autoOn}
				disabled={autoDisabled}
				onpointerenter={hover}
				onclick={() => pressAuto(context.eventEmitter)}
			>
				<img src={hudUrl('autospin')} style={imgStyle(L.auto)} alt="" draggable="false" fetchpriority="low" />
				<span class="hud-label" style={inBox(L.auto, 1350, 360)}>{autoWord}</span>
			</button>
			{#if autoBadge}<span class="hud-badge" style={at(L.auto, 1900, 130)}>{autoBadge}</span>{/if}

			<!-- Bet -->
			<div class="hud-plate-frame" style={boxStyle(L.bet)} aria-hidden="true">
				<img src={hudUrl('bet_background')} style={imgStyle(L.bet)} alt="" draggable="false" fetchpriority="low" />
			</div>
			<button
				type="button"
				class="hud-btn"
				style={boxStyle(L.minus)}
				aria-label={`${i18nDerived.decrease()} ${i18nDerived.bet()}`}
				disabled={stepLocked || stateBet.betAmount === smallest}
				onpointerenter={hover}
				onclick={() => stepBet(context.eventEmitter, -1)}
			>
				<img src={hudUrl('minus')} style={imgStyle(L.minus)} alt="" draggable="false" fetchpriority="low" />
			</button>
			<button
				type="button"
				class="hud-text bet-btn"
				style={`left:${L.minus.x + L.minus.w + 6}px;top:${L.bet.y + 6}px;width:${L.plus.x - (L.minus.x + L.minus.w) - 12}px;height:${L.bet.h - 12}px;`}
				aria-label={i18nDerived.bet()}
				disabled={stepLocked}
				onpointerenter={hover}
				onclick={() => {
					if (stepLocked) return;
					openBetMenu(context.eventEmitter);
				}}
			>
				<span class="kicker">{i18nDerived.bet()}</span>
				<span class="value">{numberToCurrencyString(stateBetDerived.betCost())}</span>
			</button>
			<button
				type="button"
				class="hud-btn"
				style={boxStyle(L.plus)}
				aria-label={`${i18nDerived.increase()} ${i18nDerived.bet()}`}
				disabled={stepLocked || stateBet.betAmount === biggest}
				onpointerenter={hover}
				onclick={() => stepBet(context.eventEmitter, 1)}
			>
				<img src={hudUrl('plus')} style={imgStyle(L.plus)} alt="" draggable="false" fetchpriority="low" />
			</button>

			<!-- SPIN / STOP -->
			<button
				type="button"
				class="hud-btn spin-btn"
				class:stop={stopMode}
				style={boxStyle(L.spin)}
				data-test="ml-spin"
				aria-label={spinLabel}
				disabled={spinDisabled || spinKey.endsWith('disabled')}
				onpointerenter={hover}
				onclick={onSpin}
			>
				<img src={hudUrl(stopMode ? 'stop' : 'spin')} style={imgStyle(spinBox)} alt="" draggable="false" fetchpriority="low" />
			</button>
		</div>

		{#if stateUi.menuOpen}
			<div class="flyout" role="menu">
				<button type="button" onpointerenter={hover} onclick={() => openRules(context.eventEmitter)}>
					{i18nDerived.info()}
				</button>
				<button type="button" onpointerenter={hover} onclick={() => openPaytable(context.eventEmitter)}>
					{i18nDerived.payTable()}
				</button>
				<button
					type="button"
					class:off={soundOff}
					onpointerenter={hover}
					onclick={() => toggleSound(context.eventEmitter)}
				>
					{soundOff ? i18nDerived.soundOff() : i18nDerived.soundOn()}
				</button>
				<button type="button" onpointerenter={hover} onclick={() => openSettings(context.eventEmitter)}>
					{i18nDerived.settings()}
				</button>
				<span class="langs">
					<button type="button" onpointerenter={hover} onclick={() => pickLanguage(context.eventEmitter, 'en')}>EN</button>
					<button type="button" onpointerenter={hover} onclick={() => pickLanguage(context.eventEmitter, 'pl')}>PL</button>
				</span>
			</div>
		{/if}
		{/if}
	</div>
{/if}

<style>
	.ml-betui {
		--gold: #f0c75a;
		--gold-soft: #fbe9b0;
		position: absolute;
		z-index: 21;
		inset: 0;
		pointer-events: none;
		color: var(--gold-soft);
		font-family: var(--ml-font-gold, 'Luckiest Guy', serif);
	}

	.backdrop {
		position: absolute;
		inset: 0;
		pointer-events: auto;
		background: rgba(6, 2, 4, 0.28);
		border: 0;
		cursor: pointer;
	}

	/* Bottom bar: dark burgundy lacquer with gold hairlines. */
	.bar {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 14px;
		height: 100px;
		display: flex;
		align-items: center;
		gap: 12px;
		/* Right padding leaves room for the SPIN button that overlaps the bar. */
		padding: 0 196px 0 22px;
		box-sizing: border-box;
		pointer-events: auto;
		background:
			linear-gradient(180deg, rgba(120, 28, 48, 0.22), transparent 40%),
			linear-gradient(180deg, #3a0f1c, #1a0910 55%, #12060b);
		box-shadow:
			0 -10px 24px rgba(0, 0, 0, 0.35),
			inset 0 1px 0 rgba(255, 220, 140, 0.18);
	}

	.bar-line {
		position: absolute;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(
			90deg,
			transparent,
			rgba(228, 190, 100, 0.9) 8%,
			rgba(228, 190, 100, 0.9) 92%,
			transparent
		);
		pointer-events: none;
	}

	.bar-line.top {
		top: 0;
	}

	.bar-line.bottom {
		bottom: 0;
	}

	svg {
		display: block;
		fill: none;
		stroke: currentColor;
		stroke-width: 1.7;
		stroke-linecap: round;
		stroke-linejoin: round;
		pointer-events: none;
	}

	.tile,
	.panel,
	.round,
	.bet-btn,
	.flyout button {
		font-family: inherit;
	}

	/* Square gold-framed buttons (menu, turbo, auto, buy bonus). */
	.tile {
		position: relative;
		display: grid;
		justify-items: center;
		align-content: center;
		gap: 4px;
		flex: 0 0 auto;
		width: 82px;
		height: 66px;
		padding: 0;
		color: var(--gold);
		background: linear-gradient(180deg, #4a1424, #1b0a10);
		border: 1.5px solid rgba(228, 190, 100, 0.85);
		border-radius: 10px;
		box-shadow: inset 0 1px 0 rgba(255, 224, 150, 0.2);
		cursor: pointer;
		transition:
			transform 120ms ease,
			border-color 120ms ease,
			box-shadow 120ms ease;
	}

	.tile svg {
		width: 26px;
		height: 26px;
	}

	.tile.menu {
		width: 62px;
		height: 62px;
	}

	.tile.menu svg {
		width: 30px;
		height: 30px;
	}

	/* The right-hand buttons sit against the SPIN button; the WIN counter is centred on the bar on its own. */
	.push {
		margin-left: auto;
	}

	/* New HUD: image buttons placed on the stage, no bar behind them. */
	.hud {
		position: absolute;
		width: 1280px;
		height: 720px;
		transform-origin: 0 0;
		pointer-events: none;
	}

	.hud-btn,
	.hud-plate-frame {
		position: absolute;
		padding: 0;
		background: none;
		border: 0;
		overflow: visible;
		pointer-events: none;
	}

	.hud-btn {
		pointer-events: auto;
		cursor: pointer;
		transition:
			transform 120ms ease,
			filter 120ms ease;
	}

	.hud-btn img,
	.hud-plate-frame img {
		position: absolute;
		max-width: none;
		pointer-events: none;
		user-select: none;
		filter: drop-shadow(0 3px 5px rgba(0, 0, 0, 0.45));
	}

	.hud-btn:hover:not(:disabled) {
		transform: translateY(-1px);
		filter: brightness(1.1);
	}

	.hud-btn:active:not(:disabled) {
		transform: scale(0.96);
	}

	/* Switched on (turbo, auto, bonus, open menu): a strong gold halo that also stays while hovered. */
	.hud-btn.active,
	.hud-btn.active:hover:not(:disabled) {
		filter: drop-shadow(0 0 3px #fff1b0) drop-shadow(0 0 7px rgba(255, 196, 64, 1)) brightness(1.2) saturate(1.2);
		animation: hud-glow 1.4s ease-in-out infinite alternate;
	}

	/* A bright ring around the switched-on pill, so the state reads at a glance on the gold artwork. */
	.hud-btn.active::before {
		content: '';
		position: absolute;
		inset: -2px;
		border-radius: 999px;
		border: 2px solid #fff3b8;
		box-shadow:
			0 0 5px 1px rgba(255, 222, 120, 0.95),
			0 0 11px 3px rgba(255, 180, 50, 0.7),
			inset 0 0 6px 1px rgba(255, 222, 120, 0.7);
		pointer-events: none;
		animation: hud-ring 1.4s ease-in-out infinite alternate;
	}

	@keyframes hud-ring {
		from {
			opacity: 0.65;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes hud-glow {
		from {
			filter: drop-shadow(0 0 2px #fff1b0) drop-shadow(0 0 5px rgba(255, 196, 64, 0.95)) brightness(1.12) saturate(1.15);
		}
		to {
			filter: drop-shadow(0 0 4px #fff7cc) drop-shadow(0 0 9px rgba(255, 206, 80, 1)) brightness(1.25) saturate(1.25);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.hud-btn.active,
		.hud-btn.active:hover:not(:disabled),
		.hud-btn.active::before {
			animation: none;
		}
	}

	.hud-btn:disabled {
		cursor: default;
		opacity: 0.5;
	}

	.hud-label,
	.hud-badge,
	.hud-text {
		position: absolute;
		transform: translate(-50%, -50%);
		color: #fbe9b0;
		font-family: var(--ml-font-gold, 'Luckiest Guy', serif);
		white-space: nowrap;
		pointer-events: none;
		text-shadow: 0 2px 0 rgba(40, 8, 16, 0.85);
	}

	.hud-label {
		font-size: 12.4px;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.hud-badge {
		min-width: 22px;
		padding: 1px 6px;
		font-size: 12px;
		text-align: center;
		background: #1b0a10;
		border: 1px solid rgba(228, 190, 100, 0.9);
		border-radius: 999px;
	}

	.hud-text {
		display: grid;
		justify-items: center;
		gap: 2px;
	}

	.hud-text.bet-btn {
		transform: none;
		align-content: center;
		background: none;
		border: 0;
		padding: 0;
		pointer-events: auto;
		cursor: pointer;
	}

	.hud-win {
		position: absolute;
		transform: translate(-50%, -50%);
		/* One line: WIN and the amount side by side. */
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 8px;
		white-space: nowrap;
		color: #fbe9b0;
		font-family: var(--ml-font-gold, 'Luckiest Guy', serif);
		text-shadow: 0 2px 0 rgba(40, 8, 16, 0.9);
		pointer-events: none;
	}

	.hud-win .win-kicker {
		font-size: 13.1px;
	}

	.hud .kicker {
		font-size: 10.7px;
	}

	.hud .value {
		font-size: 16.9px;
	}

	.hud .value.big {
		font-size: 23.1px;
	}

	/* BET plate: its lettering is 10 % smaller with the plate. */
	.hud .bet-btn .kicker {
		font-size: 15.2px;
		transform: scaleX(1.14);
	}

	.hud .bet-btn .value {
		font-size: 16px;
		transform: scaleX(1.14);
	}

	.hud .bonus-label {
		font-size: 17.1px;
	}

	.hud-win .free-spins {
		position: static;
	}

	.spin-btn img {
		filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.55));
	}

	.funds-note {
		position: absolute;
		left: 584px;
		top: 574px;
		transform: translateX(-50%);
		padding: 6px 14px;
		color: #fbe9b0;
		background: rgba(60, 10, 22, 0.92);
		border: 1.5px solid rgba(228, 190, 100, 0.85);
		border-radius: 999px;
		font-size: 12px;
		font-weight: 800;
		letter-spacing: 0.12em;
		white-space: nowrap;
		pointer-events: none;
	}

	.replay-bar {
		padding-right: 22px;
	}

	.replay-win {
		position: absolute;
	}

	.tile.wide {
		width: 108px;
	}

	/* Image button: the emblem's art spans the full width of its canvas, centred vertically. */
	.buy-emblem {
		position: relative;
		flex: 0 0 auto;
		width: 108px;
		height: 66px;
		padding: 0;
		background: none;
		border: 0;
		cursor: pointer;
		filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.45));
		transition:
			transform 120ms ease,
			filter 120ms ease;
	}

	.buy-emblem img {
		position: absolute;
		left: 0;
		top: 50%;
		width: 108px;
		height: auto;
		transform: translateY(-50%);
		pointer-events: none;
		user-select: none;
	}

	.buy-emblem:hover:not(:disabled) {
		transform: translateY(-1px);
		filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.45)) brightness(1.12);
	}

	.buy-emblem:active:not(:disabled) {
		transform: scale(0.96);
	}

	.buy-emblem.active {
		filter: drop-shadow(0 0 10px rgba(255, 205, 90, 0.85)) brightness(1.1);
	}

	.buy-emblem:disabled {
		cursor: default;
		opacity: 0.45;
	}

	.cap {
		font-size: 13px;
		font-weight: 800;
		letter-spacing: 0.08em;
		line-height: 1;
		text-transform: uppercase;
		text-align: center;
	}

	.tile:hover:not(:disabled),
	.round:hover:not(:disabled) {
		transform: translateY(-1px);
		border-color: #fbe9b0;
	}

	.tile:active:not(:disabled),
	.round:active:not(:disabled) {
		transform: scale(0.96);
	}

	.tile.active {
		border-color: #fbe9b0;
		box-shadow:
			0 0 12px rgba(255, 205, 90, 0.7),
			inset 0 0 10px rgba(255, 205, 90, 0.25);
	}

	.tile:disabled,
	.round:disabled {
		cursor: default;
		opacity: 0.45;
	}

	.badge {
		position: absolute;
		right: 4px;
		top: 3px;
		min-width: 18px;
		padding: 1px 4px;
		border-radius: 999px;
		background: #1b0a10;
		border: 1px solid rgba(228, 190, 100, 0.9);
		color: var(--gold-soft);
		font-size: 10px;
		font-weight: 800;
		text-align: center;
	}

	.panel {
		box-sizing: border-box;
		display: flex;
		align-items: center;
		gap: 10px;
		flex: 0 0 auto;
		height: 66px;
		padding: 0 14px;
		background: linear-gradient(180deg, #2a0b14, #14080d);
		border: 1.5px solid rgba(228, 190, 100, 0.55);
		border-radius: 12px;
		box-shadow: inset 0 1px 0 rgba(255, 224, 150, 0.12);
	}

	.panel .ico {
		width: 26px;
		height: 26px;
		color: var(--gold);
	}

	.text {
		display: grid;
		justify-items: start;
		gap: 4px;
	}

	.kicker {
		color: var(--gold);
		font-size: 15px;
		font-weight: 800;
		letter-spacing: 0.14em;
		line-height: 1;
		text-transform: uppercase;
	}

	.value {
		color: var(--gold-soft);
		font-size: 24px;
		font-weight: 800;
		line-height: 1;
		white-space: nowrap;
		text-shadow: 0 1px 0 rgba(40, 8, 16, 0.8);
	}

	.value.big {
		font-size: 32px;
	}

	.balance {
		width: 176px;
	}

	.sep {
		flex: 0 0 auto;
		width: 1px;
		height: 44px;
		background: linear-gradient(180deg, transparent, rgba(228, 190, 100, 0.7), transparent);
	}

	.bet {
		gap: 8px;
		width: 226px;
		justify-content: space-between;
		padding: 0 10px;
	}

	.bet-btn {
		display: grid;
		justify-items: center;
		gap: 4px;
		padding: 2px 8px;
		color: inherit;
		background: transparent;
		border: 0;
		border-radius: 8px;
		cursor: pointer;
	}

	.bet-btn:disabled {
		cursor: default;
	}

	.round {
		display: grid;
		place-items: center;
		flex: 0 0 auto;
		width: 40px;
		height: 40px;
		padding: 0;
		color: var(--gold-soft);
		background: radial-gradient(circle at 50% 30%, #a3243e, #4f0f1f);
		border: 1.5px solid rgba(228, 190, 100, 0.85);
		border-radius: 50%;
		cursor: pointer;
		transition:
			transform 120ms ease,
			border-color 120ms ease;
	}

	.round svg {
		width: 22px;
		height: 22px;
	}

	.win {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		/* Display only: its box reaches over the "+" bet button and must never swallow clicks. */
		pointer-events: none;
		flex-direction: column;
		justify-content: center;
		gap: 6px;
		width: 190px;
		padding: 0;
		background: transparent;
		border-color: transparent;
		box-shadow: none;
	}

	.win .kicker {
		font-size: 26px;
	}

	.free-spins {
		position: absolute;
		top: -2px;
		color: var(--gold);
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.1em;
	}

	/* SPIN / STOP asset, hanging over the bar at the right. */
	.spin {
		position: absolute;
		right: 16px;
		/* Centred on the bar (bar: bottom 14px, height 100px). */
		bottom: -24px;
		width: 176px;
		height: 176px;
		padding: 0;
		background: transparent;
		border: 0;
		border-radius: 50%;
		cursor: pointer;
		pointer-events: auto;
		filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.55));
		transition:
			transform 120ms ease,
			filter 120ms ease;
	}

	.spin img {
		/* 10 % darker than the artwork. */
		filter: brightness(0.9);
		display: block;
		width: 100%;
		height: 100%;
		object-fit: contain;
		pointer-events: none;
		user-select: none;
	}

	.spin:hover:not(:disabled) {
		transform: scale(1.04);
		filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.55)) brightness(1.1);
	}

	.spin:active:not(:disabled) {
		transform: scale(0.97);
	}

	.spin:disabled {
		cursor: default;
		filter: grayscale(0.6) brightness(0.65) drop-shadow(0 6px 12px rgba(0, 0, 0, 0.55));
	}

	.spin:focus-visible,
	.tile:focus-visible,
	.round:focus-visible {
		outline: 2px solid #fbe9b0;
		outline-offset: 2px;
	}

	.flyout {
		position: absolute;
		left: 24px;
		bottom: 164px;
		display: flex;
		flex-direction: column;
		gap: 6px;
		min-width: 200px;
		padding: 30px 28px;
		pointer-events: auto;
		background: none;
		border: 1px solid transparent;
		border-image: var(--ml-panel) 64 fill / 26px stretch;
		filter: drop-shadow(0 11px 20px rgba(0, 0, 0, 0.5));
	}

	.flyout button {
		min-height: 40px;
		padding: 0 14px;
		color: #f3e2b8;
		background: none;
		border: 1px solid transparent;
		border-image: var(--ml-button) 34 fill / 13px stretch;
		cursor: pointer;
		font-size: 13px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-align: center;
		transition: transform 0.12s ease, filter 0.12s ease;
	}

	.flyout button:hover {
		filter: brightness(1.12);
	}

	.flyout button:active {
		transform: scale(0.97);
	}

	.flyout button.off {
		opacity: 0.7;
	}

	.langs {
		display: flex;
		gap: 6px;
	}

	.langs button {
		flex: 1;
		text-align: center;
	}
</style>
