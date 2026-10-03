"""Shared helpers for the film sequences."""
import math
import numpy as np
import skia
from engine.mathx import V, norm, hash01, fbm1, clamp, smoothstep
from engine.anim import Ch
from engine.rig import Figure, GOJO, SUKUNA, MAHORAGA, FUSHIGURO, PANDA, DANCER, OLDMAN, GLASSES, PLAIN
from engine.camera import Cam, W, H
from engine.shot import Shot, Actor, draw_actors, cam_blur, set_blur
from engine.canvas import paint, poly_path, smooth_path, col
from engine.theme import T as THEME
from engine import fx
from engine import draw3d as d3
from engine.hand import shape

F24 = 1 / 24.0
PAPER = THEME['bg']
INK = THEME['ink']
GOJO_S = GOJO.but(extras=('scarf',))
SUKUNA_S = SUKUNA


def fr24(f):
    return f / 24.0


def paper(fr, colr=None):
    fr.b.clear(col(PAPER if colr is None else colr))


def fwd(yaw):
    return V(math.sin(yaw), 0, math.cos(yaw))


def rgt(yaw):
    return V(math.cos(yaw), 0, -math.sin(yaw))


def stand(a, t, x, z, yaw, k=None, width=0.15, stagger=0.0, h=0.0, ease='sm', y=0.0, **more):
    """key a relaxed standing pose: pelvis over the feet"""
    k = a.fig.k if k is None else k
    p = V(x, y, z)
    f, r = fwd(yaw), rgt(yaw)
    a.k(t, ease, root=p + V(0, (0.92 - h) * k, 0), yaw=yaw,
        foot_l=p - r * width * k + f * stagger * k, foot_r=p + r * width * k - f * stagger * k, **more)


def walk(a, t0, t1, p0, p1, yaw, freq=1.7, stride=None, lift=0.10, base_h=0.90, bob=0.025, lean=0.06,
         arms=0.16, first='l'):
    """walk with heel-strike feet, bobbing pelvis and counter-swinging arms"""
    k = a.fig.k
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    path = lambda t: p0 + (p1 - p0) * clamp((t - t0) / max(t1 - t0, 1e-6), 0, 1)
    T = 1.0 / freq
    f, r = fwd(yaw), rgt(yaw)
    n = int(math.ceil((t1 - t0) * freq * 8)) + 1
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        ph = ((t - t0) * freq * 2) % 1.0
        y = base_h * k - bob * k * math.cos(2 * math.pi * ph)
        sw = math.sin(2 * math.pi * (t - t0) * freq) * (1 if first == 'l' else -1)
        a.k(t, root=path(t) + V(0, y, 0), lean=lean, twist=0.10 * sw,
            hand_l=V(-0.02, -0.50, 0.08 + arms * sw) * k, hand_r=V(0.02, -0.50, 0.08 - arms * sw) * k)
    for side, off in (('l', 0.0 if first == 'l' else 0.5), ('r', 0.5 if first == 'l' else 0.0)):
        t = t0 + off * T - T
        sx = -1 if side == 'l' else 1
        while t < t1 + T:
            land, lift_t, nxt = t, t + 0.55 * T, t + T
            st = (stride if stride is not None else float(np.linalg.norm(p1 - p0)) / max(1e-6, (t1 - t0) * freq))
            pl = path(min(max(land, t0), t1)) + f * st * 0.35 + r * sx * 0.09 * k
            pn = path(min(max(nxt, t0), t1)) + f * st * 0.35 + r * sx * 0.09 * k
            name = 'foot_' + side
            if t0 - T <= land <= t1:
                a.k(max(land, t0), **{name: pl})
            if t0 <= lift_t <= t1:
                a.k(lift_t, **{name: pl})
            mid = (lift_t + nxt) / 2
            if t0 <= mid <= t1:
                a.k(mid, **{name: (pl + pn) / 2 + V(0, lift * k, 0)})
            t = nxt


def head_cam(a, t, dist=0.7, yaw=0.0, pitch=0.0, side=0.0, up=0.0, fov=36, look_off=V(0, 0, 0)):
    """camera framing a figure's head (relative to its head frame at time t)"""
    J = a.fig.pose(t)
    Hh, Rh = J['H'], J['Rh']
    d = Rh @ V(math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch))
    return Hh + d * dist + Rh @ V(side, up, 0), Hh + look_off


def face_marks(fr, cs, J, fig, k, color=(1.0, 0.12, 0.2), width=1.0):
    """Sukuna's face markings, glowing red lines on the ink head (k = intensity 0..1)"""
    if k <= 0.01:
        return
    R = fig.L['head'] * fig.style.head_k
    Rh, Hc = J['Rh'], J['H']
    strokes = [
        [(-0.62, -0.05), (-0.45, -0.22), (-0.30, -0.48)],
        [(0.62, -0.05), (0.45, -0.22), (0.30, -0.48)],
        [(-0.70, 0.10), (-0.52, 0.0)], [(0.70, 0.10), (0.52, 0.0)],
        [(-0.12, 0.55), (-0.06, 0.32)], [(0.12, 0.55), (0.06, 0.32)], [(0.0, 0.62), (0.0, 0.40)],
    ]
    for st in strokes:
        pts = []
        for (x, y) in st:
            z = math.sqrt(max(0.0, 1 - x * x - y * y))
            pts.append(Hc + Rh @ V(x, y, z) * R * 1.01)
        n = Rh @ V(0, 0, 1)
        if float(n @ norm(cs.pos - Hc)) < 0.1:
            continue
        P = cs.proj_many(np.array(pts))
        if np.any(P[:, 2] < 0.05):
            continue
        d = float(np.mean(P[:, 2]))
        w = max(1.0, 0.0045 * fig.k * cs.scale(d) * width)
        path = poly_path(P[:, :2])
        fr.b.drawPath(path, paint(color, k, stroke=w))
        fr.g.drawPath(path, paint(color, 0.6 * k, stroke=w * 1.8, add=True, blur=w * 0.6))


def mouth(fr, cs, J, fig, k=1.0, smile=0.6, width=0.55, open_=0.0, color=None, y=-0.45):
    """a thin paper-coloured mouth line on the ink head (only for close-ups)"""
    color = PAPER if color is None else color
    R = fig.L['head'] * fig.style.head_k
    Rh, Hc = J['Rh'], J['H']
    n = Rh @ V(0, 0, 1)
    if float(n @ norm(cs.pos - Hc)) < 0.15:
        return
    pts = []
    for i in range(11):
        u = -1 + 2 * i / 10
        x = u * width * 0.5
        yy = y + smile * 0.12 * (u * u - 0.35)
        z = math.sqrt(max(0.0, 1 - x * x - yy * yy))
        pts.append(Hc + Rh @ V(x, yy, z) * R * 1.01)
    P = cs.proj_many(np.array(pts))
    if np.any(P[:, 2] < 0.05):
        return
    w = max(1.0, 0.010 * fig.k * cs.scale(float(np.mean(P[:, 2]))))
    fr.b.drawPath(smooth_path(P[:, :2]), paint(color, k * 0.9, stroke=w))
    if open_ > 0.01:
        lo = []
        for i in range(11):
            u = -1 + 2 * i / 10
            x = u * width * 0.42
            yy = y - open_ * 0.25 * (1 - u * u)
            z = math.sqrt(max(0.0, 1 - x * x - yy * yy))
            lo.append(Hc + Rh @ V(x, yy, z) * R * 1.01)
        Q = cs.proj_many(np.array(lo))
        fr.b.drawPath(poly_path(np.vstack([P[1:-1, :2], Q[::-1][1:-1, :2]]), closed=True), paint(color, k * 0.9))


def wipe_diag(fr, u, ang=-0.45, color=None, reverse=False):
    """an ink slab sweeping across the frame (u: 0..1)"""
    color = INK if color is None else color
    x = -600 + u * (W + 1200)
    sk = math.tan(ang) * H
    if not reverse:
        pts = [(-4000, -10), (x, -10), (x + sk, H + 10), (-4000, H + 10)]
    else:
        pts = [(x, -10), (8000, -10), (8000, H + 10), (x + sk, H + 10)]
    fr.b.drawPath(poly_path(pts, closed=True), paint(color))
    fr.g.drawPath(poly_path(pts, closed=True), paint((0, 0, 0), 1, erase=True))


def flash_white(fr, k, color=None):
    """a flash to paper-white (light fills the frame)"""
    if k <= 0:
        return
    c = (1.0, 1.0, 1.0) if color is None else color
    fr.post.append(lambda img, k=k, c=c: img * (1 - k) + np.array(c, np.float32) * k)


def red_two_tone(fr, invert=False):
    fr.impact = dict(bg=(0.85, 0.03, 0.08) if not invert else INK, fg=INK if not invert else (0.85, 0.03, 0.08),
                     energy=False, thr=0.3)


def skyline(seed, n=40, z0=40, z1=140, spread=160, hmin=8, hmax=40, base=-60, y_top=0.0, ink=False, x0=0.0, z_off=0.0):
    from engine.env import Building
    out = []
    for i in range(n):
        x = x0 + (hash01(seed, i, 1) - 0.5) * spread
        z = z_off + z0 + (z1 - z0) * hash01(seed, i, 2)
        w = 5 + 9 * hash01(seed, i, 3)
        d = 5 + 9 * hash01(seed, i, 4)
        h = hmin + (hmax - hmin) * hash01(seed, i, 5)
        out.append(Building(x - w / 2, x + w / 2, z - d / 2, z + d / 2, (y_top - base) + h, base=base,
                            win_density=0.4, seed=seed * 100 + i, style='vstrips', ink=ink,
                            color=(0.10, 0.10, 0.12) if ink else None))
    return out
