"""Neon line-art look for the full film (handles white flashes, white backgrounds,
coloured light and bright slash/crack lines, which the pilot never met)."""
import sys
sys.path.insert(0, "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad/pilot")
import numpy as np, cv2
from fx import W, H

TINT = np.float32([0.09, 0.03, 0.02])          # deep night blue-violet (BGR)
DARKLINE = np.float32([0.22, 0.04, 0.10])      # line colour on bright backgrounds

_CLAHE = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

def sstep(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)

def neon2(img, line_gain=1.35, fill=0.10):
    """-> (styled image, glowing line layer used for motion trails)"""
    img = np.clip(img, 0, 1.5).astype(np.float32)
    g = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY)
    # dark scenes: lift local contrast first so their drawing still turns into lines
    k = np.clip((0.45 - cv2.GaussianBlur(g, (0, 0), 30)) / 0.3, 0, 1)
    if k.max() > 0.01:
        cl = _CLAHE.apply((g * 255).astype(np.uint8)).astype(np.float32) / 255
        g2 = g * (1 - k) + cl * k
        img = np.clip(img * np.clip((g2 + 1e-3) / (g + 1e-3), 0.5, 4)[..., None], 0, 1.5)
        g = g2
    gb = cv2.bilateralFilter(cv2.bilateralFilter(g, 11, 0.12, 9), 11, 0.12, 9)
    local = cv2.GaussianBlur(gb, (0, 0), 4)
    ink = np.clip((local - gb - 0.03) / 0.12, 0, 1)                  # thin dark strokes
    glint = np.clip((gb - local - 0.06) / 0.12, 0, 1)                # thin bright strokes (slashes, cracks, rims)
    solid = np.clip((0.16 - gb) / 0.1, 0, 1) * np.clip((0.2 - local) / 0.1, 0, 1)
    edge = cv2.morphologyEx((solid > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    gm = np.abs(cv2.Sobel(gb, cv2.CV_32F, 1, 0, ksize=3)) + np.abs(cv2.Sobel(gb, cv2.CV_32F, 0, 1, ksize=3))
    edge = edge * sstep(0.5, 1.2, cv2.dilate(gm, np.ones((3, 3), np.uint8)))   # only crisp silhouettes, not soft shadow borders
    lines = np.clip(ink + edge + glint, 0, 1)
    lb = (lines > 0.35).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(lb, connectivity=8)
    keep = np.zeros(n, np.float32); keep[1:] = (st[1:, 4] >= 140).astype(np.float32)
    lines = lines * keep[lab]
    # stroke colour from the saturation-boosted local colour, default icy white
    sm = cv2.GaussianBlur(np.clip(img, 0, 1), (0, 0), 10)
    hsv = cv2.cvtColor((sm * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 2.2, 0, 255); hsv[..., 2] = 255
    col = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255
    sat = hsv[..., 1:2] / 255
    col = col * sat + np.float32([1.0, 0.92, 0.85]) * (1 - sat)
    # bright areas (white flashes, white backdrops) keep their light: they carry the beat
    Lb = cv2.GaussianBlur(g, (0, 0), 18)
    br = sstep(0.55, 0.92, Lb)[..., None]
    base = (TINT[None, None] + img * fill) * (1 - br) + img * np.float32([1.0, 0.94, 0.97]) * br
    lc = col * line_gain * (1 - br) + DARKLINE * br
    L3 = lines[..., None]
    out = base * (1 - L3 * 0.9) + L3 * lc
    # saturated light (cursed energy, orbs, sky glow) stays a luminous fill
    hsv0 = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    e = sstep(0.38, 0.7, hsv0[..., 1] / 255) * sstep(0.3, 0.62, hsv0[..., 2] / 255)
    e = cv2.GaussianBlur(e.astype(np.float32), (0, 0), 2.5)[..., None]
    out = out * (1 - e * 0.65) + img * e * 1.1
    glow = L3 * col * (1 - br) * (1 - e)
    return out, glow, e[..., 0]
