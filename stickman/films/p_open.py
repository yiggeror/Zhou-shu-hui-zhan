"""Pilot part 1: cold open (original shots 0-3, 3.04 s - 6.13 s).
Fists toward the lens (cyan, then red), top-down cross-counter, title shards."""
import math
import numpy as np
import skia
from engine.mathx import V, norm, hash01, clamp, smoothstep
from engine.anim import Ch
from engine.rig import Figure, GOJO, SUKUNA
from engine.camera import Cam, W, H
from engine.shot import Shot, Actor, draw_actors, cam_blur, set_blur
from engine.env import Sky, Ground, contact_shadow
from engine.canvas import paint, poly_path, col
from engine import fx

TITLE_TEXT = False   # no text in the video (the user adds titles)


from engine.theme import T as THEME


def void(fr):
    """the bare paper"""
    fr.b.clear(col(THEME['bg']))


# ============================================================================ shot 0 / 1
class FistToLens(Shot):
    """A punch thrown straight at the camera in slow motion, the fist burning."""
    style, pal, mirror = GOJO, 'cyan', 1.0

    def setup(self):
        a = self.a = Actor(Figure(self.style, 1.06 if self.style is GOJO else 1.0))
        m = self.mirror
        # the fighter faces the camera (+z), camera in front of him, slightly low
        a.k(0, yaw=0.0, root=V(0.0, 0.86, 0.0), lean=0.15, twist=0.45 * m, hpitch=0.05, hyaw=-0.1 * m,
            eye_glow=0.2, eye_open=0.6, eye_fire=0.0, fist_l=1.0, fist_r=1.0,
            hand_r=V(0.16 * m, -0.20, -0.18), elbow_r=V(0.25, -0.6, -0.8), hand_l=V(0.0, -0.05, 0.30),
            elbow_l=V(-0.7, -0.6, 0.0))
        a.fig.set(foot_l=V(-0.18, 0, 0.35), foot_r=V(0.20, 0, -0.35))
        # fast extension, then a slow-motion drift toward the lens
        side = 'r' if m > 0 else 'l'
        a.k(0.05, hand_r=V(0.16 * m, -0.18, -0.16))
        a.k(0.17, 'outexp', twist=-0.35 * m, lean=0.30, root=V(0.0, 0.84, 0.12),
            eye_glow=1.0, eye_open=1.0, hpitch=0.0)
        a.k(0.75, twist=-0.55 * m, lean=0.40, root=V(0.0, 0.83, 0.30), eye_fire=0.4, hyaw=-0.18 * m)
        # the fist is thrown at the lens: camera half a metre in front of the extended fist
        cam0 = V(-0.08 * m, 1.34, 1.10)
        Sr = V(0.06 * m, 1.42, 0.14)
        d = norm(cam0 - Sr)
        fist = lambda reach, dx: Sr + d * reach + V(dx * m, 0.02, 0.0)
        a.fig.set(hand_rw=Ch(fist(0.20, 0.10)).key(0.17, fist(0.50, 0.06), 'outexp').key(0.75, fist(0.60, 0.02), 'sm'))
        a.k(0.0, hand_rwb=0.0).k(0.05, hand_rwb=0.0).k(0.17, 'outexp', hand_rwb=1.0)
        F = a.fig
        self.flames = [fx.Flame(lambda t: F.pose(t)['Wr'], self.pal, size=0.05, rise=0.45, life=0.22,
                                src2=lambda t: F.pose(t)['Er'], seg=(0.6, 1.0), seed=3 if m > 0 else 4, trail=0.3,
                                amount=Ch(0.0).key(0.03, 0.0).key(0.12, 1.0, 'out'))]
        # close and low, the punch comes almost straight at the lens
        self.cam = Cam(Ch(cam0).key(0.75, cam0 + V(0.03 * m, 0.03, 0.05)),
                       Ch(V(0.10 * m, 1.52, 0.0)).key(0.75, V(0.11 * m, 1.54, 0.0)), fov=52,
                       roll=Ch(-8.0 * m).key(0.75, -6.0 * m))


    def draw(self, fr, s):
        void(fr)
        cs = self.cam.at(s)
        draw_actors(fr, self.cam, s, s, [self.a])
        fx.render_flames(fr, cs, self.flames, s)


class S0(FistToLens):
    t0, t1 = 73 / 24, 91 / 24
    style, pal, mirror = GOJO, 'cyan', 1.0


class S1(FistToLens):
    t0, t1 = 91 / 24, 109 / 24
    style, pal, mirror = SUKUNA, 'red', -1.0


# ============================================================================ shot 2
class S2(Shot):
    """Top-down: cross-counter, the arms cross and the energies meet; camera rises fast."""
    t0, t1 = 109 / 24, 126 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06))
        s = self.s = Actor(Figure(SUKUNA, 1.0))
        T = self.T = 4.751 - self.t0
        GY, SY = math.pi / 2, -math.pi / 2
        # Gojo on the left (-x) facing +x, Sukuna on the right facing -x, slightly offset in z
        g.k(0, yaw=GY - 0.15, root=V(-0.58, 0.82, 0.10), lean=0.35, twist=-0.5, foot_l=V(-0.15, 0, 0.25),
            foot_r=V(-1.15, 0, -0.10), fist_l=1, fist_r=1, hand_r=V(0.15, -0.10, -0.25), hand_l=V(0.0, -0.05, 0.30),
            elbow_r=V(0.6, 0, -0.8), elbow_l=V(-0.7, -0.6, 0), eye_glow=1.0)
        s.k(0, yaw=SY - 0.15, root=V(0.58, 0.82, -0.10), lean=0.35, twist=0.5, foot_l=V(0.15, 0, -0.25),
            foot_r=V(1.15, 0, 0.10), fist_l=1, fist_r=1, hand_r=V(0.15, -0.10, -0.25), hand_l=V(0.0, -0.05, 0.30),
            elbow_r=V(0.6, 0, -0.8), elbow_l=V(-0.7, -0.6, 0), eye_glow=1.0)
        # both throw the right hand past the other's head
        for a, sg in ((g, 1), (s, -1)):
            a.k(T - 0.11, hand_r=V(0.16, -0.08, -0.28))
            a.k(T, 'in', hand_r=V(-0.10, 0.12, 0.66), twist=0.55 * sg / sg, lean=0.45)
            a.k(0.71, hand_r=V(-0.12, 0.14, 0.70), twist=0.62, lean=0.48)
        # each slips his head to the outside of the other's punch
        g.k(T, root=V(-0.50, 0.80, 0.22), hyaw=-0.35, bend=-0.35)
        s.k(T, root=V(0.50, 0.80, -0.22), hyaw=-0.35, bend=-0.35)
        g.k(0.71, root=V(-0.46, 0.79, 0.24), bend=-0.40)
        s.k(0.71, root=V(0.46, 0.79, -0.24), bend=-0.40)
        self.hitstop(T, 3)
        G, S = g.fig, s.fig
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.09, rise=0.4, src2=lambda t: G.pose(t)['Er'], seg=(0.5, 1.0), seed=7, trail=0.45),
                       fx.Flame(lambda t: S.pose(t)['Wr'], 'red', size=0.09, rise=0.4, src2=lambda t: S.pose(t)['Er'], seg=(0.5, 1.0), seed=8, trail=0.45)]
        self.ground = Ground(color=THEME['bg'], far_color=THEME['bg'],
                             lines=[(V(-30, 0, z), V(30, 0, z), 0.06, 0.7) for z in (-2.6, 2.6)] +
                                   [(V(x, 0, 0), V(x + 1.6, 0, 0), 0.05, 0.5) for x in range(-30, 30, 4)])
        # top-down: rises slowly, then shoots up at the end
        self.cam = Cam(Ch(keys=[(-0.06, V(1.2, 2.6, -1.0)), (0.04, V(0.25, 2.75, -1.55), 'out')]).key(0.55, V(0.2, 3.4, -1.8))
                       .key(0.71, V(0.1, 9.0, -2.4), 'in'),
                       Ch(keys=[(-0.06, V(-0.6, 1.0, 0.0)), (0.04, V(0.0, 1.0, 0.0), 'out')]),
                       fov=50, roll=Ch(-14.0).key(0.71, -22.0))
        self.cam.shake(T, 26, 0.35).punch(T, 0.08)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        void(fr)
        self.ground.draw(fr, cs)
        for a in (self.g, self.s):
            contact_shadow(fr, cs, a.fig.pose(tau), a.fig.k)
        draw_actors(fr, self.cam, s, tau, [self.g, self.s])
        fx.render_flames(fr, cs, self.flames, tau)
        a = s - self.T
        P = V(0.0, 1.55, 0.0)
        q = cs.proj(P)
        if a >= 0:
            fx.impact_burst(fr, q[0], q[1], a, size=200, pal='white', seed=5, spikes=12, life=0.10)
            fx.impact_burst(fr, q[0] + 30, q[1] - 20, a - 0.01, size=150, pal='cyan', seed=6, spikes=6, life=0.10, ring=False)
            fx.impact_burst(fr, q[0] - 30, q[1] + 20, a - 0.01, size=150, pal='red', seed=7, spikes=6, life=0.10, ring=False)
            fx.shock_ring_3d(fr, cs, V(0, 0.03, 0), V(0, 1, 0), a, r0=0.3, r1=3.0, life=0.4, pal='white', width=0.03, k=0.5)
            if a < 1 / 60:
                fr.impact = dict(bg=(1, 1, 1), fg=(0, 0, 0), energy=True)
            elif a < 2 / 60:
                fr.impact = dict(bg=(0, 0, 0), fg=(1, 1, 1), energy=True)
            if a < 0.25:
                fr.post.append(fx.radial_warp(q[0], q[1], 60 + 900 * a, 40 + 60 * a, 12 * (1 - a / 0.25)))
            if 0.02 < a < 0.3:
                seed = int(s * 30)
                fx.bolt(fr, (q[0] - 10, q[1]), (q[0] - 160 - 90 * hash01(seed, 1), q[1] + 120 * hash01(seed, 2)), seed, 'cyan', 2.2, 0.8 * (1 - a / 0.3))
                fx.bolt(fr, (q[0] + 10, q[1]), (q[0] + 160 + 90 * hash01(seed, 3), q[1] - 120 * hash01(seed, 4)), seed + 9, 'red', 2.2, 0.8 * (1 - a / 0.3))
        if s < 0.05:
            # whip in from the previous shot
            fr.post.append(fx.whip_blur(160 * (1 - s / 0.05), 30))
        cam_blur(fr, self.cam, s)


# ============================================================================ shot 3: title
class S3(Shot):
    """Title: white slabs slash across black, the four characters land one by one between
    the shards, then the shards break the frame apart."""
    t0, t1 = 126 / 24, 148 / 24
    vignette = 0.1

    def setup(self):
        self.font = skia.Font(skia.Typeface.MakeFromFile('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'), 290)
        self.chars = '呪術廻戦'
        self.times = [0.10, 0.17, 0.24, 0.31]
        # slabs: (angle, offset, width, t_in, colour)
        self.slabs = []
        for i in range(14):
            ang = math.radians(-28 + 56 * hash01(3, i)) + (math.pi / 2 if hash01(4, i) > 0.7 else 0)
            self.slabs.append(dict(ang=ang, off=(hash01(5, i) - 0.5) * 1300, w=20 + 110 * hash01(6, i) ** 2,
                                   t=0.02 + 0.5 * hash01(7, i) ** 1.5, white=hash01(8, i) > 0.35))

    def slab(self, c, ang, off, w, u, colr, alpha=1.0):
        # a long band through the frame centre, revealed from one end
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        L = 2600
        cx, cy = W / 2 + nx * off, H / 2 + ny * off
        x0, y0 = cx - ca * L / 2, cy - sa * L / 2
        x1, y1 = x0 + ca * L * u, y0 + sa * L * u
        pts = [(x0 + nx * w / 2, y0 + ny * w / 2), (x1 + nx * w / 2, y1 + ny * w / 2), (x1 - nx * w / 2, y1 - ny * w / 2), (x0 - nx * w / 2, y0 - ny * w / 2)]
        c.drawPath(poly_path(pts, closed=True), paint(colr, alpha))

    def draw(self, fr, s):
        c = fr.b
        void(fr)
        INKC = THEME['ink']
        LIGHT = tuple(ch * 0.82 for ch in THEME['bg'])
        # first: two giant slabs slash in
        u0 = smoothstep(0.0, 0.07, s)
        self.slab(c, math.radians(-24), -160, 520, u0, LIGHT)
        self.slab(c, math.radians(-24), 260, 180, u0, INKC)
        for i, sl in enumerate(self.slabs):
            u = smoothstep(sl['t'], sl['t'] + 0.06, s)
            if u <= 0:
                continue
            colr = LIGHT if sl['white'] else INKC
            self.slab(c, sl['ang'], sl['off'], sl['w'], u, colr)
        if TITLE_TEXT:
            x = W / 2 - 2 * 300
            for i, ch in enumerate(self.chars):
                a = s - self.times[i]
                if a < 0:
                    continue
                pop = 1.0 + 0.25 * math.exp(-a * 30)
                blob = skia.TextBlob.MakeFromString(ch, self.font)
                cx, cy = x + i * 300 + 145, H / 2 + 20
                c.save()
                c.translate(cx, cy)
                c.scale(pop, pop)
                c.translate(-145, 105)
                # thick black outline, white body (stroked too, for weight)
                c.drawTextBlob(blob, 0, 0, paint((0, 0, 0), 1.0, stroke=30))
                c.drawTextBlob(blob, 0, 0, paint((0.98, 0.98, 1.0), 1.0, stroke=7))
                c.drawTextBlob(blob, 0, 0, paint((0.98, 0.98, 1.0), 1.0))
                c.restore()
                # pulse of light when the character lands
                if a < 0.12:
                    fr.g.drawCircle(cx, cy, 160, paint((0.6, 0.4, 1.0), 0.35 * (1 - a / 0.12), add=True, blur=60))
        # end: black shards sweep in and break the frame
        if s > 0.62:
            for i in range(9):
                u = smoothstep(0.62 + 0.025 * i, 0.70 + 0.025 * i, s)
                ang = math.radians(35 + 30 * hash01(11, i))
                self.slab(c, ang, (hash01(12, i) - 0.5) * 1500, 160 + 220 * hash01(13, i), u, INKC)
        if s < 0.03:
            fx.flash(fr, (0.6, 0.4, 1.0), 0.35 * (1 - s / 0.03))


SHOTS = [S0, S1, S2, S3]
SEGMENTS = [(S0.t0, S3.t1)]
