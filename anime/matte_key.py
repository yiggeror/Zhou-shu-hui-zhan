"""Key a character cel drawn on a flat key colour, and make the check sheet the matte is reviewed with.

usage: python3 anime/matte_key.py CEL.png OUT_DIR [--street STREET.png] [--boxes x,y,w,h;...]

The key colour is measured, not assumed: the median of the image border (the cel's background).  A pixel's
distance from it is measured in chroma (YCrCb Cr, Cb) and the matte is a smooth step between two thresholds
taken from that distance's robust spread on the border (the character may touch it); spill of the key colour on the character's edge is taken
out (the key channel limited to the larger of the other two, within 2 px of where the matte is not fully
opaque: an anti-aliased edge pixel can still key as opaque).

Writes OUT_DIR/cel_rgba.png (straight alpha), matte.png, key_report.md (size, measured key colour, thresholds,
how much of the matte is in between), and matte_check.jpg: for each check region (by default the topmost hair
tips, the leftmost and rightmost points (hands), the lowest points (feet), and the darkest stretch of the
silhouette edge (the black shirt against a dark street is the hard case)), 1:1 crops of the cel on its key, the
matte, and the cel over a checkerboard, black, white and the street."""
import os
import sys

import cv2
import numpy as np


def measure_key(img, border=0.02):
    h, w = img.shape[:2]
    b = max(4, int(round(min(h, w) * border)))
    ring = np.concatenate([img[:b].reshape(-1, 3), img[-b:].reshape(-1, 3), img[:, :b].reshape(-1, 3),
                           img[:, -b:].reshape(-1, 3)])
    return np.median(ring, 0), ring


def chroma(x):
    y = cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8).reshape(-1, 1, 3), cv2.COLOR_BGR2YCrCb).reshape(-1, 3)
    return y[:, 1:].astype(np.float32)


def key(img):
    """img: BGR uint8 on a flat key colour.  Returns (rgba float 0-1 straight, matte 0-1, report dict)"""
    k, ring = measure_key(img)
    kc = chroma(k[None])[0]
    d = np.linalg.norm(chroma(img.reshape(-1, 3)) - kc, axis=1).reshape(img.shape[:2])
    dr = np.linalg.norm(chroma(ring) - kc, axis=1)
    # the character may touch the border, so the background's spread is taken robustly (median + 6 MAD)
    t0 = float(np.median(dr) + 6 * 1.4826 * np.median(np.abs(dr - np.median(dr)))) + 3.0
    t1 = t0 + 18.0                                         # fully the character from here
    t = np.clip((d - t0) / (t1 - t0), 0, 1)
    a = t * t * (3 - 2 * t)
    # loose specks of key-coloured noise: drop tiny islands of either kind
    solid = (a > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid)
    small = np.zeros(n, bool)
    small[1:] = st[1:, 4] < 40
    a[small[lab]] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(1 - solid)
    small = np.zeros(n, bool)
    small[1:] = st[1:, 4] < 40
    a[small[lab]] = 1
    f = img.astype(np.float32)
    ch = int(np.argmax(k))                                 # the key channel (green for a green key)
    others = [c for c in range(3) if c != ch]
    lim = np.maximum(f[..., others[0]], f[..., others[1]])
    edge = cv2.dilate((a < 0.999).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # the edge and 2 px into it
    f[..., ch] = np.where(edge, np.minimum(f[..., ch], lim), f[..., ch])
    rgba = np.dstack([f / 255, a]).astype(np.float32)
    rep = dict(size=f'{img.shape[1]}x{img.shape[0]}', key_bgr=[round(float(v), 1) for v in k],
               key_spread_bgr=[round(float(v), 1) for v in np.percentile(np.abs(ring - k), 99, axis=0)],
               thresholds=(round(t0, 1), round(t1, 1)), opaque=float((a > 0.999).mean()),
               transparent=float((a < 0.001).mean()), between=float(((a >= 0.001) & (a <= 0.999)).mean()))
    return rgba, a, rep


def regions(a, img, size=200):
    """default check regions: hair tips (top), hands (left/right), feet (bottom), darkest silhouette edge"""
    ys, xs = np.nonzero(a > 0.5)
    pts = {'top (hair tips)': (xs[np.argmin(ys)], ys.min()), 'bottom (feet)': (xs[np.argmax(ys)], ys.max()),
           'left (hand)': (xs.min(), ys[np.argmin(xs)]), 'right (hand)': (xs.max(), ys[np.argmax(xs)])}
    edge = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    lum = cv2.blur(img.astype(np.float32).mean(2), (31, 31))
    ey, ex = np.nonzero(edge)
    i = int(np.argmin(lum[ey, ex]))
    pts['darkest edge (black clothes)'] = (ex[i], ey[i])
    h, w = a.shape
    out = {}
    for name, (x, y) in pts.items():
        x0 = int(np.clip(x - size // 2, 0, w - size))
        y0 = int(np.clip(y - size // 2, 0, h - size))
        out[name] = (x0, y0, size, size)
    return out


def checker(h, w, s=16):
    yy, xx = np.mgrid[0:h, 0:w]
    c = ((yy // s + xx // s) % 2).astype(np.float32)
    return np.dstack([0.4 + 0.3 * c] * 3)


def over(rgba, bg):
    a = rgba[..., 3:]
    return rgba[..., :3] * a + bg * (1 - a)


def main():
    cel_p, out = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    street = boxes = None
    if '--street' in args:
        street = cv2.imread(args[args.index('--street') + 1]).astype(np.float32) / 255
    if '--boxes' in args:
        boxes = {f'box {i + 1}': tuple(int(v) for v in b.split(','))
                 for i, b in enumerate(args[args.index('--boxes') + 1].split(';'))}
    os.makedirs(out, exist_ok=True)
    img = cv2.imread(cel_p)
    rgba, a, rep = key(img)
    cv2.imwrite(os.path.join(out, 'matte.png'), (a * 255 + 0.5).astype(np.uint8))
    bgra = np.dstack([rgba[..., :3], rgba[..., 3:]])
    cv2.imwrite(os.path.join(out, 'cel_rgba.png'), (np.clip(bgra, 0, 1) * 255 + 0.5).astype(np.uint8))
    h, w = a.shape
    if street is None or street.shape[:2] != (h, w):
        street = cv2.resize(street, (w, h), interpolation=cv2.INTER_AREA) if street is not None else \
            np.full((h, w, 3), 0.15, np.float32)
    bgs = {'checker': checker(h, w), 'black': np.zeros((h, w, 3), np.float32),
           'white': np.ones((h, w, 3), np.float32), 'street': street}
    regs = boxes or regions(a, img)
    rows = []
    for name, (x, y, bw, bh) in regs.items():
        sl = (slice(y, y + bh), slice(x, x + bw))
        tiles = [img[sl].astype(np.float32) / 255, np.dstack([a[sl]] * 3)] + \
                [over(rgba[sl], bgs[k][sl]) for k in bgs]
        tiles = [cv2.copyMakeBorder((np.clip(t, 0, 1) * 255).astype(np.uint8), 22, 2, 2, 2, cv2.BORDER_CONSTANT,
                                    value=(40, 40, 40)) for t in tiles]
        for t, lab in zip(tiles, ['cel on key', 'matte'] + [f'over {k}' for k in bgs]):
            cv2.putText(t, lab, (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
        row = np.hstack(tiles)
        head = np.full((24, row.shape[1], 3), 20, np.uint8)
        cv2.putText(head, f'{name}: x {x}, y {y}, {bw}x{bh} px at 1:1', (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1)
        rows.append(np.vstack([head, row]))
    cv2.imwrite(os.path.join(out, 'matte_check.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
    small = cv2.resize(np.hstack([img, (over(rgba, bgs['checker']) * 255).astype(np.uint8),
                                  (over(rgba, bgs['street']) * 255).astype(np.uint8)]), None, fx=0.4, fy=0.4,
                       interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(out, 'matte_overview.jpg'), small, [cv2.IMWRITE_JPEG_QUALITY, 88])
    with open(os.path.join(out, 'key_report.md'), 'w') as f:
        f.write(f'# key report for `{cel_p}`\n\n')
        for k, v in rep.items():
            f.write(f'- {k}: {v}\n')
        f.write('\ncheck regions (x, y, w, h):\n')
        for name, b in regs.items():
            f.write(f'- {name}: {b}\n')
    print(rep)


if __name__ == '__main__':
    main()
