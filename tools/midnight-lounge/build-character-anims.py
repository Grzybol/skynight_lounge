"""
Build the runtime character animation packs for Midnight Lounge.

Reads the supplied spritesheet ZIPs (hand-drawn pack: woman, bartender, plant, bodyguard) (kept OUTSIDE
the repo, default ~/Downloads), validates every JSON + PNG, cuts each frame out with the
EXPLICIT x/y/w/h from the metadata (never from the grid), and writes:

  <out>/<animation id>.pack   concatenated lossless-alpha WebP frames
  <out>/manifest.json         per-animation frame offsets/sizes + fps
  <out>/validation.json       frame accounting + loop-pose seam diffs

Usage (from repo root):
  python -I tools/midnight-lounge/build-character-anims.py [--zips DIR [DIR ...]] [--out DIR] [--lossy-quality N]
                                                            [--only woman|bartender|plant|guard]

Both source layouts are supported: the old one (`sheets` is a list of objects,
frame `sheet` is an index) and the current one (`sheets` is a list of file names,
frame `sheet` is the file name). `--only` rebuilds one character and merges into
the existing manifest, leaving the other character's packs byte-for-byte alone.

Why packs: a 3894x3712 RGBA sheet decodes to ~58 MB, 70 of them ~4 GB.
One pack per animation (150 frames) is fetched in one request, kept as
compressed bytes, and frames are decoded on demand by the runtime player.
"""
import argparse, io, json, os, sys, zipfile, tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from PIL import Image
import numpy as np

# animation id -> (zip basename without .zip)
# Hand-drawn pack: woman = feet2_*, bartender = barman2_* (no extra idles, one win clip for big and mega),
# plant = background_asset_plant, bodyguard = bodyguard_drawn. The bartender's mega win reuses
# `bartender_big_win` (see CHARACTER_ANIMATIONS), so it has no pack of its own.
MAP = {
    # Woman: video_converter_batch_v2 (554x740). One big-win clip serves big and mega (`woman_mega_win` has no pack).
    'woman_idle': 'feet2_podstawowa1_v2_spritesheet',
    'woman_idle_alt': 'feet2_podstawowa2_v2_spritesheet',
    'woman_idle_1': 'feet2_przerywnik1_v3_spritesheet',
    'woman_idle_2': 'feet2_przerywnik2_v2_spritesheet',
    'woman_idle_3': 'feet2_przerywnik3_v2_spritesheet',
    'woman_idle_4': 'feet2_extra_przerywnik_v11_spritesheet',
    'woman_mini_win': 'feet2_win_v2_spritesheet',
    'woman_big_win': 'feet2_bigwin_v3_spritesheet',
    'bartender_idle': 'barman2_idle_v1_spritesheet',
    'bartender_idle_1': 'barman2_przerywnik1_v1_spritesheet',
    'bartender_mini_win': 'barman2_win_v1_spritesheet',
    'bartender_big_win': 'barman2_bigwin_v1_spritesheet',
    # Looping scene props (not characters): plant 562x748, bodyguard 488x862.
    'plant_loop': 'background_prop_plant_v4',
    'guard_loop': 'bodyguard_drawn',
}
PART_BYTES = 60_000_000  # GitHub rejects files over 100 MiB: bigger packs are stored as .pack, .pack.1, ...

def split_packs(out: Path):
    """Split every pack above 90 MB into parts of at most PART_BYTES (offsets stay global)."""
    mpath = out / 'manifest.json'
    manifest = json.loads(mpath.read_text())
    for aid, entry in manifest['animations'].items():
        if 'parts' in entry:  # already split
            continue
        pack = out / entry['file']
        for stale in out.glob(entry['file'] + '.*'):
            stale.unlink()
        data = pack.read_bytes()
        if len(data) <= 90_000_000:
            entry.pop('parts', None)
            continue
        chunks = [data[i:i + PART_BYTES] for i in range(0, len(data), PART_BYTES)]
        parts = []
        for n, chunk in enumerate(chunks):
            name = entry['file'] if n == 0 else f"{entry['file']}.{n}"
            (out / name).write_bytes(chunk)
            parts.append({'file': name, 'bytes': len(chunk)})
        entry['parts'] = parts
        print(f'split {aid}: {len(data)/1e6:.1f} MB -> {len(parts)} parts')
    mpath.write_text(json.dumps(manifest, separators=(',', ':')))

def encode(args):
    sheet_path, rects, quality = args  # quality None = lossless WebP
    im = Image.open(sheet_path).convert('RGBA')
    out = []
    for idx, x, y, w, h in rects:
        fr = im.crop((x, y, x + w, y + h))
        buf = io.BytesIO()
        if quality is None:
            fr.save(buf, 'WEBP', lossless=True, quality=100, method=4)
        else:
            fr.save(buf, 'WEBP', quality=quality, alpha_quality=100, method=4)
        arr = np.asarray(fr)
        # Keep pixels only for the loop-seam check (first/last frame): 150 full frames would be GBs.
        out.append((idx, buf.getvalue(), arr if idx in (0, 149) else None, bool(arr[..., 3].max() == 0)))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zips', nargs='+', default=[str(Path.home() / 'Downloads')],
                    help='directories searched (in order) for <base>.zip')
    ROOT = Path(__file__).resolve().parents[2]
    ap.add_argument('--out', default=str(ROOT / 'frontend/apps/poc/static/assets/midnight-lounge/characters'))
    ap.add_argument('--lossy-quality', type=int, default=None,
                    help='lossy WebP quality; default is lossless (what the game ships)')
    ap.add_argument('--only', choices=['woman', 'bartender', 'plant', 'guard'])
    ap.add_argument('--split-only', action='store_true', help='only split oversized packs of an existing build')
    a = ap.parse_args()
    if a.split_only:
        split_packs(Path(a.out))
        return
    table = dict(MAP)
    if a.only:
        table = {k: v for k, v in table.items() if k.startswith(a.only + '_')}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if not a.only:
        for stale in out.glob('*.pack'):
            if stale.stem not in table:
                stale.unlink(); print('removed stale', stale.name)
    manifest = {'version': 1, 'frame': None, 'frames': {}, 'animations': {}}
    report = {'animations': {}, 'seams': {}}
    prev = out / 'manifest.json'
    if a.only and prev.exists():
        old = json.loads(prev.read_text())
        manifest['animations'] = {k: v for k, v in old['animations'].items() if not k.startswith(a.only + '_')}
        manifest['frames'] = {k: v for k, v in old.get('frames', {}).items() if k != a.only}
        manifest['frame'] = old.get('frame')
    firsts, lasts = {}, {}
    total = 0
    # 7756x7400 sheets decode to ~230 MB each: keep the pool small.
    with tempfile.TemporaryDirectory() as tmp, ProcessPoolExecutor(max_workers=3) as pool:
        for aid, base in table.items():
            zp = next((Path(dd) / f'{base}.zip' for dd in a.zips if (Path(dd) / f'{base}.zip').exists()), None)
            assert zp, f'{base}.zip not found in {a.zips}'
            d = Path(tmp) / aid
            with zipfile.ZipFile(zp) as z:
                z.extractall(d)
            meta = json.loads(next(d.glob('*.json')).read_text())
            fw, fh = meta['frame_width'], meta['frame_height']
            assert meta['frame_count'] == len(meta['frames']) == 150, aid
            assert len(meta['sheets']) >= 1
            assert [f['index'] for f in meta['frames']] == list(range(150)), f'{aid}: frame order'
            sheet_files = [sh if isinstance(sh, str) else sh['file'] for sh in meta['sheets']]
            by_sheet = {}
            for f in meta['frames']:
                assert (f['w'], f['h']) == (fw, fh), f'{aid}: frame size'
                key = f['sheet'] if isinstance(f['sheet'], str) else sheet_files[f['sheet']]
                assert key in sheet_files, f'{aid}: frame references unknown sheet {key}'
                by_sheet.setdefault(key, []).append((f['index'], f['x'], f['y'], f['w'], f['h']))
            jobs = []
            for name in sheet_files:
                p = d / name
                assert p.exists(), f'{aid}: missing {name}'
                with Image.open(p) as im:
                    assert im.mode in ('RGBA', 'LA', 'P'), f'{aid}: {name} has no alpha ({im.mode})'
                    for (_, x, y, w, h) in by_sheet.get(name, []):
                        assert x + w <= im.width and y + h <= im.height, f'{aid}: frame outside sheet'
                jobs.append((str(p), by_sheet.get(name, []), a.lossy_quality))
            frames = {}
            empties = set()
            for res in pool.map(encode, jobs):
                for idx, blob, arr, is_empty in res:
                    frames[idx] = (blob, arr)
                    if is_empty:
                        empties.add(idx)
            assert sorted(frames) == list(range(150)), aid
            offsets, sizes, pos = [], [], 0
            with open(out / f'{aid}.pack', 'wb') as fp:
                for i in range(150):
                    b = frames[i][0]
                    fp.write(b); offsets.append(pos); sizes.append(len(b)); pos += len(b)
            empty = sorted(empties)
            durs = sorted({f['duration_ms'] for f in meta['frames']})
            manifest['frames'].setdefault(aid.split('_')[0], {'w': fw, 'h': fh})
            manifest['frame'] = manifest['frame'] or {'w': fw, 'h': fh}
            manifest['animations'][aid] = {
                'file': f'{aid}.pack', 'frames': 150, 'w': fw, 'h': fh, 'fps': meta['fps'],
                'durationMs': meta['duration_ms'], 'loop': meta['loop'],
                'offsets': offsets, 'sizes': sizes, 'bytes': pos,
            }
            report['animations'][aid] = {
                'zip': zp.name, 'sheets': len(meta['sheets']), 'frameSize': [fw, fh], 'frames': 150,
                'frameDurationsMs': durs, 'emptyFrames': empty, 'packBytes': pos,
            }
            firsts[aid] = frames[0][1].astype(np.int16); lasts[aid] = frames[149][1].astype(np.int16)
            total += 150
            print(f'{aid:20s} {zp.name:46s} frames=150 pack={pos/1e6:6.2f} MB empty={empty}', flush=True)
    def diff(x, y):
        # alpha-weighted mean abs RGB diff + alpha diff, 0..255
        if x.shape != y.shape:  # clips of different resolution: compare at the smaller one
            small = x if x.shape[0] < y.shape[0] else y
            def fit(arr):
                if arr.shape == small.shape:
                    return arr
                return np.asarray(Image.fromarray(arr.astype(np.uint8)).resize((small.shape[1], small.shape[0]), Image.BILINEAR)).astype(np.int16)
            x, y = fit(x), fit(y)
        return float(np.abs(x - y).mean())
    for aid in table:
        ch = aid.split('_')[0]
        idle = f'{ch}_idle'
        if idle not in firsts:
            report['seams'][aid] = {'lastToOwnFirst': diff(lasts[aid], firsts[aid])}
            continue
        report['seams'][aid] = {
            'lastToOwnFirst': diff(lasts[aid], firsts[aid]),
            'lastToIdleFirst': diff(lasts[aid], firsts[idle]),
            'idleLastToFirst': diff(lasts[idle], firsts[aid]),
        }
    vpath = out / 'validation.json'
    if a.only and vpath.exists():
        oldr = json.loads(vpath.read_text())
        for k in ('animations', 'seams'):
            report[k] = {**{x: y for x, y in oldr.get(k, {}).items() if not x.startswith(a.only + '_')}, **report[k]}
    report['totalFrames'] = sum(v['frames'] for v in report['animations'].values())
    (out / 'manifest.json').write_text(json.dumps(manifest, separators=(',', ':')))
    (out / 'validation.json').write_text(json.dumps(report, indent=1))
    split_packs(out)
    print('total frames', total, '| packs', sum(v['bytes'] for v in manifest['animations'].values()) / 1e6, 'MB')
    for k, v in report['seams'].items():
        print(f'{k:20s} last->own0 {v["lastToOwnFirst"]:6.2f}  ' + (f'last->idle0 {v["lastToIdleFirst"]:6.2f}  idleLast->first {v["idleLastToFirst"]:6.2f}' if 'lastToIdleFirst' in v else ''))

if __name__ == '__main__':
    main()
