"""Full film, both versions (second pass): original timing + 3-frame hit-stops, effects placed only
where they belong.

What changed from fxall.py (feedback: particles on empty sky, too little on eyes and attacks,
Hollow Purple still blown out):
  * placement is decided per shot (EYES / ENERGY tables below, every shot checked by eye); colour
    detection only locates things inside those shots, and large coloured areas (red sky, red or blue
    tinted panels, blood) never get effects; no screen-wide embers
  * EYES: glow halo with a hot core, anamorphic lens streak, flicker, and a light trail when they move
  * attacks: hits as before (flash, two-tone frame, shockwave, speed lines, lightning, sparks, shake,
    push-in) plus an impact star at the contact point, more sparks, and stronger afterimages and
    surround light on moving energy
  * HOLLOW PURPLE (32.3-34.4 s, 88.5 s to the end): red and blue spirals converge on the gathering
    point, then the blown-out white is mapped through a purple light ramp (pink-white only at the
    core, violet falloff), highlights are compressed below clipping, no white flash frame, almost no
    bloom; the closing white-out and fade become purple light instead of a white screen
  * orbs (Red, Blue) rotate; bright frames get far less bloom
Base pictures come from near-lossless videos on the 60 fps grid (base/A_*.mp4, base/B.mp4).
usage: fxall2.py MODE WORKER NWORKERS     (env ONLY_CHUNK=i, TEST_AT=t96 TEST_N=frames)
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
ts = np.load(S + "/ts.npy"); fmap = np.load(S + "/work/fmap.npy")
units = json.load(open(S + "/work/units.json"))
SEGDIR = f"{HERE}/seg2{MODE}"; os.makedirs(SEGDIR, exist_ok=True)

C = dict(r=np.float32([0.28, 0.22, 1.0]), c=np.float32([1.0, 0.92, 0.35]), w=np.float32([1, 1, 1]),
         o=np.float32([0.3, 0.65, 1.0]), p=np.float32([1.0, 0.45, 0.95]), b=np.float32([1.0, 0.6, 0.25]))
WHITE = C["w"]; PURPLE = np.float32([1.0, 0.35, 0.85]); VIOLET = np.float32([0.55, 0.08, 0.35])
HITS = {
    1.231: "w", 32.91: "p", 34.10: "p",
    35.40: "r", 35.95: "c", 36.40: "c", 36.83: "c", 36.93: "c", 37.03: "c", 37.22: "r",
    40.80: "w", 41.36: "r", 47.25: "w",
    55.79: "r", 56.07: "r", 56.35: "r", 56.92: "w", 57.61: "r",
    67.83: "c", 68.27: "c", 69.96: "o", 71.08: "c",
    73.14: "r", 74.29: "r", 75.01: "r", 78.69: "r", 80.85: "r", 82.99: "b", 89.63: "p", 92.10: "p",
}
HS = 3
MINOR = set(h for a, h in zip(sorted(HITS), sorted(HITS)[1:]) if h - a < 0.15)
MERGE = [(32.29, 32.91, (0.47, 0.66)), (88.52, 89.65, None)]   # red + blue converge -> purple (anchor)
BLAST = [(32.91, 34.43), (89.65, 96.01)]           # purple light: tone-map the white (to the end fade)
ORBS = [(71.78, 74.05, "r", 1.0), (80.94, 84.17, "c", -1.0), (85.20, 86.35, "r", 1.0)]
ARCS = [(74.95, 75.44, "r"), (84.64, 85.20, "c")]
PULSE = [(76.07, 76.51)]

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
class Base:
    def __init__(self):
        self.p = None; self.n = None
        if MODE == "A":
            step = (NSRC + 2) // 3
            self.files = [(k * step, min(NSRC, (k + 1) * step), f"{HERE}/base/A_{k}.mp4") for k in range(3)]
        elif os.environ.get("BTAIL"):                               # partial base for re-rendering the end
            self.files = [(int(os.environ["BTAIL"]), NSRC, f"{HERE}/base/B_tail.mp4")]
        else:
            self.files = [(0, NSRC, f"{HERE}/base/B.mp4")]
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

# ---------------------------------------------------------------- per-shot placement (checked shot by shot)
# Colour detection alone puts effects on red skies, red-tinted panels and blood, so every shot was
# looked at and only these get colour effects.  Key = shot index in units.json.
#   EYES:   glowing eyes in frame (c = Gojo blue, r = Sukuna red) -> eye glow, lens streak, light trail
#   ENERGY: cursed-energy fists / blasts -> burning distortion, afterimage, surround light, embers
EYES = {5: "c2", 6: "c2", 8: "c1", 14: "r2", 16: "c2", 17: "c2", 18: "r2", 19: "r2", 37: "c2", 40: "r2",
        44: "c1", 45: "c2", 46: "r1", 50: "c2", 51: "r4", 54: "c2", 56: "r2", 59: "c2", 60: "r2", 61: "r3",
        66: "c2", 67: "c2", 69: "r2", 72: "c1", 75: "c1", 77: "r2", 79: "c2", 80: "c1r2", 83: "c2", 86: "r1",
        94: "c1", 96: "c2", 97: "c1", 102: "c1", 106: "c2", 111: "c1", 113: "c1", 116: "r2", 119: "c2",
        122: "r2", 123: "c1"}                               # colour + how many glowing eyes are in frame
EYE_FROM = {14: 14.45}                                     # eyes open only later in the shot
ENERGY = {0: "c", 1: "r", 2: "cr", 42: "c", 43: "c", 44: "r", 45: "c", 46: "c", 47: "c", 48: "c", 49: "r",
          67: "c", 74: "r", 75: "cr", 76: "cr", 77: "r", 88: "c", 89: "c", 90: "c", 107: "r", 108: "r",
          110: "r", 117: "c"}
def eye_spec(ui, t):
    e = EYES.get(ui, "")
    if not e or t < EYE_FROM.get(ui, 0): return {}
    return {e[i]: int(e[i + 1]) for i in range(0, len(e), 2)}

def hue_mask(hsv, kind):
    h, s, v = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    if kind == "c":
        hm = np.clip(1 - np.abs(h - 96) / 20, 0, 1)                 # cyan .. sky-blue (Gojo)
    else:
        hm = np.clip(1 - np.minimum(np.abs(h - 0), np.abs(h - 180)) / 12, 0, 1)
    return hm * np.clip((s - 0.4) / 0.25, 0, 1) * np.clip((v - 0.45) / 0.25, 0, 1)

def detect(img, kinds, big=False):
    """-> per colour: (energy mask 1080p, eye candidates [(x, y, r, score)] best first)"""
    small = cv2.resize(np.clip(img, 0, 1), (480, 270), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor((small * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    A = 480 * 270; out = {}
    for kind in kinds:
        m = hue_mask(hsv, kind)
        n, lab, st, cen = cv2.connectedComponentsWithStats((m > 0.35).astype(np.uint8), 8)
        msum = np.bincount(lab.ravel(), m.ravel(), n); vsum = np.bincount(lab.ravel(), hsv[..., 2].ravel() / 255, n)
        keep = np.zeros(n, np.float32); cands = []
        for j in range(1, n):
            x, y, w, h, area = st[j]
            touch = int(x == 0) + int(y == 0) + int(x + w >= 480) + int(y + h >= 270)
            if area > (0.35 if big else 0.06) * A or w > 0.8 * 480 or (touch >= 2 and area > 0.08 * A) \
                    or (not big and y == 0 and w > 0.3 * 480):
                continue                                         # coloured backdrop, not energy
            keep[j] = 1.0
            cx_, cy_ = cen[j]
            if 2 <= area <= 300 and max(w, h) <= 22 and max(w, h) <= 3.2 * min(w, h) + 2 and area >= 0.4 * w * h \
                    and 0.06 * 480 < cx_ < 0.94 * 480 and 0.06 * 270 < cy_ < 0.94 * 270:
                mm_, vv_ = msum[j] / area, vsum[j] / area           # eyes glow: saturated and bright
                if mm_ >= 0.45 and vv_ >= 0.55:
                    sc = mm_ * vv_ * min(1.0, area / 6.0)
                    cands.append((float(cx_ * 4), float(cy_ * 4), float(max(w, h) * 2 + 3), float(sc)))
        mm = cv2.GaussianBlur(m * keep[lab], (0, 0), 1.0)
        cands.sort(key=lambda g: -g[3])
        out[kind] = (cv2.resize(mm, (W, H), interpolation=cv2.INTER_LINEAR), cands)
    return out


EYE_HOT = np.float32([1.0, 1.0, 1.0])
def eye_layers(glints, col, t):
    """half-res layers: glow (halo + hot core) and streak (anamorphic lens line)"""
    glow = np.zeros((H // 2, W // 2, 3), np.float32); core_l = np.zeros((H // 2, W // 2), np.float32)
    for k, (x, y, r, s) in enumerate(glints):
        x2, y2 = int(x / 2), int(y / 2)
        fl = 0.88 + 0.12 * np.sin(t * 11 + k * 1.7)
        core = np.zeros((H // 2, W // 2), np.float32); cv2.circle(core, (x2, y2), max(1, int(r / 3)), 1.0, -1)
        streak = np.zeros_like(core); L = int(70 + r * 6)
        cv2.line(streak, (x2 - L, y2), (x2 + L, y2), 1.0, 1, cv2.LINE_AA)
        halo = cv2.GaussianBlur(core, (0, 0), 2 + r * 0.5) * 2.2 + cv2.GaussianBlur(core, (0, 0), 8 + r * 1.2) * 1.6 \
            + cv2.GaussianBlur(core, (0, 0), 26 + r * 2.5) * 1.2
        st = cv2.GaussianBlur(streak, (0, 0), 1.0) * 0.9 + cv2.GaussianBlur(streak, (0, 0), 4.0) * 0.8
        glow += (halo + st)[..., None] * col * fl
        core_l += cv2.GaussianBlur(core, (0, 0), 1.2) * fl
    glow += core_l[..., None] * EYE_HOT * 0.6
    return glow, core_l

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

def purple_center(img, prev, anchor=None):
    """where Hollow Purple is gathering: the compact bright magenta light; before it shows (or when the
    whole frame is magenta) the shot's anchor point, else the brightest spot"""
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
    b = np.clip((g - 0.88) / 0.1, 0, 1)
    if b.mean() > 0.85 or b.sum() < 20:
        return prev if prev is not None else (W / 2, H * 0.35)
    yy, xx = np.mgrid[0:270, 0:480]
    c = (float((b * xx).sum() / b.sum() * 4), float((b * yy).sum() / b.sum() * 4))
    return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)

# purple light ramp (BGR): luminance -> colour; replaces the blown-out white of Hollow Purple
RAMP_L = np.float32([0.0, 0.3, 0.62, 0.85, 1.0])
RAMP_C = np.float32([[0.0, 0.0, 0.0], [0.42, 0.04, 0.26], [0.95, 0.28, 0.78], [0.98, 0.62, 0.95], [0.95, 0.84, 0.96]])
def purple_ramp(L):
    return np.stack([np.interp(L, RAMP_L, RAMP_C[:, k]) for k in range(3)], -1).astype(np.float32)

def purple_tonemap(out, c, full=False):
    """blown-out white -> purple light: hot pink-white only near the centre, violet falloff outward"""
    L = cv2.cvtColor(np.clip(out, 0, 1), cv2.COLOR_BGR2GRAY)
    d = np.clip(np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2) / 1100.0, 0, 1)
    Ld = L * (1 - 0.38 * d)                                        # depth: light falls off from the core
    k = np.ones_like(L) if full else np.clip((L - 0.55) / 0.3, 0, 1)
    k = k[..., None]
    return out * (1 - k) + purple_ramp(Ld) * k

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
    base = Base()
    embers, sparks, swirl = Particles(), Particles(), Particles()
    trailE = None; trailEye = None; last_unit = None; hit_state = {}; cut_n = -99; last_n = None; img0 = None
    pc = tuple(float(v) for v in os.environ["PC0"].split(",")) if os.environ.get("PC0") else None
    for idx in range(a0, a1):
        n, t, hk, hkey = timeline[idx]
        tout = idx * DT
        ui = unit_of_t(t)
        if n != last_n:
            img0 = base.get(n); last_n = n
        img = img0.copy()
        if ui != last_unit:
            if last_unit is not None: cut_n = idx
            trailE = None; trailEye = None; embers = Particles(); swirl = Particles(); last_unit = ui
        ek, eyespec = ENERGY.get(ui, ""), eye_spec(ui, t)
        orb = inside(t, ORBS)
        arc = next((x[2] for x in ARCS if x[0] <= t < x[1]), "")
        kinds = sorted(set(ek + arc + (orb[2] if orb else "")))
        det = detect(img, kinds, big=bool(ek or orb or arc)) if kinds else {}
        E = np.zeros((H, W), np.float32)
        for k_ in ek:
            E = np.maximum(E, det[k_][0])
        ef = float(E.mean())
        extra = np.zeros((H, W, 3), np.float32)
        zoom, sh, chrom, bl = 1.0, (0.0, 0.0), 0.0, 1.0
        merge, blast = inside(t, MERGE), inside(t, BLAST)
        if ef > 0.0005:                                            # cursed energy keeps burning
            m = cv2.GaussianBlur(cv2.dilate(E, np.ones((21, 21), np.uint8)), (0, 0), 10)
            dx = NX.field(tout * 1.4, (0, -1), 110) * 7 * m; dy = (NY.field(tout * 1.4 + 3.1, (0, -1), 110) - 0.8) * 7 * m
            img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if orb:
            blob = orb_blob(det[orb[2]][0])
            if blob:
                img = spin(img, blob, orb[3] * 5.0 * (t - orb[0]))
                m_ = 50; a = rng.uniform(0, 2 * np.pi, m_); r0 = blob[2] * rng.uniform(1.0, 1.6, m_)
                p = np.stack([blob[0] + np.cos(a) * r0, blob[1] + np.sin(a) * r0], 1)
                tang = np.stack([-np.sin(a), np.cos(a)], 1) * rng.uniform(250, 700, (m_, 1)) * orb[3] - np.stack([np.cos(a), np.sin(a)], 1) * 60
                swirl.emit(p, tang, C[orb[2]][None] * rng.uniform(0.6, 1.3, (m_, 1)), rng.uniform(0.2, 0.5, m_), rng.uniform(0.8, 1.4, m_))
                d = np.sqrt((XX - blob[0]) ** 2 + (YY - blob[1]) ** 2)
                extra += (np.exp(-(d / (blob[2] * 1.6)) ** 2) * 0.35)[..., None] * C[orb[2]]
        out = grade(img, sat=1.08)
        out = np.clip((out - 0.5) * 1.05 + 0.5, 0, None)
        if ek:
            ener = img * E[..., None]
            trailE = ener * 0.6 if trailE is None else trailE * 0.8 + ener * 0.45
            out = out + np.maximum(trailE - ener * 1.4, 0) * 0.85               # afterimage of the moving fist
            out = out + cv2.GaussianBlur(ener, (0, 0), 22) * 0.45               # energy lights its surroundings
        if ef > 0.0005 and hk < 0:                                         # embers only from the energy itself
            pw = cv2.resize(E ** 2, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
            if pw.sum() > 0:
                k = int(min(80, 6000 * ef)); sel = rng.choice(len(pw), k, p=pw / pw.sum()); ys, xs = np.divmod(sel, 240)
                p = (np.stack([xs, ys], 1) * 8 + rng.uniform(0, 8, (k, 2))).astype(np.float32)
                cols = np.clip(img[np.clip(p[:, 1].astype(int), 0, H - 1), np.clip(p[:, 0].astype(int), 0, W - 1)] * 1.3, 0, 1.6)
                a = rng.normal(-np.pi / 2, 0.8, k); sp = rng.uniform(80, 300, k)
                embers.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cols, rng.uniform(0.25, 0.7, k), rng.uniform(0.8, 1.6, k))
        # ---- eyes: glow, lens streak, and a light trail when they move
        eyeg = np.zeros((H // 2, W // 2, 3), np.float32); eyec = np.zeros((H // 2, W // 2, 3), np.float32)
        for k_, ne in eyespec.items():
            g = find_eyes(img0, k_, ne)
            if g:
                gl, cl = eye_layers(g, C[k_], tout)
                eyeg += gl; eyec += cl[..., None] * C[k_]
        if eyespec:
            trailEye = eyec if trailEye is None else np.maximum(trailEye * 0.8, eyec)
            tr = cv2.GaussianBlur(np.maximum(trailEye - eyec, 0), (0, 0), 2.5) * 2.2
            ebl = 0.35 if blast else 1.0
            extra += cv2.resize(eyeg + tr, (W, H), interpolation=cv2.INTER_LINEAR) * ebl
        # ---- Hollow Purple
        if merge:                                                  # Red and Blue circle each other and fuse
            x = (t - merge[0]) / (merge[1] - merge[0]); pc = purple_center(img, pc, merge[2]); c = pc
            lay = np.zeros((H // 2, W // 2, 3), np.float32)
            for col, ph in ((C["r"], 0.0), (C["c"], np.pi)):
                for j in range(48):                                # orb + its spiral trail
                    xx = max(0.0, x - j * 0.0035)
                    th = ph + 9.0 * np.pi * xx ** 1.3; R = 260 * (1 - xx) ** 1.3 + 6
                    px, py = (c[0] + np.cos(th) * R) / 2, (c[1] + np.sin(th) * R * 0.55) / 2
                    cv2.circle(lay, (int(px), int(py)), max(1, int((9 if j == 0 else 4) * (1 - j / 56))), tuple(float(v) * (1.0 if j == 0 else 0.4 * (1 - j / 48)) for v in col), -1, cv2.LINE_AA)
            lay = cv2.GaussianBlur(lay, (0, 0), 1.2) * 1.4 + cv2.GaussianBlur(lay, (0, 0), 6) * 2.5 + cv2.GaussianBlur(lay, (0, 0), 18) * 1.5
            extra += cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
            d = np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2)
            extra += (np.exp(-(d / (40 + 160 * x)) ** 2) * (0.25 + 0.6 * x ** 2))[..., None] * PURPLE
            bl *= 0.5
        if blast:
            pc = bright_center(img, pc)
            Lm = float(cv2.resize(cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY), (96, 54)).mean())
            out = purple_tonemap(out, pc, full=t >= 93.85 or (Lm > 0.55 and t > 93.0))   # white-out and fade: all purple
            if idx % 3 == 0 and Lm < 0.8 and t < 93.85:            # no bolts on the white-out / fade
                c = pc
                for j in range(2):
                    a = rng.uniform(0, 2 * np.pi); L = rng.uniform(300, 800)
                    extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 5 + j, depth=6, branches=2), (1.0, 0.4, 0.9), 1, 8) * 0.5
            bl *= 0.2
        for a0_, a1_, ck in ARCS:
            if a0_ <= t < a1_ and idx % 2 == 0:
                c = centroid(det[ck][0]) if ck in det else None
                if c is not None:
                    for j in range(2):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 420)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 11 + j, depth=6, branches=2), tuple(float(v) for v in C[ck]), 1, 7) * 0.8
        for p0, p1 in PULSE:
            if p0 <= t < p1:
                x = (t - p0) / (p1 - p0); d = np.sqrt((XX - W / 2) ** 2 + (YY - H / 2) ** 2)
                for k3 in range(3):
                    ph = (x * 3 + k3 / 3) % 1
                    extra += (np.exp(-((d - 120 - 900 * ph) / 6.0) ** 2) * (1 - ph) * 0.6)[..., None] * WHITE
        # ---- hits
        if hkey is not None:
            ck = HITS[hkey]; col = C[ck]
            if hkey not in hit_state:
                kk = "c" if ck in "cb" else ("r" if ck in "ro" else None)
                c = None
                if kk:
                    c = centroid(det[kk][0]) if kk in det else centroid(detect(img, kk, big=True)[kk][0])
                c = c or bright_center(img, None)
                hit_state[hkey] = dict(xy=c, n=idx)
                m_ = 200 if ck == "p" else (250 if hkey in MINOR else 600)     # fewer, bigger sparks that stay
                a = rng.uniform(0, 2 * np.pi, m_); sp = rng.uniform(300, 1500, m_)   # around the impact: no dust
                cc = np.where(rng.random((m_, 1)) < 0.2, WHITE[None] * 1.2, col[None] * rng.uniform(0.7, 1.3, (m_, 1)))
                r0 = rng.uniform(20, 90, (m_, 1))
                sparks.emit(np.float32(c)[None] + np.stack([np.cos(a), np.sin(a)], 1) * r0, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.12, 0.42, m_), rng.uniform(1.8, 3.4, m_))
            if ck == "p":                                           # purple: no white frame
                if hk == 0:
                    out = out * 0.6 + PURPLE * 0.3
                elif hk == 1:
                    two = impact(out, "bw", True, 0.5)
                    out = two * PURPLE * 0.9 + (1 - two) * np.float32([0.08, 0.0, 0.06])
            else:
                if hk == 0:
                    out = out * 0.3 + 0.7 * (WHITE * 0.6 + col * 0.4)
                elif hk == 1:
                    two = impact(out, "bw", True, 0.42)
                    out = two * (col if ck != "w" else np.float32([0.9, 0.9, 0.95])) + (1 - two) * np.float32([0.03, 0.0, 0.05])
            sh = shake(tout, 22, 3)
        for hk2, st in hit_state.items():
            dt = (idx - st["n"]) * DT
            if dt > 0.7:
                continue
            col = C[HITS[hk2]]; c = st["xy"]
            out, ring = shockwave(out, c[0], c[1], 1800 * eout(dt / 0.55), 80, 38 * (1 - ease(dt / 0.55)))
            extra += ring * col * 1.5 * (1 - ease(dt / 0.55))
            if dt < 0.16:                                          # impact star at the point of contact
                fade = 1 - dt / 0.16; star = np.zeros((H // 2, W // 2), np.float32)
                x2, y2 = int(c[0] / 2), int(c[1] / 2); L = int(420 * (0.6 + 0.4 * fade))
                for ang in (0.0, np.pi / 2, np.pi / 4, -np.pi / 4):
                    l2 = L if ang in (0.0, np.pi / 2) else L // 2
                    cv2.line(star, (int(x2 - np.cos(ang) * l2), int(y2 - np.sin(ang) * l2)), (int(x2 + np.cos(ang) * l2), int(y2 + np.sin(ang) * l2)), 1.0, 2, cv2.LINE_AA)
                star = cv2.GaussianBlur(star, (0, 0), 1.5) + cv2.GaussianBlur(star, (0, 0), 6) * 1.5
                extra += cv2.resize(star, (W, H))[..., None] * (WHITE * 0.5 + col * 0.5) * fade * (0.5 if HITS[hk2] == "p" else 1.0)
            if dt < 0.22:
                extra += speed_lines(c[0], c[1], tout, n=150, inner=220, color=tuple(float(v) for v in (WHITE * 0.6 + col * 0.4))) * 0.75 * (1 - dt / 0.22)
            if dt < 0.3 and idx % 2 == 0:
                for j in range(3):
                    a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 650)
                    extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 7 + j), tuple(float(v) for v in col), 2, 9) * (1 - dt / 0.3)
            if hkey is None:
                sh = shake(tout, 20 * (1 - ease(dt / 0.35)), 4)
            zoom *= 1 + 0.06 * (1 - eout(dt / 0.3))
            chrom = max(chrom, 0.014 * (1 - ease(dt / 0.35))); bl += (0.25 if hk2 in MINOR else 0.5) * (1 - ease(dt / 0.35))
        kc = idx - cut_n
        if 0 <= kc < 2 and hkey is None and not blast:
            out = out + (0.12 if kc == 0 else 0.04); chrom = max(chrom, 0.008 * (1 - kc / 2))
        embers.step(DT, 0.95, (0, -60)); sparks.step(DT, 0.955, (0, 140)); swirl.step(DT, 0.9, (0, 0))
        if len(embers.p): extra += embers.render(glow=3.5, gain=1.0)
        if len(sparks.p): extra += sparks.render(glow=4.0, gain=0.75)
        if len(swirl.p): extra += swirl.render(glow=3.5, gain=0.8)
        out = out + extra
        if blast:                                                  # keep the purple light below clipping
            out = out / (1 + np.maximum(out.max(-1, keepdims=True) - 0.9, 0) * 1.5)
        if zoom != 1.0 or sh != (0.0, 0.0):
            out = camera(out, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
        if chrom > 0:
            out = chroma(out, W / 2, H / 2, chrom * 0.5)
        mL = float(cv2.resize(np.clip(out, 0, 1), (96, 54)).mean())
        bl *= float(np.clip((0.75 - mL) / 0.35, 0.15, 1.0))             # bright frames: no extra glare
        out = bloom(out, 0.85, 0.4 * min(bl, 1.7))
        out = finish(out, grain=0.008, vignette=0.28, t=tout)
        enc.stdin.write(to8(out).tobytes())
    enc.stdin.close(); enc.wait()
    if base.p: base.p.kill()
    os.replace(fn + ".tmp.mp4", fn)

if os.environ.get("RANGE"):                                         # re-render a timeline range: a,b
    a0, a1 = (int(v) for v in os.environ["RANGE"].split(","))
    f = f"{SEGDIR}/range_{a0}_{a1}.mp4"
    if os.path.exists(f): os.remove(f)
    render_chunk(0, a0, a1, f); print("range", f); sys.exit(0)
if os.environ.get("TEST_AT"):
    a0 = next(i for i, x in enumerate(timeline) if x[1] >= float(os.environ["TEST_AT"]))
    a1 = a0 + int(os.environ.get("TEST_N", "60"))
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
