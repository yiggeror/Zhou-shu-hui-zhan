"""Compositing for hand-drawn (Limo) animation cels.

- key():     green-screen cel -> premultiplied RGBA (tolerant key sampled from the borders, green
             spill removed from white hair / light edges, soft 1px edge)
- match():   pull a cel's colours onto a reference cel (per-channel linear fit on the regions that
             did not change), so small palette drift between drawings does not flicker
- glow():    additive light from the brightest cyan / coloured pixels of a cel (eye light, energy),
             computed from the drawing itself so it sits exactly on what was drawn
- Camera:    a held drawing can sit under a slow camera move (scale / translate / rotate), as in
             TV anime; drawings themselves are never warped
"""
import math
import cv2
import numpy as np

W, H = 1920, 1080


def load(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        a = im[..., 3:4].astype(np.float32) / 255.0
        rgb = im[..., :3][..., ::-1].astype(np.float32) / 255.0
        return np.concatenate([rgb * a, a], -1)
    return im[..., ::-1].astype(np.float32) / 255.0


def to_canvas(img, size=(1672, 941)):
    """drawings of one shot can come back a pixel or two off in size: pad / crop (never scale)
    onto the shot's canvas, anchored top-left, padding with the edge colour"""
    w, h = size
    out = img[:h, :w]
    if out.shape[0] < h or out.shape[1] < w:
        out = cv2.copyMakeBorder(out, 0, h - out.shape[0], 0, w - out.shape[1], cv2.BORDER_REPLICATE)
    return out


def key(img, tol=0.20, soft=0.10, despill=True):
    """img: RGB float (straight).  Returns premultiplied RGBA.  The key colour is the median of
    the outer border pixels that are clearly green."""
    rgb = img[..., :3]
    h, w = rgb.shape[:2]
    border = np.concatenate([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3), rgb[:, :8].reshape(-1, 3), rgb[:, -8:].reshape(-1, 3)])
    g = border[(border[:, 1] > 0.6) & (border[:, 0] < 0.4) & (border[:, 2] < 0.4)]
    kc = np.median(g, 0) if len(g) > 50 else np.array([0.0, 1.0, 0.0])
    # greenness: how much G exceeds the larger of R, B  (robust to the key's exact shade)
    gx = rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2])
    kgx = kc[1] - max(kc[0], kc[2])
    t = gx / max(kgx, 1e-3)                      # ~1 on the screen, ~0 on the character
    alpha = np.clip((1.0 - t - tol) / soft + 0.5, 0, 1) if soft > 0 else (t < 1 - tol).astype(np.float32)
    alpha = np.clip((1.0 - t) / (1.0 - tol), 0, 1) ** 1.0
    alpha[t > 1 - tol * 0.5] = 0.0
    a = alpha[..., None].astype(np.float32)
    # unmix: the edge pixel is a*fg + (1-a)*screen  ->  recover fg, then kill leftover spill
    out = np.where(a > 0.02, (rgb - (1 - a) * kc) / np.maximum(a, 0.02), rgb)
    out = np.clip(out, 0, 1)
    if despill:
        lim = np.maximum(out[..., 0], out[..., 2])
        out[..., 1] = np.minimum(out[..., 1], lim + 0.02)
        # near the matte edge the screen bleeds into the dark outline: there green may not exceed
        # the mean of red and blue (interior colours such as cyan eyes are left alone)
        bg = (alpha < 0.99).astype(np.uint8)
        band = cv2.dilate(bg, np.ones((7, 7), np.uint8)).astype(bool) & (alpha > 0.01)
        cap = (out[..., 0] + out[..., 2]) / 2 + 0.02
        g = out[..., 1]
        out[..., 1] = np.where(band, np.minimum(g, cap), g)
    # erode the matte by a hair so no screen colour survives on the outermost pixel
    a = cv2.erode(a[..., 0], np.ones((2, 2), np.uint8))[..., None]
    return np.concatenate([out * a, a], -1).astype(np.float32)


def match(cel, ref, mask=None):
    """premultiplied RGBA cel -> colours fitted to ref on the pixels where both are opaque and
    nearly the same (unchanged areas)"""
    a = cel[..., 3]
    b = ref[..., 3]
    ok = (a > 0.98) & (b > 0.98)
    c = cel[..., :3] / np.maximum(a[..., None], 1e-4)
    r = ref[..., :3] / np.maximum(b[..., None], 1e-4)
    d = np.abs(c - r).max(-1)
    ok &= d < 0.12
    if mask is not None:
        ok &= mask
    if ok.sum() < 1000:
        return cel
    out = cel.copy()
    for ch in range(3):
        x, y = c[..., ch][ok], r[..., ch][ok]
        A = np.vstack([x, np.ones_like(x)]).T
        k, m = np.linalg.lstsq(A, y, rcond=None)[0]
        out[..., ch] = np.clip(c[..., ch] * k + m, 0, 1) * a
    return out


def place(cel, scale=1.0, tx=0.0, ty=0.0, rot=0.0, size=(W, H)):
    """cel (premultiplied RGBA, any size) fitted to the frame, then camera-transformed about the
    frame centre (scale > 1 = push in; tx, ty in pixels; rot in degrees)"""
    h, w = cel.shape[:2]
    fit = min(size[0] / w, size[1] / h)
    s = fit * scale
    cx, cy = size[0] / 2, size[1] / 2
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, s)
    M[0, 2] += cx - w / 2 + tx
    M[1, 2] += cy - h / 2 + ty
    return cv2.warpAffine(cel, M, size, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def over(dst, src):
    """premultiplied src over dst (RGB or RGBA float)"""
    a = src[..., 3:4]
    if dst.shape[2] == 3:
        return src[..., :3] + dst * (1 - a)
    return src + dst * (1 - a)


def glow_mask(cel, hue='cyan', thr=0.55):
    """where the drawing itself is a strongly lit colour (e.g. the glowing irises)"""
    a = cel[..., 3]
    c = cel[..., :3] / np.maximum(a[..., None], 1e-4)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    if hue == 'cyan':
        m = np.clip((np.minimum(g, b) - r - 0.25) / 0.25, 0, 1) * np.clip((b - thr) / 0.2, 0, 1)
    elif hue == 'red':
        m = np.clip((r - np.maximum(g, b) - 0.3) / 0.25, 0, 1)
    else:
        m = np.clip((np.maximum(r, b) - g - 0.3) / 0.25, 0, 1)
    return (m * a).astype(np.float32)


def glow(mask, colour, k=1.0, radii=(6, 18, 48), weights=(0.9, 0.5, 0.25)):
    """additive light from a mask: tight core plus wider soft falloff (never a flat white blob)"""
    acc = np.zeros(mask.shape + (3,), np.float32)
    col = np.array(colour, np.float32)
    for r, wt in zip(radii, weights):
        b = cv2.GaussianBlur(mask, (0, 0), r)
        acc += b[..., None] * col * wt
    return acc * k


def tonemap(x):
    """soft highlight roll-off that keeps the hue of coloured light"""
    m = x.max(-1, keepdims=True)
    knee = 0.8
    over = np.maximum(m - knee, 0)
    m2 = np.where(m > knee, knee + (1 - knee) * (1 - np.exp(-over / (1 - knee))), m)
    return np.clip(x * (m2 / np.maximum(m, 1e-6)), 0, 1)


def grade(img, tint=(0.96, 0.985, 1.03), desat=0.12, gamma=1.0):
    """one shot-wide grade so drawn characters and painted backgrounds sit in the same light"""
    g = img.mean(-1, keepdims=True)
    out = (img * (1 - desat) + g * desat) * np.array(tint, np.float32)
    if gamma != 1.0:
        out = np.clip(out, 0, None) ** gamma
    return out


def to8(x):
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)
