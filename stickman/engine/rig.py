"""3D stick-figure rig.  A pose is driven by channels (any callable of time):
root (pelvis, world), yaw, lean/bend/twist (spine), head angles or a look-at target,
hand targets (chest-local or world), foot targets (world), pole vectors and eye state.
Limbs are solved with soft two-bone IK, so the elbows/knees always bend naturally."""
import math
import numpy as np
from .mathx import V, norm, Rx, Ry, Rz, clamp, fbm1
from .anim import as_fn


def ik2(a, target, l1, l2, pole, soft=0.035):
    d = target - a
    dist = float(np.linalg.norm(d))
    if dist < 1e-6:
        d, dist = V(0, -1, 0), 1e-6
    u = d / dist
    L = l1 + l2
    s = soft * L
    da = L - s
    if dist > da:  # soft IK: approach full extension asymptotically, never snap
        dist = da + s * (1 - math.exp(-(dist - da) / s))
    dist = max(dist, abs(l1 - l2) + 1e-4)
    cosA = clamp((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1.0, 1.0)
    sinA = math.sqrt(max(0.0, 1 - cosA * cosA))
    p = pole - np.dot(pole, u) * u
    if np.linalg.norm(p) < 1e-6:
        p = np.cross(u, V(1, 0, 0))
        if np.linalg.norm(p) < 1e-6:
            p = np.cross(u, V(0, 0, 1))
    p = norm(p)
    mid = a + u * (l1 * cosA) + p * (l1 * sinA)
    end = a + u * dist
    return mid, end


class Style:
    def __init__(self, line=(0.93, 0.95, 0.97), eye=(0.35, 0.9, 1.0), eye_core=(0.85, 1.0, 1.0),
                 hair='gojo', four_eyes=False, width=0.052, head_w=0.034):
        self.line, self.eye, self.eye_core = line, eye, eye_core
        self.hair, self.four_eyes = hair, four_eyes
        self.width, self.head_w = width, head_w


GOJO = Style(line=(0.92, 0.95, 0.98), eye=(0.25, 0.85, 1.0), eye_core=(0.88, 1.0, 1.0), hair='gojo')
MAHORAGA = Style(line=(0.90, 0.90, 0.92), eye=(1, 1, 1), eye_core=(1, 1, 1), hair=None, width=0.075, head_w=0.045)
MAHORAGA.no_eyes = True
SUKUNA = Style(line=(0.97, 0.93, 0.92), eye=(1.0, 0.16, 0.22), eye_core=(1.0, 0.86, 0.84),
               hair='sukuna', four_eyes=True)


class Figure:
    def __init__(self, style, scale=1.0, name=''):
        self.style, self.name, self.k = style, name, scale
        k = scale
        self.L = dict(spine=0.52 * k, neck=0.10 * k, head=0.125 * k, sh_w=0.055 * k, sh_d=0.035 * k,
                      ua=0.31 * k, fa=0.29 * k, hip_w=0.075 * k, th=0.46 * k, sh=0.46 * k, foot=0.13 * k)
        S = self.L
        stand_h = 0.93 * k
        # defaults (all overridable with channels)
        self.ch = dict(
            root=V(0, stand_h, 0), yaw=0.0, lean=0.05, bend=0.0, twist=0.0, curve=0.0,
            hpitch=0.0, hyaw=0.0, hroll=0.0, look=None,
            hand_l=V(-0.05, -0.50, 0.08) * k, hand_r=V(0.05, -0.50, 0.08) * k,
            hand_lw=None, hand_rw=None, hand_lwb=0.0, hand_rwb=0.0,
            elbow_l=V(-0.6, -0.2, -0.8), elbow_r=V(0.6, -0.2, -0.8),
            foot_l=V(-0.12 * k, 0.0, 0.0), foot_r=V(0.12 * k, 0.0, 0.0),
            foot_lyaw=None, foot_ryaw=None,
            knee_l=V(-0.25, 0, 1), knee_r=V(0.25, 0, 1),
            fist_l=0.0, fist_r=0.0,
            eye_open=1.0, eye_glow=0.55, eye_fire=0.0, eye_squint=0.0, eye_l=1.0, eye_r=1.0,
            visible=1.0, idle=1.0,
        )
        self.seed = abs(hash(name)) % 997 if name else 7

    def set(self, **kw):
        for k, v in kw.items():
            if k not in self.ch:
                raise KeyError(k)
            self.ch[k] = v
        return self

    def g(self, name, t):
        v = self.ch[name]
        if v is None:
            return None
        return as_fn(v)(t)

    # ------------------------------------------------------------------
    def pose(self, t):
        c = self.__dict__.setdefault('_cache', {})
        J = c.get(t)
        if J is None:
            if len(c) > 6000:
                c.clear()
            J = c[t] = self._pose(t)
        return J

    def _pose(self, t):
        S = self.L
        g = lambda n: self.g(n, t)
        idle = float(g('idle'))
        sd = self.seed
        nz = lambda i, f=0.9: fbm1(t * f, sd + 31 * i, 2) * idle
        P = np.asarray(g('root'), dtype=np.float64) + V(nz(1) * 0.012, nz(2, 1.3) * 0.010, nz(3) * 0.012) * self.k
        yaw = float(g('yaw'))
        Rp = Ry(yaw)
        lean, bend, twist = float(g('lean')) + nz(4, 0.8) * 0.03, float(g('bend')) + nz(5, 0.7) * 0.02, float(g('twist')) + nz(6, 0.7) * 0.035
        curve = float(g('curve'))  # extra arch: lower half leans less (+) / more (-)
        Rm = Rp @ Ry(twist * 0.45) @ Rx(lean * (0.5 - 0.25 * curve)) @ Rz(bend * 0.5)
        Rc = Rp @ Ry(twist) @ Rx(lean) @ Rz(bend)
        M = P + Rm @ V(0, S['spine'] * 0.5, 0)
        C = M + Rc @ V(0, S['spine'] * 0.5, 0)
        N = C + Rc @ V(0, S['neck'], 0)
        look = g('look')
        if look is not None:
            # look-at target: express direction in chest frame
            d = np.linalg.solve(Rc, np.asarray(look) - N) if False else Rc.T @ (np.asarray(look) - N)
            hyaw = math.atan2(d[0], d[2])
            hpitch = -math.atan2(d[1], math.hypot(d[0], d[2]))
            hyaw += float(g('hyaw')); hpitch += float(g('hpitch'))
        else:
            hyaw, hpitch = float(g('hyaw')), float(g('hpitch'))
        hyaw += nz(7, 0.6) * 0.05
        hpitch += nz(8, 0.6) * 0.04
        Rh = Rc @ Ry(hyaw) @ Rx(hpitch) @ Rz(float(g('hroll')) + nz(9, 0.5) * 0.03)
        H = N + Rh @ V(0, S['head'] * 0.92, S['head'] * 0.12)
        Sl = C + Rc @ V(-S['sh_w'], -S['sh_d'], 0)
        Sr = C + Rc @ V(S['sh_w'], -S['sh_d'], 0)
        out = dict(P=P, M=M, C=C, N=N, H=H, Rp=Rp, Rc=Rc, Rh=Rh, Sl=Sl, Sr=Sr)
        for side, Sx in (('l', Sl), ('r', Sr)):
            loc = np.asarray(g('hand_' + side), dtype=np.float64) + V(nz(10 + (side == 'r'), 1.1), nz(12 + (side == 'r'), 1.0), nz(14 + (side == 'r'), 1.2)) * 0.014 * self.k
            T = Sx + Rc @ loc
            wt = self.ch['hand_%sw' % side]
            if wt is not None:
                wb = float(g('hand_%swb' % side))
                if wb > 0:
                    T = T * (1 - wb) + (np.asarray(as_fn(wt)(t)) + (T - Sx - Rc @ np.asarray(g('hand_' + side), dtype=np.float64)) * 0.5) * wb
            pole = Rc @ norm(np.asarray(g('elbow_' + side), dtype=np.float64))
            E, W = ik2(Sx, T, S['ua'], S['fa'], pole)
            out['E' + side], out['W' + side] = E, W
            out['fist_' + side] = float(g('fist_' + side))
        for side, sx in (('l', -1), ('r', 1)):
            Hp = P + Rp @ V(sx * S['hip_w'], -0.02 * self.k, 0)
            F = np.asarray(g('foot_' + side), dtype=np.float64)
            pole = Rp @ norm(np.asarray(g('knee_' + side), dtype=np.float64))
            K, A = ik2(Hp, F + V(0, 0.055 * self.k, 0), S['th'], S['sh'], pole)
            fy = self.ch['foot_%syaw' % side]
            fyaw = yaw + sx * 0.18 if fy is None else float(as_fn(fy)(t))
            # foot points forward, follows the shin a little when the foot is off the ground
            fwd = V(math.sin(fyaw), 0, math.cos(fyaw))
            lift = clamp((A[1] - 0.08 * self.k) / (0.3 * self.k), 0, 1)
            shin = norm(A - K)
            fdir = norm(fwd * (1 - 0.6 * lift) + shin * 0.6 * lift + V(0, -0.15, 0) * (1 - lift))
            out['Hp' + side], out['K' + side], out['A' + side] = Hp, K, A
            out['T' + side] = A + fdir * S['foot']
        out['eye_open'] = float(g('eye_open'))
        out['eye_glow'] = float(g('eye_glow'))
        out['eye_fire'] = float(g('eye_fire'))
        out['eye_squint'] = float(g('eye_squint'))
        out['eye_l'] = float(g('eye_l'))
        out['eye_r'] = float(g('eye_r'))
        out['visible'] = float(g('visible'))
        return out
