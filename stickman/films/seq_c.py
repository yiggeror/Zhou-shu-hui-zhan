"""Sequence C: shots 18-36 (frames 667-1170): Sukuna on the roof, observers, the ritual."""
from films.common import *
from engine.env import Building, draw_buildings
from films.seq_b import city_ring, UTAHIME

KIRARA = PLAIN.but(hair='short')
YUJI = PLAIN.but(hair='fushiguro')
CHOSO = PLAIN.but(hair='short')
HAKARI = PLAIN.but(hair='short')
GLASSMAN = GLASSES


def red_sky(fr, side='right', k=0.28):
    x = W * (0.95 if side == 'right' else 0.05)
    fx.light_wash(fr, x, H * 0.25, 900, (0.92, 0.25, 0.28), k)


def foot_closeup(fr, cs, J, side, color=INK, a=1.0):
    """bare foot for close-ups: a solid foot shape with toes, at the figure's ankle"""
    A, T, K = J['A' + side], J['T' + side], J['K' + side]
    f = norm(T - A)
    up = norm(A - K)
    lat = norm(np.cross(up, f))
    L = float(np.linalg.norm(T - A)) * 1.6
    outline = [A + lat * 0.035 - up * 0.01, A + f * L * 0.55 + lat * 0.05 - up * 0.055, A + f * L * 1.0 + lat * 0.045 - up * 0.06,
               A + f * L * 1.08 - up * 0.065, A + f * L * 1.0 - lat * 0.05 - up * 0.06, A + f * L * 0.45 - lat * 0.045 - up * 0.055,
               A - f * 0.05 - lat * 0.03 - up * 0.04, A - f * 0.06 + up * 0.02]
    P = cs.proj_many(np.array(outline))
    if np.any(P[:, 2] < 0.05):
        return
    fr.b.drawPath(smooth_path(P[:, :2], closed=True), paint(color, a))
    for i in range(5):
        tp = A + f * L * (1.02 - 0.06 * abs(i - 1.2)) + lat * (0.045 - 0.022 * i) - up * 0.055
        q = cs.proj(tp)
        r = (0.016 - 0.002 * i) * cs.scale(q[2])
        fr.b.drawCircle(q[0], q[1], r, paint(color, a))


# ============================================================================ 18: Sukuna on the rooftop edge
class S18(Shot):
    t0, t1 = 667 / 24, 700 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk18'))
        stand(k, 0, 0.3, 0, math.pi + 0.15, width=0.17, y=0.0)
        k.k(0, hand_l=V(-0.08, -0.5, 0.02), hand_r=V(0.06, -0.48, 0.05), hpitch=0.12, eye_glow=1.3, eye_fire=0.4, lean=0.03)
        k.k(1.0, hpitch=0.05, hyaw=-0.1)
        k.k(D, hpitch=0.0, hyaw=-0.18, hroll=0.05)
        k.follow(['hpitch', 'hyaw'], 0, D)
        self.blds = [Building(2.2, 9.0, 8, 16, 34, base=-40, seed=181, style='vstrips', win_density=0.5)] + city_ring(18, y_top=-10)
        self.cam = Cam(Ch(V(-0.8, 0.9, -5.6)).key(D, V(-0.7, 0.95, -4.8)), Ch(V(0.4, 1.35, 0)), fov=40)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        red_sky(fr, 'right', 0.25)
        draw_buildings(fr, cs, self.blds, fog_dist=120)
        d3.box(fr, cs, V(-14, -12, -1.0), V(14, 0, 3.0), w_m=0.02)
        draw_actors(fr, self.cam, s, s, [self.k])


# ============================================================================ 19: Sukuna smiles
class S19(Shot):
    t0, t1 = 700 / 24, 738 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk19'))
        stand(k, 0, 0, 0, math.pi + 0.25)
        k.k(0, hpitch=0.12, hyaw=-0.15, eye_glow=1.2, eye_fire=0.5, eye_open=0.85)
        k.k(0.9, 'io', hpitch=-0.02, hyaw=-0.05, eye_open=1.0, eye_glow=1.45, eye_fire=0.8)
        k.k(D, hpitch=-0.05, hyaw=0.0, hroll=0.04)
        k.follow(['hpitch', 'hyaw'], 0, D)
        self.smile = Ch(0.25).key(0.5, 0.3).key(1.1, 1.0, 'io').key(D, 1.0)
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.25, -0.12, -1.05)).key(D, H + V(0.18, -0.1, -0.82)), Ch(H + V(0.05, -0.08, 0)), fov=40)
        self.blds = skyline(19, n=30, z0=-140, z1=-40, spread=150, y_top=-1)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        red_sky(fr, 'left', 0.25)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.75)
        mouth(fr, cs, J, self.k.fig, 1.0, smile=float(self.smile(s)), width=0.55)


# ============================================================================ 20-22: observers
class Observers(Shot):
    """heads watching off to the right; small natural movements"""
    people = []
    cam_pos, cam_tgt, fov = V(0, 1.6, -2), V(0, 1.6, 0), 40

    def setup(self):
        D = self.t1 - self.t0
        self.acts = []
        for i, (st, x, z, yaw, extra) in enumerate(self.people):
            a = Actor(Figure(st, extra.pop('k', 1.0), 'obs%d_%d' % (id(self) % 97, i)))
            stand(a, 0, x, z, yaw, width=0.13)
            spec = dict(eye_glow=0.0, hand_l=V(-0.05, -0.48, 0.06), hand_r=V(0.05, -0.48, 0.06))
            spec.update(extra.pop('pose', {}))
            a.ke(0, spec)
            for (tk, sp) in extra.pop('keys', []):
                a.ke(tk * D, sp)
            a.follow(['hyaw', 'hpitch', 'hand_l', 'hand_r'], 0, D, f=2.2, z=0.7, r=1.0)
            if 'silhouette' in extra:
                a.draw_opts = dict(silhouette=extra['silhouette'])
            self.acts.append(a)
        self.cam = Cam(Ch(self.cam_pos).key(D, self.cam_pos + V(0.08, 0.0, 0.12)), Ch(self.cam_tgt), fov=self.fov)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, self.acts)


class S20(Observers):
    t0, t1 = 733 / 24, 764 / 24
    people = [
        (KIRARA, -0.75, 0.9, 1.25, dict(pose=dict(hyaw=0.2, hpitch=0.05), keys=[(0.6, dict(hyaw=0.3))])),
        (YUJI, -0.15, 0.4, 1.35, dict(pose=dict(hyaw=0.1, hpitch=0.08, lean=0.08), keys=[(0.4, dict(hpitch=0.02)), (1.0, dict(hyaw=0.25, hpitch=-0.02))])),
        (CHOSO, 0.55, 0.0, 1.45, dict(pose=dict(hyaw=0.05, hpitch=0.18), keys=[(0.7, dict(hpitch=0.12, eye_open=0.3)), (0.8, dict(eye_open=1.0))])),
    ]
    cam_pos, cam_tgt, fov = V(-0.1, 1.62, -1.45), V(-0.05, 1.55, 0.5), 42


class S21(Observers):
    t0, t1 = 760 / 24, 784 / 24
    people = [
        (CHOSO, -0.55, 0.0, 1.0, dict(pose=dict(hyaw=0.3, hpitch=0.2, hand_r=V(-0.1, 0.25, 0.2), elbow_r=V(0.6, -0.8, 0.2), hshape_r=shape('relax')),
                                     keys=[(0.6, dict(hpitch=0.25, hand_r=V(-0.1, 0.27, 0.21)))])),
        (PLAIN.but(hair='short'), 0.35, 1.3, 0.9, dict(k=1.08, pose=dict(hand_l=V(0.22, 0.02, 0.24), hand_r=V(-0.22, -0.02, 0.22),
                                                                        elbow_l=V(-0.8, -0.6, 0.1), elbow_r=V(0.8, -0.6, 0.1), hpitch=0.2, hyaw=0.3),
                                                        keys=[(1.0, dict(hyaw=0.4))])),
        (PANDA, 0.95, -0.4, 0.8, dict(pose=dict(hyaw=0.3, hpitch=0.05), keys=[(0.5, dict(hyaw=0.45)), (1.0, dict(hyaw=0.4, hroll=0.1))])),
    ]
    cam_pos, cam_tgt, fov = V(0.1, 1.45, -1.8), V(0.15, 1.35, 0.5), 46


class S22(Observers):
    t0, t1 = 780 / 24, 816 / 24
    people = [
        (HAKARI, -0.35, 0.0, 1.35, dict(pose=dict(hyaw=0.25, hpitch=0.12, hroll=0.15), keys=[(0.5, dict(hyaw=0.32)), (1.0, dict(hyaw=0.38, hpitch=0.08))])),
        (PLAIN.but(hair='long'), 0.45, 1.1, 1.1, dict(pose=dict(hand_l=V(0.2, 0.02, 0.24), hand_r=V(-0.2, -0.02, 0.22),
                                                               elbow_l=V(-0.8, -0.6, 0.1), elbow_r=V(0.8, -0.6, 0.1), hyaw=0.2),
                                                   keys=[(1.0, dict(hyaw=0.3, hpitch=0.05))])),
    ]
    cam_pos, cam_tgt, fov = V(-0.25, 1.6, -1.25), V(0.0, 1.55, 0.5), 42


# ============================================================================ 23: the ritual rooftop
class S23(Shot):
    t0, t1 = 816 / 24, 856 / 24

    def setup(self):
        D = self.t1 - self.t0
        o = self.o = Actor(Figure(OLDMAN, 0.95, 'old23'))
        u = self.u = Actor(Figure(UTAHIME, 0.96, 'uta23'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo23'))
        x2 = self.x2 = Actor(Figure(PLAIN, 1.0, 'kus23'))
        # old man sitting cross-legged, biwa upright, strumming
        o.k(0, yaw=math.pi + 0.5, root=V(-1.6, 0.38, -0.5), lean=0.2, foot_l=V(-1.85, 0.0, -0.75), foot_r=V(-1.35, 0.0, -0.8),
            knee_l=V(-1, 0.6, 0.6), knee_r=V(1, 0.6, 0.6), hand_l=V(0.05, 0.05, 0.32), elbow_l=V(-0.8, -0.5, 0),
            hand_r=V(0.10, -0.25, 0.25), hpitch=0.35, eye_glow=0.0, hshape_l=shape('grip'), hshape_r=shape('pluck'))
        for i in range(8):
            tt = 0.12 + i * 0.2
            o.k(tt, 'in', hand_r=V(0.13, -0.17, 0.27))
            o.k(tt + 0.09, 'out', hand_r=V(0.06, -0.33, 0.24), hpitch=0.35 + 0.05 * (i % 2))
        # dancer: turning step with sweeping arms
        u.k(0, yaw=math.pi - 0.6, root=V(1.4, 0.88, 0.2), foot_l=V(1.25, 0, 0.3), foot_r=V(1.55, 0, 0.05), eye_glow=0.0,
            hand_l=V(-0.35, 0.05, 0.2), hand_r=V(0.40, -0.1, 0.15), elbow_l=V(-0.7, 0.5, -0.3), hpitch=0.2, hroll=-0.15)
        u.k(0.55, 'io', yaw=math.pi - 0.1, root=V(1.3, 0.82, 0.15), hand_l=V(-0.45, 0.25, 0.0), hand_r=V(0.20, -0.30, 0.30),
            twist=0.35, lean=0.15, foot_r=V(1.25, 0.18, 0.0), hroll=0.1)
        u.k(0.85, foot_r=V(1.05, 0.0, -0.05))
        u.k(1.25, 'io', yaw=math.pi + 0.45, root=V(1.15, 0.86, 0.1), hand_l=V(-0.15, -0.35, 0.3), hand_r=V(0.45, 0.25, 0.05),
            twist=-0.35, lean=0.05, foot_l=V(1.0, 0.0, 0.35), hroll=-0.12)
        u.k(D, yaw=math.pi + 0.6, root=V(1.1, 0.85, 0.1), hand_r=V(0.48, 0.32, -0.02), twist=-0.45)
        u.follow(['hand_l', 'hand_r', 'hpitch', 'hroll'], 0, D)
        u.d.wind = V(-0.3, 0.0, 0.0)
        # far back at the roof edge: Gojo (eyes lit) and a companion
        stand(g, 0, 0.15, 7.5, math.pi, width=0.16)
        g.k(0, eye_glow=1.3, hpitch=0.1).k(D, hpitch=0.05)
        stand(x2, 0, -0.45, 7.3, math.pi - 0.2, width=0.15)
        x2.k(0, eye_glow=0.0)
        self.cam = Cam(Ch(V(-0.6, 1.2, -4.6)).key(D, V(-0.3, 1.15, -4.2)), Ch(V(0.0, 1.0, 2.5)), fov=46)
        self.blds = city_ring(23, y_top=-8)

    def biwa(self, fr, cs, t):
        J = self.o.fig.pose(t)
        Rc, C = J['Rc'], J['C']
        body = C + Rc @ V(0.02, -0.38, 0.28)
        neck = C + Rc @ V(-0.02, 0.45, 0.32)
        d3.line3(fr, cs, body, neck, color=INK, w_m=0.045)
        pts = [body + Rc @ V(math.cos(a) * 0.16, math.sin(a) * 0.24, 0) for a in np.linspace(0, 2 * math.pi, 18)]
        d3.poly3(fr, cs, pts, fill=INK)
        d3.line3(fr, cs, neck, neck + Rc @ V(0.08, 0.07, -0.02), color=INK, w_m=0.03)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        # roof: parapet at the far edge with bright panels
        d3.line3(fr, cs, V(-8, 0, 8), V(8, 0, 8), w_m=0.03)
        d3.box(fr, cs, V(-6, 0, 5.6), V(6, 0.9, 6.0), w_m=0.015)
        for i in range(5):
            x = -4.5 + i * 2.1
            d3.poly3(fr, cs, [V(x, 0.15, 5.58), V(x + 1.6, 0.15, 5.58), V(x + 1.6, 0.75, 5.58), V(x, 0.75, 5.58)],
                     fill=(1.0, 1.0, 1.0), edge=d3.PENCIL, w_m=0.01)
        draw_actors(fr, self.cam, s, s, [self.g, self.x2, self.u])
        self.biwa(fr, cs, s)
        draw_actors(fr, self.cam, s, s, [self.o])
        self.biwa_front(fr, cs, s)

    def biwa_front(self, fr, cs, t):
        pass


# ============================================================================ 24: city pan reveals Sukuna's profile
class S24(Shot):
    t0, t1 = 856 / 24, 877 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk24'))
        stand(k, 0, 0.0, 0.0, -math.pi / 2)
        k.k(0, hpitch=-0.05, eye_glow=1.3, eye_fire=0.3)
        k.k(D, hpitch=-0.08)
        H = k.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(-1.6, 0.0, -1.2)).key(D, H + V(-1.25, -0.02, -0.95)),
                       Ch(H + V(-6.0, -0.3, 30.0)).key(D, H + V(-0.6, -0.08, 2.0), 'io'), fov=44)
        self.blds = skyline(24, n=34, z0=30, z1=120, spread=160, y_top=-1)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        red_sky(fr, 'right', 0.3)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, self.k.fig.pose(s), self.k.fig, 0.6)


# ============================================================================ 25: hands getting ready
class S25(Shot):
    t0, t1 = 871 / 24, 891 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk25'))
        stand(k, 0, 0, 0, 0.0)
        k.k(0, hand_l=V(-0.15, 0.10, 0.42), hand_r=V(0.20, 0.0, 0.40), elbow_l=V(-0.8, -0.5, 0), elbow_r=V(0.8, -0.5, 0),
            hshape_l=shape('relax'), hshape_r=shape('open'), hroll_l=-1.3, hroll_r=-1.5)
        k.k(0.35, hshape_l=shape('claw'), hand_l=V(-0.14, 0.12, 0.43))
        k.k(0.6, hshape_r=shape('claw'), hand_r=V(0.21, 0.02, 0.41))
        k.k(D, hshape_l=np.array(shape('claw')) * 1.15, hshape_r=np.array(shape('claw')) * 1.1)
        J = k.fig.pose(0.4)
        mid = (J['Wl'] + J['Wr']) / 2
        self.cam = Cam(Ch(mid + V(-0.06, -0.04, 0.42)).key(D, mid + V(-0.05, -0.04, 0.37)), Ch(mid + V(0.02, 0.0, 0.0)), fov=44)
        self.blds = skyline(25, n=24, z0=-120, z1=-40, spread=120, y_top=-1)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        red_sky(fr, 'right', 0.28)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        draw_actors(fr, self.cam, s, s, [self.k])


# ============================================================================ 26: plucking the strings
class S26(Shot):
    t0, t1 = 891 / 24, 911 / 24

    def setup(self):
        D = self.t1 - self.t0
        o = self.o = Actor(Figure(OLDMAN, 0.95, 'old26'))
        stand(o, 0, 0, 0, 0.0)
        o.k(0, hand_r=V(-0.05, 0.10, 0.36), elbow_r=V(0.8, -0.5, -0.1), hshape_r=shape('pluck'), hroll_r=-0.6)
        o.k(0.18, 'in', hand_r=V(-0.12, 0.02, 0.38))
        o.k(0.26, 'out', hand_r=V(-0.20, -0.08, 0.37))
        o.k(D, hand_r=V(-0.22, -0.10, 0.36))
        J = o.fig.pose(0.15)
        self.W0 = J['Wr']
        self.cam = Cam(Ch(self.W0 + V(0.12, 0.05, 0.38)).key(D, self.W0 + V(0.1, 0.04, 0.33)), Ch(self.W0 + V(-0.03, -0.02, 0)),
                       fov=48, roll=-25)
        self.T = 0.20

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # the instrument body (ink) and four strings (paper) across the frame
        W0 = self.W0
        body = [W0 + V(-0.6, -0.5, -0.05), W0 + V(0.25, 0.6, -0.05), W0 + V(0.6, 0.6, -0.05), W0 + V(0.6, -0.5, -0.05)]
        d3.poly3(fr, cs, body, fill=INK)
        for i in range(4):
            o = V(0.03 * i, -0.02 * i, 0.0)
            a, b = W0 + V(-0.5, -0.45, -0.03) + o, W0 + V(0.3, 0.55, -0.03) + o
            amp = 0.006 * math.exp(-max(0, s - self.T) * 6) * (s > self.T) * (i + 1) / 2
            pts = []
            for j in range(15):
                u = j / 14
                p = a + (b - a) * u
                p = p + V(1, -0.7, 0) * amp * math.sin(math.pi * u) * math.sin(s * 120 + i)
                pts.append(p)
            Q = cs.proj_many(np.array(pts))
            fr.b.drawPath(poly_path(Q[:, :2]), paint(PAPER, 1.0, stroke=3.5))
        draw_actors(fr, self.cam, s, s, [self.o])


# ============================================================================ 27 / 30: bare feet stepping
class Feet(Shot):
    flip = False

    def setup(self):
        D = self.t1 - self.t0
        u = self.u = Actor(Figure(UTAHIME, 0.96, 'feet%d' % int(self.t0 * 24)))
        sx = -1 if self.flip else 1
        u.k(0, yaw=0.0, root=V(0.0, 0.86, 0.0), foot_l=V(-0.12, 0, 0.05), foot_r=V(0.12, 0.10, -0.25))
        u.k(D * 0.45, 'io', foot_r=V(0.10, 0.10, 0.25), root=V(0.0, 0.88, 0.12))
        u.k(D * 0.62, 'out', foot_r=V(0.10, 0.0, 0.32), root=V(0.0, 0.85, 0.16))
        u.k(D, foot_r=V(0.10, 0.0, 0.32), root=V(0.0, 0.86, 0.17), foot_l=V(-0.12, 0.02, 0.05))
        self.land = D * 0.62
        self.cam = Cam(Ch(V(0.42 * sx, 0.12, 0.30)).key(D, V(0.38 * sx, 0.12, 0.34)), Ch(V(0.05, 0.06, 0.2)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # concrete floor: pencil speckle
        for i in range(70):
            p = V((hash01(27, i) - 0.5) * 2.5, 0, (hash01(28, i) - 0.3) * 2.5)
            q = cs.proj(p)
            if q[2] > 0.05:
                fr.b.drawCircle(q[0], q[1], 1.2 + 2 * hash01(29, i), paint(d3.PENCIL, 0.35))
        J = self.u.fig.pose(s)
        for side in 'lr':
            d3.line3(fr, cs, J['K' + side], J['A' + side], color=INK, w_m=0.05)
            foot_closeup(fr, cs, J, side)
        a = s - self.land
        if a > 0:
            p = J['Tr']
            for i in range(10):
                ang = 2 * math.pi * i / 10
                r = 0.05 + 0.25 * (1 - math.exp(-a * 5))
                q = cs.proj(V(p[0] + math.cos(ang) * r, 0.01, p[2] + math.sin(ang) * r))
                fr.b.drawCircle(q[0], q[1], 6, paint(d3.PENCIL, 0.5 * math.exp(-a * 4), blur=6))


class S27(Feet):
    t0, t1 = 904 / 24, 924 / 24


class S30(Feet):
    t0, t1 = 984 / 24, 998 / 24
    flip = True


# ============================================================================ 28: the dancer
class S28(Shot):
    t0, t1 = 918 / 24, 971 / 24

    def setup(self):
        D = self.t1 - self.t0
        u = self.u = Actor(Figure(UTAHIME, 0.96, 'uta28'))
        u.k(0, yaw=math.pi + 0.3, root=V(0, 0.86, 0), foot_l=V(-0.15, 0, 0.1), foot_r=V(0.18, 0, -0.1), eye_glow=0.0,
            hand_l=V(-0.25, 0.30, 0.20), hand_r=V(0.35, -0.10, 0.25), elbow_l=V(-0.6, 0.6, -0.3), hpitch=0.25, hroll=0.2,
            twist=0.3, lean=0.1, hshape_l=shape('open'), hshape_r=shape('relax'))
        u.k(0.7, 'io', hand_l=V(-0.45, 0.05, 0.05), hand_r=V(0.20, 0.35, 0.25), twist=-0.15, hroll=-0.1, hpitch=0.1,
            yaw=math.pi + 0.05, root=V(0.02, 0.84, 0.02))
        u.k(1.35, 'io', hand_l=V(-0.35, 0.40, 0.15), hand_r=V(0.45, 0.10, -0.05), twist=-0.45, hroll=0.15, hpitch=-0.1,
            yaw=math.pi - 0.3, root=V(0.04, 0.82, 0.03))
        u.k(D, hand_l=V(-0.30, 0.45, 0.2), hand_r=V(0.48, 0.05, -0.1), twist=-0.55, hroll=0.2, yaw=math.pi - 0.4)
        u.follow(['hand_l', 'hand_r', 'hroll', 'hpitch'], 0, D, f=2.0, z=0.6, r=1.2)
        u.d.wind = V(0.4, 0.05, 0.0)
        H = u.fig.pose(0.8)['H']
        self.cam = Cam(Ch(H + V(0.15, -0.25, -1.35)).key(D, H + V(0.05, -0.25, -1.2)), Ch(H + V(0, -0.25, 0)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.u])


# ============================================================================ 29: the old man plays
class S29(Shot):
    t0, t1 = 965 / 24, 990 / 24

    def setup(self):
        D = self.t1 - self.t0
        o = self.o = Actor(Figure(OLDMAN, 0.95, 'old29'))
        o.k(0, yaw=math.pi + 0.35, root=V(0, 0.42, 0), lean=0.18, foot_l=V(-0.3, 0, -0.25), foot_r=V(0.25, 0, -0.3),
            knee_l=V(-1, 0.6, 0.6), knee_r=V(1, 0.6, 0.6), hand_l=V(0.02, 0.18, 0.32), elbow_l=V(-0.8, -0.5, 0),
            hand_r=V(0.10, -0.22, 0.26), hpitch=0.4, eye_glow=0.0, hshape_l=shape('grip'), hshape_r=shape('pluck'))
        for i in range(5):
            tt = 0.05 + i * 0.2
            o.k(tt, 'in', hand_r=V(0.13, -0.14, 0.28), hpitch=0.42)
            o.k(tt + 0.09, 'out', hand_r=V(0.05, -0.32, 0.24), hpitch=0.36)
        self.cam = Cam(Ch(V(-0.3, 1.0, -2.1)).key(D, V(-0.25, 0.98, -1.9)), Ch(V(0, 0.75, 0)), fov=46)
        self.biwa = S23.biwa

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        d3.line3(fr, cs, V(-5, 0, 3), V(5, 0, 3), w_m=0.02)
        draw_actors(fr, self.cam, s, s, [self.o])
        S23.biwa(self, fr, cs, s)


# ============================================================================ 31: the monitor room (pull back)
class S31(Shot):
    t0, t1 = 998 / 24, 1043 / 24

    def setup(self):
        D = self.t1 - self.t0
        m = self.m = Actor(Figure(PLAIN.but(hair='fushiguro'), 1.0, 'mon31'))
        m.k(0, yaw=0.0, root=V(0, 0.55, 0), lean=0.12, foot_l=V(-0.2, 0, 0.45), foot_r=V(0.2, 0, 0.45),
            knee_l=V(0, 0.5, 1), knee_r=V(0, 0.5, 1), hand_l=V(0.1, -0.25, 0.30), hand_r=V(-0.1, -0.25, 0.30), hpitch=-0.05, eye_glow=0.0)
        m.k(D * 0.6, hpitch=-0.12, hyaw=0.12)
        m.k(D, hpitch=-0.1, hyaw=-0.05)
        m.follow(['hyaw', 'hpitch'], 0, D)
        H = m.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(0.0, 0.05, -0.25)).key(0.5, H + V(0.0, 0.08, -0.55), 'out').key(D, H + V(0.0, 0.18, -1.35), 'io'),
                       Ch(H + V(0, 0.0, 1.0)), fov=50)
        self.screens = []
        for i in range(7):
            ang = -1.0 + 2.0 * i / 6
            for row in (0, 1):
                c = H + V(math.sin(ang) * 1.1, -0.15 + 0.55 * row, math.cos(ang) * 1.1)
                self.screens.append((c, ang))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        for (c, ang) in self.screens:
            r = V(math.cos(ang), 0, -math.sin(ang)) * 0.32
            u = V(0, 0.22, 0)
            pts = [c - r - u, c + r - u, c + r + u, c - r + u]
            d3.poly3(fr, cs, pts, fill=(1.0, 1.0, 1.0), edge=INK, w_m=0.03)
            d3.poly3(fr, cs, pts, fill=(0.85, 0.95, 1.0), alpha=0.35, layer='g')
            d3.line3(fr, cs, c - u, c - u - V(0, 0.4, 0), color=INK, w_m=0.02)
        draw_actors(fr, self.cam, s, s, [self.m])


# ============================================================================ 32: talisman ring lights up (top-down)
class S32(Shot):
    t0, t1 = 1043 / 24, 1067 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(GLASSMAN, 1.0, 'kn32'))
        k.k(0, yaw=0.3, root=V(0, 0.45, 0), lean=1.1, hpitch=0.2, foot_l=V(-0.15, 0, -0.45), foot_r=V(0.18, 0, -0.5),
            knee_l=V(0, -0.3, 1), knee_r=V(0, -0.3, 1), hand_lwb=1.0, hand_rwb=1.0, eye_glow=0.0,
            hshape_l=shape('open'), hshape_r=shape('open'))
        k.fig.set(hand_lw=V(-0.2, 0.0, 0.42), hand_rw=V(0.25, 0.0, 0.35))
        k.k(D, root=V(0, 0.43, 0.02), lean=1.15)
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo32'))
        stand(g, 0, 0.55, -0.8, 0.3, width=0.17)
        g.k(0, eye_glow=1.2, hpitch=0.3, hand_l=V(-0.1, -0.45, 0.1), hand_r=V(0.1, -0.45, 0.1))
        self.tal = []
        for i in range(12):
            ang = 2 * math.pi * i / 12 + 0.2
            r = 1.5 + 0.4 * hash01(32, i)
            self.tal.append((V(math.sin(ang) * r, 0.01, math.cos(ang) * r), ang + 0.5 * hash01(33, i), 0.05 + 0.6 * i / 12))
        self.cam = Cam(Ch(V(0.4, 4.6, -1.2)).key(D, V(0.35, 4.2, -1.0)), Ch(V(0.1, 0, 0)), fov=48, roll=Ch(0).key(D, 8))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        for (c, ang, t_on) in self.tal:
            on = smoothstep(t_on, t_on + 0.12, s)
            r = V(math.cos(ang), 0, -math.sin(ang)) * 0.28
            f = V(math.sin(ang), 0, math.cos(ang)) * 0.12
            pts = [c - r - f, c + r - f, c + r + f, c - r + f]
            d3.poly3(fr, cs, pts, fill=PAPER, edge=d3.PENCIL, w_m=0.02)
            if on > 0:
                d3.poly3(fr, cs, pts, edge=fx.PAL['cyan']['mid'], w_m=0.03, alpha=on, layer='g')
                d3.poly3(fr, cs, pts, edge=fx.PAL['cyan']['glow'], w_m=0.09, alpha=0.4 * on, layer='g')
        draw_actors(fr, self.cam, s, s, [self.k, self.g])


# ============================================================================ 33: the glasses man strains
class S33(Shot):
    t0, t1 = 1061 / 24, 1087 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(GLASSMAN, 1.0, 'gl33'))
        stand(k, 0, 0, 0, math.pi)
        k.k(0, hpitch=0.35, hroll=-0.35, hyaw=0.2, eye_glow=0.0, eye_squint=0.6)
        k.k(D, hpitch=0.42, hroll=-0.38, hyaw=0.15)
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.1, -0.25, -0.75)).key(D, H + V(0.08, -0.22, -0.68)), Ch(H + V(0, -0.05, 0)), fov=42, roll=-10)
        self.motes = [(hash01(33, i), hash01(34, i), hash01(35, i)) for i in range(26)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # strain: a small fast tremble
        self.cam.shakes = [(0.0, 3.0, 5.0, 30.0)]
        J = self.k.fig.pose(s)
        for (a, b, c) in self.motes:
            x, y = a * W, (b * H - s * 60 * (0.5 + c)) % H
            fr.g.drawCircle(x, y, 3 + 5 * c, paint(fx.PAL['cyan']['mid'], 0.7, add=True, blur=4))
        draw_actors(fr, self.cam, s, s, [self.k])
        mouth(fr, cs, J, self.k.fig, 1.0, smile=-0.2, width=0.62, open_=0.35, y=-0.5)


# ============================================================================ 34: Gojo's arm, blue motes
class S34(Shot):
    t0, t1 = 1080 / 24, 1117 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo34'))
        stand(g, 0, 0, 0, math.pi)
        g.k(0, hand_r=V(-0.05, 0.25, 0.28), elbow_r=V(0.8, -0.4, -0.2), hshape_r=shape('relax'), hpitch=-0.2, eye_glow=1.2, twist=0.2)
        g.k(D * 0.5, 'io', hand_r=V(0.05, 0.42, 0.25), hshape_r=shape('open'), twist=0.1)
        g.k(D, hand_r=V(0.08, 0.50, 0.2), hshape_r=shape('claw'), twist=0.05)
        J = g.fig.pose(0.5)
        self.C = J['C']
        self.cam = Cam(Ch(self.C + V(0.6, -0.1, -0.85)).key(D, self.C + V(0.5, 0.0, -0.75)), Ch(self.C + V(0.0, 0.25, 0)), fov=48, roll=12)
        self.motes = [V((hash01(34, i) - 0.5) * 2.4, (hash01(35, i) - 0.2) * 1.8, (hash01(36, i) - 0.5) * 1.5) for i in range(40)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.g])
        J = self.g.fig.pose(s)
        for i, m in enumerate(self.motes):
            # motes drift up toward the raised hand
            p = self.C + m + V(0, s * 0.25, 0) + (J['Wr'] - self.C - m) * min(0.5, s * 0.25)
            q = cs.proj(p)
            if q[2] < 0.05:
                continue
            tw = 0.5 + 0.5 * math.sin(s * 9 + i)
            fr.g.drawCircle(q[0], q[1], 3 + 3 * tw, paint(fx.PAL['cyan']['mid'], 0.9 * tw, add=True, blur=3))
            fr.g.drawCircle(q[0], q[1], 1.5, paint(fx.PAL['cyan']['core'], tw, add=True))


# ============================================================================ 35: a band of red energy sweeps around him
class S35(Shot):
    t0, t1 = 1117 / 24, 1148 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo35'))
        stand(g, 0, 0, 0, math.pi)
        g.k(0, hand_r=V(0.08, 0.50, 0.2), elbow_r=V(0.8, -0.4, -0.2), hshape_r=shape('claw'), hand_l=V(-0.1, 0.1, 0.32),
            hshape_l=shape('relax'), eye_glow=1.2, hpitch=-0.15)
        g.k(D, hand_r=V(0.12, 0.55, 0.15), hand_l=V(-0.18, 0.22, 0.30), hshape_l=shape('open'))
        J = g.fig.pose(0.5)
        self.C = C = J['C']
        ell = lambda t, ph: C + V(math.sin(t * 5.5 + ph) * 0.62, 0.08 + 0.10 * math.sin(t * 3.1 + ph), math.cos(t * 5.5 + ph) * 0.5)
        self.band = [fx.Flame(lambda t, ph=ph: ell(t, ph), 'red', size=0.05, life=0.32, rate=260, rise=0.05, jitter=0.25,
                              trail=1.0, seed=350 + i, amp=0.32) for i, ph in enumerate((0.0, 2.2))]
        self.cam = Cam(Ch(self.C + V(-0.5, 0.2, -0.95)).key(D, self.C + V(-0.4, 0.2, -0.85)), Ch(self.C + V(0, 0.15, 0)), fov=48, roll=-8)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.g])
        # the red band: cursed energy streaming around him, rendered like the fist flames
        fx.render_flames(fr, cs, self.band, s, warp=1.4)
        if s < 3 / 24:
            fr.post.append(fx.whip_blur(220 * (1 - s / (3 / 24)), 0))


# ============================================================================ 36: the whole roof, Gojo raises his arms
class S36(Shot):
    t0, t1 = 1148 / 24, 1170 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo36'))
        stand(g, 0, 0, 14, math.pi, width=0.2)
        g.k(0, hand_l=V(-0.15, 0.2, 0.2), hand_r=V(0.15, 0.2, 0.2), eye_glow=1.3)
        g.k(D * 0.5, 'io', hand_l=V(-0.30, 0.55, 0.05), hand_r=V(0.30, 0.55, 0.05), hpitch=-0.15)
        g.k(D, hand_l=V(-0.32, 0.62, 0.0), hand_r=V(0.32, 0.62, 0.0), hpitch=-0.2)
        g.follow(['hand_l', 'hand_r'], 0, D)
        self.roof = Building(-9, 9, 0, 16, 40, base=-40, seed=36, style='grid', win_density=0.9)
        self.blds = city_ring(36, y_top=-6, r0=50)
        self.cam = Cam(Ch(V(0.0, 14.0, -26.0)).key(D * 0.55, V(0.0, 4.0, -8.0), 'io').key(D, V(0.0, 2.0, 2.0)),
                       Ch(V(0, 2, 8)).key(D * 0.55, V(0, 0.5, 10.0), 'io').key(D, V(0, 1.2, 14)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fx.light_wash(fr, -100, 0, 1100, (0.35, 0.45, 1.0), 0.28)
        fx.light_wash(fr, W + 100, 0, 1100, (0.95, 0.3, 0.35), 0.28)
        draw_buildings(fr, cs, self.blds, fog_dist=160)
        self.roof.draw(fr, cs, fog_dist=200)
        draw_actors(fr, self.cam, s, s, [self.g])


SHOTS = [S18, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33, S34, S35, S36]
SEGMENTS = [(S18.t0, S36.t1)]
