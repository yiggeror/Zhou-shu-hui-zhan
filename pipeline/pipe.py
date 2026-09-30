"""Motion-transfer renderer.

For every shot unit: chain dense optical flow on the (watermark-masked) source
video outward from each anchor frame, then warp the registered clean generated
image along that motion, transfer low-frequency lighting, and blend anchors.
Output frames are 1920x1080 (active 16:9 picture).
"""
import cv2, numpy as np, json, os, sys
cv2.setNumThreads(int(os.environ.get("CVT", "1")))

S = os.environ.get("SCR", "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad")
P = S + "/src/Opus_Animation_Reference_Pack/"
W, H = 960, 540          # flow resolution
OW, OH = 1920, 1080      # output resolution
MARGIN = 0.5             # canvas margin (fraction of frame) around generated asset

U = np.load(S + "/work/u960.npy", mmap_mode="r")
FMAP = np.load(S + "/work/fmap.npy")
UNIQ = np.load(S + "/work/uniq.npy")
REG = json.load(open(S + "/work/reg.json"))

# watermark box (flow-resolution coords) -> excluded from measurement
if os.environ.get("WM_BOX") or not os.path.exists(S + "/work/wm_glyph.npy"):
    WM = np.zeros((H, W), np.float32)
    WM[358:420, 222:452] = 1
    WMW = 1.0 - cv2.GaussianBlur(WM, (0, 0), 3)
else:
    # exact glyph strokes (+ outline) of the overlay text, from temporal statistics
    WM = cv2.dilate(np.load(S + "/work/wm_glyph.npy").astype(np.uint8),
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))).astype(np.float32)
    WMW = np.clip(1.0 - cv2.GaussianBlur(WM, (0, 0), 1.0) * 1.5, 0, 1)

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
OYY, OXX = np.mgrid[0:OH, 0:OW].astype(np.float32)

_dis = None
def dis():
    global _dis
    if _dis is None:
        d = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        d.setFinestScale(1)
        d.setPatchSize(12)
        d.setPatchStride(4)
        d.setVariationalRefinementIterations(8)
        d.setVariationalRefinementAlpha(30.0)
        _dis = d
    return _dis

def frame(u):
    return np.ascontiguousarray(U[u])

def gray(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

def flow(a, b):
    """flow such that a(p) ~ b(p + f(p))"""
    f = dis().calc(a, b, None)
    return fill_wm(f)

def fill_wm(f):
    # replace flow in watermark box by normalized-convolution interpolation
    wgt = WMW
    num = cv2.GaussianBlur(f * wgt[..., None], (0, 0), 14)
    den = cv2.GaussianBlur(wgt, (0, 0), 14)[..., None] + 1e-4
    fi = num / den
    return f * wgt[..., None] + fi * (1 - wgt[..., None])

def warp(img, f, border=cv2.BORDER_REPLICATE):
    return cv2.remap(img, XX + f[..., 0], YY + f[..., 1], cv2.INTER_LINEAR, borderMode=border)

def compose(f_ab, f_bc):
    """a->b then b->c  => a->c"""
    return f_ab + warp(f_bc, f_ab)

def resid(a_gray, b_gray):
    r = np.abs(a_gray.astype(np.float32) - b_gray.astype(np.float32)) * WMW
    return cv2.blur(r, (9, 9))

def chain(ua, us):
    """fields[u] : flow from frame u to anchor frame ua (u in us). returns dict u->(field, conf)"""
    out = {}
    ga = gray(frame(ua))
    out[ua] = (np.zeros((H, W, 2), np.float32), np.ones((H, W), np.float32), 0.0)
    for direction in (1, -1):
        seq = [u for u in (us if direction == 1 else us[::-1]) if (u - ua) * direction > 0]
        done = [ua]
        for u in seq:
            gu = gray(frame(u))
            best = None
            # try previous frames (skip-links over flashes / outliers)
            for prev in done[::-1][:4]:
                fp, _, _ = out[prev]
                f = flow(gu, gray(frame(prev)))
                init = compose(f, fp)
                wa = warp(ga, init)
                r = flow(gu, wa)                 # drift correction toward anchor
                fld = compose(r, init)
                res = resid(gu, warp(ga, fld))
                score = float(np.percentile(res, 70))
                if best is None or score < best[2]:
                    best = (fld, res, score)
                if score < 12:
                    break
            fld, res, score = best
            conf = np.exp(-res / 25.0).astype(np.float32)
            out[u] = (fld.astype(np.float32), conf, score)
            done.append(u)
    return out

def up_field(f):
    return cv2.resize(f, (OW, OH), interpolation=cv2.INTER_LINEAR) * 2.0

_asset_cache = {}
def asset(key):
    """registered generated asset on an enlarged canvas in output coords.
    returns (img float32 BGR, alpha float32, offset)"""
    if key in _asset_cache:
        return _asset_cache[key]
    r = REG[key]
    M = np.array(r["M"], np.float64)
    sr = S + f"/panels2x/{key}.png"
    if os.path.exists(sr):
        # 2x anime super-resolved panel (crisper linework)
        pan = cv2.imread(sr).astype(np.float32)
        M = M @ np.array([[0.5, 0, -0.25], [0, 0.5, -0.25], [0, 0, 1]])
    else:
        pan = cv2.imread(S + f"/panels/{key}.png").astype(np.float32)
    mx, my = int(OW * MARGIN), int(OH * MARGIN)
    T = np.array([[1, 0, mx], [0, 1, my]], np.float64)
    M2 = T @ np.vstack([M, [0, 0, 1]])
    cw, ch = OW + 2 * mx, OH + 2 * my
    scale = np.sqrt(abs(np.linalg.det(M[:, :2])))
    interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    img = cv2.warpAffine(pan, M2, (cw, ch), flags=interp, borderMode=cv2.BORDER_REFLECT)
    a = cv2.warpAffine(np.ones(pan.shape[:2], np.float32), M2, (cw, ch), flags=cv2.INTER_LINEAR, borderValue=0)
    a = cv2.erode(a, np.ones((3, 3), np.uint8))
    a = np.clip(cv2.GaussianBlur(a, (0, 0), 6) * 1.6 - 0.3, 0, 1)
    _asset_cache[key] = (img, a, (mx, my))
    return _asset_cache[key]

def local_linear(pred, src, r=20, eps=60.0):
    """per-channel local linear model src ~ a*pred + b (weighted box stats, watermark excluded)."""
    w = WMW
    def box(x):
        return cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1), normalize=False)
    N = box(w) + 1e-4
    A = np.empty_like(pred); B = np.empty_like(pred)
    for c in range(3):
        p = pred[..., c]; s = src[..., c]
        mp = box(p * w) / N; ms = box(s * w) / N
        cps = box(p * s * w) / N - mp * ms
        vp = box(p * p * w) / N - mp * mp
        a = cps / (vp + eps)
        a = np.clip(a, 0.3, 2.5)
        b = ms - a * mp
        A[..., c] = a; B[..., c] = b
    # windows (almost) entirely inside the excluded box carry no statistics:
    # fill them from the surrounding valid coefficients
    valid = (N > 0.3 * (2 * r + 1) ** 2).astype(np.float32)
    if valid.min() < 1:
        den = cv2.GaussianBlur(valid, (0, 0), 30)[..., None] + 1e-6
        A = np.where(valid[..., None] > 0, A, cv2.GaussianBlur(A * valid[..., None], (0, 0), 30) / den)
        B = np.where(valid[..., None] > 0, B, cv2.GaussianBlur(B * valid[..., None], (0, 0), 30) / den)
    A = cv2.blur(A, (2 * r + 1, 2 * r + 1)); B = cv2.blur(B, (2 * r + 1, 2 * r + 1))
    return A, B

def render_unit(unit, outdir, light=True, scale_out=1.0, log=True):
    us = sorted(set(FMAP[unit["start"]:unit["end"]].tolist()))
    us = [u for u in us if unit["start"] <= UNIQ[u] < unit["end"]] or us
    anchors = [(k, int(FMAP[f])) for k, f in unit["anchors"]]
    chains = {k: chain(ua, us) for k, ua in anchors}
    stats = {}
    for u in us:
        src = frame(u).astype(np.float32)
        acc = np.zeros((OH, OW, 3), np.float32); wacc = np.zeros((OH, OW), np.float32)
        info = []
        for k, ua in anchors:
            fld, conf, score = chains[k][u]
            img, alpha, (mx, my) = asset(k)
            F = up_field(fld)
            mx_ = OXX + F[..., 0] + mx; my_ = OYY + F[..., 1] + my
            o = cv2.remap(img, mx_, my_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            al = cv2.remap(alpha, mx_, my_, cv2.INTER_LINEAR, borderValue=0)
            if light:
                pred = warp(frame(ua), fld).astype(np.float32)
                A, B = local_linear(pred, src)
                A = cv2.resize(A, (OW, OH)); B = cv2.resize(B, (OW, OH))
                o = o * A + B
            # temporal weight
            if len(anchors) == 1:
                tw = 1.0
            else:
                uas = [x[1] for x in anchors]
                i = [x[0] for x in anchors].index(k)
                tw = anchor_weight(u, uas, i)
            fw = tw * (0.05 + float(np.mean(conf)))
            w = al * fw + 1e-6
            acc += o * w[..., None]; wacc += w
            info.append((k, round(score, 1), round(tw, 2)))
        out = acc / wacc[..., None]
        # fill anything uncovered by any asset with blurred neighborhood
        cov = np.clip(wacc / (wacc.max() + 1e-6) * 50, 0, 1)
        if cov.min() < 0.99:
            fillv = cv2.GaussianBlur(out, (0, 0), 25)
            out = out * cov[..., None] + fillv * (1 - cov[..., None])
        out = np.clip(out, 0, 255).astype(np.uint8)
        if scale_out != 1.0:
            out = cv2.resize(out, None, fx=scale_out, fy=scale_out, interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{outdir}/u{u:05d}.jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 96])
        stats[u] = info
        if log:
            print(unit["id"], u, UNIQ[u], info, flush=True)
    return stats

def anchor_weight(u, uas, i):
    order = np.argsort(uas)
    uas_s = [uas[j] for j in order]
    pos = list(order).index(i)
    if u <= uas_s[0]:
        return 1.0 if pos == 0 else 0.0
    if u >= uas_s[-1]:
        return 1.0 if pos == len(uas_s) - 1 else 0.0
    for j in range(len(uas_s) - 1):
        a, b = uas_s[j], uas_s[j + 1]
        if a <= u <= b:
            t = (u - a) / max(1, b - a)
            t = t * t * (3 - 2 * t)
            if pos == j: return 1 - t
            if pos == j + 1: return t
            return 0.0
    return 0.0
