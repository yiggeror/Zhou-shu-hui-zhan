"""Hands.  A hand is a palm + five three-joint fingers driven by curl values, built in a
wrist frame (x: across the knuckles toward the thumb side for a right hand, y: along the
fingers, z: out of the back of the hand).  Drawn in ink like the rest of the figure.
Used for hand close-ups and, at mid range, automatically for figures' hands."""
import math
import numpy as np
import skia
from .mathx import V, norm, clamp
from .canvas import paint, poly_path, smooth_path

# shape vectors: (thumb, index, middle, ring, pinky, spread)
SHAPES = {
    'fist':   (0.85, 1.0, 1.0, 1.0, 1.0, 0.0),
    'open':   (0.05, 0.05, 0.05, 0.05, 0.08, 0.7),
    'relax':  (0.35, 0.30, 0.38, 0.45, 0.52, 0.25),
    'flat':   (0.15, 0.0, 0.0, 0.0, 0.0, 0.0),
    'claw':   (0.45, 0.55, 0.55, 0.6, 0.65, 0.8),
    'point':  (0.8, 0.0, 1.0, 1.0, 1.0, 0.0),
    'two':    (0.85, 0.0, 0.0, 1.0, 1.0, 0.0),     # Gojo's two-finger sign
    'pluck':  (0.30, 0.55, 0.25, 0.35, 0.45, 0.35),
    'grip':   (0.60, 0.75, 0.80, 0.85, 0.9, 0.1),
    'pinch':  (0.55, 0.42, 0.45, 0.92, 0.97, 0.0),
}


def shape(name):
    return np.array(SHAPES[name], dtype=np.float64)


# finger layout in the wrist frame (right hand): base x, base y, segment lengths, splay angle
FINGERS = [
    # thumb starts low on the side, angled outward
    dict(bx=0.040, by=0.025, L=(0.040, 0.032, 0.026), splay=0.75, thumb=True),
    dict(bx=0.030, by=0.090, L=(0.042, 0.026, 0.020), splay=0.10),
    dict(bx=0.010, by=0.094, L=(0.046, 0.029, 0.021), splay=0.0),
    dict(bx=-0.010, by=0.090, L=(0.043, 0.027, 0.020), splay=-0.08),
    dict(bx=-0.028, by=0.082, L=(0.034, 0.022, 0.018), splay=-0.18),
]


def hand_points(W, R, sh, side=1, k=1.0):
    """W: wrist world position, R: 3x3 hand frame (columns x, y, z), sh: shape vector,
    side: 1 right hand, -1 left hand (mirrored in x).  Returns palm polygon and finger chains."""
    s = np.asarray(sh, dtype=np.float64)
    spread = s[5]
    ex, ey, ez = R[:, 0] * side, R[:, 1], R[:, 2]
    def P(x, y, z=0.0):
        return W + (ex * x + ey * y + ez * z) * k
    palm = [P(0.030, -0.004), P(0.046, 0.040), P(0.040, 0.094), P(-0.036, 0.088), P(-0.040, 0.020), P(-0.026, -0.008)]
    chains = []
    for i, f in enumerate(FINGERS):
        curl = clamp(s[i], 0, 1)
        if f.get('thumb'):
            ang = f['splay'] + 0.5 * spread - 0.65 * curl
            d = V(math.sin(ang), math.cos(ang), 0.0)
            # thumb curls across the palm (toward -x, -z)
            pts = [P(f['bx'], f['by'])]
            cur = np.array([f['bx'], f['by'], 0.0])
            a = 0.0
            for j, L in enumerate(f['L']):
                a += curl * (0.55 if j == 0 else 0.7)
                dd = V(d[0] * math.cos(a) - 0.0, d[1] * math.cos(a), -math.sin(a) * 0.8)
                dd = dd - V(1.0, 0, 0) * curl * 0.35 * (j > 0)
                cur = cur + norm(dd) * L
                pts.append(P(*cur))
            chains.append(pts)
            continue
        ang = f['splay'] * (1 + 2.2 * spread)
        dx, dy = math.sin(ang), math.cos(ang)
        cur = np.array([f['bx'], f['by'], 0.0])
        pts = [P(*cur)]
        bend = 0.0
        for j, L in enumerate(f['L']):
            bend += curl * (1.45 if j == 0 else 1.6)
            # bending folds the finger toward the palm side (-z)
            dd = np.array([dx * math.cos(bend), dy * math.cos(bend), -math.sin(bend)])
            cur = cur + dd * L
            pts.append(P(*cur))
        chains.append(pts)
    return palm, chains


def hand_frame(elbow, wrist, roll=0.0, up_hint=None):
    """frame for a hand continuing the forearm; roll turns the palm around the forearm"""
    y = norm(np.asarray(wrist) - np.asarray(elbow))
    hint = V(0, 0, 1) if up_hint is None else np.asarray(up_hint, float)
    x = np.cross(y, hint)
    if np.linalg.norm(x) < 1e-6:
        x = np.cross(y, V(1, 0, 0))
    x = norm(x)
    z = np.cross(x, y)
    c, s = math.cos(roll), math.sin(roll)
    x, z = x * c + z * s, z * c - x * s
    return np.stack([x, y, z], axis=1)


def draw_hand(c, cs, W, R, sh, side, color, a=1.0, k=1.0, width_m=0.017, edge=None):
    """edge: (colour, px) to draw a separation outline under the hand first"""
    if edge is not None:
        draw_hand(c, cs, W, R, sh, side, edge[0], a, k, width_m + edge[1] / max(1e-6, cs.scale(float(cs.to_cam(W)[2]))) * 2.0)
    palm, chains = hand_points(W, R, sh, side, k)
    Pp = cs.proj_many(np.array(palm))
    if np.any(Pp[:, 2] < 0.05):
        return
    depth = float(np.mean(Pp[:, 2]))
    sc = cs.scale(depth)
    wpx = max(1.2, width_m * k * sc)
    path = poly_path(Pp[:, :2], closed=True)
    c.drawPath(path, paint(color, a))
    c.drawPath(path, paint(color, a, stroke=wpx * 0.9))
    for i, ch in enumerate(chains):
        Q = cs.proj_many(np.array(ch))
        if np.any(Q[:, 2] < 0.05):
            continue
        w = wpx * (1.2 if i == 0 else 1.0 if i < 4 else 0.85)
        # tapered: two strokes, the base part thicker
        c.drawPath(poly_path(Q[:3, :2]), paint(color, a, stroke=w * 1.15))
        c.drawPath(poly_path(Q[:, :2]), paint(color, a, stroke=w * 0.85))
    return wpx
