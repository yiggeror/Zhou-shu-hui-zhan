"""Minimal 3D environments: sky gradient, ground plane with line markings, box buildings
with lit window strips, soft contact shadows.  Everything is projected through the shot
camera, so camera moves produce real parallax."""
import math
import numpy as np
import skia
from .mathx import V, norm, hash01, clamp
from .canvas import paint, poly_path, col
from .camera import W, H
from .theme import T as THEME, PAPER_MODE


def clip_poly_near(cs, pts, near=0.06):
    """Sutherland-Hodgman clip of a 3D polygon against the camera near plane -> 2D points"""
    C = [cs.to_cam(p) for p in pts]
    out = []
    n = len(C)
    for i in range(n):
        a, b = C[i], C[(i + 1) % n]
        ina, inb = a[2] >= near, b[2] >= near
        if ina:
            out.append(a)
        if ina != inb:
            u = (near - a[2]) / (b[2] - a[2])
            out.append(a + (b - a) * u)
    if len(out) < 3:
        return None
    res = []
    for c in out:
        res.append((W / 2 + cs.sx + cs.focal * c[0] / c[2], H / 2 + cs.sy - cs.focal * c[1] / c[2]))
    return np.array(res)


def mixc(a, b, u):
    return tuple(float(a[i] * (1 - u) + b[i] * u) for i in range(3))


class Sky:
    """top=None: the bare paper"""
    def __init__(self, top=None, horizon=None, glow=None):
        self.top, self.horizon, self.glow = top, horizon, glow

    def draw(self, fr, cs):
        # horizon height on screen from the camera pitch
        hz = H / 2 + cs.sy + cs.focal * (cs.f[1] / max(1e-3, math.hypot(cs.f[0], cs.f[2])))
        if self.top is None:
            fr.b.clear(col(THEME['bg']))
            return hz
        y0 = hz - H * 0.9
        p = skia.Paint()
        p.setShader(skia.GradientShader.MakeLinear(
            [skia.Point(0, y0), skia.Point(0, hz)],
            [col(self.top), col(self.horizon)]))
        fr.b.drawRect(skia.Rect(0, 0, W, H), p)
        return hz


class Ground:
    def __init__(self, color=None, far_color=None, y=0.0, lines=(), line_color=None):
        color = THEME['ground'] if color is None else color
        far_color = THEME['ground_far'] if far_color is None else far_color
        line_color = THEME['env_line'] if line_color is None else line_color
        self.color, self.far_color, self.y = color, far_color, y
        self.lines = list(lines)   # list of (p0, p1, width_m, alpha)
        self.line_color = line_color

    def draw(self, fr, cs, extent=400.0):
        y = self.y
        cx, cz = cs.pos[0], cs.pos[2]
        quad = [V(cx - extent, y, cz - extent), V(cx + extent, y, cz - extent),
                V(cx + extent, y, cz + extent), V(cx - extent, y, cz + extent)]
        P = clip_poly_near(cs, quad)
        if P is None:
            return
        # gradient from near (bottom) to far (horizon)
        hz = H / 2 + cs.sy + cs.focal * (cs.f[1] / max(1e-3, math.hypot(cs.f[0], cs.f[2])))
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear(
            [skia.Point(0, hz), skia.Point(0, max(hz + 1, H))], [col(self.far_color), col(self.color)]))
        fr.b.drawPath(poly_path(P, closed=True), p)
        for (a, b, wm, al) in self.lines:
            self.line3d(fr, cs, a, b, wm, al)

    def line3d(self, fr, cs, a, b, wm, al, n=12):
        # subdivide so the width follows perspective
        a, b = np.asarray(a, float), np.asarray(b, float)
        for i in range(n):
            p0 = a + (b - a) * (i / n)
            p1 = a + (b - a) * ((i + 1) / n)
            seg = cs.clip_seg(p0, p1)
            if seg is None:
                continue
            q0, q1 = seg
            d = max((q0[2] + q1[2]) / 2, 0.05)
            w = wm * cs.focal / d
            fog = clamp(d / 120.0, 0, 0.85)
            fr.b.drawLine(float(q0[0]), float(q0[1]), float(q1[0]), float(q1[1]),
                          paint(self.line_color, al * (1 - fog), stroke=max(min(w, 6.0), 0.8), cap='round'))


class Building:
    def __init__(self, x0, x1, z0, z1, h, base=0.0, color=None, win=None,
                 win_density=0.55, seed=0, win_k=0.55, style='strips', ink=False):
        if PAPER_MODE and not ink:
            color, win = THEME['env_fill'], THEME['window']
        color = THEME['env_fill'] if color is None else color
        win = THEME['window'] if win is None else win
        self.ink = ink
        self.b = (x0, x1, z0, z1)
        self.h, self.base = h, base
        self.color, self.win, self.win_density, self.seed = color, win, win_density, seed
        self.win_k, self.style = win_k, style

    def center(self):
        x0, x1, z0, z1 = self.b
        return V((x0 + x1) / 2, self.base + self.h / 2, (z0 + z1) / 2)

    def faces(self):
        x0, x1, z0, z1 = self.b
        y0, y1 = self.base, self.base + self.h
        return [
            ('s', [V(x0, y0, z0), V(x1, y0, z0), V(x1, y1, z0), V(x0, y1, z0)], V(0, 0, -1)),
            ('n', [V(x1, y0, z1), V(x0, y0, z1), V(x0, y1, z1), V(x1, y1, z1)], V(0, 0, 1)),
            ('w', [V(x0, y0, z1), V(x0, y0, z0), V(x0, y1, z0), V(x0, y1, z1)], V(-1, 0, 0)),
            ('e', [V(x1, y0, z0), V(x1, y0, z1), V(x1, y1, z1), V(x1, y1, z0)], V(1, 0, 0)),
            ('t', [V(x0, y1, z0), V(x1, y1, z0), V(x1, y1, z1), V(x0, y1, z1)], V(0, 1, 0)),
        ]

    def draw(self, fr, cs, fog_color=(0.07, 0.09, 0.14), fog_dist=140.0, light=V(-0.5, 0.3, -0.8),
             occlude_glow=True, win_mult=1.0):
        c = self.center()
        self.fog_c = fog_color
        dist = float(np.linalg.norm(c - cs.pos))
        fog = clamp(dist / fog_dist, 0, 0.9) ** 1.2
        for name, quad, n in self.faces():
            if np.dot(n, cs.pos - quad[0]) <= 0:
                continue
            P = clip_poly_near(cs, quad)
            if P is None:
                continue
            if self.ink:
                # flat silhouette (backlit city): one colour, no edges, no windows
                path = poly_path(P, closed=True)
                fr.b.drawPath(path, paint(mixc(self.color, fog_color, fog * 0.5), 1.0))
                if occlude_glow:
                    fr.g.drawPath(path, paint((0, 0, 0), 1.0, erase=True))
                continue
            if PAPER_MODE and not self.ink:
                shade = 0.97 + 0.03 * float(np.dot(n, norm(light)))
                fog_color = THEME['bg']
            else:
                shade = 0.75 + 0.35 * float(np.dot(n, norm(light)))
            base = tuple(min(1.0, ch * shade) for ch in self.color)
            colr = mixc(base, fog_color, fog)
            path = poly_path(P, closed=True)
            fr.b.drawPath(path, paint(colr, 1.0))
            if occlude_glow:
                fr.g.drawPath(path, paint((0, 0, 0), 1.0, erase=True))
            if PAPER_MODE and not self.ink:
                fr.b.drawPath(path, paint(mixc(THEME['env_edge'], THEME['bg'], fog), 1.0, stroke=1.6))
            else:
                edge = tuple(min(1.0, ch * 1.35 + 0.04) for ch in self.color)
                fr.b.drawPath(path, paint(mixc(edge, fog_color, fog), 0.7, stroke=1.2))
            self.fog_c = fog_color
            if name != 't' and self.win_density > 0:
                self._windows(fr, cs, quad, name, fog, win_mult)

    def _windows(self, fr, cs, quad, name, fog, win_mult):
        if self.style == 'vstrips':
            return self._vstrips(fr, cs, quad, name, fog, win_mult)
        a, b, c_, d = quad  # bottom-left, bottom-right, top-right, top-left (as seen from outside)
        width = float(np.linalg.norm(b - a))
        height = float(np.linalg.norm(d - a))
        floors = max(1, int(height / 3.6))
        cols = max(1, int(width / 2.2))
        ex, ey = (b - a) / width, (d - a) / height
        seed = self.seed * 131 + ord(name)
        wc = mixc(self.win, self.fog_c, fog * 0.8)
        for f in range(floors):
            if hash01(seed, f, 7) > self.win_density + 0.25:
                continue
            y0 = (f + 0.30) * height / floors
            y1 = (f + 0.70) * height / floors
            if self.style == 'strips':
                # one or two long lit strips per floor
                c0 = 0
                while c0 < cols:
                    run = 1 + int(hash01(seed, f, c0) * 5)
                    lit = hash01(seed, f, c0, 3) < self.win_density
                    if lit:
                        x0 = (c0 + 0.12) * width / cols
                        x1 = (min(cols, c0 + run) - 0.12) * width / cols
                        pts = [a + ex * x0 + ey * y0, a + ex * x1 + ey * y0, a + ex * x1 + ey * y1, a + ex * x0 + ey * y1]
                        P = clip_poly_near(cs, pts)
                        if P is not None:
                            if PAPER_MODE and not self.ink:
                                fr.b.drawPath(poly_path(P, closed=True), paint(THEME['window'], 0.5 * (1 - fog)))
                            else:
                                br = (0.45 + 0.55 * hash01(seed, f, c0, 9)) * self.win_k * win_mult
                                fr.b.drawPath(poly_path(P, closed=True), paint(wc, 1.0, k=br))
                    c0 += run
            elif self.style == 'vstrips':
                pass
            else:
                for ci in range(cols):
                    if hash01(seed, f, ci, 5) > self.win_density:
                        continue
                    x0 = (ci + 0.2) * width / cols
                    x1 = (ci + 0.8) * width / cols
                    pts = [a + ex * x0 + ey * y0, a + ex * x1 + ey * y0, a + ex * x1 + ey * y1, a + ex * x0 + ey * y1]
                    P = clip_poly_near(cs, pts)
                    if P is not None:
                        if PAPER_MODE and not self.ink:
                            fr.b.drawPath(poly_path(P, closed=True), paint(THEME['window'], 0.5 * (1 - fog)))
                            continue
                        br = (0.45 + 0.55 * hash01(seed, f, ci, 9)) * self.win_k * win_mult
                        fr.b.drawPath(poly_path(P, closed=True), paint(wc, 1.0, k=br))


def _vstrips(self, fr, cs, quad, name, fog, win_mult):
    """tall lit window columns, like the office blocks in the original street scenes"""
    a, b, c_, d = quad
    width = float(np.linalg.norm(b - a))
    height = float(np.linalg.norm(d - a))
    ex, ey = (b - a) / width, (d - a) / height
    cols = max(1, int(width / 1.6))
    seed = self.seed * 131 + ord(name)
    wc = mixc(self.win, self.fog_c, fog * 0.8)
    for ci in range(cols):
        if hash01(seed, ci, 1) > self.win_density:
            continue
        x0 = (ci + 0.28) * width / cols
        x1 = (ci + 0.72) * width / cols
        y0 = height * (0.08 + 0.35 * hash01(seed, ci, 2) ** 2)
        y1 = height * (0.65 + 0.33 * hash01(seed, ci, 3))
        pts = [a + ex * x0 + ey * y0, a + ex * x1 + ey * y0, a + ex * x1 + ey * y1, a + ex * x0 + ey * y1]
        P = clip_poly_near(cs, pts)
        if P is None:
            continue
        if PAPER_MODE and not self.ink:
            fr.b.drawPath(poly_path(P, closed=True), paint(THEME['window'], 0.45 * (1 - fog)))
            continue
        br = (0.55 + 0.45 * hash01(seed, ci, 9)) * self.win_k * win_mult
        fr.b.drawPath(poly_path(P, closed=True), paint(wc, 1.0, k=br))
        # thin dark mullions across the strip
        nfl = max(1, int((y1 - y0) / 3.4))
        for fl in range(1, nfl):
            yy = y0 + (y1 - y0) * fl / nfl
            q = clip_poly_near(cs, [a + ex * x0 + ey * (yy - 0.12), a + ex * x1 + ey * (yy - 0.12), a + ex * x1 + ey * (yy + 0.12), a + ex * x0 + ey * (yy + 0.12)])
            if q is not None:
                fr.b.drawPath(poly_path(q, closed=True), paint(mixc(self.color, self.fog_c, fog), 1.0))


Building._vstrips = _vstrips


def draw_buildings(fr, cs, blds, **kw):
    order = sorted(blds, key=lambda b: -float(np.linalg.norm(b.center() - cs.pos)))
    for b in order:
        b.draw(fr, cs, **kw)


def contact_shadow(fr, cs, J, k=1.0, y=0.0, alpha=None):
    """soft dark blob on the ground under the feet and pelvis"""
    if alpha is None:
        alpha = THEME['shadow_alpha'] * 2.2
    if alpha <= 0:
        return
    for key, r, a in (('Tl', 0.16, 0.6), ('Tr', 0.16, 0.6), ('P', 0.38, 0.45)):
        p = np.array(J[key], float)
        hgt = max(0.0, p[1] - y)
        if key == 'P':
            hgt = max(0.0, hgt - 0.85 * k)
        fade = clamp(1 - hgt / 1.2, 0, 1)
        if fade <= 0:
            continue
        c = V(p[0], y, p[2])
        q = cs.proj(c)
        if q[2] < 0.1:
            continue
        s = cs.scale(q[2])
        rx = r * k * s * (1 + hgt)
        # squash with the view angle onto the ground
        tilt = abs(float(norm(cs.pos - c)[1]))
        ry = rx * max(0.12, tilt)
        rect = skia.Rect(q[0] - rx, q[1] - ry, q[0] + rx, q[1] + ry)
        fr.b.drawOval(rect, paint((0, 0, 0), alpha * a * fade, blur=max(1.0, ry * 0.5)))
