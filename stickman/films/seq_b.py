"""Sequence B: shots 4-17 (frames 148-667): morgue, Gojo's eyes, rooftop trio, Fushiguro,
Gojo lying, Sukuna awakening, Gojo on the roof, memories."""
from films.common import *
from engine.env import Building, draw_buildings
from engine.rig import Style

SHOKO = DANCER.but(hair='long')
UTAHIME = DANCER


def city_ring(seed, r0=40, r1=120, n=36, y_top=-8, base=-80):
    """skyline all around the camera, roofs below the viewer's roof"""
    out = []
    for i in range(n):
        ang = 2 * math.pi * i / n + hash01(seed, i) * 0.12
        rr = r0 + (r1 - r0) * hash01(seed, i, 2)
        x, z = math.sin(ang) * rr, math.cos(ang) * rr
        w = 8 + 10 * hash01(seed, i, 3)
        h = (y_top - base) + 22 * hash01(seed, i, 4)
        out.append(Building(x - w / 2, x + w / 2, z - w / 2, z + w / 2, h, base=base, seed=seed * 50 + i,
                            style='vstrips', win_density=0.35))
    return out


# ============================================================================ shot 4: morgue
class S4(Shot):
    t0, t1 = 148 / 24, 219 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo4'))
        s = self.s = Actor(Figure(SHOKO, 0.97, 'shoko'))
        m = self.m = Actor(Figure(PLAIN, 1.08, 'fg4'))
        D = self.t1 - self.t0
        # Gojo behind the gurney, leaning on it with both hands, looking down at the body
        stand(g, 0, -0.15, 1.05, math.pi, width=0.17, h=0.06)
        g.k(0, lean=0.55, hpitch=0.45, hyaw=0.1, twist=0.05, fist_l=0.0, fist_r=0.0,
            elbow_l=V(-0.8, 0.2, -0.4), elbow_r=V(0.8, 0.2, -0.4), hand_lwb=1.0, hand_rwb=1.0, eye_open=0.6, eye_glow=0.3)
        g.fig.set(hand_lw=Ch(V(0.32, 0.86, 0.5)).key(1.2, V(0.30, 0.86, 0.52)).key(2.0, V(0.18, 0.84, 0.32)),
                  hand_rw=V(-0.55, 0.86, 0.5))
        g.k(1.0, lean=0.62, hpitch=0.55, root=V(-0.15, 0.80, 1.02))
        g.k(1.9, lean=0.70, hpitch=0.62, hyaw=-0.05, root=V(-0.12, 0.78, 0.98))
        g.k(D, lean=0.66, hpitch=0.58, root=V(-0.13, 0.79, 1.0))
        g.k(0, hshape_l=shape('relax'), hshape_r=shape('relax'))
        g.k(1.2, hshape_l=shape('relax')).k(1.9, hshape_l=shape('open'))
        # Shoko on the right: cigarette up to the lips, holds, lowers, exhales
        stand(s, 0, 1.75, 1.7, math.pi - 0.45, width=0.12, stagger=0.05)
        s.k(0, lean=0.0, hpitch=0.05, hyaw=-0.25, hand_r=V(-0.02, -0.45, 0.10), hand_l=V(0.10, -0.15, 0.18),
            elbow_l=V(-0.8, -0.4, 0.2), eye_glow=0.0, hshape_r=shape('relax'), hshape_l=shape('relax'))
        s.k(0.35, hand_r=V(-0.02, -0.40, 0.12))
        s.k(0.95, 'io', hand_r=V(-0.08, 0.12, 0.17), elbow_r=V(0.7, -0.6, 0.1), hshape_r=shape('pluck'), hpitch=-0.08)
        s.k(1.55, hand_r=V(-0.08, 0.13, 0.17))
        s.k(2.25, 'io', hand_r=V(-0.03, -0.20, 0.22), hpitch=0.02, hyaw=-0.35)
        s.k(D, hand_r=V(-0.02, -0.25, 0.22))
        # foreground silhouette (back to camera), weight shifting
        stand(m, 0, -1.55, -1.6, 0.25, width=0.17)
        m.k(0, hand_l=V(-0.06, -0.50, 0.04), hand_r=V(0.06, -0.50, 0.04), hpitch=0.1, hyaw=0.3, eye_glow=0.0)
        m.k(1.6, root=V(-1.53, 0.97, -1.62), hyaw=0.45, twist=0.08)
        m.k(D, root=V(-1.52, 0.96, -1.63), hyaw=0.5)
        for a in (g, s, m):
            a.follow(['hand_l', 'hand_r', 'hpitch', 'hyaw'], 0, D)
        self.cam = Cam(Ch(V(0.35, 1.55, -4.0)).key(D, V(0.25, 1.50, -3.55)),
                       Ch(V(0.15, 1.05, 1.0)).key(D, V(0.12, 1.02, 1.0)), fov=48)

    def cig(self, t):
        J = self.s.fig.pose(t)
        return J['Wr'] + norm(J['Wr'] - J['Er']) * 0.10

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # room: floor line, back wall with the drawer grid, ceiling light
        d3.line3(fr, cs, V(-6, 0, 3.2), V(6, 0, 3.2), w_m=0.02)
        d3.line3(fr, cs, V(-6, 3.2, 3.2), V(6, 3.2, 3.2), w_m=0.02)
        d3.line3(fr, cs, V(3.2, 0, -3), V(3.2, 0, 3.2), w_m=0.02)
        d3.line3(fr, cs, V(3.2, 0, 3.2), V(3.2, 3.2, 3.2), w_m=0.02)
        d3.grid_on_plane(fr, cs, V(-0.6, 0.15, 3.18), V(1, 0, 0), V(0, 1, 0), 4, 3, 0.95, 0.95, inset=0.06, w_m=0.012)
        d3.grid_on_plane(fr, cs, V(3.18, 0.15, 2.9), V(0, 0, -1), V(0, 1, 0), 3, 3, 0.95, 0.95, inset=0.06, w_m=0.012)
        q = cs.proj(V(0.2, 3.15, 1.8))
        fx.light_wash(fr, q[0], q[1], 260, (1.0, 1.0, 0.97), 0.55)
        # gurney with the covered body
        d3.box(fr, cs, V(-1.0, 0.78, 0.05), V(0.85, 0.84, 0.70), w_m=0.012)
        for x in (-0.9, 0.75):
            for z in (0.12, 0.62):
                d3.line3(fr, cs, V(x, 0.0, z), V(x, 0.78, z), w_m=0.02)
        d3.line3(fr, cs, V(-0.95, 0.30, 0.12), V(0.8, 0.30, 0.12), w_m=0.015)
        body = [V(-0.85, 0.84, 0.38) + V(math.cos(a) * 0.82, 0.12 * math.sin(a) * (1 if math.sin(a) > 0 else 0), 0) for a in np.linspace(0, math.pi, 12)]
        hump = [V(-0.02 + 0.82 * math.cos(a), 0.84 + 0.13 * math.sin(a), 0.38) for a in np.linspace(0, math.pi, 14)]
        d3.poly3(fr, cs, hump + [V(-0.84, 0.84, 0.38)], fill=PAPER, edge=d3.PENCIL, w_m=0.012)
        draw_actors(fr, self.cam, s, s, [self.g, self.s, self.m])
        d3.smoke(fr, cs, self.cig(s), s, seed=4, k=1.0)
        if s < 5 / 24:
            wipe_diag(fr, s / (5 / 24), reverse=True)


# ============================================================================ shot 5: Gojo's eyes
class S5(Shot):
    t0, t1 = 212 / 24, 268 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO_S, 1.06, 'gojo5'))
        D = self.t1 - self.t0
        stand(g, 0, 0, 0, math.pi)
        g.k(0, hroll=0.28, hyaw=-0.32, hpitch=0.20, eye_open=0.35, eye_glow=0.25, eye_fire=0.0, lean=0.05)
        g.k(0.8, eye_open=0.55, eye_glow=0.6)
        g.k(1.6, 'io', eye_open=1.0, eye_glow=1.25, hyaw=-0.22, hpitch=0.12, eye_fire=0.25)
        g.k(D, eye_open=1.0, eye_glow=1.35, hroll=0.24, hyaw=-0.18, hpitch=0.10, eye_fire=0.35)
        g.d.wind = V(-0.5, 0.1, 0.4)
        J = g.fig.pose(0)
        self.H = J['H']
        self.cam = Cam(Ch(self.H + V(-0.30, -0.02, -0.62)).key(D, self.H + V(-0.24, -0.02, -0.55)),
                       Ch(self.H + V(-0.04, -0.03, 0)), fov=40, roll=Ch(-6.0).key(D, -4.0))
        self.blds = skyline(5, n=30, z0=30, z1=110, spread=140, y_top=-2, base=-60)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=140)
        draw_actors(fr, self.cam, s, s, [self.g])


# ============================================================================ shot 6: rooftop trio
class S6(Shot):
    t0, t1 = 252 / 24, 298 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.o = Actor(Figure(OLDMAN, 0.95, 'old6'))
        self.g = Actor(Figure(GOJO_S, 1.06, 'gojo6'))
        self.u = Actor(Figure(UTAHIME, 0.96, 'uta6'))
        for a, x, z0, z1, ph in ((self.o, -1.05, 2.6, 1.55, 'r'), (self.g, 0.0, 2.3, 1.05, 'l'), (self.u, 1.05, 3.0, 1.95, 'r')):
            a.k(0, yaw=math.pi, hpitch=0.25, eye_glow=0.0, hshape_l=shape('relax'), hshape_r=shape('relax'))
            walk(a, -0.4, D + 0.3, V(x, 0, z0 + 0.35), V(x, 0, z1), math.pi, freq=1.25, first=ph, arms=0.12, lean=0.08)
        self.g.k(0, hpitch=0.38, eye_glow=0.9, eye_open=0.8, eye_fire=0.15)
        self.g.k(D, hpitch=0.30, eye_glow=1.1)
        self.u.k(0, hyaw=0.15).k(D, hyaw=0.05)
        self.o.k(0, hpitch=0.15, lean=0.15)
        for a in (self.g, self.u):
            a.d.wind = V(-0.6, 0.1, -0.2)
        self.cam = Cam(Ch(V(0.25, 1.45, -1.6)).key(D, V(0.18, 1.42, -1.95)),
                       Ch(V(0.05, 1.30, 2.0)).key(D, V(0.03, 1.28, 1.5)), fov=48)
        self.blds = city_ring(6, y_top=-6)

    def case(self, fr, cs, t):
        J = self.o.fig.pose(t)
        Rc, C = J['Rc'], J['C']
        a = C + Rc @ V(-0.05, 0.35, -0.16)
        b = C + Rc @ V(0.12, -0.75, -0.16)
        d3.line3(fr, cs, a, b, color=INK, w_m=0.17)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        for x in np.arange(-6, 6.1, 1.2):
            d3.line3(fr, cs, V(x, 0, 6), V(x, 1.1, 6), w_m=0.03)
        d3.line3(fr, cs, V(-6, 1.1, 6), V(6, 1.1, 6), w_m=0.04)
        d3.line3(fr, cs, V(-6, 0, 6), V(6, 0, 6), w_m=0.03)
        self.case(fr, cs, s)
        draw_actors(fr, self.cam, s, s, [self.o, self.u, self.g])
        if s > (298 - 252) / 24 - 1.5 / 24:
            flash_white(fr, (s - ((298 - 252) / 24 - 1.5 / 24)) / (1.5 / 24))


# ============================================================================ shot 7: Fushiguro turns
class S7(Shot):
    t0, t1 = 298 / 24, 335 / 24

    def setup(self):
        D = self.t1 - self.t0
        f = self.f = Actor(Figure(FUSHIGURO, 1.0, 'fushi7'))
        stand(f, 0, 0, 0, math.pi)
        f.k(0, hyaw=-1.25, hpitch=0.05, eye_glow=0.0, eye_open=0.9, twist=-0.15)
        f.k(0.30, hyaw=-1.15)
        f.k(1.05, 'io', hyaw=-0.30, hpitch=-0.04, twist=0.0, hroll=-0.05)
        f.k(D, hyaw=-0.22, hpitch=-0.06, hroll=-0.04)
        f.follow(['hyaw'], 0, D, f=2.5, z=0.6, r=1.0)
        H = f.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.35, -0.08, -0.80)).key(D, H + V(-0.32, -0.08, -0.74)), Ch(H + V(-0.12, -0.05, 0)), fov=40)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.f])
        d3.letterbox(fr, 0.11)
        if s < 6 / 24:
            flash_white(fr, 1 - s / (6 / 24))


# ============================================================================ shot 8: Gojo lying, eye opens
class S8(Shot):
    t0, t1 = 335 / 24, 392 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo8'))
        stand(g, 0, 0, 0, math.pi)
        g.k(0, hroll=0.0, hyaw=0.15, hpitch=0.0, eye_open=0.0, eye_glow=0.0, fist_r=1.0, idle=0.6,
            hand_r=V(-0.10, 0.20, 0.22), elbow_r=V(0.7, -0.7, 0.1), hand_l=V(0.0, -0.45, 0.1))
        g.k(1.45, eye_open=0.0, eye_glow=0.0)
        g.k(1.95, 'io', eye_open=1.0, eye_glow=1.2, hyaw=0.05, hand_r=V(-0.09, 0.22, 0.24))
        g.k(D, eye_open=1.0, eye_glow=1.3, eye_fire=0.2)
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.55, 0.05, -0.85)).key(D, H + V(0.48, 0.04, -0.75)), Ch(H + V(0.02, -0.12, 0)),
                       fov=44, roll=Ch(-72.0).key(D, -70.0))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        d3.line3(fr, cs, V(-3, -0.2, 0.5), V(3, -0.2, 0.5), w_m=0.02)
        draw_actors(fr, self.cam, s, s, [self.g])
        d3.letterbox(fr, 0.11)
        D = self.t1 - self.t0
        if s > D - 5 / 24:
            u = (s - (D - 5 / 24)) / (5 / 24)
            y = H * (1 - u ** 1.5)
            fr.b.drawRect(skia.Rect(0, y, W, H + 10), paint(INK))
            fr.g.drawRect(skia.Rect(0, y, W, H + 10), paint((0, 0, 0), 1, erase=True))


# ============================================================================ shot 9: Sukuna lying, marks light up
class S9(Shot):
    t0, t1 = 392 / 24, 440 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk9'))
        stand(k, 0, 0, 0, 0.0)
        k.k(0, hyaw=-1.35, hpitch=-0.1, eye_open=0.0, eye_glow=0.0, idle=0.4)
        k.k(D, hyaw=-1.30, hpitch=-0.14)
        self.marks = Ch(0.0).key(0.25, 0.0).key(1.3, 1.0, 'in').key(D, 1.0)
        H = k.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(-0.75, 0.05, 0.25)).key(D, H + V(-0.62, 0.05, 0.2)), Ch(H + V(0, -0.05, 0)), fov=40,
                       roll=Ch(85.0).key(D, 84.0))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, float(self.marks(s)) * (0.85 + 0.15 * fbm1(s * 9, 3)))
        D = self.t1 - self.t0
        if s > D - 3 / 24:
            fr.post.append(fx.chroma_split(6))


# ============================================================================ shot 10: red/black flash, open mouth
class S10(Shot):
    t0, t1 = 440 / 24, 449 / 24

    def setup(self):
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk10'))
        stand(k, 0, 0, 0, 0.3)
        k.k(0, lean=-0.55, hpitch=-0.75, twist=0.3, hand_l=V(-0.25, 0.35, 0.25), hand_r=V(0.3, 0.45, 0.1),
            elbow_l=V(-0.8, 0.3, -0.3), elbow_r=V(0.8, 0.3, -0.3), hshape_l=shape('claw'), hshape_r=shape('claw'))
        k.k(9 / 24, lean=-0.70, hpitch=-0.95, hand_l=V(-0.3, 0.42, 0.3))
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.6, -0.5, 1.0)).key(9 / 24, H + V(0.5, -0.45, 0.85)), Ch(H + V(-0.05, -0.25, 0)), fov=50, roll=18)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k], smear=0.0)
        mouth(fr, cs, J, self.k.fig, 1.0, smile=-0.3, width=0.6, open_=0.9, color=(0.85, 0.03, 0.08))
        red_two_tone(fr, invert=(int(s * 24) % 4) >= 2)


# ============================================================================ shot 11: in front of the red curtain
class S11(Shot):
    t0, t1 = 449 / 24, 515 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk11'))
        # kneeling, bent far over, hands on the floor; slowly rises, head coming up
        k.k(0, yaw=math.pi / 2, root=V(0, 0.52, 0), lean=1.25, curve=0.4, hpitch=0.9, foot_l=V(-0.55, 0.0, 0.14),
            foot_r=V(-0.6, 0.0, -0.14), knee_l=V(0, -0.2, 1), knee_r=V(0, -0.2, 1), hand_lwb=1.0, hand_rwb=1.0,
            eye_open=0.0, eye_glow=0.0, hshape_l=shape('open'), hshape_r=shape('open'))
        k.fig.set(hand_lw=V(0.52, 0.02, 0.20), hand_rw=V(0.50, 0.02, -0.18))
        k.k(0.9, lean=1.20, hpitch=0.75, root=V(0.02, 0.55, 0))
        k.k(1.9, 'io', lean=0.95, hpitch=0.35, root=V(0.0, 0.66, 0), hand_lwb=0.7, hand_rwb=0.7, curve=0.2)
        k.k(D, lean=0.78, hpitch=0.12, root=V(-0.02, 0.72, 0), hand_lwb=0.45, hand_rwb=0.45, hyaw=0.2)
        k.follow(['hpitch', 'lean'], 0, D, f=2.0, z=0.7, r=0.8)
        self.cam = Cam(Ch(V(0.15, 0.55, -2.0)).key(D, V(0.12, 0.6, -1.75)), Ch(V(0.12, 0.82, 0)), fov=44)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        # the red curtain (set colour), folds swaying slowly
        paper(fr, (0.62, 0.05, 0.09))
        for i in range(14):
            x = -200 + i * 170 + 35 * math.sin(s * 0.8 + i)
            fr.b.drawLine(x, -10, x + 30 * math.sin(i), H * 0.72, paint((0.42, 0.02, 0.05), 0.75, stroke=40 + 25 * hash01(i, 1), blur=18))
        # floor: ink band with a soft top edge
        q = cs.proj(V(0, 0, 4))
        fr.b.drawRect(skia.Rect(0, q[1], W, H), paint(INK))
        draw_actors(fr, self.cam, s, s, [self.k])


class S12(Shot):
    """red/ink flash: head in profile"""
    t0, t1 = 515 / 24, 516 / 24

    def setup(self):
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk12'))
        stand(k, 0, 0, 0, -math.pi / 2)
        k.k(0, hpitch=-0.2)
        H = k.fig.pose(0)['H']
        self.cam = Cam(H + V(0.0, -0.1, -1.0), H + V(0, -0.15, 0), fov=50)

    def draw(self, fr, s):
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.k], smear=0)
        red_two_tone(fr)


class S13(Shot):
    """red/ink flash: hand over the forehead, the other arm raised"""
    t0, t1 = 516 / 24, 523 / 24

    def setup(self):
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk13'))
        stand(k, 0, 0, 0, math.pi)
        k.k(0, hpitch=-0.35, lean=-0.2, hand_r=V(-0.05, 0.32, 0.18), hand_l=V(-0.35, 0.40, 0.0),
            elbow_l=V(-0.7, 0.6, -0.2), hshape_r=shape('claw'), hshape_l=shape('open'))
        k.k(7 / 24, hpitch=-0.5, lean=-0.3, hand_l=V(-0.4, 0.48, -0.05))
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.1, -0.6, -1.1)).key(7 / 24, H + V(0.08, -0.55, -0.95)), H + V(0, -0.3, 0), fov=55, roll=-8)

    def draw(self, fr, s):
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.k], smear=0)
        red_two_tone(fr, invert=s > 3 / 24)


# ============================================================================ shot 14: Sukuna opens his eyes
class S14(Shot):
    t0, t1 = 523 / 24, 597 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk14'))
        stand(k, 0, 0, 0, math.pi)
        k.k(0, hpitch=0.42, eye_open=0.0, eye_glow=0.0, eye_fire=0.0)
        k.k(0.85, eye_open=0.0, eye_glow=0.0)
        k.k(1.9, 'io', eye_open=1.0, eye_glow=1.1, hpitch=0.30)
        k.k(2.6, eye_fire=0.5, eye_glow=1.3, hpitch=0.22)
        k.k(D, eye_open=1.0, eye_glow=1.35, eye_fire=0.6, hpitch=0.18)
        self.smile = Ch(0.0).key(2.2, 0.0).key(D, 1.0, 'io')
        self.H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(self.H + V(0.0, -0.18, -0.95)).key(D, self.H + V(0.0, -0.16, -0.78)), Ch(self.H + V(0, -0.08, 0)), fov=40)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # red vignette around the frame edge
        p = skia.Paint()
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.45), W * 0.62,
                                                   [col((0.75, 0.05, 0.1), 0.0), col((0.75, 0.05, 0.1), 0.0), col((0.72, 0.04, 0.09), 0.85)],
                                                   [0.0, 0.55, 1.0]))
        fr.b.drawRect(skia.Rect(0, 0, W, H), p)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.55)
        sm = float(self.smile(s))
        if sm > 0.02:
            mouth(fr, cs, J, self.k.fig, sm, smile=0.9 * sm, width=0.5)


# ============================================================================ shot 15: Gojo's back on the roof
class S15(Shot):
    t0, t1 = 597 / 24, 633 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO_S, 1.06, 'gojo15'))
        stand(g, 0, 0, 0, 0.35, width=0.17, stagger=0.06)
        g.k(0, hand_l=V(-0.08, -0.48, 0.0), hand_r=V(0.08, -0.48, 0.0), hpitch=-0.05, hyaw=0.0, eye_glow=0.6)
        g.k(0.8, hyaw=0.0)
        g.k(1.4, 'io', hyaw=0.45, twist=0.08)
        g.k(D, hyaw=0.55, twist=0.10)
        g.follow(['hyaw'], 0, D, f=2.0, z=0.6, r=1.0)
        g.d.wind = V(-1.0, 0.25, 0.3)
        self.cam = Cam(Ch(V(-0.6, 0.9, -3.0)).key(D, V(-0.45, 0.92, -2.6)), Ch(V(0.4, 1.35, 2.0)), fov=46, roll=-3)
        self.blds = city_ring(15, y_top=-5)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fx.light_wash(fr, W * 0.95, H * 0.66, 520, (0.9, 0.35, 0.35), 0.22)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        d3.line3(fr, cs, V(-8, 0, 1.2), V(8, 0, 1.2), w_m=0.03)
        draw_actors(fr, self.cam, s, s, [self.g])


# ============================================================================ shot 16: whip to Gojo's face
class S16(Shot):
    t0, t1 = 633 / 24, 650 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO_S, 1.06, 'gojo16'))
        stand(g, 0, 0, 0, math.pi + 0.5)
        g.k(0, hyaw=0.55, hpitch=0.05, eye_open=1.0, eye_glow=1.2, eye_fire=0.25)
        g.k(0.22, 'out', hyaw=0.05, hpitch=0.0)
        g.k(D, hyaw=-0.02, hpitch=0.02)
        g.follow(['hyaw'], 0, D, f=3.0, z=0.5, r=1.4)
        g.d.wind = V(-0.8, 0.2, 0.2)
        H = g.fig.pose(0.3)['H']
        self.cam = Cam(Ch(H + V(0.2, -0.05, -0.85)).key(D, H + V(0.15, -0.05, -0.80)),
                       Ch(H + V(-2.0, 0.1, 0)).key(0.12, H + V(-0.05, -0.05, 0), 'out').key(D, H + V(-0.03, -0.05, 0)), fov=38)
        self.blds = city_ring(16, y_top=-4)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        draw_actors(fr, self.cam, s, s, [self.g])
        cam_blur(fr, self.cam, s, k=0.6, thresh=20)


# ============================================================================ shot 17: memories
class S17(Shot):
    t0, t1 = 649 / 24, 667 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO_S, 1.06, 'gojo17'))
        stand(g, 0, 0.0, 0, math.pi - 0.35)
        g.k(0, hpitch=0.15, eye_glow=1.1, eye_open=0.9).k(D, hpitch=0.12, hyaw=-0.08)
        g.d.wind = V(-0.4, 0.1, 0.1)
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.55, -0.15, -1.15)).key(D, H + V(-0.5, -0.15, -1.05)), Ch(H + V(-0.45, -0.18, 0)), fov=46)
        # pencil-grey memory figures on the left (friends), drifting slowly
        self.mem = []
        for i, st in enumerate([PLAIN.but(hair='sukuna'), PANDA, FUSHIGURO, PLAIN.but(hair='long'), PLAIN.but(hair='short')]):
            a = Actor(Figure(st, 0.9, 'mem%d' % i))
            x = -1.05 - 0.35 * (i % 3) + 0.05 * i
            y = 0.25 * (i // 3)
            stand(a, 0, x, 0.6 + 0.25 * i, math.pi - 0.2 + 0.15 * i, y=y - 0.15)
            a.k(0, eye_glow=0.0, hpitch=0.1 * (i - 2), hand_r=V(0.1 * (i % 2), -0.2 + 0.25 * (i % 2), 0.25))
            a.k(D, root=a.fig.g('root', 0) + V(0.04, 0.03 * (-1) ** i, 0))
            a.draw_opts = dict(silhouette=(0.62, 0.60, 0.57))
            self.mem.append(a)

    def draw(self, fr, s):
        paper(fr)
        draw_actors(fr, self.cam, s, s, self.mem + [self.g])
        if s < 3 / 24:
            flash_white(fr, 1 - s / (3 / 24))


SHOTS = [S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17]
SEGMENTS = [(S4.t0, S17.t1)]
