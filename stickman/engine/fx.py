"""Effects.  Everything is a function of time and of things that exist in the shot
(fists, eyes, impact points), so effects move with the bodies and the camera and vanish
at the cut.  Emissive light goes to fr.G (blooms), solid cel shapes to fr.B."""
import math
import cv2
import numpy as np
import skia
from .mathx import V, norm, hash01, fbm1, clamp, smoothstep
from .canvas import paint, poly_path, smooth_path, col
from .camera import W, H
from .theme import T as THEME, PAPER_MODE

PAL = {
    'cyan':   dict(outer=(0.00, 0.50, 0.85), mid=(0.15, 0.85, 1.00), core=(0.80, 1.00, 1.00), glow=(0.10, 0.70, 1.00)),
    'red':    dict(outer=(0.72, 0.00, 0.08), mid=(1.00, 0.18, 0.26), core=(1.00, 0.80, 0.76), glow=(1.00, 0.08, 0.15)),
    'purple': dict(outer=(0.40, 0.08, 0.80), mid=(0.72, 0.38, 1.00), core=(0.95, 0.86, 1.00), glow=(0.60, 0.20, 1.00)),
    'white':  dict(outer=(0.70, 0.75, 0.85), mid=(0.90, 0.93, 1.00), core=(1.00, 1.00, 1.00), glow=(0.80, 0.85, 1.00)),
}
if PAPER_MODE:
    # on paper the neutral hit marks are drawn in ink (manga style); coloured energy is unchanged
    PAL['white'] = dict(outer=(0.10, 0.10, 0.11), mid=(0.14, 0.14, 0.16), core=(0.06, 0.06, 0.07), glow=(0.35, 0.35, 0.38))

# --------------------------------------------------------------------------- noise texture
_rng = np.random.default_rng(7)
_NT = 256


def _make_noise(seed):
    r = np.random.default_rng(seed)
    acc = np.zeros((_NT, _NT), np.float32)
    amp, tot = 1.0, 0.0
    for o, s in enumerate((8, 16, 32, 64)):
        g = r.random((s, s)).astype(np.float32)
        g = np.tile(g, (2, 2))
        up = cv2.resize(g, (_NT * 2, _NT * 2), interpolation=cv2.INTER_CUBIC)[_NT // 2:_NT // 2 + _NT, _NT // 2:_NT // 2 + _NT]
        acc += amp * up
        tot += amp
        amp *= 0.55
    acc /= tot
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    return acc


NOISE = [_make_noise(s) for s in (1, 2, 3)]
NOISE2 = [np.tile(n, (2, 2)) for n in NOISE]


def sample_noise(k, x, y):
    """sample tileable noise k at float arrays x, y (in texture pixels)"""
    xm = np.mod(x, _NT).astype(np.float32)
    ym = np.mod(y, _NT).astype(np.float32)
    return cv2.remap(NOISE2[k], xm, ym, cv2.INTER_LINEAR)


# --------------------------------------------------------------------------- flames
class Flame:
    """Cursed-energy flame wrapped around a moving source (fist / forearm / foot).
    Particles are emitted on a fixed time grid.  A particle of age `a` sits where the source
    was `a * trail` seconds ago (plus its own rise and jitter): it stays attached to the fist,
    trails behind fast motion, and gathers back on the fist as soon as the fist stops -
    nothing keeps flying off on its own."""

    def __init__(self, src, pal='cyan', size=0.10, life=0.26, rate=480.0, rise=1.1, jitter=0.35,
                 src2=None, seg=(0.5, 1.0), amount=1.0, seed=0, trail=0.35, up=None, amp=0.34):
        self.src, self.src2, self.seg = src, src2, seg
        self.pal, self.size, self.life, self.rate = pal, size, life, rate
        self.rise, self.jitter, self.seed = rise, jitter, seed
        self.amount = amount if callable(amount) else (lambda t, a=amount: a)
        self.trail, self.amp = trail, amp
        self.up = (lambda t: V(0, 1, 0)) if up is None else (up if callable(up) else (lambda t, u=norm(np.asarray(up, float)): u))
        self._g1, self._g2 = {}, {}

    def _grid(self, fn, cache, x, hz=480.0):
        i = math.floor(x * hz)
        f = x * hz - i
        out = []
        for j in (i, i + 1):
            v = cache.get(j)
            if v is None:
                if len(cache) > 20000:
                    cache.clear()
                v = cache[j] = np.asarray(fn(j / hz), dtype=np.float64)
            out.append(v)
        return out[0] * (1 - f) + out[1] * f

    def particles(self, t):
        """-> list of (pos, vel, radius, weight)"""
        dt = 1.0 / self.rate
        k1 = int(math.floor(t / dt))
        k0 = int(math.floor((t - self.life) / dt)) + 1
        out = []
        for k in range(k0, k1 + 1):
            te = k * dt
            a = t - te
            if a < 0:
                continue
            amt = float(self.amount(te))
            if amt <= 0.01:
                continue
            h = lambda j: hash01(self.seed, k, j)
            lf = self.life * (0.55 + 0.6 * h(7))
            if a > lf:
                continue
            ts = t - a * self.trail
            if self.src2 is not None:
                u = self.seg[0] + (self.seg[1] - self.seg[0]) * h(1) ** 0.5
                s = self._grid(self.src2, self._g2, ts) * (1 - u) + self._grid(self.src, self._g1, ts) * u
            else:
                s = self._grid(self.src, self._g1, ts)
            rnd = V(h(2) - 0.5, h(3) - 0.5, h(4) - 0.5) * 2
            off = rnd * self.size * 0.6
            up = self.up(te)
            vel = up * self.rise * (0.5 + 1.0 * h(5)) + rnd * self.jitter * self.size * 3.0
            p = s + off + vel * a + up * (self.rise * 1.2 * a * a)
            vnow = vel + up * (self.rise * 2.4 * a)
            # apparent motion of the particle on screen includes the source's drift
            vs = (self._grid(self.src, self._g1, ts) - self._grid(self.src, self._g1, ts - 0.01)) / 0.01
            vnow = vnow + vs * (1 - self.trail) * 0.5
            lu = a / lf
            r = self.size * (0.6 + 0.7 * h(6)) * (1 - lu) ** 0.8 * (0.5 + 0.5 * min(1.0, amt))
            young = max(0.0, 1.0 - lu / 0.18)
            out.append((p, vnow, r, self.amp * min(1.0, amt) * (1 - lu * 0.3), young))
        return out


def render_flames(fr, cs, flames, t, fscale=0.25, opacity=0.95, glow=0.85, edge=0.04, warp=1.0):
    """rasterise all flames of the same palette as a field, warp with flowing noise and cut
    into flat cel bands (outer / mid / core)."""
    by_pal = {}
    for f in flames:
        by_pal.setdefault(f.pal, []).append(f)
    for pal, fl in by_pal.items():
        _render_pal(fr, cs, fl, t, PAL[pal], fscale, opacity, glow, edge, warp)


def _render_pal(fr, cs, flames, t, pal, fs, opacity, glow, edge, warp):
    w, h = int(W * fs), int(H * fs)
    F = np.zeros((h, w), np.float32)
    Fc = np.zeros((h, w), np.float32)
    pts = []
    for f in flames:
        for p, v, r, wt, yg in f.particles(t):
            q = cs.proj(p)
            if not np.isfinite(q[0]) or q[2] < 0.08:
                continue
            sc = cs.scale(q[2])
            rp = r * sc * fs
            if rp < 0.25:
                continue
            q2 = cs.proj(p + v * 0.01)
            dv = (q2[:2] - q[:2]) if np.isfinite(q2[0]) else np.zeros(2)
            pts.append((q[0] * fs, q[1] * fs, rp, wt, dv[0], dv[1], yg))
    if not pts:
        return
    P = np.array(pts)
    x0 = int(max(0, np.min(P[:, 0] - 4 * P[:, 2]) - 8)); x1 = int(min(w, np.max(P[:, 0] + 4 * P[:, 2]) + 8))
    y0 = int(max(0, np.min(P[:, 1] - 4 * P[:, 2]) - 8)); y1 = int(min(h, np.max(P[:, 1] + 4 * P[:, 2]) + 8))
    if x1 <= x0 or y1 <= y0:
        return
    for (cx, cy, rp, wt, vx, vy, yg) in pts:
        # anisotropic gaussian stretched along the particle's motion (tongue shape)
        sp = math.hypot(vx, vy)
        if sp > 1e-6:
            ux, uy = vx / sp, vy / sp
        else:
            ux, uy = 0.0, -1.0
        stretch = 1.0 + min(1.6, sp * fs * 0.25)
        sa, sb = rp * 0.7 * stretch, rp * 0.6
        R = int(3 * max(sa, sb)) + 2
        ax0, ax1 = max(0, int(cx) - R), min(w, int(cx) + R + 1)
        ay0, ay1 = max(0, int(cy) - R), min(h, int(cy) + R + 1)
        if ax1 <= ax0 or ay1 <= ay0:
            continue
        xs = np.arange(ax0, ax1, dtype=np.float32) - cx
        ys = np.arange(ay0, ay1, dtype=np.float32) - cy
        X, Y = xs[None, :], ys[:, None]
        u = X * ux + Y * uy
        v = -X * uy + Y * ux
        g = np.exp(-(u * u) / (2 * sa * sa) - (v * v) / (2 * sb * sb))
        F[ay0:ay1, ax0:ax1] += g * wt
        if yg > 0:
            Fc[ay0:ay1, ax0:ax1] += g * (wt * yg)
    Fk = Fc[y0:y1, x0:x1]
    Fc = F[y0:y1, x0:x1]
    hh, ww = Fc.shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    gx, gy = xx + x0, yy + y0
    sc = 3.0 * (0.25 / fs)
    n1 = sample_noise(0, gx * sc, gy * sc + t * 140.0)
    n2 = sample_noise(1, gx * sc * 1.9 + 37, gy * sc * 1.3 + t * 220.0)
    amp = 4.0 * warp * (fs / 0.25)
    mx = (xx + (n1 - 0.5) * amp * 1.4).astype(np.float32)
    my = (yy + (n2 - 0.35) * amp * 2.6).astype(np.float32)
    Fw = cv2.remap(Fc, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    Fw *= (0.70 + 0.6 * n2)
    Fkw = cv2.remap(Fk, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * (0.8 + 0.4 * n1)
    X0, Y0 = int(x0 / fs), int(y0 / fs)
    X1, Y1 = min(W, int(x1 / fs)), min(H, int(y1 / fs))
    if X1 <= X0 or Y1 <= Y0:
        return
    Fu = cv2.resize(Fw, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_CUBIC)
    Fku = cv2.resize(Fkw, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_CUBIC)
    a_out = np.clip((Fu - (0.40 - edge)) / (2 * edge), 0, 1)
    a_mid = np.clip((Fu - (0.95 - edge)) / (2 * edge), 0, 1) * 0.9
    a_core = np.clip((Fku - (1.0 - edge)) / (2 * edge), 0, 1)
    c = np.zeros(Fu.shape + (3,), np.float32)
    c[:] = pal['outer']
    c = c * (1 - a_mid[..., None]) + np.array(pal['mid'], np.float32) * a_mid[..., None]
    c = c * (1 - a_core[..., None]) + np.array(pal['core'], np.float32) * a_core[..., None]
    A = (a_out * opacity)[..., None]
    Bv = fr.B[Y0:Y1, X0:X1, :3]
    fr.B[Y0:Y1, X0:X1, :3] = Bv * (1 - A) + c * A
    fr.G[Y0:Y1, X0:X1, :3] += c * A * glow
    fr.G[Y0:Y1, X0:X1, 3:4] += A * glow
    soft = cv2.resize(cv2.GaussianBlur(np.clip(Fw, 0, 1.5), (0, 0), 12 * fs), (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_LINEAR)
    sk = (soft * 0.25 * glow)[..., None]
    fr.G[Y0:Y1, X0:X1, :3] += sk * np.array(pal['glow'], np.float32)
    fr.G[Y0:Y1, X0:X1, 3:4] += sk


# --------------------------------------------------------------------------- sparks
def sparks(fr, cs, p0, age, n=18, pal='cyan', speed=6.0, life=0.35, seed=0, dirv=None, cone=1.0,
           gravity=-7.0, length=0.05, width=2.2, k=1.0):
    if age < 0 or age > life * 1.6:
        return
    P = PAL[pal]
    dirv = None if dirv is None else norm(np.asarray(dirv, float))
    for i in range(n):
        h = lambda j: hash01(seed, i, j)
        lf = life * (0.5 + 0.8 * h(1))
        if age > lf:
            continue
        rnd = norm(V(h(2) - 0.5, h(3) - 0.5, h(4) - 0.5))
        d = rnd if dirv is None else norm(dirv + rnd * cone)
        v = d * speed * (0.4 + 0.9 * h(5))
        g = V(0, gravity, 0)
        def pos(a):
            # air drag: velocity decays
            dec = (1 - math.exp(-3.0 * a)) / 3.0
            return np.asarray(p0) + v * dec + 0.5 * g * a * a
        a1 = age
        a0 = max(0.0, age - max(0.012, length / max(speed, 0.1)))
        q0, q1 = cs.proj(pos(a0)), cs.proj(pos(a1))
        if not (np.isfinite(q0[0]) and np.isfinite(q1[0])):
            continue
        fade = (1 - age / lf) ** 1.2 * k
        wpx = max(0.8, width * (1 - age / lf) * min(2.0, cs.scale(q1[2]) / 300))
        if PAPER_MODE and pal == 'white':
            fr.b.drawLine(q0[0], q0[1], q1[0], q1[1], paint(P['core'], fade, stroke=wpx * 1.2))
            continue
        fr.g.drawLine(q0[0], q0[1], q1[0], q1[1], paint(P['mid'], fade, stroke=wpx * 2.2, add=True, blur=wpx * 0.8))
        fr.g.drawLine(q0[0], q0[1], q1[0], q1[1], paint(P['core'], fade, stroke=wpx, add=True))


# --------------------------------------------------------------------------- lightning
def bolt_points(a, b, seed, jag=0.18, depth=6):
    pts = [np.asarray(a, float), np.asarray(b, float)]
    amp = float(np.hypot(*(pts[1] - pts[0]))) * jag
    for d in range(depth):
        new = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            m = (p + q) / 2
            dv = q - p
            nrm = np.array([-dv[1], dv[0]]) / (np.hypot(*dv) + 1e-6)
            off = (hash01(seed, d, i) - 0.5) * 2 * amp
            new += [m + nrm * off, q]
        pts = new
        amp *= 0.55
    return np.array(pts)


def bolt(fr, a, b, seed, pal='cyan', width=2.5, k=1.0, jag=0.2, branches=2):
    P = PAL[pal]
    pts = bolt_points(a, b, seed, jag)
    path = poly_path(pts)
    fr.g.drawPath(path, paint(P['glow'], 0.55 * k, stroke=width * 5, add=True, blur=width * 2.5))
    fr.g.drawPath(path, paint(P['mid'], 0.9 * k, stroke=width * 1.8, add=True))
    fr.g.drawPath(path, paint(P['core'], k, stroke=width * 0.8, add=True))
    for j in range(branches):
        i = int(hash01(seed, 99, j) * (len(pts) - 2)) + 1
        base = pts[i]
        L = float(np.hypot(*(np.asarray(b) - np.asarray(a)))) * (0.15 + 0.2 * hash01(seed, 98, j))
        ang = math.atan2(b[1] - a[1], b[0] - a[0]) + (hash01(seed, 97, j) - 0.5) * 2.2
        end = base + np.array([math.cos(ang), math.sin(ang)]) * L
        bp = bolt_points(base, end, seed * 7 + j, jag, 4)
        pth = poly_path(bp)
        fr.g.drawPath(pth, paint(P['mid'], 0.6 * k, stroke=width * 1.1, add=True))
        fr.g.drawPath(pth, paint(P['core'], 0.7 * k, stroke=width * 0.5, add=True))


# --------------------------------------------------------------------------- impact
def impact_burst(fr, x, y, age, size=160.0, pal='white', k=1.0, seed=0, spikes=9, life=0.16, ring=True):
    """hit flash: hot core, sharp star spikes, expanding thin ring"""
    if age < 0:
        return
    P = PAL[pal]
    ink = PAPER_MODE and pal == 'white'
    if ink:
        # manga hit mark: sharp ink spikes and a thin ring, no glow
        if age < life:
            u = age / life
            for i in range(spikes + 4):
                ang = hash01(seed, i) * 2 * math.pi
                L = size * (0.7 + 1.2 * hash01(seed, i, 1)) * (0.7 + 0.5 * u)
                r0 = size * 0.25 * (0.6 + u)
                wd = size * 0.035 * (1 - u)
                ca, sa = math.cos(ang), math.sin(ang)
                pts = [(x + ca * L, y + sa * L), (x + ca * r0 - sa * wd, y + sa * r0 + ca * wd), (x + ca * r0 + sa * wd, y + sa * r0 - ca * wd)]
                fr.b.drawPath(poly_path(pts, closed=True), paint(P['core'], k * (1 - u)))
        if ring and age < life * 2.2:
            u = age / (life * 2.2)
            rr = size * (0.3 + 1.5 * (1 - (1 - u) ** 2.5))
            fr.b.drawCircle(x, y, rr, paint(P['core'], 0.8 * k * (1 - u) ** 1.5, stroke=max(1.0, size * 0.025 * (1 - u))))
        return
    if age < life:
        u = age / life
        core = size * (0.22 + 0.15 * u) * (1 - u) ** 0.5
        fr.g.drawCircle(x, y, core * 1.6, paint(P['glow'], 0.7 * k * (1 - u), add=True, blur=core * 0.7))
        fr.g.drawCircle(x, y, core * 0.6, paint(P['core'], 1.2 * k * (1 - u), add=True, blur=core * 0.12))
        for i in range(spikes):
            ang = hash01(seed, i) * 2 * math.pi
            L = size * (0.6 + 1.1 * hash01(seed, i, 1)) * (0.6 + 0.6 * u) * (1 - u ** 2)
            wd = size * 0.05 * (1 - u)
            ca, sa = math.cos(ang), math.sin(ang)
            pts = [(x + ca * L, y + sa * L), (x - sa * wd, y + ca * wd), (x - ca * wd * 2, y - sa * wd * 2), (x + sa * wd, y - ca * wd)]
            fr.g.drawPath(poly_path(pts, closed=True), paint(P['core'], 1.1 * k * (1 - u), add=True))
    if ring and age < life * 2.2:
        u = age / (life * 2.2)
        rr = size * (0.3 + 1.5 * (1 - (1 - u) ** 2.5))
        fr.g.drawCircle(x, y, rr, paint(P['mid'], 0.9 * k * (1 - u) ** 1.5, stroke=max(1.0, size * 0.05 * (1 - u)), add=True))


def shock_ring_3d(fr, cs, center, normal, age, r0=0.2, r1=2.5, life=0.35, pal='white', k=1.0, width=0.05, n=64):
    if age < 0 or age > life:
        return
    u = age / life
    r = r0 + (r1 - r0) * (1 - (1 - u) ** 2.2)
    nrm = norm(np.asarray(normal, float))
    a = norm(np.cross(nrm, V(0, 1, 0) if abs(nrm[1]) < 0.9 else V(1, 0, 0)))
    b = np.cross(nrm, a)
    pts = [np.asarray(center) + (a * math.cos(2 * math.pi * i / n) + b * math.sin(2 * math.pi * i / n)) * r for i in range(n)]
    Q = cs.proj_many(np.array(pts))
    if np.any(Q[:, 2] < 0.05):
        return
    d = float(np.mean(Q[:, 2]))
    wpx = max(1.0, width * cs.scale(d) * (1 - u))
    P = PAL[pal]
    path = poly_path(Q[:, :2], closed=True)
    if PAPER_MODE and pal == 'white':
        fr.b.drawPath(path, paint(P['core'], 0.7 * k * (1 - u) ** 1.3, stroke=wpx))
        return
    fr.g.drawPath(path, paint(P['glow'], 0.6 * k * (1 - u), stroke=wpx * 3, add=True, blur=wpx))
    fr.g.drawPath(path, paint(P['core'], 0.9 * k * (1 - u) ** 1.3, stroke=wpx, add=True))


def speed_lines(fr, cx, cy, seed, n=90, rin=320.0, color=None, alpha=0.8, width=5.0, layer='b'):
    """manga focus lines converging on (cx, cy)"""
    color = THEME['speed'] if color is None else color
    c = fr.b if layer == 'b' else fr.g
    R = math.hypot(W, H)
    for i in range(n):
        ang = hash01(seed, i) * 2 * math.pi
        r0 = rin * (0.8 + 0.9 * hash01(seed, i, 1))
        wd = width * (0.4 + 1.2 * hash01(seed, i, 2))
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(cx + ca * r0, cy + sa * r0), (cx + ca * R - sa * wd, cy + sa * R + ca * wd), (cx + ca * R + sa * wd, cy + sa * R - ca * wd)]
        c.drawPath(poly_path(pts, closed=True), paint(color, alpha * (0.4 + 0.6 * hash01(seed, i, 3)), add=(layer == 'g')))


def streak_lines(fr, angle, seed, n=40, color=None, alpha=0.35, width=3.0, length=(300, 900), layer='b', band=None):
    """parallel motion streaks (whip pans / dashes)"""
    color = THEME['speed'] if color is None else color
    c = fr.b if layer == 'b' else fr.g
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(n):
        L = length[0] + (length[1] - length[0]) * hash01(seed, i)
        px = hash01(seed, i, 1) * (W + 600) - 300
        py = hash01(seed, i, 2) * H if band is None else band[0] + (band[1] - band[0]) * hash01(seed, i, 2)
        wd = width * (0.4 + 1.0 * hash01(seed, i, 3))
        pts = [(px - ca * L / 2, py - sa * L / 2), (px + ca * L / 2, py + sa * L / 2)]
        c.drawLine(pts[0][0], pts[0][1], pts[1][0], pts[1][1], paint(color, alpha * (0.3 + 0.7 * hash01(seed, i, 4)), stroke=wd, add=(layer == 'g')))


# --------------------------------------------------------------------------- post effects
def two_tone(dark=(0.0, 0.0, 0.0), light=(1.0, 1.0, 1.0), thr=0.33, invert=False, accent=None):
    """impact frame: picture reduced to two flat tones (optionally a third accent tone for
    strongly coloured light)"""
    def fn(img):
        lum = img[..., 0] * 0.3 + img[..., 1] * 0.55 + img[..., 2] * 0.15
        m = np.clip((lum - thr) / 0.04, 0, 1)
        if invert:
            m = 1 - m
        out = np.array(dark, np.float32) * (1 - m[..., None]) + np.array(light, np.float32) * m[..., None]
        if accent is not None:
            ac, chan = accent
            sat = img[..., chan] - 0.5 * (img[..., (chan + 1) % 3] + img[..., (chan + 2) % 3])
            am = np.clip((sat - 0.25) / 0.05, 0, 1)
            out = out * (1 - am[..., None]) + np.array(ac, np.float32) * am[..., None]
        return out
    return fn


_GRID = {}


def radial_warp(cx, cy, radius, width, amp):
    """shockwave refraction: pixels in a ring pushed outward (only the ring's box is touched)"""
    def fn(img):
        h, w = img.shape[:2]
        R = radius + 3 * width
        x0, x1 = int(max(0, cx - R)), int(min(w, cx + R))
        y0, y1 = int(max(0, cy - R)), int(min(h, cy + R))
        if x1 - x0 < 4 or y1 - y0 < 4:
            return img
        key = (h, w)
        if key not in _GRID:
            _GRID[key] = np.mgrid[0:h, 0:w].astype(np.float32)
        yy, xx = _GRID[key][0][y0:y1, x0:x1], _GRID[key][1][y0:y1, x0:x1]
        dx, dy = xx - np.float32(cx), yy - np.float32(cy)
        r = np.sqrt(dx * dx + dy * dy) + 1e-3
        k = np.exp(-((r - radius) / width) ** 2) * amp
        mx = (xx - dx / r * k).astype(np.float32)
        my = (yy - dy / r * k).astype(np.float32)
        out = img.copy()
        out[y0:y1, x0:x1] = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return out
    return fn


def flash(fr, color=(1, 1, 1), k=0.5):
    fr.G[..., :3] += np.array(color, np.float32) * k
    fr.G[..., 3] += k


def chroma_split(amount_px):
    def fn(img):
        if amount_px < 0.5:
            return img
        out = img.copy()
        M1 = np.float32([[1, 0, amount_px], [0, 1, 0]])
        M2 = np.float32([[1, 0, -amount_px], [0, 1, 0]])
        out[..., 0] = cv2.warpAffine(img[..., 0], M1, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)
        out[..., 2] = cv2.warpAffine(img[..., 2], M2, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)
        return out
    return fn


def whip_blur(dx, dy):
    """directional blur for whip pans (in pixels); long blurs are done at half resolution"""
    def fn(img):
        L = int(max(abs(dx), abs(dy)))
        if L < 2:
            return img
        if L > 3:
            h, w = img.shape[:2]
            small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
            out = whip_blur(dx / 2, dy / 2)(small)
            return cv2.resize(out, (w, h), interpolation=cv2.INTER_LINEAR)
        k = np.zeros((2 * L + 1, 2 * L + 1), np.float32)
        n = 2 * L + 1
        for i in range(n):
            u = i / (n - 1) - 0.5
            x = int(round(L + u * dx)); y = int(round(L + u * dy))
            k[y, x] = 1
        k /= k.sum()
        return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)
    return fn


# --------------------------------------------------------------------------- Red / Blue / Purple
def orb(fr, cs, P, r, pal, t, spin=1.0, k=1.0, seed=0, arcs=4, trail=None):
    """a technique orb: solid glowing body, tight halo, bright arcs that wrap the sphere and
    turn with it (only the orb itself spins), optional light trail along its own path.
    trail: list of earlier world positions (oldest first)."""
    q = cs.proj(P)
    if not np.isfinite(q[0]) or q[2] < 0.05:
        return
    P = np.asarray(P, float)
    rp = r * cs.scale(q[2])
    C = PAL[pal]
    if trail:
        pts = [cs.proj(p) for p in list(trail) + [P]]
        pts = [p for p in pts if np.isfinite(p[0])]
        n = len(pts)
        for i in range(n - 1):
            u = (i + 1) / n
            w = rp * 1.4 * u
            fr.g.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                          paint(C['glow'], 0.35 * k * u, stroke=w, add=True, blur=w * 0.4))
    # halo
    fr.g.drawCircle(q[0], q[1], rp * 2.4, paint(C['glow'], 0.45 * k, add=True, blur=rp * 1.1))
    fr.g.drawCircle(q[0], q[1], rp * 1.35, paint(C['mid'], 0.55 * k, add=True, blur=rp * 0.35))
    # body: radial gradient core -> mid -> outer
    pb = skia.Paint(AntiAlias=True)
    pb.setShader(skia.GradientShader.MakeRadial(skia.Point(q[0] - rp * 0.15, q[1] - rp * 0.15), rp * 1.05,
                                                [col(C['core'], 1.0, 1.6), col(C['mid'], 1.0, 1.25), col(C['outer'], 1.0, 1.0)],
                                                [0.0, 0.45, 1.0]))
    pb.setAlphaf(float(min(1.0, k)))
    fr.b.drawCircle(q[0], q[1], rp, pb)
    fr.g.drawCircle(q[0], q[1], rp * 0.6, paint(C['core'], 0.6 * k, add=True, blur=rp * 0.3))
    # wrapping arcs that rotate with the sphere
    for j in range(arcs):
        ax = norm(V(hash01(seed, j, 1) - 0.5, hash01(seed, j, 2) - 0.5, hash01(seed, j, 3) - 0.5))
        u = norm(np.cross(ax, V(0, 1, 0.3)))
        v = np.cross(ax, u)
        ph = spin * t * (5.0 + 3.0 * hash01(seed, j, 4)) + 6.28 * hash01(seed, j, 5)
        span = 1.2 + 1.2 * hash01(seed, j, 6)
        ptsw = []
        for i in range(14):
            th = ph + span * i / 13
            ptsw.append(P + (u * math.cos(th) + v * math.sin(th)) * r * 1.08)
        Q = cs.proj_many(np.array(ptsw))
        front = [(np.dot(norm(pw - P), cs.pos - P) > 0) for pw in ptsw]
        seg = [Q[i][:2] for i in range(14) if front[i]]
        if len(seg) >= 2:
            fr.g.drawPath(poly_path(seg), paint(C['core'], 0.9 * k, stroke=max(1.2, rp * 0.07), add=True))
            fr.g.drawPath(poly_path(seg), paint(C['mid'], 0.5 * k, stroke=max(2.0, rp * 0.2), add=True, blur=rp * 0.08))


def defocus(sigma):
    def fn(img):
        if sigma < 0.4:
            return img
        return cv2.GaussianBlur(img, (0, 0), sigma)
    return fn


def light_wash(fr, x, y, radius, colr, k, layer='b'):
    """broad soft light from a source position on screen.  layer 'b': part of the backdrop
    (drawn before the figures, so they stay solid in front of it); 'g': light on top"""
    if layer == 'b':
        fr.b.drawCircle(x, y, radius, paint(colr, min(1.0, k), blur=radius * 0.5))
    else:
        fr.g.drawCircle(x, y, radius, paint(colr, k, add=True, blur=radius * 0.5))
