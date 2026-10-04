"""Render one layered shot and every review file from ONE run, and record what produced them.

usage: python3 anime/package_shot.py PANEL.png OUT_DIR [--shot s0|s1] [--ref N]

OUT_DIR gets: frames/R_n0073..R_n0090.png, side_by_side.mp4, crop_1to1.mp4, rebuilt_only.mp4 (3 loops, labelled),
sequence.jpg (all frames, original above rebuilt), layers_nXX.jpg (flame alpha, flame colour, panel lines shown
through the flame, ink, FX on flat grey) for a few frames per shot, and run.json (code hashes, git commit, panel hash,
reference frame, parameters).  A camera check on left-out frames is a separate run (anime/validate_shot0_camera.py
for shot 0) because it needs its own camera estimate without those frames."""
import hashlib
import json
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layered as S0  # noqa: E402
import review_window as RW  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LAYER_FRAMES = {'s0': (74, 75, 82, 88), 's1': (92, 93, 100, 106)}


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def tile(x, name, crop, k=1.0, size=(475, 395)):
    x = np.asarray(x, np.float32)
    if x.ndim == 2:
        x = np.dstack([x, x, x])
    y0, y1, x0, x1 = crop
    v = np.clip(x[y0:y1, x0:x1] * k * 255, 0, 255).astype(np.uint8)
    v = cv2.resize(v, size, interpolation=cv2.INTER_AREA)
    cv2.putText(v, name, (4, 16), 0, 0.45, (0, 0, 0), 3)
    cv2.putText(v, name, (4, 16), 0, 0.45, (0, 255, 255), 1)
    return v


def main():
    panel_path, out = sys.argv[1], sys.argv[2]
    S0.configure(sys.argv[sys.argv.index('--shot') + 1] if '--shot' in sys.argv else 's0')
    if '--ref' in sys.argv:
        S0.REF = int(sys.argv[sys.argv.index('--ref') + 1])
    os.makedirs(os.path.join(out, 'frames'), exist_ok=True)
    panel = cv2.imread(panel_path).astype(np.float32) / 255
    vig = S0.vignette()
    O = {n: S0.orig(n) for n in range(S0.F0, S0.F1)}
    o_ref = O[S0.REF]
    panel = S0.prepare_panel(panel, o_ref, vig)
    fields = S0.camera_fields(O)
    gains = S0.smooth_ramp({n: S0.exposure(n, O[n], o_ref, fields[n]) for n in range(S0.F0, S0.F1)})
    R, layers = {}, {}
    for n in range(S0.F0, S0.F1):
        L = {}
        img = S0.render(panel, n, O[n], o_ref, gains[n], vig, fields[n], L)
        R[n] = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
        cv2.imwrite(os.path.join(out, 'frames', f'R_n{n:04d}.png'), R[n])
        if n in LAYER_FRAMES[S0.SHOT]:
            layers[n] = L

    # videos, from the same frames
    ns = list(range(S0.F0, S0.F1))
    Ob = {n: np.clip(O[n] * 255 + 0.5, 0, 255).astype(np.uint8) for n in ns}
    sw, sh = 960, int(round(960 * S0.H / S0.W))
    RW.write_mp4(os.path.join(out, 'side_by_side.mp4'),
                 [np.hstack([RW.label(cv2.resize(Ob[n], (sw, sh), interpolation=cv2.INTER_AREA), f'orig n{n}'),
                             RW.label(cv2.resize(R[n], (sw, sh), interpolation=cv2.INTER_AREA), f'rebuilt n{n}')])
                  for n in ns])
    RW.write_mp4(os.path.join(out, 'rebuilt_only.mp4'), [R[n] for n in ns])
    cx, cy, cw, ch = 380, 430, 720, 420
    RW.write_mp4(os.path.join(out, 'crop_1to1.mp4'),
                 [np.hstack([RW.label(Ob[n][cy:cy + ch, cx:cx + cw].copy(), f'orig n{n}'),
                             RW.label(R[n][cy:cy + ch, cx:cx + cw].copy(), 'rebuilt')]) for n in ns])

    # sequence sheet
    t = []
    for n in ns:
        a = cv2.resize(Ob[n], (418, 235), interpolation=cv2.INTER_AREA)
        b = cv2.resize(R[n], (418, 235), interpolation=cv2.INTER_AREA)
        cv2.putText(a, f'orig n{n}', (4, 16), 0, 0.45, (0, 255, 255), 1)
        cv2.putText(b, f'rebuilt n{n}', (4, 16), 0, 0.45, (0, 255, 255), 1)
        t.append(np.vstack([a, b]))
    while len(t) % 6:
        t.append(np.zeros_like(t[0]))
    cv2.imwrite(os.path.join(out, 'sequence.jpg'), np.vstack([np.hstack(t[i:i + 6]) for i in range(0, len(t), 6)]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])

    # layer views
    crop = (150, 941, 500, 1450)
    for n, L in layers.items():
        k = 2.5 if n < S0.FADE_END else 1.0
        row = [tile(O[n], f'orig n{n}' + (' x2.5' if k > 1 else ''), crop, k),
               tile(R[n] / 255.0, 'rebuilt' + (' x2.5' if k > 1 else ''), crop, k),
               tile(L['core'], 'flame alpha', crop), tile(L['fill_colour'], 'flame colour (from orig)', crop),
               tile(L['lines'] * 3, f'panel lines in flame x3 (strength {L["line_strength"]:.2f})', crop),
               tile(L['ink'], 'ink', crop), tile(L['fx_on_flat'], 'FX on flat grey' + (' x2.5' if k > 1 else ''),
                                                 crop, k)]
        cv2.imwrite(os.path.join(out, f'layers_n{n}.jpg'), np.hstack(row), [cv2.IMWRITE_JPEG_QUALITY, 85])

    try:
        commit = subprocess.run(['git', '-C', HERE, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(['git', '-C', HERE, 'status', '--porcelain', 'anime'], capture_output=True,
                                    text=True).stdout.strip())
    except OSError:
        commit, dirty = '?', True
    run = dict(git_commit=commit, anime_dir_had_uncommitted_changes=dirty,
               code_sha256={f: sha(os.path.join(HERE, f)) for f in ('layered.py', 'flowcam.py', 'package_shot.py')},
               panel=os.path.relpath(panel_path, os.path.dirname(HERE)), panel_sha256=sha(panel_path),
               shot=S0.SHOT, reference_frame=S0.REF, frames=[S0.F0, S0.F1], fade_end=S0.FADE_END, flame=S0.FLAME,
               size=[S0.W, S0.H],
               params=dict(SIGMA_PARALLAX=S0.SIGMA_PARALLAX, REFINE=S0.REFINE, FOCUS=S0.FOCUS,
                           HOLDOUT=sorted(S0.HOLDOUT), BLOOM=list(S0.BLOOM), GLOW=S0.GLOW.round(4).tolist(),
                           WATERMARK=[[S0.WATERMARK[0].start, S0.WATERMARK[0].stop],
                                      [S0.WATERMARK[1].start, S0.WATERMARK[1].stop]]),
               exposure={n: round(float(gains[n]), 4) for n in ns},
               line_strength={n: round(float(layers[n]['line_strength']), 3) for n in layers},
               fade_steps={f'n{S0.FADE_END - 1 - i}->n{S0.FADE_END - i}': e for i, e in enumerate(S0.FADE_LOG)})
    json.dump(run, open(os.path.join(out, 'run.json'), 'w'), indent=1)
    print(json.dumps(run, indent=1)[:1500])


if __name__ == '__main__':
    main()
