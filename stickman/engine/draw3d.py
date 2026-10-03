"""Pencil-style 3D drawing primitives for sets and props (paper world)."""
import math
import numpy as np
import skia
from .mathx import V, norm, clamp, hash01, fbm1
from .canvas import paint, poly_path, smooth_path, col
from .env import clip_poly_near
from .theme import T as THEME

PENCIL = THEME['env_line']
FILL = THEME['env_fill']
INK = THEME['ink']
PAPER = THEME['bg']


def line3(fr, cs, a, b, color=None, w_m=0.02, alpha=1.0, n=1, min_px=0.8, max_px=40.0, layer='b'):
    color = PENCIL if color is None else color
    c = fr.b if layer == 'b' else fr.g
    a, b = np.asarray(a, float), np.asarray(b, float)
    for i in range(n):
        p0 = a + (b - a) * (i / n)
        p1 = a + (b - a) * ((i + 1) / n)
        seg = cs.clip_seg(p0, p1)
        if seg is None:
            continue
        q0, q1 = seg
        d = max((q0[2] + q1[2]) / 2, 0.05)
        w = clamp(w_m * cs.focal / d, min_px, max_px)
        c.drawLine(float(q0[0]), float(q0[1]), float(q1[0]), float(q1[1]), paint(color, alpha, stroke=w))


def poly3(fr, cs, pts, fill=None, edge=None, w_m=0.02, alpha=1.0, edge_alpha=1.0, layer='b'):
    P = clip_poly_near(cs, pts)
    if P is None:
        return None
    c = fr.b if layer == 'b' else fr.g
    path = poly_path(P, closed=True)
    if fill is not None:
        c.drawPath(path, paint(fill, alpha))
    if edge is not None:
        d = float(np.mean([cs.to_cam(p)[2] for p in pts]))
        w = clamp(w_m * cs.focal / max(d, 0.05), 0.8, 30)
        c.drawPath(path, paint(edge, alpha * edge_alpha, stroke=w))
    return path


def box(fr, cs, lo, hi, fill=None, edge=None, w_m=0.015, alpha=1.0):
    """axis-aligned box, visible faces only, pencil edges"""
    fill = FILL if fill is None else fill
    edge = PENCIL if edge is None else edge
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    faces = [
        ([V(x0, y0, z0), V(x1, y0, z0), V(x1, y1, z0), V(x0, y1, z0)], V(0, 0, -1)),
        ([V(x1, y0, z1), V(x0, y0, z1), V(x0, y1, z1), V(x1, y1, z1)], V(0, 0, 1)),
        ([V(x0, y0, z1), V(x0, y0, z0), V(x0, y1, z0), V(x0, y1, z1)], V(-1, 0, 0)),
        ([V(x1, y0, z0), V(x1, y0, z1), V(x1, y1, z1), V(x1, y1, z0)], V(1, 0, 0)),
        ([V(x0, y1, z0), V(x1, y1, z0), V(x1, y1, z1), V(x0, y1, z1)], V(0, 1, 0)),
        ([V(x0, y0, z1), V(x1, y0, z1), V(x1, y0, z0), V(x0, y0, z0)], V(0, -1, 0)),
    ]
    for q, n in faces:
        if np.dot(n, cs.pos - q[0]) <= 0:
            continue
        poly3(fr, cs, q, fill=fill, edge=edge, w_m=w_m, alpha=alpha)


def grid_on_plane(fr, cs, o, ex, ey, nx, ny, cw, ch, inset=0.08, color=None, w_m=0.012, alpha=1.0, fill=None):
    """rows of rectangles on a plane (drawers, windows, tiles)"""
    color = PENCIL if color is None else color
    ex, ey = norm(np.asarray(ex, float)), norm(np.asarray(ey, float))
    for i in range(nx):
        for j in range(ny):
            a = o + ex * (i * cw + inset) + ey * (j * ch + inset)
            pts = [a, a + ex * (cw - 2 * inset), a + ex * (cw - 2 * inset) + ey * (ch - 2 * inset), a + ey * (ch - 2 * inset)]
            poly3(fr, cs, pts, fill=fill, edge=color, w_m=w_m, alpha=alpha)


def wash(fr, colr, alpha, y0=0.0, y1=1.0, layer='b'):
    """flat watercolour wash over the whole frame (vertical gradient of alpha)"""
    W, H = fr.w, fr.h
    p = skia.Paint()
    c0 = col(colr, alpha * (1 - y0))
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                               [col(colr, alpha * y1), col(colr, alpha * y0)]))
    (fr.b if layer == 'b' else fr.g).drawRect(skia.Rect(0, 0, W, H), p)


def letterbox(fr, frac=0.1, color=None):
    color = INK if color is None else color
    W, H = fr.w, fr.h
    h = H * frac
    fr.b.drawRect(skia.Rect(0, 0, W, h), paint(color))
    fr.b.drawRect(skia.Rect(0, H - h, W, H), paint(color))
    fr.g.drawRect(skia.Rect(0, 0, W, h), paint((0, 0, 0), 1.0, erase=True))
    fr.g.drawRect(skia.Rect(0, H - h, W, H), paint((0, 0, 0), 1.0, erase=True))


def ribbon(fr, cs, pts, w_m, color=None, alpha=1.0, taper=0.4):
    """thick flowing ribbon through 3D points (scarf ends, cloth)"""
    color = INK if color is None else color
    P = cs.proj_many(np.array(pts))
    if np.any(P[:, 2] < 0.05):
        return
    n = len(P)
    for i in range(n - 1):
        u = i / max(1, n - 2)
        d = (P[i, 2] + P[i + 1, 2]) / 2
        w = max(1.0, w_m * cs.focal / d * (1 - taper * u))
        fr.b.drawLine(P[i, 0], P[i, 1], P[i + 1, 0], P[i + 1, 1], paint(color, alpha, stroke=w))


def smoke(fr, cs, src, t, seed=0, k=1.0, color=(0.55, 0.55, 0.58), n=6, rise=0.18, wind=V(0.05, 0, 0)):
    """thin cigarette smoke wisps rising and curling"""
    for i in range(n):
        ph = (t * 0.35 + i / n) % 1.0
        pts = []
        for j in range(10):
            u = j / 9
            age = ph * 1.0 + u * 0.6
            p = np.asarray(src) + V(0, rise * (u * 2.5 + ph), 0) + wind * (u + ph) * 2 \
                + V(fbm1(t * 0.8 + u * 3 + i, seed + i) * 0.05 * u, 0, fbm1(t * 0.7 + u * 2, seed + 9 + i) * 0.04 * u)
            pts.append(p)
        P = cs.proj_many(np.array(pts))
        if np.any(P[:, 2] < 0.05):
            continue
        a = k * 0.5 * math.sin(math.pi * ph)
        fr.b.drawPath(smooth_path(P[:, :2]), paint(color, a, stroke=1.6))


def rot3(yaw, pitch, roll):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def cube(fr, cs, c, size, R, fill=None, edge=None, w_m=0.01, alpha=1.0):
    """a rotated cube (debris)"""
    fill = INK if fill is None else fill
    h = size / 2
    faces = [((0, 0, -1), [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)]),
             ((0, 0, 1), [(-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1)]),
             ((-1, 0, 0), [(-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)]),
             ((1, 0, 0), [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)]),
             ((0, -1, 0), [(-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)]),
             ((0, 1, 0), [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)])]
    c = np.asarray(c, float)
    for n, q in faces:
        nw = R @ np.array(n, float)
        pts = [c + R @ (np.array(v, float) * h) for v in q]
        if np.dot(nw, cs.pos - pts[0]) <= 0:
            continue
        shade = 0.85 + 0.15 * nw[1]
        f = tuple(min(1.0, x * shade + (0.08 if fill is INK else 0) * (1 - shade)) for x in fill)
        poly3(fr, cs, pts, fill=f, edge=edge, w_m=w_m, alpha=alpha)
