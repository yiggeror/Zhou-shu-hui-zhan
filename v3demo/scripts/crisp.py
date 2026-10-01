"""Crisp base: one clean Astra drawing per frame, moved by the measured motion.
No lighting transfer from the original, no blur fallback, no multi-anchor ghosting."""
import sys
sys.path.insert(0, "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad/work")
import numpy as np, cv2
import basefrac as bf
from basefrac import asset, up_field, OXX, OYY, OW, OH

def render_crisp(tau):
    ui, u0, u1, a = bf.locate(tau)
    it0 = bf._items(u0, bf.cands_for(ui, u0))
    it1 = {it["k"]: it for it in bf._items(u1, bf.cands_for(ui, u1))} if (u1 is not None and a > 1e-3) else {}
    best = None
    for it in it0:
        w = it["w"]; o1 = it1.get(it["k"])
        if o1 is not None:
            w = (1 - a) * w + a * o1["w"]
        if best is None or w > best[0]:
            best = (w, it, o1)
    w, it, o1 = best
    fld = it["fld"] if o1 is None else (1 - a) * it["fld"] + a * o1["fld"]
    img, alpha, (mx, my) = asset(it["k"])
    F = up_field(fld)
    o = cv2.remap(img, OXX + F[..., 0] + mx, OYY + F[..., 1] + my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    conf = it["conf"] if o1 is None else (1 - a) * it["conf"] + a * o1["conf"]
    return np.clip(o / 255.0, 0, 1).astype(np.float32), it["k"], float(np.mean(conf))

def regularize(fld, sigma):
    """keep the big motion (similarity + smooth residual), drop local tearing"""
    h, w = fld.shape[:2]
    ys, xs = np.mgrid[10:h:20, 10:w:20]
    p = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
    q = p + fld[ys.ravel(), xs.ravel()]
    M, _ = cv2.estimateAffinePartial2D(p, q, method=cv2.LMEDS)
    YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
    rig = np.stack([M[0, 0] * XX + M[0, 1] * YY + M[0, 2] - XX, M[1, 0] * XX + M[1, 1] * YY + M[1, 2] - YY], -1).astype(np.float32)
    if sigma <= 0:
        return rig
    res = cv2.GaussianBlur(fld - rig, (0, 0), sigma)
    return rig + res

def render_crisp2(tau, sigma=12, mode="auto"):
    """mode: 'warp' local warp, 'smooth' similarity+smooth residual, 'auto' picks by confidence"""
    ui, u0, u1, a = bf.locate(tau)
    it0 = bf._items(u0, bf.cands_for(ui, u0))
    it1 = {it["k"]: it for it in bf._items(u1, bf.cands_for(ui, u1))} if (u1 is not None and a > 1e-3) else {}
    best = None
    for it in it0:
        w = it["w"]; o1 = it1.get(it["k"])
        if o1 is not None:
            w = (1 - a) * w + a * o1["w"]
        if best is None or w > best[0]:
            best = (w, it, o1)
    w, it, o1 = best
    fld = it["fld"] if o1 is None else (1 - a) * it["fld"] + a * o1["fld"]
    q = it["q"] if o1 is None else (1 - a) * it["q"] + a * o1["q"]
    s = sigma if mode == "smooth" else (0 if mode == "warp" else float(np.interp(q, [0.55, 0.8], [sigma * 2, 3])))
    if s > 0:
        fld = regularize(fld, s)
    img, alpha, (mx, my) = asset(it["k"])
    F = up_field(fld)
    o = cv2.remap(img, OXX + F[..., 0] + mx, OYY + F[..., 1] + my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return np.clip(o / 255.0, 0, 1).astype(np.float32), it["k"], float(q), fld
