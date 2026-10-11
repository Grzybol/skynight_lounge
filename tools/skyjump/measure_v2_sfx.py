"""Measure V2/legacy SFX total vs audible duration; optional WAV runtime trims."""
from __future__ import annotations

import json
import struct
import wave
from pathlib import Path

import miniaudio
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIRS = [
	ROOT / "frontend/apps/poc/static/assets/audio/skyjump/sfx/v2",
	ROOT / "frontend/apps/poc/static/assets/audio/skyjump/sfx/legacy_v1",
]
THR_DB = -40
PAD_SEC = 0.08
OUT_JSON = ROOT / "docs/skyjump-v2/audio_duration_measure.json"
TRIM_DIR = ROOT / "frontend/apps/poc/static/assets/audio/skyjump/sfx/v2_trimmed"


def decode(path: Path):
	decoded = miniaudio.decode_file(str(path))
	# decoded.samples is memoryview of interleaved int16/float
	fmt = decoded.sample_format
	chans = decoded.nchannels
	rate = decoded.sample_rate
	raw = np.frombuffer(decoded.samples, dtype=np.int16).astype(np.float64)
	if chans > 1:
		raw = raw.reshape((-1, chans)).mean(axis=1)
	return raw, rate, chans


def analyze(path: Path) -> dict:
	samples, rate, _chans = decode(path)
	total = len(samples) / float(rate) if rate else 0.0
	if samples.size == 0:
		return {
			"file": path.name,
			"dir": path.parent.name,
			"totalSec": 0,
			"audibleStartSec": 0,
			"audibleEndSec": 0,
			"audibleSec": 0,
			"leadSec": 0,
			"trailSec": 0,
			"peakDbfs": -99,
			"problematicTail": False,
		}
	peak = float(np.max(np.abs(samples)) + 1e-12)
	thr = peak * (10 ** (THR_DB / 20.0))
	nz = np.where(np.abs(samples) >= thr)[0]
	if len(nz) == 0:
		aud_start = aud_end = 0.0
	else:
		aud_start = float(nz[0] / rate)
		aud_end = float((nz[-1] + 1) / rate)
	trail = max(0.0, total - aud_end)
	aud_len = max(0.0, aud_end - aud_start)
	peak_db = 20.0 * np.log10(peak / 32768.0)
	problematic = trail >= 0.4 and aud_len < total * 0.55
	return {
		"file": path.name,
		"dir": path.parent.name,
		"totalSec": round(total, 3),
		"audibleStartSec": round(aud_start, 3),
		"audibleEndSec": round(aud_end, 3),
		"audibleSec": round(aud_len, 3),
		"leadSec": round(aud_start, 3),
		"trailSec": round(trail, 3),
		"peakDbfs": round(float(peak_db), 1),
		"problematicTail": problematic,
		"sampleRate": rate,
	}


def write_trimmed_wav(src: Path, dest: Path, audible_end_sec: float) -> float:
	samples, rate, chans = decode(src)
	end = int(min(len(samples), (audible_end_sec + PAD_SEC) * rate))
	end = max(end, int(0.12 * rate))
	clip = samples[:end].astype(np.int16)
	# short fade-out
	fade = min(int(0.04 * rate), len(clip) // 4)
	if fade > 0:
		ramp = np.linspace(1.0, 0.0, fade)
		clip[-fade:] = (clip[-fade:].astype(np.float64) * ramp).astype(np.int16)
	dest.parent.mkdir(parents=True, exist_ok=True)
	with wave.open(str(dest), "wb") as w:
		w.setnchannels(1)
		w.setsampwidth(2)
		w.setframerate(rate)
		w.writeframes(clip.tobytes())
	return end / float(rate)


def main() -> None:
	rows: list[dict] = []
	for d in DIRS:
		if not d.exists():
			continue
		for p in sorted(d.glob("*.mp3")):
			rows.append(analyze(p))

	print(f"{'file':42} {'tot':>6} {'aud':>6} {'trail':>6} {'pkdB':>6} bad")
	for r in rows:
		flag = "YES" if r["problematicTail"] else ""
		print(
			f"{r['file']:42} {r['totalSec']:6.2f} {r['audibleSec']:6.2f} "
			f"{r['trailSec']:6.2f} {r['peakDbfs']:6.1f} {flag}"
		)

	OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
	OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
	print(f"\nWrote {OUT_JSON}")

	meta: dict[str, dict] = {}
	trimmed: list[str] = []
	for r in rows:
		key = r["file"]
		meta[key] = {
			"totalSec": r["totalSec"],
			"audibleSec": r["audibleSec"],
			"audibleEndSec": r["audibleEndSec"],
			"trailSec": r["trailSec"],
			"problematicTail": r["problematicTail"],
			"peakDbfs": r["peakDbfs"],
			"dir": r["dir"],
		}
		if r["problematicTail"] and r["dir"] == "v2":
			src = ROOT / "frontend/apps/poc/static/assets/audio/skyjump/sfx/v2" / r["file"]
			# Keep .mp3 name but write wav companion; catalog will prefer trimmed wav
			dest = TRIM_DIR / (Path(r["file"]).stem + ".wav")
			dur = write_trimmed_wav(src, dest, r["audibleEndSec"])
			meta[key]["trimmedWav"] = dest.name
			meta[key]["trimmedSec"] = round(dur, 3)
			trimmed.append(dest.name)
			print(f"TRIMMED {r['file']} -> {dest.name} ({dur:.2f}s)")

	meta_path = (
		ROOT
		/ "frontend/apps/poc/src/game/skyjump_v2/audioDurationMeta.json"
	)
	# Also write TS-friendly JSON next to audio.ts consumers
	meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
	print(f"TRIMMED_COUNT {len(trimmed)}")
	print(f"Wrote {meta_path}")


if __name__ == "__main__":
	main()
