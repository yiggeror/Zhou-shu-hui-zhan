"""Rotoscoped stick figures.

Poses are keyed in screen space, traced from the original frames: for every key the head centre
and radius, the neck / chest / pelvis, elbows, wrists, knees, ankles (in percent of the frame,
x of the width, y of the height), the head's turn / nod / tilt, and the hands.  Each key only
lists what changed; everything else carries over from the previous key.  Between keys every
value follows a smooth monotone curve, sampled at the output frame rate.

The screen points are lifted into 3D along the camera rays of a fixed camera at the origin
looking down +z, at the depth where the figure's head has the traced size.  So the stick figure
lands exactly where the character is in the original frame, and the normal figure drawing
(depth-sorted limbs, hair, glowing eyes, hands with fingers) and the 3D effects (flames attached
to fists, orbs, sparks) all work unchanged in metres."""
import math
import numpy as np
from scipy.interpolate import PchipInterpolator
from .mathx import V, norm, Rx, Ry, Rz, clamp
from .camera import Cam, W, H
from .rig import Figure
from .figure import FigDraw
from .hand import SHAPES

FOV = 40.0
FOCAL = (H / 2) / math.tan(math.radians(FOV) / 2)

JOINTS = ('H', 'N', 'C', 'P', 'El', 'Wl', 'Er', 'Wr', 'Kl', 'Al', 'Kr', 'Ar', 'Tl', 'Tr', 'Sl', 'Sr', 'Hpl', 'Hpr')
SCALARS = ('r', 'yaw', 'pitch', 'roll', 'eye_open', 'eye_glow', 'eye_fire', 'eye_squint', 'eye_l', 'eye_r', 'eye_k',
           'visible', 'hdl', 'hdr', 'fist_l', 'fist_r', 'bend')
DEFAULTS = dict(yaw=0.0, pitch=0.0, roll=0.0, eye_open=1.0, eye_glow=0.0, eye_fire=0.0, eye_squint=0.0, eye_l=1.0, eye_k=1.0,
                eye_r=1.0, visible=1.0, fist_l=0.0, fist_r=0.0, bend=0.0)


def screen_cam(**kw):
    """the fixed camera every rotoscoped shot is seen through (shake / punch-in still apply)"""
    c = Cam(V(0, 0, 0), V(0, 0, 1), fov=FOV, **kw)
    c.drift = 0.0
    return c


def px(p):
    """percent coordinates -> pixels"""
    return np.array([p[0] * W / 100.0, p[1] * H / 100.0])


def lift(p_px, z):
    """pixel position at depth z -> world point on that camera ray"""
    return V((p_px[0] - W / 2) * z / FOCAL, (H / 2 - p_px[1]) * z / FOCAL, z)


def lift_pct(p, z):
    return lift(px(p), z)


def _numeric(v):
    if isinstance(v, (int, float, np.floating, np.integer)) and not isinstance(v, bool):
        return True
    if isinstance(v, (tuple, list, np.ndarray)) and len(v) and all(isinstance(x, (int, float, np.floating, np.integer)) for x in v):
        return True
    return False


class Track:
    """keyed values over original-film frame numbers; a key inherits what it does not set.
    Numbers and points are interpolated smoothly over the keys where they are set; setting a
    point to None hides it from that key on.  Anything else (hand shapes, hide lists, depth
    offsets) switches at its key."""

    def __init__(self, keys):
        keys = sorted(keys, key=lambda k: k[0])
        self.frames = np.array([k[0] for k in keys], float)
        state = {}
        rows = []
        for f, d in keys:
            state = dict(state)
            state.update(d)
            rows.append(state)
        self.rows = rows
        self.curves = {}
        names = set()
        for r in rows:
            names.update(r.keys())
        for n in names:
            idx = [i for i, r in enumerate(rows) if r.get(n) is not None]
            if not idx or not all(_numeric(rows[i][n]) for i in idx):
                continue
            fr = self.frames[idx]
            arr = np.array([rows[i][n] for i in idx], float)
            if len(idx) == 1:
                self.curves[n] = (fr[0], fr[0], (lambda f, a=arr[0]: a))
            else:
                self.curves[n] = (fr[0], fr[-1], PchipInterpolator(fr, arr, axis=0, extrapolate=False))

    def _row(self, f):
        i = int(np.searchsorted(self.frames, f + 1e-9, side='right')) - 1
        return self.rows[max(i, 0)], i

    def get(self, name, f):
        row, i = self._row(f)
        c = self.curves.get(name)
        if c is not None:
            f0, f1, fn = c
            if i >= 0 and row.get(name) is None:
                return None
            if f < f0 - 1e-9 and f0 > self.frames[0] + 1e-9:
                return None         # appears later in the shot
            return np.asarray(fn(clamp(f, f0, f1)), float)
        return row.get(name)

    def has(self, name):
        return any(name in r for r in self.rows)


class RotoFigure(Figure):
    """a Figure whose pose comes from screen-space keys (see module doc).  t is shot-local time;
    t0 is the shot start in seconds, so keys use absolute original frame numbers."""

    def __init__(self, style, keys, t0, name='', z_ofs=None):
        super().__init__(style, 1.0, name)
        self.track = Track(keys)
        self.t0 = t0
        self.z_ofs = dict(z_ofs or {})
        self._cache = {}

    def frame(self, t):
        return (self.t0 + t) * 24.0

    def pose(self, t):
        J = self._cache.get(t)
        if J is None:
            if len(self._cache) > 4000:
                self._cache.clear()
            J = self._cache[t] = self._roto_pose(t)
        return J

    def _roto_pose(self, t):
        f = self.frame(t)
        T = self.track
        def g(n, d=None):
            v = T.get(n, f) if T.has(n) else None
            return d if v is None else v
        S = self.L
        Rw = S['head'] * self.style.head_k
        r = float(g('r'))
        z = FOCAL * Rw / max(r * H / 100.0, 1e-3)
        zo = dict(self.z_ofs)
        zo.update(g('z') or {})
        Hs = px(g('H'))
        roll = math.radians(float(g('roll', 0.0)))
        # neck: just under the head, along the head's tilt, unless traced
        if g('N') is not None:
            Ns = px(g('N'))
        else:
            Ns = Hs + np.array([math.sin(roll), math.cos(roll)]) * r * H / 100.0 * 1.05
        pts = {'H': Hs, 'N': Ns}
        for j in JOINTS[2:]:
            v = g(j)
            if v is not None:
                pts[j] = px(v)
        hide = set(g('hide') or ())
        # anything not traced is hidden (and parked on the neck so nothing reads it as a pose)
        for chain, need in (('torso', ('C', 'P')), ('arml', ('El', 'Wl')), ('armr', ('Er', 'Wr')),
                            ('legl', ('Kl', 'Al')), ('legr', ('Kr', 'Ar'))):
            if any(n not in pts for n in need):
                hide.add(chain)
        if 'C' not in pts:
            pts['C'] = Ns
        if 'P' not in pts:
            pts['P'] = pts['C'] + (pts['C'] - Hs) * 1.5
        for s in 'lr':
            if 'W' + s not in pts:
                hide.add('fist' + s)
                pts['E' + s] = pts.get('E' + s, pts['C'])
                pts['W' + s] = pts['E' + s]
            if 'E' + s not in pts:
                pts['E' + s] = (pts['C'] + pts['W' + s]) / 2
            pts['K' + s] = pts.get('K' + s, pts['P'])
            pts['A' + s] = pts.get('A' + s, pts['K' + s])
        J = {}
        for n, p in pts.items():
            J[n] = lift(p, z + float(zo.get(n, 0.0)))
        # feet: toe point given, or a short step out to the side the body faces
        side_sign = -1.0 if float(g('yaw', 0.0)) < 0 else 1.0
        for s in 'lr':
            if 'T' + s not in pts:
                A, K = pts['A' + s], pts['K' + s]
                shin = A - K
                L = np.hypot(*shin) + 1e-6
                toe = A + np.array([side_sign, 0.25]) * L * 0.28
                J['T' + s] = lift(toe, z + float(zo.get('A' + s, 0.0)))
        J['M'] = J['P'] + (J['C'] - J['P']) * 0.5 + V(0, 0, 0)
        for s in 'lr':
            # shoulders / hips: traced, or on the chest / pelvis point
            if 'S' + s not in J:
                J['S' + s] = J['C']
            if 'Hp' + s not in J:
                J['Hp' + s] = J['P']
        # rotations: head from turn / nod / tilt (0 = facing the lens), chest from the spine
        yaw = math.radians(float(g('yaw', 0.0)))
        pitch = math.radians(float(g('pitch', 0.0)))
        J['Rh'] = Rz(-roll) @ Ry(math.pi + yaw) @ Rx(pitch)
        up = norm(J['C'] - J['P']) if 'torso' not in hide else norm(J['N'] - J['H']) * -1
        fw = V(math.sin(math.pi + yaw), 0, math.cos(math.pi + yaw))
        x = norm(np.cross(up, fw)) if np.linalg.norm(np.cross(up, fw)) > 1e-6 else V(1, 0, 0)
        fw2 = np.cross(x, up)
        Rc = np.stack([x, up, fw2], axis=1)
        J['Rc'] = J['Rp'] = Rc
        for s in 'lr':
            hs = g('hs_' + s)
            J['hs_' + s] = None if hs is None else np.asarray(SHAPES[hs] if isinstance(hs, str) else hs, float)
            J['fist_' + s] = float(g('fist_' + s, 1.0 if hs == 'fist' else 0.0))
            J['hroll_' + s] = 0.0
            J['hbend_' + s] = 0.0
            # finger direction: traced screen angle (deg, 0 = right, 90 = up) or along the forearm
            ang = g('hd' + s)
            if ang is None:
                d = pts['W' + s] - pts['E' + s]
                d = np.array([d[0], -d[1]])
            else:
                a = math.radians(float(ang))
                d = np.array([math.cos(a), math.sin(a)])
            hup = norm(V(d[0], d[1], 0.0) + V(0, 0, 1e-4))
            palm = g('palm_' + s, 'cam')
            if palm == 'cam':
                hb = V(0, 0, 1)        # palm toward the lens, back of the hand away
            elif palm == 'away':
                hb = V(0, 0, -1)
            elif palm == 'in':
                hb = V(-hup[1], hup[0], 0) * (1 if s == 'r' else -1)
            else:
                hb = V(hup[1], -hup[0], 0) * (1 if s == 'r' else -1)
            J['hup_' + s] = hup
            J['hback_' + s] = hb
        for n in ('eye_open', 'eye_glow', 'eye_fire', 'eye_squint', 'eye_l', 'eye_r', 'eye_k', 'visible'):
            J[n] = float(g(n, DEFAULTS[n]))
        J['hide'] = hide
        J['depth'] = z
        return J

    def world(self, t, name):
        return self.pose(t)[name]


class RotoActor:
    """what draw_actors needs: .fig, .d (drawer), optional draw_opts"""

    def __init__(self, style, keys, t0, name='', z_ofs=None, **draw_opts):
        self.fig = RotoFigure(style, keys, t0, name, z_ofs)
        self.d = FigDraw(self.fig)
        self.draw_opts = draw_opts

    def J(self, t):
        return self.fig.pose(t)


def K(f, **kw):
    """one key: K(frame, H=(x, y), r=..., C=..., ...)"""
    return (f, kw)
