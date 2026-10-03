"""Sequence L: shots 118-125 (frames 2967-3272): Red gathers, Mahoraga, Hollow Purple."""
from films.common import *
from engine.env import Building, draw_buildings
from films.seq_b import city_ring
from films.seq_d import violet_wash, lavender_flash

CY = fx.PAL['cyan']
RD = fx.PAL['red']
BL = fx.PAL['blue']
MG = fx.PAL['magenta']
GOJO_C = GOJO


def night_city(seed, y_top=-4, r0=30, r1=120, n=40):
    return city_ring(seed, r0=r0, r1=r1, n=n, y_top=y_top)


# ============================================================================ 118: red sparks gather around him
class S118(Shot):
    t0, t1 = 2967 / 24, 3006 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo118'))
        stand(g, 0, 0, 0, math.pi - 0.15, width=0.18)
        g.k(0, hand_r=V(-0.08, -0.05, 0.25), hshape_r=shape('two'), hand_l=V(0.05, -0.15, 0.22), eye_glow=1.4, hpitch=0.1)
        g.k(D, hand_r=V(-0.07, 0.0, 0.27), hpitch=0.0, eye_glow=1.6)
        g.d.wind = V(0.3, 0.1, 0.0)
        self.cam = Cam(Ch(V(0.4, 1.0, -5.5)).key(D, V(0.3, 1.05, -4.6)), Ch(V(0, 1.15, 0)), fov=40)
        self.city = night_city(118, y_top=-6)
        self.sp = [(hash01(118, i), hash01(119, i), hash01(120, i)) for i in range(70)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=150)
        d3.box(fr, cs, V(-6, -40, -2), V(6, 0, 4), w_m=0.03)
        draw_actors(fr, self.cam, s, s, [self.g])
        if s < 2 / 24:
            wipe_diag(fr, s / (2 / 24), ang=0.0, reverse=True)
        u = smoothstep(0.5, D, s)
        if u > 0:
            fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.85, 0.4, 0.42), 0.25 * u))
            J = self.g.fig.pose(s)
            c = cs.proj(J['C'])
            for i, (a, b, cc) in enumerate(self.sp):
                if b > u:
                    continue
                ang = a * 6.28 + s * (1.5 + cc)
                r = 120 + 520 * cc * (1 - 0.3 * u)
                p0 = (c[0] + math.cos(ang) * r, c[1] + math.sin(ang) * r * 0.75)
                p1 = (c[0] + math.cos(ang - 0.18) * r, c[1] + math.sin(ang - 0.18) * r * 0.75)
                fr.g.drawLine(p0[0], p0[1], p1[0], p1[1], paint(RD['mid'], 0.9, stroke=3 + 3 * cc, add=True))
            q = cs.proj(J['Wr'])
            fx.orb(fr, cs, J['Wr'] + V(0, 0.08, -0.05), 0.03 * u, 'red', s, seed=118)


# ============================================================================ 119: finger to the sky
class S119(Shot):
    t0, t1 = 3006 / 24, 3042 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo119'))
        stand(g, 0, 0, 0, math.pi - 0.25)
        g.k(0, hand_r=V(-0.05, 0.25, 0.2), hshape_r=shape('point'), hup_r=V(0, 1, 0), hback_r=V(0, 0, -1), hand_l=V(0.08, 0.05, 0.25),
            hshape_l=shape('two'), eye_glow=1.5, hpitch=-0.15)
        g.k(0.3, 'out', hand_r=V(0.0, 0.62, 0.05))
        g.k(D, hand_r=V(0.0, 0.64, 0.04), hpitch=-0.2)
        H = g.fig.pose(0.5)['H']
        self.cam = Cam(Ch(H + V(0.25, -0.95, -0.85)).key(D, H + V(0.22, -0.9, -0.78)), Ch(H + V(-0.05, 0.25, 0)), fov=54)
        self.flash_t = (3030 - 3006) / 24

    def tip(self, t):
        J = self.g.fig.pose(t)
        return J['Wr'] + J['hup_r'] * 0.2

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        red = 1.0 if s < self.flash_t + 3 / 24 else max(0.0, 1 - (s - self.flash_t - 3 / 24) / (2 / 24))
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.85, 0.12, 0.16), 0.55 * red))
        for i in range(30):
            ang = hash01(119, i) * 6.28 + s * 2
            r = 200 + 700 * hash01(120, i)
            q0 = (W * 0.5 + math.cos(ang) * r, H * 0.4 + math.sin(ang) * r)
            fr.g.drawLine(q0[0], q0[1], q0[0] + math.cos(ang + 1.5) * 60, q0[1] + math.sin(ang + 1.5) * 60,
                          paint(RD['mid'], 0.7 * red, stroke=4, add=True))
        draw_actors(fr, self.cam, s, s, [self.g])
        p = self.tip(s)
        if red > 0:
            fx.orb(fr, cs, p, 0.035, 'red', s, seed=119, k=red)
        a = s - self.flash_t
        if 0 <= a < 3 / 24:
            q = cs.proj(p)
            for j in range(16):
                ang = math.pi / 2 + (hash01(1190, j) - 0.5) * 1.6
                L = 900 + 700 * hash01(1191, j)
                fr.g.drawLine(q[0], q[1], q[0] + math.cos(ang) * L, q[1] + math.sin(ang) * L, paint((1, 0.85, 0.85), 0.8, stroke=30, add=True, blur=12))
            fx.flash(fr, (1.0, 0.75, 0.75), 0.4 * (1 - a / (3 / 24)))


# ============================================================================ 120: Mahoraga bounds over the city
class S120(Shot):
    t0, t1 = 3042 / 24, 3080 / 24

    def setup(self):
        D = self.t1 - self.t0
        m = self.m = Actor(Figure(MAHORAGA, 1.45, 'maho120'))
        jt = 7 / 24
        z = lambda t: 10 + 14 * (t - jt)
        m.k(0, visible=0.0).k(jt - 0.01, visible=0.0).k(jt, visible=1.0)
        n = 12
        for i in range(n + 1):
            t = jt + (D - jt) * i / n
            m.k(t, yaw=0.0, root=V(0.0, 18 + 2.0 * math.sin((t - jt) * 2.5), z(t)), lean=0.6, twist=0.2 * math.sin(t * 3),
                foot_l=V(-0.4, 17.4, z(t) - 0.8), foot_r=V(0.5, 17.0, z(t) - 1.2), hand_l=V(-0.6, 0.3, 0.2), hand_r=V(0.65, 0.2, 0.25),
                fist_l=1, fist_r=1, knee_l=V(0, 0.5, 1))
        self.city = []
        for i in range(-3, 4):
            for j in range(0, 10):
                h = 6 + 22 * hash01(120, i, j)
                self.city.append(Building(i * 9 - 3.5, i * 9 + 3.5, j * 9, j * 9 + 7, h, base=-10, seed=1200 + i * 13 + j, style='vstrips'))
        self.cam = Cam(lambda t: V(0.5, 21.0, z(max(t, jt)) - 6.0), lambda t: V(0.0, 15.0, z(max(t, jt)) + 4.0), fov=56, roll=8)
        self.whip = Cam(Ch(V(-20, 30, 0)).key(5 / 24, V(20, 26, 10)), Ch(V(0, 10, 20)), fov=70)

    def draw(self, fr, s):
        D = self.t1 - self.t0
        if s < 5 / 24:
            cs = self.whip.at(s)
            paper(fr)
            draw_buildings(fr, cs, self.city, fog_dist=150)
            fr.post.append(fx.whip_blur(260, 60))
            return
        if s < 7 / 24:
            paper(fr, INK)
            return
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=150)
        u = smoothstep(D * 0.55, D, s)
        if u > 0:
            fx.light_wash(fr, 0, H * 0.4, 900, (0.3, 0.8, 1.0), 0.3 * u)
            fx.light_wash(fr, W, H * 0.4, 900, (1.0, 0.3, 0.35), 0.3 * u)
        draw_actors(fr, self.cam, s, s, [self.m])


# ============================================================================ 121: Red and Blue meet above Gojo
class S121(Shot):
    t0, t1 = 3080 / 24, 3118 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.Tm = Tm = (3115 - 3080) / 24
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo121'))
        k = self.k = Actor(Figure(SUKUNA.but(extras=('wheel',)), 1.0, 'suk121'))
        m = self.m = Actor(Figure(MAHORAGA, 1.45, 'maho121'))
        # Gojo hovering above the building, arms raised to the two orbs
        self.red0, self.blue0 = V(-1.6, 4.4, 0.4), V(1.6, 4.4, 0.4)
        self.meet = V(0.0, 3.75, 0.45)
        ease = lambda u: u * u * (3 - 2 * u)
        self.redp = lambda t: self.red0 + (self.meet + V(-0.02, 0, 0) - self.red0) * ease(clamp((t - 0.25) / (Tm - 0.25), 0, 1)) ** 1.4
        self.bluep = lambda t: self.blue0 + (self.meet + V(0.02, 0, 0) - self.blue0) * ease(clamp((t - 0.25) / (Tm - 0.25), 0, 1)) ** 1.4
        g.k(0, yaw=math.pi, root=V(0.0, 2.1, 0.6), lean=-0.05, hpitch=-0.45, foot_l=V(0.18, 1.25, 0.55), foot_r=V(-0.18, 1.2, 0.7),
            eye_glow=1.5, eye_fire=0.6, hand_lwb=1.0, hand_rwb=1.0, hshape_l=shape('claw'), hshape_r=shape('claw'))
        R, B = self.redp, self.bluep
        g.fig.set(hand_lw=lambda t: B(t) + V(0.12, -0.35, 0.0), hand_rw=lambda t: R(t) + V(-0.12, -0.35, 0.0))
        g.k(D, root=V(0.0, 2.15, 0.6), hpitch=-0.6)
        # Sukuna falling in from the right, Mahoraga leaping from the left
        k.k(0, yaw=-math.pi * 0.75, root=V(4.0, 3.2, 2.5), lean=0.3, foot_l=V(3.9, 2.5, 2.3), foot_r=V(4.3, 2.35, 2.8),
            hand_l=V(0.1, 0.2, 0.3), hand_r=V(-0.2, 0.25, 0.3), fist_l=1, fist_r=1, eye_glow=1.3, eye_fire=0.6)
        k.k(D, root=V(3.3, 1.9, 2.0), foot_l=V(3.2, 1.2, 1.8), foot_r=V(3.6, 1.05, 2.3), lean=0.4, hpitch=0.3)
        m.k(0, yaw=math.pi * 0.62, root=V(-5.2, 2.6, 3.2), lean=0.35, twist=-0.4, foot_l=V(-4.8, 1.75, 3.5), foot_r=V(-6.1, 1.4, 2.8),
            hand_r=V(0.25, 0.3, -0.45), hand_l=V(-0.1, 0.1, 0.45), fist_l=1, fist_r=1, knee_l=V(0, 0.4, 1))
        m.k(D, root=V(-3.9, 3.3, 2.6), foot_l=V(-3.5, 2.5, 2.9), foot_r=V(-4.8, 2.15, 2.2), hand_r=V(0.2, 0.4, -0.3))
        self.roof = Building(-2.0, 2.0, -0.2, 4.0, 60, base=-58.6, seed=5, style='grid')
        self.blds = city_ring(121, y_top=-10, r0=25, n=40)
        self.cam = Cam(Ch(V(0.5, -1.6, -8.2)).key(D, V(0.25, -1.1, -6.6)), Ch(V(-0.3, 2.9, 1.2)).key(D, V(-0.2, 3.0, 1.2)), fov=48)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        u = smoothstep(0.0, self.Tm, s)
        paper(fr)
        # sky coloured by the two lights: blue on one side, red on the other, purple as they meet
        fx.light_wash(fr, 0, 0, 1000, (0.4, 0.75, 1.0), 0.3)
        fx.light_wash(fr, W, 0, 1000, (1.0, 0.35, 0.4), 0.3)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        self.roof.draw(fr, cs, fog_dist=200)
        if u > 0.6:
            qm = cs.proj(self.meet)
            fx.light_wash(fr, qm[0], qm[1], 700, (0.75, 0.55, 1.0), 0.35 * (u - 0.6) / 0.4)
        draw_actors(fr, self.cam, s, s, [self.m, self.k, self.g])
        tr = lambda f: [f(s - 0.03 * (6 - i)) for i in range(6)]
        fx.orb(fr, cs, self.redp(s), 0.22, 'red', s, spin=1.0, seed=1, trail=tr(self.redp))
        fx.orb(fr, cs, self.bluep(s), 0.22, 'blue', s, spin=-1.0, seed=2, trail=tr(self.bluep))
        d = float(np.linalg.norm(self.redp(s) - self.bluep(s)))
        if d < 1.6:
            qa, qb = cs.proj(self.redp(s)), cs.proj(self.bluep(s))
            kk = clamp((1.6 - d) / 1.4, 0, 1)
            seed = int(s * 30)
            fx.bolt(fr, qa[:2], qb[:2], seed, 'magenta', 2.0 + 2 * kk, 0.5 + 0.5 * kk, jag=0.3)
        a = s - self.Tm
        if a >= 0:
            q = cs.proj(self.meet)
            fx.orb(fr, cs, self.meet, 0.3 + a * 3, 'magenta', s, seed=3)
            fx.impact_burst(fr, q[0], q[1], a, size=260, pal='magenta', seed=9, spikes=10, life=0.1)
            r = 80 + 2600 * a
            fr.g.drawCircle(q[0], q[1], r, paint(MG['mid'], 0.6 * max(0, 1 - a * 6), stroke=8, add=True))
        if s < 0.3:
            fr.post.append(fx.defocus(8.0 * (1 - s / 0.3) ** 1.5))


# ============================================================================ 122: Sukuna guards against the purple light
class S122(Shot):
    t0, t1 = 3118 / 24, 3154 / 24
    vignette = 0.15

    def setup(self):
        D = self.t1 - self.t0
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'suk122'))
        s.k(0, yaw=-math.pi * 0.80, root=V(0, 0.90, 0), lean=0.05, twist=0.15, hpitch=0.05, hyaw=0.15,
            foot_l=V(-0.2, 0, 0.1), foot_r=V(0.2, 0, -0.2), fist_l=1, fist_r=1, eye_glow=1.4, eye_fire=0.8,
            hand_l=V(0.05, -0.2, 0.25), hand_r=V(-0.05, -0.2, 0.25))
        s.k(0.35, 'io', hand_l=V(0.30, 0.16, 0.40), elbow_l=V(-0.9, -0.4, 0.5), hand_r=V(0.02, -0.30, 0.05),
            elbow_r=V(0.8, -0.3, -0.4), lean=0.12, hpitch=0.12)
        s.k(D, hand_l=V(0.26, 0.22, 0.46), lean=0.32, hpitch=0.28, hyaw=0.35, twist=0.35, root=V(0.12, 0.86, 0.10))
        J = s.fig.pose(0.0)
        Hh = J['H']
        F = J['Rh'] @ V(0, 0, 1)
        self.cam = Cam(Ch(Hh + F * 1.30 + V(0.25, -0.02, 0)).key(D, Hh + F * 0.95 + V(0.12, 0.0, 0)),
                       Ch(Hh + V(-0.05, -0.12, 0)), fov=44, roll=Ch(6.0))
        self.cam.shake(0.0, 3, 1.5, 9)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        u = smoothstep(0.0, D, s)
        paper(fr)
        violet_wash(fr, 0.35 + 0.3 * u)
        fx.light_wash(fr, -100, 100, 900 + 1100 * u, (0.65, 0.25, 1.0), 0.25 + 0.6 * u ** 1.5)
        fx.light_wash(fr, -100, 100, 400 + 700 * u, (0.92, 0.8, 1.0), 0.1 + 0.6 * u ** 2)
        draw_actors(fr, self.cam, s, s, [self.s])
        face_marks(fr, cs, self.s.fig.pose(s), self.s.fig, 0.8)
        fx.light_wash(fr, -100, 100, 600 + 600 * u, (0.7, 0.35, 1.0), 0.08 + 0.25 * u, layer='g')


# ============================================================================ 123: one eye, backlit
class S123(Shot):
    t0, t1 = 3154 / 24, 3194 / 24
    vignette = 0.12

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo123'))
        g.k(0, yaw=math.pi, root=V(0, 0.95, 0), hpitch=-0.05, hroll=0.04, eye_glow=1.3, eye_fire=0.4,
            eye_r=0.08, eye_l=1.0, eye_open=0.9, foot_l=V(0.15, 0, 0), foot_r=V(-0.15, 0, 0))
        g.k(D, eye_glow=1.7, eye_fire=0.6, eye_open=1.0, hpitch=-0.12, hyaw=0.12, hroll=-0.03)
        Hh = g.fig.pose(0.0)['H']
        self.H = Hh
        self.cam = Cam(Ch(Hh + V(0.06, -0.08, -1.0)).key(D, Hh + V(-0.02, -0.05, -0.62)), Ch(Hh + V(0, -0.06, 0)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        u = smoothstep(0.0, D, s)
        paper(fr)
        violet_wash(fr, 0.5)
        q = cs.proj(self.H + V(0, -0.1, 0.6))
        # the light swells behind the head: violet outside, lavender inside, a white-ish centre late
        fx.light_wash(fr, q[0], q[1], 600 + 900 * u ** 1.3, (0.55, 0.2, 1.0), 0.3 + 0.6 * u ** 1.5)
        fx.light_wash(fr, q[0], q[1], 400 + 900 * u ** 1.3, (0.9, 0.75, 1.0), 0.1 + 0.8 * u ** 2)
        fx.light_wash(fr, q[0], q[1], 200 + 800 * u ** 1.5, (1.0, 0.97, 1.0), 0.6 * u ** 3)
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.light_wash(fr, q[0], q[1], 600 + 700 * u, (0.7, 0.4, 1.0), 0.04 + 0.12 * u, layer='g')


# ============================================================================ 124: he stands on the roof, the camera rushes back, the light rises
class S124(Shot):
    t0, t1 = 3194 / 24, 3200 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo124'))
        g.k(0, yaw=math.pi, root=V(0, 0.95, 0), foot_l=V(-0.22, 0, 0.0), foot_r=V(0.22, 0, 0.05), hand_l=V(-0.45, 0.28, 0.05),
            hand_r=V(0.45, 0.28, 0.05), hshape_l=shape('open'), hshape_r=shape('open'), hpitch=-0.15, eye_glow=1.5)
        g.k(D, root=V(0, 1.2, 0), foot_l=V(-0.2, 0.3, 0.05), foot_r=V(0.2, 0.25, 0.1), hand_l=V(-0.5, 0.35, 0.0), hand_r=V(0.5, 0.35, 0.0))
        g.d.wind = V(0.6, 0.2, 0)
        # fast pull-back: starts close, rushes away and up
        self.cam = Cam(Ch(V(0.3, 0.6, -6.0)).key(3 / 24, V(1.5, 4.0, -55.0), 'outexp').key(D, V(1.6, 4.5, -62.0)),
                       Ch(V(0.0, 1.4, 0.0)).key(3 / 24, V(0.0, 3.0, 0.0), 'outexp'), fov=46)
        self.roof = Building(-3.0, 3.0, -2.0, 3.0, 60, base=-60, seed=124, ink=True, color=(0.20, 0.08, 0.30))
        self.blds = skyline(124, n=50, z0=-20, z1=60, spread=200, hmin=-30, hmax=-6, base=-80, ink=True)
        self.bloom_t = 3 / 24

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        violet_wash(fr, 1.2)
        fx.streak_lines(fr, -0.06, 124, n=40, color=(0.95, 0.75, 1.0), alpha=0.7, width=7, length=(500, 1500), layer='g', band=(0, H * 0.6))
        draw_buildings(fr, cs, self.blds, fog_dist=400)
        self.roof.draw(fr, cs, fog_dist=400)
        draw_actors(fr, self.cam, s, s, [self.g], silhouette=(0.15, 0.05, 0.22))
        a = s - self.bloom_t
        if a >= 0:
            c = self.g.fig.pose(s)['C']
            fx.orb(fr, cs, c, 0.6 + 14 * a, 'magenta', s, seed=124, arcs=4)
            q = cs.proj(c)
            fx.light_wash(fr, q[0], q[1], 300 + 3000 * a, (0.95, 0.85, 1.0), 0.6, layer='g')


class S124b(Shot):
    """tracking sideways behind the skyline; the sphere of light rises behind it"""
    t0, t1 = 3200 / 24, 3222 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.C = V(0, 30, 160)
        self.blds = []
        for i in range(30):
            x = -60 + i * 4.2 + 2 * hash01(1241, i)
            z = 30 + 40 * hash01(1242, i)
            self.blds.append(Building(x - 1.8, x + 1.8, z, z + 4, 30 + 30 * hash01(1243, i), base=-10, seed=1240 + i, ink=True,
                                      color=(0.18, 0.07, 0.27)))
        self.fg = [Building(x - 2, x + 2, 6, 9, 60, base=-10, seed=1250 + j, ink=True, color=(0.10, 0.04, 0.15))
                   for j, x in enumerate((-3.0, 9.0, 16.0))]
        self.cam = Cam(Ch(V(-6.0, 6.0, 0)).key(D, V(14.0, 6.5, 0), 'lin'), lambda t: V(-6.0 + 20 * t / D, 14, 100), fov=50)
        self.r = Ch(14.0).key(D, 40.0, 'in')

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        violet_wash(fr, 1.2)
        fx.streak_lines(fr, -0.05, 125, n=30, color=(0.95, 0.75, 1.0), alpha=0.6, width=6, length=(600, 1600), layer='g', band=(0, H * 0.55))
        q = cs.proj(self.C)
        rp = float(self.r(s)) * cs.scale(q[2])
        dome(fr, q[0], q[1], rp, 0.4)
        draw_buildings(fr, cs, self.blds, fog_dist=500, occlude_glow=True)
        for b in self.fg:
            b.draw(fr, cs, fog_dist=500)


def dome(fr, x, y, rp, glow):
    """layered sphere of light: violet halo, magenta body, lavender inner, small hot core (never flat white)"""
    fr.g.drawCircle(x, y, rp * 2.2, paint((0.55, 0.15, 0.95), 0.35 + 0.3 * glow, add=True, blur=rp * 0.9))
    pb = skia.Paint(AntiAlias=True)
    pb.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), rp,
                                                [col((1.00, 0.92, 1.0), 1, 1.5), col((0.92, 0.65, 1.0), 1, 1.3),
                                                 col((0.75, 0.30, 1.0), 1, 1.15), col((0.48, 0.10, 0.85), 1, 1.0)],
                                                [0.0, 0.3, 0.7, 1.0]))
    fr.b.drawCircle(x, y, rp, pb)
    fr.g.drawCircle(x, y, rp * 0.5, paint((0.95, 0.8, 1.0), 0.45, add=True, blur=rp * 0.25))
    fr.g.drawCircle(x, y, rp, paint((0.9, 0.65, 1.0), 0.8, stroke=max(2, rp * 0.02), add=True, blur=rp * 0.01))


class S124c(Shot):
    """the light swallows the city"""
    t0, t1 = 3222 / 24, 3261 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.C = V(0, 10, 150)
        self.blds = []
        for i in range(40):
            x = -70 + i * 3.6 + 2 * hash01(1244, i)
            z = 25 + 40 * hash01(1245, i)
            self.blds.append(Building(x - 1.6, x + 1.6, z, z + 4, 22 + 26 * hash01(1246, i), base=-10, seed=1260 + i, ink=True,
                                      color=(0.18, 0.07, 0.27)))
        self.cam = Cam(Ch(V(10.0, 6.0, 0)).key(D, V(16.0, 6.0, 4.0)), Ch(V(14, 14, 100)), fov=52)
        self.r = Ch(40.0).key(D, 170.0, 'in')
        self.cam.shake(0.3, 6, D, 14)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        violet_wash(fr, 1.2)
        q = cs.proj(self.C)
        rp = float(self.r(s)) * cs.scale(q[2])
        dome(fr, q[0], q[1], rp, smoothstep(0, D, s))
        if s < 1.5 / 24:
            fr.b.drawRect(skia.Rect(0, 0, W * 0.7, H), paint((0.1, 0.04, 0.15)))
        # the skyline is eaten from the top: buildings fade into the light as it reaches them
        k = smoothstep(D * 0.4, D, s)
        draw_buildings(fr, cs, self.blds, fog_color=(0.85, 0.6, 1.0), fog_dist=400 - 330 * k)
        # particles at the edge of the light
        for i in range(60):
            ang = math.pi + hash01(1247, i) * math.pi
            rr = rp * (0.98 + 0.08 * hash01(1248, i))
            x, y = q[0] + math.cos(ang) * rr, q[1] + math.sin(ang) * rr * 0.4
            fr.g.drawCircle(x, y, 2 + 3 * hash01(1249, i), paint((0.95, 0.8, 1.0), 0.8, add=True))


# ============================================================================ 125: white, the purple edge recedes
class S125(Shot):
    t0, t1 = 3261 / 24, 3272 / 24

    def draw(self, fr, s):
        D = self.t1 - self.t0
        u = smoothstep(0.0, D, s)
        paper(fr, (0.99, 0.97, 1.0))
        h = H * (0.22 * (1 - u))
        if h > 1:
            p = skia.Paint()
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, H - h), skia.Point(0, H)],
                                                       [col((0.99, 0.97, 1.0)), col((0.55, 0.15, 0.9))]))
            fr.b.drawRect(skia.Rect(0, H - h, W, H), p)


SHOTS = [S118, S119, S120, S121, S122, S123, S124, S124b, S124c, S125]
SEGMENTS = [(S118.t0, S125.t1)]
