/**
 * Unit tests for the character animation logic that has no DOM:
 * playback timeline math, idle scheduling rules, win arbitration and the
 * controller state machine (against a fake player).
 *
 *   node --experimental-transform-types --import ./tools/midnight-lounge/register.mjs tools/midnight-lounge/test-characters.ts
 */
import assert from "node:assert/strict";

import {
  frameAt,
  isFinished,
  stallShiftMs,
} from "../../frontend/apps/poc/src/game/loungeCharacters/timeline.ts";
import {
  nextVariationDelayMs,
  pickVariation,
  winMayStart,
} from "../../frontend/apps/poc/src/game/loungeCharacters/idleScheduler.ts";
import {
  CHARACTER_ANIMATIONS,
  CHARACTER_TUNING,
  animationIdsFor,
  PROP_ANIMATION,
  PROP_TUNING,
} from "../../frontend/apps/poc/src/game/loungeCharacters/config.ts";
import { categoryForTier, categoryForWinX } from "../../frontend/apps/poc/src/game/loungeCharacters/loungeWinCue.ts";
import { CharacterController } from "../../frontend/apps/poc/src/game/loungeCharacters/CharacterController.ts";

let passed = 0;
const test = async (name: string, fn: () => void | Promise<void>) => {
  await fn();
  passed += 1;
  console.log(`ok  ${name}`);
};

// ---- timeline -------------------------------------------------------------
await test("frameAt is time based, not rAF based", () => {
  assert.equal(frameAt(0, 30, 150, true), 0);
  assert.equal(frameAt(33, 30, 150, true), 0);
  assert.equal(frameAt(34, 30, 150, true), 1);
  assert.equal(frameAt(1000, 30, 150, true), 30);
  assert.equal(
    frameAt(5000, 30, 150, true),
    0,
    "loop wraps at 150 frames / 5 s",
  );
  assert.equal(
    frameAt(5000, 30, 150, false),
    150,
    "one-shot clamps to frames (finished)",
  );
  assert.equal(frameAt(-5, 30, 150, true), 0);
});

await test("isFinished flips exactly after 150 frames at 30 fps", () => {
  assert.equal(isFinished(4966, 30, 150), false);
  assert.equal(isFinished(5000, 30, 150), true);
});

await test("long gaps are shifted, short gaps are not", () => {
  assert.equal(stallShiftMs(16, 30), 0);
  assert.equal(stallShiftMs(250, 30), 0);
  const shift = stallShiftMs(10_000, 30);
  assert.ok(
    shift > 9900 && shift < 10_000,
    "hidden tab does not fast-forward the clip",
  );
});

// ---- scheduler ------------------------------------------------------------
await test("variation delay stays inside the configured window", () => {
  for (const t of Object.values(CHARACTER_TUNING)) {
    assert.equal(
      nextVariationDelayMs(t.idleVariationMinMs, t.idleVariationMaxMs, () => 0),
      t.idleVariationMinMs,
    );
    assert.equal(
      nextVariationDelayMs(
        t.idleVariationMinMs,
        t.idleVariationMaxMs,
        () => 0.999999,
      ),
      t.idleVariationMaxMs,
    );
  }
  assert.ok(CHARACTER_TUNING.woman.idleVariationMinMs >= 15_000);
  assert.ok(CHARACTER_TUNING.bartender.idleVariationMaxMs <= 30_000);
});

await test("never repeats the same variation back to back", () => {
  const vars = CHARACTER_ANIMATIONS.woman.variations;
  let seed = 1;
  const rng = () =>
    (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
  let last: string | null = null;
  const seen = new Set<string>();
  for (let i = 0; i < 2000; i++) {
    const v = pickVariation(vars, last, rng)!;
    assert.notEqual(v, last);
    seen.add(v);
    last = v;
  }
  assert.equal(seen.size, vars.length, "every variation is reachable");
  assert.equal(pickVariation([], null, rng), null);
  assert.equal(pickVariation(["only"], "only", rng), "only");
});

await test("win priority: higher interrupts, equal or lower do not", () => {
  assert.equal(winMayStart(null, 1), true);
  assert.equal(winMayStart(1, 2), true);
  assert.equal(winMayStart(2, 2), false);
  assert.equal(winMayStart(3, 1), false);
});

// ---- mapping --------------------------------------------------------------
await test("tier -> category mapping reuses existing celebration tiers", () => {
  assert.equal(categoryForTier("none"), null);
  assert.equal(categoryForTier("big"), "big");
  for (const t of ["mega", "super", "max", "worldRecord"] as const) {
    assert.equal(categoryForTier(t), "mega");
  }
});

await test("animation table: 7 woman + 3 bartender clips, every win category uses the win clip", () => {
  assert.equal(animationIdsFor("woman").length, 7);
  assert.equal(animationIdsFor("bartender").length, 3);
  assert.equal(CHARACTER_ANIMATIONS.bartender.wins.mega, CHARACTER_ANIMATIONS.bartender.wins.big);
  assert.deepEqual(CHARACTER_ANIMATIONS.bartender.variations, ["bartender_idle_1"]);
  assert.ok(CHARACTER_ANIMATIONS.woman.variations.includes("woman_idle_alt"));
  assert.equal(CHARACTER_ANIMATIONS.woman.wins.mega, CHARACTER_ANIMATIONS.woman.wins.big);
});

await test("weighted variation pick respects weights and still avoids repeats", () => {
  let seed = 3;
  const rng = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
  const vars = ["a", "b", "c"];
  const counts: Record<string, number> = { a: 0, b: 0, c: 0 };
  for (let i = 0; i < 3000; i++) counts[pickVariation(vars, null, rng, { a: 8, b: 1, c: 1 })!]++;
  assert.ok(counts.a > counts.b * 4);
  assert.notEqual(pickVariation(vars, "a", rng, { a: 100 }), "a");
});

// ---- controller against a fake player -------------------------------------
type Call = {
  id: string;
  loop: boolean;
  resolve: (ok: boolean) => void;
  opts: any;
};
const fakePlayer = () => {
  const calls: Call[] = [];
  let active: string | null = null;
  const player = {
    get activeId() {
      return active;
    },
    play(id: string, opts: any) {
      return new Promise<boolean>((resolve) => {
        calls.push({
          id,
          loop: opts.loop,
          opts,
          resolve: (ok) => {
            if (ok) active = id;
            resolve(ok);
          },
        });
      });
    },
    prepare: () => Promise.resolve(true),
    pause() {},
    resume() {},
    destroy() {},
    getStats: () => ({}) as any,
  };
  return { player, calls };
};
const tick = () => new Promise((r) => setTimeout(r, 0));
const quiet = { warmMiniDelayMs: 1e9, rng: () => 0.5 };

await test("controller: starts default idle as a loop and does not restart it", async () => {
  const f = fakePlayer();
  const c = new CharacterController("woman", f.player as any, quiet);
  c.start();
  assert.equal(f.calls[0].id, "woman_idle");
  assert.equal(f.calls[0].loop, true);
  f.calls[0].resolve(true);
  await tick();
  assert.equal(f.calls.length, 1);
  c.destroy();
});

await test("controller: every win category plays the one win clip once; requests for the playing clip are absorbed", async () => {
  for (const ch of ["woman", "bartender"] as const) {
    const f = fakePlayer();
    const c = new CharacterController(ch, f.player as any, quiet);
    c.start();
    f.calls[0].resolve(true);
    await tick();
    assert.equal(c.requestWin("mini"), true);
    const win = f.calls[1];
    assert.equal(win.id, `${ch}_mini_win`);
    assert.equal(win.loop, false);
    assert.equal(win.opts.pingPong, false, "win clips play once");
    win.resolve(true);
    await tick();
    // The counter later crosses the big and mega thresholds: same clip, nothing restarts.
    assert.equal(c.requestWin("big"), true);
    assert.equal(c.requestWin("mega", { turbo: true }), true);
    assert.equal(f.calls.length, 2, "the playing clip was not touched");
    win.opts.onComplete();
    await tick();
    assert.equal(c.getState().mode, "idle");
    assert.equal(f.calls.at(-1)!.id, `${ch}_idle`);
    // A big win on its own starts the same clip, also once.
    f.calls.at(-1)!.resolve(true);
    await tick();
    c.requestWin("mega");
    assert.equal(f.calls.at(-1)!.id, `${ch}_mini_win`);
    assert.equal(f.calls.at(-1)!.opts.pingPong, false);
    c.destroy();
  }
});

await test("controller: a stale completion from a replaced clip is ignored", async () => {
  const f = fakePlayer();
  const c = new CharacterController("woman", f.player as any, quiet);
  c.start();
  f.calls[0].resolve(true);
  await tick();
  c.requestWin("mini");
  const mini = f.calls[1];
  mini.resolve(true);
  await tick();
  mini.opts.onComplete();
  await tick();
  c.requestWin("big");
  const n = f.calls.length;
  mini.opts.onComplete(); // old clip reports again
  await tick();
  assert.equal(f.calls.length, n, "old completion started nothing");
  assert.equal(c.getState().winCategory, "big");
  c.destroy();
});

await test("win counter categories: mini only above the bet", () => {
  const th = { big: 10, mega: 50 };
  assert.equal(categoryForWinX(0, th), null);
  assert.equal(categoryForWinX(0.5, th), null);
  assert.equal(categoryForWinX(1, th), null, "a win equal to the bet is not above it");
  assert.equal(categoryForWinX(1.01, th), "mini");
  assert.equal(categoryForWinX(9.99, th), "mini");
  assert.equal(categoryForWinX(10, th), "big");
  assert.equal(categoryForWinX(50, th), "mega");
  assert.equal(categoryForWinX(1000, th), "mega");
});

await test("controller: a failed clip load falls back to idle", async () => {
  const f = fakePlayer();
  const c = new CharacterController("woman", f.player as any, quiet);
  c.start();
  f.calls[0].resolve(true);
  await tick();
  const warn = console.warn;
  console.warn = () => {};
  c.requestWin("big");
  f.calls[1].resolve(false);
  await tick();
  console.warn = warn;
  assert.equal(c.getState().mode, "idle");
  c.destroy();
});

await test("controller: idle variations fire on a timer, play once, return to idle, never repeat", async () => {
  const t = CHARACTER_TUNING.bartender;
  const saved = [t.idleVariationMinMs, t.idleVariationMaxMs];
  const savedLoops = [t.idleLoopsMin, t.idleLoopsMax];
  t.idleLoopsMin = undefined; // exercise the time-based fallback
  t.idleLoopsMax = undefined;
  t.idleVariationMinMs = 20;
  t.idleVariationMaxMs = 20;
  try {
    const f = fakePlayer();
    let seed = 7;
    const rng = () =>
      (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
    const c = new CharacterController("bartender", f.player as any, {
      warmMiniDelayMs: 1e9,
      rng,
    });
    c.start();
    f.calls[0].resolve(true);
    const played: string[] = [];
    for (let i = 0; i < 6; i++) {
      const before = f.calls.length;
      await new Promise((r) => setTimeout(r, 60));
      const v = f.calls[before];
      assert.ok(v, "a variation was requested");
      assert.equal(v.loop, false, "variation plays exactly once");
      assert.ok(CHARACTER_ANIMATIONS.bartender.variations.includes(v.id));
      played.push(v.id);
      v.resolve(true);
      await tick();
      assert.equal(c.getState().mode, "variation");
      v.opts.onComplete();
      await tick();
      assert.equal(c.getState().mode, "idle");
      const idle = f.calls.at(-1)!;
      assert.equal(idle.id, "bartender_idle");
      idle.resolve(true);
      await tick();
    }
    // With a single variation (the current bartender) repeating is the only option.
    if (CHARACTER_ANIMATIONS.bartender.variations.length > 1) {
      for (let i = 1; i < played.length; i++)
        assert.notEqual(played[i], played[i - 1]);
    }
    c.destroy();
  } finally {
    [t.idleVariationMinMs, t.idleVariationMaxMs] = saved;
    [t.idleLoopsMin, t.idleLoopsMax] = savedLoops;
  }
});

await test("controller: a win during a variation wins and cancels the pending variation timer", async () => {
  const t = CHARACTER_TUNING.bartender;
  const saved = [t.idleVariationMinMs, t.idleVariationMaxMs];
  const savedLoops = [t.idleLoopsMin, t.idleLoopsMax];
  t.idleLoopsMin = undefined; // exercise the time-based fallback
  t.idleLoopsMax = undefined;
  t.idleVariationMinMs = 20;
  t.idleVariationMaxMs = 20;
  try {
    const f = fakePlayer();
    const c = new CharacterController("bartender", f.player as any, quiet);
    c.start();
    f.calls[0].resolve(true);
    await tick();
    assert.equal(c.requestWin("big"), true);
    const n = f.calls.length;
    await new Promise((r) => setTimeout(r, 80));
    assert.equal(
      f.calls.length,
      n,
      "no variation started while the win is active",
    );
    c.destroy();
  } finally {
    [t.idleVariationMinMs, t.idleVariationMaxMs] = saved;
    [t.idleLoopsMin, t.idleLoopsMax] = savedLoops;
  }
});

await test("woman: idle loops 1-4 whole times then a variation; clips trimmed 0.2 s per end", async () => {
  const t = CHARACTER_TUNING.woman;
  assert.equal(t.trimHeadFrames, 6);
  assert.equal(t.trimTailFrames, 6);
  assert.ok(t.idleLoopsMin === 1 && t.idleLoopsMax === 4);
  for (const rngValue of [0, 0.999]) {
    const f = fakePlayer();
    const c = new CharacterController("woman", f.player as any, { warmMiniDelayMs: 1e9, rng: () => rngValue });
    c.start();
    const idle = f.calls[0];
    idle.resolve(true);
    await tick();
    const want = rngValue === 0 ? 1 : 4;
    for (let loop = 1; loop < want; loop++) {
      idle.opts.onLoop(loop);
      assert.equal(c.getState().mode, "idle", `still idle after ${loop} loops`);
    }
    idle.opts.onLoop(want);
    await tick();
    assert.equal(c.getState().mode, "variation", `variation after ${want} loops`);
    assert.equal(f.calls.at(-1)!.loop, false);
    c.destroy();
  }
});

await test("bartender: main idle loops only 1-2 times before a variation", async () => {
  const t = CHARACTER_TUNING.bartender;
  assert.ok(t.idleLoopsMin === 1 && t.idleLoopsMax === 2);
  for (const rngValue of [0, 0.999]) {
    const f = fakePlayer();
    const c = new CharacterController("bartender", f.player as any, { warmMiniDelayMs: 1e9, rng: () => rngValue });
    c.start();
    const idle = f.calls[0];
    idle.resolve(true);
    await tick();
    const want = rngValue === 0 ? 1 : 2;
    for (let loop = 1; loop < want; loop++) {
      idle.opts.onLoop(loop);
      assert.equal(c.getState().mode, "idle");
    }
    idle.opts.onLoop(want);
    await tick();
    assert.equal(c.getState().mode, "variation", `variation after ${want} loops`);
    c.destroy();
  }
});

await test("win clips drop their first 0.1 s (3 frames) for both characters; props configured", () => {
  assert.equal(CHARACTER_TUNING.woman.winTrimHeadFrames, 6);
  assert.equal(CHARACTER_TUNING.bartender.winTrimHeadFrames, 3);
  assert.equal(CHARACTER_TUNING.bartender.trimHeadFrames, 3);
  assert.equal(CHARACTER_TUNING.bartender.trimTailFrames, 3);
  assert.equal(PROP_TUNING.guard.trimHeadFrames, 3, "bodyguard: 0.1 s off the start");
  assert.equal(PROP_TUNING.guard.trimTailFrames, 3, "bodyguard: 0.1 s off the end");
  assert.equal(PROP_ANIMATION.plant, "plant_loop");
  assert.equal(PROP_ANIMATION.guard, "guard_loop");
});

await test("celebration timing: big and above 4+1 s (5 s), turbo 3.4+1.5 s", async () => {
  const m = await import("../../frontend/apps/poc/src/game/skyjump_v2/winPresentation.ts");
  assert.equal(m.v2WinCountUpMs({ tier: "big" }), 4000);
  assert.equal(m.v2WinHoldMs({ tier: "big" }), 1000);
  for (const tier of ["mega", "super", "max", "worldRecord"] as const) {
    assert.equal(m.v2WinCountUpMs({ tier }), 4000, tier);
    assert.equal(m.v2WinHoldMs({ tier }), 1000, tier);
  }
  for (const tier of ["big", "mega", "max"] as const) {
    assert.equal(m.v2WinCountUpMs({ tier, turbo: true }), 3400);
    assert.equal(m.v2WinHoldMs({ tier, turbo: true }), 1500);
  }
  assert.equal(m.v2WinCountUpMs({ tier: "mega", catchUp: true }), 0);
});

await test("controller: nothing is requested after destroy", async () => {
  const f = fakePlayer();
  const c = new CharacterController("bartender", f.player as any, quiet);
  c.start();
  f.calls[0].resolve(true);
  c.destroy();
  assert.equal(c.requestWin("big"), false);
  await tick();
  assert.equal(f.calls.length, 1);
});

console.log(`\n${passed} tests passed`);
