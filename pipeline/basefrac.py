"""Render the motion-transfer base layer at ANY source time tau (sub-frame).

Between two consecutive source frames of the same shot the anchor-relative
motion fields are interpolated, so slow motion stays continuous and crisp
instead of holding frames. Returns float BGR 0..1 at 1920x1080, the per-pixel
confidence map (1080p) and the image-space velocity field (flow res).
"""
import numpy as np, cv2, os, json
import stage2
from stage2 import load_chain, fill_box, smoothstep, velocity, streak, unit_us, units
from pipe import *

TS = np.load(S + "/ts.npy")

def locate(tau):
    """-> (unit index, u0, u1 or None, fraction)"""
    i = max(0, int(np.searchsorted(TS, tau, side="right")) - 1)
    u0 = int(FMAP[i])
    ui = next(j for j, un in enumerate(units) if un["start"] <= UNIQ[u0] < un["end"])
    u1 = u0 + 1
    if u1 >= len(UNIQ) or UNIQ[u1] >= units[ui]["end"]:
        return ui, u0, None, 0.0
    t0, t1 = TS[UNIQ[u0]], TS[UNIQ[u1]]
    return ui, u0, u1, float(np.clip((tau - t0) / max(t1 - t0, 1e-6), 0, 1))

def _field(ch, u):
    i = ch["idx"][u]
    f = ch["fl"][i].astype(np.float32)
    return cv2.resize(f, (W, H), interpolation=cv2.INTER_LINEAR) * (W / f.shape[1]) if f.shape[0] != H else f

def _items(u, cands):
    gs = gray(frame(u)).astype(np.float32)
    sw = cv2.GaussianBlur(np.abs(cv2.Sobel(gs, cv2.CV_32F, 1, 0)) + np.abs(cv2.Sobel(gs, cv2.CV_32F, 0, 1)), (0, 0), 6) * WMW
    flat = sw.sum() < 2.0 * WMW.sum()
    items = []
    for k, tw in cands:
        if not os.path.exists(f"{S}/chains/{k}.npz"):
            continue
        ch = load_chain(k)
        if u not in ch["idx"]:
            continue
        fld = _field(ch, u)
        pr = warp(frame(ch["ua"]), fld)
        g = np.abs(gs - gray(pr).astype(np.float32)) * WMW
        conf = fill_box(np.exp(-cv2.blur(g, (9, 9)) / 25.0).astype(np.float32))
        q = float((conf * WMW).sum() / WMW.sum()) if flat else float((conf * sw).sum() / sw.sum())
        items.append(dict(k=k, tw=tw, fld=fld, conf=conf, q=q, ua=ch["ua"], pred=pr.astype(np.float32)))
    nb = [j for j, it in enumerate(items) if it["tw"] < 0]
    best_nb = max(nb, key=lambda j: items[j]["q"]) if nb else None
    p = stage2.DEF
    ws = []
    for j, it in enumerate(items):
        prior = (p["lam_nb"] if (j == best_nb and not flat) else 0.0) if it["tw"] < 0 else max(it["tw"], 0.0) + p["lam_own"]
        ws.append(prior * max(it["q"] - 0.15, 0.02) ** 4)
    ws = np.array(ws); ws = ws / (ws.sum() + 1e-9)
    for it, w in zip(items, ws):
        it["w"] = float(w)
    return items

def cands_for(ui, u):
    un = units[ui]
    own = [k for k, _ in un["anchors"]]; own_u = [int(FMAP[f]) for _, f in un["anchors"]]
    nbs = [k for j in (ui - 1, ui + 1) if 0 <= j < len(units) for k, _ in units[j]["anchors"]]
    return [(k, anchor_weight(u, own_u, n)) for n, k in enumerate(own)] + [(k, -1) for k in nbs]

def render_at(tau, p=None):
    p = dict(stage2.DEF, **(p or {}))
    ui, u0, u1, a = locate(tau)
    it0 = _items(u0, cands_for(ui, u0))
    it1 = {it["k"]: it for it in _items(u1, cands_for(ui, u1))} if (u1 is not None and a > 1e-3) else {}
    src0 = frame(u0).astype(np.float32)
    src1 = frame(u1).astype(np.float32) if it1 else None
    det = np.zeros((OH, OW, 3), np.float32); fba = np.zeros((OH, OW, 3), np.float32)
    dw = np.zeros((OH, OW), np.float32); Cacc = np.zeros((H, W), np.float32); vacc = np.zeros((H, W, 2), np.float32)
    for it in it0:
        k = it["k"]; w = it["w"]
        o1 = it1.get(k)
        if o1 is not None:
            w = (1 - a) * w + a * o1["w"]
        if w < 1e-3:
            continue
        fld = it["fld"] if o1 is None else (1 - a) * it["fld"] + a * o1["fld"]
        conf = it["conf"] if o1 is None else (1 - a) * it["conf"] + a * o1["conf"]
        img, alpha, (mx, my) = asset(k)
        F = up_field(fld)
        mx_ = OXX + F[..., 0] + mx; my_ = OYY + F[..., 1] + my
        o = cv2.remap(img, mx_, my_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        al = cv2.remap(alpha, mx_, my_, cv2.INTER_LINEAR, borderValue=0)
        A, B = local_linear(it["pred"], src0, r=p["ll_r"], eps=p["ll_eps"])
        if o1 is not None:                       # lighting interpolated too (no popping flashes)
            A1, B1 = local_linear(o1["pred"], src1, r=p["ll_r"], eps=p["ll_eps"])
            A = (1 - a) * A + a * A1; B = (1 - a) * B + a * B1
        o = o * cv2.resize(A, (OW, OH)) + cv2.resize(B, (OW, OH))
        vel = velocity(k, u0, it["fld"])
        fbo = streak(o, vel, p)
        cs = cv2.GaussianBlur(conf, (0, 0), 4)
        c = smoothstep(p["c_lo"], p["c_hi"], cs)
        Cacc += w * c * cv2.resize(al, (W, H)); vacc += w * vel
        wa = w * (al + 1e-3)
        det += o * wa[..., None]; fba += fbo * wa[..., None]; dw += wa
    det /= dw[..., None] + 1e-9; fba /= dw[..., None] + 1e-9
    C = cv2.resize(np.clip(Cacc, 0, 1), (OW, OH))
    out = det * C[..., None] + fba * (1 - C[..., None])
    return np.clip(out / 255.0, 0, 1.5).astype(np.float32), C, vacc
