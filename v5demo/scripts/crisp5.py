"""v5 base: the v4 motion (per-pixel follow of the source, 1x timing) rendered crisp.

Differences from v4 (stage2):
  * no blur fill: where the measured motion is unreliable the drawing is moved by a
    regularised (similarity + smooth residual) field instead of being replaced by a streak;
  * at most two drawings are mixed, and only when both fit the frame well (no ghosting);
  * lighting is transferred only at a coarse scale (flashes / exposure), so the
    original's blur never enters the frame;
  * source frames that are themselves whip-blur transitions get an intentional
    directional smear of the crisp drawing (like the original's own motion blur).
usage: crisp5.py WORKER NWORKERS UNIT_IDX...
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
sys.path.insert(0, S + "/work"); sys.path.insert(0, S + "/v3")
import numpy as np, cv2, json
import basefrac as bf
import stage2, pipe
from stage2 import smoothstep, velocity, streak, unit_us, units
from pipe import asset, up_field, OXX, OYY, OW, OH, W, H, frame, local_linear
from crisp import regularize

OUT = HERE + "/frames"; os.makedirs(OUT, exist_ok=True)
COV = np.load(S + "/v3/coverage.npy")            # q, C, sharp, mot, unit, t96, frame per unique drawing
SHARP = COV[:, 2]
P = dict(stage2.DEF)
REG_SIGMA = float(os.environ.get("REG_SIGMA", "0"))   # unreliable areas move rigidly (no waves)

def distortion(fld):
    """how much the local (non-rigid) part of the field stretches / shears the drawing"""
    r = fld - regularize(fld, 0)
    d = sum(np.abs(cv2.Sobel(r[..., c], cv2.CV_32F, dx, dy, ksize=3)) / 8.0 for c in (0, 1) for dx, dy in ((1, 0), (0, 1)))
    return cv2.GaussianBlur(d, (0, 0), 8)

def guarded(fld, conf, src):
    """field actually used: the measured one where it is reliable and does not tear the drawing,
    otherwise a rigid move with only a very smooth residual"""
    conf = cv2.GaussianBlur(conf, (0, 0), 6)
    g = cv2.cvtColor(src.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    sharp = cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 0.8), cv2.CV_32F)), (0, 0), 10)
    c = smoothstep(0.35, 0.75, conf) * smoothstep(1.5, 4.0, sharp) * (1 - smoothstep(0.12, 0.35, distortion(fld)))
    c = cv2.GaussianBlur(c.astype(np.float32), (0, 0), 6)[..., None]
    return fld * c + regularize(fld, REG_SIGMA) * (1 - c)

def warp_asset(k, fld):
    img, alpha, (mx, my) = asset(k)
    F = up_field(fld)
    return cv2.remap(img, OXX + F[..., 0] + mx, OYY + F[..., 1] + my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def light(pred, src):
    A, B = local_linear(pred, src, r=70, eps=400.0)              # coarse: flashes and exposure only
    return np.clip(cv2.GaussianBlur(A, (0, 0), 20), 0.6, 1.5), cv2.GaussianBlur(B, (0, 0), 20)

def layer(it, src):
    fld = guarded(it["fld"], it["conf"], src)
    img, alpha, (mx, my) = asset(it["k"])
    F = up_field(fld)
    o = cv2.remap(img, OXX + F[..., 0] + mx, OYY + F[..., 1] + my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    A, B = local_linear(it["pred"], src, r=70, eps=400.0)        # coarse: flashes and exposure only
    A = np.clip(cv2.GaussianBlur(A, (0, 0), 20), 0.6, 1.5); B = cv2.GaussianBlur(B, (0, 0), 20)
    o = o * cv2.resize(A, (OW, OH)) + cv2.resize(B, (OW, OH))
    return o, fld

def combine(layers):
    """mix two drawings only where they agree; where they disagree (fast motion, different
    poses) mixing would show a double image, so the stronger drawing is used alone"""
    if len(layers) == 1:
        return layers[0][0]
    (o0, w0), (o1, w1) = layers
    g0 = cv2.resize(cv2.cvtColor(np.clip(o0, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY), (480, 270)).astype(np.float32)
    g1 = cv2.resize(cv2.cvtColor(np.clip(o1, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY), (480, 270)).astype(np.float32)
    d = cv2.GaussianBlur(np.abs(g0 - g1), (0, 0), 6)
    agree = 1 - smoothstep(10.0, 25.0, d)                       # per-pixel: blend only where similar
    m = cv2.resize(agree * w1 / (w0 + w1), (OW, OH))[..., None]
    return o0 * (1 - m) + o1 * m

def render(ui, u, rigid=False):
    items = bf._items(u, bf.cands_for(ui, u))
    own = [it for it in items if it["tw"] >= 0]
    if rigid and own:                      # camera-only move of the best own drawing (no local warp)
        it = max(own, key=lambda it: it["q"])
        it = dict(it, fld=regularize(it["fld"], 0), conf=np.zeros_like(it["conf"]))
        o, _ = layer(it, frame(u).astype(np.float32))
        return np.clip(o, 0, 255).astype(np.uint8), dict(k=[it["k"]], q=round(float(it["q"]), 2), rigid=True)
    items = sorted(items, key=lambda it: -it["w"])
    src = frame(u).astype(np.float32)
    p0 = items[0]
    use = [(p0, 1.0)]
    if len(items) > 1:
        p1 = items[1]
        if p1["w"] > 0.35 * p0["w"] and p0["q"] > 0.7 and p1["q"] > 0.7:
            a = p1["w"] / (p0["w"] + p1["w"]); use = [(p0, 1 - a), (p1, a)]
    out = combine([(layer(it, src)[0], a) for it, a in use])
    # the original is itself a whip-blur frame here: smear the crisp drawing along the motion
    if SHARP[u] < 8 and p0["q"] < 0.65:
        vel = velocity(p0["k"], u, p0["fld"])
        out = streak(out, vel, P, gain=0.8, cap=70.0, soft=0)
    return np.clip(out, 0, 255).astype(np.uint8), dict(k=[it["k"] for it, _ in use], q=round(float(p0["q"]), 2))

if __name__ == "__main__":
    wk, nw = int(sys.argv[1]), int(sys.argv[2])
    RIGID = os.environ.get("RIGID") == "1"
    if RIGID:
        OUT = HERE + "/frames_rigid"; os.makedirs(OUT, exist_ok=True)
        jobs = [tuple(x) for x in json.load(open(HERE + "/rigid_jobs.json"))]
    else:
        uis = [int(x) for x in sys.argv[3:]]
        jobs = [(ui, u) for ui in uis for u in unit_us(units[ui])]
    log = {}
    for ui, u in jobs[wk::nw]:
        fn = f"{OUT}/u{u:05d}.jpg"
        if os.path.exists(fn):
            continue
        keep = {k for j in (ui - 1, ui, ui + 1) if 0 <= j < len(units) for k, _ in units[j]["anchors"]}
        for cache in (stage2._chain_cache, pipe._asset_cache):
            for k in [k for k in cache if k not in keep]:
                del cache[k]
        img, info = render(ui, u, rigid=RIGID)
        cv2.imwrite(fn, img, [cv2.IMWRITE_JPEG_QUALITY, 96])
        log[u] = info
        print(u, units[ui]["id"], info, flush=True)
    json.dump(log, open(f"{HERE}/log{'r' if RIGID else ''}_{wk}.json", "w"))
    print("done", wk)
