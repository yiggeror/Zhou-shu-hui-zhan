"""Crisp base at every 60 fps output frame (sub-frame interpolation between the original's
drawings), so fast motion -- the flying red orb, whip pans -- is smooth instead of stepping.

Per output frame n (time n/60 on the 96 s timeline) the on-screen drawing u0 and the next one
u1 of the same shot are found; the same clean drawing is moved by the motion field interpolated
between them (lighting interpolated too). Frames whose pose no drawing covers are held on the
nearest clear drawing (only where the original is sharp -- motion-blurred flight frames are
rendered moving, with the original's own directional blur).
usage: crisp60.py WORKER NWORKERS
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np, cv2
import crisp5 as c5
from crisp5 import bf, stage2, pipe, units, frame, guarded, warp_asset, light, velocity, streak, SHARP, P, OW, OH, smoothstep
from stage2 import unit_us

FPS = 60
OUT = HERE + "/frames60"; os.makedirs(OUT, exist_ok=True)
SEGS = [(42, 50), (72, 79), (92, 104)]
DISP = {int(k): v for k, v in json.load(open(HERE + "/display.json")).items()}
_items = {}
def items(ui, u):
    if u not in _items:
        if len(_items) > 6: _items.pop(next(iter(_items)))
        _items[u] = sorted(bf._items(u, bf.cands_for(ui, u)), key=lambda it: -it["w"])
    return _items[u]

YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
def whip(img, k, dx, dy, n=12):
    """designed whip: directional smear (+ slight push) along the original's own whip direction"""
    L = float(np.hypot(dx, dy))
    if L < 40:                                               # no clear direction: radial push instead
        acc = np.zeros(img.shape, np.float32)
        for i in range(n):
            s = 1 + 0.25 * k * i / (n - 1)
            M = cv2.getRotationMatrix2D((OW / 2, OH / 2), 0, s)
            acc += cv2.warpAffine(img, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
        return np.clip(acc / n, 0, 255).astype(np.uint8)
    ux, uy = dx / L, dy / L
    span = min(L * 2.0, 420) * k
    acc = np.zeros(img.shape, np.float32)
    for i in range(n):
        f = (i / (n - 1) - 0.5) * span
        acc += cv2.warpAffine(img, np.float32([[1, 0, ux * f], [0, 1, uy * f]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
    return np.clip(acc / n, 0, 255).astype(np.uint8)

def static(u, frac=0.0):
    v = DISP.get(u, ["self", u])
    if v[0] == "whip":
        _, ref, k, dx, dy = v
        img = cv2.imread(f"{HERE}/frames/u{ref:05d}.jpg").astype(np.float32)
        return whip(img, k, dx, dy)
    d = "frames_rigid" if v[0] == "rigid" else "frames"
    return cv2.imread(f"{HERE}/{d}/u{v[1]:05d}.jpg")

V4 = os.path.dirname(HERE) + "/render_v4"
MOT = np.load(os.path.dirname(HERE) + "/v3/coverage.npy")[:, 3]
def edge_energy(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.resize(g, (960, 540), interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 0.8), cv2.CV_32F)), (0, 0), 10)

def hybrid(crisp, u):
    """keep the original's own motion blur: where the original is smeared but the clean drawing
    still has lines (fast motion, whips), show the v4 rendering of that spot (which reproduces the
    original's blur from the drawing); everywhere the original is sharp, show the crisp drawing"""
    if DISP.get(u, ["self"])[0] == "whip":
        return cv2.imread(f"{V4}/u{u:05d}.jpg"), 1.0
    # only frames where the whole original is motion-blurred (fast flight / whip pans):
    # a sharp or slow original never gets the v4 look (that is where v4's blotches came from)
    if not (SHARP[u] < 11 and MOT[u] > 15):
        return crisp, 0.0
    # relative test: the original has much less detail than the clean drawing at the same spot
    # (= the original is motion-blurred there); absolute levels differ too much between shots
    es = cv2.GaussianBlur(edge_energy(frame(u)), (0, 0), 8); ec = cv2.GaussianBlur(edge_energy(crisp), (0, 0), 8)
    w = (1 - smoothstep(0.15, 0.35, es / (ec + 0.3))) * smoothstep(1.5, 4.0, ec)
    w = cv2.GaussianBlur(w.astype(np.float32), (0, 0), 6)
    if float(w.max()) < 0.05:
        return crisp, 0.0
    w = cv2.resize(w, (OW, OH))[..., None]
    # the original's motion blur is re-created from the single clean drawing (directional streak
    # along the measured motion) -- never by mixing drawings, which shows double images
    ui = bf.locate(float(bf.TS[bf.UNIQ[u]]) + 1e-4)[0]
    p0 = items(ui, u)[0]
    blur = streak(crisp.astype(np.float32), velocity(p0["k"], u, p0["fld"]), P, gain=1.0, cap=90.0, soft=0)
    out = crisp.astype(np.float32) * (1 - w) + blur * w
    return np.clip(out, 0, 255).astype(np.uint8), float(w.mean())

def render_n(n):
    img, how = render_n0(n)
    u0 = bf.locate(n / FPS)[1]
    if DISP.get(u0, ["self"])[0] == "hold":                    # held clear drawing: never blur it
        return img, how
    img, wm = hybrid(img, u0)
    return img, f"{how} v4share={wm:.2f}"

def render_n0(n):
    tau = n / FPS
    ui, u0, u1, a = bf.locate(tau)
    if DISP.get(u0, ["self"])[0] != "self" or u1 is None or a < 0.03 or DISP.get(u1, ["self"])[0] != "self":
        return static(u0), "static"
    i0 = items(ui, u0); i1 = {it["k"]: it for it in items(ui, u1)}
    p0 = i0[0]
    # interpolate only if the same drawing also fits the next original frame; otherwise show
    # u0 until u1 arrives (exactly what the original does) instead of morphing toward a bad fit
    if p0["k"] not in i1 or i1[p0["k"]]["q"] < 0.5 or p0["q"] < 0.5:
        return static(u0), "static"
    use = [(p0, 1.0)]
    if len(i0) > 1 and i0[1]["w"] > 0.35 * p0["w"] and p0["q"] > 0.7 and i0[1]["q"] > 0.7:
        b = i0[1]["w"] / (p0["w"] + i0[1]["w"]); use = [(p0, 1 - b), (i0[1], b)]
    s0 = frame(u0).astype(np.float32); s1 = frame(u1).astype(np.float32)
    src = s0 * (1 - a) + s1 * a
    layers = []
    for it, wgt in use:
        o1 = i1.get(it["k"])
        if o1 is None:
            if layers: break
            return static(u0), "static"
        fld = guarded(it["fld"] * (1 - a) + o1["fld"] * a, it["conf"] * (1 - a) + o1["conf"] * a, src)
        o = warp_asset(it["k"], fld)
        A0, B0 = light(it["pred"], s0); A1, B1 = light(o1["pred"], s1)
        A = A0 * (1 - a) + A1 * a; B = B0 * (1 - a) + B1 * a
        layers.append((o * cv2.resize(A, (OW, OH)) + cv2.resize(B, (OW, OH)), wgt))
    out = c5.combine(layers)
    if SHARP[u0] < 8 and p0["q"] < 0.65:                     # the original is a whip-blur frame here
        out = streak(out, velocity(p0["k"], u0, p0["fld"]), P, gain=0.8, cap=70.0, soft=0)
    return np.clip(out, 0, 255).astype(np.uint8), "interp"

if __name__ == "__main__":
    wk, nw = int(sys.argv[1]), int(sys.argv[2])
    ns = []
    for a_, b_ in SEGS:
        t0 = float(c5.bf.TS[units[a_]["start"]]); e = units[b_]["end"]
        t1 = float(c5.bf.TS[e]) if e < len(c5.bf.TS) else 96.0
        ns += list(range(int(np.ceil(t0 * FPS)), int(np.ceil(t1 * FPS))))
    chunk = (len(ns) + nw - 1) // nw                            # contiguous blocks: consecutive frames share work
    for n in ns[wk * chunk:(wk + 1) * chunk]:
        fn = f"{OUT}/n{n:05d}.jpg"
        if os.path.exists(fn):
            continue
        ui = bf.locate(n / FPS)[0]
        keep = {k for j in (ui - 1, ui, ui + 1) if 0 <= j < len(units) for k, _ in units[j]["anchors"]}
        for cache in (stage2._chain_cache, pipe._asset_cache):
            for k in [k for k in cache if k not in keep]:
                del cache[k]
        img, how = render_n(n)
        cv2.imwrite(fn, img, [cv2.IMWRITE_JPEG_QUALITY, 96])
        if n % 30 == 0:
            print(n, how, flush=True)
    print("done", wk)
