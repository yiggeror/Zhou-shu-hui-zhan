"""Pinhole camera driven by channels, with screen-space shake / punch-in on top."""
import math
import numpy as np
from .mathx import V, norm, fbm1
from .anim import as_fn

W, H = 1920, 1080


class Cam:
    def __init__(self, pos, target, fov=40.0, roll=0.0):
        self.pos, self.target, self.fov, self.roll = pos, target, fov, roll
        self.shakes = []   # (t0, amp_px, dur, freq)
        self.drift = 1.0     # slow hand-held float (never perfectly locked off)
        self.punches = []  # (t0, amount, attack, release)
        self.extra_zoom = 1.0

    def shake(self, t0, amp=18.0, dur=0.35, freq=26.0):
        self.shakes.append((t0, amp, dur, freq))
        return self

    def punch(self, t0, amount=0.06, attack=0.04, release=0.30):
        self.punches.append((t0, amount, attack, release))
        return self

    def at(self, t):
        return CamState(self, t)


class CamState:
    def __init__(self, cam, t):
        self.t = t
        self.pos = np.asarray(as_fn(cam.pos)(t), dtype=np.float64)
        tgt = np.asarray(as_fn(cam.target)(t), dtype=np.float64)
        if cam.drift:
            dist = float(np.linalg.norm(tgt - self.pos))
            a = cam.drift * 0.006 * max(1.0, dist)
            self.pos = self.pos + V(fbm1(t * 0.45, 501, 2), fbm1(t * 0.4, 502, 2), fbm1(t * 0.35, 503, 2)) * a
            tgt = tgt + V(fbm1(t * 0.5, 504, 2), fbm1(t * 0.45, 505, 2), 0.0) * a * 1.3
        fov = float(as_fn(cam.fov)(t))
        roll = math.radians(float(as_fn(cam.roll)(t)))
        f = norm(tgt - self.pos)
        r = np.cross(V(0, 1, 0), f)
        if np.linalg.norm(r) < 1e-6:
            r = V(1, 0, 0)
        r = norm(r)
        u = np.cross(f, r)
        cr, sr = math.cos(roll), math.sin(roll)
        self.r = r * cr + u * sr
        self.u = u * cr - r * sr
        self.f = f
        self.focal = (H / 2) / math.tan(math.radians(fov) / 2)
        # screen-space shake & punch-in
        sx = sy = 0.0
        for (t0, amp, dur, fq) in cam.shakes:
            a = t - t0
            if 0 <= a < dur:
                k = amp * (1 - a / dur) ** 2
                sx += k * fbm1(a * fq, 11 + int(t0 * 100))
                sy += k * fbm1(a * fq, 23 + int(t0 * 100))
        z = cam.extra_zoom
        for (t0, amt, att, rel) in cam.punches:
            a = t - t0
            if 0 <= a < att:
                z *= 1 + amt * (a / att)
            elif att <= a < att + rel:
                u_ = (a - att) / rel
                z *= 1 + amt * (1 - u_) ** 2
        self.sx, self.sy, self.zoom = sx, sy, z
        self.focal *= z

    def to_cam(self, p):
        d = np.asarray(p) - self.pos
        return np.array([d @ self.r, d @ self.u, d @ self.f])

    def proj(self, p):
        """-> (x, y, depth). depth<=0 means behind the camera"""
        c = self.to_cam(p)
        z = c[2]
        if z <= 1e-4:
            return np.array([np.nan, np.nan, z])
        return np.array([W / 2 + self.sx + self.focal * c[0] / z,
                         H / 2 + self.sy - self.focal * c[1] / z, z])

    def proj_many(self, P):
        P = np.asarray(P, dtype=np.float64)
        d = P - self.pos
        c = np.stack([d @ self.r, d @ self.u, d @ self.f], -1)
        z = np.maximum(c[..., 2], 1e-4)
        return np.stack([W / 2 + self.sx + self.focal * c[..., 0] / z,
                         H / 2 + self.sy - self.focal * c[..., 1] / z, c[..., 2]], -1)

    def scale(self, depth):
        """pixels per metre at a given depth"""
        return self.focal / max(depth, 1e-4)

    def clip_seg(self, a, b, near=0.05):
        ca, cb = self.to_cam(a), self.to_cam(b)
        if ca[2] < near and cb[2] < near:
            return None
        if ca[2] < near:
            u = (near - ca[2]) / (cb[2] - ca[2]); a = a + (b - a) * u
        elif cb[2] < near:
            u = (near - cb[2]) / (ca[2] - cb[2]); b = b + (a - b) * u
        return self.proj(a), self.proj(b)
