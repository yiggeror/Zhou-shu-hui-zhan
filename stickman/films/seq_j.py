"""Sequence J: shots 96-105 (frames 2511-2672): Red, the blast behind Sukuna, Black Flash, the wheel."""
from films.common import *
from films.seq_h import draw_street
from films.seq_i import SUK_W
from engine.env import Building, draw_buildings
from films.seq_b import city_ring

CY = fx.PAL['cyan']
RD = fx.PAL['red']


def red_wash(fr, k):
    if k > 0:
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.85, 0.35, 0.38), min(0.8, k * 0.55)))


def black_bolt(fr, a, b, seed, width=5.0, k=1.0):
    """Black Flash lightning: ink bolt with a red glow around it"""
    pts = fx.bolt_points(a, b, seed, 0.22, 6)
    path = poly_path(pts)
    fr.g.drawPath(path, paint(RD['glow'], 0.7 * k, stroke=width * 5, add=True, blur=width * 2))
    fr.g.drawPath(path, paint(RD['mid'], 0.9 * k, stroke=width * 2.2, add=True))
    fr.b.drawPath(path, paint(INK, k, stroke=width))


# ============================================================================ 96: the eye, then the grin
class S96(Shot):
    t0, t1 = 2511 / 24, 2521 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo96'))
        stand(g, 0, 0, 0, math.pi + 0.3)
        g.k(0, hpitch=0.35, hroll=-0.25, eye_glow=1.7, eye_fire=0.7, eye_open=1.15)
        g.k(D, hpitch=0.3, hroll=-0.3)
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.02, 0.0, -0.22)).key(4 / 24, H + V(0.0, -0.05, -0.55), 'outexp').key(D, H + V(0.0, -0.05, -0.5)),
                       Ch(H + V(0.04, 0.02, 0)).key(4 / 24, H + V(0, -0.02, 0), 'outexp'), fov=46, roll=-6)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        if s > 4 / 24:
            mouth(fr, cs, J, self.g.fig, 1.0, smile=1.0, width=0.6, open_=0.35)


# ============================================================================ 97: Red forms at his fingertips
class S97(Shot):
    t0, t1 = 2521 / 24, 2550 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo97'))
        stand(g, 0, 0, 0, math.pi - 0.4)
        g.k(0, hand_r=V(-0.10, 0.10, 0.25), elbow_r=V(0.8, -0.6, 0.0), hshape_r=shape('two'), hup_r=V(0.1, 1, 0.2),
            hback_r=V(0, 0, -1), hand_l=V(0.1, -0.2, 0.3), hpitch=0.15, eye_glow=1.5, lean=0.25)
        g.k(0.3, hand_r=V(-0.10, 0.14, 0.27))
        g.k(D, hand_r=V(-0.09, 0.16, 0.28), hpitch=0.1)
        self.form = Ch(0.0).key(6 / 24, 0.0).key(9 / 24, 1.0, 'out').key(D, 1.15)
        J = g.fig.pose(0.5)
        F = J['Rp'] @ V(0, 0, 1)
        Rr = J['Rp'] @ V(1, 0, 0)
        self.cam = Cam(Ch(J['H'] + F * 0.95 + Rr * 0.25 + V(0, -0.2, 0)).key(D, J['H'] + F * 0.85 + Rr * 0.23 + V(0, -0.2, 0)),
                       Ch(J['H'] + F * 0.15 + V(0, -0.18, 0)), fov=50)
        self.motes = [(hash01(97, i), hash01(98, i), hash01(99, i)) for i in range(50)]

    def orb_pos(self, t):
        J = self.g.fig.pose(t)
        return J['Wr'] + J['hup_r'] * 0.16 + J['Rc'] @ V(-0.07, 0.0, 0.05)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        f = float(self.form(s))
        paper(fr)
        red_wash(fr, 0.15 + 0.35 * f)
        draw_actors(fr, self.cam, s, s, [self.g])
        if f > 0:
            p = self.orb_pos(s)
            fx.orb(fr, cs, p, 0.04 * f, 'red', s, spin=1.0, seed=97, arcs=3)
            q = cs.proj(p)
            fx.light_wash(fr, q[0], q[1], 140 * f, RD['glow'], 0.18 * f, layer='g')
            # embers drifting slowly around the orb (only where it is)
            for i, (a, b, c) in enumerate(self.motes):
                ang = a * 6.28 + s * (0.5 + c)
                r = (60 + 380 * b) * f
                x, y = q[0] + math.cos(ang) * r, q[1] + math.sin(ang) * r * 0.7
                tw = 0.5 + 0.5 * math.sin(s * 10 + i)
                fr.g.drawCircle(x, y, 1.5 + 2 * c, paint(RD['mid'], 0.8 * tw * f, add=True))
        if 6 / 24 <= s < 8 / 24:
            fx.flash(fr, RD['glow'], 0.35)


# ============================================================================ 98: he throws it
class S98(Shot):
    t0, t1 = 2550 / 24, 2558 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo98'))
        g.k(0, yaw=math.pi - 0.2, root=V(0, 0.7, 0), lean=0.55, foot_l=V(-0.25, 0, 0.35), foot_r=V(0.3, 0, -0.35),
            hand_r=V(-0.25, 0.25, 0.25), hshape_r=shape('two'), hand_l=V(0.2, -0.1, 0.3), eye_glow=1.6, hpitch=-0.3)
        g.k(0.12, 'outexp', hand_r=V(0.25, -0.35, 0.45), hshape_r=shape('open'), twist=-0.5, lean=0.7, root=V(0, 0.62, 0.05))
        g.k(D, hand_r=V(0.3, -0.4, 0.4), twist=-0.55)
        self.cam = Cam(Ch(V(0.3, 1.5, -1.6)).key(D, V(0.25, 1.45, -1.5)), Ch(V(0.0, 1.0, 0)), fov=50, roll=-8)
        self.flame = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'red', size=0.06, trail=0.9, life=0.25, seed=98)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        red_wash(fr, 0.4)
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.render_flames(fr, cs, [self.flame], s)
        J = self.g.fig.pose(s)
        if s < 0.14:
            p = J['Wr'] + norm(J['Wr'] - J['Er']) * 0.15
            fx.orb(fr, cs, p, 0.05, 'red', s, seed=98)


# ============================================================================ 99: the orb flies around the buildings
class S99(Shot):
    t0, t1 = 2558 / 24, 2587 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.D = D
        pts = [V(-2, 6, -8), V(2, 5, 6), V(-4, 6, 20), V(3, 6, 34), V(10, 5, 44), V(14, 4, 58)]
        self.path = Ch(pts[0])
        for i, p in enumerate(pts[1:]):
            self.path.key(D * (i + 1) / (len(pts) - 1), p)
        self.blds = []
        for i in range(16):
            x = (-1) ** i * (6 + 6 * hash01(990, i))
            z = -10 + i * 6
            self.blds.append(Building(x - 2.5, x + 2.5, z, z + 4, 30 + 30 * hash01(991, i), base=-10, seed=990 + i,
                                      style='vstrips', win_density=0.6))
        o = lambda t: np.asarray(self.path(t))
        self.cam = Cam(lambda t: o(t - 0.12) + V(-1.5, 1.2, -4.5), lambda t: o(t), fov=58, roll=Ch(-15).key(D, 10))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        red_wash(fr, 0.2)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        set_blur(fr, self.cam, s, k=0.6, thresh=8, dist=8)
        p = np.asarray(self.path(s))
        tr = [np.asarray(self.path(s - 0.02 * (8 - i))) for i in range(8)]
        fx.orb(fr, cs, p, 0.45, 'red', s, spin=1.0, seed=99, arcs=4, trail=tr)
        q = cs.proj(p)
        fx.light_wash(fr, q[0], q[1], 260, RD['glow'], 0.2, layer='g')
        # sparks shed where it scrapes past a building (4-6 frames in)
        a = s - 3 / 24
        if 0 <= a < 0.4:
            fx.sparks(fr, cs, np.asarray(self.path(3 / 24)), a, n=40, pal='red', speed=8, life=0.4, seed=990)


# ============================================================================ 100: from far down the street, it comes back
class S100(Shot):
    t0, t1 = 2587 / 24, 2596 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk100'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo100'))
        stand(k, 0, 0.6, 0, math.pi, width=0.2)
        k.k(0, hand_l=V(-0.15, -0.3, 0.25), hand_r=V(0.15, -0.3, 0.25), eye_glow=1.2)
        stand(g, 0, -0.8, -0.8, 0.5, width=0.2)
        g.k(0, eye_glow=1.4, hand_r=V(0.2, -0.1, 0.3))
        self.orb = Ch(V(4.0, 1.4, 22.0)).key(D, V(0.6, 1.3, 0.3), 'in')
        self.cam = Cam(Ch(V(-1.0, 2.6, 30.0)).key(D, V(-0.9, 2.4, 24.0)), Ch(V(0.2, 1.2, 0.0)), fov=36)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        red_wash(fr, 0.15)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])
        p = np.asarray(self.orb(s))
        fx.orb(fr, cs, p, 0.45, 'red', s, seed=100, trail=[np.asarray(self.orb(s - 0.03 * (6 - i))) for i in range(6)])


# ============================================================================ 101: the blast throws Sukuna forward
class S101(Shot):
    t0, t1 = 2596 / 24, 2609 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk101'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo101'))
        k.k(0, yaw=math.pi, root=V(0.4, 0.95, 1.5), lean=-0.3, foot_l=V(0.2, 0.0, 1.6), foot_r=V(0.6, 0.0, 1.4),
            hand_l=V(-0.3, 0.1, -0.2), hand_r=V(0.3, 0.1, -0.2), eye_glow=1.3, hpitch=-0.4)
        k.k(0.15, 'out', root=V(0.3, 1.4, 0.3), lean=0.4, foot_l=V(0.1, 0.9, 1.0), foot_r=V(0.6, 0.7, 0.8), hand_l=V(-0.45, 0.3, 0.0),
            hand_r=V(0.45, 0.35, 0.0), hpitch=-0.6)
        k.k(D, root=V(0.25, 1.5, -0.2), lean=0.6, foot_l=V(0.1, 1.0, 0.4), foot_r=V(0.5, 0.85, 0.3))
        g.k(0, yaw=0.0, root=V(-0.9, 0.8, -1.2), lean=0.3, foot_l=V(-1.1, 0, -1.0), foot_r=V(-0.7, 0, -1.4), hand_r=V(0.15, -0.1, 0.3),
            fist_r=1, eye_glow=1.5, hpitch=-0.2)
        g.k(D, root=V(-0.85, 0.78, -1.15), lean=0.45, hand_r=V(0.1, 0.1, -0.2))
        self.burst = fx.Burst(V(0.6, 1.4, 2.8), 0.0, 'red', n=70, speed=5.0, size=0.5, life=0.8, seed=101, up=0.6, amp=0.36)
        self.cam = Cam(Ch(V(-1.6, 1.5, -2.4)).key(D, V(-1.5, 1.45, -2.1)), Ch(V(0.3, 1.4, 1.0)), fov=56, roll=6)
        self.cam.shake(0.0, 16, 0.4)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 1 / 24:
            paper(fr, (1.0, 0.85, 0.82))
            return
        draw_street(fr, cs)
        red_wash(fr, 0.3)
        fx.render_flames(fr, cs, [self.burst], s, fscale=0.22, warp=2.0)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])
        fx.sparks(fr, cs, V(0.4, 1.4, 2.4), s, n=50, pal='red', speed=9, life=0.6, seed=102)


# ============================================================================ 102: Gojo's eye, cyan light
class S102(Shot):
    t0, t1 = 2609 / 24, 2617 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo102'))
        stand(g, 0, 0, 0, math.pi + 0.5)
        g.k(0, hpitch=0.3, hroll=0.2, eye_glow=1.8, eye_fire=0.8, eye_open=1.1)
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.25, -0.05, -0.55)).key(D, H + V(-0.22, -0.05, -0.5)), Ch(H + V(0.05, 0, 0)), fov=44, roll=12)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 1 / 24:
            paper(fr, INK)
            fr.b.drawRect(skia.Rect(W * 0.2, 0, W * 0.32, H), paint((1, 1, 1)))
            return
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.g])
        u = (s - 3 / 24) / (4 / 24)
        if 0 < u < 1:
            x = -200 + (W + 400) * u
            fr.g.drawRect(skia.Rect(x - 120, 0, x + 120, H), paint(CY['glow'], 0.5, add=True, blur=60))
            fr.g.drawRect(skia.Rect(x - 20, 0, x + 20, H), paint(CY['mid'], 0.6, add=True, blur=10))


# ============================================================================ 103: Black Flash
class S103(Shot):
    t0, t1 = 2617 / 24, 2635 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk103'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo103'))
        stand(k, 0, 0.3, 0, -math.pi / 2 - 0.3, width=0.2)
        k.k(0, lean=0.15, hand_l=V(-0.1, -0.2, 0.25), hand_r=V(0.1, -0.2, 0.25), eye_glow=1.3, hpitch=0.0)
        k.k(5 / 24, hpitch=0.0, hroll=0.0)
        k.k(6 / 24, 'out', hroll=0.6, hyaw=0.7, hpitch=-0.3, lean=-0.3, root=V(0.45, 0.88, 0.0), twist=0.5)
        k.k(D, hroll=0.75, hyaw=0.85, lean=-0.4, root=V(0.6, 0.85, 0.05), twist=0.65)
        stand(g, 0, -0.55, 0.05, math.pi / 2 - 0.3, width=0.22, stagger=0.2)
        g.k(0, lean=0.4, twist=-0.4, hand_r=V(0.1, 0.0, -0.15), fist_r=1, eye_glow=1.6, eye_fire=0.8)
        J0 = k.fig.pose(5 / 24)
        g.fig.set(hand_rw=J0['H'] + V(-0.12, -0.02, 0.0))
        g.k(0, hand_rwb=0.0).k(3 / 24, hand_rwb=0.0).k(5.5 / 24, 'in', hand_rwb=1.0).k(D, hand_rwb=0.85)
        g.k(5.5 / 24, twist=0.6, lean=0.55, root=V(-0.4, 0.86, 0.05))
        self.hitstop(5.5 / 24, 4)
        self.P = J0['H'] + V(-0.1, 0, 0)
        self.cam = Cam(Ch(V(0.0, 1.7, -1.4)).key(D, V(0.05, 1.68, -1.25)), Ch(V(0.0, 1.5, 0)), fov=54, roll=-14)
        self.cam.shake(5.5 / 24, 22, 0.5).punch(5.5 / 24, 0.08)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        if s < 4 / 24:
            # impact frames: white/ink/red
            i = int(s * 24)
            paper(fr, ((1, 1, 1), INK, (0.85, 0.04, 0.1), (1, 1, 1))[i])
            col_ = (INK, (1, 1, 1), INK, (0.85, 0.04, 0.1))[i]
            for j in range(7):
                x = W * hash01(103, i, j)
                fr.b.drawLine(x, -20, x + (hash01(104, i, j) - 0.5) * 900, H + 20, paint(col_, 1.0, stroke=40 + 120 * hash01(105, i, j)))
            return
        draw_street(fr, cs)
        red_wash(fr, 0.5)
        draw_actors(fr, self.cam, s, tau, [self.k, self.g])
        a = s - 5.5 / 24
        q = cs.proj(self.P)
        if a >= 0:
            for j in range(5):
                seed = int(s * 24) * 11 + j
                ang = hash01(seed, 1) * 6.28
                L = 300 + 500 * hash01(seed, 2)
                black_bolt(fr, (q[0], q[1]), (q[0] + math.cos(ang) * L, q[1] + math.sin(ang) * L), seed, 8 + 6 * hash01(seed, 3),
                           max(0.0, 1 - a / 0.6))
            fx.impact_burst(fr, q[0], q[1], a, size=260, pal='red', seed=103, spikes=10, life=0.12)
            if a < 1 / 60:
                fr.impact = dict(bg=(0.85, 0.04, 0.1), fg=INK, energy=False, thr=0.3)


# ============================================================================ 104: both bent over, a pause
class S104(Shot):
    t0, t1 = 2635 / 24, 2656 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk104'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo104'))
        stand(k, 0, 0.35, 0, -math.pi / 2, width=0.2, h=0.15)
        k.k(0, lean=0.85, hpitch=0.6, hand_l=V(-0.05, -0.4, 0.2), hand_r=V(0.1, -0.35, 0.25), eye_glow=1.0, fist_r=0.5)
        k.k(D, lean=0.9, hpitch=0.7, root=V(0.37, 0.76, 0.0))
        stand(g, 0, -0.35, 0, math.pi / 2, width=0.2, h=0.12)
        g.k(0, lean=0.8, hpitch=0.65, hand_r=V(0.05, -0.2, 0.35), fist_r=1, hand_l=V(-0.05, -0.4, 0.15), eye_glow=1.2)
        g.k(D, lean=0.85, hpitch=0.7, root=V(-0.36, 0.79, 0.0))
        for a in (k, g):
            a.follow(['lean', 'hpitch'], 0, D, f=1.2, z=0.8, r=1.0)
        self.cam = Cam(Ch(V(0.0, 1.0, -1.9)).key(D, V(0.0, 1.0, -1.75)), Ch(V(0.0, 1.15, 0)), fov=50)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        red_wash(fr, 0.15)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])


# ============================================================================ 105: the wheel symbol
class S105(Shot):
    t0, t1 = 2656 / 24, 2672 / 24

    def draw(self, fr, s):
        D = self.t1 - self.t0
        i = int(s * 24)
        grey = 5 / 24 <= s < 8 / 24
        paper(fr, (0.72, 0.72, 0.72) if grey else INK)
        sc = 1.6 if s < 1 / 24 else (1.25 if s < 2 / 24 else 1.0 - 0.75 * smoothstep(10 / 24, D, s))
        cx, cy = W / 2, H / 2
        R = 300 * sc
        col_ = INK if grey else PAPER
        rot = s * 1.5 + (0.4 if grey else 0)
        c = fr.b
        c.drawCircle(cx, cy, R, paint(col_, 1.0, stroke=18 * sc))
        c.drawCircle(cx, cy, R * 0.16, paint(col_, 1.0))
        for j in range(8):
            th = rot + j * math.pi / 4
            x, y = cx + math.cos(th) * R, cy + math.sin(th) * R
            c.drawLine(cx, cy, x, y, paint(col_, 1.0, stroke=10 * sc))
            c.drawCircle(cx + math.cos(th) * R * 1.32, cy + math.sin(th) * R * 1.32, R * 0.15, paint(col_, 1.0))
        if grey:
            fr.post.append(fx.whip_blur(0, 0))


SHOTS = [S96, S97, S98, S99, S100, S101, S102, S103, S104, S105]
SEGMENTS = [(S96.t0, S105.t1)]
