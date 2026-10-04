"""Shot 0 [73, 91) rebuilt in layers, the way the original is built.

  panel   one drawing (the redrawn manga panel, in the reference frame's framing) moved as the original moves it:
          a 2.5D camera (perspective move plus slight parallax between parts of the panel), measured from
          the original per frame (anime/flowcam.py: optical flow chained from the reference frame, regularised into
          one perspective move plus a very smooth parallax correction, then smoothed in time as the original's
          eased camera is, so the drawing is carried rigidly and never wobbles); the darkest fade-in frames
          n73-77 are tied to n78 by feature-matched homographies
  flame   the cyan cursed-energy flame: its shape, colour and inner light (blurred so the old lines vanish)
          and its black ink tendrils are taken from the original frame by frame, so it moves exactly like
          the original; the new panel's strokes show through it
  light   the flame's blue light on the panel around it, the screen vignette, the exposure ramp and the
          fade from black, all measured from the original

usage: python3 anime/shot0.py PANEL.png OUT_DIR [--ref N] [--panel-has-flame]
  PANEL.png is in the framing of frame N (default 82) at 1672x941.  --panel-has-flame: the panel still shows n82's flame (a stand-in
  such as R_n0082); its cyan is pushed back to the panel's grey-blue before use.
Writes OUT_DIR/R_n0073.png ... R_n0090.png (1672x941)."""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_window import original  # noqa: E402
import flowcam  # noqa: E402

W, H = 1672, 941
F0, F1, REF = 73, 91, 82
SIGMA_PARALLAX = float(os.environ.get('SIGMA_PARALLAX', 70))
REFINE = os.environ.get('REFINE', '0') == '1'          # edge-aware local motion on top: closer, but the screentone swims   # px; smaller follows the arm/body parallax closer

CYAN = np.float32([214, 203, 32]) / 255          # BGR, median of the original's flame core
GLOW = np.float32([0.45, 0.30, 0.055]) / 0.91    # BGR, the blue haze right at the flame's edge (measured)
WATERMARK = (slice(635, 712), slice(400, 765))    # screen-fixed creator watermark in the source frames


def _boost(o):
    l = o.mean(2) * 255
    b, g, r = o[..., 0], o[..., 1], o[..., 2]
    c = (np.minimum(g, b) - r) * 255 > 35
    p = np.percentile(l[~c], 99.5) + 1 if (~c).any() else 255
    return (255 * np.clip(l / p, 0, 1) ** 0.7).astype(np.uint8), c


def _homography(oa, ob):
    """feature-matched homography from frame a to frame b, panel features only (flame, watermark masked)"""
    sift = cv2.SIFT_create(4000, contrastThreshold=0.01)
    kp = []
    for o in (oa, ob):
        g, c = _boost(o)
        m = (~cv2.dilate(c.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)).astype(np.uint8) * 255
        m[480:560, 230:560] = 0
        kp.append(sift.detectAndCompute(g, m))
    (ka, da), (kb, db) = kp
    good = [x for x, y in cv2.BFMatcher().knnMatch(da, db, k=2) if x.distance < 0.75 * y.distance]
    pa = np.float32([ka[x.queryIdx].pt for x in good])
    pb = np.float32([kb[x.trainIdx].pt for x in good])
    Hm, _ = cv2.findHomography(pa, pb, cv2.RANSAC, 3.0)
    return Hm


def _polyfit_fields(F, ns, deg, anchor=None, w=None):
    """least-squares polynomial in n per pixel; anchor: frame whose field is pinned to zero (the reference)"""
    X = np.array([F[n] for n in ns])
    t = np.array(ns, np.float64) - (anchor if anchor is not None else 0)
    A = np.stack([t ** k for k in range(0 if anchor is None else 1, deg + 1)], 1)
    w = np.ones(len(ns)) if w is None else np.asarray(w, np.float64)
    C = np.tensordot(np.linalg.pinv(A * w[:, None]), X * w[:, None, None, None], axes=(1, 0))
    return lambda n: np.tensordot(np.array([(n - (anchor if anchor is not None else 0)) ** k
                                            for k in range(0 if anchor is None else 1, deg + 1)]), C, axes=(0, 0))


def smooth_in_time(F):
    """The original's camera is keyframed and eased, so the true motion of every panel point is smooth in time;
    the measured fields carry a few px of frame-to-frame noise, which would make the drawing jitter.  Fit a
    quadratic in n per pixel: one over the main move (n77-90, pinned to zero at the reference) and one over the
    fade (n74-79), blended across n77-79."""
    main = _polyfit_fields(F, list(range(77, F1)), 2, anchor=REF)
    fade = _polyfit_fields(F, list(range(74, 80)), 2)
    out = {}
    for n in range(F0, F1):
        a = float(np.clip((n - 77) / 2, 0, 1))         # 0 up to n77, 1 from n79
        m = main(n) if a > 0 else 0
        f = fade(max(n, 74)) if a < 1 else 0
        out[n] = (a * m + (1 - a) * f).astype(np.float32)
    out[REF] = np.zeros_like(out[REF])
    return out


def camera_fields(O):
    """{n: displacement field from frame n to the reference framing} for the whole shot"""
    F = flowcam.fields({n: O[n] for n in range(78, F1)}, REF)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def off_edge(o):
        """away from the flame's moving outline and its ink (the panel lines inside the flame are fine)"""
        c = (flame_core(o) > 0.5).astype(np.uint8)
        band = cv2.dilate(c, np.ones((61, 61), np.uint8)) - cv2.erode(c, np.ones((25, 25), np.uint8))
        return band == 0
    off_ref = off_edge(O[REF]).astype(np.float32)
    for n in range(78, F1):
        if n == REF:
            continue
        back = flowcam.warp(off_ref, F[n]) > 0.99
        g = flowcam.prep(O[n]).astype(np.float32)
        tex = cv2.GaussianBlur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (0, 0), 6) > 25
        rel = off_edge(O[n]) & back & tex
        rel[WATERMARK] = False                             # the screen-fixed watermark drags the flow
        reg, _, inl = flowcam.regularize(F[n], rel, sigma=SIGMA_PARALLAX)
        F[n] = flowcam.refine(F[n], rel, flowcam.prep(O[n]), reg) if REFINE else reg
        print(f'camera n{n}: reliable {rel.mean():.2f} of frame, homography inliers {inl:.2f}')
    Hn = np.eye(3)
    for n in range(77, F0 - 1, -1):
        if n >= 74:
            Hn = Hn @ _homography(O[n], O[n + 1])           # n -> n+1 -> ... -> 78
        p = cv2.perspectiveTransform(np.dstack([xx, yy]).reshape(1, -1, 2), Hn).reshape(H, W, 2)
        f78 = cv2.remap(F[78], p[..., 0], p[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        F[n] = (p - np.dstack([xx, yy]) + f78).astype(np.float32)
    return smooth_in_time(F)


def orig(n):
    return original(n, (W, H)).astype(np.float32) / 255


def lum(x):
    return x @ np.float32([0.114, 0.587, 0.299])


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def close_watermark(m, k=11):
    """the grey watermark letters punch holes in masks taken from the original; close them inside its box"""
    m = m.copy()
    m[WATERMARK] = cv2.morphologyEx(m[WATERMARK], cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    return m


def flame_core(o):
    """soft alpha of the cyan flame body in an original frame"""
    b, g, r = o[..., 0], o[..., 1], o[..., 2]
    # in the fade from black the whole flame is dimmer: measure against this frame's own flame brightness
    cy = np.minimum(g, b) - r
    cand = cy > 0.08
    k = float(np.percentile(g[cand], 95)) / 0.86 if cand.sum() > 500 else 1.0
    k = min(max(k, 0.25), 1.0)
    a = close_watermark(smooth(cy / k, 0.20, 0.42) * smooth(g / k, 0.30, 0.55))
    keep = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(keep)
    good = np.zeros(n, bool)
    good[1:] = st[1:, 4] >= 40                   # the detached droplets are part of the original flame
    m = cv2.dilate(good[lab].astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
    a = a * m
    # darker, still cyan patches enclosed by the flame belong to it (its shading), not holes
    body = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))   # seal gaps
    ff = body.copy()
    cv2.floodFill(ff, np.zeros((o.shape[0] + 2, o.shape[1] + 2), np.uint8), (0, 0), 1)
    # enclosed patches that are cyan or bright belong to the flame (its whitish hot centre, its darker
    # shading); enclosed near-black patches are real holes in it (ink), as in n88-90
    holes = (ff == 0) & ((cy > 0.06) | (lum(o) / k > 0.30))
    return np.maximum(a, holes.astype(np.float32))


def decyan(panel):
    """stand-in only: turn the n82 flame in a redrawn frame back into grey-blue panel"""
    a = flame_core(panel)
    a = cv2.GaussianBlur(a, (0, 0), 2)[..., None]
    l = lum(panel)[..., None]
    grey = (l - 0.55).clip(0) * 1.4 * np.float32([0.92, 0.80, 0.62])    # lines stay, cyan glow goes
    return panel * (1 - a) + grey * a


def exposure(n, o, o_ref, field):
    """the original's brightness of the panel in frame n relative to the reference frame (fade + ramp)"""
    w = flowcam.warp(o_ref, field)
    m = (flame_core(o) < 0.01) & (flame_core(w) < 0.01) & (lum(w) > 0.08)
    m = cv2.erode(m.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    if m.sum() < 500:
        return float(lum(o).mean() / max(lum(o_ref).mean(), 1e-4))
    if n < 78:      # fade: most of the panel is still black, compare the brightest panel parts instead
        return float(np.percentile(lum(o)[m], 95) / max(np.percentile(lum(w)[m], 95), 1e-4))
    return float(np.median(lum(o)[m]) / np.median(lum(w)[m]))


def smooth_ramp(g):
    """the measured exposure jitters by a few percent from frame to frame; the original's ramp does not"""
    ns = sorted(g)
    out = dict(g)
    for n in ns[1:-1]:
        if g[n] > 0.3:
            out[n] = (g[n - 1] + g[n] + g[n + 1]) / 3
    return out


def match_tone(panel, o_ref, vig):
    """bring the redrawn panel's brightness and colour cast to the original reference frame, so the original's
    exposure ramp lands on the same levels: one global gain per colour channel plus a gentle large-scale
    correction (sigma 150 px, within 0.75-1.33).  Measured away from the flame, its ink band and the watermark,
    and only where the panel is not black.  Lines and screentone keep their own contrast."""
    m = cv2.dilate((flame_core(o_ref) > 0.05).astype(np.uint8), np.ones((161, 161), np.uint8)) == 0
    m[WATERMARK] = False
    pv = panel * vig
    m &= (lum(o_ref) > 0.03) & (lum(pv) > 0.03)
    mf = m.astype(np.float32)

    def nlp(x):
        return cv2.GaussianBlur(x * mf, (0, 0), 150) / np.maximum(cv2.GaussianBlur(mf, (0, 0), 150), 1e-3)
    gains = []
    for c in range(3):
        g0 = float(np.median(o_ref[..., c][m]) / max(np.median(pv[..., c][m]), 1e-3))
        local = np.clip((nlp(o_ref[..., c]) + 0.01) / (nlp(pv[..., c]) * g0 + 0.01), 0.75, 1.33)
        gains.append(g0 * local)
    return panel * np.dstack(gains)


def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W * 0.47) / (W * 0.50)) ** 2 + ((y - H * 0.55) / (H * 0.62)) ** 2)
    return (1 - 0.92 * smooth(r, 0.45, 1.05))[..., None]


def render(panel, n, o, o_ref, gain, vig, field):
    P = np.clip(flowcam.warp(panel, field), 0, 1)
    base = P * gain * vig
    if n < 78:                                        # the fade from black: the panel is also soft
        base = cv2.GaussianBlur(base, (0, 0), 1.0 + 0.8 * (78 - n))
    core = flame_core(o)
    c3 = core[..., None]
    # the flame's own colour and inner light come from the original, blurred inside the flame only so the
    # old panel lines vanish; the new panel's strokes then show through it
    cm = (core > 0.5).astype(np.float32)
    cm[WATERMARK] = 0                                 # the screen-fixed watermark crosses the flame: fill it in
    def ncb(sig):
        return (cv2.GaussianBlur(o * cm[..., None], (0, 0), sig),
                cv2.GaussianBlur(cm, (0, 0), sig)[..., None])
    (n5, w5), (n30, w30) = ncb(5), ncb(30)
    t = np.clip(w5 / 0.3, 0, 1)
    glow_src = t * n5 / np.maximum(w5, 1e-3) + (1 - t) * n30 / np.maximum(w30, 1e-3)
    glow_src = np.where(core[..., None] > 0.5, glow_src, CYAN)
    lp = lum(P)
    lines = np.clip((cv2.GaussianBlur(lp, (0, 0), 4) - lp) / 0.12, 0, 1)[..., None]   # the new panel's strokes
    fill = glow_src * (1 - 0.32 * lines)
    # black ink of the energy: where the original is near-black beside the flame (its tendrils move with it)
    dist = cv2.distanceTransform((core < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    near = smooth(-dist, -70, -20)
    # the ink is told apart by its red channel: lit panel ~0.55, ink (under the blue glow) ~0.06
    dark = close_watermark(1 - smooth(o[..., 2] / max(gain, 0.3), 0.10, 0.22))
    ink = (near * dark > 0.5).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))   # solid shapes, no specks
    ink = cv2.GaussianBlur(ink.astype(np.float32), (0, 0), 0.8)[..., None]
    # blue haze around the flame, by distance from it (profile measured on the original's dark surroundings:
    # B 0.45 at the edge, 0.32 at 10 px, 0.21 at 28 px, 0.13 at 60 px, 0.05 at 130 px)
    f = 0.45 * np.exp(-dist / 10) + 0.55 * np.exp(-dist / 70)
    img = base * (1 - ink) + GLOW * f[..., None] * min(1.0, gain * 1.2)
    img = img * (1 - c3) + fill * c3
    return img


def main():
    global REF
    panel_path, out = sys.argv[1], sys.argv[2]
    if '--ref' in sys.argv:
        REF = int(sys.argv[sys.argv.index('--ref') + 1])
    os.makedirs(out, exist_ok=True)
    panel = cv2.imread(panel_path).astype(np.float32) / 255
    if panel.shape[:2] != (H, W):
        panel = cv2.resize(panel, (W, H), interpolation=cv2.INTER_AREA)
    if '--panel-has-flame' in sys.argv:
        panel = decyan(panel)
    vig = vignette()
    O = {n: orig(n) for n in range(F0, F1)}
    o_ref = O[REF]
    panel = match_tone(panel, o_ref, vig)
    fields = camera_fields(O)
    gains = smooth_ramp({n: exposure(n, O[n], o_ref, fields[n]) for n in range(F0, F1)})
    for n in range(F0, F1):
        img = render(panel, n, O[n], o_ref, gains[n], vig, fields[n])
        cv2.imwrite(os.path.join(out, f'R_n{n:04d}.png'), np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8))
        print(n, f'exposure {gains[n]:.3f}')


if __name__ == '__main__':
    main()
