"""Sequence H: shots 72-83 (frames 1924-2233): second close fight, cuts, split screen, collages."""
from films.common import *
from engine.env import Building, draw_buildings, contact_shadow
from films import street

CY = fx.PAL['cyan']
RD = fx.PAL['red']
SET = None


def street_set():
    global SET
    if SET is None:
        SET = street.build()
    return SET


def draw_street(fr, cs):
    sky, ground, blds = street_set()
    sky.draw(fr, cs)
    ground.draw(fr, cs)
    draw_buildings(fr, cs, blds, fog_dist=170)


def ring(fr, cs, c, r, k=1.0, t=0.0):
    pts = [c + V(math.cos(a) * r, 0.01, math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 60)]
    Q = cs.proj_many(np.array(pts))
    if np.any(Q[:, 2] < 0.05):
        return
    pul = 0.85 + 0.15 * math.sin(t * 8)
    path = poly_path(Q[:, :2], closed=True)
    fr.g.drawPath(path, paint(CY['glow'], 0.45 * k * pul, stroke=40, add=True, blur=16))
    fr.g.drawPath(path, paint(CY['mid'], 0.95 * k * pul, stroke=9, add=True))
    fr.g.drawPath(path, paint(CY['core'], 0.8 * k, stroke=3, add=True))


# ============================================================================ 72: hurt Gojo inside the ring
class S72(Shot):
    t0, t1 = 1924 / 24, 1951 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo72'))
        g.k(0, yaw=math.pi + 0.3, root=V(0, 0.40, 0), lean=1.05, foot_l=V(-0.25, 0, 0.3), foot_r=V(0.3, 0, -0.4),
            knee_l=V(0, 0.3, 1), knee_r=V(0, -0.5, 1), hand_rwb=1.0, hshape_r=shape('open'), hand_l=V(0.05, -0.2, 0.2), hpitch=-0.9,
            eye_glow=1.4, eye_fire=0.3)
        g.fig.set(hand_rw=V(0.35, 0.0, -0.45))
        g.k(0.5, root=V(0, 0.42, 0), lean=1.0, hpitch=-0.95)
        g.k(D, root=V(0.02, 0.45, 0.0), lean=0.95, hpitch=-1.0, hand_l=V(0.08, -0.15, 0.25))
        g.follow(['lean', 'hpitch'], 0, D, f=1.8, z=0.6, r=1.0)
        self.cam = Cam(Ch(V(-0.5, 1.4, -1.9)).key(D, V(-0.45, 1.35, -1.7)), Ch(V(0, 0.75, 0)), fov=48, roll=-6)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        ring(fr, cs, V(0, 0, 0), 1.3, 1.0, s)
        draw_actors(fr, self.cam, s, s, [self.g])


# ============================================================================ 73: Sukuna closes in
class S73(Shot):
    t0, t1 = 1951 / 24, 1968 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk73'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo73'))
        k.k(0, yaw=0.2, eye_glow=1.2, hand_l=V(-0.1, -0.4, 0.15), hand_r=V(0.2, -0.2, 0.2), fist_r=1.0)
        walk(k, 0, D, V(-0.4, 0, -2.4), V(-0.2, 0, -1.6), 0.2, freq=1.3, arms=0.08)
        g.k(0, yaw=math.pi + 0.3, root=V(0, 0.6, 0), lean=0.8, foot_l=V(-0.25, 0, 0.25), foot_r=V(0.3, 0, -0.35),
            hand_l=V(0.05, -0.2, 0.2), hand_r=V(-0.05, -0.3, 0.2), hpitch=-0.4, eye_glow=1.4)
        g.k(D, hpitch=-0.6, root=V(0, 0.58, 0.02))
        self.cam = Cam(Ch(V(-1.2, 1.7, -4.0)).key(D, V(-1.0, 1.65, -3.6)), Ch(V(0, 0.8, 0)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        draw_street(fr, cs)
        ring(fr, cs, V(0, 0, 0), 1.3, 1.0, s)
        draw_actors(fr, self.cam, s, s, [self.g, self.k])
        if s > D - 2 / 24:
            fx.flash(fr, CY['mid'], 0.5 * (s - (D - 2 / 24)) / (2 / 24))


# ============================================================================ 74-76: the exchange inside the ring
class S74(Shot):
    """the red fist drives down; Gojo ducks"""
    t0, t1 = 1968 / 24, 1977 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk74'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo74'))
        stand(k, 0, 0.7, 0.0, -math.pi / 2, width=0.2, stagger=0.15)
        k.k(0, lean=0.3, twist=-0.5, hand_r=V(0.1, 0.3, -0.1), elbow_r=V(0.6, 0.6, -0.6), fist_r=1.0, hand_l=V(-0.1, -0.2, 0.25),
            eye_glow=1.3)
        k.k(0.17, 'in', hand_r=V(-0.05, -0.35, 0.55), twist=0.45, lean=0.6, root=V(0.55, 0.8, 0.0))
        k.k(D, hand_r=V(-0.08, -0.45, 0.55), lean=0.65, root=V(0.5, 0.78, 0.0))
        g.k(0, yaw=math.pi / 2, root=V(-0.35, 0.7, 0), lean=0.6, foot_l=V(-0.1, 0, 0.2), foot_r=V(-0.7, 0, -0.15), hpitch=-0.4,
            hand_l=V(0.05, -0.1, 0.3), hand_r=V(-0.05, -0.2, 0.2), fist_l=1, fist_r=1, eye_glow=1.4)
        g.k(0.12, 'out', root=V(-0.5, 0.48, 0.05), lean=0.95, hpitch=-0.2)
        g.k(D, root=V(-0.55, 0.45, 0.06), lean=1.0)
        self.flame = fx.Flame(lambda t: k.fig.pose(t)['Wr'], 'red', size=0.09, src2=lambda t: k.fig.pose(t)['Er'], seg=(0.3, 1.0),
                              seed=74, trail=0.5)
        self.cam = Cam(Ch(V(0.4, 1.3, -1.8)).key(D, V(0.35, 1.2, -1.6)), Ch(V(0.1, 0.9, 0)), fov=50, roll=8)
        self.cam.shake(0.17, 12, 0.25)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.g, self.k])
        fx.render_flames(fr, cs, [self.flame], s)


class S75(Shot):
    """Gojo slips under the arm; his fist ignites"""
    t0, t1 = 1977 / 24, 1986 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk75'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo75'))
        stand(k, 0, 0.5, 0.0, -math.pi / 2, width=0.2, stagger=0.15)
        k.k(0, lean=0.65, twist=0.45, hand_r=V(-0.1, -0.4, 0.55), fist_r=1.0, hand_l=V(-0.1, -0.2, 0.25), eye_glow=1.3)
        k.k(D, hand_r=V(-0.15, -0.35, 0.6), twist=0.5)
        g.k(0, yaw=math.pi / 2, root=V(-0.6, 0.48, 0.05), lean=1.0, foot_l=V(-0.1, 0, 0.25), foot_r=V(-0.8, 0, -0.15), hpitch=-0.3,
            hand_l=V(0.05, -0.1, 0.3), hand_r=V(0.1, -0.3, -0.15), fist_l=1, fist_r=1, eye_glow=1.5)
        g.k(0.25, 'io', root=V(0.0, 0.55, 0.1), lean=0.7, foot_r=V(-0.3, 0, -0.1), hand_r=V(0.12, 0.0, -0.25))
        g.k(D, root=V(0.1, 0.6, 0.1), lean=0.6, hand_r=V(0.1, 0.1, -0.2))
        self.flame_k = fx.Flame(lambda t: k.fig.pose(t)['Wr'], 'red', size=0.09, src2=lambda t: k.fig.pose(t)['Er'], seg=(0.3, 1.0), seed=75)
        self.flame_g = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.09, seed=76, amount=Ch(0.0).key(0.15, 0.0).key(0.25, 1.0, 'out'))
        self.cam = Cam(Ch(V(0.2, 0.9, -1.6)).key(D, V(0.3, 0.9, -1.5)), Ch(V(0.0, 0.85, 0)), fov=52)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])
        fx.render_flames(fr, cs, [self.flame_k, self.flame_g], s)


class S76(Shot):
    """clinch: the cyan fist drives up under his arm, slow motion"""
    t0, t1 = 1986 / 24, 2006 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk76'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo76'))
        stand(k, 0, 0.35, 0.0, -math.pi / 2, width=0.2, stagger=0.15)
        k.k(0, lean=0.5, twist=0.4, hand_r=V(-0.3, -0.1, 0.35), fist_r=1.0, hand_l=V(0.1, 0.1, 0.25), eye_glow=1.3, hpitch=0.2)
        k.k(0.1, 'out', lean=0.25, hpitch=-0.2, root=V(0.45, 0.95, 0.0))
        k.k(D, lean=0.15, hpitch=-0.3, root=V(0.55, 1.0, 0.0))
        g.k(0, yaw=math.pi / 2, root=V(-0.15, 0.62, 0.1), lean=0.55, foot_l=V(0.15, 0, 0.25), foot_r=V(-0.6, 0, -0.1), hpitch=-0.5,
            hand_r=V(0.1, 0.1, -0.1), hand_l=V(0.0, -0.1, 0.25), fist_l=1, fist_r=1, eye_glow=1.5, eye_fire=0.5)
        g.fig.set(hand_rw=Ch(V(0.2, 1.05, 0.05)).key(0.08, V(0.3, 1.3, 0.05), 'out').key(D, V(0.42, 1.45, 0.05)))
        g.k(0, hand_rwb=0.0).k(0.08, 'in', hand_rwb=1.0)
        g.k(D, root=V(-0.05, 0.68, 0.1), lean=0.45)
        self.hitstop(0.08, 3)
        self.flame = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.11, src2=lambda t: g.fig.pose(t)['Er'], seg=(0.3, 1.0), seed=77, trail=0.4)
        self.cam = Cam(Ch(V(-0.2, 1.0, -1.3)).key(D, V(-0.1, 1.05, -1.15)), Ch(V(0.2, 1.15, 0)), fov=50, roll=-10)
        self.cam.shake(0.08, 14, 0.3)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, tau, [self.k, self.g])
        fx.render_flames(fr, cs, [self.flame], tau)
        a = s - 0.08
        if a >= 0:
            q = cs.proj(V(0.42, 1.4, 0.05))
            fx.impact_burst(fr, q[0], q[1], a, size=160, pal='cyan', seed=76, spikes=8, life=0.12)
            fx.sparks(fr, cs, V(0.42, 1.4, 0.05), a, n=18, pal='cyan', speed=4, life=0.4, seed=78)
        D = self.t1 - self.t0
        if s > D - 1.5 / 24:
            fr.post.append(fx.whip_blur(170, -60))


# ============================================================================ 77: the slashes across his face
class S77(Shot):
    t0, t1 = 2006 / 24, 2030 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo77'))
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk77'))
        stand(g, 0, 0, 0, math.pi / 2 + 0.3)
        g.k(0, hpitch=0.1, eye_glow=1.4, eye_open=1.1, hand_l=V(-0.1, -0.2, 0.25), hand_r=V(0.1, -0.1, 0.25), fist_r=1)
        g.k(6 / 24, hroll=0.0).k(9 / 24, 'out', hroll=0.25, hyaw=-0.3, root=V(-0.05, 0.92, 0)).k(D, hroll=0.3, hyaw=-0.35)
        stand(k, 0, 0.55, -0.15, -math.pi / 2 + 0.3)
        k.k(0, hand_r=V(-0.2, 0.25, 0.45), hshape_r=shape('flat'), eye_glow=1.3, hpitch=0.1)
        k.k(D, hand_r=V(-0.25, 0.3, 0.5))
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.25, 0.05, -0.85)).key(D, H + V(0.2, 0.05, -0.78)), Ch(H + V(0.15, -0.05, 0)), fov=50, roll=-12)
        self.cuts = [(4 / 24 + 0.04 * i, hash01(77, i) * 0.6 - 0.3, (hash01(78, i) - 0.5) * 500) for i in range(6)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s < 4 / 24:
            paper(fr, INK)
            for i in range(3):
                y = H * (0.3 + 0.2 * i) + 200 * s
                fr.b.drawLine(-50, y + 300, W + 50, y - 300, paint((1, 1, 1), 1.0, stroke=60 - 15 * i))
            return
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.k, self.g])
        for (t_on, ang, off) in self.cuts:
            a = s - t_on
            if a < 0:
                continue
            k = max(0.0, 1 - a / 0.3)
            ca, sa = math.cos(ang), math.sin(ang)
            cx, cy = W / 2 + off * 0.3, H / 2 + off
            p0, p1 = (cx - ca * 1300, cy - sa * 1300), (cx + ca * 1300, cy + sa * 1300)
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint(INK, 0.9 * (0.3 + 0.7 * k), stroke=8 + 10 * k))
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint((1, 1, 1), 1.0 * (0.3 + 0.7 * k), stroke=4 + 6 * k))
            for j in range(4):
                u = hash01(79, int(t_on * 100), j)
                x, y = p0[0] + (p1[0] - p0[0]) * (0.35 + 0.3 * u), p0[1] + (p1[1] - p0[1]) * (0.35 + 0.3 * u)
                fr.b.drawLine(x, y, x - 60 - 80 * u, y + 20 * (u - 0.5) - 30 * a, paint((0.8, 0.04, 0.09), 0.9 * k, stroke=6 + 6 * u))


# ============================================================================ 78: slashes across his back as he pulls away
class S78(Shot):
    t0, t1 = 2030 / 24, 2044 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo78'))
        g.k(0, yaw=0.3, root=V(0, 0.75, 0), lean=0.6, foot_l=V(-0.2, 0, 0.3), foot_r=V(0.25, 0, -0.35), hand_l=V(-0.1, -0.3, 0.2),
            hand_r=V(0.1, -0.3, 0.2), hpitch=-0.2, eye_glow=1.2)
        g.k(D, root=V(0.3, 0.72, 0.6), lean=0.7, foot_l=V(0.15, 0, 0.9), foot_r=V(0.4, 0.15, 0.1))
        # he breaks away; the camera whips off him on the last two frames (into the next shot)
        self.cam = Cam(Ch(V(-0.6, 1.6, -1.3)).key(D, V(-0.4, 1.55, -1.0)),
                       Ch(V(0.1, 0.9, 0.3)).key(D - 2 / 24, V(0.15, 0.9, 0.35)).key(D, V(2.4, 0.9, 0.6), 'in'), fov=52, roll=8)
        self.cuts = [(0.02 + 0.06 * i, hash01(780, i) * math.pi, (hash01(781, i) - 0.5) * 700) for i in range(7)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.g])
        for (t_on, ang, off) in self.cuts:
            a = s - t_on
            if a < 0:
                continue
            k = max(0.0, 1 - a / 0.25)
            ca, sa = math.cos(ang), math.sin(ang)
            cx, cy = W / 2 - sa * off, H / 2 + ca * off
            p0, p1 = (cx - ca * 1300, cy - sa * 1300), (cx + ca * 1300, cy + sa * 1300)
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint(INK, 0.9 * (0.3 + 0.7 * k), stroke=6 + 12 * k))
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint((1, 1, 1), 1.0 * (0.3 + 0.7 * k), stroke=3 + 7 * k))
        cam_blur(fr, self.cam, s, k=0.6, thresh=25.0)


# ============================================================================ 79: wounded, on guard
class S79(Shot):
    t0, t1 = 2044 / 24, 2063 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo79'))
        g.k(0, yaw=math.pi, root=V(0, 0.62, 1.0), lean=0.55, foot_l=V(-0.3, 0, 1.25), foot_r=V(0.3, 0, 0.7), hand_l=V(0.05, -0.15, 0.3),
            hand_r=V(-0.1, -0.35, 0.2), hshape_l=shape('claw'), hpitch=-0.45, eye_glow=1.5, eye_fire=0.4)
        g.k(0.4, root=V(0, 0.6, 0.85), foot_r=V(0.3, 0, 0.55))
        g.k(D, root=V(0.05, 0.58, 0.7), lean=0.6, hpitch=-0.5, foot_l=V(-0.3, 0, 1.0))
        g.follow(['root', 'hpitch'], 0, D, f=2.0, z=0.7, r=1.0)
        # whips in from the left and settles on him
        self.cam = Cam(Ch(V(0.4, 0.9, -1.2)).key(D, V(0.3, 0.85, -0.9)),
                       Ch(V(-1.4, 0.9, 1.0)).key(3 / 24, V(0, 0.9, 1.0), 'outexp'), fov=56, roll=Ch(-10).key(D, -14))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        draw_street(fr, cs)
        draw_actors(fr, self.cam, s, s, [self.g])
        cam_blur(fr, self.cam, s, k=0.6, thresh=25.0)


# ============================================================================ 80: split screen
class S80(Shot):
    t0, t1 = 2063 / 24, 2080 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo80'))
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk80'))
        stand(g, 0, 0, 0, math.pi + 0.3)
        g.k(0, hand_r=V(-0.1, 0.12, 0.25), hshape_r=shape('open'), hup_r=V(0, 1, 0.2), hback_r=V(0, 0, -1), eye_glow=1.5,
            hpitch=0.1, eye_fire=0.4)
        g.k(D, hand_r=V(-0.1, 0.18, 0.25))
        stand(k, 0, 10, 0, math.pi - 0.3)
        k.k(0, hand_l=V(0.045, 0.06, 0.30), hand_r=V(-0.045, 0.06, 0.30), hshape_l=shape('flat'), hshape_r=shape('flat'),
            hup_l=V(0, 1, 0.15), hup_r=V(0, 1, 0.15), hback_l=V(-1, 0, 0), hback_r=V(1, 0, 0), eye_glow=1.5, eye_fire=0.6, hpitch=0.25)
        Hg = g.fig.pose(0)['H']
        Hk = k.fig.pose(0)['H']
        self.cg = Cam(Ch(Hg + V(0.25, -0.2, -0.85)).key(D, Hg + V(0.22, -0.18, -0.8)), Ch(Hg + V(0.05, -0.15, 0)), fov=46)
        self.ck = Cam(Ch(Hk + V(-0.25, -0.25, -0.85)).key(D, Hk + V(-0.22, -0.23, -0.8)), Ch(Hk + V(-0.05, -0.2, 0)), fov=46)

    def draw(self, fr, s):
        D = self.t1 - self.t0
        sep = smoothstep(D - 4 / 24, D - 1 / 24, s)
        gap = 30 + sep * 1400
        slope = 260
        # left panel (Gojo, cool wash)
        left = skia.Path()
        xm = W * 0.55
        left.addPoly([skia.Point(-10, -10), skia.Point(xm + slope - gap / 2, -10), skia.Point(xm - slope - gap / 2, H + 10), skia.Point(-10, H + 10)], True)
        right = skia.Path()
        right.addPoly([skia.Point(xm + slope + gap / 2, -10), skia.Point(W + 10, -10), skia.Point(W + 10, H + 10), skia.Point(xm - slope + gap / 2, H + 10)], True)
        paper(fr, INK)
        for path, actor, cam, tint in ((left, self.g, self.cg, (0.55, 0.85, 1.0)), (right, self.k, self.ck, (1.0, 0.55, 0.55))):
            fr.b.save(); fr.g.save()
            fr.b.clipPath(path, skia.ClipOp.kIntersect, True)
            fr.g.clipPath(path, skia.ClipOp.kIntersect, True)
            fr.b.drawPath(path, paint(PAPER))
            fr.b.drawPath(path, paint(tint, 0.25))
            cs = cam.at(s)
            J = actor.fig.pose(s)
            draw_actors(fr, cam, s, s, [actor])
            if actor is self.k:
                face_marks(fr, cs, J, actor.fig, 0.8)
            mouth(fr, cs, J, actor.fig, 1.0, smile=0.8, width=0.5)
            fr.b.restore(); fr.g.restore()


# ============================================================================ 81-82: line-art collages
def eye_art(c, cx, cy, w, color, a=1.0, iris=None, iris_col=None, lw=3.0, u=1.0, lid=True):
    """an eye drawn in lines: lids, brow, iris rings (u = how much of the drawing is done)"""
    h = w * 0.32
    top = [(cx - w / 2 + w * i / 16, cy - h * math.sin(math.pi * i / 16)) for i in range(17)]
    bot = [(cx - w / 2 + w * i / 16, cy + h * 0.6 * math.sin(math.pi * i / 16)) for i in range(17)]
    n = max(2, int(17 * u))
    c.drawPath(smooth_path(top[:n]), paint(color, a, stroke=lw * 1.4))
    c.drawPath(smooth_path(bot[:n]), paint(color, a * 0.8, stroke=lw * 0.8))
    if lid:
        brow = [(cx - w * 0.55 + w * 1.1 * i / 10, cy - h * 1.9 - h * 0.4 * math.sin(math.pi * i / 10)) for i in range(11)]
        c.drawPath(smooth_path(brow[:max(2, int(11 * u))]), paint(color, a, stroke=lw * 2.0))
    if iris and u > 0.6:
        k = (u - 0.6) / 0.4
        for j, rr in enumerate((iris, iris * 0.62, iris * 0.25)):
            c.drawCircle(cx, cy - h * 0.1, rr, paint(iris_col or color, a * k, stroke=lw if j < 2 else None))


def hand_art(fr, cs_cam, t, W0, R, shp, side, color, a=1.0, k=1.0):
    from engine.hand import draw_hand
    draw_hand(fr.b, cs_cam.at(t), W0, R, shp, side, color, a, k, width_m=0.008)


class S81(Shot):
    """black: Gojo's eyes and hand sign draw themselves in white lines; cyan floods in patches"""
    t0, t1 = 2080 / 24, 2153 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.cam = Cam(Ch(V(0, 0, -1.0)).key(D, V(0, 0, -0.75)), Ch(V(0, 0, 0)), fov=40, roll=Ch(0).key(D, 3))
        self.blobs = [(hash01(81, i), hash01(82, i), hash01(83, i)) for i in range(7)]

    def draw(self, fr, s):
        D = self.t1 - self.t0
        cs = self.cam.at(s)
        paper(fr, INK)
        zoom = 1.0 + 0.25 * s / D
        u = smoothstep(2 / 24, 14 / 24, s)
        fill = smoothstep(14 / 24, 22 / 24, s)
        # cyan collage patches (behind the lines)
        for i, (a, b, c) in enumerate(self.blobs):
            if fill <= 0:
                break
            x = W * (0.1 + 0.8 * a)
            y = H * (0.15 + 0.7 * b)
            r = (120 + 220 * c) * fill * zoom
            pts = [(x + math.cos(th) * r * (0.75 + 0.25 * hash01(84, i, j)), y + math.sin(th) * r * (0.75 + 0.25 * hash01(85, i, j)))
                   for j, th in enumerate(np.linspace(0, 2 * math.pi, 14, endpoint=False))]
            fr.b.drawPath(smooth_path(pts, closed=True), paint(CY['mid'], 0.95))
        cx, cy = W / 2, H * 0.42
        sep = 300 * zoom
        for sx in (-1, 1):
            eye_art(fr.b, cx + sx * sep, cy, 300 * zoom, PAPER, 1.0, iris=55 * zoom, iris_col=PAPER, lw=3.5, u=u)
        # crossed-finger sign in the middle (index over middle)
        from engine.hand import draw_hand, SHAPES
        Rr = np.stack([V(-1, 0, 0), V(0, 1, 0), V(0, 0, -1)], axis=1)
        sh = np.array(SHAPES['two'])
        if u > 0.3:
            draw_hand(fr.b, cs, V(0.0, -0.18, 0.0), Rr, sh, 1, PAPER, min(1.0, (u - 0.3) / 0.4), 1.6, width_m=0.009)
        if s > D - 8 / 24:
            v = (s - (D - 8 / 24)) / (8 / 24)
            fr.post.append(fx.chroma_split(12 * v))
            fr.b.drawRect(skia.Rect(0, 0, W * v * 1.2, H), paint(INK, min(1.0, v * 1.5)))


class S82(Shot):
    """red strips slash in; Sukuna's many eyes and joined hands in white lines; push into the hands"""
    t0, t1 = 2153 / 24, 2219 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.cam = Cam(Ch(V(0, -0.1, -1.1)).key(D - 8 / 24, V(0, -0.1, -0.85)).key(D, V(0, -0.15, -0.25), 'in'), Ch(V(0, -0.1, 0)), fov=40)

    def draw(self, fr, s):
        D = self.t1 - self.t0
        cs = self.cam.at(s)
        paper(fr, INK)
        u = smoothstep(0, 5 / 24, s)
        RC = (0.86, 0.06, 0.1)
        for i, (y0, y1, wd) in enumerate(((0.05, 0.35, 180), (0.95, 0.6, 220), (0.2, 0.75, 120), (0.7, 0.15, 100))):
            k = smoothstep(i * 1.5 / 24, i * 1.5 / 24 + 4 / 24, s)
            x1 = -100 + (W + 200) * k
            fr.b.drawLine(-100, H * y0, x1, H * (y0 + (y1 - y0) * k), paint(RC, 1.0, stroke=wd))
        zoom = float(np.linalg.norm(cs.pos - V(0, -0.1, 0)))
        z = 1.1 / max(zoom, 0.1)
        cx, cy = W / 2, H * 0.36
        if u > 0:
            for (ex, ey, sc) in ((-0.36, 0.0, 1.0), (0.36, 0.0, 1.0), (-0.42, 0.25, 0.6), (0.42, 0.25, 0.6)):
                eye_art(fr.b, cx + ex * W * 0.7 * z, cy + ey * H * z, 260 * sc * z, PAPER, 1.0, iris=40 * sc * z, iris_col=RC, lw=3.5, u=u)
        # the joined hands, huge, in white lines
        from engine.hand import draw_hand, SHAPES
        sh = np.array(SHAPES['flat'])
        sh = np.array(SHAPES['open']) * np.array([1, 0.15, 0.1, 0.1, 0.15, 0.2])
        for side, xo, zo in ((1, 0.035, 0.0), (-1, -0.035, -0.01)):
            Rh = np.stack([V(-1, 0, 0), V(0, 1, 0), V(0, 0, -1)], axis=1)
            draw_hand(fr.b, cs, V(xo, -0.33, zo), Rh, sh, side, PAPER if side > 0 else (0.75, 0.72, 0.68), u, 2.2, width_m=0.008)
        if s > D - 3 / 24:
            fr.post.append(fx.chroma_split(14))


class S82b(Shot):
    t0, t1 = 2219 / 24, 2222 / 24

    def draw(self, fr, s):
        paper(fr, INK)


# ============================================================================ 83: the bloodied nose
class S83(Shot):
    t0, t1 = 2222 / 24, 2233 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo83'))
        stand(g, 0, 0, 0, math.pi - 0.5)
        g.k(0, hpitch=0.2, hroll=0.15, eye_glow=1.5, eye_open=1.1).k(D, hpitch=0.18)
        H = g.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(0.1, -0.15, -0.7)).key(D, H + V(0.08, -0.15, -0.65)), Ch(H + V(-0.05, -0.12, 0)), fov=46, roll=-10)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fx.light_wash(fr, W * 0.95, H * 0.5, 900, (1, 1, 1), 0.9)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        # blood from the nose: two red runs down over the mouth
        Rh, Hc = J['Rh'], J['H']
        R = self.g.fig.L['head']
        for sx in (-0.12, 0.08):
            top = cs.proj(Hc + Rh @ V(sx, -0.2, 0.98) * R)
            L = (120 + 60 * abs(sx) * 10) * min(1.0, 0.4 + s * 2)
            fr.b.drawLine(top[0], top[1], top[0] - 8, top[1] + L, paint((0.82, 0.04, 0.09), 1.0, stroke=16))
        if s < 1 / 24:
            red_two_tone(fr)


SHOTS = [S72, S73, S74, S75, S76, S77, S78, S79, S80, S81, S82, S82b, S83]
SEGMENTS = [(S72.t0, S83.t1)]
