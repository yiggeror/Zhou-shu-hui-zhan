"""Sequence L: shots 118-125 (frames 2967-3272): Red gathers, Mahoraga, Hollow Purple."""
from films.common import *
from engine.env import Building, draw_buildings, clip_poly_near
from films.seq_b import city_ring
from films.purple_fx import violet_wash, lavender_flash, wisp, sky_streaks, light_body, god_rays, ink_box, mixc3
from scipy.interpolate import PchipInterpolator
import cv2

CY = fx.PAL['cyan']
RD = fx.PAL['red']
BL = fx.PAL['blue']
MG = fx.PAL['magenta']
GOJO_C = GOJO


def night_city(seed, y_top=-4, r0=30, r1=120, n=40):
    return city_ring(seed, r0=r0, r1=r1, n=n, y_top=y_top)


def red_vortex(fr, cs, center, s, k, seed, n=70, r0=0.25, r1=2.6, plane_u=None, plane_v=None, width=1.0):
    """red energy drawn in: each streak spirals in toward `center` (world), fades out as it
    arrives and starts again at the rim (a steady inflow, not random sparks)"""
    if k <= 0:
        return
    pu = V(1, 0, 0) if plane_u is None else plane_u
    pv = V(0, 1, 0) if plane_v is None else plane_v
    for i in range(n):
        ph = hash01(seed, i, 1)
        sp = 0.55 + 0.6 * hash01(seed, i, 2)
        u = (s * sp + ph) % 1.0               # 0 = at the rim, 1 = arrived
        if hash01(seed, i, 5) > k:
            continue
        rr = r0 + (r1 - r0) * (1 - u) ** 1.6
        a0 = hash01(seed, i, 3) * 6.283 + u * (2.2 + 1.5 * hash01(seed, i, 4))
        al = math.sin(math.pi * u) ** 0.7
        pts = []
        for j in range(6):
            a = a0 - j * 0.07 * (1.6 - u)
            r = rr * (1 + j * 0.03)
            p = center + pu * (math.cos(a) * r) + pv * (math.sin(a) * r * 0.8)
            q = cs.proj(p)
            if not np.isfinite(q[0]):
                break
            pts.append(q)
        if len(pts) < 2:
            continue
        w = (2.0 + 4.0 * hash01(seed, i, 6)) * width * (0.6 + 0.6 * (1 - u))
        fr.g.drawPath(poly_path([(p[0], p[1]) for p in pts]), paint(RD['mid'], 0.85 * al * k, stroke=w, add=True))
        fr.g.drawCircle(pts[0][0], pts[0][1], w * 0.7, paint(RD['core'], 0.7 * al * k, add=True))


# ============================================================================ 118: red sparks gather around him
class S118(Shot):
    t0, t1 = 2967 / 24, 3006 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo118'))
        # hovering above the city: legs hang, the right hand holds the sign at the chest, Red forms there
        n = 10
        for i in range(n + 1):
            t = D * i / n
            hv = 0.035 * math.sin(t * 2.4) + 0.012 * t
            g.k(t, yaw=math.pi - 0.18, root=V(0, 0.95 + hv, 0), lean=0.04 + 0.02 * math.sin(t * 1.7), twist=-0.08,
                foot_l=V(0.13, 0.07 + hv + 0.01 * math.sin(t * 2.4 + 0.6), 0.04), foot_r=V(-0.10, 0.13 + hv, -0.10 + 0.01 * math.sin(t * 2.0)))
        g.k(0, knee_r=V(-0.25, 0, 1), knee_l=V(0.25, 0, 1), hand_r=V(-0.12, -0.30, 0.24), hshape_r=shape('two'), hup_r=V(0, 1, 0.2), hback_r=V(0, 0, 1),
            hand_l=V(0.06, -0.46, 0.18), hshape_l=shape('relax'), eye_glow=1.4, hpitch=0.12, hyaw=0.05)
        g.k(0.5, hand_r=V(-0.10, -0.26, 0.26), hand_l=V(0.08, -0.42, 0.20), hshape_l=shape('two'), hpitch=0.06)
        g.k(D, hand_r=V(-0.09, -0.22, 0.28), hand_l=V(0.07, -0.40, 0.21), hpitch=0.0, eye_glow=1.7, eye_fire=0.3)
        g.follow(['hand_r', 'hand_l'], 0, D)
        g.d.wind = V(0.3, 0.1, 0.0)
        C0 = g.fig.pose(0.0)['C']
        self.cam = Cam(Ch(C0 + V(0.45, -0.55, -3.6)).key(D, C0 + V(0.35, -0.45, -3.0)), Ch(C0 + V(0, 0.02, 0)), fov=40)
        self.city = night_city(118, y_top=-26, r0=40, r1=160, n=50)

    def tip(self, t):
        J = self.g.fig.pose(t)
        return J['Wr'] + J['hup_r'] * 0.13

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        u = smoothstep(0.4, D, s)
        if u > 0:
            fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.85, 0.4, 0.42), 0.28 * u))
        draw_buildings(fr, cs, self.city, fog_dist=200)
        draw_actors(fr, self.cam, s, s, [self.g])
        if s < 2 / 24:
            wipe_diag(fr, s / (2 / 24), ang=0.0, reverse=True)
        if u > 0:
            J = self.g.fig.pose(s)
            Rc = J['Rc']
            red_vortex(fr, cs, self.tip(s), s, u, 118, n=80, r0=0.12, r1=2.4, plane_u=Rc @ V(1, 0, 0), plane_v=Rc @ V(0, 1, 0.25))
            fx.orb(fr, cs, self.tip(s), 0.008 + 0.022 * u, 'red', s, seed=118)


# ============================================================================ 119: finger to the sky
class S119(Shot):
    t0, t1 = 3006 / 24, 3042 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo119'))
        self.flash_t = (3030 - 3006) / 24
        ft = self.flash_t
        g.k(0, yaw=math.pi + 0.10, root=V(0, 0.95, 0), lean=0.02, twist=0.12, foot_l=V(-0.13, 0.05, 0.02), foot_r=V(0.12, 0.1, -0.08),
            hand_r=V(0.12, 0.55, 0.08), elbow_r=V(0.9, 0.0, 0.3), hshape_r=shape('point'), hup_r=V(0, 1, 0.05), hback_r=V(0, 0, -1),
            hand_l=V(0.24, -0.10, 0.26), hshape_l=shape('two'), hup_l=V(0.1, 1, 0.1), hback_l=V(0, 0, 1),
            eye_glow=1.5, eye_fire=0.3, hpitch=0.10, hyaw=-0.12, hroll=-0.16)
        # a slight press upward, then the arm locks straight for the release
        g.k(0.35, 'io', hand_r=V(0.11, 0.59, 0.06), hpitch=0.06)
        g.k(ft - 0.12, 'io', hand_r=V(0.12, 0.56, 0.08), hand_l=V(0.25, -0.08, 0.27))
        g.k(ft, 'out', hand_r=V(0.10, 0.62, 0.04), hand_l=V(0.24, -0.06, 0.28), hpitch=0.0, eye_glow=2.0, eye_fire=0.7)
        g.k(D, hand_r=V(0.11, 0.61, 0.05), hpitch=0.04, eye_glow=1.6, eye_fire=0.4)
        g.follow(['hand_r', 'hand_l'], 0, D, f=3.6)
        C = g.fig.pose(0.5)['C']
        self.cam = Cam(Ch(C + V(0.16, 0.0, -1.08)).key(D, C + V(0.14, 0.02, -1.0)), Ch(C + V(-0.02, 0.36, 0)), fov=44)
        self.cam.shake(ft, 10, 0.3, 24)
        self.cam.punch(ft, 0.05, 0.03, 0.3)

    def tip(self, t):
        J = self.g.fig.pose(t)
        return J['Wr'] + J['hup_r'] * 0.2

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        a = s - self.flash_t
        red = 1.0 if a < 3 / 24 else max(0.0, 1 - (a - 3 / 24) / (6 / 24))
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.85, 0.12, 0.16), 0.55 * red))
        J = self.g.fig.pose(s)
        p = self.tip(s)
        # the red is pulled into the fingertip
        red_vortex(fr, cs, p, s, red, 119, n=60, r0=0.06, r1=1.2, plane_u=cs.r, plane_v=cs.u * 0.9 + cs.f * 0.3, width=1.2)
        draw_actors(fr, self.cam, s, s, [self.g])
        if red > 0:
            fx.orb(fr, cs, p, 0.03 + 0.01 * smoothstep(0, self.flash_t, s), 'red', s, seed=119, k=red)
        if 0 <= a < 4 / 24:
            q = cs.proj(p)
            e = 1 - a / (4 / 24)
            for j in range(18):
                ang = math.pi / 2 + (hash01(1190, j) - 0.5) * 1.5
                L = 1000 + 800 * hash01(1191, j)
                fr.g.drawLine(q[0], q[1], q[0] + math.cos(ang) * L, q[1] + math.sin(ang) * L,
                              paint((1, 0.85, 0.85), 0.75 * e, stroke=26 + 20 * hash01(1192, j), add=True, blur=14))
            fr.g.drawCircle(q[0], q[1], 160 + 300 * a * 24 / 4, paint((1.0, 0.8, 0.8), 0.8 * e, add=True, blur=60))
            fx.flash(fr, (1.0, 0.7, 0.7), 0.35 * e)


# ============================================================================ 120: Mahoraga bounds over the city
class S120(Shot):
    t0, t1 = 3042 / 24, 3080 / 24

    def setup(self):
        D = self.t1 - self.t0
        m = self.m = Actor(Figure(MAHORAGA, 1.45, 'maho120'))
        jt = self.jt = 7 / 24
        vz = 17.0

        def P(t):
            u = max(t, jt) - jt
            return V(0.5 * math.sin(u * 1.4), 40.0 + 3.2 * u - 2.6 * u * u, vz * u)
        self.P = P
        m.k(0, visible=0.0).k(jt - 0.01, visible=0.0).k(jt, visible=1.0)
        n = 16
        for i in range(n + 1):
            t = jt + (D - jt) * i / n
            u = t - jt
            p = P(t)
            sw = math.sin(u * 4.2)
            m.k(t, yaw=0.0, root=p, lean=1.25 + 0.06 * math.sin(u * 3.0), twist=-0.30 + 0.12 * sw, bend=0.12 + 0.06 * math.sin(u * 2.1),
                hpitch=-1.0, hyaw=0.15 - 0.1 * sw,
                foot_l=p + V(-0.30, -0.70 + 0.1 * sw, 0.25 + 0.1 * sw), foot_r=p + V(0.32, -0.75 - 0.08 * sw, -1.55 + 0.15 * sw),
                hand_l=V(-0.70, 0.25 + 0.08 * sw, 0.55 - 0.08 * sw), hand_r=V(0.82, 0.10 - 0.10 * sw, -0.05 + 0.12 * sw),
                fist_l=1, fist_r=1, knee_l=V(0, 0.2, 1), knee_r=V(0, -0.5, 1),
                elbow_l=V(-0.6, -0.5, -0.2), elbow_r=V(0.5, -0.6, -0.4))
        m.follow(['hand_l', 'hand_r', 'foot_l', 'foot_r'], jt, D, f=2.6, z=0.5)
        self.city = []
        for i in range(-4, 5):
            for j in range(-2, 12):
                h = 8 + 26 * hash01(120, i, j) ** 1.5
                x = i * 10 + 2 * (hash01(121, i, j) - 0.5)
                z = j * 10 + 2 * (hash01(122, i, j) - 0.5)
                self.city.append(Building(x - 3.6, x + 3.6, z - 3.6, z + 3.6, h, base=-10, seed=1200 + i * 17 + j, style='vstrips'))
        self.cam = Cam(lambda t: P(t) + V(0.6, 4.2, -2.4), lambda t: P(t) + V(-0.1, -1.6, 1.8), fov=56, roll=-16)
        self.cam.drift = 0.3
        self.whip = Cam(Ch(V(-24, 34, -6)).key(5 / 24, V(18, 30, 8)), Ch(V(0, 4, 26)), fov=70)

    def draw(self, fr, s):
        D = self.t1 - self.t0
        if s < 5 / 24:
            cs = self.whip.at(s)
            paper(fr)
            draw_buildings(fr, cs, self.city, fog_dist=160)
            fr.post.append(fx.whip_blur(260, 60))
            return
        if s < self.jt:
            paper(fr, INK)
            return
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=160)
        set_blur(fr, self.cam, s, k=0.6, thresh=8.0, dist=30.0)
        u = smoothstep(D * 0.72, D, s)
        if u > 0:
            fx.light_wash(fr, 0, H * 0.4, 1000, (0.3, 0.8, 1.0), 0.35 * u)
            fx.light_wash(fr, W, H * 0.4, 1000, (1.0, 0.3, 0.35), 0.35 * u)
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


# ============================================================================ 124-125: Hollow Purple swallows the city
PURP_INK = (0.17, 0.06, 0.26)      # buildings backlit by the purple
PURP_DEEP = (0.08, 0.03, 0.12)     # buildings right in front of the lens
PURP_LIT = (0.50, 0.17, 0.80)      # buildings bathed in the light at the end
PURP_FOG = (0.58, 0.40, 0.80)      # haze in the purple air


class S124(Shot):
    """silhouette on the roof, arms spread; the camera rushes away and he becomes the light"""
    t0, t1 = 3194 / 24, 3200 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo124'))
        g.k(0, yaw=0.0, root=V(0, 0.95, 0), lean=-0.06, hpitch=-0.22, foot_l=V(-0.17, 0, 0.03), foot_r=V(0.18, 0, -0.04),
            hand_l=V(-0.55, 0.08, 0.10), hand_r=V(0.55, 0.10, 0.10), elbow_l=V(-0.2, -1, -0.2), elbow_r=V(0.2, -1, -0.2),
            hshape_l=shape('open'), hshape_r=shape('open'), eye_glow=0.0)
        g.k(D, 'out', hand_l=V(-0.56, 0.20, 0.12), hand_r=V(0.57, 0.22, 0.12), lean=-0.12, hpitch=-0.32)
        g.d.wind = V(0.5, 0.25, 0)
        self.Cg = g.fig.pose(0.0)['C']
        self.P = self.Cg + V(0.0, 0.25, 1.8)        # where the purple gathers, in front of him
        l0, l1 = math.log(3.8), math.log(56.0)
        self.dist = lambda s: math.exp(l0 + (l1 - l0) * (1 - (1 - clamp(s / D, 0, 1)) ** 2.2))

        def cpos(s):
            d = self.dist(s)
            return V(self.Cg[0] + 0.04 * d, 0.3 + 0.06 * (d - 3.8), self.Cg[2] - d)

        def ctgt(s):
            d = self.dist(s)
            return self.Cg + V(0.0, -0.3 - 0.085 * (d - 3.8), 0.0)
        self.cam = Cam(cpos, ctgt, fov=46)
        self.cam.drift = 0.1
        self.roof = Building(-2.4, 2.4, -1.8, 3.0, 600, base=-600, seed=124, ink=True, color=PURP_INK)
        self.blds = []
        for i in range(80):
            x = (hash01(1241, i) - 0.5) * 420
            z = -150 + 560 * hash01(1242, i)
            if abs(x) < 10 and -75 < z < 14:
                continue      # the street the camera flies back along stays open
            w, d = 8 + 14 * hash01(1243, i), 8 + 14 * hash01(1244, i)
            top = -34 + 28 * hash01(1245, i)
            self.blds.append(Building(x - w / 2, x + w / 2, z - d / 2, z + d / 2, top + 600, base=-600, seed=1250 + i, ink=True, color=PURP_INK))
        # the block the camera passes on the way out: it wipes in from the left on the last frame
        self.wiper = Building(-14.0, 0.25, -95.0, -46.5, 115, base=-90, seed=1249, ink=True, color=PURP_DEEP)

    def light_r(self, s):
        return float(np.interp(s * 24, [0, 1, 2, 3, 4, 5, 6], [0, 6, 34, 120, 175, 195, 205]))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        f = s * 24
        paper(fr)
        violet_wash(fr, 1.2)
        q = cs.proj(self.P)
        rc = self.light_r(s)
        fx.light_wash(fr, q[0], q[1], 300 + 5 * rc, (0.82, 0.58, 1.0), 0.6)
        sky_streaks(fr, q, 800 + 3 * rc, 0.45 + 0.55 * smoothstep(1, 4, f), 124)
        draw_buildings(fr, cs, self.blds, fog_color=PURP_FOG, fog_dist=420)
        self.roof.draw(fr, cs, fog_color=PURP_FOG, fog_dist=420)
        light_body(fr, q[0], q[1], rc, heat=1.0)
        draw_actors(fr, self.cam, s, s, [self.g], silhouette=(0.12, 0.04, 0.19))
        # the light grows over him: a glow that swallows the tiny figure, with a level flare
        e = smoothstep(1.5, 3.2, f)
        if e > 0:
            fr.g.drawCircle(q[0], q[1], rc * 1.15, paint((0.92, 0.72, 1.0), 0.3 * e, k=3.0, add=True, blur=rc * 0.35))
            wisp(fr.g, q[0] - rc * 6, q[1] + rc * 0.05, q[0] + rc * 6, q[1] - rc * 0.05, rc * 0.22, (0.95, 0.75, 1.0), 0.8 * e)
        self.wiper.draw(fr, cs, fog_color=PURP_FOG, fog_dist=420)


class PurpleCity:
    """frames 3200-3272 as one continuous move: the camera tracks sideways low across the
    rooftops while the sphere of light rises behind the city, grows, and eats it from the top
    (blocks dissolve where the sphere reaches them) until only light is left"""
    T0 = 3200 / 24
    VX = 32.0
    CAM_Y = 22.0
    C = V(-55.0, 175.0, 520.0)
    PITCH = math.radians(5.0)

    def __init__(self):
        # radius keyed so the eaten edge reaches the blocks at the depths the original shows:
        # far rows by 3236, the middle rows 3240-50, the nearest rows at the very end
        fr_ = [3200, 3210, 3218, 3224, 3230, 3236, 3240, 3245, 3250, 3255, 3260, 3266, 3272, 3280]
        R_ = [45, 60, 80, 118, 230, 408, 455, 484, 503, 518, 528, 534.5, 539.3, 545]
        self.Rf = PchipInterpolator(np.array(fr_, float) / 24.0, np.array(R_, float))
        self.cam = Cam(self.cam_pos, self.cam_tgt, fov=50)
        self.cam.drift = 0.0
        blds = []   # (x0, x1, z0, z1, top, kind)
        # blocks right in front of the lens (black frames at 3200-01 and 3206-08)
        blds.append((-2.35, 9.0, 1.3, 10.0, 70.0, 'fg'))
        blds.append((-12.0, -7.34, 1.6, 9.0, 70.0, 'fg'))
        blds.append((-33.0, -27.5, 4.0, 10.0, 46.0, 'fg'))
        rows = [14, 26, 40, 56, 75, 98, 125, 160, 200, 250, 310, 380, 450]
        for ri, z in enumerate(rows):
            sp = 10 + 0.12 * z
            xa, xb = -96 - 0.95 * z - 20, 0.95 * z + 20
            x = xa + sp * hash01(1300, ri)
            j = 0
            while x < xb:
                j += 1
                wdt = sp * (0.55 + 0.3 * hash01(1301, ri, j))
                dep = 6 + 0.06 * z + 4 * hash01(1302, ri, j)
                hv = hash01(1303, ri, j)
                if z < 30:
                    top = 6 + 12 * hv
                elif z < 90:
                    top = 18 + 13 * hv if hash01(1304, ri, j) > 0.05 else 34 + 6 * hv
                else:
                    top = 24 + 24 * hv if hash01(1304, ri, j) > 0.08 else 55 + 15 * hv
                zz = z + 3 * (hash01(1305, ri, j) - 0.5)
                blds.append((x, x + wdt, zz, zz + dep, top, 'city'))
                x += sp
        self.blds = blds

    def cam_pos(self, t):
        u = t - self.T0
        return V(-self.VX * u, self.CAM_Y - 1.2 * u, 0.0)

    def cam_tgt(self, t):
        p = self.cam_pos(t)
        d = self.C - p
        hz = math.hypot(d[0], d[2])
        return p + V(d[0] / hz, math.tan(self.PITCH), d[2] / hz) * 100.0

    def R(self, t):
        return float(self.Rf(t))

    def draw(self, fr, t):
        cs = self.cam.at(t)
        R = self.R(t)
        C = self.C
        L = float(np.linalg.norm(C - cs.pos))
        lit = smoothstep(3236 / 24, 3264 / 24, t)
        paper(fr)
        violet_wash(fr, 1.2)
        q = cs.proj(C)
        al = math.asin(min(R / L, 0.9995))
        rp = min(cs.focal * math.tan(al), 30000.0)
        # the sky lit around the light, then the light itself
        fx.light_wash(fr, q[0], q[1], rp * 2.4 + 350, (0.80, 0.50, 1.0), 0.55 + 0.35 * lit)
        sky_streaks(fr, q, 900 + 1.3 * rp, 0.8, 1240)
        ref = float(np.interp(t * 24, [3228, 3238, 3248, 3256, 3264], [800, 950, 1250, 2000, 4000]))
        light_body(fr, q[0], q[1], rp, heat=1.0, ref=ref)
        # ground in front of where the sphere meets it
        zf = C[2] - math.sqrt(max(R * R - C[1] * C[1], 0.0)) if R > C[1] else 4000.0
        if zf > 1.0:
            gq = [V(-3000, 0, 0.6), V(3000, 0, 0.6), V(3000, 0, zf), V(-3000, 0, zf)]
            Q = clip_poly_near(cs, gq, near=0.3)
            if Q is not None:
                path = poly_path(Q, closed=True)
                fr.b.drawPath(path, paint(mixc3(PURP_INK, PURP_LIT, 0.5 * lit), 1.0))
                fr.g.drawPath(path, paint((0, 0, 0), 1.0, erase=True))
        # blocks, far to near; each is cut down to where the sphere has reached
        items = []
        for (x0, x1, z0, z1, top, kind) in self.blds:
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            rho = math.hypot(cx - C[0], cz - C[2])
            ycut = C[1] - math.sqrt(R * R - rho * rho) if R > rho else 1e9
            if ycut <= 0.4:
                continue
            d = math.hypot(cx - cs.pos[0], cz - cs.pos[2])
            items.append((d, x0, x1, z0, z1, top, kind, ycut))
        items.sort(key=lambda it: -it[0])
        for (d, x0, x1, z0, z1, top, kind, ycut) in items:
            y1 = min(top, ycut)
            fog = clamp(d / 520.0, 0, 0.9) ** 1.2
            if kind == 'fg':
                colr = mixc3(PURP_DEEP, PURP_LIT, 0.4 * lit)
                grid = (mixc3((0.22, 0.12, 0.32), (0.65, 0.35, 0.9), lit), 3.6, 2.6)
            else:
                colr = mixc3(mixc3(PURP_INK, PURP_LIT, 0.75 * lit), PURP_FOG, fog * 0.6)
                grid = None
            ink_box(fr, cs, x0, x1, z0, z1, 0.0, y1, colr, grid)
            if ycut < top:
                self.fringe(fr, cs, t, x0, x1, z0, z1, y1, colr, d)
        k = smoothstep(3226 / 24, 3250 / 24, t)
        if k > 0:
            fr.post.append(god_rays(q[0], q[1], 0.32 * k, tint=(0.85, 0.6, 1.0), thr=1.05))

    def fringe(self, fr, cs, t, x0, x1, z0, z1, y, colr, d):
        """the edge where the light is eating a block: material lifting off and drifting into
        the light (dark specks that pale as they rise), a glowing seam along the cut"""
        seed = int(abs(x0 * 7 + z0 * 13)) % 9973
        per = 2 * ((x1 - x0) + (z1 - z0))
        n = int(clamp(per * 9, 80, 420))
        i = np.arange(n)
        h1 = np.array([hash01(seed, k, 1) for k in i])
        h2 = np.array([hash01(seed, k, 2) for k in i])
        h3 = np.array([hash01(seed, k, 3) for k in i])
        h4 = np.array([hash01(seed, k, 4) for k in i])
        u = h1 * per
        wx, wz = x1 - x0, z1 - z0
        px = np.where(u < wx, x0 + u, np.where(u < wx + wz, x1, np.where(u < 2 * wx + wz, x1 - (u - wx - wz), x0)))
        pz = np.where(u < wx, z0, np.where(u < wx + wz, z0 + (u - wx), np.where(u < 2 * wx + wz, z1, z1 - (u - 2 * wx - wz))))
        v = (t * (0.7 + 0.8 * h2) + h3) % 1.0
        base = np.stack([px, np.full(n, y), pz], -1)
        to_c = self.C[None, :] - base
        to_c /= np.linalg.norm(to_c, axis=1, keepdims=True)
        dirn = np.array([0.0, 1.0, 0.0])[None, :] * 0.55 + to_c * 0.45
        P = base + dirn * (0.2 + 10.0 * v ** 1.4)[:, None]
        Q = cs.proj_many(P)
        sc = cs.scale(max(d, 1.0))
        dark = mixc3(colr, (0.05, 0.02, 0.08), 0.5)
        pale = (0.80, 0.60, 0.98)
        for k in range(n):
            if Q[k, 2] < 0.3:
                continue
            r = max(1.0, (0.16 + 0.32 * h4[k]) * sc * (1 - 0.5 * v[k]))
            c = mixc3(dark, pale, float(v[k]) ** 1.6)
            fr.b.drawRect(skia.Rect(Q[k, 0] - r, Q[k, 1] - r, Q[k, 0] + r, Q[k, 1] + r), paint(c, float(1 - v[k] ** 3)))
        corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        pts = [cs.proj(V(cx, y, cz)) for cx, cz in corners + corners[:1]]
        if all(np.isfinite(p[0]) for p in pts):
            fr.g.drawPath(poly_path([(p[0], p[1]) for p in pts]),
                          paint((0.92, 0.70, 1.0), 0.25, k=3.0, stroke=max(2.0, 1.2 * sc), add=True, blur=max(1.0, 0.8 * sc)))


_CITY = {}


def purple_city():
    if 'c' not in _CITY:
        _CITY['c'] = PurpleCity()
    return _CITY['c']


class S124b(Shot):
    """sideways past the blocks; the sphere of light rises behind the city"""
    t0, t1 = 3200 / 24, 3222 / 24

    def draw(self, fr, s):
        purple_city().draw(fr, self.t0 + s)


class S124c(Shot):
    """the light grows and eats the city from the top"""
    t0, t1 = 3222 / 24, 3261 / 24

    def draw(self, fr, s):
        purple_city().draw(fr, self.t0 + s)


class S125(Shot):
    """all light; the last of the purple city sinks out of the bottom of the frame"""
    t0, t1 = 3261 / 24, 3272 / 24

    def draw(self, fr, s):
        D = self.t1 - self.t0
        purple_city().draw(fr, self.t0 + s)
        u = smoothstep(0.0, D, s)

        def fn(img, u=u):
            h, w = img.shape[:2]
            edge = h * (0.80 + 0.17 * u)
            yy = np.arange(h, dtype=np.float32)[:, None, None]
            m = np.clip((edge - yy) / (h * 0.12), 0, 1) * (0.55 + 0.45 * u)
            tgt = np.array((1.08, 1.03, 1.10), np.float32)
            return img + (tgt - img) * m
        fr.post.append(fn)


SHOTS = [S118, S119, S120, S121, S122, S123, S124, S124b, S124c, S125]
SEGMENTS = [(S118.t0, S125.t1)]
