"""Full film, both versions: original timing (96 s, 60 fps) + 3-frame hit-stops on landed blows,
with the effects layer drawn on top of a base picture:
  MODE=A  crisp redrawn frames (Astra drawings moved by the measured motion, crisp60.render_n)
  MODE=B  the original, restored (vB/prepB.py)
Effects: living cursed-energy flames, afterimages, glow and embers on the moving energy; hits get a
white flash frame, a two-tone impact frame, shockwave, radial speed lines, lightning, sparks, shake
and a push-in; spinning orbs; rising embers / arcs / orb swirls at the big moments; soft cut flashes;
credit card at the end.  Work is split into chunks at shot boundaries; each chunk is piped straight
into its own video segment (no frames on disk), the segments are concatenated afterwards.
usage: fxall.py MODE WORKER NWORKERS
"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
MODE, WK, NW = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, S + "/pilot")
import numpy as np, cv2
from fx import (W, H, XX, YY, Noise, Particles, camera, shake, chroma, shockwave, bloom, speed_lines,
                lightning, draw_bolts, finish, to8, energy_mask, impact, grade)
if MODE == "A":
    sys.path.insert(0, S + "/v5")
    import crisp60, stage2, pipe
    from crisp60 import bf

FPS = 60; DT = 1.0 / FPS; NSRC = 5760
ts = np.load(S + "/ts.npy"); fmap = np.load(S + "/work/fmap.npy")
units = json.load(open(S + "/work/units.json"))
SEGDIR = f"{HERE}/seg{MODE}"; os.makedirs(SEGDIR, exist_ok=True)

C = dict(r=np.float32([0.28, 0.22, 1.0]), c=np.float32([1.0, 0.92, 0.35]), w=np.float32([1, 1, 1]),
         o=np.float32([0.3, 0.65, 1.0]), p=np.float32([1.0, 0.45, 0.95]), b=np.float32([1.0, 0.6, 0.25]))
WHITE = C["w"]
HITS = {  # 96 s timeline -> colour of the blow
    1.231: "w", 32.91: "p", 34.10: "p",
    35.40: "r", 35.95: "c", 36.40: "c", 36.83: "c", 36.93: "c", 37.03: "c", 37.22: "r",
    40.80: "w", 41.36: "r", 47.25: "w",
    55.79: "r", 56.07: "r", 56.35: "r", 56.92: "w", 57.61: "r",
    67.83: "c", 68.27: "c", 69.96: "o", 71.08: "c",
    73.14: "r", 74.29: "r", 75.01: "r", 78.69: "r", 80.85: "r", 82.99: "b", 89.63: "p", 92.10: "p",
}
HS = 3
MINOR = set(h for a, h in zip(sorted(HITS), sorted(HITS)[1:]) if h - a < 0.15)
EV = [e for e in json.load(open(S + "/full/events.json")) if e["kind"] in ("rise", "arcs", "orb", "pulse")]
SPIN = [(71.78, 74.05, "r", 1.0), (80.94, 83.38, "b", -1.0), (85.20, 86.35, "r", 1.0)]
CREDIT = "Original animation: NinjaristicNinja" + ("   |   redrawn remake + VFX" if MODE == "A" else "   |   VFX enhanced edit")

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3
def src_i(t):
    return max(0, int(np.searchsorted(ts, t + 1e-6, side="right")) - 1)
def u_at(t):
    return int(fmap[src_i(t)])
UNIT_OF_SRC = np.zeros(len(ts), np.int32)
for j, x in enumerate(units):
    UNIT_OF_SRC[x["start"]:x["end"]] = j
def unit_of_t(t):
    return int(UNIT_OF_SRC[src_i(t)])

# ---- timeline over the whole film, chunked at shot boundaries
timeline = []
pending = sorted(HITS)
for n in range(NSRC):
    t = n / FPS
    while pending and pending[0] <= t:
        h = pending.pop(0)
        for k in range(1 if h in MINOR else HS):
            timeline.append((n, t, k if h not in MINOR else 2, h))
    timeline.append((n, t, -1, None))
chunks = []; start = 0
for i in range(1, len(timeline) + 1):
    if i == len(timeline) or (unit_of_t(timeline[i][1]) != unit_of_t(timeline[i - 1][1]) and i - start >= 150):
        chunks.append((start, i)); start = i
loads = [0] * NW; mine = []
for ci in sorted(range(len(chunks)), key=lambda c: -(chunks[c][1] - chunks[c][0])):
    j = int(np.argmin(loads)); loads[j] += chunks[ci][1] - chunks[ci][0]
    if j == WK: mine.append(ci)
json.dump(dict(frames=len(timeline), chunks=chunks), open(f"{SEGDIR}/plan.json", "w"))

NX, NY = Noise(41), Noise(42)

def base(n, u):
    if MODE == "B":
        return cv2.imread(f"{HERE}/../vB/base/u{u:05d}.jpg").astype(np.float32) / 255
    ui = bf.locate(n / FPS)[0]
    _, u0, u1, _ = bf.locate(n / FPS)
    keep = {k for uu in (u0, u1) if uu is not None for k, _ in bf.cands_for(ui, uu)}
    for cache in (stage2._chain_cache, pipe._asset_cache):
        for k in [k for k in cache if k not in keep]:
            del cache[k]
    img, _ = crisp60.render_n(n)
    return img.astype(np.float32) / 255

def centroid(m):
    s = float(m.sum()); return None if s < 80 else (float((m * XX).sum() / s), float((m * YY).sum() / s))

def spin_orb(out, m, ang):
    """rotate the inside of the largest round energy blob (the orb) by ang"""
    b = (cv2.resize(m, (480, 270)) > 0.3).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(b, 8)
    if n < 2:
        return out
    j = 1 + int(np.argmax(st[1:, 4])); x, y, w, h, area = st[j]
    if area < 150 or area / (np.pi * (max(w, h) / 2) ** 2 + 1e-6) < 0.45:
        return out
    cx, cy = cen[j] * 4; r = max(w, h) * 4 * 0.55
    M = cv2.getRotationMatrix2D((float(cx), float(cy)), float(np.degrees(ang)), 1.0)
    rot = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    a = np.clip((r - d) / (0.25 * r), 0, 1)[..., None]
    return out * (1 - a) + rot * a

def credit(img, tout_left):
    a = float(ease((1.8 - tout_left) / 0.5) * ease(tout_left / 0.3))
    if a <= 0:
        return img
    lay = np.zeros((H, W, 3), np.uint8)
    (tw, th), _ = cv2.getTextSize(CREDIT, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
    cv2.putText(lay, CREDIT, ((W - tw) // 2, H - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (235, 235, 240), 2, cv2.LINE_AA)
    return img * (1 - 0.35 * a * (lay.max(-1, keepdims=True) > 0)) + lay.astype(np.float32) / 255 * a

def render_chunk(ci):
    a0, a1 = chunks[ci]
    fn = f"{SEGDIR}/c{ci:03d}.mp4"
    if os.environ.get("TEST_AT"):                              # quick check: a few frames around a time
        a0 = int(float(os.environ["TEST_AT"]) * FPS); a1 = a0 + int(os.environ.get("TEST_N", "20"))
        fn = f"{SEGDIR}/test_{a0}.mp4"
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        return
    rng = np.random.default_rng(100 + ci)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-threads", "1", "-crf", "13", "-tune", "animation",
                            "-pix_fmt", "yuv420p", "-g", "120", fn + ".tmp.mp4"], stdin=subprocess.PIPE)
    embers, sparks, swirl = Particles(), Particles(), Particles()
    trailE = None; last_unit = None; hit_state = {}; cut_n = -99; last_n = None; img0 = None
    total = len(timeline)
    for idx in range(a0, a1):
        n, t, hk, hkey = timeline[idx]
        tout = idx * DT
        u = u_at(t); ui = unit_of_t(t)
        if n != last_n:
            img0 = base(n, u); last_n = n
        img = img0.copy()
        if ui != last_unit:
            if last_unit is not None: cut_n = idx
            trailE = None; embers = Particles(); swirl = Particles(); last_unit = ui
        mc, mr = energy_mask(img, "c"), energy_mask(img, "r")
        E = np.maximum(mc, mr); ef = float(E.mean())
        extra = np.zeros((H, W, 3), np.float32)
        zoom, sh, chrom, bl = 1.0, (0.0, 0.0), 0.0, 1.0
        if 0.001 < ef < 0.25:                                     # cursed energy keeps burning
            m = cv2.GaussianBlur(cv2.dilate(E, np.ones((21, 21), np.uint8)), (0, 0), 10)
            dx = NX.field(tout * 1.4, (0, -1), 110) * 6 * m; dy = (NY.field(tout * 1.4 + 3.1, (0, -1), 110) - 0.8) * 6 * m
            img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        for t0, t1, ck, sg in SPIN:                               # orbs rotate
            if t0 <= t < t1:
                img = spin_orb(img, mr if ck == "r" else mc, sg * 5.0 * (t - t0))
        out = grade(img, sat=1.08)
        out = np.clip((out - 0.5) * 1.05 + 0.5, 0, None)
        energy = img * E[..., None] * float(ef < 0.25)
        trailE = energy * 0.6 if trailE is None else trailE * 0.78 + energy * 0.4
        out = out + np.maximum(trailE - energy * 1.5, 0) * 0.55
        out = out + cv2.GaussianBlur(energy, (0, 0), 24) * 0.25 * max(0.0, 1 - ef * 4)
        if 0.001 < ef < 0.25 and hk < 0:
            pw = cv2.resize(E ** 2, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
            if pw.sum() > 0:
                k = int(min(60, 4000 * ef)); sel = rng.choice(len(pw), k, p=pw / pw.sum()); ys, xs = np.divmod(sel, 240)
                p = (np.stack([xs, ys], 1) * 8 + rng.uniform(0, 8, (k, 2))).astype(np.float32)
                cols = np.clip(img[np.clip(p[:, 1].astype(int), 0, H - 1), np.clip(p[:, 0].astype(int), 0, W - 1)] * 1.3, 0, 1.6)
                a = rng.normal(-np.pi / 2, 0.8, k); sp = rng.uniform(80, 300, k)
                embers.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cols, rng.uniform(0.3, 0.8, k), rng.uniform(0.8, 1.6, k))
        # ---- continuous events
        for ev in EV:
            if not (ev["t0"] <= t < ev["t1"]):
                continue
            col = np.float32(ev.get("col", [1.0, 0.85, 1.0]))
            if ev["kind"] == "rise" and idx % 2 == 0:
                m_ = 30; p = np.stack([rng.uniform(0, W, m_), rng.uniform(H * 0.4, H, m_)], 1)
                embers.emit(p, np.stack([rng.normal(0, 30, m_), rng.uniform(-260, -90, m_)], 1), col[None] * rng.uniform(0.5, 1.2, (m_, 1)), rng.uniform(0.8, 1.8, m_), 1.2)
            elif ev["kind"] == "arcs" and idx % 2 == 0:
                c = centroid(E)
                if c is not None:
                    for j in range(int(ev.get("n", 2))):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 420)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 11 + j, depth=6, branches=2), tuple(float(v) for v in col), 1, 7) * 0.8
            elif ev["kind"] == "orb":
                c = centroid(E ** 2)
                if c is not None:
                    m_ = 160; a = rng.uniform(0, 2 * np.pi, m_); r0 = rng.uniform(40, 180, m_)
                    p = np.stack([c[0] + np.cos(a) * r0, c[1] + np.sin(a) * r0], 1)
                    tang = np.stack([-np.sin(a), np.cos(a)], 1) * rng.uniform(300, 800, (m_, 1)) * ev.get("spin", 1)
                    swirl.emit(p, tang, col[None] * rng.uniform(0.6, 1.3, (m_, 1)), rng.uniform(0.25, 0.6, m_), rng.uniform(0.8, 1.4, m_))
            elif ev["kind"] == "pulse":
                x = (t - ev["t0"]) / (ev["t1"] - ev["t0"]); d = np.sqrt((XX - W / 2) ** 2 + (YY - H / 2) ** 2)
                for k3 in range(3):
                    ph = (x * 3 + k3 / 3) % 1
                    extra += (np.exp(-((d - 120 - 900 * ph) / 6.0) ** 2) * (1 - ph) * 0.6)[..., None] * col
        # ---- hits
        if hkey is not None:
            col = C[HITS[hkey]]
            if hkey not in hit_state:
                ck = HITS[hkey]
                m = mc if ck in "cb" else (mr if ck in "ro" else np.maximum(E, cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY) ** 4))
                c = centroid(m) or (W / 2, H / 2)
                hit_state[hkey] = dict(xy=c, n=idx)
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
        for hk2, st in hit_state.items():
            dt = (idx - st["n"]) * DT
            if dt > 0.7:
                continue
            col = C[HITS[hk2]]; c = st["xy"]
            out, ring = shockwave(out, c[0], c[1], 1800 * eout(dt / 0.55), 80, 34 * (1 - ease(dt / 0.55)))
            extra += ring * col * 1.4 * (1 - ease(dt / 0.55))
            if dt < 0.22:
                extra += speed_lines(c[0], c[1], tout, n=130, inner=220, color=tuple(float(v) for v in (WHITE * 0.6 + col * 0.4))) * 0.7 * (1 - dt / 0.22)
            if dt < 0.3 and idx % 2 == 0:
                for j in range(3):
                    a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 650)
                    extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 7 + j), tuple(float(v) for v in col), 2, 9) * (1 - dt / 0.3)
            if hkey is None:
                sh = shake(tout, 18 * (1 - ease(dt / 0.35)), 4)
            zoom *= 1 + 0.05 * (1 - eout(dt / 0.3))
            chrom = max(chrom, 0.012 * (1 - ease(dt / 0.35))); bl += (0.25 if hk2 in MINOR else 0.5) * (1 - ease(dt / 0.35))
        kc = idx - cut_n                                          # soft flash on hard cuts
        if 0 <= kc < 2 and hkey is None:
            out = out + (0.18 if kc == 0 else 0.06); chrom = max(chrom, 0.008 * (1 - kc / 2))
        embers.step(DT, 0.95, (0, -60)); sparks.step(DT, 0.955, (0, 140)); swirl.step(DT, 0.9, (0, 0))
        if len(embers.p): extra += embers.render(glow=3.5, gain=1.1)
        if len(sparks.p): extra += sparks.render(glow=4.0, gain=0.75)
        if len(swirl.p): extra += swirl.render(glow=3.5, gain=0.8)
        out = out + extra
        if zoom != 1.0 or sh != (0.0, 0.0):
            out = camera(out, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
        if chrom > 0:
            out = chroma(out, W / 2, H / 2, chrom * 0.5)
        out = bloom(out, 0.85, 0.4 * min(bl, 1.7))
        out = finish(out, grain=0.008, vignette=0.28, t=tout)
        enc.stdin.write(to8(out).tobytes())
    enc.stdin.close(); enc.wait()
    os.replace(fn + ".tmp.mp4", fn)

if os.environ.get("TEST_AT"):
    mine = [0]
if os.environ.get("ONLY_CHUNK"):                                # re-render one chunk with the current code
    mine = [int(os.environ["ONLY_CHUNK"])]
    f = f"{SEGDIR}/c{mine[0]:03d}.mp4"
    if os.path.exists(f): os.remove(f)
for ci in sorted(mine):
    render_chunk(ci)
    print("chunk", ci, chunks[ci], flush=True)
print("done", WK)
