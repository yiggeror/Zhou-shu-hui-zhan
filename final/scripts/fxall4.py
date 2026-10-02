"""Full film, both versions (fourth pass): original timing + 3-frame hit-stops; effects follow a
shot-by-shot cue sheet (FIST / EYES below, plus the timed events) instead of colour detection deciding
on its own; detection is only used to find where the fist, eye or orb is inside a shot that the cue
sheet gives an effect.
  * FIST: cursed-energy fists and techniques burn (flame distortion), leave afterimages, light their
    surroundings and throw embers (the first-pass look)
  * EYES: 1 = soft glow; 2-3 = "cursed energy in the eyes": glow, small flames and embers drifting off
    the eyes, for the shots where the expression carries it
  * Red / Blue: the orb spins, swirl particles, coloured aura, crackling arcs
  * Hollow Purple: Red and Blue circle each other and fuse at the gathering point; in version B the two
    explosion shots use the redrawn frames (sharper and less blown out); the blast gets crackling purple
    lightning, sparks thrown from the core and shockwaves; highlights are compressed instead of
    clipping, purple instead of white hit flashes, little bloom
  * hits, cut flashes, rising embers (shrine, Red, final blast) and the wheel pulse as in the first pass
Base pictures: near-lossless videos on the 60 fps grid (base/A_*.mp4, base/B.mp4).
usage: fxall4.py MODE WORKER NWORKERS     (env ONLY_CHUNK=i, TEST_AT=t96 TEST_N=frames, RANGE=a,b)
"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
MODE, WK, NW = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, S + "/pilot"); sys.path.insert(0, HERE)
import numpy as np, cv2
from fx import (W, H, XX, YY, Noise, Particles, camera, shake, chroma, shockwave, bloom, speed_lines,
                lightning, draw_bolts, finish, to8, impact, grade)
from eyedet import eyes as find_eyes

FPS = 60; DT = 1.0 / FPS; NSRC = 5760
ts = np.load(S + "/ts.npy")
units = json.load(open(S + "/work/units.json"))
SEGDIR = f"{HERE}/seg4{MODE}"; os.makedirs(SEGDIR, exist_ok=True)

C = dict(r=np.float32([0.28, 0.22, 1.0]), c=np.float32([1.0, 0.92, 0.35]), w=np.float32([1, 1, 1]),
         o=np.float32([0.3, 0.65, 1.0]), p=np.float32([1.0, 0.45, 0.95]), b=np.float32([1.0, 0.6, 0.25]))
WHITE = C["w"]; PURPLE = np.float32([1.0, 0.35, 0.85]); PINK = np.float32([1.0, 0.7, 1.0])
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
# first-pass continuous events (full/events.json) minus the embers rising over the red sky (30.75 s)
EV = [e for e in json.load(open(S + "/full/events.json"))
      if e["kind"] in ("rise", "arcs", "orb", "pulse") and not (e["kind"] == "rise" and e["t0"] == 30.75)]
SPIN = [(71.78, 74.05, "r", 1.0), (80.94, 83.38, "c", -1.0), (85.20, 86.35, "r", 1.0)]
ORB_T = [(71.78, 74.29, "r"), (80.94, 84.17, "c"), (85.20, 86.35, "r")]        # aura / arcs / haze
MERGE = [(32.29, 32.91, (0.47, 0.66)), (88.52, 89.65, None)]                   # Red + Blue -> purple
BLAST = [(32.91, 34.43), (89.65, 93.85)]
WHITEOUT = (93.85, 96.01)
A_FOR_B = {41, 124}                                     # B uses the redrawn frames for these explosions
# cue sheet: shot index (work/units.json) -> effect.  Every shot was looked at; shots not listed get only
# the timed events (hits, cut flash, Red/Blue/Purple, rising embers, pulse).
FIST = {0: "c", 1: "r", 2: "cr", 32: "c", 33: "c", 34: "c", 42: "c", 43: "c", 44: "r", 45: "c", 46: "c",
        47: "c", 48: "c", 49: "r", 67: "c", 72: "c", 73: "c", 74: "r", 75: "cr", 76: "cr", 77: "r", 88: "c",
        89: "c", 90: "c", 101: "r", 103: "r", 107: "r", 108: "r", 110: "r", 117: "c"}
LOOSE = {0, 1, 2, 42, 43, 44, 45, 46, 47, 48, 49, 67, 74, 75, 76, 77, 88, 89, 90, 107, 108, 110, 117}   # big fists
# eyes: colour, how many glowing eyes are in frame, strength (1 glow, 2-3 cursed energy in the eyes)
EYES = {5: "c23", 6: "c22", 8: "c11", 9: "r11", 14: "r23", 16: "c23", 17: "c23", 18: "r21", 19: "r23",
        37: "c22", 40: "r21", 44: "c11", 45: "c22", 46: "r11", 50: "c22", 51: "r42", 54: "c23", 56: "r22",
        59: "c23", 60: "r22", 61: "r32", 66: "c22", 67: "c22", 69: "r22", 72: "c11", 75: "c11", 77: "r21",
        79: "c22", 80: "c12r22", 83: "c22", 86: "r11", 94: "c12", 96: "c23", 97: "c11", 102: "c13",
        106: "c22", 111: "c12", 113: "c12", 116: "r22", 119: "c21", 122: "r22", 123: "c13"}
EYE_FROM = {14: 14.45}

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3
def inside(t, segs):
    return next((s for s in segs if s[0] <= t < s[1]), None)
def src_i(t):
    return max(0, int(np.searchsorted(ts, t + 1e-6, side="right")) - 1)
UNIT_OF_SRC = np.zeros(len(ts), np.int32)
for j, x in enumerate(units):
    UNIT_OF_SRC[x["start"]:x["end"]] = j
def unit_of_t(t):
    return int(UNIT_OF_SRC[src_i(t)])
def eye_spec(ui, t):
    e = EYES.get(ui, "")
    if not e or t < EYE_FROM.get(ui, 0): return {}
    return {e[i]: (int(e[i + 1]), int(e[i + 2])) for i in range(0, len(e), 3)}

# ---------------------------------------------------------------- timeline + chunks (as fxall.py)
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

# ---------------------------------------------------------------- base pictures (sequential decode)
A_FILES = [(k * 1920, min(NSRC, (k + 1) * 1920), f"{HERE}/base/A_{k}.mp4") for k in range(3)]
B_FILES = [(0, NSRC, f"{HERE}/base/B.mp4")]
class Reader:
    def __init__(self, files):
        self.files = files; self.p = None; self.n = None
    def _open(self, n):
        if self.p: self.p.kill()
        a, b, f = next(x for x in self.files if x[0] <= n < x[1])
        self.lim = b
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{(n - a - 0.4) / FPS:.5f}", "-i", f,
                                   "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
        self.n = n - 1
    def get(self, n):
        if self.p is None or n <= self.n or n > self.n + 30 or n >= self.lim:
            self._open(n)
        while self.n < n:
            buf = self.p.stdout.read(W * H * 3); self.n += 1
        return np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    def close(self):
        if self.p: self.p.kill()

# ---------------------------------------------------------------- energy detection (no backdrops)
def hue_mask(hsv, kind):
    h, s, v = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    if kind == "c":
        hm = np.clip(1 - np.abs(h - 93) / 20, 0, 1)
    else:
        hm = np.clip(1 - np.minimum(np.abs(h - 0), np.abs(h - 180)) / 13, 0, 1)
    return hm * np.clip((s - 0.35) / 0.3, 0, 1) * np.clip((v - 0.35) / 0.3, 0, 1)

def energy(img, loose=False):
    """-> {c, r}: energy masks at 1080p; coloured areas that span the frame are left out
    (loose: shots with huge energy fists, only areas covering most of the frame are left out)"""
    small = cv2.resize(np.clip(img, 0, 1), (480, 270), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor((small * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    A = 480 * 270; out = {}
    for kind in ("c", "r"):
        m = hue_mask(hsv, kind)
        n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0.3).astype(np.uint8), 8)
        keep = np.ones(n, np.float32); keep[0] = 0
        for j in range(1, n):
            x, y, w, h, area = st[j]
            touch = int(x == 0) + int(y == 0) + int(x + w >= 480) + int(y + h >= 270)
            if area > 0.4 * A or w > 0.85 * 480 or (not loose and ((touch >= 2 and area > 0.1 * A) or (y == 0 and w > 0.45 * 480 and h < 0.5 * 270))):
                keep[j] = 0
        km = cv2.dilate(keep[lab], np.ones((5, 5), np.uint8))
        mm = cv2.GaussianBlur(m * km, (0, 0), 0.8)
        out[kind] = cv2.resize(mm, (W, H), interpolation=cv2.INTER_LINEAR)
    return out

def centroid(m):
    s = float(m.sum()); return None if s < 80 else (float((m * XX).sum() / s), float((m * YY).sum() / s))

def orb_blob(m):
    b = (cv2.resize(m, (480, 270)) > 0.3).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(b, 8)
    if n < 2: return None
    j = 1 + int(np.argmax(st[1:, 4])); x, y, w, h, area = st[j]
    if area < 120 or area / (np.pi * (max(w, h) / 2) ** 2 + 1e-6) < 0.45: return None
    return float(cen[j][0] * 4), float(cen[j][1] * 4), float(max(w, h) * 4 * 0.55)

def spin(out, blob, ang):
    cx, cy, r = blob
    M = cv2.getRotationMatrix2D((cx, cy), float(np.degrees(ang)), 1.0)
    rot = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = np.clip((r - np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)) / (0.25 * r), 0, 1)[..., None]
    return out * (1 - a) + rot * a

def haze(img, cx, cy, r, tout, amp):
    """heat distortion in a ring around an energy source"""
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    m = np.exp(-((d - r) / (r * 0.8 + 40)) ** 2) * amp
    dx = NX.field(tout * 2.0, (0, -1), 160) * m; dy = NY.field(tout * 2.0 + 5.0, (0, -1), 160) * m
    return cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def eye_glow(glints, col, t):
    """soft glow around glowing eyes, half resolution"""
    lay = np.zeros((H // 2, W // 2), np.float32); acc = np.zeros((H // 2, W // 2, 3), np.float32)
    for k, (x, y, r, s) in enumerate(glints):
        lay[:] = 0
        cv2.circle(lay, (int(x / 2), int(y / 2)), max(1, int(r * 0.35)), 1.0, -1, cv2.LINE_AA)
        fl = 0.9 + 0.1 * np.sin(t * 7 + k * 1.9)
        g = cv2.GaussianBlur(lay, (0, 0), 2 + r * 0.35) * 0.9 + cv2.GaussianBlur(lay, (0, 0), 7 + r * 0.9) * 0.7
        acc += g[..., None] * col * fl
    return cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)

def purple_center(img, prev, anchor=None):
    """where Hollow Purple is gathering: the compact bright magenta light (else the shot's anchor)"""
    hsv = cv2.cvtColor((np.clip(cv2.resize(img, (480, 270)), 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    m = np.clip(1 - np.abs(hsv[..., 0] - 148) / 18, 0, 1) * np.clip((hsv[..., 1] / 255 - 0.25) / 0.2, 0, 1) * np.clip((hsv[..., 2] / 255 - 0.6) / 0.2, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 4)
    if m.sum() < 30 or (m > 0.3).mean() > 0.12:
        if anchor is not None:
            c = (anchor[0] * W, anchor[1] * H)
            return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)
        return bright_center(img, prev)
    y, x = np.unravel_index(int(np.argmax(m)), m.shape)
    c = (float(x * 4), float(y * 4))
    return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)

def bright_center(img, prev):
    """centre of the blinding light; keeps the previous one when the whole frame is white"""
    g = cv2.cvtColor(np.clip(cv2.resize(img, (480, 270)), 0, 1), cv2.COLOR_BGR2GRAY)
    b = np.clip((g - 0.85) / 0.1, 0, 1)
    if b.mean() > 0.85 or b.sum() < 20:
        return prev if prev is not None else (W / 2, H * 0.4)
    yy, xx = np.mgrid[0:270, 0:480]
    c = (float((b * xx).sum() / b.sum() * 4), float((b * yy).sum() / b.sum() * 4))
    return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)

def shoulder(out, k0=0.72, top=0.94):
    """compress highlights smoothly so the explosion keeps its texture instead of clipping to white"""
    L = out.max(-1, keepdims=True)
    over = np.maximum(L - k0, 0)
    newL = k0 + (top - k0) * (1 - np.exp(-over / (top - k0)))
    return out * np.where(L > k0, newL / (L + 1e-6), 1.0)

# ---------------------------------------------------------------- chunk renderer
NX, NY = Noise(41), Noise(42)

def render_chunk(ci, a0=None, a1=None, fn=None):
    if a0 is None:
        a0, a1 = chunks[ci]; fn = f"{SEGDIR}/c{ci:03d}.mp4"
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        return
    rng = np.random.default_rng(100 + ci)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-threads", "1", "-crf", "14",
                            "-tune", "animation", "-pix_fmt", "yuv420p", "-g", "120", fn + ".tmp.mp4"], stdin=subprocess.PIPE)
    main = Reader(A_FILES if MODE == "A" else B_FILES); alt = Reader(A_FILES) if MODE == "B" else None
    embers, sparks, swirl, burst, eyeP = Particles(), Particles(), Particles(), Particles(), Particles()
    trailE = None; last_unit = None; hit_state = {}; cut_n = -99; last_n = None; img0 = None; pc = None
    for idx in range(a0, a1):
        n, t, hk, hkey = timeline[idx]
        tout = idx * DT
        ui = unit_of_t(t)
        if n != last_n:
            img0 = (alt if (alt is not None and ui in A_FOR_B) else main).get(n); last_n = n
        img = img0.copy()
        if ui != last_unit:
            if last_unit is not None: cut_n = idx
            trailE = None; embers = Particles(); swirl = Particles(); eyeP = Particles(); last_unit = ui
        merge, blast = inside(t, MERGE), inside(t, BLAST)
        whiteout = WHITEOUT[0] <= t < WHITEOUT[1]
        en = energy(img, ui in LOOSE)
        mc, mr = en["c"], en["r"]
        E = np.zeros((H, W), np.float32)
        for k_ in FIST.get(ui, ""):
            E = np.maximum(E, en[k_])
        ef = float(E.mean())
        extra = np.zeros((H, W, 3), np.float32)
        zoom, sh, chrom, bl = 1.0, (0.0, 0.0), 0.0, 1.0
        if 0.001 < ef < 0.25:                                     # cursed energy keeps burning
            m = cv2.GaussianBlur(cv2.dilate(E, np.ones((21, 21), np.uint8)), (0, 0), 10)
            dx = NX.field(tout * 1.4, (0, -1), 110) * 7 * m; dy = (NY.field(tout * 1.4 + 3.1, (0, -1), 110) - 0.8) * 7 * m
            img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        orb = inside(t, ORB_T); blob = None
        if orb:                                                   # Red / Blue: spin, aura, arcs, haze
            blob = orb_blob(mr if orb[2] == "r" else mc)
            if blob is not None:
                img = haze(img, blob[0], blob[1], blob[2] * 1.3, tout, 3.5)
                for t0, t1, ck, sg in SPIN:
                    if t0 <= t < t1:
                        img = spin(img, blob, sg * 5.0 * (t - t0))
        out = grade(img, sat=1.1)
        out = np.clip((out - 0.5) * 1.05 + 0.5, 0, None)
        ener = img * E[..., None] * float(ef < 0.25)
        trailE = ener * 0.6 if trailE is None else trailE * 0.8 + ener * 0.42
        out = out + np.maximum(trailE - ener * 1.5, 0) * 0.7               # afterimage of the moving energy
        out = out + cv2.GaussianBlur(ener, (0, 0), 24) * 0.35 * max(0.0, 1 - ef * 4)
        if 0.001 < ef < 0.25 and hk < 0:                                   # embers from the energy
            pw = cv2.resize(E ** 2, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
            if pw.sum() > 0:
                k = int(min(80, 5000 * ef)); sel = rng.choice(len(pw), k, p=pw / pw.sum()); py, px = np.divmod(sel, 240)
                p = (np.stack([px, py], 1) * 8 + rng.uniform(0, 8, (k, 2))).astype(np.float32)
                cols = np.clip(img[np.clip(p[:, 1].astype(int), 0, H - 1), np.clip(p[:, 0].astype(int), 0, W - 1)] * 1.3, 0, 1.6)
                a = rng.normal(-np.pi / 2, 0.8, k); sp = rng.uniform(80, 320, k)
                embers.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cols, rng.uniform(0.3, 0.9, k), rng.uniform(0.8, 1.7, k))
        if blob is not None:                                      # orb aura + crackle
            col = C[orb[2]]; d = np.sqrt((XX - blob[0]) ** 2 + (YY - blob[1]) ** 2)
            extra += (np.exp(-((d - blob[2]) / (blob[2] * 0.35 + 10)) ** 2) * 0.45 + np.exp(-(d / (blob[2] * 2.2)) ** 2) * 0.25)[..., None] * col
            if idx % 3 == 0:
                for j in range(2):
                    a = rng.uniform(0, 2 * np.pi); r0 = blob[2] * 0.9; L = blob[2] * rng.uniform(1.2, 2.6)
                    p0 = (blob[0] + np.cos(a) * r0, blob[1] + np.sin(a) * r0)
                    extra += draw_bolts(lightning(p0, (blob[0] + np.cos(a) * (r0 + L), blob[1] + np.sin(a) * (r0 + L)), idx * 13 + j, depth=5, branches=2),
                                        tuple(float(v) for v in col), 1, 6) * 0.7
        # ---- eyes: soft glow
        for k_, (ne, lv) in eye_spec(ui, t).items():
            g = find_eyes(img0, k_, ne)
            if not g:
                continue
            extra += eye_glow(g, C[k_], tout) * ((0.5 if blast else 1.0) * (0.75 if lv == 1 else 1.0))
            if lv >= 2 and hk < 0:                                 # small flames and embers off the eyes
                for (ex, ey, er, _) in g:
                    k = 3 if lv == 2 else 7                         # sparks leave from around the eye
                    ra = rng.uniform(0, 2 * np.pi, k); rr = er * rng.uniform(0.7, 1.5, k)
                    p = np.stack([ex + np.cos(ra) * rr, ey + np.sin(ra) * rr * 0.6], 1)
                    a = rng.normal(-np.pi / 2, 0.6, k) * 0.6 + ra * 0.4 * 0 + rng.normal(0, 0.3, k)
                    a = np.where(np.sin(ra) < 0, -np.pi / 2 + (ra + np.pi / 2) * 0.5, -np.pi / 2 + rng.normal(0, 0.9, k))
                    sp = rng.uniform(120, 330, k) * (1 + 0.004 * er)
                    cc = (C[k_][None] * 0.85 + WHITE[None] * 0.15) * rng.uniform(0.9, 1.3, (k, 1))
                    sz = rng.uniform(1.1, 2.0, k) if lv == 2 else rng.uniform(1.4, 2.6, k) * (1 + 0.006 * er)
                    eyeP.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.4, 0.9, k), sz)
                if lv == 3:
                    em = np.zeros((H // 4, W // 4), np.float32)
                    for (ex, ey, er, _) in g:
                        cv2.circle(em, (int(ex / 4), int(ey / 4)), max(3, int(er * 1.4 / 4)), 1.0, -1)
                    em = cv2.resize(cv2.GaussianBlur(em, (0, 0), 5), (W, H))
                    dx = NX.field(tout * 1.6, (0, -1), 90) * 6 * em; dy = (NY.field(tout * 1.6 + 2.0, (0, -1), 90) - 0.8) * 6 * em
                    out = cv2.remap(out, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # ---- first-pass continuous events
        for ev in EV:
            if not (ev["t0"] <= t < ev["t1"]):
                continue
            col = np.float32(ev.get("col", [1.0, 0.85, 1.0]))
            if ev["kind"] == "rise" and idx % 2 == 0:
                m_ = 30; p = np.stack([rng.uniform(0, W, m_), rng.uniform(H * 0.45, H, m_)], 1)
                embers.emit(p, np.stack([rng.normal(0, 30, m_), rng.uniform(-280, -90, m_)], 1), col[None] * rng.uniform(0.5, 1.2, (m_, 1)), rng.uniform(0.8, 1.8, m_), 1.3)
            elif ev["kind"] == "arcs" and idx % 2 == 0:
                c = (pc if (merge and pc is not None) else None) or centroid(np.maximum(mc, mr))
                if c is not None:
                    for j in range(int(ev.get("n", 2))):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 420)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 11 + j, depth=6, branches=2), tuple(float(v) for v in col), 1, 7) * 0.8
            elif ev["kind"] == "orb":
                c = (blob[0], blob[1]) if blob is not None else None    # only around a found orb
                if c is not None:
                    rr = blob[2]
                    m_ = 160; a = rng.uniform(0, 2 * np.pi, m_); r0 = rr * rng.uniform(0.9, 2.2, m_)
                    p = np.stack([c[0] + np.cos(a) * r0, c[1] + np.sin(a) * r0], 1)
                    tang = np.stack([-np.sin(a), np.cos(a)], 1) * rng.uniform(300, 800, (m_, 1)) * ev.get("spin", 1)
                    swirl.emit(p, tang, col[None] * rng.uniform(0.6, 1.3, (m_, 1)), rng.uniform(0.25, 0.6, m_), rng.uniform(0.9, 1.6, m_))
            elif ev["kind"] == "pulse":
                x = (t - ev["t0"]) / (ev["t1"] - ev["t0"]); d = np.sqrt((XX - W / 2) ** 2 + (YY - H / 2) ** 2)
                for k3 in range(3):
                    ph = (x * 3 + k3 / 3) % 1
                    extra += (np.exp(-((d - 120 - 900 * ph) / 6.0) ** 2) * (1 - ph) * 0.6)[..., None] * col
        # ---- Hollow Purple: Red and Blue circle each other and fuse
        if merge:
            x = (t - merge[0]) / (merge[1] - merge[0]); pc = purple_center(img, pc, merge[2]); c = pc
            lay = np.zeros((H // 2, W // 2, 3), np.float32)
            for col, ph in ((C["r"], 0.0), (C["c"], np.pi)):
                for j in range(48):
                    xx = max(0.0, x - j * 0.0035)
                    th = ph + 9.0 * np.pi * xx ** 1.3; R = 260 * (1 - xx) ** 1.3 + 6
                    px_, py_ = (c[0] + np.cos(th) * R) / 2, (c[1] + np.sin(th) * R * 0.55) / 2
                    cv2.circle(lay, (int(px_), int(py_)), max(1, int((10 if j == 0 else 5) * (1 - j / 56))), tuple(float(v) * (1.0 if j == 0 else 0.5 * (1 - j / 48)) for v in col), -1, cv2.LINE_AA)
            lay = cv2.GaussianBlur(lay, (0, 0), 1.2) * 1.5 + cv2.GaussianBlur(lay, (0, 0), 6) * 2.8 + cv2.GaussianBlur(lay, (0, 0), 18) * 1.6
            extra += cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
            d = np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2)
            extra += (np.exp(-(d / (40 + 180 * x)) ** 2) * (0.3 + 0.7 * x ** 2))[..., None] * PURPLE
            m_ = 12; a = rng.uniform(0, 2 * np.pi, m_); r0 = rng.uniform(150, 420, m_)        # energy drawn inward
            p = np.stack([c[0] + np.cos(a) * r0, c[1] + np.sin(a) * r0], 1)
            v = (np.float32(c)[None] - p) * 3.0 + np.stack([-np.sin(a), np.cos(a)], 1) * 300
            swirl.emit(p, v, np.where(rng.random((m_, 1)) < 0.5, C["r"][None], C["c"][None]) * rng.uniform(0.8, 1.4, (m_, 1)), rng.uniform(0.2, 0.35, m_), rng.uniform(2.6, 4.0, m_))
            bl *= 0.6
        # ---- Hollow Purple: the blast
        if blast or whiteout:
            pc = bright_center(img, pc)
            out = shoulder(out)
            if blast:
                c = pc
                Lm = float(cv2.resize(cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY), (96, 54)).mean())
                core = float((cv2.cvtColor(np.clip(cv2.resize(img, (96, 54)), 0, 1), cv2.COLOR_BGR2GRAY) > 0.85).mean())
                if 0.01 < core < 0.6:                              # sparks thrown from a visible core
                    m_ = 22; a = rng.uniform(0, 2 * np.pi, m_); sp = rng.uniform(250, 1000, m_); r0 = rng.uniform(60, 240, (m_, 1))
                    cc = np.where(rng.random((m_, 1)) < 0.3, PINK[None], PURPLE[None]) * rng.uniform(0.8, 1.4, (m_, 1))
                    burst.emit(np.float32(c)[None] + np.stack([np.cos(a), np.sin(a)], 1) * r0, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.25, 0.6, m_), rng.uniform(1.8, 3.2, m_))
                if idx % 2 == 0 and Lm < 0.82 and core > 0.01 and ui not in (40, 122, 123):   # not over the faces
                    for j in range(3):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 750)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 5 + j, depth=6, branches=3), (1.0, 0.45, 0.95), 2, 9) * 0.75
            bl *= 0.35
        # ---- hits
        if hkey is not None:
            ck = HITS[hkey]; col = C[ck]
            if hkey not in hit_state:
                m = mc if ck in "cb" else (mr if ck in "ro" else None)
                c = (centroid(m) if m is not None else None) or bright_center(img, None)
                hit_state[hkey] = dict(xy=c, n=idx)
                m_ = 400 if ck == "p" else (700 if hkey in MINOR else 2500); a = rng.uniform(0, 2 * np.pi, m_); sp = rng.uniform(400, 2400, m_)
                cc = np.where(rng.random((m_, 1)) < 0.2, WHITE[None] * 1.2, col[None] * rng.uniform(0.7, 1.3, (m_, 1)))
                r0 = rng.uniform(20, 90, (m_, 1))
                sparks.emit(np.float32(c)[None] + np.stack([np.cos(a), np.sin(a)], 1) * r0, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.2, 0.8, m_), rng.uniform(0.9, 2.2, m_))
            if ck == "p":                                           # Hollow Purple: purple flash, no white
                if hk == 0:
                    out = out * 0.55 + PURPLE * 0.38
                elif hk == 1:
                    two = impact(out, "bw", True, 0.5)
                    out = two * PURPLE * 0.92 + (1 - two) * np.float32([0.08, 0.0, 0.06])
            else:
                if hk == 0:
                    out = out * 0.2 + 0.95
                elif hk == 1:
                    two = impact(out, "bw", True, 0.42)
                    out = two * (col if ck != "w" else np.float32([0.9, 0.9, 0.95])) + (1 - two) * np.float32([0.03, 0.0, 0.05])
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
        if 0 <= kc < 2 and hkey is None and not (blast or whiteout):
            out = out + (0.16 if kc == 0 else 0.05); chrom = max(chrom, 0.008 * (1 - kc / 2))
        embers.step(DT, 0.95, (0, -60)); sparks.step(DT, 0.955, (0, 140)); swirl.step(DT, 0.9, (0, 0)); burst.step(DT, 0.93, (0, 0)); eyeP.step(DT, 0.97, (0, -70))
        if len(embers.p): extra += embers.render(glow=3.5, gain=1.1)
        if len(sparks.p): extra += sparks.render(glow=4.0, gain=0.75)
        if len(swirl.p): extra += swirl.render(glow=3.5, gain=0.85)
        if len(burst.p): extra += burst.render(glow=4.0, gain=0.8)
        if len(eyeP.p): extra += eyeP.render(glow=3.0, gain=1.0)
        out = out + extra
        if zoom != 1.0 or sh != (0.0, 0.0):
            out = camera(out, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
        if chrom > 0:
            out = chroma(out, W / 2, H / 2, chrom * 0.5)
        mL = float(cv2.resize(np.clip(out, 0, 1), (96, 54)).mean())
        bl *= float(np.clip((0.8 - mL) / 0.35, 0.2, 1.0))              # already-bright frames: less glare
        out = bloom(out, 0.85, 0.4 * min(bl, 1.7))
        if blast or whiteout:
            out = shoulder(out, 0.8, 0.96)
        out = finish(out, grain=0.008, vignette=0.28, t=tout)
        enc.stdin.write(to8(out).tobytes())
    enc.stdin.close(); enc.wait()
    main.close()
    if alt is not None: alt.close()
    os.replace(fn + ".tmp.mp4", fn)

if os.environ.get("RANGE"):
    a0, a1 = (int(v) for v in os.environ["RANGE"].split(","))
    f = f"{SEGDIR}/range_{a0}_{a1}.mp4"
    if os.path.exists(f): os.remove(f)
    render_chunk(0, a0, a1, f); print("range", f); sys.exit(0)
if os.environ.get("TEST_AT"):
    a0 = next(i for i, x in enumerate(timeline) if x[1] >= float(os.environ["TEST_AT"]))
    a1 = min(len(timeline), a0 + int(os.environ.get("TEST_N", "60")))
    f = f"{SEGDIR}/test_{a0}.mp4"
    if os.path.exists(f): os.remove(f)
    render_chunk(0, a0, a1, f); print("test", f); sys.exit(0)
if os.environ.get("ONLY_CHUNK"):
    mine = [int(os.environ["ONLY_CHUNK"])]
    f = f"{SEGDIR}/c{mine[0]:03d}.mp4"
    if os.path.exists(f): os.remove(f)
json.dump(dict(frames=len(timeline), chunks=chunks), open(f"{SEGDIR}/plan.json", "w"))
for ci in sorted(mine):
    render_chunk(ci)
    print("chunk", ci, chunks[ci], flush=True)
print("done", WK)
