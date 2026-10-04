"""A manga-panel shot rebuilt in layers, the way the MMV builds it (shot 0 was the method proof).

  panel   one drawing (the redrawn manga panel, in the reference frame's framing) moved as the original moves it:
          a 2.5D camera (perspective move plus slight parallax between parts of the panel), measured from
          the original per frame (anime/flowcam.py: optical flow chained from the reference frame, regularised into
          one perspective move plus a very smooth parallax correction, then smoothed in time as the original's
          eased camera is, so the drawing is carried rigidly and never wobbles); the dark fade-in frames are tied
          to the first normal frame by flow similarities measured on the drawing seen through the bright flame
  flame   the cursed-energy flame (cyan for Gojo, red for Sukuna): its shape, colour and inner light (blurred so
          the old lines vanish) and its black ink tendrils are taken from the original frame by frame, so it
          moves exactly like the original; the new panel's strokes show through it
  light   the flame's haze on the panel around it, the screen vignette, the exposure ramp and the fade from
          black, all measured from the original

usage: python3 anime/layered.py PANEL.png OUT_DIR [--shot s0|s1] [--ref N]
  PANEL.png is in the framing of the shot's reference frame at 1672x941.
Writes OUT_DIR/R_nNNNN.png for every frame of the shot (1672x941)."""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_window import original  # noqa: E402
import flowcam  # noqa: E402

W, H = 1672, 941
SIGMA_PARALLAX = float(os.environ.get('SIGMA_PARALLAX', 70))   # px; smaller follows parallax closer but stretches
HOLDOUT = {int(x) for x in os.environ.get('HOLDOUT', '').split(',') if x}   # frames kept out of the camera fit (validation)
FOCUS = os.environ.get('FOCUS', '1') == '1'            # match the original's depth of field
REFINE = os.environ.get('REFINE', '0') == '1'          # edge-aware local motion on top: closer, but the screentone swims
BLOOM = (0.30, 0.20)                              # soft bloom of the flame at sigma 20 and 60 px
WATERMARK = (slice(635, 712), slice(400, 765))    # screen-fixed creator watermark in the source frames

# per shot: frame range [F0, F1), reference frame, first frame after the fade from black, flame colour model,
# the flame's typical colour (fallback) and the haze colour right at its edge (both BGR 0-1, measured)
SHOTS = {
    's0': dict(F0=73, F1=91, REF=86, FADE_END=78, FLAME='cyan',
               FLAME_BGR=(214 / 255, 203 / 255, 32 / 255), GLOW=(0.45 / 0.91, 0.30 / 0.91, 0.055 / 0.91)),
    's1': dict(F0=91, F1=109, REF=100, FADE_END=94, FLAME='red',
               FLAME_BGR=(97 / 255, 84 / 255, 231 / 255), GLOW=(0.08 / 0.91, 0.05 / 0.91, 0.264 / 0.91)),
    # shot 1 haze, n98-106 over dark surroundings: R 0.26 at the edge, 0.15 at 11 px, 0.10 at 28 px, 0.06 at 62 px
}
SHOT = None


def configure(name):
    """select the shot; sets F0, F1, REF, FADE_END, FLAME, FLAME_BGR, GLOW as module globals"""
    global SHOT, F0, F1, REF, FADE_END, FLAME, FLAME_BGR, GLOW
    c = SHOTS[name]
    SHOT, F0, F1, REF, FADE_END, FLAME = name, c['F0'], c['F1'], c['REF'], c['FADE_END'], c['FLAME']
    FLAME_BGR = np.float32(c['FLAME_BGR'])
    GLOW = np.float32(c['GLOW']) if c['GLOW'] is not None else None


def chroma(o):
    """how strongly a pixel has the flame's hue (0-1 scale): cyan = min(G,B)-R, red = R-max(G,B)"""
    b, g, r = o[..., 0], o[..., 1], o[..., 2]
    return np.minimum(g, b) - r if FLAME == 'cyan' else r - np.maximum(g, b)


def bright(o):
    """the flame's dominant channel: G for cyan, R for red"""
    return o[..., 1] if FLAME == 'cyan' else o[..., 2]


def pale(o):
    """weak channel over dominant one: low for the saturated flame, high for the flame-lit panel beside it"""
    b, g, r = o[..., 0], o[..., 1], o[..., 2]
    return r / np.maximum(g, 1e-3) if FLAME == 'cyan' else np.maximum(g, b) / np.maximum(r, 1e-3)


# saturation gate per flame colour: (fully flame below, not flame above) for pale(); measured on the originals:
# cyan flame ~0.14, its dim body ~0.22, cyan-lit sleeve ~0.5; red flame ~0.42, pink-lit panel ~0.8
# red (shot 1, n100): flame interior pale 0.30-0.51 / chroma 0.45-0.60; pink-lit panel pale 0.61-0.73 / chroma 0.22-0.32
PALE_GATE = {'cyan': (0.27, 0.40), 'red': (0.48, 0.60)}
PALE_WEAK = {'cyan': 0.30, 'red': 0.50}
PALE_VIVID = {'cyan': 0.22, 'red': 0.42}
CHROMA_GATE = {'cyan': (0.20, 0.42), 'red': (0.30, 0.45)}     # chroma / k: not flame below, flame above
CHROMA_WEAK = {'cyan': 0.18, 'red': 0.30}


configure('s0')


FADE_LOG = []      # one entry per fade step (n77->78, n76->77, ...): whether it was accepted or fell back


def _fade_step(oa, ob):
    """Similarity from frame a to frame b in the fade from black (n74-78).  The panel is nearly black there, but
    the old drawing's lines inside the bright flame are clear, and they belong to the panel: measure the optical
    flow on them (plus any lit panel), keep forward-backward consistent vectors, fit a similarity by RANSAC.
    Feature-matched homographies had only ~8 inliers here and threw the hand ~250 px off (Limo, review 020)."""
    a, b = flowcam.prep(oa, chroma), flowcam.prep(ob, chroma)
    dis = flowcam._dis()
    f = cv2.GaussianBlur(dis.calc(a, b, None), (0, 0), 3)
    fb = cv2.GaussianBlur(dis.calc(b, a, None), (0, 0), 3)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    back = cv2.remap(fb, xx + f[..., 0], yy + f[..., 1], cv2.INTER_LINEAR)
    g = a.astype(np.float32)
    tex = cv2.GaussianBlur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (0, 0), 3) > 20
    inner = cv2.erode((flame_core(oa) > 0.5).astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
    rel = tex & (inner | (lum(oa) > 0.04)) & (np.hypot(*(f + back).transpose(2, 0, 1)) < 1.0)
    rel[WATERMARK] = False
    ys, xs = np.mgrid[0:H:6, 0:W:6]
    m = rel[ys, xs]
    src = np.float32(np.c_[xs[m], ys[m]])
    dst = src + f[ys[m], xs[m]]
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    if M is None:
        return np.eye(3)
    s, rot = np.hypot(M[0, 0], M[1, 0]), np.degrees(np.arctan2(M[1, 0], M[0, 0]))
    ok = inl is not None and inl.sum() >= 100 and 0.8 < s < 1.25 and abs(rot) < 8 and np.abs(M[:, 2]).max() < 300
    FADE_LOG.append(dict(inliers=int(inl.sum()) if inl is not None else 0, scale=round(float(s), 4),
                         rotation_deg=round(float(rot), 3), shift=[round(float(v), 1) for v in M[:, 2]],
                         accepted=bool(ok), fallback='identity' if not ok else None))
    print(f'fade step: {int(inl.sum()) if inl is not None else 0} inliers, scale {s:.3f}, rotation {rot:+.2f} deg'
          + ('' if ok else '  -> REJECTED, identity used instead (recorded in run.json)'))
    return np.vstack([M, [0, 0, 1]]) if ok else np.eye(3)


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
    quadratic in n per pixel: one over the main move (from the frame before FADE_END on, pinned to zero at the
    reference) and one over the fade, blended across FADE_END-1 .. FADE_END+1."""
    main = _polyfit_fields(F, [n for n in range(FADE_END - 1, F1) if n in F], 2, anchor=REF)
    fade = _polyfit_fields(F, [n for n in range(F0 + 1, FADE_END + 2) if n in F], 2)
    out = {}
    for n in range(F0, F1):
        a = float(np.clip((n - (FADE_END - 1)) / 2, 0, 1))
        m = main(n) if a > 0 else 0
        f = fade(max(n, F0 + 1)) if a < 1 else 0
        out[n] = (a * m + (1 - a) * f).astype(np.float32)
    out[REF] = np.zeros_like(out[REF])
    return out


def camera_fields(O):
    """{n: displacement field from frame n to the reference framing} for the whole shot"""
    F = flowcam.fields({n: O[n] for n in range(FADE_END, F1) if n not in HOLDOUT}, REF, chroma=chroma)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def off_edge(o):
        """away from the flame's moving outline and its ink (the panel lines inside the flame are fine)"""
        c = (flame_core(o) > 0.5).astype(np.uint8)
        band = cv2.dilate(c, np.ones((61, 61), np.uint8)) - cv2.erode(c, np.ones((25, 25), np.uint8))
        return band == 0
    off_ref = off_edge(O[REF])
    off_ref[WATERMARK] = False                             # the watermark sits in the reference frame too
    off_ref = off_ref.astype(np.float32)
    for n in range(FADE_END, F1):
        if n == REF or n in HOLDOUT:
            continue
        back = flowcam.warp(off_ref, F[n]) > 0.99
        g = flowcam.prep(O[n], chroma).astype(np.float32)
        tex = cv2.GaussianBlur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (0, 0), 6) > 25
        rel = off_edge(O[n]) & back & tex
        rel[WATERMARK] = False                             # ... and in this frame (screen-fixed: same box)
        reg, _, inl = flowcam.regularize(F[n], rel, sigma=SIGMA_PARALLAX)
        F[n] = flowcam.refine(F[n], rel, flowcam.prep(O[n], chroma), reg) if REFINE else reg
        print(f'camera n{n}: reliable {rel.mean():.2f} of frame, homography inliers {inl:.2f}')
    Hn = np.eye(3)
    FADE_LOG.clear()
    for n in range(FADE_END - 1, F0 - 1, -1):
        if n >= F0 + 1:                                   # the very first frame is black: reuse the next one's
            Hn = Hn @ _fade_step(O[n], O[n + 1])            # n -> n+1 -> ... -> FADE_END
        p = cv2.perspectiveTransform(np.dstack([xx, yy]).reshape(1, -1, 2), Hn).reshape(H, W, 2)
        fe = cv2.remap(F[FADE_END], p[..., 0], p[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        F[n] = (p - np.dstack([xx, yy]) + fe).astype(np.float32)
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
    closed = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))   # whole frame: no box-edge artefacts
    m[WATERMARK] = closed[WATERMARK]
    return m


def flame_core(o):
    """soft alpha of the cyan flame body in an original frame"""
    cy, g = chroma(o), bright(o)
    pl = pale(o)
    # in the fade from black the whole flame is dimmer: measure against this frame's own flame brightness
    cand = cy > 0.08
    k = float(np.percentile(g[cand], 95)) / 0.86 if cand.sum() > 500 else 1.0
    k = min(max(k, 0.25), 1.0)
    # the flame is strongly saturated; the flame-lit panel beside it has the same hue but paler
    sat = 1 - smooth(pl, *PALE_GATE[FLAME])
    a = close_watermark(smooth(cy / k, *CHROMA_GATE[FLAME]) * smooth(g / k, 0.30, 0.55) * sat)
    keep = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(keep)
    good = np.zeros(n, bool)
    good[1:] = st[1:, 4] >= 12                   # the detached droplets (some only ~4 px across) are part of the flame
    m = cv2.dilate(good[lab].astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
    a = a * m
    # the body can be much dimmer than its bright crest (n74-77): grow the flame from the confident part into
    # connected, clearly cyan pixels that are still well above the dark glow-over-ink beside it (green > 0.32 k)
    weak = ((cy / k > CHROMA_WEAK[FLAME]) & (g / k > 0.32) & (pl < PALE_WEAK[FLAME])).astype(np.uint8)
    n2, lab2 = cv2.connectedComponents(weak | (a > 0.5).astype(np.uint8))
    seeded = np.zeros(n2, bool)
    seeded[np.unique(lab2[a > 0.5])] = True
    seeded[0] = False
    a = np.maximum(a, (seeded[lab2] & (weak > 0)).astype(np.float32))
    # darker, still cyan patches enclosed by the flame belong to it (its shading), not holes
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    body = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, disk)   # seal gaps (round, no square bridges)
    ff = body.copy()
    cv2.floodFill(ff, np.zeros((o.shape[0] + 2, o.shape[1] + 2), np.uint8), (0, 0), 1)
    # enclosed pockets count only if they are cyan (the flame's own darker shading); a pocket of ink between the
    # body and a droplet is not flame (n88: a square bridge there showed as a dark block, Limo review 020)
    inside = ((ff == 0) & (cy / k > 0.06)) | (a > 0.5)
    # the old drawing's dark lines inside the flame can run out to its edge, so they are not enclosed holes:
    # with those thin lines closed away (grey closing, 11 px), the flame body is solid; its outline still comes
    # from the unclosed alpha (the body is eroded back before use)
    oc = cv2.morphologyEx(o, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    ac = smooth(chroma(oc) / k, *CHROMA_GATE[FLAME]) * smooth(bright(oc) / k, 0.30, 0.55)
    inside |= cv2.erode((ac > 0.5).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    # inside the flame everything is flame (the old drawing's lines only dim it), except real holes: large
    # near-black patches such as the ring in n88-90
    black = (lum(o) / k < 0.12).astype(np.uint8)
    n_, lab, st, _ = cv2.connectedComponentsWithStats(black)
    big = np.zeros(n_, bool)
    big[1:] = st[1:, 4] >= 300
    holes = big[lab]
    solid = (inside & ~holes).astype(np.float32)
    solid = cv2.GaussianBlur(solid, (0, 0), 1.5)
    a = np.maximum(a, solid)
    # thin strips hanging off the body are the flame-lit sleeve and cuff edges beside it, not flame (n82)
    body = (a > 0.5).astype(np.uint8)
    opened = cv2.morphologyEx(body, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    strips = body & (cv2.dilate(opened, np.ones((3, 3), np.uint8)) == 0)
    a = a * (1 - strips)
    # keep the main body and round detached droplets; drop thin strips (flame-lit sleeve edges, not flame)
    n3, lab3, st3, _ = cv2.connectedComponentsWithStats((a > 0.5).astype(np.uint8))
    if n3 > 2:
        main_i = 1 + int(np.argmax(st3[1:, 4]))
        keep3 = np.zeros(n3, bool)
        keep3[main_i] = True
        for i in range(1, n3):
            if i == main_i or st3[i, 4] < 12:
                continue
            comp = lab3 == i
            pts = np.column_stack(np.where(comp)[::-1]).astype(np.float32)
            (_, _), (w_, h_), _ = cv2.minAreaRect(pts)
            # a real droplet floats in the dark; a bit of flame-lit sleeve sits among lit panel
            ring = (cv2.dilate(comp.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & ~comp
            dark_around = float(np.mean(lum(o)[ring] / k)) < 0.25 if ring.any() else True
            # ... unless it is as saturated as the flame itself (n89-90: a cyan dot on the white cuff, Limo 021)
            vivid = float(np.median(pl[comp])) < PALE_VIVID[FLAME]
            keep3[i] = st3[i, 4] < 4000 and max(w_, h_) < 3 * max(min(w_, h_), 1) and (dark_around or vivid)
        drop = (lab3 > 0) & ~keep3[lab3]
        a = a * (1 - cv2.dilate(drop.astype(np.uint8), np.ones((5, 5), np.uint8)))
    # small pale-cyan light dots sitting inside a dark ink ring (n88-90, right white region): flame light too,
    # though too pale for the saturation gate
    dots = ((cy / k > 0.12) & (lum(o) / k > 0.40) & (a < 0.5)).astype(np.uint8)
    n4, lab4, st4, _ = cv2.connectedComponentsWithStats(dots)
    for i in range(1, n4):
        if not 12 <= st4[i, 4] <= 400:
            continue
        comp = lab4 == i
        ring = (cv2.dilate(comp.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & ~comp
        if ring.any() and float(np.mean(lum(o)[ring] / k)) < 0.25:
            a = np.maximum(a, cv2.GaussianBlur(comp.astype(np.float32), (0, 0), 0.8))
    return a


def exposure(n, o, o_ref, field):
    """the original's brightness of the panel in frame n relative to the reference frame (fade + ramp)"""
    w = flowcam.warp(o_ref, field)
    m = (flame_core(o) < 0.01) & (flame_core(w) < 0.01) & (lum(w) > 0.08)
    m = cv2.erode(m.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    if m.sum() < 500:
        return float(lum(o).mean() / max(lum(o_ref).mean(), 1e-4))
    if n < FADE_END:      # fade: the panel first shows near the flame; compare its brightest parts there
        d = cv2.distanceTransform((flame_core(o) < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
        mm = m & (d < 250)
        mm = mm if mm.sum() > 500 else m
        return float(np.percentile(lum(o)[mm], 95) / max(np.percentile(lum(w)[mm], 95), 1e-4))
    return float(np.median(lum(o)[m]) / np.median(lum(w)[m]))


def smooth_ramp(g):
    """the measured exposure jitters by a few percent from frame to frame; the original's ramp does not"""
    ns = sorted(g)
    out = dict(g)
    for n in ns[1:-1]:
        if g[n] > 0.3:
            out[n] = (g[n - 1] + g[n] + g[n + 1]) / 3
    # the shot only ever fades in and brightens: no dips (two measurements meet at n77/78)
    run = 0.0
    for n in ns:
        run = max(run, out[n])
        out[n] = run
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


FOCUS_SIGMAS = (0.0, 0.8, 1.6, 2.4, 3.2, 4.5, 6.0)


def match_focus(panel, o_ref):
    """The original keeps the manga panel's depth of field (the near sleeve is soft); the redrawn panel is sharp
    everywhere.  Per region, blur the panel until its fine detail matches the original's (local energy of the
    Laplacian over ~25 px), measured away from the flame and the watermark; under the flame, keep it sharp."""
    def energy(x):
        g = cv2.GaussianBlur(lum(x), (0, 0), 0.7)
        return cv2.GaussianBlur(np.abs(cv2.Laplacian(g, cv2.CV_32F)), (0, 0), 25)
    m = cv2.dilate((flame_core(o_ref) > 0.05).astype(np.uint8), np.ones((61, 61), np.uint8)) == 0
    m[WATERMARK] = False
    m &= lum(o_ref) > 0.06
    mf = m.astype(np.float32)
    eo = energy(o_ref)
    stack = [panel if s0 == 0 else cv2.GaussianBlur(panel, (0, 0), s0) for s0 in FOCUS_SIGMAS]
    # the original is a video frame (compressed, slightly soft overall): compare against its in-focus level
    err = np.array([np.abs(np.log((energy(b) + 1e-3) / (eo + 1e-3))) for b in stack])
    best = np.argmin(err, 0).astype(np.float32)
    sig = np.array(FOCUS_SIGMAS, np.float32)[best.astype(int)]
    sig = cv2.GaussianBlur(sig * mf, (0, 0), 30) / np.maximum(cv2.GaussianBlur(mf, (0, 0), 30), 1e-3)
    sig = np.where(cv2.GaussianBlur(mf, (0, 0), 30) > 0.05, sig, 0.0)
    # blend between the two nearest blur levels
    out = np.zeros_like(panel)
    levels = np.array(FOCUS_SIGMAS, np.float32)
    idx = np.clip(np.searchsorted(levels, sig) - 1, 0, len(levels) - 2)
    t = np.clip((sig - levels[idx]) / (levels[idx + 1] - levels[idx]), 0, 1)[..., None]
    for i in range(len(levels) - 1):
        sel = (idx == i)[..., None]
        out = np.where(sel, stack[i] * (1 - t) + stack[i + 1] * t, out)
    return out, sig


def prepare_panel(panel, o_ref, vig):
    """tone and depth of field brought to the original reference frame"""
    panel = match_tone(panel, o_ref, vig)
    if FOCUS:
        panel, _ = match_focus(panel, o_ref)
    return panel


def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W * 0.47) / (W * 0.50)) ** 2 + ((y - H * 0.55) / (H * 0.62)) ** 2)
    return (1 - 0.92 * smooth(r, 0.45, 1.05))[..., None]


def render(panel, n, o, o_ref, gain, vig, field, layers=None):
    """one output frame; if a dict is passed as layers, the intermediate layers are stored in it"""
    P = np.clip(flowcam.warp(panel, field), 0, 1)
    if n < FADE_END:                                  # the fade from black: the whole drawing is soft
        P = cv2.GaussianBlur(P, (0, 0), 1.0 + 0.8 * (FADE_END - n))
    base = P * gain * vig
    core = flame_core(o)
    c3 = core[..., None]
    # the flame's own colour and inner light come from the original: the old drawing's dark lines are closed
    # away first (grey closing, 9 px), then the colour is spread smoothly with the flame alpha as weight, so
    # there is no hard switch anywhere inside or at the edge
    oc = cv2.morphologyEx(o, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cw = core.copy()
    cw[WATERMARK] = 0                                 # the screen-fixed watermark crosses the flame: fill it in
    def ncb(sig):
        return (cv2.GaussianBlur(oc * cw[..., None], (0, 0), sig),
                cv2.GaussianBlur(cw, (0, 0), sig)[..., None])
    (n4, w4), (n30, w30) = ncb(4), ncb(30)
    t = np.clip(w4 / 0.5, 0, 1)
    colour = t * n4 / np.maximum(w4, 1e-3) + (1 - t) * n30 / np.maximum(w30, 1e-3)
    # the new drawing's strokes show through the flame as much as the old ones did in this very frame
    lp = lum(P)
    lines = np.clip((cv2.GaussianBlur(lp, (0, 0), 4) - lp) / 0.12, 0, 1)
    lo = lum(o)
    old = np.clip((lum(oc) - lo) / np.maximum(lum(oc), 0.05), 0, 1)
    inner = (core > 0.9) & (cw > 0)
    strength = float(np.clip(old[inner].mean() / max(lines[inner].mean(), 1e-3), 0.05, 0.45)) if inner.sum() > 500 else 0.2
    fill = colour * (1 - strength * lines[..., None])
    # black ink of the energy: thick near-black shapes beside (not inside) the flame, where the original is dark
    dist = cv2.distanceTransform((core < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    near = smooth(-dist, -90, -50) > 0.5
    dark = close_watermark((o[..., 1] / max(gain, 0.3) < 0.30).astype(np.float32)) > 0.5
    ink = (near & dark & (core < 0.5)).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))   # tendrils are thick; panel lines are not
    ink = cv2.GaussianBlur(ink.astype(np.float32), (0, 0), 0.8)[..., None]
    # blue haze beside the flame (profile measured on the original's dark surroundings) and a soft bloom
    f = 0.45 * np.exp(-dist / 10) + 0.55 * np.exp(-dist / 70)
    lit = colour * c3
    bloom = BLOOM[0] * cv2.GaussianBlur(lit, (0, 0), 20) + BLOOM[1] * cv2.GaussianBlur(lit, (0, 0), 60)
    img = base * (1 - ink) + (GLOW * f[..., None] * min(1.0, gain * 1.2) + bloom) * (1 - c3)
    img = img * (1 - c3) + fill * c3
    if layers is not None:
        flat = np.float32([0.45, 0.42, 0.40]) * gain * vig
        layers.update(core=core, fill_colour=colour, lines=lines * strength, ink=ink[..., 0], base=base,
                      line_strength=strength,
                      fx_on_flat=(flat * (1 - ink) + (GLOW * f[..., None] * min(1.0, gain * 1.2) + bloom)
                                  * (1 - c3)) * (1 - c3) + fill * c3)
    return img


def main():
    global REF
    panel_path, out = sys.argv[1], sys.argv[2]
    configure(sys.argv[sys.argv.index('--shot') + 1] if '--shot' in sys.argv else 's0')
    if '--ref' in sys.argv:
        REF = int(sys.argv[sys.argv.index('--ref') + 1])
    os.makedirs(out, exist_ok=True)
    panel = cv2.imread(panel_path).astype(np.float32) / 255
    if panel.shape[:2] != (H, W):
        panel = cv2.resize(panel, (W, H), interpolation=cv2.INTER_AREA)
    vig = vignette()
    O = {n: orig(n) for n in range(F0, F1)}
    o_ref = O[REF]
    panel = prepare_panel(panel, o_ref, vig)
    fields = camera_fields(O)
    gains = smooth_ramp({n: exposure(n, O[n], o_ref, fields[n]) for n in range(F0, F1)})
    for n in range(F0, F1):
        img = render(panel, n, O[n], o_ref, gains[n], vig, fields[n])
        cv2.imwrite(os.path.join(out, f'R_n{n:04d}.png'), np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8))
        print(n, f'exposure {gains[n]:.3f}')


if __name__ == '__main__':
    main()
