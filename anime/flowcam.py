"""Measure how a static drawing moves through a shot, from the original frames themselves.

MMV shots are cut-up manga panels moved by a 2.5D camera (a perspective move plus a little parallax between
parts of the panel), so one homography per frame does not fit the whole panel.  Instead this measures a
dense, smooth displacement field per frame: for every pixel of frame n, where that point of the panel sits
in the reference frame.  Frames are chained step by step (n -> n+-1 -> ... -> ref), each step a small,
reliable optical flow on contrast-normalised grey images in which the cyan effect is toned down, so the
panel lines inside the effect still guide it; the drift that chaining accumulates is then measured directly
against the reference frame and removed.

Raw optical flow swirls wherever the original has moving effects or ink over the panel, and a drawing warped
by it wobbles (the puppet look).  So the raw field is only a measurement: regularize() replaces it by one
perspective move (homography) fitted to the reliable panel area, plus a very smooth correction for the slight
parallax.  The drawing is then carried rigidly, as a 2.5D camera would carry it.

Use: warp(drawing_in_ref_framing, field[n]) puts the redrawn panel where the original shows it in frame n.
Effects that really move (flames, energy) are not carried by this; they are rebuilt per frame."""
import cv2
import numpy as np


def prep(o):
    """o: float BGR 0-1 original frame -> uint8 grey for tracking"""
    o = o * 255.0
    b, g, r = o[..., 0], o[..., 1], o[..., 2]
    l = o.mean(2)
    l = np.where(np.minimum(g, b) - r > 35, l * 0.35, l)
    l = 255 * np.clip(l / max(np.percentile(l, 99.7), 1.0), 0, 1) ** 0.6
    return cv2.createCLAHE(3.0, (16, 16)).apply(l.astype(np.uint8))


def _dis():
    d = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST)
    d.setFinestScale(1)
    d.setPatchSize(16)
    d.setPatchStride(4)
    d.setGradientDescentIterations(25)
    d.setVariationalRefinementIterations(10)
    d.setVariationalRefinementAlpha(40.0)
    d.setUseSpatialPropagation(True)
    return d


def fields(frames, ref, smooth=6.0):
    """frames: {n: float BGR 0-1}, consecutive n.  Returns {n: HxWx2 float32 displacement to ref}."""
    ns = sorted(frames)
    h, w = frames[ref].shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    P = {n: prep(frames[n]) for n in ns}
    dis = _dis()

    def step(a, b):
        return cv2.GaussianBlur(dis.calc(P[a], P[b], None), (0, 0), smooth)

    def compose(f1, f2):
        f2w = cv2.remap(f2, xx + f1[..., 0], yy + f1[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return f1 + f2w

    out = {ref: np.zeros((h, w, 2), np.float32)}
    for n in [m for m in ns if m > ref]:
        out[n] = compose(step(n, n - 1), out[n - 1])
    for n in [m for m in reversed(ns) if m < ref]:
        out[n] = compose(step(n, n + 1), out[n + 1])
    # chaining adds up small errors; measure what is left directly against the reference and take it out
    for n in ns:
        if n == ref:
            continue
        for _ in range(2):
            moved = cv2.remap(P[ref], xx + out[n][..., 0], yy + out[n][..., 1], cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
            r = cv2.GaussianBlur(dis.calc(P[n], moved, None), (0, 0), smooth)
            out[n] = compose(r, out[n])
    return out


def warp(img, field, border=cv2.BORDER_CONSTANT):
    h, w = field.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(img, xx + field[..., 0], yy + field[..., 1], cv2.INTER_CUBIC, borderMode=border)


def regularize(field, reliable, sigma=140.0, step=8):
    """field: raw displacement (frame n -> ref); reliable: bool mask in frame-n pixels.
    Returns homography fitted to the reliable vectors + a smooth correction (Gaussian-weighted mean of the
    residual with sigma px, shrinking to zero where reliable data is sparse)."""
    h, w = field.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ys, xs = np.mgrid[0:h:step, 0:w:step]
    m = reliable[ys, xs]
    src = np.float32(np.c_[xs[m], ys[m]])
    dst = src + field[ys[m], xs[m]]
    Hm, inl = cv2.findHomography(src, dst, cv2.RANSAC, 2.0)
    pts = np.dstack([xx, yy]).reshape(1, -1, 2)
    hf = cv2.perspectiveTransform(pts, Hm).reshape(h, w, 2) - np.dstack([xx, yy])
    res = (field - hf) * reliable[..., None]
    wgt = reliable.astype(np.float32)
    small = (int(w / 8), int(h / 8))
    rs = cv2.GaussianBlur(cv2.resize(res, small, interpolation=cv2.INTER_AREA), (0, 0), sigma / 8)
    ws = cv2.GaussianBlur(cv2.resize(wgt, small, interpolation=cv2.INTER_AREA), (0, 0), sigma / 8)
    corr = rs / (ws[..., None] + 0.05)
    corr = cv2.resize(corr, (w, h), interpolation=cv2.INTER_CUBIC)
    return (hf + corr).astype(np.float32), Hm, float(inl.mean())


def guided(I, p, r, eps):
    """He et al. guided filter: smooth p while keeping the edges of guide I (both float32, single channel)"""
    k = (2 * r + 1, 2 * r + 1)
    mI, mp = cv2.boxFilter(I, -1, k), cv2.boxFilter(p, -1, k)
    cov = cv2.boxFilter(I * p, -1, k) - mI * mp
    var = cv2.boxFilter(I * I, -1, k) - mI * mI
    a = cov / (var + eps)
    b = mp - a * mI
    return cv2.boxFilter(a, -1, k) * I + cv2.boxFilter(b, -1, k)


def refine(raw, reliable, guide, fallback, r=20, eps=1e-3):
    """Keep the measured motion where it is trustworthy, layer edges included: the raw field is averaged only
    over reliable pixels with an edge-preserving (guided) filter on the panel image, so a cut between two
    panel pieces that move differently stays sharp; where reliable data is thin, fall back to the smooth
    regularised field.  raw/fallback: HxWx2; reliable: bool HxW; guide: uint8 or float grey of frame n."""
    G = guide.astype(np.float32) / 255.0 if guide.dtype == np.uint8 else guide.astype(np.float32)
    c = reliable.astype(np.float32)
    den = guided(G, c, r, eps)
    out = np.empty_like(raw)
    for k in range(2):
        out[..., k] = guided(G, raw[..., k] * c, r, eps) / np.maximum(den, 1e-3)
    dens = cv2.boxFilter(c, -1, (2 * r + 1, 2 * r + 1))
    t = np.clip((dens - 0.15) / 0.25, 0, 1)[..., None]
    out = np.where(np.isfinite(out), out, fallback)
    return (t * out + (1 - t) * fallback).astype(np.float32)
