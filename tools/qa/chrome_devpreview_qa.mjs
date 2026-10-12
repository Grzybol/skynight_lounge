import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = process.env.QA_BASE || 'http://127.0.0.1:4010';
const PORT = Number(process.env.QA_CDP_PORT || 9223);
const OUT = path.join(process.cwd(), 'tools', 'qa', 'output');
mkdirSync(OUT, { recursive: true });

const userData = path.join(os.tmpdir(), `garden-bounty-qa-${Date.now()}`);
mkdirSync(userData, { recursive: true });

const chrome = spawn(
	CHROME,
	[
		'--headless=new',
		`--remote-debugging-port=${PORT}`,
		`--user-data-dir=${userData}`,
		'--disable-gpu',
		'--hide-scrollbars',
		'--window-size=1440,900',
		'--no-first-run',
		'--no-default-browser-check',
		'about:blank',
	],
	{ stdio: ['ignore', 'pipe', 'pipe'] },
);

const waitForListening = async () => {
	const started = Date.now();
	while (Date.now() - started < 25000) {
		try {
			const res = await fetch(`http://127.0.0.1:${PORT}/json/version`);
			if (res.ok) return;
		} catch {}
		await sleep(250);
	}
	throw new Error('Chrome CDP did not start');
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function cdp(ws, idRef) {
	return (method, params = {}) =>
		new Promise((resolve, reject) => {
			const id = ++idRef.current;
			const timer = setTimeout(() => {
				ws.removeEventListener('message', onMessage);
				reject(new Error(`CDP timeout: ${method}`));
			}, 30000);
			const onMessage = (event) => {
				const msg = JSON.parse(event.data.toString());
				if (msg.id !== id) return;
				clearTimeout(timer);
				ws.removeEventListener('message', onMessage);
				if (msg.error) reject(new Error(`${method}: ${JSON.stringify(msg.error)}`));
				else resolve(msg.result);
			};
			ws.addEventListener('message', onMessage);
			ws.send(JSON.stringify({ id, method, params }));
		});
}

async function main() {
	const report = { startedAt: new Date().toISOString(), base: BASE, steps: [] };
	await waitForListening();
	await sleep(500);
	const pageTarget = await fetch(
		`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(`${BASE}/dev-preview`)}`,
		{ method: 'PUT' },
	).then((res) => res.json());
	const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
	await new Promise((resolve, reject) => {
		ws.addEventListener('open', resolve);
		ws.addEventListener('error', reject);
	});
	const idRef = { current: 0 };
	const send = cdp(ws, idRef);
	await send('Page.enable');
	await send('Runtime.enable');

	const evaluate = async (expression) => {
		const result = await send('Runtime.evaluate', {
			expression,
			awaitPromise: true,
			returnByValue: true,
		});
		if (result.exceptionDetails) {
			throw new Error(result.exceptionDetails.text || 'evaluate failed');
		}
		return result.result?.value;
	};

	const screenshot = async (name) => {
		const shot = await send('Page.captureScreenshot', { format: 'png' });
		writeFileSync(path.join(OUT, `${name}.png`), Buffer.from(shot.data, 'base64'));
	};

	const waitReady = async () => {
		const started = Date.now();
		while (Date.now() - started < 25000) {
			const state = await evaluate(`({
				action: !!document.querySelector('button.action'),
				actionDisabled: document.querySelector('button.action')?.disabled ?? null,
				diag: document.querySelector('[data-test="demo-diagnostics"]')?.textContent?.replace(/\\s+/g,' ').trim() || '',
				canvas: !!document.querySelector('canvas'),
				select: document.querySelector('#test-mode')?.value || null,
				body: (document.body?.innerText || '').slice(0, 400)
			})`);
			if (state.action && state.diag && state.actionDisabled === false) return state;
			await sleep(400);
		}
		throw new Error('dev-preview UI did not become ready');
	};

	const setMode = async (value) => {
		await evaluate(`(() => {
			const select = document.querySelector('#test-mode');
			select.value = ${JSON.stringify(value)};
			select.dispatchEvent(new Event('change', { bubbles: true }));
			select.dispatchEvent(new Event('input', { bubbles: true }));
			return select.value;
		})()`);
	};

	const clickActionAndWait = async (label, timeoutMs = 20000) => {
		await evaluate(`document.querySelector('button.action')?.click()`);
		const started = Date.now();
		while (Date.now() - started < timeoutMs) {
			const state = await evaluate(`({
				message: document.querySelector('.message')?.textContent || '',
				disabled: document.querySelector('button.action')?.disabled ?? null,
				diag: document.querySelector('[data-test="demo-diagnostics"]')?.textContent?.replace(/\\s+/g,' ').trim() || '',
				modals: Array.from(document.querySelectorAll('h2,h1,.kicker,[role="dialog"]')).map(el => el.textContent?.trim()).filter(Boolean).slice(0, 12)
			})`);
			if (String(state.message).includes('resolved')) return state;
			await sleep(400);
		}
		return evaluate(`({
			timeout: true,
			message: document.querySelector('.message')?.textContent || '',
			diag: document.querySelector('[data-test="demo-diagnostics"]')?.textContent?.replace(/\\s+/g,' ').trim() || '',
			modals: Array.from(document.querySelectorAll('h2,h1,.kicker,[role="dialog"]')).map(el => el.textContent?.trim()).filter(Boolean).slice(0, 12)
		})`);
	};

	const pressSpace = async () => {
		await evaluate(`(() => {
			window.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
			window.dispatchEvent(new KeyboardEvent('keyup', { key: ' ', code: 'Space', bubbles: true }));
			return true;
		})()`);
	};

	const step = async (name, fn) => {
		try {
			const result = await fn();
			report.steps.push({ name, ok: true, result });
			console.log(`OK  ${name}`);
		} catch (error) {
			report.steps.push({ name, ok: false, error: String(error) });
			console.error(`FAIL ${name}: ${error}`);
		}
	};

	await send('Emulation.setDeviceMetricsOverride', {
		width: 1440,
		height: 900,
		deviceScaleFactor: 1,
		mobile: false,
	});
	await send('Page.navigate', { url: `${BASE}/dev-preview` });
	await sleep(2500);

	await step('idle-ready', async () => {
		const state = await waitReady();
		await screenshot('01-idle-desktop');
		return state;
	});

	await step('base-spin', async () => {
		await setMode('baseSpin');
		const before = await evaluate(`document.querySelector('[data-test="demo-diagnostics"]')?.textContent`);
		const result = await clickActionAndWait('baseSpin', 18000);
		await screenshot('02-base-spin');
		return { before: before?.replace(/\s+/g, ' ').trim(), ...result };
	});

	await step('real-space-bet', async () => {
		await evaluate(`document.body.click()`);
		const before = await evaluate(`document.querySelector('[data-test="demo-diagnostics"]')?.textContent`);
		await pressSpace();
		await sleep(2500);
		const mid = await evaluate(`document.querySelector('[data-test="demo-diagnostics"]')?.textContent`);
		const started = Date.now();
		let after = mid;
		while (Date.now() - started < 15000) {
			after = await evaluate(`document.querySelector('[data-test="demo-diagnostics"]')?.textContent`);
			if (String(after).includes('Machine idle')) break;
			await pressSpace();
			await sleep(500);
		}
		await screenshot('03-space-bet');
		return {
			before: before?.replace(/\s+/g, ' ').trim(),
			mid: mid?.replace(/\s+/g, ' ').trim(),
			after: after?.replace(/\s+/g, ' ').trim(),
		};
	});

	await step('symbol-win', async () => {
		await setMode('symbolWin');
		const result = await clickActionAndWait('symbolWin', 12000);
		await screenshot('04-symbol-win');
		return result;
	});

	await step('big-win', async () => {
		await setMode('win');
		const running = clickActionAndWait('win', 25000);
		for (let i = 0; i < 16; i += 1) {
			await sleep(800);
			await pressSpace();
		}
		const result = await running;
		await screenshot('05-big-win');
		return result;
	});

	await step('bonus-flow', async () => {
		await setMode('bonus');
		const running = clickActionAndWait('bonus', 20000);
		for (let i = 0; i < 12; i += 1) {
			await sleep(700);
			await pressSpace();
		}
		const result = await running;
		await screenshot('06-bonus');
		return result;
	});

	await step('anticipation', async () => {
		await setMode('anticipation');
		const result = await clickActionAndWait('anticipation', 8000);
		await screenshot('07-anticipation');
		return result;
	});

	await step('modal-paytable', async () => {
		await setMode('modalPaytable');
		await clickActionAndWait('paytable', 4000);
		await sleep(600);
		const html = await evaluate(`document.body.innerText`);
		await screenshot('08-paytable');
		return { text: html.slice(0, 1500) };
	});

	await step('modal-rules', async () => {
		await evaluate(`document.querySelector('button.reset')?.click()`);
		await sleep(400);
		await setMode('modalRules');
		await clickActionAndWait('rules', 4000);
		await sleep(600);
		const html = await evaluate(`document.body.innerText`);
		await screenshot('09-rules');
		return { text: html.slice(0, 1500) };
	});

	await step('modal-buy-bonus', async () => {
		await evaluate(`document.querySelector('button.reset')?.click()`);
		await sleep(400);
		await setMode('modalBuyBonus');
		await clickActionAndWait('buyBonus', 4000);
		await sleep(600);
		const html = await evaluate(`document.body.innerText`);
		await screenshot('10-buy-bonus');
		return { text: html.slice(0, 1500) };
	});

	await step('modal-settings', async () => {
		await evaluate(`document.querySelector('button.reset')?.click()`);
		await sleep(400);
		await setMode('modalSettings');
		await clickActionAndWait('settings', 4000);
		await sleep(600);
		const html = await evaluate(`document.body.innerText`);
		await screenshot('11-settings');
		return { text: html.slice(0, 800) };
	});

	await step('reset-idle', async () => {
		await evaluate(`document.querySelector('button.reset')?.click()`);
		await sleep(500);
		const diag = await evaluate(`document.querySelector('[data-test="demo-diagnostics"]')?.textContent?.replace(/\\s+/g,' ').trim()`);
		await screenshot('12-reset-idle');
		return { diag };
	});

	await step('portrait-480x900', async () => {
		await send('Emulation.setDeviceMetricsOverride', {
			width: 480,
			height: 900,
			deviceScaleFactor: 1,
			mobile: true,
		});
		await send('Page.reload', { ignoreCache: true });
		await sleep(2500);
		const state = await waitReady().catch((error) => ({ error: String(error) }));
		await screenshot('13-portrait');
		return state;
	});

	await step('production-route', async () => {
		await send('Emulation.setDeviceMetricsOverride', {
			width: 1440,
			height: 900,
			deviceScaleFactor: 1,
			mobile: false,
		});
		await send('Page.navigate', { url: `${BASE}/` });
		await sleep(4000);
		const text = await evaluate(`document.body.innerText`);
		await screenshot('14-production-authenticate');
		return { text: text.slice(0, 1200) };
	});

	report.finishedAt = new Date().toISOString();
	writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
	ws.close();
	chrome.kill();
	console.log(`Wrote ${path.join(OUT, 'report.json')}`);
}

main().catch((error) => {
	console.error(error);
	chrome.kill();
	process.exit(1);
});
