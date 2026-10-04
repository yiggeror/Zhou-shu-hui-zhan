"""Assemble a redrawn action window from an exposure sheet: every exposure is one drawing.

A window is described by an exposure sheet (JSON):
  {"name": "shots42-44", "frames": [1248, 1284],
   "frames_sheet": {
      "1264": {"drawing": "collab/from_limo/023/pilot_001/D07_n1264.png", "id": "D07"},
      "1267": {"hold": "D10", "plate": ".../D10_n1267_noFX.png", "full": ".../D10_n1267.png", "ref": 1267},
      "1276": {"hold": "D14p", ..., "provisional": "why"},
      ...}}
Every frame of the window must be listed.
  drawing  a complete drawing (characters, background, its own drawn effects), shown unchanged
  hold     one drawing held for several frames.  Its effect-free version (plate, drawn in the framing of source
           frame ref) is moved by ONE full-frame perspective transform per frame (the camera, measured on the
           original by feature matching; no local warping; one extra zoom for the whole hold, at most MAX_ZOOM, keeps
           the drawing's edges out of frame, and what still shows is filled with its smeared edge colours, logged),
           blurred along that same camera path where the original is blurred (length fitted per frame), lit by
           the light the full drawing has over the plate (a smooth quadratic field; a strong drawn light such as
           D04's purple wash fades as the original's does) times the original's change of brightness, and the
           original's flames of this frame are rebuilt on top as a TEMPORARY source-derived effect: their shape,
           colour and glow, opaque (the old drawing inside them is not taken, and the plate's inferred parts under
           them stay covered)

usage: python3 anime/action_window.py SHEET.json OUT_DIR
Writes OUT_DIR/R_nNNNN.png, side_by_side.mp4 (24 fps), slow_6fps.mp4, holds_diag_6fps.mp4 (original | effect-free
base | effects alone | result, hold frames only), contact_sheet.jpg, sources.md, run.json."""
import hashlib
import json
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as FR  # noqa: E402
import layered as L  # noqa: E402
import review_window as RW  # noqa: E402

W, H = L.W, L.H
SHUTTERS = (0.0, 0.05, 0.1, 0.15, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0)   # blur length along the camera path, in frame intervals
LINES_THROUGH = 0.0   # the plate's lines inside the rebuilt flame: off, so the parts of the plate that are only
                      # inferred (hidden under the flame in the full drawing) stay covered (Limo, completion_001)
MAX_ZOOM = 1.06                               # at most this much zoom to keep the drawing's edges out of frame


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- flames of the original (temporary effect source)

def _core(o, colour):
    L.FLAME = colour
    a = L.flame_core(o)
    L.FLAME = 'cyan'
    return a


def _pink(o, seed):
    """the red flame under purple light turns pink and falls below the red gate: grow the red core into connected
    pink-red, saturated, bright pixels within 90 px of it (n1254-1257)"""
    hsv = cv2.cvtColor(o, cv2.COLOR_BGR2HSV_FULL)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    hr = np.minimum(np.abs(h - 350), 360 - np.abs(h - 350))
    near = cv2.dilate((seed > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (181, 181)))
    c = (((hr < 22) & (s > 0.35) & (v > 0.45)).astype(np.uint8) & near) | (seed > 0.5).astype(np.uint8)
    c = cv2.morphologyEx(c, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab = cv2.connectedComponents(c)
    sd = np.zeros(n, bool)
    sd[np.unique(lab[seed > 0.5])] = True
    sd[0] = False
    g = sd[lab].astype(np.uint8)
    ff = g.copy()
    cv2.floodFill(ff, np.zeros((g.shape[0] + 2, g.shape[1] + 2), np.uint8), (0, 0), 1)
    return cv2.GaussianBlur((g | (ff == 0)).astype(np.float32), (0, 0), 1.5)


def flames(o):
    """soft alpha of the cyan and red flames in an original frame; small dark patches enclosed by a flame (the old
    drawing's dark parts seen through it, up to 2500 px) are flame here, not holes"""
    red = _core(o, 'red')
    a = np.maximum(np.maximum(_core(o, 'cyan'), red), _pink(o, red))
    body = (a > 0.5).astype(np.uint8)
    ff = body.copy()
    cv2.floodFill(ff, np.zeros((body.shape[0] + 2, body.shape[1] + 2), np.uint8), (0, 0), 1)
    holes = (ff == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(holes)
    small_ = np.zeros(n, bool)
    small_[1:] = st[1:, 4] <= 2500
    return np.maximum(a, cv2.GaussianBlur(small_[lab].astype(np.float32), (0, 0), 1.5))


def fx_layer(o, a, plate_lines):
    """the flame rebuilt from original frame o: colour (the old drawing inside it removed), the plate's lines through it
    at the strength the old lines had, and its glow on the surroundings.  Returns (fill, glow, colour, strength)."""
    # the old drawing seen through the flame (lines, and darker hands or fists up to ~25 px across) is closed away;
    # anything left darker than 80 % of the flame's bright colour nearby is replaced by that colour (the darker,
    # the more), so no old body shape remains
    oc = cv2.morphologyEx(o, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    cw = a.copy()
    cw[L.WATERMARK] = 0

    def ncb(sig):
        return cv2.GaussianBlur(oc * cw[..., None], (0, 0), sig), cv2.GaussianBlur(cw, (0, 0), sig)[..., None]
    (n4, w4), (n30, w30) = ncb(4), ncb(30)
    t = np.clip(w4 / 0.5, 0, 1)
    colour = t * n4 / np.maximum(w4, 1e-3) + (1 - t) * n30 / np.maximum(w30, 1e-3)
    lc = L.lum(colour)
    bright = cw * (lc > np.median(lc[cw > 0.5])) if (cw > 0.5).any() else cw
    wb = cv2.GaussianBlur(bright, (0, 0), 30)
    typical = cv2.GaussianBlur(colour * bright[..., None], (0, 0), 30) / np.maximum(wb, 1e-3)[..., None]
    far = cv2.GaussianBlur(colour * bright[..., None], (0, 0), 120) / np.maximum(cv2.GaussianBlur(bright, (0, 0), 120), 1e-3)[..., None]
    typical = np.where((wb > 0.05)[..., None], typical, far)          # the flame's own bright colour nearby
    floor = 0.8 * L.lum(typical)
    k = np.clip((floor - lc) / np.maximum(floor, 1e-3), 0, 1)[..., None]
    colour = colour * (1 - k) + typical * k
    old = np.clip((L.lum(oc) - L.lum(o)) / np.maximum(L.lum(oc), 0.05), 0, 1)
    inner = (a > 0.9) & (cw > 0)
    strength = float(np.clip(old[inner].mean() / max(plate_lines[inner].mean(), 1e-3), 0.05, 0.45)) \
        if inner.sum() > 500 else 0.2
    fill = colour * (1 - strength * plate_lines[..., None])
    lit = colour * a[..., None]
    glow = L.BLOOM[0] * cv2.GaussianBlur(lit, (0, 0), 20) + L.BLOOM[1] * cv2.GaussianBlur(lit, (0, 0), 60)
    return fill, glow, colour, strength


# ---------------------------------------------------------------- camera: one perspective transform per frame

_sift = cv2.SIFT_create(6000)


def feature_mask(o, a=None):
    """where features may be taken: not flame (they change every frame), not the screen-fixed watermark"""
    a = flames(o) if a is None else a
    m = (cv2.dilate((a > 0.05).astype(np.uint8), np.ones((15, 15), np.uint8)) == 0).astype(np.uint8) * 255
    m[L.WATERMARK] = 0
    return m


def match_h(a, b, ma, mb, ratio=0.75, thr=2.0):
    """perspective transform a -> b from SIFT matches (RANSAC thr px); returns (H, inliers, median error px)"""
    ga = cv2.cvtColor(np.clip(a * 255, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(np.clip(b * 255, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    ka, da = _sift.detectAndCompute(ga, ma)
    kb, db = _sift.detectAndCompute(gb, mb)
    if da is None or db is None or len(ka) < 8 or len(kb) < 8:
        return None, 0, np.inf
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < ratio * n.distance]
    if len(good) < 8:
        return None, 0, np.inf
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    Hm, inl = cv2.findHomography(pa, pb, cv2.RANSAC, thr)
    if Hm is None:
        return None, 0, np.inf
    inl = inl.ravel().astype(bool)
    err = np.linalg.norm(cv2.perspectiveTransform(pa[inl][None], Hm)[0] - pb[inl], axis=1)
    return Hm, int(inl.sum()), float(np.median(err))


def describe(Hm):
    """scale, rotation and shift of the transform at the frame centre"""
    c = np.float32([[[W / 2, H / 2], [W / 2 + 10, H / 2], [W / 2, H / 2 + 10]]])
    p = cv2.perspectiveTransform(c, Hm)[0]
    ex, ey = (p[1] - p[0]) / 10, (p[2] - p[0]) / 10
    s = float(np.sqrt(abs(ex[0] * ey[1] - ex[1] * ey[0])))
    r = float(np.degrees(np.arctan2(ex[1], ex[0])))
    return s, r, (float(p[0][0] - W / 2), float(p[0][1] - H / 2))


def overscan(Hs):
    """the smallest zoom about the frame centre (one for the whole hold) at which the moved plate covers the whole
    frame in every frame, so no edge of the drawing is ever shown"""
    corners = np.float32([[[0, 0], [W, 0], [0, H], [W, H], [W / 2, 0], [W / 2, H], [0, H / 2], [W, H / 2]]])

    def covers(c):
        C = np.array([[c, 0, (1 - c) * W / 2], [0, c, (1 - c) * H / 2], [0, 0, 1]])
        for Hm in Hs.values():
            q = cv2.perspectiveTransform(corners, np.linalg.inv(C @ Hm))[0]
            if (q[:, 0] < -0.5).any() or (q[:, 0] > W + 0.5).any() or (q[:, 1] < -0.5).any() or (q[:, 1] > H + 0.5).any():
                return False
        return True
    lo, hi = 1.0, MAX_ZOOM
    if covers(lo):
        return 1.0
    if not covers(hi):
        return hi
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if covers(mid) else (mid, hi)
    return hi


def _edges(x):
    g = L.lum(x)
    return cv2.GaussianBlur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (0, 0), 2)


def agreement(o_ref, o, Hm, m):
    """normalised correlation of edge strength between the moved reference frame and frame n, on mask m"""
    a = _edges(cv2.warpPerspective(o_ref, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))[m]
    b = _edges(o)[m]
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / max(np.sqrt((a * a).sum() * (b * b).sum()), 1e-6))


def hold_camera(O, A, ref, ns, raw, region=None):
    """H[n]: ref -> n (display pixels) for the frames of a hold, one perspective transform per frame.  Features
    are matched on the full-resolution original (flames and watermark left out); candidates are the match
    straight to ref, the match chained through the previous frame (subject features, and whole frame), and the
    previous transform; the one under which the previous frame, moved on to n, agrees best with frame n (edge
    correlation) is used.  region (x0, y0, x1, y1 in ref
    display pixels) limits the features to the subject."""
    sx, sy = raw[ref].shape[1] / W, raw[ref].shape[0] / H
    S = np.diag([sx, sy, 1.0])
    Si = np.linalg.inv(S)
    big = (raw[ref].shape[1], raw[ref].shape[0])

    def bigmask(m):
        return cv2.resize(m, big, interpolation=cv2.INTER_NEAREST)

    def full(n):
        return raw[n].astype(np.float32) / 255
    mref = feature_mask(O[ref], A[ref])
    if region is not None:
        r = np.zeros_like(mref)
        x0, y0, x1, y1 = region
        r[y0:y1, x0:x1] = 255
        mref &= r
    Hs, info, prev = {ref: np.eye(3)}, {ref: 'reference frame'}, ref
    for n in ns:
        if n == ref:
            continue
        mn = feature_mask(O[n], A[n])
        cands = []
        Hd, id_, ed = match_h(full(ref), full(n), bigmask(mref), bigmask(mn), thr=3.0)
        if Hd is not None and id_ >= 12:
            cands.append((Si @ Hd @ S, f'matched to n{ref}: {id_} inliers, median error {ed * 1 / sx:.2f} px'))
        mprev = cv2.warpPerspective(mref, Hs[prev], (W, H), flags=cv2.INTER_NEAREST) & feature_mask(O[prev], A[prev])
        Hc, ic, ec = match_h(full(prev), full(n), bigmask(mprev), bigmask(mn), thr=3.0)
        if Hc is not None and ic >= 12:
            cands.append((Si @ Hc @ S @ Hs[prev], f'chained via n{prev}: {ic} inliers, median error {ec / sx:.2f} px'))
        if region is not None or mprev.mean() < 0.9 * 255 * (mn > 0).mean():
            Hw, iw, ew = match_h(full(prev), full(n), bigmask(feature_mask(O[prev], A[prev])), bigmask(mn), thr=3.0)
            if Hw is not None and iw >= 12:
                cands.append((Si @ Hw @ S @ Hs[prev], f'chained via n{prev} (whole frame): {iw} inliers, median '
                                                      f'error {ew / sx:.2f} px'))
        cands.append((Hs[prev], f'previous transform (n{prev}) kept'))
        m = mn > 0
        # judged against the previous frame (less has changed there than since ref)
        scored = [(agreement(O[prev], O[n], Hc_ @ np.linalg.inv(Hs[prev]), m), Hc_, t) for Hc_, t in cands]
        sc, Hs[n], t = max(scored, key=lambda x: x[0])
        info[n] = f'{t}; edge agreement with n{prev} {sc:.3f} (other candidates: ' + \
            ', '.join(f'{x[0]:.3f}' for x in scored if x[2] != t) + ')'
        prev = n
    return Hs, info


def register_plate(plate, o_ref):
    """the plate is drawn in the framing of the reference frame but not pixel-locked to it: one perspective
    transform plate -> reference frame (identity if the match is weak)"""
    Hm, inl, err = match_h(plate, o_ref, None, feature_mask(o_ref), ratio=0.8)
    if Hm is None or inl < 50:
        return np.eye(3), f'identity (weak match: {inl} inliers)'
    s, r, c = describe(Hm)
    return Hm, f'{inl} inliers, median error {err:.2f} px; scale {s:.4f}, rotation {r:+.2f} deg, centre shift ' \
               f'({c[0]:+.1f}, {c[1]:+.1f}) px'


# ---------------------------------------------------------------- camera blur along the measured path

def interp(H0, H1, t):
    a, b = H0 / H0[2, 2], H1 / H1[2, 2]
    return (1 - t) * a + t * b


def moved(img, Hm, flags=cv2.INTER_CUBIC):
    """img moved by Hm; where the drawing does not reach (its edge came into frame) its edge colours are smeared
    in, softly (the plate has no margin beyond the source framing)"""
    out = cv2.warpPerspective(img, Hm, (W, H), flags=flags, borderMode=cv2.BORDER_REPLICATE)
    valid = cv2.warpPerspective(np.ones(img.shape[:2], np.float32), Hm, (W, H), flags=cv2.INTER_LINEAR)
    if valid.min() > 0.999:
        return out
    soft = cv2.GaussianBlur(out, (0, 0), 25)
    v = cv2.GaussianBlur((valid > 0.999).astype(np.float32), (0, 0), 3)[..., None]
    return out * v + soft * (1 - v)


def path_blur(img, Hprev, Hcur, shutter, samples=None):
    """img moved by Hcur, averaged over the camera path back towards Hprev for `shutter` frame intervals"""
    if shutter <= 0:
        return moved(img, Hcur)
    # sample density: about one sample per 1.5 px of the largest displacement along the path
    corners = np.float32([[[0, 0], [W, 0], [0, H], [W, H], [W / 2, H / 2]]])
    d = np.linalg.norm(cv2.perspectiveTransform(corners, Hcur)[0] - cv2.perspectiveTransform(corners, Hprev)[0], axis=1)
    k = samples or int(np.clip(d.max() * shutter / 1.5, 3, 64))
    acc = np.zeros((H, W, img.shape[2]), np.float32)
    for t in np.linspace(1 - shutter, 1, k):
        acc += moved(img, interp(Hprev, Hcur, t), cv2.INTER_LINEAR)
    return acc / k


def _energy(x, m):
    g = L.lum(cv2.resize(x, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    return float(e[m].mean())


def fit_shutter(o_ref, o, Hprev, Hcur, mask):
    """the shutter (blur length along the camera path) that makes the original's reference frame, moved along the
    path, as soft as the original's frame n.  Matched on edge energy (mean gradient), away from flames and the
    watermark, so that a changed detail does not pass for blur; measured back in the reference framing, so that a
    zoom-in's enlargement does not pass for blur either.  0 unless frame n is clearly softer (< 0.85)."""
    back = np.linalg.inv(Hcur)
    m = cv2.warpPerspective(mask, back, (W, H), flags=cv2.INTER_NEAREST)
    m = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST) > 0
    if m.sum() < 1000:
        return 0.0, 1.0, {0.0: 1.0}

    def e(x):
        return _energy(cv2.warpPerspective(x, back, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), m)
    e0 = e(path_blur(o_ref, Hprev, Hcur, 0))
    target = e(o) / max(e0, 1e-6)
    ratios = {0.0: 1.0}
    if target >= 0.85:
        return 0.0, target, ratios
    for s in SHUTTERS[1:]:
        ratios[s] = e(path_blur(o_ref, Hprev, Hcur, s, samples=24)) / max(e0, 1e-6)
    best = min(ratios, key=lambda k: abs(ratios[k] - target))
    return best, target, ratios


# ---------------------------------------------------------------- light

def poly_gain(src, dst, m, step=4):
    """dst / src per colour channel as exp(quadratic in x, y), fitted robustly on mask m: a smooth light change
    that cannot carry any shape, line or edge"""
    yy, xx = np.mgrid[0:H:step, 0:W:step]
    mm = m[::step, ::step]
    if mm.sum() < 200:
        return np.ones((H, W, 3), np.float32), None
    x, y = (xx[mm] / W - 0.5) * 2, (yy[mm] / H - 0.5) * 2
    X = np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], 1)
    Y, X_ = np.mgrid[0:H, 0:W]
    gx, gy = (X_ / W - 0.5) * 2, (Y / H - 0.5) * 2
    G = np.stack([np.ones_like(gx), gx, gy, gx * gx, gx * gy, gy * gy], -1).astype(np.float32)
    out, coefs = np.ones((H, W, 3), np.float32), []
    for c in range(3):
        t = np.log(np.maximum(dst[::step, ::step, c][mm], 0.01)) - np.log(np.maximum(src[::step, ::step, c][mm], 0.01))
        keep = np.ones(len(t), bool)
        for _ in range(3):
            k, *_ = np.linalg.lstsq(X[keep], t[keep], rcond=None)
            r = t - X @ k
            mad = np.median(np.abs(r[keep] - np.median(r[keep]))) + 1e-4
            keep = np.abs(r) < 2.5 * 1.4826 * mad
        out[..., c] = np.exp(G @ k.astype(np.float32))
        coefs.append(k)
    return np.clip(out, 0.4, 2.5), np.array(coefs)


def light_of_full(full, plate):
    """the light the full drawing has over its effect-free version (e.g. D04's purple wash), as a smooth field;
    measured on flat, lit areas; the drawn flames with a 45 px band and the red flame glow are left out (the
    rebuilt flame brings its own glow)"""
    hsv = cv2.cvtColor(full, cv2.COLOR_BGR2HSV_FULL)
    hr = np.minimum(np.abs(hsv[..., 0] - 350), 360 - np.abs(hsv[..., 0] - 350))
    fx = cv2.dilate((flames(full) > 0.3).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45)))
    flat = (_edges(plate) < 0.08) & (_edges(full) < 0.08)
    m = (fx == 0) & (L.lum(plate) > 0.10) & flat & ~((hr < 20) & (hsv[..., 1] > 0.3))
    return poly_gain(plate, full, m)


def _lowpass(img, m, sig=30):
    a = cv2.GaussianBlur(img * m[..., None], (0, 0), sig)
    w = cv2.GaussianBlur(m.astype(np.float32), (0, 0), sig)
    return a / np.maximum(w, 1e-3)[..., None], w


def light_change(o, o_ref_moved, a, a_ref_moved):
    """the original's change of light since the reference frame (e.g. the purple wash fading out), smooth:
    the ratio of the two frames' local means (30 px, flames and a 30 px band around them left out, so that small
    misfits and changed details do not count), fitted with exp(quadratic in x, y) per colour channel"""
    fx = cv2.dilate(((a > 0.05) | (a_ref_moved > 0.05)).astype(np.uint8),
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    m = fx == 0
    m[L.WATERMARK] = False
    on, wn = _lowpass(o, m)
    orf, _ = _lowpass(o_ref_moved, m)
    return poly_gain(orf, on, m & (wn > 0.5) & (L.lum(orf) > 0.05))


WASH = 0.25      # the full drawing's added light is followed frame by frame only when it is this strong (std of log)


def frame_light(light0, change, o, o_ref_moved, a, a_ref_moved):
    """this frame's light.  Where the full drawing adds a strong light of its own (D04's purple wash), it is raised
    to w (1 = all of it, 0 = none) and times one brightness gain g for all colours, fitted to the original's
    change since ref (log change = (w - 1) log light0 + log g, least squares over the frame): the drawn light fades
    as the original's does, without tinting the drawing in a colour of its own.  Otherwise the drawing's light is
    kept (w = 1) and g is the original's change of mean brightness, away from the flames (a sliding character
    or a changed detail cannot pump it)."""
    L0 = np.log(light0[::4, ::4]).reshape(-1)
    if L0.std() < WASH:
        m = (a < 0.05) & (a_ref_moved < 0.05)
        m[L.WATERMARK] = False
        v = float(np.log(max(L.lum(o)[m].mean(), 1e-4) / max(L.lum(o_ref_moved)[m].mean(), 1e-4)))
        u = 0.0
    else:
        Lc = np.log(change[::4, ::4]).reshape(-1)
        X = np.stack([L0, np.ones_like(L0)], 1)
        (u, v), *_ = np.linalg.lstsq(X, Lc, rcond=None)
        u = float(np.clip(u, -1.0, 0.2))
        v = float((Lc - u * L0).mean())
    w = 1 + u
    return np.exp(w * np.log(light0) + v).astype(np.float32), w, np.float32([v, v, v])


# ---------------------------------------------------------------- assembly

def load(p):
    im = cv2.imread(p).astype(np.float32) / 255
    return im if im.shape[:2] == (H, W) else cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def to8(x):
    return np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8)


def small(x, label=None, w=836):
    im = cv2.resize(to8(x) if x.dtype != np.uint8 else x, (w, int(round(w * H / W))), interpolation=cv2.INTER_AREA)
    return RW.label(im, label) if label else im


def render_holds(name, hn, fs, O, A, raw):
    spec = fs[hn[0]]
    ref = spec['ref']
    plate, full = load(spec['plate']), load(spec['full'])
    Hp, preg = register_plate(plate, O[ref])
    light0, _ = light_of_full(*(cv2.warpPerspective(x, Hp, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
                                for x in (full, plate)))
    ns = sorted(set(hn) | {ref})
    Hs, cinfo = hold_camera(O, A, ref, ns, raw, spec.get('region'))
    zoom = overscan({n: Hs[n] @ Hp for n in hn})
    C = np.array([[zoom, 0, (1 - zoom) * W / 2], [0, zoom, (1 - zoom) * H / 2], [0, 0, 1]])
    edge_px = {n: 100 * float((cv2.warpPerspective(np.ones((H, W), np.float32), C @ Hs[n] @ Hp, (W, H)) < 0.999).mean())
               for n in hn}
    out = {}
    prev = None
    for n in ns:
        if n not in hn:
            prev = n
            continue
        Hn = Hs[n]
        Hprev = Hs[prev] if prev is not None else Hn
        fmask = (feature_mask(O[n], A[n]) > 0).astype(np.uint8)
        shutter, target, ratios = fit_shutter(O[ref], O[n], Hprev, Hn, fmask) if prev is not None else (0.0, 1.0, {})
        o_ref_moved = cv2.warpPerspective(O[ref], Hn, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        a_ref_moved = cv2.warpPerspective(A[ref], Hn, (W, H), flags=cv2.INTER_LINEAR)
        lc, _ = light_change(O[n], o_ref_moved, A[n], a_ref_moved)
        light0_moved = cv2.warpPerspective(light0, Hn, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        light, w, bgain = frame_light(light0_moved, lc, O[n], o_ref_moved, A[n], a_ref_moved)
        base = path_blur(plate, Hprev @ Hp, Hn @ Hp, shutter) * light
        lp = L.lum(base)
        lines = LINES_THROUGH * np.clip((cv2.GaussianBlur(lp, (0, 0), 4) - lp) / 0.12, 0, 1)
        a = A[n]
        fill, glow, colour, strength = fx_layer(O[n], a, lines)
        a3 = a[..., None]
        res = (base + glow * (1 - a3)) * (1 - a3) + fill * a3
        fx_only = glow * (1 - a3) + colour * a3          # the effect alone, plate lines OFF

        def zoomed(x):
            return x if zoom == 1.0 else cv2.warpPerspective(x, C, (W, H), flags=cv2.INTER_CUBIC,
                                                             borderMode=cv2.BORDER_REFLECT)
        s, r, c = describe(C @ Hn)
        out[n] = dict(R=zoomed(res), base=zoomed(base), fx=zoomed(fx_only), src=(
            f'{name} repeat exposure (hold, ref n{ref}){" PROVISIONAL: " + spec["provisional"] if spec.get("provisional") else ""}; '
            f'plate `{spec["plate"]}` (registered to n{ref}: {preg}); light of the full drawing `{spec["full"]}` '
            f'over the plate (smooth: exp of a quadratic in x, y per colour channel), kept at {w:.2f} of its strength '
            f'as the original\'s light changes n{ref}->n{n}, brightness gain {float(np.exp(bgain[0])):.3f}; '
            f'camera (one perspective transform; measured {cinfo[n]}; whole hold zoomed {zoom:.3f} about the centre to '
            f'keep the drawing\'s edges out of frame (at most {MAX_ZOOM}; beyond that its edge colours are smeared in: '
            f'{edge_px[n]:.1f}% of this frame)): at the centre scale {s:.4f}, rotation {r:+.2f} deg, shift ({c[0]:+.1f}, {c[1]:+.1f}) '
            f'px; camera blur: shutter {shutter} frame(s) along the path from n{prev} (original\'s edge energy vs. '
            f'moved n{ref}: {target:.2f}' +
            (f'; reached ' + ', '.join(f'{k}: {v:.2f}' for k, v in ratios.items()) if len(ratios) > 1 else '') + '); '
            f'TEMPORARY effect: flames of original n{n} (shape, colour, glow; zoomed with the frame), opaque: plate '
            f'lines through them ' + (f'at {strength:.2f}' if LINES_THROUGH else 'off')))
        prev = n
    return out


def write_mp4(path, imgs, fps=24, loops=1):
    h, w = imgs[0].shape[:2]
    h2, w2 = h + h % 2, w + w % 2
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w2}x{h2}',
                          '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow',
                          '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for k in range(loops):
        for im in imgs:
            im = cv2.copyMakeBorder(im, 0, h2 - h, 0, w2 - w, cv2.BORDER_REPLICATE)
            if loops > 1:
                t = f'loop {k + 1}/{loops}'
                cv2.putText(im, t, (w - 120, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
                cv2.putText(im, t, (w - 120, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()


def main():
    sheet = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    f0, f1 = sheet['frames']
    ns = list(range(f0, f1))
    fs = {int(k): v for k, v in sheet['frames_sheet'].items()}
    missing = [n for n in ns if n not in fs]
    if missing:
        sys.exit(f'exposure sheet misses frames {missing}')
    refs = {v['ref'] for v in fs.values() if 'hold' in v}
    lo, hi = min(ns + list(refs)), max(ns + list(refs)) + 1
    raw = FR.frames(lo, hi)
    O = {n: cv2.resize(raw[n], (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 for n in raw}
    holds = {}
    for n in ns:
        if 'hold' in fs[n]:
            holds.setdefault(fs[n]['hold'], []).append(n)
    A = {}
    for name, hn in holds.items():
        for n in set(hn) | {fs[hn[0]]['ref']}:
            if n not in A:
                A[n] = flames(O[n])
    R, BASE, FX, src, tag = {}, {}, {}, {}, {}
    for name, hn in holds.items():
        for n, d in render_holds(name, hn, fs, O, A, raw).items():
            R[n], BASE[n], FX[n], src[n] = d['R'], d['base'], d['fx'], d['src']
            k = hn.index(n) + 1
            tag[n] = f'{name} hold {k}/{len(hn)}' + (' PROVISIONAL' if fs[n].get('provisional') else '')
    for n in ns:
        if 'drawing' in fs[n]:
            R[n] = load(fs[n]['drawing'])
            src[n] = f'{fs[n].get("id", "drawing")} new drawing `{fs[n]["drawing"]}` (sha256 {sha(fs[n]["drawing"])}), shown unchanged'
            tag[n] = f'{fs[n].get("id", "drawing")} drawing'
    for n in ns:
        cv2.imwrite(os.path.join(out, f'R_n{n:04d}.png'), to8(R[n]))
    pair = [np.hstack([small(O[n], f'original n{n}'), small(R[n], f'n{n} {tag[n]}')]) for n in ns]
    write_mp4(os.path.join(out, 'side_by_side.mp4'), pair, 24, loops=3)
    slow = [cv2.putText(p.copy(), 'SLOW 6 fps (each frame x4)', (p.shape[1] // 2 - 140, p.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2) for p in pair]
    write_mp4(os.path.join(out, 'slow_6fps.mp4'), [p for p in slow for _ in range(4)], 24)
    hold_ns = [n for n in ns if n in BASE]
    diag = []
    for n in hold_ns:
        top = np.hstack([small(O[n], f'original n{n}'), small(BASE[n], f'n{n} effect-free base (plate+camera+blur+light)')])
        bot = np.hstack([small(FX[n], f'n{n} effects alone, new lines OFF (temporary, from original)'),
                         small(R[n], f'n{n} result: {tag[n]}')])
        diag.append(np.vstack([top, bot]))
    if diag:
        write_mp4(os.path.join(out, 'holds_diag_6fps.mp4'), [d for d in diag for _ in range(4)], 24)
        cv2.imwrite(os.path.join(out, 'holds_diag_sheet.jpg'),
                    np.vstack([cv2.resize(d, (d.shape[1] // 2, d.shape[0] // 2), interpolation=cv2.INTER_AREA)
                               for d in diag[::2]]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    tiles = [np.vstack([small(O[n], f'orig n{n}', 320), small(R[n], tag[n], 320)]) for n in ns]
    rows = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
    cv2.imwrite(os.path.join(out, 'contact_sheet.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    drawings = sorted({fs[n].get('id', fs[n].get('drawing', fs[n].get('hold'))) for n in ns})
    with open(os.path.join(out, 'sources.md'), 'w') as f:
        f.write(f'# {sheet.get("name", "window")} [{f0}, {f1}): where every frame comes from\n\n')
        f.write(f'{len(ns)} frames at 24 fps; {len(drawings)} distinct drawings ({", ".join(drawings)}); '
                f'{sum(1 for n in ns if "hold" in fs[n])} frames are exposures of a held drawing (each hold counted once, '
                f'with its effect-free version; not counted as new drawings).\n\n')
        for n in ns:
            f.write(f'- n{n}: {src[n]}\n')
    code = {p: sha(os.path.join(os.path.dirname(os.path.abspath(__file__)), p))
            for p in ('action_window.py', 'layered.py', 'frames.py', 'review_window.py')}
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    json.dump(dict(sheet=sheet, code_sha256_16=code, git_head=commit, shutters=SHUTTERS),
              open(os.path.join(out, 'run.json'), 'w'), indent=1)
    print(f'{len(ns)} frames written to {out}')


if __name__ == '__main__':
    main()
