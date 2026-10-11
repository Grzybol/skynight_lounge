"""
Build the runtime character animation packs for Midnight Lounge.

Reads the supplied spritesheet ZIPs (8 bartender V3 + 8 woman) (kept OUTSIDE the repo, default
~/Downloads), validates every JSON + PNG, cuts each frame out with the
EXPLICIT x/y/w/h from the metadata (never from the grid), and writes:

  <out>/<animation id>.pack   concatenated lossless-alpha WebP frames
  <out>/manifest.json         per-animation frame offsets/sizes + fps
  <out>/validation.json       frame accounting + loop-pose seam diffs

Usage (from repo root):
  python -I tools/midnight-lounge/build-character-anims.py [--zips DIR] [--out DIR] [--quality 90]
                                                            [--only woman|bartender] [--legacy-bartender]

Both source layouts are supported: the old one (`sheets` is a list of objects,
frame `sheet` is an index) and the V3 one (`sheets` is a list of file names,
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
MAP = {
    'woman_idle': 'podstawowa_v1_spritesheet',
    'woman_idle_1': 'przerywnik1_v1_spritesheet',
    'woman_idle_2': 'przerywnik2_v1_spritesheet',
    'woman_idle_3': 'przerywnik_3_v1_spritesheet',
    'woman_idle_4': 'przerywnik4_v1_spritesheet',
    'woman_mini_win': 'mini_wow_v1_spritesheet',
    'woman_big_win': 'wow_v2_spritesheet',
    'woman_mega_win': 'mega_win_spritesheet',
    # Bartender V3 (562x748, 30 sheets of 1 column x 5 rows per animation).
    'bartender_idle': 'barman_idle_1_v1_spritesheet',
    'bartender_idle_alt': 'barman_idle_2_spritesheet',
    'bartender_idle_1': 'barman_przerywnik_1_spritesheet',
    'bartender_idle_2': 'barman_przerywnik_2_spritesheet',
    'bartender_idle_3': 'barman_przerywnik_3_spritesheet',
    'bartender_mini_win': 'barman_przerywnik_mini_win_spritesheet',
    'bartender_big_win': 'barman_przerywnik_win_spritesheet',
    'bartender_mega_win': 'barman_przerywnik_mega_win_spritesheet',
    # Looping scene props (not characters): plant 562x748, bodyguard 530x792.
    'plant_loop': 'background_plant5',
    'guard_loop': 'bodyguard3',
}
# The pre-V3 bartender sources (5 sheets of 7x5, 554x740) are still readable:
LEGACY_BARTENDER = {
    'bartender_idle': 'barman_podstawiwa_v1_spritesheet',
    'bartender_idle_1': 'barman_przerywnik1_v2_spritesheet',
    'bartender_idle_2': 'barman_przerywnik2_spritesheet',
    'bartender_idle_3': 'barman_przerywnik3_spritesheet',
    'bartender_mini_win': 'barman_mini_wow_spritesheet',
    'bartender_big_win': 'barman_wow_spritesheet',
}

def encode(args):
    sheet_path, rects, quality = args
    im = Image.open(sheet_path).convert('RGBA')
    out = []
    for idx, x, y, w, h in rects:
        fr = im.crop((x, y, x + w, y + h))
        buf = io.BytesIO()
        fr.save(buf, 'WEBP', quality=quality, alpha_quality=100, method=4)
        arr = np.asarray(fr)
        out.append((idx, buf.getvalue(), arr))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zips', default=str(Path.home() / 'Downloads'))
    ROOT = Path(__file__).resolve().parents[2]
    ap.add_argument('--out', default=str(ROOT / 'frontend/apps/poc/static/assets/midnight-lounge/characters'))
    ap.add_argument('--quality', type=int, default=90)
    ap.add_argument('--only', choices=['woman', 'bartender', 'plant', 'guard'])
    ap.add_argument('--legacy-bartender', action='store_true')
    a = ap.parse_args()
    table = dict(MAP)
    if a.legacy_bartender:
        for k in [k for k in table if k.startswith('bartender_')]:
            del table[k]
        table.update(LEGACY_BARTENDER)
    if a.only:
        table = {k: v for k, v in table.items() if k.startswith(a.only + '_')}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
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
    with tempfile.TemporaryDirectory() as tmp, ProcessPoolExecutor() as pool:
        for aid, base in table.items():
            zp = Path(a.zips) / f'{base}.zip'
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
                jobs.append((str(p), by_sheet.get(name, []), a.quality))
            frames = {}
            for res in pool.map(encode, jobs):
                for idx, blob, arr in res:
                    frames[idx] = (blob, arr)
            assert sorted(frames) == list(range(150)), aid
            offsets, sizes, pos = [], [], 0
            with open(out / f'{aid}.pack', 'wb') as fp:
                for i in range(150):
                    b = frames[i][0]
                    fp.write(b); offsets.append(pos); sizes.append(len(b)); pos += len(b)
            empty = [i for i in range(150) if frames[i][1][..., 3].max() == 0]
            durs = sorted({f['duration_ms'] for f in meta['frames']})
            manifest['frames'][aid.split('_')[0]] = {'w': fw, 'h': fh}
            manifest['frame'] = manifest['frame'] or {'w': fw, 'h': fh}
            manifest['animations'][aid] = {
                'file': f'{aid}.pack', 'frames': 150, 'fps': meta['fps'],
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
    print('total frames', total, '| packs', sum(v['bytes'] for v in manifest['animations'].values()) / 1e6, 'MB')
    for k, v in report['seams'].items():
        print(f'{k:20s} last->own0 {v["lastToOwnFirst"]:6.2f}  ' + (f'last->idle0 {v["lastToIdleFirst"]:6.2f}  idleLast->first {v["idleLastToFirst"]:6.2f}' if 'lastToIdleFirst' in v else ''))

if __name__ == '__main__':
    main()
