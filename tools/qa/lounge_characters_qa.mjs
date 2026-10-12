/**
 * Live QA for the Midnight Lounge character animation system.
 * Needs the Vite dev server (default http://127.0.0.1:3020) and Chrome.
 *   node tools/qa/lounge_characters_qa.mjs
 * Writes screenshots + report.json into tools/qa/output/lounge-characters/.
 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import os from "node:os";

const CHROME =
  process.env.QA_CHROME ||
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE = process.env.QA_BASE || "http://127.0.0.1:3020";
const PORT = Number(process.env.QA_CDP_PORT || 9333);
const OUT = path.join(
  process.cwd(),
  "tools",
  "qa",
  "output",
  "lounge-characters",
);
mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${path.join(os.tmpdir(), `lounge-qa-${Date.now()}`)}`,
    "--hide-scrollbars",
    "--window-size=1280,720",
    "--no-first-run",
    "--autoplay-policy=no-user-gesture-required",
    "--enable-precise-memory-info",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "about:blank",
  ],
  { stdio: "ignore" },
);

const cdpSend = (ws) => {
  let id = 0;
  return (method, params = {}) =>
    new Promise((resolve, reject) => {
      const myId = ++id;
      const timer = setTimeout(
        () => reject(new Error(`CDP timeout ${method}`)),
        120000,
      );
      const on = (ev) => {
        const msg = JSON.parse(ev.data.toString());
        if (msg.id !== myId) return;
        clearTimeout(timer);
        ws.removeEventListener("message", on);
        if (msg.error)
          reject(new Error(`${method}: ${JSON.stringify(msg.error)}`));
        else resolve(msg.result);
      };
      ws.addEventListener("message", on);
      ws.send(JSON.stringify({ id: myId, method, params }));
    });
};

const report = { startedAt: new Date().toISOString(), base: BASE, checks: [] };
const check = (name, ok, detail) => {
  report.checks.push({ name, ok, detail });
  console.log(
    `${ok ? "PASS" : "FAIL"}  ${name}${detail !== undefined ? "  " + JSON.stringify(detail) : ""}`,
  );
};

// In-page rAF sampler: records the clip/frame each character canvas shows and
// whether the canvas is fully transparent (a "blank frame").
const SAMPLER = `
window.__samp = (() => {
	const scratch = document.createElement('canvas'); scratch.width = 24; scratch.height = 32;
	const sctx = scratch.getContext('2d', { willReadFrequently: true });
	const log = { woman: [], bartender: [] }; let running = false; let rafs = 0; let t0 = 0;
	const blank = (c) => { sctx.clearRect(0,0,24,32); sctx.drawImage(c,0,0,24,32); const d = sctx.getImageData(0,0,24,32).data; let a = 0; for (let i=3;i<d.length;i+=4) a += d[i]; return a === 0; };
	const tick = (now) => {
		if (!running) return; rafs++;
		for (const k of ['woman','bartender']) {
			const c = document.querySelector('canvas[data-lounge-character='+k+']'); if (!c) continue;
			log[k].push([now, c.dataset.clip, +c.dataset.frame, blank(c) ? 1 : 0]);
		}
		requestAnimationFrame(tick);
	};
	return {
		start() { log.woman.length = 0; log.bartender.length = 0; rafs = 0; running = true; t0 = performance.now(); requestAnimationFrame(tick); },
		stop() { running = false; return { log: { woman: log.woman.slice(), bartender: log.bartender.slice() }, rafs, ms: performance.now() - t0 }; },
	};
})(); true`;

const analyse = (samples) => {
  const clips = [];
  let blanks = 0;
  let maxGap = 0;
  let maxStall = 0;
  let cur = null;
  let lastChange = 0;
  let prev = null;
  for (const [t, clip, frame, blank] of samples) {
    if (blank) blanks++;
    if (!cur || cur.id !== clip) {
      cur = { id: clip, start: t, end: t, frames: new Set() };
      clips.push(cur);
      prev = null;
    }
    cur.end = t;
    cur.frames.add(frame);
    if (prev !== null && frame !== prev)
      frame > prev && (maxGap = Math.max(maxGap, frame - prev));
    if (prev === null || frame !== prev) lastChange = t;
    else maxStall = Math.max(maxStall, t - lastChange);
    prev = frame;
  }
  return {
    clips: clips.map((c) => ({
      id: c.id,
      ms: Math.round(c.end - c.start),
      uniqueFrames: c.frames.size,
    })),
    blanks,
    maxGap,
    maxStallMs: Math.round(maxStall),
  };
};

const main = async () => {
  for (let i = 0; i < 80; i++) {
    try {
      if ((await fetch(`http://127.0.0.1:${PORT}/json/version`)).ok) break;
    } catch {}
    await sleep(250);
  }
  const target = await fetch(
    `http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(BASE + "/dev-preview")}`,
    {
      method: "PUT",
    },
  ).then((r) => r.json());
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.addEventListener("open", res);
    ws.addEventListener("error", rej);
  });
  const send = cdpSend(ws);
  await send("Page.enable");
  await send("Runtime.enable");
  const pageErrors = [];
  ws.addEventListener("message", (ev) => {
    const m = JSON.parse(ev.data.toString());
    if (m.method === "Runtime.exceptionThrown") {
      const d = m.params.exceptionDetails;
      pageErrors.push(
        `${d.text} ${(d.exception?.description || "").slice(0, 200)}`,
      );
    }
  });
  const ev = async (expression) => {
    const r = await send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (r.exceptionDetails)
      throw new Error(
        r.exceptionDetails.exception?.description || r.exceptionDetails.text,
      );
    return r.result.value;
  };
  const shot = async (name) =>
    writeFileSync(
      path.join(OUT, name + ".png"),
      Buffer.from(
        (await send("Page.captureScreenshot", { format: "png" })).data,
        "base64",
      ),
    );
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1280,
    height: 720,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await send("Page.navigate", { url: BASE + "/dev-preview" });

  // Intro screen -> play screen.
  for (let i = 0; i < 120; i++) {
    if (await ev(`!!document.querySelector('canvas[data-lounge-character]')`))
      break;
    await sleep(500);
  }
  await sleep(2000);
  await send("Input.dispatchMouseEvent", {
    type: "mousePressed",
    x: 400,
    y: 200,
    button: "left",
    clickCount: 1,
  });
  await send("Input.dispatchMouseEvent", {
    type: "mouseReleased",
    x: 400,
    y: 200,
    button: "left",
    clickCount: 1,
  });
  for (let i = 0; i < 60; i++) {
    if (
      await ev(`!!window.__loungeQa && window.__loungeQa.registry.size === 2`)
    )
      break;
    await sleep(500);
  }
  check(
    "both controllers registered",
    await ev(`window.__loungeQa?.registry.size === 2`),
  );
  await ev(SAMPLER);
  await ev(
    `(() => { const i = document.querySelector('.inspector'); if (i) i.style.visibility = 'hidden'; return true; })()`,
  );
  await sleep(3000);
  await shot("01-idle");
  if (process.env.QA_SHOT_ONLY) {
    await ev(`window.__loungeQa.emit("mega", "mega"); true`);
    await sleep(2500);
    await shot("03-mega-win");
    ws.close();
    chrome.kill();
    process.exit(0);
  }

  const stateOf = () =>
    ev(
      `(() => { const o = {}; for (const [k,h] of window.__loungeQa.registry) { const s = h.player.getStats(); const c = h.controller.getState(); o[k] = { mode: c.mode, win: c.winCategory, active: s.active, bitmaps: s.decodedBitmaps, stalls: s.stalls, err: s.lastError, packs: h.store.snapshot().length }; } return o; })()`,
    );
  const settleIdle = async (timeout = 14000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < timeout) {
      const s = await stateOf();
      if (
        s.woman.mode === "idle" &&
        s.bartender.mode === "idle" &&
        s.woman.active === "woman_idle" &&
        s.bartender.active === "bartender_idle"
      )
        return true;
      await sleep(250);
    }
    return false;
  };

  // A. Default idle loops at ~30 fps with no blank frames.
  await ev(`window.__samp.start()`);
  await sleep(6000);
  const idleRun = await ev(`window.__samp.stop()`);
  for (const k of ["woman", "bartender"]) {
    const a = analyse(idleRun.log[k]);
    const seconds = idleRun.ms / 1000;
    const changes = idleRun.log[k].filter(
      (s, i, arr) => i > 0 && s[2] !== arr[i - 1][2],
    ).length;
    check(
      `${k} default idle loops`,
      a.clips.some((c) => c.id.endsWith("_idle")),
      a.clips.map((c) => c.id),
    );
    check(
      `${k} idle advances ~30 fps (rAF ${Math.round(idleRun.rafs / seconds)} Hz)`,
      changes / seconds > 24 && changes / seconds < 36,
      { framesPerSec: +(changes / seconds).toFixed(1) },
    );
    check(
      `${k} idle no blank frames, no skips >3`,
      a.blanks === 0 && a.maxGap <= 3,
      {
        blanks: a.blanks,
        maxGap: a.maxGap,
        maxStallMs: a.maxStallMs,
      },
    );
  }

  // B. Every clip of each character plays once, then returns to default idle.
  const ids = {
    woman: [
      "woman_idle_1",
      "woman_idle_2",
      "woman_idle_3",
      "woman_idle_4",
      "woman_mini_win",
      "woman_big_win",
      "woman_mega_win",
    ],
    bartender: [
      "bartender_idle_alt",
      "bartender_idle_1",
      "bartender_idle_2",
      "bartender_idle_3",
      "bartender_mini_win",
      "bartender_big_win",
      "bartender_mega_win",
    ],
  };
  for (const ch of ["woman", "bartender"]) {
    for (const id of ids[ch]) {
      await ev(
        `window.__samp.start(); window.__loungeQa.registry.get('${ch}').controller.playManual('${id}'); true`,
      );
      if (id === "bartender_idle_alt" || id === "bartender_idle_2" || id === "woman_idle_3") {
        await sleep(2200);
        await shot(`02-variation-${id}`);
      }
      const t0 = Date.now();
      let done = false;
      while (Date.now() - t0 < 20000) {
        const s = await stateOf();
        if (s[ch].mode === "idle" && s[ch].active === `${ch}_idle`) {
          done = true;
          break;
        }
        await sleep(200);
      }
      await sleep(800);
      const run = await ev(`window.__samp.stop()`);
      const a = analyse(run.log[ch]);
      const clip = a.clips.find((c) => c.id === id);
      const seq = a.clips.map((c) => c.id);
      const ok =
        done &&
        !!clip &&
        clip.uniqueFrames >= 138 &&
        a.blanks === 0 &&
        a.maxGap <= 3 &&
        seq.at(-1) === `${ch}_idle` &&
        seq.includes(id);
      check(`${id}: plays through once, returns to idle, no blank frames`, ok, {
        sequence: a.clips.map((c) => `${c.id}(${c.ms}ms/${c.uniqueFrames}f)`),
        blanks: a.blanks,
        maxGap: a.maxGap,
        maxStallMs: a.maxStallMs,
      });
    }
  }
  await shot("02-after-clips");

  // C. Win events through the same bus the board uses.
  await settleIdle();
  const winCase = async (label, category, want) => {
    await ev(`window.__loungeQa.emit('${category}', '${category}'); true`);
    await sleep(2500);
    const s = await stateOf();
    check(
      `${label}: woman=${want.woman} bartender=${want.bartender}`,
      s.woman.active === want.woman && s.bartender.active === want.bartender,
      {
        woman: s.woman.active,
        bartender: s.bartender.active,
      },
    );
    await shot(`03-${category}-win`);
    await settleIdle(12000);
  };
  await winCase("mini win", "mini", {
    woman: "woman_mini_win",
    bartender: "bartender_mini_win",
  });
  await winCase("big win", "big", {
    woman: "woman_big_win",
    bartender: "bartender_big_win",
  });
  await winCase("mega win (bartender has its own mega clip)", "mega", {
    woman: "woman_mega_win",
    bartender: "bartender_mega_win",
  });
  check("wins return to default idle", await settleIdle(15000));

  // D. Rapid overlapping wins: higher priority pre-empts, equal/lower are ignored.
  await ev(
    `(async () => { const e = window.__loungeQa.emit; for (const c of ['mini','mini','big','mini','mega','big','mini','mega','mini']) { e(c, c); await new Promise(r => setTimeout(r, 150)); } })(); true`,
  );
  // Wins queue behind the playing clip: mini (5 s) first, then the highest waiting one (mega).
  await sleep(7500);
  const rapid = await stateOf();
  check(
    "rapid wins: mega stays on screen (lower requests ignored)",
    rapid.woman.active === "woman_mega_win" &&
      rapid.bartender.active === "bartender_mega_win",
    {
      woman: rapid.woman.active,
      bartender: rapid.bartender.active,
    },
  );
  check(
    "rapid wins: settles back to idle without errors",
    (await settleIdle(15000)) && !(await stateOf()).woman.err,
  );
  const listeners = await ev(`window.__loungeQa.listeners()`);
  check(
    "no duplicate bus listeners (2 characters + QA logger)",
    listeners === 3,
    listeners,
  );

  // E0. Natural idle-variation scheduling (15-30 s woman, 17-33 s bartender), independent per character.
  await settleIdle();
  await ev(`window.__samp.start()`);
  await sleep(42000);
  const nat = await ev(`window.__samp.stop()`);
  const starts = {};
  for (const k of ['woman', 'bartender']) {
    const a = analyse(nat.log[k]);
    const variations = a.clips.filter((c) => /_idle_\d$/.test(c.id));
    const first = nat.log[k].find((r) => /_idle_\d$/.test(r[1]));
    starts[k] = first ? Math.round(first[0] - nat.log[k][0][0]) : null;
    check(
      `${k}: natural idle variation fired and returned to default idle`,
      variations.length >= 1 &&
        // The sample window can end mid-variation; only completed ones must be whole.
        variations
          .filter((v) => v !== a.clips.at(-1))
          .every((v) => v.uniqueFrames >= 138) &&
        a.clips.some((c, i) => i > 0 && c.id === `${k}_idle`) &&
        a.blanks === 0,
      { sequence: a.clips.map((c) => `${c.id}(${c.ms}ms)`), firstVariationAtMs: starts[k] },
    );
  }
  check(
    'characters are not synchronised (variation start times differ)',
    starts.woman !== null && starts.bartender !== null && starts.woman !== starts.bartender,
    starts,
  );

  // E. Soak: 25 wins, then memory bounds.
  const heap0 = await ev(`performance.memory.usedJSHeapSize`);
  for (let i = 0; i < 25; i++) {
    await ev(
      `window.__loungeQa.emit(['mini','big','mega'][${i} % 3], 'x'); true`,
    );
    await sleep(400);
  }
  await settleIdle(25000);
  await sleep(1500);
  const soak = await stateOf();
  const heap1 = await ev(`performance.memory.usedJSHeapSize`);
  check(
    "soak: pack cache bounded (woman<=5, bartender<=4)",
    soak.woman.packs <= 5 && soak.bartender.packs <= 4,
    {
      woman: soak.woman.packs,
      bartender: soak.bartender.packs,
    },
  );
  check(
    "soak: decoded bitmaps bounded (<=40 each)",
    soak.woman.bitmaps <= 40 && soak.bartender.bitmaps <= 40,
    {
      woman: soak.woman.bitmaps,
      bartender: soak.bartender.bitmaps,
    },
  );
  report.heapMB = {
    before: +(heap0 / 1e6).toFixed(1),
    after: +(heap1 / 1e6).toFixed(1),
  };
  console.log("JS heap MB", report.heapMB);
  check(
    "listeners unchanged after soak",
    (await ev(`window.__loungeQa.listeners()`)) === 3,
  );

  // H. Real spins through the board: the board's own win events must drive both characters.
  await settleIdle();
  await ev(`window.__loungeQa.events.length = 0; true`);
  const spinLog = [];
  for (let i = 0; i < 14; i++) {
    await send("Input.dispatchMouseEvent", {
      type: "mousePressed",
      x: 1185,
      y: 631,
      button: "left",
      clickCount: 1,
    });
    await send("Input.dispatchMouseEvent", {
      type: "mouseReleased",
      x: 1185,
      y: 631,
      button: "left",
      clickCount: 1,
    });
    const t0 = Date.now();
    let seen = await ev(`window.__loungeQa.events.length`);
    const before = spinLog.length ? spinLog.at(-1).total : 0;
    while (Date.now() - t0 < 14000) {
      seen = await ev(`window.__loungeQa.events.length`);
      if (seen > before) break;
      await sleep(300);
    }
    if (seen > before) {
      await sleep(700);
      const st = await stateOf();
      const evs = await ev(`window.__loungeQa.events.slice(${before})`);
      spinLog.push({
        total: seen,
        events: evs.map((e) => e.category + "/" + e.tier),
        woman: st.woman.active,
        bartender: st.bartender.active,
      });
      await shot(`05-spin-${i}-${evs.at(-1).category}`);
    }
    await sleep(1500);
  }
  report.spins = spinLog;
  console.log("spin events", JSON.stringify(spinLog));
  const all = await ev(`window.__loungeQa.events.map((e) => e.category)`);
  check(
    "board spins announced at least one win to the characters",
    all.length > 0,
    { events: all },
  );
  check(
    "every announced board win produced the matching clip on both characters",
    spinLog.every((r) => {
      const last = r.events[0].split("/")[0];
      const w = {
        mini: "woman_mini_win",
        big: "woman_big_win",
        mega: "woman_mega_win",
      }[last];
      const b = {
        mini: "bartender_mini_win",
        big: "bartender_big_win",
        mega: "bartender_mega_win",
      }[last];
      // A celebration announces mini first, then big/mega as its counter crosses the
      // thresholds; clips queue, so a later event can still be on its way (mini playing).
      const miniOk = r.woman === "woman_mini_win" && r.bartender === "bartender_mini_win";
      return (r.woman === w && r.bartender === b) || miniOk;
    }),
    spinLog.map(
      (r) => r.events.at(-1) + " -> " + r.woman + " / " + r.bartender,
    ),
  );
  check(
    "characters healthy after spins",
    !(await stateOf()).woman.err && !(await stateOf()).bartender.err,
  );

  // I. Turbo spins through the board: fast result cadence must not break the controllers.
  await settleIdle();
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 838, y: 660, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 838, y: 660, button: 'left', clickCount: 1 });
  await sleep(400);
  const turboOn = await ev(`document.body.innerText.includes('turbo on') || !!document.querySelector('.inspector')?.textContent?.includes('turbo on')`);
  const evBefore = await ev(`window.__loungeQa.events.length`);
  for (let i = 0; i < 10; i++) {
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 1185, y: 631, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 1185, y: 631, button: 'left', clickCount: 1 });
    await sleep(2600);
  }
  const evAfter = await ev(`window.__loungeQa.events.length`);
  const turboState = await stateOf();
  check('turbo spins: wins announced, controllers healthy', evAfter > evBefore && !turboState.woman.err && !turboState.bartender.err, {
    turboOn,
    newEvents: evAfter - evBefore,
    woman: turboState.woman.active,
    bartender: turboState.bartender.active,
  });
  check('turbo spins: listeners unchanged, caches bounded', (await ev(`window.__loungeQa.listeners()`)) === 3 && turboState.woman.bitmaps <= 40 && turboState.woman.packs <= 5);
  await shot('06-turbo');

  // F. Pause / resume.
  await ev(
    `(() => { for (const h of window.__loungeQa.registry.values()) h.player.pause(); true })()`,
  );
  const f1 = await ev(
    `document.querySelector('canvas[data-lounge-character=woman]').dataset.frame`,
  );
  await sleep(1500);
  const f2 = await ev(
    `document.querySelector('canvas[data-lounge-character=woman]').dataset.frame`,
  );
  await ev(
    `(() => { for (const h of window.__loungeQa.registry.values()) h.player.resume(); true })()`,
  );
  await sleep(1000);
  const f3 = await ev(
    `document.querySelector('canvas[data-lounge-character=woman]').dataset.frame`,
  );
  check("pause freezes, resume continues", f1 === f2 && f3 !== f2, {
    f1,
    f2,
    f3,
  });

  report.pageErrors = pageErrors.slice(0, 10);
  check(
    "no uncaught page exceptions",
    pageErrors.length === 0,
    pageErrors.slice(0, 3),
  );
  await shot("04-final");
  writeFileSync(path.join(OUT, "report.json"), JSON.stringify(report, null, 2));
  const failed = report.checks.filter((c) => !c.ok);
  console.log(
    `\n${report.checks.length - failed.length}/${report.checks.length} checks passed`,
  );
  ws.close();
  chrome.kill();
  process.exit(failed.length ? 1 : 0);
};

main().catch((err) => {
  console.error(err);
  chrome.kill();
  process.exit(2);
});
