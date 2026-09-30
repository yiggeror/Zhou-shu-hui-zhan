"""Stage 2: render every unique source frame from cached motion chains.

detail  = registered clean asset(s) warped along the measured motion, with
          local lighting transfer (flashes, glows, colour shifts)
fallback= soft low-pass rendition used only where no asset explains the frame
out     = C * detail + (1 - C) * fallback     (C = per-pixel confidence)
"""
import sys, json, os, time
import numpy as np, cv2
from pipe import *

units = json.load(open(S + "/work/units.json"))
OUT = S + "/render"
os.makedirs(OUT, exist_ok=True)
PARAM = json.load(open(S + "/work/params.json")) if os.path.exists(S + "/work/params.json") else {}

_chain_cache = {}
def load_chain(k):
    if k not in _chain_cache:
        z = np.load(f"{S}/chains/{k}.npz")
        us = z["us"].tolist()
        _chain_cache[k] = dict(idx={u: i for i, u in enumerate(us)}, fl=z["fl"], cf=z["cf"], sc=z["sc"], ua=int(z["ua"]))
    return _chain_cache[k]

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def unit_us(un):
    a = int(FMAP[un["start"]]); b = int(FMAP[un["end"] - 1])
    if UNIQ[a] < un["start"]:
        a += 1
    return list(range(a, b + 1))

def fill_box(x):
    """values inside the excluded box are unmeasured: interpolate from around it"""
    w = WMW
    f = cv2.GaussianBlur(x * w, (0, 0), 4) / (cv2.GaussianBlur(w, (0, 0), 4) + 1e-4)
    return x * w + f * (1 - w)

def fallback(src, sigma):
    w = WMW
    num = cv2.GaussianBlur(src * w[..., None], (0, 0), sigma)
    den = cv2.GaussianBlur(w, (0, 0), sigma)[..., None]
    # deep inside the excluded box: use a wide normalized blur instead
    num2 = cv2.GaussianBlur(src * w[..., None], (0, 0), 24)
    den2 = cv2.GaussianBlur(w, (0, 0), 24)[..., None] + 1e-4
    t = np.clip(den / 0.5, 0, 1)
    return (num / (den + 1e-4)) * t + (num2 / den2) * (1 - t)

def render_frame(u, cands, p):
    """cands: list of (key, temporal_weight)"""
    src = frame(u).astype(np.float32)
    items = []
    for k, tw in cands:
        if not os.path.exists(f"{S}/chains/{k}.npz"):
            continue
        ch = load_chain(k)
        if u not in ch["idx"]:
            continue
        i = ch["idx"][u]
        fld = ch["fl"][i].astype(np.float32)
        conf = ch["cf"][i].astype(np.float32) / 255.0
        if fld.shape[0] != H:   # chains stored at half flow resolution
            fld = cv2.resize(fld, (W, H), interpolation=cv2.INTER_LINEAR) * (W / fld.shape[1])
            conf = cv2.resize(conf, (W, H), interpolation=cv2.INTER_LINEAR)
        # confidence re-measured here with the exact exclusion mask:
        # how well the motion-compensated anchor frame explains this frame
        pr = warp(frame(ch["ua"]), fld)
        g = np.abs(gray(frame(u)).astype(np.float32) - gray(pr).astype(np.float32)) * WMW
        conf = fill_box(np.exp(-cv2.blur(g, (9, 9)) / 25.0).astype(np.float32))
        q = float((conf * WMW).sum() / WMW.sum())
        items.append((k, tw, fld, conf, q, ch["ua"]))
    # frame-level weights
    own_best = max([it[4] for it in items if it[1] > 0] + [0.0])
    ws = []
    for k, tw, fld, conf, q, ua in items:
        if tw < 0:   # neighbour-unit anchor: only if clearly better
            tw = 1.0 if q > own_best + p["nb_margin"] else 0.0
        ws.append(tw * max(q - 0.15, 0.02) ** 3)
    ws = np.array(ws); ws = ws / (ws.sum() + 1e-9)
    preds = {}
    def pred_of(j):
        if j not in preds:
            preds[j] = warp(frame(items[j][5]), items[j][2]).astype(np.float32)
        return preds[j]

    # ---- dissolve detection: src ~ a*pred_nb + (1-a)*pred_own ----
    mix = None
    own_idx = [j for j, it in enumerate(items) if it[1] > 0]
    nb_idx = [j for j, it in enumerate(items) if it[1] < 0]
    if p["dissolve"] and own_idx and nb_idx:
        jo = max(own_idx, key=lambda j: ws[j])
        jn = max(nb_idx, key=lambda j: items[j][4])
        def small(x):
            return cv2.resize(cv2.GaussianBlur(x, (0, 0), 2), (240, 135), interpolation=cv2.INTER_AREA)
        wm = cv2.resize(WMW, (240, 135)).ravel()
        s = small(src).reshape(-1, 3); po = small(pred_of(jo)).reshape(-1, 3); pn = small(pred_of(jn)).reshape(-1, 3)
        d = (pn - po)
        a = float(((s - po) * d * wm[:, None]).sum() / ((d * d * wm[:, None]).sum() + 1e-6))
        a = float(np.clip(a, 0, 1))
        rm = float((np.abs(s - (a * pn + (1 - a) * po)) * wm[:, None]).mean())
        ro = float((np.abs(s - po) * wm[:, None]).mean()); rn = float((np.abs(s - pn) * wm[:, None]).mean())
        if 0.06 < a < 0.94 and rm < p["dis_ratio"] * min(ro, rn):
            mix = (jo, jn, a)
            ws = np.zeros(len(items)); ws[jo] = 1 - a; ws[jn] = a
            mixpred = a * pred_of(jn) + (1 - a) * pred_of(jo)
            resid_mix = src - mixpred
            g = np.abs(gray(np.clip(src, 0, 255).astype(np.uint8)).astype(np.float32) -
                       gray(np.clip(mixpred, 0, 255).astype(np.uint8)).astype(np.float32)) * WMW
            cmix = fill_box(np.exp(-cv2.blur(g, (9, 9)) / 25.0))

    det = np.zeros((OH, OW, 3), np.float32); dw = np.zeros((OH, OW), np.float32)
    Cacc = np.zeros((H, W), np.float32)
    for j, ((k, tw, fld, conf, q, ua), w) in enumerate(zip(items, ws)):
        if w < 1e-3:
            continue
        img, alpha, (mx, my) = asset(k)
        F = up_field(fld)
        mx_ = OXX + F[..., 0] + mx; my_ = OYY + F[..., 1] + my
        o = cv2.remap(img, mx_, my_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        al = cv2.remap(alpha, mx_, my_, cv2.INTER_LINEAR, borderValue=0)
        pred = pred_of(j)
        target = src
        if mix is not None:
            target = pred + resid_mix      # this layer's share of the dissolve
            conf = cmix
        A, B = local_linear(pred, target, r=p["ll_r"], eps=p["ll_eps"])
        A = cv2.resize(A, (OW, OH)); B = cv2.resize(B, (OW, OH))
        o = o * A + B
        cs = cv2.GaussianBlur(conf, (0, 0), 4)
        c = smoothstep(p["c_lo"], p["c_hi"], cs)
        Cacc += w * c * cv2.resize(al, (W, H))
        det += o * (w * al)[..., None]; dw += w * al
    det = det / (dw[..., None] + 1e-6)
    C = cv2.resize(np.clip(Cacc, 0, 1), (OW, OH))
    fb = cv2.resize(fallback(src, p["fb_sigma"]), (OW, OH), interpolation=cv2.INTER_CUBIC)
    has = (dw > 1e-3).astype(np.float32)
    C = C * has
    out = det * C[..., None] + fb * (1 - C[..., None])
    return np.clip(out, 0, 255).astype(np.uint8), dict(q=[round(it[4], 2) for it in items], w=[round(float(x), 2) for x in ws], C=round(float(C.mean()), 3),
                                                       mix=None if mix is None else round(mix[2], 2))

DEF = dict(nb_margin=0.12, ll_r=20, ll_eps=60.0, c_lo=0.3, c_hi=0.7, fb_sigma=3.0, dissolve=True, dis_ratio=0.7)

def render_unit_idx(i):
    un = units[i]
    p = dict(DEF); p.update(PARAM.get(un["id"], {}))
    own = [k for k, _ in un["anchors"]]
    own_u = [int(FMAP[f]) for _, f in un["anchors"]]
    nbs = []
    for j in (i - 1, i + 1):
        if 0 <= j < len(units):
            nbs += [k for k, _ in units[j]["anchors"]]
    # keep memory bounded: drop cached assets/chains this unit does not use
    import pipe
    keep = set(own) | set(nbs)
    for cache in (_chain_cache, pipe._asset_cache):
        for k in [k for k in cache if k not in keep]:
            del cache[k]
    log = {}
    for u in unit_us(un):
        cands = [(k, anchor_weight(u, own_u, n)) for n, k in enumerate(own)] + [(k, -1) for k in nbs]
        img, info = render_frame(u, cands, p)
        cv2.imwrite(f"{OUT}/u{u:05d}.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        log[u] = info
    json.dump({str(k): v for k, v in log.items()}, open(f"{OUT}/log_{un['id']}.json", "w"))
    return log

if __name__ == "__main__":
    for i in map(int, sys.argv[1:]):
        t = time.time()
        lg = render_unit_idx(i)
        print(units[i]["id"], len(lg), round(time.time() - t, 1), "C", round(np.mean([v["C"] for v in lg.values()]), 2), flush=True)
