"""Side-by-side comparison of a short frame range: the original next to one or more rendered windows (the compositor's
native frames R_n<n>.png), one row per frame, brightened for dark shots.  Writes OUT.jpg, OUT_24fps_x4.mp4 (the range
looped 4 times at 24 fps) and OUT_slow_4fps.mp4.  Labels come from the column names only.
usage: python3 anime/gap_compare.py OUT A B GAIN 'label=DIR[;n=PATH,...]' ['label=DIR' ...]
  DIR holds R_n<n>.png for every frame in [A, B); ';n=PATH' replaces frame n of that column by another native PNG
  (e.g. the no-wipe R4 column: 'no wipe=out;1482=out/R_n1481.png').  The first column is always the original."""
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as FR  # noqa: E402

PW, PH = 560, 315


def label(im, t):
    im = im.copy()
    (tw, th), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(im, (0, 0), (tw + 10, th + 10), (0, 0, 0), -1)
    cv2.putText(im, t, (5, th + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return im


def panel(im, gain):
    return cv2.resize(np.clip(im[:941].astype(np.float32) * gain, 0, 255).astype(np.uint8), (PW, PH),
                      interpolation=cv2.INTER_AREA)


def main():
    out, a, b, gain = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
    cols = []
    for spec in sys.argv[5:]:
        name, rest = spec.split('=', 1)
        d, *swaps = rest.split(';')
        sw = dict((int(k), v) for k, v in (s.split('=', 1) for s in ','.join(swaps).split(',') if s))
        cols.append((name, d, sw))
    orig = FR.frames(a, b)
    rows = []
    for n in range(a, b):
        tiles = [label(panel(orig[n], gain), f'original n{n} (x{gain:g})')]
        for name, d, sw in cols:
            im = cv2.imread(sw.get(n, os.path.join(d, f'R_n{n}.png')))
            tiles.append(label(panel(im, gain), f'{name} n{n}'))
        rows.append(np.hstack(tiles))
    cv2.imwrite(out + '.jpg', np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
    k = len(rows)
    with tempfile.TemporaryDirectory() as tmp:
        for i, r in enumerate(rows):
            cv2.imwrite(os.path.join(tmp, f'{i:03d}.png'), cv2.copyMakeBorder(r, 0, 1, 0, 0, cv2.BORDER_REPLICATE))
        enc = ['-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p']
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '24', '-i', os.path.join(tmp, '%03d.png'), '-vf',
                        f'loop=3:size={k}:start=0,setpts=N/24/TB', *enc, out + '_24fps_x4.mp4'], check=True)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '4', '-i', os.path.join(tmp, '%03d.png'), *enc,
                        out + '_slow_4fps.mp4'], check=True)
    print(f'{out}.jpg / _24fps_x4.mp4 / _slow_4fps.mp4: {k} frames x {len(cols) + 1} columns')


if __name__ == '__main__':
    main()
