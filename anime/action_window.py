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
           frame ref) is moved by ONE whole-drawing transform per frame: move + rotation + uniform scale, as an
           animation camera moves a cel (measured on the original by feature matching; no local warping, no tilt; one extra zoom for the whole hold, at most MAX_ZOOM, keeps
           the drawing's edges out of frame, and what still shows is filled with its smeared edge colours, logged),
           blurred along that same camera path where the original is blurred (length fitted per frame), lit by
           the light the full drawing has over the plate (a smooth quadratic field; a strong drawn light such as
           D04's purple wash fades as the original's does) times the original's change of brightness, and the
           original's flames of this frame are rebuilt on top as a TEMPORARY source-derived effect: their shape,
           colour and glow, opaque (the old drawing inside them is not taken, and the plate's inferred parts under
           them stay covered)

usage: python3 anime/action_window.py SHEET.json OUT_DIR
Writes OUT_DIR/R_nNNNN.png, redraw_24fps_once.mp4 (the redraw alone at 1672x941, one pass; the encoder needs even
sizes, so one row is repeated to 1672x942), side_by_side.mp4 (24 fps), slow_6fps.mp4, holds_diag_6fps.mp4 (original | effect-free
base | effects alone | result, hold frames only), cover_check_sheet.jpg (yellow: where the full drawing has its own
flames, so the plate there is inferred; red: such inferred plate left showing), contact_sheet.jpg, sources.md, run.json."""
import hashlib
import json
import os
import subprocess
import sys
import time

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
CAMERA = 'similarity'   # hold camera: move + rotation + uniform scale (no tilt, no stretch of the drawing)
THR = {'similarity': 5.0, 'perspective': 3.0}   # RANSAC tolerance, source pixels (a cel move fits a 3D scene loosely)
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


def match_h(a, b, ma, mb, ratio=0.75, thr=2.0, model='perspective'):
    """transform a -> b from SIFT matches (RANSAC thr px), as a 3x3 matrix: a perspective transform, or with
    model='similarity' a move + rotation + uniform scale only; returns (H, inliers, median error px)"""
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
    if model == 'similarity':
        M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=thr, maxIters=5000)
        Hm = None if M is None else np.vstack([M, [0, 0, 1]])
    else:
        Hm, inl = cv2.findHomography(pa, pb, cv2.RANSAC, thr)
    if Hm is None:
        return None, 0, np.inf
    inl = inl.ravel().astype(bool)
    if inl.sum() < 4:
        return None, int(inl.sum()), np.inf
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


def non_uniform(Hm):
    """how far the transform is from a rigid move plus uniform scale, at the frame centre: the ratio of its two
    scale axes and its shear (deg)"""
    c = np.float32([[[W / 2, H / 2], [W / 2 + 10, H / 2], [W / 2, H / 2 + 10]]])
    p = cv2.perspectiveTransform(c, Hm)[0]
    J = np.stack([(p[1] - p[0]) / 10, (p[2] - p[0]) / 10], 1)
    sv = np.linalg.svd(J, compute_uv=False)
    ex, ey = J[:, 0], J[:, 1]
    shear = 90 - np.degrees(np.arccos(np.clip(ex @ ey / (np.linalg.norm(ex) * np.linalg.norm(ey)), -1, 1)))
    return float(sv[0] / sv[1]), float(shear)


def overscan(Hs, size=(W, H)):
    """the smallest zoom about the frame centre (one for the whole hold) at which the moved plate (size: its pixel
    width and height; Hs map its pixels to the frame) covers the whole frame in every frame, so no edge of the
    drawing is ever shown"""
    pw, ph = size
    corners = np.float32([[[0, 0], [W, 0], [0, H], [W, H], [W / 2, 0], [W / 2, H], [0, H / 2], [W, H / 2]]])

    def covers(c):
        C = np.array([[c, 0, (1 - c) * W / 2], [0, c, (1 - c) * H / 2], [0, 0, 1]])
        for Hm in Hs.values():
            q = cv2.perspectiveTransform(corners, np.linalg.inv(C @ Hm))[0]
            if (q[:, 0] < -0.5).any() or (q[:, 0] > pw + 0.5).any() or (q[:, 1] < -0.5).any() or (q[:, 1] > ph + 0.5).any():
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


def plausible(Hm):
    """a camera move between neighbouring frames of one hold: finite, scale 0.5-2, centre kept within the frame"""
    if Hm is None or not np.all(np.isfinite(Hm)):
        return False
    s, _, c = describe(Hm)
    return 0.5 < s < 2.0 and abs(c[0]) < W and abs(c[1]) < H


def agreement(o_ref, o, Hm, m):
    """normalised correlation of edge strength between the moved reference frame and frame n, on mask m"""
    if not plausible(Hm):
        return -1.0
    moved_ = cv2.warpPerspective(o_ref, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = m & (cv2.warpPerspective(np.ones((H, W), np.uint8), Hm, (W, H), flags=cv2.INTER_NEAREST) > 0)
    if m.sum() < 1000:
        return -1.0
    a = _edges(moved_)[m]
    b = _edges(o)[m]
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / max(np.sqrt((a * a).sum() * (b * b).sum()), 1e-6))


def hold_camera(O, A, ref, ns, raw, region=None, model=None, exclude=None, subject=None):
    """H[n]: ref -> n (display pixels) for the frames of a hold, one transform of the whole drawing per frame.
    Features are matched on the full-resolution original (flames and watermark left out); candidates are the
    match straight to ref, the match chained through the neighbouring frame towards ref (subject features, and
    whole frame), and the neighbour's transform; the one under which the neighbour, moved on to n, agrees best
    with frame n (edge correlation) is used.  Frames are taken outwards from ref, so ref may be any frame of the
    hold.  region (x0, y0, x1, y1) or subject (a mask), both in ref display pixels, limit the features to the
    subject, and then the agreement is judged on the subject only; exclude {n: mask} leaves those pixels of
    frame n out (e.g. a character moving over the background being tracked).  model: 'similarity' (default,
    CAMERA) moves, turns and scales the drawing as an animation camera does a cel; 'perspective' also tilts it."""
    model = model or CAMERA
    sx, sy = raw[ref].shape[1] / W, raw[ref].shape[0] / H
    S = np.diag([sx, sy, 1.0])
    Si = np.linalg.inv(S)
    big = (raw[ref].shape[1], raw[ref].shape[0])

    def bigmask(m):
        return cv2.resize(m, big, interpolation=cv2.INTER_NEAREST)

    def full(n):
        return raw[n].astype(np.float32) / 255

    def fmask(n):
        m = feature_mask(O[n], A[n])
        if exclude is not None and n in exclude:
            m[exclude[n]] = 0
        return m
    mref = fmask(ref)
    subj = None
    if region is not None:
        subj = np.zeros((H, W), bool)
        x0, y0, x1, y1 = region
        subj[y0:y1, x0:x1] = True
    if subject is not None:
        subj = subject if subj is None else subj & subject
    if subj is not None:
        mref[~subj] = 0
    Hs, info = {ref: np.eye(3)}, {ref: 'reference frame'}
    after = sorted(n for n in ns if n > ref)
    before = sorted((n for n in ns if n < ref), reverse=True)
    for seq in (after, before):
        prev = ref
        for n in seq:
            mn = fmask(n)
            cands = []
            Hd, id_, ed = match_h(full(ref), full(n), bigmask(mref), bigmask(mn), thr=THR[model], model=model)
            if Hd is not None and id_ >= 12:
                cands.append((Si @ Hd @ S, f'matched to n{ref}: {id_} inliers, median error {ed / sx:.2f} px'))
            mprev = cv2.warpPerspective(mref, Hs[prev], (W, H), flags=cv2.INTER_NEAREST) & fmask(prev)
            Hc, ic, ec = match_h(full(prev), full(n), bigmask(mprev), bigmask(mn), thr=THR[model], model=model)
            if Hc is not None and ic >= 12:
                cands.append((Si @ Hc @ S @ Hs[prev], f'chained via n{prev}: {ic} inliers, median error '
                                                      f'{ec / sx:.2f} px'))
            if subj is None and mprev.mean() < 0.9 * 255 * (mn > 0).mean():
                Hw, iw, ew = match_h(full(prev), full(n), bigmask(fmask(prev)), bigmask(mn), thr=THR[model],
                                     model=model)
                if Hw is not None and iw >= 12:
                    cands.append((Si @ Hw @ S @ Hs[prev], f'chained via n{prev} (whole frame): {iw} inliers, '
                                                          f'median error {ew / sx:.2f} px'))
            cands.append((Hs[prev], f'previous transform (n{prev}) kept'))
            cands = [(Hc_, t) for Hc_, t in cands if plausible(Hc_ @ np.linalg.inv(Hs[prev]))]

            def judge(Hc_):
                step = Hc_ @ np.linalg.inv(Hs[prev])
                m = mn > 0
                if subj is not None:                 # the subject where this candidate puts it in frame n
                    m &= cv2.warpPerspective(subj.astype(np.uint8), Hc_, (W, H), flags=cv2.INTER_NEAREST) > 0
                return agreement(O[prev], O[n], step, m)
            scored = [(judge(Hc_), Hc_, t) for Hc_, t in cands]
            sc, Hs[n], t = max(scored, key=lambda x: x[0])
            info[n] = f'{t}; edge agreement with n{prev} {sc:.3f} (other candidates: ' + \
                ', '.join(f'{x[0]:.3f}' for x in scored if x[2] != t) + ')'
            prev = n
    return Hs, info


def register_plate(plate, o_ref):
    """the plate is drawn in the framing of the reference frame but not pixel-locked to it: one move + rotation +
    uniform scale plate -> reference frame (identity if the match is weak)"""
    Hm, inl, err = match_h(plate, o_ref, None, feature_mask(o_ref), ratio=0.8, model='similarity')
    if Hm is None or inl < 50:
        return np.eye(3), f'identity (weak match: {inl} inliers)'
    s, r, c = describe(Hm)
    return Hm, f'{inl} inliers, median error {err:.2f} px; scale {s:.4f}, rotation {r:+.2f} deg, centre shift ' \
               f'({c[0]:+.1f}, {c[1]:+.1f}) px'


# ---------------------------------------------------------------- camera blur along the measured path

def interp(H0, H1, t):
    a, b = H0 / H0[2, 2], H1 / H1[2, 2]
    return (1 - t) * a + t * b


def moved(img, Hm, flags=cv2.INTER_CUBIC, layer=False):
    """img moved by Hm; where the drawing does not reach (its edge came into frame) its edge colours are smeared
    in, softly (the plate has no margin beyond the source framing)"""
    if layer:                                   # a cel: nothing outside it (transparent), no smearing
        return cv2.warpPerspective(img, Hm, (W, H), flags=flags, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out = cv2.warpPerspective(img, Hm, (W, H), flags=flags, borderMode=cv2.BORDER_REPLICATE)
    valid = cv2.warpPerspective(np.ones(img.shape[:2], np.float32), Hm, (W, H), flags=cv2.INTER_LINEAR)
    if valid.min() > 0.999:
        return out
    soft = cv2.GaussianBlur(out, (0, 0), 25)
    v = cv2.GaussianBlur((valid > 0.999).astype(np.float32), (0, 0), 3)[..., None]
    return out * v + soft * (1 - v)


def path_blur(img, Hprev, Hcur, shutter, samples=None, layer=False):
    """img moved by Hcur, averaged over the camera path back towards Hprev for `shutter` frame intervals"""
    if shutter <= 0:
        return moved(img, Hcur, layer=layer)
    # sample density: about one sample per 1.5 px of the largest displacement along the path
    corners = np.float32([[[0, 0], [W, 0], [0, H], [W, H], [W / 2, H / 2]]])
    d = np.linalg.norm(cv2.perspectiveTransform(corners, Hcur)[0] - cv2.perspectiveTransform(corners, Hprev)[0], axis=1)
    k = samples or int(np.clip(d.max() * shutter / 1.5, 3, 64))
    acc = np.zeros((H, W, img.shape[2]), np.float32)
    for t in np.linspace(1 - shutter, 1, k):
        acc += moved(img, interp(Hprev, Hcur, t), cv2.INTER_LINEAR, layer=layer)
    return acc / k


def _energy(x, m):
    g = L.lum(cv2.resize(x, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    return float(e[m].mean())


def _cell_energy(x, m, gx=4, gy=3):
    """edge energy per cell of a gx x gy grid (cells with too little usable area or almost no edges left out)"""
    g = L.lum(cv2.resize(x, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    h, w = m.shape
    out = {}
    for j in range(gy):
        for i in range(gx):
            sl = (slice(j * h // gy, (j + 1) * h // gy), slice(i * w // gx, (i + 1) * w // gx))
            if m[sl].sum() >= 2000:
                out[(i, j)] = float(e[sl][m[sl]].mean())
    return out


def fit_shutter(o_ref, o, Hprev, Hcur, mask):
    """the shutter (blur length along the camera path) that makes the original's reference frame, moved along the
    path, as soft as the original's frame n.  Matched on edge energy (mean gradient), away from flames and the
    watermark, so that a changed detail does not pass for blur; measured back in the reference framing, so that a
    zoom-in's enlargement does not pass for blur either.  A camera blur softens the whole frame, so it is read per
    cell of a 4 x 3 grid and the upper quartile of the cells decides: a blur that only one part of the original has
    (a foreground limb moving on its own) does not pass for a camera blur (Limo, 042: never blur a sharp character
    to chase a local blur).  0 unless frame n is clearly softer (< 0.85)."""
    back = np.linalg.inv(Hcur)
    m = cv2.warpPerspective(mask, back, (W, H), flags=cv2.INTER_NEAREST)
    m = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST) > 0
    if m.sum() < 1000:
        return 0.0, 1.0, {0.0: 1.0}

    def e(x):
        return _cell_energy(cv2.warpPerspective(x, back, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), m)
    c0 = e(path_blur(o_ref, Hprev, Hcur, 0))
    keep = [k for k, v in c0.items() if v > 1e-3]
    if len(keep) < 3:                                    # too little to read per cell: the whole frame
        def stat(x):
            return _energy(cv2.warpPerspective(x, back, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), m)
        e0 = stat(path_blur(o_ref, Hprev, Hcur, 0))

        def ratio(x):
            return stat(x) / max(e0, 1e-6)
    else:
        def ratio(x):
            cx = e(x)
            return float(np.percentile([cx[k] / c0[k] for k in keep], 75))
    target = ratio(o)
    ratios = {0.0: 1.0}
    if target >= 0.85:
        return 0.0, target, ratios
    for s in SHUTTERS[1:]:
        ratios[s] = ratio(path_blur(o_ref, Hprev, Hcur, s, samples=24))
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


WASH = 0.25      # the full drawing's added light is followed frame by frame only when it is this strong (std of log)


def _lit(o, a):
    """lit, flame-free pixels of an original frame (60 px away from the flames, not the watermark)"""
    m = (cv2.dilate((a > 0.05).astype(np.uint8), np.ones((61, 61), np.uint8)) == 0) & (L.lum(o) > 0.12)
    m[L.WATERMARK] = False
    return m


def brightness_change(o, o_ref, Hn, a, a_ref):
    """the original's change of brightness from the reference frame to this one, on the same content: the median
    ratio of lit, flame-free pixels with the reference frame moved by this frame's camera (a push-in onto bright
    parts, or a hand that moved, is not taken for a change of light)"""
    moved_ = cv2.warpPerspective(o_ref, Hn, (W, H), flags=cv2.INTER_LINEAR)
    valid = cv2.warpPerspective(np.ones((H, W), np.float32), Hn, (W, H), flags=cv2.INTER_NEAREST) > 0.5
    a_m = cv2.warpPerspective(a_ref, Hn, (W, H), flags=cv2.INTER_LINEAR)
    m = valid & _lit(o, a) & (cv2.dilate((a_m > 0.05).astype(np.uint8), np.ones((61, 61), np.uint8)) == 0) & \
        (L.lum(moved_) > 0.12)
    if m.sum() < 2000:
        return 1.0
    return float(np.clip(np.median(L.lum(o)[m] / L.lum(moved_)[m]), 0.5, 2.0))


def frame_light(light0, o, o_ref, a, a_ref, Hn):
    """this frame's light.  Where the full drawing adds a strong coloured light of its own (D04's purple wash),
    that light is raised to w = how much of the wash colour the original still has, relative to the reference
    frame (the lit pixels' mean colour along the wash's own hue: for D04 1.0 at n1254 down to 0.22 at n1261),
    times g = the change of the lit pixels' mean brightness.  Otherwise the drawing's light is kept (w = 1) and g
    is the original's change of brightness on the same content (brightness_change).  Wash and brightness are
    measured separately: the purple glow going out is not taken for the picture getting darker."""
    L0 = np.log(light0)
    if L0[::4, ::4].std() < WASH:
        g = brightness_change(o, o_ref, Hn, a, a_ref)
        return light0 * np.float32(g), 1.0, g
    d = L0.reshape(-1, 3).mean(0)
    d = d - d.mean()
    d = d / max(np.linalg.norm(d), 1e-6)                     # the wash's hue as a direction in colour space

    def wash(x, m):
        return float(((x[m] - L.lum(x)[m][:, None]) @ d).mean())
    mn, mr = _lit(o, a), _lit(o_ref, a_ref)
    pn, pr = wash(o, mn), wash(o_ref, mr)
    w = float(np.clip(pn / max(pr, 1e-4), 0, 1.2)) if pr > 0.02 else 1.0
    # brightness here from the lit pixels of each frame (not the same pixels: under the wash the same pixels are
    # brighter because of the wash itself, which w already takes out)
    g = float(L.lum(o)[mn].mean() / max(L.lum(o_ref)[mr].mean(), 1e-4))
    return np.exp(w * L0).astype(np.float32) * np.float32(g), w, g


# ---------------------------------------------------------------- assembly

def load(p):
    im = cv2.imread(p).astype(np.float32) / 255
    if abs(im.shape[1] / im.shape[0] - W / H) > 0.01 * W / H:
        sys.exit(f'{p}: {im.shape[1]}x{im.shape[0]} is not the source framing; give it a viewport')
    return im if im.shape[:2] == (H, W) else cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)


def load_canvas(p, viewport=None):
    """a plate and the transform from its pixels to the source framing (display pixels).  viewport = [x, y, w, h]:
    where the source framing sits inside a plate drawn with extra margin; without it the whole image is the
    source framing.  The margin is kept (not squeezed into the frame): it is what the camera may reveal."""
    im = cv2.imread(p).astype(np.float32) / 255
    x, y, w, h = viewport if viewport else (0, 0, im.shape[1], im.shape[0])
    V = np.array([[W / w, 0, -x * W / w], [0, H / h, -y * H / h], [0, 0, 1]], np.float64)
    if abs(W / w - H / h) > 0.01 * W / w:
        sys.exit(f'{p}: viewport {viewport} does not have the source aspect ratio')
    if W / w < 1:                                   # work at display resolution (plates are larger than it)
        f = W / w
        im = cv2.resize(im, (int(round(im.shape[1] * f)), int(round(im.shape[0] * f))), interpolation=cv2.INTER_AREA)
        V = V @ np.diag([1 / f, 1 / f, 1.0])
    return im, V


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def to8(x):
    return np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8)


def small(x, label=None, w=836):
    im = cv2.resize(to8(x) if x.dtype != np.uint8 else x, (w, int(round(w * H / W))), interpolation=cv2.INTER_AREA)
    return RW.label(im, label) if label else im


def load_sprite(sp):
    """a drawn layer with its own transparency: an RGBA PNG (straight alpha), or RGB on a flat key colour (keyed by
    anime/matte_key.py); placed in the source framing by sp['to_framing'] (2x3 move + rotation + uniform scale) or
    sp['viewport'] [x, y, w, h], else the image is the source framing.  Returns (rgba at display scale, V: sprite
    pixels -> source framing, report)"""
    import matte_key as MK
    im = cv2.imread(sp['image'], cv2.IMREAD_UNCHANGED)
    if im.ndim == 3 and im.shape[2] == 4:
        rgba = im.astype(np.float32) / 255
        rep = dict(alpha='own (RGBA)', opaque=float((rgba[..., 3] > 0.999).mean()),
                   between=float(((rgba[..., 3] > 0.001) & (rgba[..., 3] < 0.999)).mean()))
    else:
        rgba, a, rep = MK.key(im[..., :3])
        rep['alpha'] = 'keyed'
    for box in sp.get('clear', []):
        a2, _, crep = MK.clear_fragment((rgba[..., :3] * 255).astype(np.uint8), rgba[..., 3], tuple(box))
        rgba[..., 3] = a2
        rep.setdefault('cleared', []).append(crep)
    if sp.get('to_framing'):
        V = np.vstack([np.float64(sp['to_framing']), [0, 0, 1]])
        A2 = V[:2, :2]
        if abs(A2[0, 0] - A2[1, 1]) > 1e-6 or abs(A2[0, 1] + A2[1, 0]) > 1e-6:
            sys.exit(f'{sp["image"]}: to_framing must be a move + rotation + uniform scale')
        return rgba, V, rep
    vx, vy, vw, vh = sp.get('viewport') or (0, 0, im.shape[1], im.shape[0])
    if abs(vw / vh - W / H) > 0.01 * W / H:
        sys.exit(f'{sp["image"]}: viewport {vw}x{vh} is not the source framing')
    f = W / vw
    rgba = cv2.resize(rgba, (int(round(rgba.shape[1] * f)), int(round(rgba.shape[0] * f))), interpolation=cv2.INTER_AREA)
    return rgba, np.array([[1, 0, -vx * f], [0, 1, -vy * f], [0, 0, 1]], np.float64), rep


def _exposure_counts(fs, ns):
    """how many frames are single exposures and how many belong to holds (the same image on consecutive frames)"""
    runs, prev = [], None
    whites = [n for n in ns if fs[n].get('white') or fs[n].get('black')]
    for n in ns:
        if fs[n].get('white') or fs[n].get('black'):
            prev = None
            continue
        key = fs[n].get('id', fs[n].get('drawing', fs[n].get('hold')))
        if runs and key == prev:
            runs[-1][1] += 1
        else:
            runs.append([key, 1])
        prev = key
    seen, loop, singles, held = set(), {}, 0, []
    for k, c in runs:
        if k in seen:                                  # a drawing shown again after others (a cycle, e.g. a barrage)
            loop[k] = loop.get(k, 0) + c
        elif c == 1:
            singles += 1
        else:
            held.append([k, c])
        seen.add(k)
    out = [f'{singles} frames are single exposures']
    if loop:
        out.append(f'{sum(loop.values())} frames re-show a drawing already used earlier in a cycle '
                   f'({", ".join(f"{k} +{c}" for k, c in loop.items())}; not new drawings)')
    if whites:
        out.append(f'{len(whites)} frame(s) are composited white/black frames (no drawing)')
    if held:
        out.append(f'{sum(r[1] for r in held)} frames are {len(held)} hold(s) of one image each '
                   f'({", ".join(f"{k} x{c}" for k, c in held)}; the {sum(r[1] - 1 for r in held)} repeat exposures are '
                   f'not new drawings)')
    return out


def render_holds(name, hn, fs, O, A, raw):
    """the frames hn of one hold.  mode "fx" (default): the effect-free plate moved by the camera, the original's
    flames rebuilt on top (temporary).  mode "full": a short hold of the full drawing itself, its own drawn flames
    moving with it, no source effect added."""
    spec = fs[hn[0]]
    ref = spec['ref']
    mode = spec.get('mode', 'fx')
    full_c, Vf = load_canvas(spec['full'], spec.get('full_viewport'))
    if mode == 'full':
        plate_c, Vp = full_c, Vf
    else:
        plate_c, Vp = load_canvas(spec['plate'], spec.get('viewport'))
    view = cv2.warpPerspective(plate_c, Vp, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if spec.get('register_with'):
        # a same-canvas edit of another drawing (e.g. only its effect changed): it takes that drawing's registration,
        # so the unchanged body stays exactly where it was on the previous exposure
        other_c, Vo = load_canvas(spec['register_with'], spec.get('full_viewport'))
        Hp, preg = register_plate(cv2.warpPerspective(other_c, Vo, (W, H), flags=cv2.INTER_CUBIC,
                                                      borderMode=cv2.BORDER_REFLECT), O[ref])
        preg = f'the registration of `{spec["register_with"]}` (same canvas; this image is an edit of it): {preg}'
    else:
        Hp, preg = register_plate(view, O[ref])
    P = Hp @ Vp                                          # plate pixels -> the reference frame
    if mode == 'full':
        light0 = np.ones((H, W, 3), np.float32)
        drawn_fx = np.zeros((H, W), np.float32)
    else:
        full_v = cv2.warpPerspective(full_c, Hp @ Vf, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        light0, _ = light_of_full(full_v, cv2.warpPerspective(plate_c, P, (W, H), flags=cv2.INTER_CUBIC,
                                                               borderMode=cv2.BORDER_REFLECT))
        # where the full drawing has its own flames: under them the plate's content is inferred, so the rebuilt
        # flame must cover it (Limo, completion_001); checked per frame below
        drawn_fx = (np.maximum(_core(full_v, 'cyan'), _core(full_v, 'red')) > 0.3).astype(np.float32)   # cores only
    drawn, drawn_spec = {}, {}
    for sp in spec.get('fx_drawn', []):                    # drawn effect layers replacing the source flame
        loaded = load_sprite(sp)
        if sp.get('tone'):
            # explicit whole-layer tone change of a drawn effect: contrast about its own mean colour, then a gain;
            # alpha, shape and placement untouched
            rgba_t = loaded[0].copy()
            a_t = rgba_t[..., 3:]
            tn = sp['tone']
            mean = (rgba_t[..., :3] * a_t).reshape(-1, 3).sum(0) / max(float(a_t.sum()), 1e-6)
            rgb = (mean + tn.get('contrast', 1.0) * (rgba_t[..., :3] - mean)) * tn.get('gain', 1.0)
            if tn.get('shadow_lift') or tn.get('highlight'):
                # luminance-only curve (hue and saturation kept): dark outline lifted towards 0.3, highlights above
                # 0.75 compressed by the given factor
                lu = np.maximum(L.lum(rgb), 1e-4)
                lift = tn.get('shadow_lift', 0.0)
                l2 = np.where(lu < 0.3, lu + lift * (1 - lu / 0.3), lu)
                hc = tn.get('highlight', 1.0)
                l2 = np.where(l2 > 0.75, 0.75 + (l2 - 0.75) * hc, l2)
                # near black a ratio cannot lift (no colour to scale): there the lift is added in the layer's mean
                # flame colour, i.e. near-black pixels are TINTED as they are lifted; blended smoothly with the ratio
                # branch over luminance 0.02-0.08 so there is no seam
                tint = rgb + (l2 - lu)[..., None] * (mean / max(L.lum(mean[None])[0], 1e-3)) * 0.5
                ratio = rgb * (l2 / lu)[..., None]
                k = np.clip((lu - 0.02) / 0.06, 0, 1)[..., None]
                rgb = k * ratio + (1 - k) * tint
            rgba_t[..., :3] = np.clip(rgb, 0, 1)
            loaded = (rgba_t, loaded[1], dict(loaded[2], tone=sp['tone']))
        for fn in sp['frames']:
            drawn[fn], drawn_spec[fn] = loaded, sp
    ns = sorted(set(hn) | {ref})
    Hs, cinfo = hold_camera(O, A, ref, ns, raw, spec.get('region'), spec.get('camera'))
    if spec.get('camera_only') == 'none':
        # held still: the drawing is shown in its own framing on every exposure, no camera move at all
        for n in ns:
            Hs[n] = np.eye(3)
            cinfo[n] += '; NOT USED: held still, no camera move (the drawing shown in its own framing)'
    elif spec.get('camera_only') == 'scale':
        # the characters move differently from each other inside this hold (no single whole-frame move fits both):
        # keep only the shared push/pull, a uniform scale about the frame centre, and drop rotation and slide
        for n in ns:
            sc_n = describe(Hs[n])[0]
            Hs[n] = np.array([[sc_n, 0, (1 - sc_n) * W / 2], [0, sc_n, (1 - sc_n) * H / 2], [0, 0, 1]])
            cinfo[n] += f'; REDUCED to its uniform scale {sc_n:.4f} about the frame centre (rotation and slide dropped)'
    size = (plate_c.shape[1], plate_c.shape[0])
    zoom = spec['zoom'] if spec.get('zoom') else overscan({n: Hs[n] @ P for n in hn}, size)
    C = np.array([[zoom, 0, (1 - zoom) * W / 2], [0, zoom, (1 - zoom) * H / 2], [0, 0, 1]])
    ones = np.ones(plate_c.shape[:2], np.float32)
    fill_m = {n: cv2.warpPerspective(ones, C @ Hs[n] @ P, (W, H)) < 0.999 for n in hn}
    edge_px = {n: 100 * float(fill_m[n].mean()) for n in hn}
    out = {}
    prev = None
    chain_c = {}
    for n in ns:
        if n not in hn:
            prev = n
            continue
        Hn = Hs[n]
        Hprev = Hs[prev] if prev is not None else Hn
        fmask = (feature_mask(O[n], A[n]) > 0).astype(np.uint8)
        shutter, target, ratios = fit_shutter(O[ref], O[n], Hprev, Hn, fmask) if prev is not None else (0.0, 1.0, {})
        light0_moved = cv2.warpPerspective(light0, Hn, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if spec.get('light') == 'mean_ratio' and n != ref:
            # a different view in the original (drawings on twos) that is darker or lighter as a whole: the exposure
            # change is the ratio of the original's mean luminance, one scalar for the whole drawing
            bgain = float(L.lum(O[n]).astype(np.float64).mean() / L.lum(O[ref]).astype(np.float64).mean())
            light, w = light0_moved * np.float32(bgain), 1.0
        elif spec.get('light') in ('fixed', 'mean_ratio'):
            # each original frame of this hold is a different view (drawings on twos over a 3D fly-through): there is
            # no same content to measure a change of light on, so the light is held
            light, w, bgain = light0_moved, 1.0, 1.0
        else:
            light, w, bgain = frame_light(light0_moved, O[n], O[ref], A[n], A[ref], Hn)
        canvas = plate_c
        if mode == 'full' and fs[n]['full'] != spec['full']:
            # a chain of same-canvas edits held as one group (e.g. E09a -> E09b): this frame shows its own image of
            # the chain, placed by the group's registration and moved along the group's one camera path
            if fs[n]['full'] not in chain_c:
                chain_c[fs[n]['full']] = load_canvas(fs[n]['full'], spec.get('full_viewport'))[0]
            canvas = chain_c[fs[n]['full']]
            if canvas.shape != plate_c.shape:
                sys.exit(f'{fs[n]["full"]}: a chain image must have the size of `{spec["full"]}`')
        base = path_blur(canvas, Hprev @ P, Hn @ P, shutter) * light
        zone = cv2.warpPerspective(drawn_fx, Hn, (W, H), flags=cv2.INTER_NEAREST) > 0.5
        if mode == 'full':
            res, fx_only, fxs = base, np.zeros_like(base), 'no source effect: the drawing\'s own flames move with it'
            exposed = np.zeros((H, W), bool)
            labels = ('full drawing moved (its own flames)', 'no added effect (nothing here)')
        elif n in drawn:
            # a drawn effect layer for this frame (its own alpha), in the plate's framing, moved with the plate
            rgba_d, Vd, _ = drawn[n]
            Td = Hn @ Hp @ Vd
            Tdp = Hprev @ Hp @ Vd
            fxl = path_blur(np.dstack([rgba_d[..., :3] * rgba_d[..., 3:], rgba_d[..., 3]]), Tdp, Td, shutter,
                            layer=True)
            a = np.clip(fxl[..., 3], 0, 1)
            clamp = drawn_spec[n].get('core_clamp')
            if clamp:                                   # explicit: the drawing's near-opaque core made solid,
                solid = a >= clamp / 255                # after placement (soft edges untouched)
                fxl[..., :3][solid] /= np.maximum(a[solid], 1e-6)[:, None]
                a = a.copy()
                a[solid] = 1.0
                fxl[..., 3] = a
            a3 = a[..., None]
            lit = fxl[..., :3] * np.float32(bgain)
            glow = L.BLOOM[0] * cv2.GaussianBlur(lit, (0, 0), 20) + L.BLOOM[1] * cv2.GaussianBlur(lit, (0, 0), 60)
            halo_s = drawn_spec[n].get('halo')
            if halo_s:
                # a faint same-colour halo hugging the outline (within ~40 px), behind the flame, fading with the
                # hold's drawn light (w): explicit, so the flame sits in its haze without a lasting pink wash
                near = cv2.GaussianBlur(cv2.dilate((a > 0.5).astype(np.uint8), cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (81, 81))).astype(np.float32), (0, 0), 10)
                glow = glow + float(halo_s) * w * cv2.GaussianBlur(lit, (0, 0), 12) * near[..., None]
            res = (base + glow * (1 - a3)) * (1 - a3) + lit
            fx_only = glow * (1 - a3) + lit
            exposed = zone & (a < 0.5)
            labels = ('effect-free base (plate+camera+blur+light)', 'drawn effect layer alone (its own alpha)')
            fxs = (f'DRAWN effect layer `{drawn_spec[n]["image"]}` ({drawn[n][2].get("alpha")})'
                   + (f', placed by {drawn_spec[n]["to_framing"]}' if drawn_spec[n].get('to_framing') else '')
                   + (f', core alpha >= {clamp}/255 made solid after placement ({int(solid.sum())} px)' if clamp else '')
                   + (f', faint halo {halo_s} x drawn-light strength {w:.2f} within ~40 px of its outline' if halo_s else '')
                   + (f', layer tone {drawn_spec[n]["tone"]} (luminance curve; near-black pixels tinted with the layer\'s '
                      f'mean flame colour as they are lifted)' if drawn_spec[n].get('tone') else '')
                   + f', its own general glow {L.BLOOM} (not tied to the purple fade)'
                   + ', moved with the plate; '
                   f'of the full drawing\'s own flame zone (where the plate is inferred), {exposed.sum()} px '
                   f'({100 * exposed.sum() / max(zone.sum(), 1):.1f}%) are not under the drawn flame (alpha < 0.5)')
        else:
            lp = L.lum(base)
            lines = LINES_THROUGH * np.clip((cv2.GaussianBlur(lp, (0, 0), 4) - lp) / 0.12, 0, 1)
            a = A[n]
            fill, glow, colour, strength = fx_layer(O[n], a, lines)
            a3 = a[..., None]
            res = (base + glow * (1 - a3)) * (1 - a3) + fill * a3
            fx_only = glow * (1 - a3) + colour * a3          # the effect alone, plate lines OFF
            exposed = zone & (a < 0.5)
            labels = ('effect-free base (plate+camera+blur+light)', 'effects alone, new lines OFF (temporary, from original)')
            fxs = (f'TEMPORARY effect: flames of original n{n} (shape, colour, glow; zoomed with the frame), opaque: '
                   f'plate lines through them ' + (f'at {strength:.2f}' if LINES_THROUGH else 'off') +
                   f'; of the full drawing\'s own flame zone (where the plate is inferred), {exposed.sum()} px '
                   f'({100 * exposed.sum() / max(zone.sum(), 1):.1f}%) are not under the rebuilt flame')
        cover = (0.45 * res).copy()
        cover[zone] = 0.45 * res[zone] + np.float32([0.25, 0.25, 0.0])         # drawn-flame zone: tinted
        cover[exposed] = np.float32([0.1, 0.1, 1.0])                             # inferred plate showing: red

        def zoomed(x):
            return x if zoom == 1.0 else cv2.warpPerspective(x, C, (W, H), flags=cv2.INTER_CUBIC,
                                                             borderMode=cv2.BORDER_REFLECT)
        s, r, c = describe(C @ Hn)
        nu = non_uniform(Hn)
        what = ((f'full drawing `{fs[n]["full"]}` (a same-canvas edit of `{spec["full"]}`, held in one group with it)'
                 if fs[n]['full'] != spec['full'] else
                 f'full drawing `{spec["full"]}` held (short hold, its own effects)') if mode == 'full' else
                f'plate `{spec["plate"]}`' + (f' (viewport {spec["viewport"]})' if spec.get('viewport') else ''))
        light_s = (f'exposure scalar {bgain:.3f} = the original\'s mean luminance n{n} / n{ref} (light: mean_ratio; a '
                   f'different, darker or lighter view, approximated by the drawing of n{ref})'
                   if spec.get('light') == 'mean_ratio' and n != ref else
                   'light held (light: fixed; the original\'s frames of this hold are different views, no same content '
                   'to measure a change on)' if spec.get('light') in ('fixed', 'mean_ratio') else
                   f'brightness gain {bgain:.3f} (the original\'s change n{ref}->n{n} on the same content)' if mode == 'full' else
                   f'light of the full drawing `{spec["full"]}` over the plate (smooth: exp of a quadratic in x, y per '
                   f'colour channel), kept at {w:.2f} of its strength as the original\'s light changes n{ref}->n{n}, '
                   f'brightness gain {bgain:.3f} (on the same content)')
        out[n] = dict(R=zoomed(res), base=zoomed(base), fx=zoomed(fx_only), cover=zoomed(cover), fill=fill_m[n],
                      base_label=labels[0], fx_label=labels[1],
                      exposed=(int(exposed.sum()), int(zone.sum())), src=(
            f'{name} ' + ('single exposure (1 frame; placed through the hold path for registration and light)' if len(hn) == 1 else
                          f'exposure {hn.index(n) + 1} of {len(hn)} (hold' + ('' if hn.index(n) == 0 else '; a repeat, not a new drawing') + ')') +
            f' (ref n{ref}){" PROVISIONAL: " + spec["provisional"] if spec.get("provisional") else ""}; '
            f'{what}, registered to n{ref}: {preg}; {light_s}; '
            f'camera (one {spec.get("camera", CAMERA)} transform of the whole drawing; measured {cinfo[n]}; whole hold zoomed {zoom:.3f} about the centre to '
            f'keep the drawing\'s edges out of frame (at most {MAX_ZOOM}; beyond that its edge colours are smeared in: '
            f'{edge_px[n]:.1f}% of this frame)): at the centre scale {s:.4f}, rotation {r:+.2f} deg, shift ({c[0]:+.1f}, {c[1]:+.1f}) '
            f'px, scale axes ratio {nu[0]:.4f}, shear {nu[1]:+.2f} deg; camera blur: shutter {shutter} frame(s) along the path from n{prev} (original\'s edge energy vs. '
            f'moved n{ref}, upper quartile of 12 cells: {target:.2f}' +
            (f'; reached ' + ', '.join(f'{k}: {v:.2f}' for k, v in ratios.items()) if len(ratios) > 1 else '') + '); '
            + fxs))
        prev = n
    return out


def cut_edges(mask, T):
    """where a cel's character touches the edge of its drawing (a cut, e.g. the hair cropped by the source frame),
    find how far into this frame that cut edge lands once the cel is moved by T: {side: (pixels of cut edge,
    deepest point inside the frame in px)}; empty when every cut edge stays outside the frame"""
    h, w = mask.shape
    sides = {'top': [(x, 0) for x in np.nonzero(mask[0])[0]], 'bottom': [(x, h - 1) for x in np.nonzero(mask[-1])[0]],
             'left': [(0, y) for y in np.nonzero(mask[:, 0])[0]], 'right': [(w - 1, y) for y in np.nonzero(mask[:, -1])[0]]}
    out = {}
    for side, pts in sides.items():
        if not pts:
            continue
        q = cv2.perspectiveTransform(np.float32(pts)[None], T)[0]
        inside = (q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)
        if inside.any():
            depth = np.minimum.reduce([q[inside, 0], W - q[inside, 0], q[inside, 1], H - q[inside, 1]])
            out[side] = (int(inside.sum()), round(float(depth.max()), 1))
    return out


def render_layers(name, hn, fs, O, A, raw):
    """a hold drawn as two layers, as a character cel sliding over a background in cel animation: the character
    (drawn on a key colour, keyed by anime/matte_key.py) and the background plate each moved by their own
    transform measured on the original (move + rotation + uniform scale): the character from features on the
    character, the background from features off it.  The full drawing's own flames (its flame cores, cut from
    the full drawing with a soft edge) ride on the character layer; no source effect is added."""
    import matte_key as MK
    spec = fs[hn[0]]
    cs, bs = spec['cel'], spec['background']
    cref, bref = cs['ref'], bs['ref']
    ns = sorted(set(hn) | {cref, bref})
    # character layer: keyed cel, registered to its reference frame on the character only
    cimg = cv2.imread(cs['image'])
    crgba, ka, krep = MK.key(cimg)                        # keyed on the whole canvas (margin included)
    cleared = []
    for box in cs.get('clear', []):                       # named non-anatomical fragments made transparent
        ka, _, crep = MK.clear_fragment(cimg, ka, tuple(box))
        cleared.append(crep)
    crgba[..., 3] = ka
    if cs.get('to_framing'):
        # the cel's own canvas, mapped into the source framing by a given move + rotation + uniform scale (e.g. a
        # redrawn cel the drawing tool returned at another size); the character may reach outside the framing
        V = np.vstack([np.float64(cs['to_framing']), [0, 0, 1]])
        A2 = V[:2, :2]
        if abs(np.linalg.det(A2)) <= 0 or abs(A2[0, 0] - A2[1, 1]) > 1e-6 or abs(A2[0, 1] + A2[1, 0]) > 1e-6:
            sys.exit(f'{cs["image"]}: to_framing must be a move + rotation + uniform scale')
    else:
        vx, vy, vw, vh = cs.get('viewport') or (0, 0, cimg.shape[1], cimg.shape[0])
        if abs(vw / vh - W / H) > 0.01 * W / H:
            sys.exit(f'{cs["image"]}: viewport {vw}x{vh} is not the source framing')
        f = W / vw                                         # canvas at display resolution
        crgba = cv2.resize(crgba, (int(round(crgba.shape[1] * f)), int(round(crgba.shape[0] * f))),
                           interpolation=cv2.INTER_AREA)
        V = np.array([[1, 0, -vx * f], [0, 1, -vy * f], [0, 0, 1]], np.float64)   # canvas -> source framing
    calpha = crgba[..., 3]
    cmask = (calpha > 0.5).astype(np.uint8) * 255
    grey = crgba[..., :3] * calpha[..., None] + 0.5 * (1 - calpha[..., None])
    gview = cv2.warpPerspective(grey, V, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mview = cv2.warpPerspective(cmask, V, (W, H), flags=cv2.INTER_NEAREST)
    Hm, inl, err = match_h(gview, O[cref], mview, feature_mask(O[cref]), ratio=0.8, model='similarity')
    ok = Hm is not None and inl >= 30 and plausible(Hm)
    Rc = Hm if ok else np.eye(3)                           # source framing -> reference frame
    Pc = Rc @ V                                            # cel canvas -> reference frame
    creg = f'{inl} inliers, median error {err:.2f} px' if ok else f'identity (weak match: {inl} inliers)'
    subject = cv2.warpPerspective(cv2.dilate(cmask, np.ones((41, 41), np.uint8)), Pc, (W, H)) > 0
    Hc, cinfo = hold_camera(O, A, cref, ns, raw, subject=subject, model='similarity')
    # the full drawing's own flames, riding on the character
    full = load(spec['full'])
    fx_a = cv2.GaussianBlur((np.maximum(_core(full, 'cyan'), _core(full, 'red')) > 0.3).astype(np.float32), (0, 0), 1.5)
    # background layer: features off the character (its matte moved to each frame, 40 px wider)
    excl = {n: cv2.warpPerspective(cv2.dilate(cmask, np.ones((81, 81), np.uint8)), Hc[n] @ Pc, (W, H)) > 0 for n in ns}
    bimg, Vb = load_canvas(bs['plate'], bs.get('viewport'))
    bview = cv2.warpPerspective(bimg, Vb, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    bm = feature_mask(O[bref])
    bm[excl[bref]] = 0
    Hb_, binl, berr = match_h(bview, O[bref], None, bm, ratio=0.8, model='similarity')
    Pb = (Hb_ if (Hb_ is not None and binl >= 30 and plausible(Hb_)) else np.eye(3)) @ Vb
    Hb, binfo = hold_camera(O, A, bref, ns, raw, exclude=excl, model='similarity')
    for tn, (na, nb) in ((int(k), v) for k, v in bs.get('interp', {}).items()):
        # this frame's background camera from two measured anchors on the original, interpolated as a similarity
        # (scale geometric, rotation and translation linear); an anchor outside the hold is measured against the
        # nearest held frame on the original's background (its character area left out by anchor_exclude)
        anchors = {}
        for na_ in (na, nb):
            if na_ in Hb and na_ != tn:
                anchors[na_] = (Hb[na_], binfo[na_])
                continue
            near = min((m for m in Hb if m != tn and m in hn), key=lambda m: abs(m - na_))
            mk = feature_mask(O[na_], A[na_] if na_ in A else flames(O[na_]))
            for box in bs.get('anchor_exclude', {}).get(str(na_), []):
                x0, y0, x1, y1 = box
                mk[y0:y1, x0:x1] = 0
            mnear = feature_mask(O[near], A[near])
            mnear[excl[near]] = 0
            sx_, sy_ = raw[near].shape[1] / W, raw[near].shape[0] / H
            Sm = np.diag([sx_, sy_, 1.0])
            Hn_, inl_, err_ = match_h(raw[near].astype(np.float32) / 255, raw[na_].astype(np.float32) / 255,
                                      cv2.resize(mnear, (raw[near].shape[1], raw[near].shape[0]), interpolation=cv2.INTER_NEAREST),
                                      cv2.resize(mk, (raw[na_].shape[1], raw[na_].shape[0]), interpolation=cv2.INTER_NEAREST),
                                      thr=THR['similarity'], model='similarity')
            if Hn_ is None or inl_ < 12:
                sys.exit(f'background anchor n{na_}: no reliable match to n{near} ({inl_} inliers)')
            anchors[na_] = (np.linalg.inv(Sm) @ Hn_ @ Sm @ Hb[near],
                            f'measured n{near}->n{na_} on the background: {inl_} inliers, median error {err_ / sx_:.2f} px')

        def params(M):
            M = M / M[2, 2]
            return np.hypot(M[0, 0], M[1, 0]), np.arctan2(M[1, 0], M[0, 0]), M[0, 2], M[1, 2]
        (sa, ra, xa, ya), (sb_, rb_, xb, yb) = params(anchors[na][0]), params(anchors[nb][0])
        t = (tn - na) / (nb - na)
        sc = sa ** (1 - t) * sb_ ** t
        rr = ra + t * (np.arctan2(np.sin(rb_ - ra), np.cos(rb_ - ra)))
        Hb[tn] = np.array([[sc * np.cos(rr), -sc * np.sin(rr), xa + t * (xb - xa)],
                           [sc * np.sin(rr), sc * np.cos(rr), ya + t * (yb - ya)], [0, 0, 1]])
        binfo[tn] = (f'INTERPOLATED at {t:.2f} between n{na} ({anchors[na][1]}) and n{nb} ({anchors[nb][1]}) as a '
                     f'similarity (was: {binfo[tn]})')
    size = (bimg.shape[1], bimg.shape[0])
    zoom = bs['zoom'] if bs.get('zoom') else overscan({n: Hb[n] @ Pb for n in hn}, size)
    C = np.array([[zoom, 0, (1 - zoom) * W / 2], [0, zoom, (1 - zoom) * H / 2], [0, 0, 1]])
    ones = np.ones(bimg.shape[:2], np.float32)
    out = {}
    order = sorted(hn)
    for i, n in enumerate(order):
        prev = order[i - 1] if i else None
        Tb, Tc = Hb[n] @ Pb, Hc[n] @ Pc
        g = brightness_change(O[n], O[bref], Hb[n], A[n], A[bref])
        shutter = 0.0
        if prev is not None:
            shutter, _, _ = fit_shutter(O[bref], O[n], Hb[prev], Hb[n], (feature_mask(O[n], A[n]) > 0).astype(np.uint8))
        bg = path_blur(bimg, (Hb[prev] if prev else Hb[n]) @ Pb, Tb, shutter)
        Tc_prev = (Hc[prev] if prev else Hc[n]) @ Pc
        cel = path_blur(np.dstack([crgba[..., :3] * calpha[..., None], calpha]), Tc_prev, Tc, shutter, layer=True)
        fxl = path_blur(np.dstack([full * fx_a[..., None], fx_a]), Tc_prev @ np.linalg.inv(V), Tc @ np.linalg.inv(V),
                        shutter, layer=True)                # the full drawing is in the source framing, not the canvas
        res = bg * (1 - cel[..., 3:]) + cel[..., :3]                      # premultiplied after the move
        res = res * (1 - fxl[..., 3:]) + fxl[..., :3]
        lit = fxl[..., :3]
        res = res + (L.BLOOM[0] * cv2.GaussianBlur(lit, (0, 0), 20) + L.BLOOM[1] * cv2.GaussianBlur(lit, (0, 0), 60)) \
            * (1 - fxl[..., 3:])
        res = res * np.float32(g)
        edge = 100 * float((cv2.warpPerspective(ones, C @ Tb, (W, H)) < 0.999).mean())

        def zoomed(x):
            return x if zoom == 1.0 else cv2.warpPerspective(x, C, (W, H), flags=cv2.INTER_CUBIC,
                                                             borderMode=cv2.BORDER_REFLECT)
        sb, rb, cb = describe(C @ Hb[n])
        sc_, rc, cc = describe(C @ Hc[n])
        cut = cut_edges(cmask > 0, C @ Tc)
        char = (cel[..., :3] * (1 - fxl[..., 3:]) + fxl[..., :3]) * np.float32(g)
        out[n] = dict(R=zoomed(res), base=zoomed(bg * np.float32(g)), fx=zoomed(char), exposed=(0, 0),
                      base_label='background layer alone', fx_label='character layer alone (cel + its own flame)', src=(
            f'{name} repeat exposure, two layers (cel animation){" PROVISIONAL: " + spec["provisional"] if spec.get("provisional") else ""}; '
            f'character cel `{cs["image"]}` keyed (key BGR {krep["key_bgr"]}, edge pixels {100 * krep["between"]:.2f}%)'
            + (f', made transparent: {cleared}' if cleared else '') +
            (f', canvas mapped into the source framing by {np.round(V[:2], 6).tolist()}' if cs.get('to_framing') else '') + ', '
            f'registered to n{cref}: {creg}; moved: {cinfo[n]}; at the centre scale {sc_:.4f}, rotation {rc:+.2f} deg, '
            f'shift ({cc[0]:+.1f}, {cc[1]:+.1f}) px; its own flame cores from `{spec["full"]}` ride on it; '
            f'background `{bs["plate"]}` (drawn in the n{bref} framing; registered off the character: {binl} inliers), '
            f'moved: {binfo[n]}; at the centre scale {sb:.4f}, rotation {rb:+.2f} deg, shift ({cb[0]:+.1f}, {cb[1]:+.1f}) px; '
            f'whole hold zoomed {zoom:.3f} (edge colours smeared in: {edge:.1f}% of this frame); camera blur shutter '
            f'{shutter} frame(s), each layer along its own path; brightness gain {g:.3f} (the original\'s change on the '
            f'same background content); no source effect; the cel\'s own cut edges (where the character touches the edge '
            f'of its drawing) inside this frame: {cut or "none"}'))
        out[n]['cut'] = cut
    return out


def fit_grade(r, o, ar=None, ao=None, sigma=4.0):
    """one tone curve per colour channel taking a drawing's look to the original's: each channel's distribution in
    the drawing matched to the same channel's distribution in the original, in the same frame and area (not a
    pixel-pair fit; framing, flame share and small misfits can still shift the distributions); both
    smoothed (sigma px) so lines and small misfits do not count; the watermark and a 20 px border left out (and,
    if their masks are given, the flames of either with a 15 px band; by default the flames count: they are part
    of the picture's look, and leaving them out darkened the flame-filled close-ups).  The curve matches the quantiles (2 % ... 98 %) of the two on those
    pixels, monotone; outside them it continues from its end points with the end slopes (0.3-1.5), so it is
    continuous there (a slope limit no longer opens a step at the low end).  Not a frame mean: the share of
    background or a push-in does not move it.  Returns (curves [(x_q, y_q, lo_slope, hi_slope)] per channel, n px)"""
    m = np.ones(r.shape[:2], bool) if ar is None else \
        (cv2.dilate(((ar > 0.05) | (ao > 0.05)).astype(np.uint8), np.ones((31, 31), np.uint8)) == 0)
    m[L.WATERMARK] = False
    m[:20], m[-20:], m[:, :20], m[:, -20:] = False, False, False, False
    rl, ol = cv2.GaussianBlur(r, (0, 0), sigma), cv2.GaussianBlur(o, (0, 0), sigma)
    qs = np.array([2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98], np.float32)
    curves = []
    for c in range(3):
        x = np.percentile(rl[..., c][m], qs)
        y = np.percentile(ol[..., c][m], qs)
        x = np.maximum.accumulate(x + np.arange(len(x)) * 1e-5)
        y = np.maximum.accumulate(y)
        lo_s = float(np.clip(y[0] / max(x[0], 1e-3), 0.3, 1.5))
        hi_s = float(np.clip((y[-1] - y[-3]) / max(x[-1] - x[-3], 1e-3), 0.3, 1.5))
        curves.append((x, y, lo_s, hi_s))
    return curves, int(m.sum())


LUMA_WB_LIMIT = 0.10


def fit_grade_luma(r, o, sigma=4.0):
    """a luminance-only grade: the drawing's luminance distribution matched to the original's (same frame and
    area), applied as a ratio so each pixel keeps its colour ratios, then one global white balance (channel means
    of the luma-matched drawing against the original's, normalised to keep luminance) limited to +-10 %"""
    m = np.ones(r.shape[:2], bool)
    m[L.WATERMARK] = False
    m[:20], m[-20:], m[:, :20], m[:, -20:] = False, False, False, False
    lr = L.lum(cv2.GaussianBlur(r, (0, 0), sigma))[m]
    lo = L.lum(cv2.GaussianBlur(o, (0, 0), sigma))[m]
    qs = np.array([2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98], np.float32)
    x = np.maximum.accumulate(np.percentile(lr, qs) + np.arange(len(qs)) * 1e-5)
    y = np.maximum.accumulate(np.percentile(lo, qs))
    lo_s = float(np.clip(y[0] / max(x[0], 1e-3), 0.3, 1.5))
    hi_s = float(np.clip((y[-1] - y[-3]) / max(x[-1] - x[-3], 1e-3), 0.3, 1.5))
    cv = dict(x=x, y=y, lo=lo_s, hi=hi_s, wb=np.ones(3, np.float32))
    lm = apply_grade_luma(r, cv)
    g = np.float32([o[..., c][m].mean() / max(lm[..., c][m].mean(), 1e-4) for c in range(3)])
    g = g / float(g @ np.float32([0.114, 0.587, 0.299]))
    cv['wb'] = np.clip(g, 1 - LUMA_WB_LIMIT, 1 + LUMA_WB_LIMIT)
    return cv, int(m.sum())


def _luma_curve(lu, cv):
    l2 = np.interp(lu, cv['x'], cv['y'])
    l2 = np.where(lu < cv['x'][0], np.maximum(cv['y'][0] + (lu - cv['x'][0]) * cv['lo'], 0), l2)   # joins at (x0, y0)
    return np.where(lu > cv['x'][-1], cv['y'][-1] + (lu - cv['x'][-1]) * cv['hi'], l2)


def apply_grade_luma(img, cv, strength=1.0):
    lu = np.maximum(L.lum(img), 1e-4)
    l2 = _luma_curve(lu, cv)
    ref = cv.get('ref')
    if ref is not None and cv.get('hold_hi'):
        # a darker exposure of the same drawing: the curve darkens the mid-tones and shadows, but above the drawing's
        # input luminance x0 it eases (smoothstep up to x1) back to the reference exposure's curve, so the glow
        # (white core and its soft pink-purple falloff) keeps the reference exposure's tones (Limo, 038 review_003)
        x0, x1 = cv['hold_hi']
        sh = np.clip((lu - x0) / (x1 - x0), 0, 1)
        sh = sh * sh * (3 - 2 * sh)
        l2 = (1 - sh) * l2 + sh * _luma_curve(lu, ref)
    out = img * (l2 / lu)[..., None]
    wb = cv['wb']
    if cv.get('protect'):
        # highlight protection: the white balance fades out towards pure white (smallest channel from a to b), so
        # a white core stays white instead of taking the balance's tint.  For a later exposure of the same drawing
        # the mask is the reference exposure's (fixed within the hold), so a glow protected there does not drop out
        # of the protection when this exposure darkens it
        a, b = cv['protect']
        base = img * (_luma_curve(lu, ref) / lu)[..., None] if ref is not None else out
        k = np.clip((np.clip(base, 0, 1).min(2) - a) / (b - a), 0, 1)[..., None]
        k = k * k * (3 - 2 * k)
        wb = 1 + (wb - 1) * (1 - k)
    out = out * wb
    return np.clip(img + strength * (out - img), 0, 1)


def describe_luma(cv):
    return (f'0.1/0.3/0.5/0.7/0.9 -> {np.round(np.interp([0.1, 0.3, 0.5, 0.7, 0.9], cv["x"], cv["y"]), 3).tolist()}, '
            f'white balance B,G,R {np.round(cv["wb"], 3).tolist()}'
            + (f', faded out towards pure white (smallest channel {cv["protect"][0]}-{cv["protect"][1]})'
               if cv.get('protect') else ''))


def apply_grade(img, curves, strength=1.0):
    out = img.copy()
    for c, (x, y, lo_s, hi_s) in enumerate(curves):
        v = img[..., c]
        g = np.interp(v, x, y)
        g = np.where(v < x[0], np.maximum(y[0] + (v - x[0]) * lo_s, 0), g)        # joins the curve at (x0, y0)
        g = np.where(v > x[-1], y[-1] + (v - x[-1]) * hi_s, g)
        out[..., c] = v + strength * (g - v)
    return np.clip(out, 0, 1)


SWS_FLAGS = None      # set per sheet ("encode": {"sws_flags": ...}); None keeps the frozen windows' encoding


def write_mp4(path, imgs, fps=24, loops=1):
    h, w = imgs[0].shape[:2]
    h2, w2 = h + h % 2, w + w % 2
    # accurate_rnd+full_chroma_int: the RGB -> YUV 4:2:0 conversion rounds exactly, so a pure white frame decodes as
    # pure white (the default conversion turned it into Y234 / RGB 251,253,250; Limo, 038 review_002)
    sws = ['-sws_flags', SWS_FLAGS] if SWS_FLAGS else []
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w2}x{h2}',
                          '-r', str(fps), '-i', '-'] + sws + ['-c:v', 'libx264', '-crf', '16', '-preset', 'slow',
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
    global SWS_FLAGS
    sheet = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    SWS_FLAGS = sheet.get('encode', {}).get('sws_flags')
    os.makedirs(out, exist_ok=True)
    f0, f1 = sheet['frames']
    ns = list(range(f0, f1))
    fs = {int(k): v for k, v in sheet['frames_sheet'].items()}
    missing = [n for n in ns if n not in fs]
    if missing:
        sys.exit(f'exposure sheet misses frames {missing}')
    refs = {v['ref'] for v in fs.values() if 'hold' in v} | \
        {v[k]['ref'] for v in fs.values() if v.get('mode') == 'layers' for k in ('cel', 'background')}
    lo, hi = min(ns + list(refs)), max(ns + list(refs)) + 1
    raw = FR.frames(lo, hi)
    O = {n: cv2.resize(raw[n], (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 for n in raw}
    holds = {}
    for n in ns:
        if 'hold' in fs[n]:
            holds.setdefault(fs[n]['hold'], []).append(n)
    A = {}
    for name, hn in holds.items():
        sp = fs[hn[0]]
        extra = {sp[k]['ref'] for k in ('cel', 'background')} if sp.get('mode') == 'layers' else set()
        for n in set(hn) | {sp['ref']} | extra:
            if n not in A:
                A[n] = flames(O[n])
    R, BASE, FX, src, tag, COVER, EXPOSED, LABELS, FILL = {}, {}, {}, {}, {}, {}, {}, {}, {}
    for name, hn in holds.items():
        t0 = time.time()
        rendered = (render_layers if fs[hn[0]].get('mode') == 'layers' else render_holds)(name, hn, fs, O, A, raw)
        print(f'hold {name}: {len(hn)} frames in {time.time() - t0:.0f} s', flush=True)
        for n, d in rendered.items():
            R[n], BASE[n], FX[n], src[n] = d['R'], d['base'], d['fx'], d['src']
            COVER[n], EXPOSED[n] = d.get('cover', d['R']), d['exposed']
            if d.get('fill') is not None:
                FILL[n] = d['fill']
            LABELS[n] = (d.get('base_label', 'effect-free base (plate+camera+blur+light)'),
                         d.get('fx_label', 'effects alone, new lines OFF (temporary, from original)'))
            k = hn.index(n) + 1
            tag[n] = f'{name} hold {k}/{len(hn)}' + (' PROVISIONAL' if fs[n].get('provisional') else '')
    for n in ns:
        if 'drawing' in fs[n]:
            R[n] = load(fs[n]['drawing'])
            src[n] = (f'{fs[n].get("id", "drawing")} FROZEN output frame `{fs[n]["drawing"]}` (sha256 {sha(fs[n]["drawing"])}), '
                      f'shown as it is (not regraded)' if fs[n].get('frozen') else
                      f'{fs[n].get("id", "drawing")} new drawing `{fs[n]["drawing"]}` (sha256 {sha(fs[n]["drawing"])}), its lines '
                      f'and shapes unchanged; AI-generated/edited image (Limo), whole-frame camera only')
            tag[n] = f'{fs[n].get("id", "drawing")} drawing'
        elif fs[n].get('white'):
            # a white flash: composited, no drawing
            R[n] = np.ones((H, W, 3), np.float32)
            src[n] = (f'WHITE FLASH (composited, no drawing): pure white; the original has '
                      f'{100 * float((O[n].min(2) >= 250 / 255).mean()):.1f}% of its pixels >= 250/255 in all channels')
            tag[n] = 'white flash'
        elif fs[n].get('black'):
            # a black frame: composited, no drawing
            R[n] = np.zeros((H, W, 3), np.float32)
            src[n] = (f'BLACK FRAME (composited, no drawing): pure black; the original has '
                      f'{100 * float((O[n].max(2) <= 5 / 255).mean()):.1f}% of its pixels <= 5/255 in all channels')
            tag[n] = 'black frame'
    grade = sheet.get('grade')
    if grade:
        # one tone curve per drawing (all its exposures), fitted at its reference frame on the same content
        ids = {}
        for n in ns:
            if fs[n].get('frozen') or fs[n].get('white') or fs[n].get('black'):  # frozen / flat frames: not graded
                continue
            ids.setdefault(fs[n].get('id', fs[n].get('drawing', fs[n].get('hold'))), []).append(n)
        st = grade.get('strength', 1.0)
        probe = np.repeat(np.float32([0.1, 0.3, 0.5, 0.7, 0.9])[:, None, None], 3, 2).reshape(5, 1, 3)

        def describe_curve(cv):
            pr = apply_grade(probe, cv, st).reshape(5, 3)
            return (f'inputs 0.1/0.3/0.5/0.7/0.9 -> B {np.round(pr[:, 0], 3).tolist()}, G {np.round(pr[:, 1], 3).tolist()}, '
                    f'R {np.round(pr[:, 2], 3).tolist()}')
        fitted = {}
        for did, dns in ids.items():
            # one curve per drawing, fitted on the same content at its first exposure; a hold also gets one at its
            # last exposure and moves linearly between them (the light changes inside a hold, e.g. D04's fade)
            first, last = dns[0], dns[-1]
            mode = grade.get('modes', {}).get(did, 'channels')
            fit = fit_grade if mode == 'channels' else fit_grade_luma
            app = apply_grade if mode == 'channels' else apply_grade_luma
            # grade_at: the frames the grade is fitted at, when the hold's first or last exposure cannot show the
            # drawing's own light (e.g. under a white wash); between them it blends, outside them it is held
            fa, fb = grade.get('grade_at', {}).get(did, [first, last])
            c0, n0 = fit(R[fa], O[fa], sigma=grade.get('sigma', 4.0))
            if mode == 'luma' and grade.get('white_protect'):
                c0 = dict(c0, protect=tuple(grade['white_protect']))
            # first_only: one grade for the whole hold, fitted at its first exposure.  For a hold whose last original
            # frame differs from the drawing in content (n1291's larger source flame), not only in light, a second fit
            # there would carry that content difference into the colour (Limo, 043: keep the colour continuous; the
            # light change is the scalar brightness gain alone)
            if did in grade.get('first_only', []):
                fb = fa
            c1, n1 = fit(R[fb], O[fb], sigma=grade.get('sigma', 4.0)) if fb != fa else (c0, n0)
            if mode == 'luma' and grade.get('white_protect'):
                c1 = dict(c1, protect=tuple(grade['white_protect']))
            if did in grade.get('glow_hold', {}):
                # the later exposure keeps the reference exposure's protection mask and, above x0, its curve
                c1 = dict(c1, ref=c0, hold_hi=tuple(grade['glow_hold'][did]))
            if did in grade.get('wb_same', []):
                # each exposure gets its own luminance curve (fitted at the original's frame, e.g. a darkening
                # fly-through on twos), but one white balance, the one at the drawing's own source frame: the same
                # drawing does not change colour between its exposures
                c1 = dict(c1, wb=c0['wb'])
            wb_from = grade.get('wb_from', {}).get(did)
            if wb_from:
                # a same-canvas effect edit of the previous drawing: its own luminance curve (the edit can come back
                # a little lighter or darker), but the white balance of that drawing at its last exposure, so the
                # unchanged body keeps its colour across the change (Limo, 043: no colour flicker)
                if mode != 'luma' or fitted.get(wb_from, (None, None, None))[2] != 'luma':
                    sys.exit(f'wb_from: {did} and {wb_from} must both be graded in luma mode')
                wb = fitted[wb_from][1]['wb']
                c0, c1 = dict(c0, wb=wb), dict(c1, wb=wb)
            fitted[did] = (c0, c1, mode)
            for n in dns:
                t = 0.0 if fb == fa else float(np.clip((n - fa) / (fb - fa), 0, 1))

                def g(x):
                    return (1 - t) * app(x, c0, st) + t * app(x, c1, st) if t else app(x, c0, st)
                R[n] = g(R[n])
                if n in BASE:
                    BASE[n], FX[n] = g(BASE[n]), g(FX[n])
                how = ('one tone curve per colour channel (each channel\'s distribution matched to the original\'s, '
                       'same frame and area; not a pixel-pair fit)' if mode == 'channels' else
                       'one luminance curve (distribution match, colour ratios kept) and a global white balance '
                       f'limited to +-{int(100 * LUMA_WB_LIMIT)} %')
                desc = describe_curve if mode == 'channels' else (lambda cv: f'luma {describe_luma(cv)}')
                src[n] += (f'; GRADE {did}: {how}, strength {st}, at n{fa} ({n0} px): {desc(c0)}'
                           + (f'; and at n{fb} ({n1} px): {desc(c1)}; this frame blends the two graded results at '
                              f'{t:.2f}' if fb != fa else
                              (f'; the same grade on every exposure of the hold (first_only; the light change inside '
                               f'the hold is the scalar brightness gain above)' if last != first else ''))
                           + (f'; white balance taken from {wb_from} at its last exposure (same canvas, unchanged body)'
                              if wb_from else '')
                           + (f'; one white balance for all exposures, the one at n{fa} (wb_same)'
                              if did in grade.get('wb_same', []) else '')
                           + (f'; glow hold: at n{fb} the white-balance protection mask is the one of n{fa}, and above '
                              f'input luminance {grade["glow_hold"][did][0]} the curve eases (smoothstep to '
                              f'{grade["glow_hold"][did][1]}) back to the n{fa} curve, so only mid-tones and shadows darken'
                              if did in grade.get('glow_hold', {}) and n == fb and fb != fa else ''))
    for n in ns:
        ww = fs[n].get('white_wash')
        if ww:
            # the white flash fading out over the drawing: where the original is (near) white, a smooth white field,
            # i.e. only the rough shape of the original's white area (blurred by sigma px), not its detail
            lo, hi = ww.get('lo', 0.80), ww.get('hi', 0.95)
            w = np.clip((L.lum(O[n]) - lo) / (hi - lo), 0, 1).astype(np.float32)
            # the source watermark (light grey text) would lower the whiteness under it and leave a faint dark band
            # in the blurred field: inside its box the field is filled from the surroundings (normalised convolution)
            wm_before = float(w[L.WATERMARK].mean())
            outside = np.ones_like(w)
            outside[L.WATERMARK] = 0
            fill = cv2.GaussianBlur(w * outside, (0, 0), 15) / np.maximum(cv2.GaussianBlur(outside, (0, 0), 15), 1e-4)
            w[L.WATERMARK] = fill[L.WATERMARK]
            a0 = np.clip(cv2.GaussianBlur(w, (0, 0), ww.get('sigma', 40)), 0, 1)[..., None]
            thr = 249.5 / 255                          # what rounds to >= 250 in the 8-bit output
            before = float((R[n].min(2) >= thr).mean())
            target = float((O[n].min(2) >= thr).mean())
            lum_o = float(L.lum(O[n]).mean())
            sub = (slice(None, None, 2), slice(None, None, 2))
            r_s, a_s = R[n][sub], a0[sub]

            if ww.get('color') == 'source':
                # a coloured light field (a white-to-pink/purple flood): the wash colour is the original's own colour,
                # blurred like the field (watermark box filled from its surroundings first), so only the rough
                # colour of the light is taken, never the original's detail or figure
                o_f = O[n].copy()
                fill3 = cv2.GaussianBlur(o_f * outside[..., None], (0, 0), 15) / \
                    np.maximum(cv2.GaussianBlur(outside, (0, 0), 15), 1e-4)[..., None]
                o_f[L.WATERMARK] = fill3[L.WATERMARK]
                wcol = np.clip(cv2.GaussianBlur(o_f, (0, 0), ww.get('sigma', 40)), 0, 1)
            else:
                wcol = np.ones((1, 1, 3), np.float32)
            wcol_s = wcol[sub] if wcol.shape[0] > 1 else wcol

            screen = ww.get('blend') == 'screen'

            def washed(k, c, x=r_s, a=a_s):
                al = np.clip(k * a + c, 0, 1)
                if screen:
                    # light added over the drawing (screen): the drawing's dark lines and shapes stay readable under
                    # the flood, as in the original where the figure still shows through the light
                    return 1 - (1 - x) * (1 - al * wcol_s)
                return x * (1 - al) + al * wcol_s

            def share(k, c):
                return float((washed(k, c).min(2) >= thr).mean())

            def fit_k(c):
                # the scalar on the field so the white share matches the original's (bisection; 0 if already as white)
                if share(0.0, c) >= target:
                    return 0.0
                klo, khi = 0.0, 3.0
                for _ in range(18):
                    km = (klo + khi) / 2
                    klo, khi = (km, khi) if share(km, c) < target else (klo, km)
                return (klo + khi) / 2
            # two numbers fitted to the original: the field's scale (white share) and a uniform white veil over the
            # whole frame (mean luminance; the flash washes out the frame as a whole as it fades)
            best = None
            for c in np.arange(0.0, ww.get('veil_max', 0.9) + 0.02, 0.02):
                k = fit_k(c)
                err = abs(float(L.lum(washed(k, c)).mean()) - lum_o)
                if best is None or err < best[0]:
                    best = (err, k, float(c))
            _, kk, cc = best
            alpha = np.clip(kk * a0 + cc, 0, 1)
            R[n] = 1 - (1 - R[n]) * (1 - alpha * wcol) if screen else R[n] * (1 - alpha) + alpha * wcol
            src[n] += (f'; WHITE WASH (composited): ' + ('the original\'s own colour blurred ' + str(ww.get('sigma', 40)) +
                                                         ' px (watermark filled; rough light colour only)' if
                                                         ww.get('color') == 'source' else 'white') +
                       (' added as light (screen)' if screen else ' over the drawing') + f', strength = {kk:.3f} x the original\'s '
                       f'whiteness (luminance {lo}-{hi} -> 0-1; inside the source watermark box filled from its '
                       f'surroundings, mean {wm_before:.3f} -> {float(w[L.WATERMARK].mean()):.3f}; blurred '
                       f'{ww.get("sigma", 40)} px) + a uniform veil {cc:.2f}; '
                       f'the two numbers fitted (grid of 0.02 on the veil, bisection on the scale, on every 2nd pixel) so '
                       f'that the share of pixels >= 250/255 in all channels and the mean luminance come close to the '
                       f'original\'s; mean strength {float(alpha.mean()):.2f}; white share original '
                       f'{100 * target:.1f}%, drawing before {100 * before:.1f}%, after '
                       f'{100 * float((R[n].min(2) >= thr).mean()):.1f}%; mean luminance original {255 * lum_o:.1f}, after '
                       f'{255 * float(L.lum(R[n]).mean()):.1f}')
            tag[n] += ' + white wash'
    for n in ns:
        cv2.imwrite(os.path.join(out, f'R_n{n:04d}.png'), to8(R[n]))
    # the redraw alone, native size, 24 fps, played once (no labels): for judging the motion itself
    write_mp4(os.path.join(out, 'redraw_24fps_once.mp4'), [to8(R[n]) for n in ns], 24, loops=1)
    new_ns = [n for n in ns if not fs[n].get('frozen')]
    if len(new_ns) != len(ns):                       # also the new frames alone (frozen seam frames left out)
        write_mp4(os.path.join(out, 'redraw_24fps_once_new_frames_only.mp4'), [to8(R[n]) for n in new_ns], 24, loops=1)
    if FILL:
        # where the drawing's edge came into frame and was filled with its smeared edge colours: whole frame
        # (red tint), and the depth of the fill at each side's middle and corners, so no edge goes unchecked
        tiles = []
        for n in sorted(FILL):
            fm = FILL[n]
            v = small(R[n], None, 560).copy()
            fs_ = cv2.resize(fm.astype(np.uint8), (v.shape[1], v.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
            v[fs_] = (0.5 * v[fs_] + np.float32([0, 0, 127])).astype(np.uint8)

            def depth(line):
                idx = np.nonzero(~line)[0]
                return int(idx[0]) if len(idx) else len(line)
            d = dict(top=depth(fm[:, W // 2]), bottom=depth(fm[::-1, W // 2]), left=depth(fm[H // 2, :]),
                     right=depth(fm[H // 2, ::-1]))
            xs_, ys_ = range(int(0.1 * W), int(0.9 * W), 8), range(int(0.1 * H), int(0.9 * H), 8)   # inner 80 %
            mx = dict(top=int(max(depth(fm[:, x]) for x in xs_)), bottom=int(max(depth(fm[::-1, x]) for x in xs_)),
                      left=int(max(depth(fm[y, :]) for y in ys_)), right=int(max(depth(fm[y, ::-1]) for y in ys_)))
            RW.label(v, f'n{n} fill {100 * fm.mean():.1f}%  side middles T{d["top"]} B{d["bottom"]} L{d["left"]} R{d["right"]} px')
            for th, col in ((3, (0, 0, 0)), (1, (255, 255, 255))):
                cv2.putText(v, f'deepest (inner 80%) T{mx["top"]} B{mx["bottom"]} L{mx["left"]} R{mx["right"]} px', (6, 42),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, th)
            tiles.append(v)
            src[n] += (f'; edge fill: {100 * fm.mean():.1f}% of the frame, depth at the side middles top {d["top"]}, '
                       f'bottom {d["bottom"]}, left {d["left"]}, right {d["right"]} px, deepest along the inner 80 % of each side top '
                       f'{mx["top"]}, bottom {mx["bottom"]}, left {mx["left"]}, right {mx["right"]} px')
        tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 3)
        cv2.imwrite(os.path.join(out, 'edge_fill_sheet.jpg'),
                    np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    pair = [np.hstack([small(O[n], f'original n{n}'), small(R[n], f'n{n} {tag[n]}')]) for n in ns]
    write_mp4(os.path.join(out, 'side_by_side.mp4'), pair, 24, loops=3)
    slow = [cv2.putText(p.copy(), 'SLOW 6 fps (each frame x4)', (p.shape[1] // 2 - 140, p.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2) for p in pair]
    write_mp4(os.path.join(out, 'slow_6fps.mp4'), [p for p in slow for _ in range(4)], 24)
    hold_ns = [n for n in ns if n in BASE]
    diag = []
    for n in hold_ns:
        top = np.hstack([small(O[n], f'original n{n}'), small(BASE[n], f'n{n} {LABELS[n][0]}')])
        bot = np.hstack([small(FX[n], f'n{n} {LABELS[n][1]}'),
                         small(R[n], f'n{n} result: {tag[n]}')])
        diag.append(np.vstack([top, bot]))
    if diag:
        write_mp4(os.path.join(out, 'holds_diag_6fps.mp4'), [d for d in diag for _ in range(4)], 24)
        cv2.imwrite(os.path.join(out, 'holds_diag_sheet.jpg'),
                    np.vstack([cv2.resize(d, (d.shape[1] // 2, d.shape[0] // 2), interpolation=cv2.INTER_AREA)
                               for d in diag[::2]]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    cov = [small(COVER[n], f'n{n} {tag[n]}: inferred showing {EXPOSED[n][0]} px of {EXPOSED[n][1]}', 560)
           for n in hold_ns if EXPOSED[n][1]]
    if cov:
        cov += [np.zeros_like(cov[0])] * (-len(cov) % 3)
        cv2.imwrite(os.path.join(out, 'cover_check_sheet.jpg'),
                    np.vstack([np.hstack(cov[i:i + 3]) for i in range(0, len(cov), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    tiles = [np.vstack([small(O[n], f'orig n{n}', 320), small(R[n], tag[n], 320)]) for n in ns]
    tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 6)         # pad the last row
    rows = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
    cv2.imwrite(os.path.join(out, 'contact_sheet.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    drawings = sorted({fs[n].get('id', fs[n].get('drawing', fs[n].get('hold'))) for n in ns
                       if not fs[n].get('white') and not fs[n].get('black')})
    with open(os.path.join(out, 'sources.md'), 'w') as f:
        f.write(f'# {sheet.get("name", "window")} [{f0}, {f1}): where every frame comes from\n\n')
        frozen = sorted({fs[n].get('id') for n in ns if fs[n].get('frozen')})
        variants = sorted({fs[n].get('id') for n in ns if fs[n].get('variant_of')})
        bodies = [d for d in drawings if d not in frozen and d not in variants]
        f.write(f'{len(ns)} frames at 24 fps ({len(new_ns)} new, {len(ns) - len(new_ns)} frozen seam frame(s) from an '
                f'earlier window: {", ".join(frozen) or "none"}); {len(drawings)} distinct images in use: '
                f'{len(bodies)} {sheet.get("state_label", "body/smear states")} ({", ".join(bodies)})'
                + (f', {len(variants)} effect variant(s) of an existing body ({", ".join(variants)})' if variants else '')
                + (f', {len(frozen)} frozen' if frozen else '') +
                f'; ' + '; '.join(_exposure_counts(fs, ns)) + '.\n\n')
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
