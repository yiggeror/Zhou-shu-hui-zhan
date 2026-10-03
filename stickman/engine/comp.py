"""Compositing: base + emissive + bloom, hue-preserving highlight roll-off (never clips
coloured light to flat white), output 8-bit."""
import cv2
import numpy as np
from .theme import T as THEME, PAPER_MODE


def bloom(G, strength=1.0):
    g = G
    h, w = g.shape[:2]
    half = cv2.resize(g, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(half)
    cur = half
    weights = (0.55, 0.45, 0.35, 0.28, 0.2)
    for i, wt in enumerate(weights):
        cur = cv2.resize(cur, (max(1, cur.shape[1] // 2), max(1, cur.shape[0] // 2)), interpolation=cv2.INTER_AREA)
        bl = cv2.GaussianBlur(cur, (0, 0), 1.6)
        acc += wt * cv2.resize(bl, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(acc, (w, h), interpolation=cv2.INTER_LINEAR) * strength


def tonemap(x, knee=0.72, white_mix=0.18):
    """x: HxWx3 linear-ish. Below `knee` untouched. Above, the max channel rolls off smoothly
    toward 1 while keeping hue; only very hot light drifts slightly toward white."""
    m = x.max(axis=-1)
    span = 1.0 - knee
    over = np.maximum(m - knee, 0, dtype=np.float32)
    m2 = np.where(m > knee, knee + span * (1 - np.exp(-over / span)), m).astype(np.float32)
    sc = m2 / np.maximum(m, 1e-6)
    y = x * sc[..., None]
    hot = m > 1.0
    if hot.any():
        heat = (np.clip((m - 1.0) / 2.5, 0, 1) * white_mix).astype(np.float32)
        y += (m2 - y.transpose(2, 0, 1)).transpose(1, 2, 0) * heat[..., None] if False else (m2[..., None] - y) * heat[..., None]
    return np.clip(y, 0, 1, out=y)


_VIG = {}


def vignette_mask(h, w, amount):
    key = (h, w, round(amount, 3))
    if key not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
        _VIG[key] = (1 - amount * np.clip(r - 0.35, 0, None) / 1.65).astype(np.float32)[..., None]
    return _VIG[key]


def impact_frame(fr):
    """two-tone impact frame built from the layers: whatever is drawn (figures, props) becomes
    one tone, the paper the other; strongly coloured energy keeps its hue as a flat accent.
    mode 'pos' = ink on paper, 'neg' = paper on ink (or explicit bg/fg colours)."""
    im = fr.impact
    B = fr.B[..., :3]
    G = fr.G
    bgc = np.array(THEME['bg'], np.float32)
    d = np.abs(B - bgc).max(-1)
    m = np.clip((d - im.get('thr', 0.35)) / 0.08, 0, 1)
    ga = np.clip((G[..., 3] - im.get('ethr', 0.45)) / 0.15, 0, 1)
    mode = im.get('mode', 'pos')
    if 'bg' in im:
        bg, fg = np.array(im['bg'], np.float32), np.array(im['fg'], np.float32)
    elif mode == 'pos':
        bg, fg = np.array(THEME['tone_bg'], np.float32), np.array(THEME['tone_fg'], np.float32)
    else:
        bg, fg = np.array(THEME['tone_fg'], np.float32), np.array(THEME['tone_bg'], np.float32)
    out = bg * (1 - m[..., None]) + fg * m[..., None]
    if im.get('energy', True):
        rgb = G[..., :3] / np.maximum(G[..., 3:4], 1e-3)
        mx = rgb.max(-1)
        mn = rgb.min(-1)
        sat = np.clip((mx - mn - 0.25) / 0.15, 0, 1) * ga
        hue = rgb / np.maximum(mx[..., None], 1e-4)
        out = out * (1 - sat[..., None]) + hue * sat[..., None]
    return out


def composite(fr, vignette=0.22, grain=0.0, seed=0):
    if PAPER_MODE:
        vignette = min(vignette, 0.05)
    B = fr.B[..., :3]
    G = fr.G[..., :3]
    if fr.impact is not None:
        img = impact_frame(fr)
        for fn in fr.post:
            img = fn(img)
        return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    Bl = bloom(fr.G, fr.bloom)
    Ga = np.clip(fr.G[..., 3:4] + Bl[..., 3:4], 0.0, 1.0)
    img = B * (1.0 - Ga) + G + Bl[..., :3]
    img *= fr.exposure
    for fn in fr.post:
        img = fn(img)
    img = tonemap(img)
    if vignette > 0:
        img *= vignette_mask(img.shape[0], img.shape[1], vignette)
    if grain > 0:
        rng = np.random.default_rng(seed)
        img += (rng.standard_normal(img.shape[:2]).astype(np.float32) * grain)[..., None]
    out = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    return out
