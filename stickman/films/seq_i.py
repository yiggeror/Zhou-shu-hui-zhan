"""Sequence I: shots 84-95 (frames 2233-2511): the standoff, the wheel, the third exchange."""
from films.common import *
from films.seq_h import draw_street, ring
from engine.env import Building

CY = fx.PAL['cyan']
RD = fx.PAL['red']
SUK_W = SUKUNA.but(extras=('wheel',))


# ============================================================================ 84: standoff, Sukuna's back
class S84(Shot):
    t0, t1 = 2233 / 24, 2276 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk84'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo84'))
        stand(k, 0, 0.6, -1.0, 0.15, width=0.2)
        k.k(0, hand_l=V(-0.08, -0.45, 0.05), hand_r=V(0.08, -0.45, 0.05), eye_glow=1.2, hpitch=0.05)
        k.k(D, hyaw=-0.1, hpitch=0.08)
        g.k(0, yaw=math.pi + 0.2, root=V(-1.6, 0.5, 8.0), lean=0.85, foot_l=V(-1.85, 0, 8.3), foot_r=V(-1.3, 0, 7.6),
            hand_l=V(0.05, -0.2, 0.25), hand_r=V(-0.05, -0.3, 0.2), hpitch=-0.5, eye_glow=1.4)
        g.k(D * 0.6, root=V(-1.6, 0.52, 7.9), lean=0.8)
        g.k(D, root=V(-1.55, 0.55, 7.85), lean=0.75, hpitch=-0.55)
        self.cam = Cam(Ch(V(1.6, 1.4, -3.2)).key(D, V(1.4, 1.38, -2.8)), Ch(V(-0.3, 1.0, 6.0)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.g, self.k])


class S85(Shot):
    """reverse: Gojo's back low in front, Sukuna far off with the wheel above his head"""
    t0, t1 = 2269 / 24, 2307 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk85'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo85'))
        stand(k, 0, 0.6, -1.0, math.pi + 0.15, width=0.2)
        k.k(0, hand_l=V(0.045, 0.02, 0.28), hand_r=V(-0.045, 0.02, 0.28), hshape_l=shape('flat'), hshape_r=shape('flat'),
            hup_l=V(0, 1, 0.15), hup_r=V(0, 1, 0.15), hback_l=V(-1, 0, 0), hback_r=V(1, 0, 0), eye_glow=1.3)
        g.k(0, yaw=math.pi + 0.2, root=V(-1.6, 0.5, 8.0), lean=0.85, foot_l=V(-1.85, 0, 8.3), foot_r=V(-1.3, 0, 7.6),
            hand_l=V(0.05, -0.2, 0.25), hand_r=V(-0.05, -0.3, 0.2), hpitch=-0.5, eye_glow=1.4)
        g.k(D, root=V(-1.55, 0.56, 7.85), lean=0.72, hpitch=-0.45)
        self.cam = Cam(Ch(V(-3.3, 1.15, 10.2)).key(D, V(-3.1, 1.15, 9.6)), Ch(V(0.9, 1.4, -1.0)), fov=40)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])


# ============================================================================ 86: fists flash, then Sukuna's bleeding eyes
class S86(Shot):
    t0, t1 = 2307 / 24, 2340 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk86'))
        stand(k, 0, 0, 0, math.pi - 0.9)
        k.k(0, hpitch=0.3, eye_glow=1.6, eye_fire=1.0, hand_r=V(-0.05, 0.05, 0.3), fist_r=1.0)
        k.k(D, hpitch=0.32, hroll=0.05)
        H = k.fig.pose(0)['H']
        self.H = H
        F = k.fig.pose(0)['Rp'] @ V(0, 0, 1)
        Rr = k.fig.pose(0)['Rp'] @ V(1, 0, 0)
        self.cam = Cam(Ch(H + F * 0.55 - Rr * 0.25 + V(0, -0.15, 0)).key(D, H + F * 0.5 - Rr * 0.22 + V(0, -0.15, 0)),
                       Ch(H + V(0, -0.08, 0)), fov=46, roll=8)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 3 / 24:
            # fists: close flash, then red/ink
            paper(fr, (1.0, 1.0, 1.0))
            from engine.hand import draw_hand, SHAPES
            cam = Cam(V(0, 0, -0.6), V(0, 0, 0), fov=50).at(s)
            for i, (x, side) in enumerate(((-0.11, -1), (0.11, 1))):
                Rh = np.stack([V(0, 1, 0), V(side * -1.0, 0, 0), V(0, 0, -1)], axis=1)
                draw_hand(fr.b, cam, V(x + side * 0.05, -0.02 + 0.03 * i + 0.02 * s * 24, 0), Rh, np.array(SHAPES['fist']), side, INK, 1.0, 1.8,
                          width_m=0.012)
            if s >= 2 / 24:
                red_two_tone(fr)
            return
        paper(fr, (1.0, 1.0, 1.0))
        fx.light_wash(fr, 0, H * 0.3, 900, (1, 1, 1), 1.0)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.9)
        # blood running from the eyes
        Rh, Hc = J['Rh'], J['H']
        R = self.k.fig.L['head']
        age = s - 3 / 24
        for (x, y, sp) in ((-0.40, 0.05, 1.0), (0.40, 0.05, 0.8), (-0.33, -0.25, 0.7), (0.33, -0.25, 0.6)):
            z = math.sqrt(max(0.0, 1 - x * x - y * y))
            top = cs.proj(Hc + Rh @ V(x, y - 0.1, z) * R)
            L = 260 * sp * min(1.0, 0.2 + age * 1.5)
            fr.b.drawLine(top[0], top[1], top[0] + 6, top[1] + L, paint((0.82, 0.04, 0.09), 1.0, stroke=12 * sp + 4))


# ============================================================================ 87: Gojo reaches, then makes a fist
class S87(Shot):
    t0, t1 = 2340 / 24, 2360 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo87'))
        g.k(0, yaw=math.pi - 0.3, root=V(0, 0.75, 0), lean=0.55, foot_l=V(-0.2, 0, 0.3), foot_r=V(0.25, 0, -0.35),
            hand_r=V(-0.05, 0.0, 0.62), hshape_r=shape('open'), hup_r=V(0, 0.4, 1), hback_r=V(0, 1, 0), hand_l=V(0.0, -0.3, 0.2),
            eye_glow=1.6, eye_fire=0.5, hpitch=-0.15)
        g.k(0.3, hshape_r=shape('open'))
        g.k(0.5, 'in', hshape_r=shape('fist'), lean=0.6)
        g.k(D, hshape_r=shape('fist'))
        J = g.fig.pose(0)
        F = J['Rp'] @ V(0, 0, 1)
        Hh = J['H']
        g.fig.set(hand_rw=Ch(Hh + F * 0.55 + V(0.05, -0.12, 0)).key(0.3, Hh + F * 0.58 + V(0.05, -0.12, 0))
                  .key(0.5, Hh + F * 0.42 + V(0.04, -0.2, 0), 'in').key(D, Hh + F * 0.40 + V(0.04, -0.22, 0)))
        g.k(0, hand_rwb=1.0)
        self.cam = Cam(Ch(J['H'] + F * 1.2 + V(0.3, -0.2, 0)).key(D, J['H'] + F * 1.1 + V(0.28, -0.2, 0)), Ch(J['H'] + F * 0.35 + V(0, -0.2, 0)), fov=52)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        mouth(fr, cs, J, self.g.fig, 1.0, smile=0.9, width=0.5, open_=0.25)


# ============================================================================ 88: white field, two silhouettes trade blows
class S88(Shot):
    t0, t1 = 2360 / 24, 2377 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk88'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo88'))
        k.k(0, yaw=-math.pi / 2, root=V(-0.6, 1.1, 0), lean=-0.3, foot_l=V(-0.3, 0.6, 0.1), foot_r=V(-0.9, 0.5, -0.1),
            hand_l=V(-0.2, 0.2, 0.2), hand_r=V(0.25, 0.3, 0.1), fist_l=1, fist_r=1, knee_l=V(0, 0.5, 1))
        k.k(D, root=V(-0.95, 1.0, 0), lean=-0.45, foot_l=V(-0.7, 0.45, 0.1), foot_r=V(-1.3, 0.35, -0.1), hand_r=V(0.3, 0.4, 0.0))
        g.k(0, yaw=-math.pi / 2, root=V(0.7, 0.8, 0), lean=0.3, foot_l=V(0.4, 0, 0.2), foot_r=V(1.2, 0, -0.15), hand_r=V(0.1, 0.1, -0.2),
            fist_r=1, fist_l=1, hand_l=V(0.0, -0.1, 0.3), eye_glow=0.0)
        g.k(0.15, hand_r=V(0.12, 0.12, -0.25))
        g.k(0.35, 'outexp', hand_r=V(-0.05, 0.35, 0.55), twist=0.5, lean=0.45, root=V(0.55, 0.78, 0))
        g.k(D, hand_r=V(-0.08, 0.40, 0.58), twist=0.55)
        self.flame = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.07, seed=88, amount=Ch(0.0).key(0.3, 0.0).key(0.4, 1.0))
        self.cam = Cam(Ch(V(0.1, 1.0, -4.0)).key(D, V(0.05, 1.0, -3.8)), Ch(V(0.0, 1.0, 0)), fov=40)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 1.5 / 24:
            paper(fr, INK)
            return
        paper(fr, (1.0, 1.0, 1.0))
        draw_actors(fr, self.cam, s, s, [self.k, self.g], eyes=False)
        fx.render_flames(fr, cs, [self.flame], s)
        d3.letterbox(fr, 0.16)


# ============================================================================ 89-90: cyan and red fists cross; the horizontal blow
class S89(Shot):
    t0, t1 = 2377 / 24, 2392 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk89'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo89'))
        stand(g, 0, -0.3, 0, math.pi / 2, width=0.2, stagger=0.15)
        g.k(0, lean=0.4, twist=0.4, hand_r=V(-0.15, 0.15, 0.6), fist_r=1, hand_l=V(0.0, -0.1, 0.25), eye_glow=1.5)
        g.k(D, hand_r=V(-0.18, 0.18, 0.62), twist=0.45)
        stand(k, 0, 0.35, 0.05, -math.pi / 2, width=0.2, stagger=0.15)
        k.k(0, lean=0.4, twist=0.4, hand_r=V(-0.15, 0.2, 0.62), fist_r=1, hand_l=V(0.0, -0.1, 0.25), eye_glow=1.3, hpitch=0.2)
        k.k(0.2, 'out', root=V(0.45, 0.9, 0.05), hpitch=-0.1, lean=0.2)
        k.k(D, root=V(0.5, 0.9, 0.05))
        self.fl = [fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.12, src2=lambda t: g.fig.pose(t)['Er'], seg=(0.2, 1.0), seed=89),
                   fx.Flame(lambda t: k.fig.pose(t)['Wr'], 'red', size=0.1, src2=lambda t: k.fig.pose(t)['Er'], seg=(0.3, 1.0), seed=90)]
        self.cam = Cam(Ch(V(-0.2, 1.65, -1.0)).key(D, V(-0.15, 1.62, -0.9)), Ch(V(0.1, 1.45, 0)), fov=52, roll=-12)
        self.cam.shake(0, 10, 0.3)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])
        fx.render_flames(fr, cs, self.fl, s)
        if s < 2 / 24:
            fr.post.append(fx.whip_blur(160 * (1 - s / (2 / 24)), 0))


class S90(Shot):
    t0, t1 = 2392 / 24, 2407 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo90'))
        stand(g, 0, -0.4, 0, math.pi / 2, width=0.22, stagger=0.2)
        g.k(0, lean=0.35, twist=-0.5, hand_r=V(0.15, 0.0, -0.2), fist_r=1, hand_l=V(0.0, -0.05, 0.35), fist_l=1, eye_glow=1.6, eye_fire=0.5)
        g.k(0.1, 'outexp', hand_r=V(-0.05, 0.12, 0.68), twist=0.55, lean=0.5, root=V(-0.25, 0.88, 0))
        g.k(D, hand_r=V(-0.06, 0.13, 0.7), twist=0.6)
        self.hitstop(0.1, 3)
        self.flame = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.13, src2=lambda t: g.fig.pose(t)['Er'], seg=(0.0, 1.0),
                              seed=91, trail=0.7, life=0.3)
        self.cam = Cam(Ch(V(0.2, 1.3, -1.7)).key(D, V(0.15, 1.3, -1.55)), Ch(V(0.1, 1.25, 0)), fov=50)
        self.cam.shake(0.1, 16, 0.3)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, tau, [self.g])
        fx.render_flames(fr, cs, [self.flame], tau)
        a = s - 0.1
        J = self.g.fig.pose(tau)
        if a >= 0:
            q = cs.proj(J['Wr'] + V(0.15, 0, 0))
            fx.impact_burst(fr, q[0], q[1], a, size=150, pal='cyan', seed=90, spikes=7, life=0.1)
            fx.sparks(fr, cs, J['Wr'], a, n=24, pal='cyan', speed=4, life=0.5, seed=92, dirv=V(1, 0.2, 0), cone=1.0)
        if s < 1.5 / 24:
            fr.post.append(fx.whip_blur(200 * (1 - s / (1.5 / 24)), 30))


# ============================================================================ 91: the wheel, red light turning blue
class S91(Shot):
    t0, t1 = 2407 / 24, 2435 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk91'))
        stand(k, 0, 0, 0, 0.2, width=0.2)
        k.k(0, hand_l=V(-0.15, -0.2, 0.25), hand_r=V(0.15, -0.2, 0.25), fist_l=1, fist_r=1, hpitch=0.1, eye_glow=1.2)
        k.k(D, hpitch=0.15, hyaw=0.15)
        k.d.wheel_turn = 0.0
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.6, 0.3, -1.1)).key(D, H + V(-0.5, 0.25, -0.95)), Ch(H + V(0.2, 0.15, 2.0)), fov=56, roll=-10)
        self.col = Ch(0.0).key(0.4, 0.0).key(D, 1.0, 'io')

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        u = float(self.col(s))
        c = tuple(RD['glow'][i] * (1 - u) + CY['glow'][i] * u for i in range(3))
        fx.light_wash(fr, W * 0.65, H * 0.8, 600, c, 0.45)
        self.k.d.wheel_turn = s * 2.5
        draw_actors(fr, self.cam, s, s, [self.k])


# ============================================================================ 92: over the shoulder, Gojo dashes in low
class S92(Shot):
    t0, t1 = 2435 / 24, 2449 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk92'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo92'))
        stand(k, 0, 0, 0, 0.0, width=0.2)
        k.k(0, hand_l=V(-0.15, -0.2, 0.25), hand_r=V(0.15, -0.2, 0.25), fist_l=1, fist_r=1, eye_glow=1.2)
        x = Ch(-7.0).key(D, -0.9, 'in')
        path = lambda t: V(float(x(t)) * 0.15, 0, -float(x(t)) * -1.0 + 0.0) if False else V(0.3, 0, 7.0 + (float(x(t)) + 7.0) * -0.98)
        g.k(0, yaw=math.pi, eye_glow=1.5, hand_l=V(0.05, -0.3, -0.2), hand_r=V(-0.05, -0.3, -0.25), fist_l=1, fist_r=1)
        bake_run = __import__('engine.moves', fromlist=['bake_run']).bake_run
        bake_run(g, -0.1, D, path, math.pi, freq=3.4, stride_lead=0.45, lift=0.25, base_h=0.62, bob=0.04, lean=0.9)
        self.trail = fx.Flame(lambda t: g.fig.pose(t)['Tl'], 'cyan', size=0.07, rise=0.1, trail=0.9, life=0.35, seed=92)
        self.cam = Cam(Ch(V(0.8, 1.7, -1.2)).key(D, V(0.75, 1.65, -1.05)), Ch(V(0.0, 0.7, 6.0)).key(D, V(0.0, 0.7, 2.0)), fov=50, roll=6)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.g, self.k])
        fx.render_flames(fr, cs, [self.trail], s)


# ============================================================================ 93: the collision, sparks
class S93(Shot):
    t0, t1 = 2449 / 24, 2475 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk93'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo93'))
        stand(k, 0, 0.25, 0, -math.pi / 2, width=0.2, stagger=0.15)
        k.k(0, lean=0.2, hand_l=V(0.0, 0.1, 0.35), hand_r=V(0.1, -0.1, 0.3), fist_l=1, fist_r=1, eye_glow=1.3, hpitch=0.1)
        k.k(0.08, 'out', root=V(0.45, 0.88, 0), lean=-0.15, hpitch=-0.25)
        k.k(D, root=V(0.55, 0.86, 0), lean=-0.1)
        g.k(0, yaw=math.pi / 2, root=V(-0.35, 0.75, 0), lean=0.85, foot_l=V(-0.05, 0, 0.2), foot_r=V(-0.95, 0.1, -0.1),
            hand_l=V(0.05, 0.3, 0.45), fist_l=1, hand_r=V(0.0, -0.1, 0.2), fist_r=1, hpitch=-0.3, eye_glow=1.5)
        g.k(0.08, root=V(-0.2, 0.8, 0), lean=0.7)
        g.k(D, root=V(-0.1, 0.82, 0), lean=0.6, hand_l=V(0.08, 0.35, 0.5))
        self.hitstop(0.06, 4)
        self.C = V(0.1, 1.45, 0.0)
        self.cam = Cam(Ch(V(0.0, 1.5, -1.3)).key(D, V(0.05, 1.5, -1.15)), Ch(V(0.05, 1.3, 0)), fov=54, roll=-14)
        self.cam.shake(0.06, 18, 0.4)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, tau, [self.k, self.g])
        a = s - 0.06
        if a >= 0:
            q = cs.proj(self.C)
            fx.impact_burst(fr, q[0], q[1], a, size=200, pal='white', seed=93, spikes=10, life=0.12)
            for j in range(4):
                fx.sparks(fr, cs, self.C, a - 0.08 * j, n=16, pal='red' if j % 2 else 'cyan', speed=5, life=0.5, seed=930 + j)
            fx.light_wash(fr, q[0], q[1], 260, (1.0, 0.7, 0.4), 0.35 * max(0.0, 1 - a), layer='g')


# ============================================================================ 94: Gojo twists away, grinning
class S94(Shot):
    t0, t1 = 2475 / 24, 2486 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo94'))
        g.k(0, yaw=math.pi / 2, root=V(0, 1.1, 0), lean=0.3, twist=0.6, foot_l=V(0.3, 0.6, 0.2), foot_r=V(-0.4, 0.5, -0.2),
            hand_l=V(-0.3, 0.1, -0.1), hand_r=V(0.3, 0.2, 0.2), eye_glow=1.6, eye_fire=0.6, hpitch=0.1)
        g.k(D, yaw=math.pi / 2 - 1.0, twist=1.0, root=V(-0.2, 1.15, 0.1), hand_l=V(-0.4, 0.2, -0.2))
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.2, -0.15, -0.9)).key(D, H + V(-0.25, -0.15, -0.85)), Ch(H + V(0, -0.15, 0)), fov=50, roll=-15)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        mouth(fr, cs, J, self.g.fig, 1.0, smile=1.0, width=0.55, open_=0.3)
        D = self.t1 - self.t0
        if s > D - 2 / 24:
            fr.post.append(fx.whip_blur(-220, 40))


# ============================================================================ 95: the swing from above, a ring far off
class S95(Shot):
    t0, t1 = 2486 / 24, 2511 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo95'))
        g.k(0, yaw=math.pi / 2 + 0.4, root=V(0, 20.0, 0), lean=0.9, foot_l=V(-0.4, 19.6, 0.3), foot_r=V(-0.6, 19.4, -0.2),
            hand_r=V(0.1, 0.35, -0.2), fist_r=1, hand_l=V(-0.1, -0.1, 0.3), hpitch=-0.4, eye_glow=1.4)
        g.k(0.15, 'outexp', hand_r=V(-0.05, -0.25, 0.55), twist=0.6)
        g.k(D, hand_r=V(-0.08, -0.35, 0.5), twist=0.7, root=V(0.1, 19.8, 0))
        self.ring_c = V(6.0, 4.0, 40.0)
        self.cam = Cam(Ch(V(-1.2, 20.6, -1.6)).key(D, V(-1.1, 20.5, -1.45)), Ch(V(1.5, 18.5, 8.0)), fov=54, roll=-20)
        from films.seq_b import city_ring
        self.city = city_ring(95, y_top=0, r0=30)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        from engine.env import draw_buildings
        draw_buildings(fr, cs, self.city, fog_dist=200)
        # the far shock ring
        q = cs.proj(self.ring_c)
        r = (80 + 260 * s) * (1.0)
        fr.g.drawCircle(q[0], q[1], r, paint((0.85, 0.9, 1.0), 0.8 * max(0, 1 - s), stroke=10, add=True))
        fr.g.drawCircle(q[0], q[1], r, paint((0.85, 0.9, 1.0), 0.35 * max(0, 1 - s), stroke=40, add=True, blur=16))
        draw_actors(fr, self.cam, s, s, [self.g])


SHOTS = [S84, S85, S86, S87, S88, S89, S90, S91, S92, S93, S94, S95]
SEGMENTS = [(S84.t0, S95.t1)]
