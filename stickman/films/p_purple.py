"""Pilot part 3: Hollow Purple (original shots 121-125, 128.33 s - 136.33 s)."""
import math
import numpy as np
import skia
from engine.mathx import V, norm, hash01, clamp, smoothstep
from engine.anim import Ch
from engine.rig import Figure, GOJO, SUKUNA, MAHORAGA
from engine.camera import Cam, W, H
from engine.shot import Shot, Actor, draw_actors, cam_blur, set_blur
from engine.env import Sky, Building, draw_buildings
from engine.canvas import paint, poly_path, col
from engine import fx

from engine.theme import T as THEME

T_MERGE = 129.882


def paper(fr):
    fr.b.clear(col(THEME['bg']))


def sky_grad(fr, top, mid, bottom, y_mid=0.6):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                               [col(top), col(mid), col(bottom)], [0.0, y_mid, 1.0]))
    fr.b.drawRect(skia.Rect(0, 0, W, H), p)


def mix(a, b, u):
    return tuple(a[i] * (1 - u) + b[i] * u for i in range(3))


def city(seed=0, y_top=0.0, n=26, spread=60.0, z0=8.0, z1=60.0, hmin=8.0, hmax=34.0, base=-60.0, ink=False):
    blds = []
    for i in range(n):
        x = (hash01(seed, i, 1) - 0.5) * spread * 2
        z = z0 + (z1 - z0) * hash01(seed, i, 2)
        w = 5 + 7 * hash01(seed, i, 3)
        d = 5 + 7 * hash01(seed, i, 4)
        h = hmin + (hmax - hmin) * hash01(seed, i, 5)
        blds.append(Building(x - w / 2, x + w / 2, z - d / 2, z + d / 2, (y_top - base) + h, base=base,
                             win_density=0.35, seed=seed * 100 + i, style='grid', ink=ink,
                             color=(0.13, 0.11, 0.17) if ink else None))
    return blds


# ============================================================================ shot 121
class S121(Shot):
    """Low wide angle: Mahoraga leaps from the left, Sukuna drops from the right, Gojo on the
    roof edge between them brings Red and Blue together over his head."""
    t0, t1 = 3080 / 24, 3118 / 24

    def setup(self):
        Tm = self.Tm = T_MERGE - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06))
        s = self.s = Actor(Figure(SUKUNA, 1.0))
        m = self.m = Actor(Figure(MAHORAGA, 1.45))
        # Gojo on the roof edge (roof at y = 0), facing the camera, arms raised out to the orbs
        self.red0, self.blue0 = V(-2.3, 3.9, 0.4), V(2.3, 3.9, 0.4)
        self.meet = V(0.0, 2.75, 0.55)
        ease = lambda u: u * u * (3 - 2 * u)
        self.redp = lambda t: self.red0 + (self.meet + V(-0.02, 0, 0) - self.red0) * ease(clamp(t / Tm, 0, 1)) ** 1.6
        self.bluep = lambda t: self.blue0 + (self.meet + V(0.02, 0, 0) - self.blue0) * ease(clamp(t / Tm, 0, 1)) ** 1.6
        g.k(0, yaw=math.pi, root=V(0.0, 0.92, 0.6), lean=-0.08, hpitch=-0.35, foot_l=V(0.18, 0, 0.5), foot_r=V(-0.18, 0, 0.7),
            eye_glow=1.3, eye_fire=0.5, fist_l=0.0, fist_r=0.0, hand_lwb=1.0, hand_rwb=1.0)
        R, B = self.redp, self.bluep
        # hands hold the orbs from slightly below
        g.fig.set(hand_lw=lambda t: B(t) + V(0.10, -0.32, 0.0), hand_rw=lambda t: R(t) + V(-0.10, -0.32, 0.0))
        g.k(1.58, root=V(0.0, 0.94, 0.6), hpitch=-0.6)
        # Sukuna dropping in from the upper right (slow motion)
        s.k(0, yaw=-math.pi * 0.75, root=V(4.4, 3.4, 2.5), lean=0.2, twist=0.2, hpitch=0.2,
            foot_l=V(4.3, 2.75, 2.3), foot_r=V(4.7, 2.55, 2.8), hand_l=V(0.1, -0.1, 0.3), hand_r=V(-0.1, 0.0, 0.3),
            fist_l=1, fist_r=1, eye_glow=1.2, eye_fire=0.6, knee_l=V(-0.2, 0.3, 1), knee_r=V(0.2, 0.3, 1))
        s.k(1.58, root=V(3.3, 2.2, 2.0), foot_l=V(3.2, 1.5, 1.8), foot_r=V(3.6, 1.35, 2.3), lean=0.35, hpitch=0.35)
        # Mahoraga leaping from the left, one arm drawn back
        m.k(0, yaw=math.pi * 0.62, root=V(-5.6, 2.2, 3.4), lean=0.35, twist=-0.4, hpitch=0.1,
            foot_l=V(-5.2, 1.35, 3.7), foot_r=V(-6.5, 1.0, 3.0), hand_r=V(0.25, 0.2, -0.45), hand_l=V(-0.1, 0.1, 0.45),
            elbow_r=V(0.6, 0.5, -0.6), fist_l=1, fist_r=1, knee_l=V(0, 0.4, 1), knee_r=V(0, -0.3, 1))
        m.k(1.58, root=V(-3.9, 2.9, 2.6), foot_l=V(-3.5, 2.1, 2.9), foot_r=V(-4.8, 1.75, 2.2), twist=-0.1,
            hand_r=V(0.2, 0.35, -0.3))
        # roof + city below
        self.roof = Building(-2.2, 2.2, -0.2, 4.0, 60, base=-60, win_density=0.4, seed=5, style='grid')
        self.blds = city(seed=3, y_top=-12, hmin=0, hmax=10) + [Building(-14, -7, 6, 14, 52, base=-60, seed=81, style='grid', win_density=0.3),
                                                                Building(8, 15, 2, 10, 48, base=-60, seed=82, style='grid', win_density=0.3)]
        self.cam = Cam(Ch(V(0.5, -2.6, -8.6)).key(1.58, V(0.2, -1.8, -6.6)),
                       Ch(V(-0.3, 2.3, 1.2)).key(1.58, V(-0.2, 2.3, 1.2)), fov=46)

    def wheel(self, fr, cs, tau, s):
        J = self.m.fig.pose(tau)
        C = J['H'] + J['Rh'] @ V(0, 0.42, -0.05) * 1.45
        R = 0.32 * 1.45
        up = J['Rh'] @ V(0, 0, 1)
        a = norm(np.cross(up, V(0, 1, 0)) + V(1e-3, 0, 0))
        b = np.cross(up, a)
        rot = s * 1.5
        ring = [C + (a * math.cos(2 * math.pi * i / 40) + b * math.sin(2 * math.pi * i / 40)) * R for i in range(40)]
        Q = cs.proj_many(np.array(ring))
        wpx = max(2.0, 0.035 * cs.scale(float(np.mean(Q[:, 2]))))
        line = THEME['ink']
        fr.b.drawPath(poly_path(Q[:, :2], closed=True), paint(line, 1.0, stroke=wpx))
        for i in range(8):
            th = rot + i * math.pi / 4
            p0 = cs.proj(C)
            p1 = cs.proj(C + (a * math.cos(th) + b * math.sin(th)) * R * 1.25)
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint(line, 1.0, stroke=wpx * 0.8))

    def draw(self, fr, s):
        tau = s
        cs = self.cam.at(s)
        u = smoothstep(0.0, self.Tm, s)
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=120)
        self.roof.draw(fr, cs, fog_dist=200)
        # the light of the two orbs: red from the left, blue from the right, purple where they meet
        qr, qb = cs.proj(self.redp(s)), cs.proj(self.bluep(s))
        fx.light_wash(fr, qr[0], qr[1], 420, (1.0, 0.45, 0.55), 0.10 + 0.10 * u)
        fx.light_wash(fr, qb[0], qb[1], 420, (0.45, 0.8, 1.0), 0.10 + 0.10 * u)
        if u > 0.7:
            qm = cs.proj(self.meet)
            fx.light_wash(fr, qm[0], qm[1], 520, (0.75, 0.55, 1.0), 0.25 * (u - 0.7) / 0.3)
        self.wheel(fr, cs, tau, s)
        draw_actors(fr, self.cam, s, tau, [self.m, self.s, self.g])
        # the orbs with short trails along their own paths
        tr = lambda f: [f(s - 0.03 * (6 - i)) for i in range(6)]
        rr = 0.26 + 0.06 * u
        fx.orb(fr, cs, self.redp(s), rr, 'red', s, spin=1.0, seed=1, trail=tr(self.redp))
        fx.orb(fr, cs, self.bluep(s), rr, 'cyan', s, spin=-1.0, seed=2, trail=tr(self.bluep))
        d = float(np.linalg.norm(self.redp(s) - self.bluep(s)))
        if d < 2.2:
            qa, qb = cs.proj(self.redp(s)), cs.proj(self.bluep(s))
            k = clamp((2.2 - d) / 1.8, 0, 1)
            seed = int(s * 30)
            fx.bolt(fr, qa[:2], qb[:2], seed, 'purple', 2.0 + 2 * k, 0.5 + 0.5 * k, jag=0.25)
            if k > 0.5:
                fx.bolt(fr, qa[:2], qb[:2], seed + 5, 'purple', 1.5, 0.6 * k, jag=0.35)
        a = s - self.Tm
        if a >= 0:
            q = cs.proj(self.meet)
            fx.orb(fr, cs, self.meet, 0.38 + a * 4, 'purple', s, seed=3)
            fx.impact_burst(fr, q[0], q[1], a, size=320, pal='purple', seed=9, spikes=10, life=0.1)
        if s < 0.35:
            # rack focus: starts soft
            fr.post.append(fx.defocus(9.0 * (1 - s / 0.35) ** 1.5))


# ============================================================================ shot 122
class S122(Shot):
    """Sukuna crosses his arms against the purple light; the light floods in (purple, not white)."""
    t0, t1 = 3118 / 24, 3154 / 24
    vignette = 0.15

    def setup(self):
        s = self.s = Actor(Figure(SUKUNA, 1.0))
        s.k(0, yaw=-math.pi * 0.80, root=V(0, 0.90, 0), lean=0.05, twist=0.15, hpitch=0.05, hyaw=0.15,
            foot_l=V(-0.2, 0, 0.1), foot_r=V(0.2, 0, -0.2), fist_l=1, fist_r=1, eye_glow=1.4, eye_fire=0.8,
            hand_l=V(0.05, -0.2, 0.25), hand_r=V(-0.05, -0.2, 0.25), elbow_l=V(-0.8, -0.4, 0.2), elbow_r=V(0.8, -0.4, 0.2))
        # raise the forearms into a cross guard in front of the face
        # one forearm raised across the face as a shield, the eyes looking over it
        s.k(0.35, 'io', hand_l=V(0.30, 0.16, 0.40), elbow_l=V(-0.9, -0.4, 0.5), hand_r=V(0.02, -0.30, 0.05),
            elbow_r=V(0.8, -0.3, -0.4), lean=0.12, hpitch=0.12)
        s.k(1.5, hand_l=V(0.26, 0.22, 0.46), lean=0.32, hpitch=0.28, hyaw=0.35, twist=0.35, root=V(0.12, 0.86, 0.10))
        J = s.fig.pose(0.0)
        Hh = J['H']
        F = J['Rh'] @ V(0, 0, 1)
        self.cam = Cam(Ch(Hh + F * 1.30 + V(0.25, -0.02, 0)).key(1.5, Hh + F * 0.95 + V(0.12, 0.0, 0)),
                       Ch(Hh + V(-0.05, -0.12, 0)), fov=44, roll=Ch(6.0))
        self.cam.shake(0.0, 3, 1.5, 9)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        u = smoothstep(0.0, 1.5, s)
        paper(fr)
        # the purple light comes from the upper left and swells (layered, never flat white);
        # it is behind him, he stays a solid figure guarding against it
        fx.light_wash(fr, -100, 100, 900 + 1100 * u, (0.55, 0.20, 1.0), 0.15 + 0.6 * u ** 1.5)
        fx.light_wash(fr, -100, 100, 400 + 600 * u, (0.85, 0.65, 1.0), 0.08 + 0.5 * u ** 2)
        draw_actors(fr, self.cam, s, s, [self.s])
        fx.light_wash(fr, -100, 100, 600 + 500 * u, (0.6, 0.3, 1.0), 0.05 + 0.15 * u, layer='g')


# ============================================================================ shot 123
class S123(Shot):
    """Gojo's face, one eye open and burning cyan, backlit as the purple light swells behind him."""
    t0, t1 = 3154 / 24, 3194 / 24
    vignette = 0.12

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06))
        g.k(0, yaw=math.pi, root=V(0, 0.95, 0), hpitch=-0.05, hroll=0.04, eye_glow=1.2, eye_fire=0.35,
            eye_r=0.08, eye_l=1.0, eye_open=0.85, foot_l=V(0.15, 0, 0), foot_r=V(-0.15, 0, 0))
        g.k(1.66, eye_glow=1.6, eye_fire=0.6, eye_open=1.0, hpitch=-0.14, hyaw=0.18, hroll=-0.04)
        J = g.fig.pose(0.0)
        Hh = J['H']
        self.H = Hh
        self.cam = Cam(Ch(Hh + V(0.06, -0.08, -1.05)).key(1.66, Hh + V(-0.03, -0.04, -0.62)),
                       Ch(Hh + V(0, -0.06, 0)), fov=46)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        u = smoothstep(0.0, 1.66, s)
        paper(fr)
        q = cs.proj(self.H + V(0, -0.1, 0.6))
        # backlight swelling behind the head: violet outside, lavender inside
        fx.light_wash(fr, q[0], q[1], 500 + 900 * u ** 1.3, (0.50, 0.15, 0.95), 0.25 + 0.6 * u ** 1.5)
        fx.light_wash(fr, q[0], q[1], 300 + 700 * u ** 1.3, (0.85, 0.65, 1.0), 0.1 + 0.6 * u ** 2)
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.light_wash(fr, q[0], q[1], 500 + 700 * u, (0.6, 0.3, 1.0), 0.04 + 0.12 * u, layer='g')


# ============================================================================ shot 124
class S124(Shot):
    """The explosion: purple streaks across the sky, then a sphere of purple light rising behind
    the skyline and swallowing it - layered, never flat white."""
    t0, t1 = 3194 / 24, 3261 / 24

    def setup(self):
        self.blds = city(seed=7, y_top=0, n=40, spread=110, z0=40, z1=110, hmin=6, hmax=26, base=-60, ink=True)
        self.C = V(4.0, 6.0, 140.0)
        self.cam = Cam(Ch(V(-8.0, 16.0, -30.0)).key(2.79, V(8.0, 17.5, -26.0)),
                       Ch(V(-2.0, 20.0, 60.0)).key(2.79, V(6.0, 23.0, 60.0)), fov=50)
        self.cam.shake(0.21, 10, 0.6)

    def dome(self, fr, cs, s):
        a = s - 0.21
        if a < 0:
            return
        R = 8.0 + 120.0 * (1 - math.exp(-a / 1.1))
        q = cs.proj(self.C)
        rp = R * cs.scale(q[2])
        x, y = q[0], q[1]
        # layered sphere of light: wide purple halo, violet body, lavender inner, small hot core
        fr.g.drawCircle(x, y, rp * 2.2, paint((0.45, 0.10, 0.85), 0.55, add=True, blur=rp * 0.9))
        pb = skia.Paint(AntiAlias=True)
        pb.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), rp,
                                                    [col((1.00, 0.86, 1.0), 1, 1.7), col((0.85, 0.55, 1.0), 1, 1.4),
                                                     col((0.62, 0.25, 1.0), 1, 1.2), col((0.40, 0.08, 0.80), 1, 1.0)],
                                                    [0.0, 0.25, 0.65, 1.0]))
        fr.b.drawCircle(x, y, rp, pb)
        fr.g.drawCircle(x, y, rp * 0.55, paint((0.9, 0.7, 1.0), 0.5, add=True, blur=rp * 0.25))
        # rim and a second, faster shock shell
        fr.g.drawCircle(x, y, rp, paint((0.85, 0.6, 1.0), 0.8, stroke=max(2, rp * 0.02), add=True, blur=rp * 0.01))
        r2 = rp * (1.15 + 0.6 * smoothstep(0, 2.5, a))
        fr.g.drawCircle(x, y, r2, paint((0.7, 0.4, 1.0), 0.35 * (1 - smoothstep(0, 2.6, a)), stroke=max(2, rp * 0.03), add=True, blur=rp * 0.02))
        # rays
        for i in range(36):
            ang = hash01(4, i) * 2 * math.pi + a * 0.05
            L = rp * (1.3 + 1.2 * hash01(5, i))
            wdt = rp * 0.02 * (0.5 + hash01(6, i))
            ca, sa = math.cos(ang), math.sin(ang)
            pts = [(x + ca * rp * 0.6 - sa * wdt, y + sa * rp * 0.6 + ca * wdt), (x + ca * L, y + sa * L),
                   (x + ca * rp * 0.6 + sa * wdt, y + sa * rp * 0.6 - ca * wdt)]
            fr.g.drawPath(poly_path(pts, closed=True), paint((0.7, 0.45, 1.0), 0.35, add=True, blur=wdt))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        if s < 0.21:
            # the purple beam tearing across the sky with a tiny figure caught in it
            fx.streak_lines(fr, -0.12, int(s * 60), n=60, color=(0.55, 0.2, 1.0), alpha=0.8, width=6,
                            length=(500, 1400), layer='g', band=(H * 0.25, H * 0.7))
            ink = THEME['ink']
            fr.b.drawCircle(W * 0.5, H * 0.45, 9, paint(ink))
            fr.b.drawLine(W * 0.5, H * 0.45, W * 0.5 - 6, H * 0.45 + 22, paint(ink, stroke=5))
            draw_buildings(fr, cs, self.blds, fog_color=THEME['bg'], fog_dist=400)
            return
        a = s - 0.21
        glow = smoothstep(0, 2.4, a)
        q = cs.proj(self.C)
        fx.light_wash(fr, q[0], q[1], 900 + 1400 * glow, (0.62, 0.35, 1.0), 0.25 + 0.6 * glow)
        self.dome(fr, cs, s)
        draw_buildings(fr, cs, self.blds, fog_color=(0.45, 0.35, 0.6), fog_dist=400)


# ============================================================================ shot 125
class S125(Shot):
    t0, t1 = 3261 / 24, 3272 / 24

    def draw(self, fr, s):
        u = smoothstep(0.0, 0.46, s)
        c = mix((0.80, 0.62, 1.0), THEME['bg'], u)
        fr.b.clear(paint(c).getColor4f())


SHOTS = [S121, S122, S123, S124, S125]
SEGMENTS = [(S121.t0, S125.t1)]
