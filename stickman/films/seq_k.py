"""Sequence K: shots 106-117 (frames 2672-2967): Mahoraga, the chase, Blue."""
from films.common import *
from films.seq_h import draw_street
from films.seq_i import SUK_W
from engine.env import Building, draw_buildings
from films.seq_b import city_ring

CY = fx.PAL['cyan']
RD = fx.PAL['red']
BL = fx.PAL['blue']


def tilted_city(seed, n=30):
    out = []
    for i in range(n):
        x = (hash01(seed, i) - 0.5) * 60
        z = 5 + 70 * hash01(seed, i, 1)
        w = 4 + 6 * hash01(seed, i, 2)
        out.append(Building(x - w / 2, x + w / 2, z, z + w, 40 + 50 * hash01(seed, i, 3), base=-60, seed=seed * 10 + i,
                            style='vstrips', win_density=0.6))
    return out


# ============================================================================ 106: before the white light, arm raised
class S106(Shot):
    t0, t1 = 2672 / 24, 2727 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo106'))
        stand(g, 0, 0, 0, math.pi - 0.35, width=0.2)
        g.k(0, hand_r=V(0.10, 0.35, 0.22), elbow_r=V(0.8, 0.0, -0.5), hshape_r=shape('relax'), hand_l=V(0.0, -0.35, 0.15),
            eye_glow=1.3, hpitch=-0.05, hyaw=0.1)
        g.k(D * 0.5, hand_r=V(0.12, 0.38, 0.2), hyaw=0.05)
        g.k(D, hand_r=V(0.12, 0.40, 0.18), hyaw=0.0, hpitch=-0.1)
        g.follow(['hyaw', 'hpitch'], 0, D, f=1.5, z=0.7, r=1.0)
        H = g.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(0.4, -0.45, -1.4)).key(D - 2 / 24, H + V(0.36, -0.42, -1.3)).key(D, H + V(0.2, -0.3, -0.8), 'in'),
                       Ch(H + V(0.1, -0.25, 0)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 3 / 24:
            paper(fr, INK)
            fr.b.drawRect(skia.Rect(W * 0.18, 0, W * 0.24, H), paint((1, 1, 1)))
            fr.g.drawRect(skia.Rect(W * 0.14, 0, W * 0.28, H), paint((0.9, 0.95, 1.0), 0.6, add=True, blur=40))
            draw_actors(fr, self.cam, s, s, [self.g], silhouette=PAPER, eyes=True)
            return
        paper(fr, (1.0, 1.0, 1.0))
        # the blade edge (Mahoraga's) at the top left
        fr.b.drawPath(poly_path([(W * 0.18, 0), (W * 0.3, 0), (W * 0.2, H * 0.22), (W * 0.12, H * 0.2)], closed=True), paint(INK))
        draw_actors(fr, self.cam, s, s, [self.g])


# ============================================================================ 107: Mahoraga swings, Gojo flips away
class S107(Shot):
    t0, t1 = 2727 / 24, 2746 / 24

    def setup(self):
        D = self.t1 - self.t0
        m = self.m = Actor(Figure(MAHORAGA, 1.45, 'maho107'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo107'))
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk107'))
        m.k(0, yaw=0.7, root=V(-2.0, 1.4, 1.0), lean=0.4, foot_l=V(-1.7, 0, 1.5), foot_r=V(-2.6, 0, 0.4), hand_r=V(0.3, 0.4, -0.3),
            elbow_r=V(0.6, 0.6, -0.6), hand_l=V(-0.2, -0.2, 0.4), fist_l=1, fist_r=1)
        m.k(0.25, 'outexp', hand_r=V(-0.2, -0.3, 0.8), twist=0.6, lean=0.7, root=V(-1.7, 1.3, 1.3))
        m.k(D, hand_r=V(-0.3, -0.45, 0.7), twist=0.7, lean=0.75)
        # Gojo: low crouch, then a twisting flip up and back
        g.k(0, yaw=-0.6, root=V(0.0, 0.55, 2.0), lean=0.8, foot_l=V(-0.2, 0, 2.3), foot_r=V(0.3, 0, 1.6), hand_l=V(0.1, -0.2, 0.3),
            hand_r=V(-0.1, -0.3, 0.2), eye_glow=1.4)
        g.k(0.22, 'out', root=V(0.6, 1.6, 2.6), lean=-0.6, twist=1.2, foot_l=V(0.3, 1.2, 3.0), foot_r=V(0.9, 1.4, 2.4),
            hand_l=V(-0.4, 0.2, 0.1), hand_r=V(0.4, 0.2, 0.0), yaw=0.5)
        g.k(D, root=V(1.2, 1.4, 3.2), lean=-1.2, twist=2.0, foot_l=V(1.0, 1.9, 3.6), foot_r=V(1.5, 2.0, 3.0), yaw=1.5)
        stand(k, 0, 2.8, 4.5, -2.4, width=0.2)
        k.k(0, hand_r=V(0.2, -0.1, 0.4), eye_glow=1.2).k(D, hand_r=V(0.25, 0.0, 0.45))
        self.cam = Cam(Ch(V(0.4, 0.5, -2.8)).key(D, V(0.6, 0.6, -2.4)), Ch(V(0.2, 1.0, 2.0)).key(D, V(0.6, 1.3, 2.5)), fov=60, roll=-8)
        self.flame = fx.Flame(lambda t: k.fig.pose(t)['Wr'], 'red', size=0.08, seed=107)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 2 / 24:
            paper(fr, (1, 1, 1))
            fr.b.drawRect(skia.Rect(0, 0, W * (1 - s * 12), H), paint(INK))
            return
        draw_street(fr, cs)
        fx.streak_lines(fr, 0.15, int(s * 30), n=30, alpha=0.3, width=3, band=(H * 0.6, H))
        draw_actors(fr, self.cam, s, s, [self.k, self.m, self.g])
        fx.render_flames(fr, cs, [self.flame], s)


# ============================================================================ 108: Sukuna's red slash chases him
class S108(Shot):
    t0, t1 = 2746 / 24, 2756 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk108'))
        k.k(0, yaw=-0.3, root=V(0.0, 2.0, 0), lean=0.6, foot_l=V(-0.3, 1.5, -0.4), foot_r=V(0.3, 1.3, -0.3), hand_r=V(0.4, 0.2, -0.1),
            hshape_r=shape('flat'), hand_l=V(-0.1, 0.1, 0.3), eye_glow=1.4)
        k.k(0.2, 'outexp', hand_r=V(-0.3, -0.25, 0.6), twist=0.7)
        k.k(D, hand_r=V(-0.35, -0.3, 0.55), twist=0.8)
        self.cam = Cam(Ch(V(-0.8, 2.4, -1.8)).key(D, V(-0.7, 2.3, -1.6)), Ch(V(0.1, 2.0, 0.5)), fov=56, roll=-20)
        self.trail = fx.Flame(lambda t: k.fig.pose(t)['Wr'], 'red', size=0.16, trail=1.0, life=0.4, rate=500, seed=108, amp=0.4)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        set_blur(fr, self.cam, s)
        fx.streak_lines(fr, -0.5, int(s * 60), n=30, alpha=0.25, width=3)
        draw_actors(fr, self.cam, s, s, [self.k])
        fx.render_flames(fr, cs, [self.trail], s, warp=1.6)


# ============================================================================ 109-110: flight through the tilted city, the red fire catches up
class S109(Shot):
    t0, t1 = 2756 / 24, 2822 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.D = D
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo109'))
        k = self.k = Actor(Figure(SUK_W, 1.0, 'suk109'))
        z = lambda t: 5 + 9 * t
        g.k(0, yaw=0.0, eye_glow=1.4, visible=0.0)
        g.k(8 / 24, visible=0.0).k(9 / 24, visible=1.0)
        n = 24
        for i in range(n + 1):
            t = D * i / n
            sw = math.sin(t * 7)
            g.k(t, root=V(0.3 * sw, 30 + 0.2 * math.sin(t * 5), z(t)), lean=1.15, twist=0.3 * sw,
                foot_l=V(0.3 * sw - 0.25, 29.5, z(t) - 0.95), foot_r=V(0.3 * sw + 0.2, 29.4, z(t) - 0.8),
                hand_l=V(-0.3, 0.15, -0.25), hand_r=V(0.35, -0.1, 0.15 + 0.1 * sw), fist_r=1, hpitch=-0.6)
        # Sukuna arrives from behind at the end (shot 110 begins at 2814)
        ta = (2814 - 2756) / 24
        k.k(0, visible=0.0).k(ta - 0.01, visible=0.0).k(ta, visible=1.0)
        k.k(ta, root=V(-1.2, 30.6, z(ta) - 1.6), lean=1.1, yaw=0.3, foot_l=V(-1.3, 30.0, z(ta) - 2.5), foot_r=V(-1.0, 29.9, z(ta) - 2.3),
            hand_r=V(0.2, 0.2, 0.5), hshape_r=shape('claw'), eye_glow=1.5)
        k.k(D, root=V(-0.6, 30.4, z(D) - 0.7), hand_r=V(0.25, 0.25, 0.6))
        self.city = tilted_city(109, 40)
        self.cam = Cam(lambda t: V(0.0, 31.6, z(t) - 3.2), lambda t: V(0.0, 29.8, z(t) + 2.0), fov=60,
                       roll=Ch(-35).key(D, -50))
        self.fire = fx.Flame(lambda t: k.fig.pose(t)['Wr'], 'red', size=0.14, seed=110, trail=0.8, life=0.35,
                             amount=Ch(0.0).key(ta, 0.0).key(ta + 0.05, 1.0))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if 8 / 24 <= s < 9 / 24:
            paper(fr, INK)
            return
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=180)
        set_blur(fr, self.cam, s, k=0.6, thresh=6, dist=25)
        draw_actors(fr, self.cam, s, s, [self.g, self.k])
        fx.render_flames(fr, cs, [self.fire], s)


# ============================================================================ 111: he looks back; Blue gathers
class S111(Shot):
    t0, t1 = 2822 / 24, 2843 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo111'))
        g.k(0, yaw=math.pi - 0.5, root=V(0, 1.0, 0), lean=0.3, foot_l=V(-0.2, 0.3, 0.3), foot_r=V(0.2, 0.2, -0.2),
            hand_r=V(0.35, 0.15, -0.2), hshape_r=shape('claw'), hand_l=V(0, -0.2, 0.3), eye_glow=1.7, eye_fire=0.6, hyaw=0.4)
        g.k(0.3, hyaw=0.2, hand_r=V(0.4, 0.2, -0.25))
        g.k(D, hyaw=0.15, hand_r=V(0.42, 0.22, -0.28))
        self.form = Ch(0.0).key(3 / 24, 0.0).key(0.45, 1.0, 'out').key(D, 1.1)
        J = g.fig.pose(0.4)
        F = J['Rp'] @ V(0, 0, 1)
        mid = J['H'] * 0.6 + J['Wr'] * 0.4
        self.cam = Cam(Ch(mid + F * 1.15 + V(-0.1, -0.15, 0)).key(D, mid + F * 1.08 + V(-0.1, -0.15, 0)), Ch(mid + V(0, -0.05, 0)), fov=54)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        f = float(self.form(s))
        paper(fr)
        if f > 0:
            fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.55, 0.65, 0.9), 0.25 * f))
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        mouth(fr, cs, J, self.g.fig, 1.0, smile=1.0, width=0.55, open_=0.25)
        if f > 0:
            p = J['Wr'] + J['Rc'] @ V(0.1, 0.12, -0.05)
            fx.orb(fr, cs, p, 0.13 * f, 'blue', s, spin=-1.0, seed=111, arcs=3)
            q = cs.proj(p)
            fr.g.drawLine(0, q[1], W, q[1], paint(BL['mid'], 0.4 * f, stroke=6, add=True, blur=4))


# ============================================================================ 112: Mahoraga swallowed by the blue flow
class S112(Shot):
    t0, t1 = 2843 / 24, 2858 / 24

    def setup(self):
        D = self.t1 - self.t0
        m = self.m = Actor(Figure(MAHORAGA, 1.45, 'maho112'))
        m.k(0, yaw=math.pi, root=V(0, 1.4, 0), lean=-0.3, foot_l=V(-0.3, 0.6, 0.2), foot_r=V(0.3, 0.5, -0.1), hand_l=V(-0.4, 0.4, 0.2),
            hand_r=V(0.4, 0.3, 0.2), fist_l=1, fist_r=1, hpitch=-0.3)
        m.k(D, root=V(0, 1.35, 0.3), lean=-0.5, hand_l=V(-0.5, 0.5, 0.0), hand_r=V(0.5, 0.45, 0.0), twist=0.3)
        self.C = V(0.0, 1.5, -0.3)
        self.cam = Cam(Ch(V(0.3, 1.6, -3.0)).key(D, V(0.25, 1.6, -2.6)), Ch(V(0, 1.6, 0)), fov=56, roll=10)
        self.cam.shake(0, 8, D, 20)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.55, 0.65, 0.9), 0.3))
        draw_actors(fr, self.cam, s, s, [self.m])
        q = cs.proj(self.C)
        # inward flow: streaks pulled toward the orb
        for i in range(60):
            ang = hash01(112, i) * 6.28
            ph = (s * 2.5 + hash01(113, i)) % 1.0
            r0 = 900 * (1 - ph)
            r1 = r0 + 120
            ca, sa = math.cos(ang), math.sin(ang)
            fr.g.drawLine(q[0] + ca * r0, q[1] + sa * r0, q[0] + ca * r1, q[1] + sa * r1, paint(BL['mid'], 0.7 * ph, stroke=4 + 6 * hash01(114, i), add=True))
        fx.orb(fr, cs, self.C, 0.18, 'blue', s, spin=-1.5, seed=112, arcs=4)


# ============================================================================ 113: hand out, controlling it
class S113(Shot):
    t0, t1 = 2858 / 24, 2890 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo113'))
        stand(g, 0, 0, 0, math.pi - 0.2)
        g.k(0, hand_r=V(-0.05, 0.05, 0.6), hshape_r=shape('claw'), hup_r=V(0, 0.6, 1), hback_r=V(0, 1, -0.4), eye_glow=1.7,
            eye_fire=0.6, hpitch=0.25, lean=0.2)
        for i in range(6):
            t = 0.1 + i * D / 6
            g.k(t, hshape_r=np.array(shape('claw')) * (0.85 + 0.25 * (i % 2)), hand_r=V(-0.05 + 0.02 * math.sin(i), 0.05, 0.6))
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.35, -0.25, -0.85)).key(D, H + V(-0.3, -0.25, -0.75)), Ch(H + V(0.0, -0.2, -0.2)), fov=50)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.55, 0.65, 0.9), 0.28))
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        q = cs.proj(J['Wr'])
        fx.light_wash(fr, q[0], q[1] + 120, 260, BL['glow'], 0.35, layer='g')


# ============================================================================ 114: from behind, Blue leaves his hand
class S114(Shot):
    t0, t1 = 2890 / 24, 2905 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo114'))
        stand(g, 0, 0, 0, 0.2)
        g.k(0, hand_l=V(-0.05, 0.1, 0.6), hshape_l=shape('open'), eye_glow=1.6)
        g.k(D, hand_l=V(-0.06, 0.12, 0.62))
        self.orb = Ch(V(-0.15, 1.5, 1.0)).key(D, V(-2.0, 2.5, 25.0), 'in')
        self.cam = Cam(Ch(V(0.55, 1.75, -1.0)).key(D, V(0.5, 1.7, -0.9)), Ch(V(-0.3, 1.5, 3.0)), fov=56)
        self.city = tilted_city(114, 30)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 4 / 24:
            paper(fr, (0.35, 0.5, 0.9))
            fr.post.append(fx.whip_blur(240, 0))
            return
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=150)
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.55, 0.65, 0.9), 0.22))
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.orb(fr, cs, np.asarray(self.orb(s)), 0.35, 'blue', s, spin=-1.0, seed=114)


# ============================================================================ 115: Blue tears through the city
class S115(Shot):
    t0, t1 = 2905 / 24, 2932 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.path = Ch(V(0, 8, 0)).key(D, V(0, 8, 40), 'lin')
        o = lambda t: np.asarray(self.path(t))
        self.cam = Cam(lambda t: o(t) + V(-2.0, 0.6, -9.0), lambda t: o(t) + V(0, 0, 4.0), fov=50, roll=Ch(4).key(D, -4))
        self.city = []
        for i in range(30):
            x = (-1) ** i * (6 + 8 * hash01(115, i))
            z = -10 + i * 3
            self.city.append(Building(x - 2, x + 2, z, z + 2.5, 30 + 20 * hash01(116, i), base=-20, seed=1150 + i, style='vstrips'))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        p = np.asarray(self.path(s))
        # buildings bend toward the orb (its pull)
        draw_buildings(fr, cs, self.city, fog_dist=120)
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.55, 0.65, 0.9), 0.25))
        q = cs.proj(p)
        for i in range(40):
            ang = hash01(115, i) * 6.28 + s * 3
            r = 300 + 400 * hash01(117, i)
            pts = [(q[0] + math.cos(ang + j * 0.08) * r * (1 - 0.03 * j), q[1] + math.sin(ang + j * 0.08) * r * 0.6 * (1 - 0.03 * j)) for j in range(10)]
            fr.g.drawPath(poly_path(pts), paint(BL['mid'], 0.5, stroke=3 + 4 * hash01(118, i), add=True))
        fx.orb(fr, cs, p, 1.6, 'blue', s, spin=-1.0, seed=115, arcs=5)


# ============================================================================ 116: Sukuna, cold light
class S116(Shot):
    t0, t1 = 2932 / 24, 2948 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk116'))
        stand(k, 0, 0, 0, math.pi + 0.35)
        k.k(0, hpitch=0.25, eye_glow=1.4, eye_fire=0.4, hand_l=V(0.0, -0.3, 0.2), hand_r=V(0.0, -0.3, 0.2), root=V(0, 0.5, 0))
        k.k(0.35, 'out', hpitch=0.15, root=V(0, 0.92, 0))
        k.k(D, hpitch=0.12, root=V(0, 0.93, 0))
        H = k.fig.pose(0.5)['H']
        self.cam = Cam(Ch(H + V(0.4, -0.3, -1.1)).key(D, H + V(0.38, -0.3, -1.0)), Ch(H + V(0.05, -0.2, 0)), fov=46)
        self.smoke = [(hash01(116, i), hash01(117, i), hash01(118, i)) for i in range(18)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        for (a, b, c) in self.smoke:
            x = W * (0.4 + 0.6 * a) + 40 * s
            y = H * b - 30 * s
            fr.b.drawCircle(x, y, 120 + 200 * c, paint((0.78, 0.78, 0.8), 0.35, blur=60))
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.7)


# ============================================================================ 117: Gojo raises his hand, cyan light runs up his arm
class S117(Shot):
    t0, t1 = 2948 / 24, 2967 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo117'))
        stand(g, 0, 0, 0, math.pi + 0.2)
        g.k(0, hand_r=V(0.05, -0.2, 0.3), hshape_r=shape('relax'), eye_glow=1.5, hpitch=-0.1, root=V(0, 0.75, 0))
        g.k(0.25, 'out', root=V(0, 0.93, 0))
        g.k(0.45, 'io', hand_r=V(0.0, 0.25, 0.25), hshape_r=shape('claw'), hup_r=V(0, 1, 0.1), hback_r=V(0, 0, -1), hpitch=-0.25)
        g.k(D, hand_r=V(0.0, 0.3, 0.24))
        H = g.fig.pose(0.5)['H']
        self.cam = Cam(Ch(H + V(-0.45, -0.3, -1.05)).key(D, H + V(-0.4, -0.3, -0.95)), Ch(H + V(-0.05, -0.2, 0)), fov=48)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        u = smoothstep(0.35, 0.6, s)
        if u > 0:
            pts = [J['Er'] + (J['Wr'] - J['Er']) * (j / 9) for j in range(10)] + [J['Wr'] + J['hup_r'] * 0.12 * (j / 4) for j in range(1, 5)]
            P = cs.proj_many(np.array(pts))
            n = max(2, int(len(P) * u))
            for j in range(n - 1):
                jit = (hash01(117, int(s * 24), j) - 0.5) * 16
                fr.g.drawLine(P[j][0] + jit, P[j][1], P[j + 1][0] - jit, P[j + 1][1], paint(CY['mid'], 0.95, stroke=5, add=True))
                fr.g.drawLine(P[j][0], P[j][1], P[j + 1][0], P[j + 1][1], paint(CY['glow'], 0.35, stroke=18, add=True, blur=6))


SHOTS = [S106, S107, S108, S109, S111, S112, S113, S114, S115, S116, S117]
SEGMENTS = [(S106.t0, S117.t1)]
