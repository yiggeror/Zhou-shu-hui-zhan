"""Review a continuous window of redrawn frames against the original (flicker check).

usage: python3 anime/review_window.py DELIVERY_DIR F0 F1 OUT_DIR [crop x,y,w,h]

DELIVERY_DIR holds R_nNNNN.png for every n in [F0, F1) (frame-number convention in collab/README.md).
Writes to OUT_DIR:
  side_by_side.mp4   original | redraw, 24 fps, played 3 times
  redraw.mp4         the redraw alone at its own size, 24 fps, played 3 times
  crop_1to1.mp4      a 1:1 detail crop, original | redraw, 24 fps, played 3 times
  diff_sheet.jpg     per adjacent pair: original change | redraw change | change of (redraw - original)
  metrics.md         the same as numbers

The key number is the last one.  E_n = redraw_n - original_n is everything the redraw adds or removes
(hatching, cleaned lines, removed watermark).  If that layer stays put from frame to frame, the redraw
moves exactly like the original; if it jumps, that is flicker.  The original's own change is the
yardstick: in a shot where only the energy edge moves, |dE| should stay well below |dO| everywhere
except at that edge."""
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as FR  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIRS = [os.path.join(REPO, 'collab/to_limo', d) for d in sorted(os.listdir(os.path.join(REPO, 'collab/to_limo')))
            if d.endswith('_ref')]


def original(n, size):
    for d in REF_DIRS:
        p = os.path.join(d, f'n{n:04d}.png')
        if os.path.exists(p):
            im = cv2.imread(p)
            break
    else:
        im = FR.frame(n)
    return cv2.resize(im, size, interpolation=cv2.INTER_AREA)


def heat(d, vmax):
    v = np.clip(d / vmax, 0, 1)
    return cv2.applyColorMap((v * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)


def label(im, text):
    cv2.putText(im, text, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
    cv2.putText(im, text, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return im


def write_mp4(path, imgs, loops=3):
    h, w = imgs[0].shape[:2]
    h2, w2 = h + h % 2, w + w % 2
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w2}x{h2}', '-r', '24',
                          '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p', path],
                         stdin=subprocess.PIPE)
    for _ in range(loops):
        for im in imgs:
            p.stdin.write(cv2.copyMakeBorder(im, 0, h2 - h, 0, w2 - w, cv2.BORDER_REPLICATE).tobytes())
    p.stdin.close()
    p.wait()


def main():
    src, f0, f1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    os.makedirs(out, exist_ok=True)
    ns = list(range(f0, f1))
    R = []
    for n in ns:
        p = os.path.join(src, f'R_n{n:04d}.png')
        if not os.path.exists(p):
            sys.exit(f'missing {p}')
        R.append(cv2.imread(p))
    h, w = R[0].shape[:2]
    R = [r if r.shape[:2] == (h, w) else cv2.resize(r, (w, h), interpolation=cv2.INTER_AREA) for r in R]
    O = [original(n, (w, h)) for n in ns]

    # videos
    sw, sh = 960, int(round(960 * h / w))
    write_mp4(os.path.join(out, 'side_by_side.mp4'),
              [np.hstack([label(cv2.resize(o, (sw, sh), interpolation=cv2.INTER_AREA), f'orig n{n}'),
                          label(cv2.resize(r, (sw, sh), interpolation=cv2.INTER_AREA), f'redraw n{n}')])
               for n, o, r in zip(ns, O, R)])
    write_mp4(os.path.join(out, 'redraw.mp4'), R)
    if len(sys.argv) > 5:
        cx, cy, cw, ch = (int(v) for v in sys.argv[5].split(','))
    else:   # the most detailed region of the first redraw
        g = cv2.cvtColor(R[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
        e = cv2.boxFilter(np.abs(cv2.Laplacian(g, cv2.CV_32F)), -1, (480, 270))
        cy, cx = np.unravel_index(np.argmax(e[135:h - 135, 240:w - 240]), (h - 270, w - 480))
        cw, ch = 480, 270
    write_mp4(os.path.join(out, 'crop_1to1.mp4'),
              [np.hstack([label(o[cy:cy + ch, cx:cx + cw].copy(), f'orig n{n}'), label(r[cy:cy + ch, cx:cx + cw].copy(), 'redraw')])
               for n, o, r in zip(ns, O, R)])

    # adjacent-frame change
    def gray(im):
        return cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.5)
    Og, Rg = [gray(o) for o in O], [gray(r) for r in R]
    E = [r - o for r, o in zip(Rg, Og)]
    rows, lines = [], []
    tw, th = 420, int(round(420 * h / w))
    vmax = 24.0
    lines.append('| pair | orig change | redraw change | change of (redraw - orig) | ratio | worst 1% of (redraw - orig) change |')
    lines.append('|---|---|---|---|---|---|')
    for i in range(len(ns) - 1):
        dO = np.abs(Og[i + 1] - Og[i])
        dR = np.abs(Rg[i + 1] - Rg[i])
        dE = np.abs(E[i + 1] - E[i])
        ratio = dE.mean() / max(dO.mean(), 0.05)
        lines.append(f'| n{ns[i]}->{ns[i + 1]} | {dO.mean():.2f} | {dR.mean():.2f} | {dE.mean():.2f} | {ratio:.2f} | '
                     f'{np.percentile(dE, 99):.1f} |')
        tiles = [label(cv2.resize(heat(d, vmax), (tw, th), interpolation=cv2.INTER_AREA), f'{name} n{ns[i]}->{ns[i + 1]}')
                 for d, name in ((dO, 'orig'), (dR, 'redraw'), (dE, 'redraw-orig'))]
        rows.append(np.hstack(tiles))
    cv2.imwrite(os.path.join(out, 'diff_sheet.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    with open(os.path.join(out, 'metrics.md'), 'w') as f:
        f.write(f'# flicker check [{f0}, {f1}), {len(ns)} frames, {w}x{h}\n\n'
                f'Mean absolute change of a 1.5 px blurred grey image between adjacent frames (0-255).\n'
                f'"ratio" = change of (redraw - orig) / orig change; well under 1 means the redraw moves like the original.\n'
                f'crop for crop_1to1.mp4: x={cx} y={cy} w={cw} h={ch}\n\n')
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
