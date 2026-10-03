"""Procedural VFX / stylization toolkit for the reinterpretation pilot.

Everything is drawn in float32 BGR, 0..1, at 1920x1080.
"""
import cv2, numpy as np, json, os

S = "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad"
W, H = 1920, 1080
cv2.setNumThreads(int(os.environ.get("CVT", "4")))
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
RNG = np.random.default_rng(7)

# ---------------------------------------------------------------- assets
_REG = json.load(open(S + "/work/reg.json"))

def asset(key):
    """clean super-resolved key state placed exactly as in its source framing"""
    r = _REG[key]
    M = np.array(r["M"], np.float64) @ np.array([[0.5, 0, -0.25], [0, 0.5, -0.25], [0, 0, 1]])
    pan = cv2.imread(f"{S}/panels2x/{key}.png").astype(np.float32) / 255
    return cv2.warpAffine(pan, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def energy_mask(img, hue):
    """saturated cyan ('c') or red ('r') energy regions"""
    hsv = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    if hue == "c":
        hm = np.clip(1 - np.abs(h - 90) / 18, 0, 1)
    else:
        hm = np.clip(1 - np.minimum(np.abs(h - 0), np.abs(h - 180)) / 14, 0, 1)
    m = hm * np.clip((s - 0.35) / 0.3, 0, 1) * np.clip((v - 0.35) / 0.3, 0, 1)
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)

def centroid(m):
    w = m.sum() + 1e-6
    return float((m * XX).sum() / w), float((m * YY).sum() / w)

# ---------------------------------------------------------------- noise
class Noise:
    """cheap animated fractal value noise (smooth, tileable enough for fx)"""
    def __init__(self, seed, scales=(96, 48, 24), amps=(1.0, 0.5, 0.25)):
        r = np.random.default_rng(seed)
        self.layers = []
        for sc, a in zip(scales, amps):
            gh, gw = H // sc + 4, W // sc + 4
            self.layers.append((sc, a, r.standard_normal((3, gh, gw)).astype(np.float32)))
    def field(self, t, flow=(0.0, -1.0), speed=60.0):
        out = np.zeros((H, W), np.float32)
        for sc, a, g in self.layers:
            # scroll the grid and morph between 3 random slices over time
            k = (t * 0.7) % 3; i0 = int(k); fr = k - i0
            grid = g[i0] * (1 - fr) + g[(i0 + 1) % 3] * fr
            ox = -flow[0] * speed * t / sc; oy = -flow[1] * speed * t / sc
            ix, iy = int(np.floor(ox)), int(np.floor(oy)); fx_, fy_ = ox - ix, oy - iy
            grid = np.roll(grid, (-iy, -ix), axis=(0, 1))       # whole cells
            big = cv2.warpAffine(grid, np.float32([[sc, 0, -(fx_ + 1) * sc], [0, sc, -(fy_ + 1) * sc]]),
                                 (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
            out += a * big
        return out

def flame(img, mask, t, noise_x, noise_y, amp=10.0, flow=(0, -1), speed=90):
    """make static flames lick and flow: displacement confined to the flame region"""
    m = cv2.GaussianBlur(cv2.dilate(mask, np.ones((25, 25), np.uint8)), (0, 0), 12)
    dx = noise_x.field(t, flow, speed) * amp * m + flow[0] * amp * 0.6 * m * (0.5 + 0.5 * np.sin(t * 9))
    dy = noise_y.field(t + 3.1, flow, speed) * amp * m + flow[1] * amp * 0.9 * m
    return cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---------------------------------------------------------------- camera / lens
def camera(img, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0, shake=(0.0, 0.0), border=cv2.BORDER_REFLECT):
    M = cv2.getRotationMatrix2D((cx, cy), rot, zoom)
    M[0, 2] += (W / 2 - cx) + shake[0]; M[1, 2] += (H / 2 - cy) + shake[1]
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=border)

def shake(t, amp, seed=0):
    r = np.random.default_rng(int(t * 60) + seed * 1000)
    return (float(r.normal() * amp), float(r.normal() * amp))

def zoom_blur(img, cx, cy, strength, n=10):
    """radial streak (speed-line smear) — intentional motion blur"""
    acc = np.zeros_like(img)
    for i in range(n):
        s = 1 + strength * i / (n - 1)
        acc += camera(img, s, cx, cy)
    return acc / n

def chroma(img, cx, cy, amt):
    """lateral chromatic aberration around (cx,cy)"""
    if amt <= 0:
        return img
    b = camera(img[..., 0:1].repeat(3, -1), 1 + amt, cx, cy)[..., 0]
    r = camera(img[..., 2:3].repeat(3, -1), 1 - amt, cx, cy)[..., 0]
    out = img.copy(); out[..., 0] = b; out[..., 2] = r
    return out

def shockwave(img, cx, cy, radius, width=60.0, amp=28.0):
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2) + 1e-3
    prof = np.exp(-((d - radius) / width) ** 2)
    disp = amp * prof
    out = cv2.remap(img, (XX - (XX - cx) / d * disp).astype(np.float32), (YY - (YY - cy) / d * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ring = np.exp(-((d - radius) / (width * 0.25)) ** 2)[..., None]
    return out, ring

def bloom(img, thr=0.65, strength=1.0, sigmas=(6, 18, 48)):
    lum = img.max(-1, keepdims=True)
    bright = img * np.clip((lum - thr) / (1 - thr + 1e-6), 0, 1)
    acc = np.zeros_like(img)
    for s in sigmas:
        acc += cv2.GaussianBlur(bright, (0, 0), s)
    return img + acc * (strength / len(sigmas))

def impact(img, mode="bw", invert=True, thr=0.45):
    """two-tone impact frame (anime 'cut-in' flash)"""
    g = cv2.cvtColor(np.clip(img, 0, 1).astype(np.float32), cv2.COLOR_BGR2GRAY)
    g = cv2.bilateralFilter(cv2.GaussianBlur(g, (0, 0), 1.5), 9, 0.15, 7)
    b = (g > thr).astype(np.uint8)
    b = cv2.morphologyEx(cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(np.float32)
    if invert:
        b = 1 - b
    if mode == "bw":
        return np.repeat(b[..., None], 3, -1)
    col = np.float32([0.05, 0.05, 0.95]) if mode == "red" else np.float32([0.95, 0.85, 0.2])
    return b[..., None] * col + (1 - b[..., None]) * np.float32([0.02, 0.0, 0.03])

def speed_lines(cx, cy, t, n=140, inner=260, seed=3, color=(1, 1, 1)):
    r = np.random.default_rng(seed + int(t * 30))
    layer = np.zeros((H, W, 3), np.float32)
    for _ in range(n):
        a = r.uniform(0, 2 * np.pi); r0 = inner + r.uniform(0, 400); r1 = r0 + r.uniform(300, 1400)
        p0 = (int(cx + np.cos(a) * r0), int(cy + np.sin(a) * r0)); p1 = (int(cx + np.cos(a) * r1), int(cy + np.sin(a) * r1))
        cv2.line(layer, p0, p1, color, int(r.integers(1, 4)), cv2.LINE_AA)
    return cv2.GaussianBlur(layer, (0, 0), 1.2)

def lightning(p0, p1, seed, jag=0.22, depth=7, branches=3):
    """fractal midpoint-displacement bolt; returns list of polylines"""
    r = np.random.default_rng(seed)
    def bolt(a, b, d, jj):
        pts = [np.array(a, np.float32), np.array(b, np.float32)]
        for _ in range(d):
            new = [pts[0]]
            for i in range(len(pts) - 1):
                m = (pts[i] + pts[i + 1]) / 2; v = pts[i + 1] - pts[i]
                n = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-6)
                new += [m + n * r.normal() * jj * np.linalg.norm(v), pts[i + 1]]
            pts = new
        return np.array(pts)
    main = bolt(p0, p1, depth, jag); out = [main]
    for _ in range(branches):
        k = int(r.integers(len(main) // 4, 3 * len(main) // 4)); a = main[k]
        ang = r.normal() * 0.9; v = (main[-1] - main[0]) * r.uniform(0.2, 0.45)
        rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        out.append(bolt(a, a + rot @ v, depth - 2, jag * 1.2))
    return out

def draw_bolts(bolts, color, core=2, glow=10):
    lay = np.zeros((H, W, 3), np.float32)
    for i, b in enumerate(bolts):
        cv2.polylines(lay, [b.astype(np.int32)], False, color, core if i == 0 else max(1, core - 1), cv2.LINE_AA)
    g = cv2.GaussianBlur(lay, (0, 0), glow)
    white = cv2.GaussianBlur(lay, (0, 0), 0.8)
    return g * 2.5 + white.max(-1, keepdims=True) * 1.2

# ---------------------------------------------------------------- particles
class Particles:
    def __init__(self, n=0):
        self.p = np.zeros((0, 2), np.float32); self.v = np.zeros((0, 2), np.float32)
        self.c = np.zeros((0, 3), np.float32); self.life = np.zeros(0, np.float32); self.age = np.zeros(0, np.float32)
        self.size = np.zeros(0, np.float32)
    def emit(self, pos, vel, col, life, size=1.0):
        self.p = np.vstack([self.p, pos.astype(np.float32)]); self.v = np.vstack([self.v, vel.astype(np.float32)])
        self.c = np.vstack([self.c, col.astype(np.float32)]); self.life = np.concatenate([self.life, life.astype(np.float32)])
        self.age = np.concatenate([self.age, np.zeros(len(pos), np.float32)])
        self.size = np.concatenate([self.size, np.full(len(pos), size, np.float32) if np.isscalar(size) else size.astype(np.float32)])
    def step(self, dt, drag=0.98, accel=(0, 0), swirl=None):
        if len(self.p) == 0:
            return
        a = np.array(accel, np.float32)[None]
        if swirl is not None:
            a = a + swirl(self.p)
        self.v = self.v * drag + a * dt
        self.p += self.v * dt; self.age += dt
        keep = (self.age < self.life) & (self.p[:, 0] > -200) & (self.p[:, 0] < W + 200) & (self.p[:, 1] > -200) & (self.p[:, 1] < H + 200)
        for k in ("p", "v", "c", "life", "age", "size"):
            setattr(self, k, getattr(self, k)[keep])
    def render(self, glow=4.0, gain=1.0):
        lay = np.zeros((H, W, 3), np.float32)
        if len(self.p):
            fade = np.clip(1 - self.age / self.life, 0, 1)[:, None] ** 0.7
            x = np.clip(self.p[:, 0].astype(np.int32), 0, W - 1); y = np.clip(self.p[:, 1].astype(np.int32), 0, H - 1)
            np.add.at(lay, (y, x), self.c * fade * self.size[:, None])
        core = cv2.GaussianBlur(lay, (0, 0), 0.9)
        return (core * 1.6 + cv2.GaussianBlur(lay, (0, 0), glow) * 6.0) * gain

# ---------------------------------------------------------------- styles
def neon(img, tint_bg=(0.09, 0.03, 0.02), line_gain=1.35, fill=0.10):
    """ink-line art -> glowing neon strokes on a deep night background"""
    g = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY)
    g = cv2.bilateralFilter(g, 11, 0.12, 9)
    g = cv2.bilateralFilter(g, 11, 0.12, 9)
    local = cv2.GaussianBlur(g, (0, 0), 4)
    ink = np.clip((local - g - 0.03) / 0.12, 0, 1)                       # thin dark strokes
    solid = np.clip((0.16 - g) / 0.1, 0, 1) * np.clip((0.2 - local) / 0.1, 0, 1)  # large black fills
    edge = cv2.morphologyEx((solid > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    lines = np.clip(ink + edge, 0, 1)
    # drop speckle outlines from textured ground/noise (keep only real strokes)
    lb = (lines > 0.35).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(lb, connectivity=8)
    keep = np.zeros(n, np.float32); keep[1:] = (st[1:, 4] >= 140).astype(np.float32)
    lines = lines * keep[lab]
    # colour each stroke from the (saturation-boosted) local colour, default icy white
    hsv = cv2.cvtColor((np.clip(cv2.GaussianBlur(img, (0, 0), 10), 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 2.2, 0, 255); hsv[..., 2] = 255
    col = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255
    sat = hsv[..., 1:2] / 255
    col = col * sat + np.float32([1.0, 0.92, 0.85]) * (1 - sat)
    base = np.float32(tint_bg)[None, None] + img * fill
    out = base * (1 - lines[..., None] * 0.9) + lines[..., None] * col * line_gain
    # cursed-energy flames stay as luminous fills
    e = np.maximum(energy_mask(img, "c"), energy_mask(img, "r"))[..., None]
    out = out * (1 - e * 0.6) + img * e * 1.1
    return out

def grade(img, lift=0.0, gamma=1.0, gain=1.0, sat=1.0):
    out = np.clip(img, 0, None)
    if sat != 1.0:
        m = out.mean(-1, keepdims=True); out = m + (out - m) * sat
    return np.clip((out * gain + lift) ** (1 / gamma), 0, None)

VIG = None
def finish(img, grain=0.035, vignette=0.35, t=0.0):
    global VIG
    if VIG is None:
        d = np.sqrt(((XX - W / 2) / (W / 2)) ** 2 + ((YY - H / 2) / (H / 2)) ** 2)
        VIG = (1 - vignette * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None].astype(np.float32)
    out = img * VIG
    r = np.random.default_rng(int(t * 1000) % 100000)
    n = r.standard_normal((H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    out = out + n * grain * (0.3 + 0.7 * np.clip(out.mean(-1, keepdims=True), 0, 1))
    # soft filmic shoulder instead of hard clipping
    out = np.clip(out, 0, None)
    out = out / (1 + np.maximum(out - 0.85, 0) * 1.4)
    return np.clip(out, 0, 1)

def to8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
