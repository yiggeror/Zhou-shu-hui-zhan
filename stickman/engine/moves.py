"""Choreography helpers: stances, baked run cycles, pose presets (hand positions are in the
chest frame relative to the shoulder: x right, y up, z forward)."""
import math
import numpy as np
from .mathx import V, norm


def fwd(yaw):
    return V(math.sin(yaw), 0, math.cos(yaw))


def right(yaw):
    return V(math.cos(yaw), 0, -math.sin(yaw))


def feet(root_xz, yaw, front=0.35, back=-0.30, width=0.16, lead='l'):
    """world foot positions for a fighting stance around a pelvis ground point"""
    p = V(root_xz[0], 0, root_xz[-1]) if len(root_xz) == 2 else V(root_xz[0], 0, root_xz[2])
    f, r = fwd(yaw), right(yaw)
    if lead == 'l':
        return p + f * front - r * width, p + f * back + r * width
    else:
        return p + f * back - r * width, p + f * front + r * width


def bake_run(actor, t0, t1, path, yaw, freq=2.6, stride_lead=0.32, lift=0.30, base_h=0.86,
             bob=0.05, lean=0.35, first='l', stance_frac=0.38, land_ease='sm'):
    """path(t)->ground point under the pelvis (V with y=0).  Adds root / foot keys."""
    T = 1.0 / freq
    k = actor.fig.k
    f = fwd(yaw)
    # root keys every 1/4 step
    n = int(math.ceil((t1 - t0) * freq * 8))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        ph = ((t - t0) * freq * 2) % 1.0   # half-cycle phase: 0 = a landing
        y = base_h * k - bob * k * math.cos(2 * math.pi * ph)
        actor.k(t, root=path(t) + V(0, y, 0), lean=lean)
    # feet
    for side, off in (('l', 0.0 if first == 'l' else 0.5), ('r', 0.5 if first == 'l' else 0.0)):
        t = t0 + off * T - T
        while t < t1 + T:
            land = t
            lift_t = land + stance_frac * T
            nxt = land + T
            pl = path(min(max(land, t0), t1)) + f * stride_lead * k + right(yaw) * (0.09 if side == 'r' else -0.09) * k
            pn = path(min(max(nxt, t0), t1)) + f * stride_lead * k + right(yaw) * (0.09 if side == 'r' else -0.09) * k
            name = 'foot_' + side
            if t0 - T * 0.5 <= land <= t1:
                actor.k(max(land, t0), **{name: pl})
            if t0 <= lift_t <= t1:
                actor.k(lift_t, **{name: pl})
            mid = (lift_t + nxt) / 2
            if t0 <= mid <= t1:
                pm = pl * 0.45 + pn * 0.55 + V(0, lift * k, 0) - f * 0.05 * k
                actor.k(mid, **{name: pm})
            t = nxt


GUARD = dict(hand_l=V(0.02, -0.05, 0.36), hand_r=V(-0.02, -0.12, 0.28), fist_l=1.0, fist_r=1.0,
             elbow_l=V(-0.7, -0.6, -0.2), elbow_r=V(0.7, -0.6, -0.2))
