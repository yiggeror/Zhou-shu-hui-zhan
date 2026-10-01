"""v5 demo: crisp base at the original's own timing (1x) + hit-stops and effects.

Every output frame shows the drawing the original shows at that moment (same cuts, same
holds, same camera); the only timing change is a 3-frame hit-stop on each landed blow.
Also writes a side-by-side comparison (new | original | v4) with the same hit-stops.
usage: fx5.py
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
sys.path.insert(0, S + "/pilot")
import numpy as np, cv2
from fx import (W, H, XX, YY, Noise, Particles, camera, shake, chroma, shockwave, bloom, speed_lines,
                lightning, draw_bolts, finish, to8, energy_mask, impact, grade)

FPS = 60; DT = 1.0 / FPS
ts = np.load(S + "/ts.npy"); fmap = np.load(S + "/work/fmap.npy")
units = json.load(open(S + "/work/units.json"))
u960 = np.load(S + "/work/u960.npy", mmap_mode="r")
SEGS = [(42, 50), (72, 79), (92, 104)]                    # unit index ranges (inclusive)
CYAN = np.float32([1.0, 0.92, 0.35]); RED = np.float32([0.28, 0.22, 1.0]); WHITE = np.float32([1, 1, 1])
ORANGE = np.float32([0.3, 0.65, 1.0])
HITS = {  # source time on the 96 s timeline -> colour of the blow
    35.40: "r", 35.95: "c", 36.40: "c", 36.83: "c", 36.93: "c", 37.03: "c", 37.22: "r",
    55.79: "r", 56.07: "r", 56.35: "r", 56.92: "w", 57.61: "r",
    69.96: "o", 71.08: "c", 73.14: "r", 74.29: "r", 75.01: "r",
}
HCOL = dict(r=RED, c=CYAN, w=WHITE, o=ORANGE)
HS = 3                                                    # hit-stop frames
# blows closer than 0.15 s to the previous one are a flurry: they get sparks and a ring, no stop
MINOR = set(h for a, h in zip(sorted(HITS), sorted(HITS)[1:]) if h - a < 0.15)

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3
def t_start(ui):
    return float(ts[units[ui]["start"]])
def t_end(ui):
    e = units[ui]["end"]; return float(ts[e]) if e < len(ts) else 96.0
def u_at(t):
    i = max(0, int(np.searchsorted(ts, t + 1e-6, side="right")) - 1); return int(fmap[i])
def unit_of_t(t):
    i = max(0, int(np.searchsorted(ts, t + 1e-6, side="right")) - 1)
    return next(j for j, x in enumerate(units) if x["start"] <= i < x["end"])

# ---- build the output timeline: (u, t96, unit, hit-frame index or -1, hit key)
timeline = []
for a, b in SEGS:
    t0, t1 = t_start(a), t_end(b)
    n0, n1 = int(np.ceil(t0 * FPS)), int(np.ceil(t1 * FPS))
    pending = sorted(h for h in HITS if t0 <= h < t1)
    for n in range(n0, n1):
        t = n / FPS
        while pending and pending[0] <= t:
            h = pending.pop(0)
            for k in range(1 if h in MINOR else HS):
                timeline.append((u_at(t), t, unit_of_t(t), k if h not in MINOR else 2, h))
        timeline.append((u_at(t), t, unit_of_t(t), -1, None))
    timeline += [(None, None, None, -1, None)] * int(0.35 * FPS)      # black gap between segments
print("output frames", len(timeline), "%.2fs" % (len(timeline) / FPS))

OUT = HERE + "/out"; CMP = HERE + "/cmp"
os.makedirs(OUT, exist_ok=True); os.makedirs(CMP, exist_ok=True)
NX, NY = Noise(41), Noise(42)
rng = np.random.default_rng(3)
embers, sparks = Particles(), Particles()
trailE = None; last_unit = None; hit_state = {}; cut_n = -99
_cache = {}
DISP = {int(k): v for k, v in json.load(open(HERE + "/display.json")).items()}
def base(u):
    """the drawing shown for unique frame u: itself, a held neighbour of the same shot when this
    frame's pose is not covered by any drawing, or a camera-only move of the best drawing"""
    kind, src = DISP.get(u, ["self", u])
    fn = f"{HERE}/frames_rigid/u{src:05d}.jpg" if kind == "rigid" else f"{HERE}/frames/u{src:05d}.jpg"
    if fn not in _cache:
        if len(_cache) > 8: _cache.pop(next(iter(_cache)))
        _cache[fn] = cv2.imread(fn).astype(np.float32) / 255
    return _cache[fn]
def centroid(m):
    s = float(m.sum()); return None if s < 80 else (float((m * XX).sum() / s), float((m * YY).sum() / s))

for n, (u, t, ui, hk, hkey) in enumerate(timeline):
    tout = n * DT
    if u is None:
        out = np.zeros((H, W, 3), np.float32)
        embers.step(DT, 0.9, (0, -40)); sparks.step(DT, 0.9, (0, 100))
        trailE = None; last_unit = None
        cv2.imwrite(f"{OUT}/f{n:04d}.jpg", to8(out), [cv2.IMWRITE_JPEG_QUALITY, 95])
        cv2.imwrite(f"{CMP}/f{n:04d}.jpg", np.zeros((1080, 1920, 3), np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
        continue
    img = base(u).copy()
    if ui != last_unit:
        if last_unit is not None: cut_n = n
        trailE = None; embers = Particles(); last_unit = ui
    mc, mr = energy_mask(img, "c"), energy_mask(img, "r")
    E = np.maximum(mc, mr); ef = float(E.mean())
    extra = np.zeros((H, W, 3), np.float32)
    zoom, sh, chrom, bl = 1.0, (0.0, 0.0), 0.0, 1.0
    # living energy: flames keep flowing even while a drawing is held
    if 0.001 < ef < 0.25:
        m = cv2.GaussianBlur(cv2.dilate(E, np.ones((21, 21), np.uint8)), (0, 0), 10)
        dx = NX.field(tout * 1.4, (0, -1), 110) * 6 * m; dy = (NY.field(tout * 1.4 + 3.1, (0, -1), 110) - 0.8) * 6 * m
        img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out = grade(img, sat=1.08)
    out = np.clip((out - 0.5) * 1.05 + 0.5, 0, None)
    energy = img * E[..., None] * float(ef < 0.25)
    trailE = energy * 0.6 if trailE is None else trailE * 0.78 + energy * 0.4
    out = out + np.maximum(trailE - energy * 1.5, 0) * 0.55              # afterimage of the moving fist
    out = out + cv2.GaussianBlur(energy, (0, 0), 24) * 0.25 * max(0.0, 1 - ef * 4)   # energy lights its surroundings
    if 0.001 < ef < 0.25 and hk < 0:
        pts_w = cv2.resize(E ** 2, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
        if pts_w.sum() > 0:
            k = int(min(60, 4000 * ef)); idx = rng.choice(len(pts_w), k, p=pts_w / pts_w.sum()); ys, xs = np.divmod(idx, 240)
            p = (np.stack([xs, ys], 1) * 8 + rng.uniform(0, 8, (k, 2))).astype(np.float32)
            cols = np.clip(img[np.clip(p[:, 1].astype(int), 0, H - 1), np.clip(p[:, 0].astype(int), 0, W - 1)] * 1.3, 0, 1.6)
            a = rng.normal(-np.pi / 2, 0.8, k); sp = rng.uniform(80, 300, k)
            embers.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cols, rng.uniform(0.3, 0.8, k), rng.uniform(0.8, 1.6, k))
    # ---- hits: hit-stop frames, then the blow's aftermath in real time
    if hkey is not None:
        col = HCOL[HITS[hkey]]
        if hkey not in hit_state:
            m = mc if HITS[hkey] == "c" else (mr if HITS[hkey] == "r" else np.maximum(E, cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY) ** 4))
            c = centroid(m) or (W / 2, H / 2)
            hit_state[hkey] = dict(xy=c, n=n)
            m_ = 700 if hkey in MINOR else 2500; a = rng.uniform(0, 2 * np.pi, m_); sp = rng.uniform(400, 2400, m_)
            cc = np.where(rng.random((m_, 1)) < 0.2, WHITE[None] * 1.2, col[None] * rng.uniform(0.7, 1.3, (m_, 1)))
            r0 = rng.uniform(20, 90, (m_, 1))
            sparks.emit(np.float32(c)[None] + np.stack([np.cos(a), np.sin(a)], 1) * r0, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.2, 0.8, m_), rng.uniform(0.9, 2.2, m_))
        if hk == 0:
            out = out * 0.2 + 0.95
        elif hk == 1:
            two = impact(out, "bw", True, 0.42)
            out = two * (col if HITS[hkey] != "w" else np.float32([0.9, 0.9, 0.95])) + (1 - two) * np.float32([0.03, 0.0, 0.05])
        sh = shake(tout, 22, 3)
    for hkey2, st in hit_state.items():
        dt = (n - st["n"]) * DT
        if dt > 0.7:
            continue
        col = HCOL[HITS[hkey2]]; c = st["xy"]
        out, ring = shockwave(out, c[0], c[1], 1800 * eout(dt / 0.55), 80, 34 * (1 - ease(dt / 0.55)))
        extra += ring * col * 1.4 * (1 - ease(dt / 0.55))
        if dt < 0.22:
            extra += speed_lines(c[0], c[1], tout, n=130, inner=220, color=tuple(float(v) for v in (WHITE * 0.6 + col * 0.4))) * 0.7 * (1 - dt / 0.22)
        if dt < 0.3 and n % 2 == 0:
            for j in range(3):
                a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 650)
                extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), n * 7 + j), tuple(float(v) for v in col), 2, 9) * (1 - dt / 0.3)
        if hkey is None:
            sh = shake(tout, 18 * (1 - ease(dt / 0.35)), 4)
        zoom *= 1 + 0.05 * (1 - eout(dt / 0.3))
        chrom = max(chrom, 0.012 * (1 - ease(dt / 0.35))); bl += (0.25 if hkey2 in MINOR else 0.5) * (1 - ease(dt / 0.35))
    # ---- hard-cut accent: one soft flash frame + brief colour split
    kc = n - cut_n
    if 0 <= kc < 2 and hkey is None:
        out = out + (0.18 if kc == 0 else 0.06); chrom = max(chrom, 0.008 * (1 - kc / 2))
    embers.step(DT, 0.95, (0, -60)); sparks.step(DT, 0.955, (0, 140))
    if len(embers.p): extra += embers.render(glow=3.5, gain=1.1)
    if len(sparks.p): extra += sparks.render(glow=4.0, gain=0.75)
    out = out + extra
    if zoom != 1.0 or sh != (0.0, 0.0):
        out = camera(out, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
    if chrom > 0:
        out = chroma(out, W / 2, H / 2, chrom * 0.5)
    out = bloom(out, 0.85, 0.4 * min(bl, 1.7))
    out = finish(out, grain=0.01, vignette=0.3, t=tout)
    o8 = to8(out)
    cv2.imwrite(f"{OUT}/f{n:04d}.jpg", o8, [cv2.IMWRITE_JPEG_QUALITY, 95])
    # ---- comparison frame: new (large) | original | v4
    cv = np.zeros((1080, 1920, 3), np.uint8)
    cv[180:900, 0:1280] = cv2.resize(o8, (1280, 720), interpolation=cv2.INTER_AREA)
    cv[180:540, 1280:1920] = cv2.resize(np.ascontiguousarray(u960[u]), (640, 360), interpolation=cv2.INTER_AREA)
    v4 = cv2.imread(f"{S}/render_v4/u{u:05d}.jpg")
    cv[540:900, 1280:1920] = cv2.resize(v4, (640, 360), interpolation=cv2.INTER_AREA)
    for txt, x, y in (("NEW (v5)", 12, 168), ("ORIGINAL (reference only)", 1292, 168), ("v4 (previous)", 1292, 930)):
        cv2.putText(cv, txt, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (230, 230, 230), 2, cv2.LINE_AA)
    cv2.putText(cv, f"t96 {t:6.2f}s" + ("  HIT-STOP" if hk >= 0 else ""), (12, 960), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2, cv2.LINE_AA)
    cv2.imwrite(f"{CMP}/f{n:04d}.jpg", cv, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if n % 60 == 0:
        print(n, round(t, 2), flush=True)
print("done", len(timeline))
