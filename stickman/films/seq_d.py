"""Sequence D: the first Hollow Purple, shots 37-41 (frames 1170-1242)."""
from films.common import *
from engine.env import Building, draw_buildings
from films.seq_b import city_ring

MAG = fx.PAL['magenta']


def violet_wash(fr, k):
    """the purple light colouring the paper (watercolour-like wash, kept light)"""
    if k > 0:
        fr.b.drawRect(skia.Rect(0, 0, W, H), paint((0.62, 0.45, 0.82), min(0.85, k * 0.6)))


def lavender_flash(fr, k):
    """a flash that stays purple: the centre goes lavender-white, the edges keep magenta"""
    if k <= 0:
        return
    def fn(img, k=k):
        h, w = img.shape[:2]
        yy, xx = np.mgrid[0:h:8, 0:w:8].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        m = np.clip(1.15 - r * 0.55, 0, 1)
        import cv2
        m = cv2.resize(m, (w, h))[..., None]
        tint = np.array((0.96, 0.86, 1.0), np.float32) * m + np.array((0.78, 0.32, 0.98), np.float32) * (1 - m)
        return img * (1 - k) + tint * k
    fr.post.append(fn)


# ============================================================================ 37: the charge in his fingers
class S37(Shot):
    t0, t1 = 1170 / 24, 1190 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO_S, 1.06, 'gojo37'))
        stand(g, 0, 0, 0, math.pi, width=0.18)
        # right hand in front of the face, fingers pinched around the light
        g.k(0, hand_r=V(-0.10, 0.27, 0.22), elbow_r=V(0.7, -0.7, 0.1), hshape_r=shape('pinch'), hroll_r=-0.9,
            hand_l=V(0.05, -0.3, 0.2), hpitch=0.15, eye_open=0.75, eye_glow=0.9, eye_fire=0.2, lean=0.05, idle=0.5)
        g.k(0.25, eye_open=1.0, eye_glow=1.4, hpitch=0.05)
        # anticipation: hand draws back toward the face, then thrusts at the lens (world target)
        g.k(0.50, 'io', lean=-0.02, twist=0.08)
        g.k(0.78, 'outexp', lean=0.18, twist=-0.15, eye_fire=0.6, hpitch=-0.02)
        g.k(D, lean=0.2, twist=-0.18)
        H0 = g.fig.pose(0)['H']
        g.fig.set(hand_rw=Ch(H0 + V(0.02, -0.14, -0.22)).key(0.50, H0 + V(0.03, -0.13, -0.17), 'io').key(0.62, H0 + V(0.03, -0.13, -0.16))
                  .key(0.78, H0 + V(-0.02, -0.16, -0.55), 'outexp').key(D, H0 + V(-0.03, -0.16, -0.58)))
        g.k(0, hand_rwb=1.0)
        g.follow(['hpitch'], 0, D)
        g.d.wind = V(0.0, 0.3, -0.6)
        J = g.fig.pose(0)
        self.H = J['H']
        self.cam = Cam(Ch(self.H + V(-0.10, -0.10, -0.95)).key(D, self.H + V(-0.08, -0.10, -0.86)), Ch(self.H + V(0.04, -0.1, 0)), fov=46)
        self.cam.shake(0.78, 18, 0.25)
        self.blds = city_ring(37, y_top=-4)
        self.charge = Ch(0.05).key(0.25, 0.15).key(0.62, 0.55, 'in').key(0.80, 1.0, 'out').key(D, 1.3, 'in')

    def tip(self, t):
        J = self.g.fig.pose(t)
        return J['Wr'] + norm(J['Wr'] - J['Er']) * 0.12 + J['Rc'] @ V(-0.02, 0.0, 0.0)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        ch = float(self.charge(s))
        violet_wash(fr, 0.12 + 0.3 * ch)
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        draw_actors(fr, self.cam, s, s, [self.g])
        p = self.tip(s)
        q = cs.proj(p)
        r = 0.012 + 0.03 * ch
        fx.orb(fr, cs, p, r, 'magenta', s, seed=7, arcs=3, k=min(1.0, 0.4 + ch))
        fx.light_wash(fr, q[0], q[1], 180 + 380 * ch, MAG['glow'], 0.25 * ch, layer='g')
        # arcs crawling off the hand, more and longer as the charge builds
        nb = int(1 + 4 * ch)
        for j in range(nb):
            seed = int(s * 24) * 7 + j
            ang = hash01(seed, 1) * 2 * math.pi
            L = (80 + 380 * ch) * (0.5 + hash01(seed, 2))
            e = (q[0] + math.cos(ang) * L, q[1] + abs(math.sin(ang)) * L * 0.8 + 20)
            fx.bolt(fr, q[:2], e, seed, 'magenta', 1.5 + 2 * ch, 0.6 + 0.4 * ch, jag=0.3, branches=2)
        if s > 0.84:
            u = (s - 0.84) / (D - 0.84)
            fx.light_wash(fr, q[0], q[1], 300 + 1400 * u, MAG['mid'], 0.6 * u, layer='g')
            lavender_flash(fr, 0.85 * u ** 2)


class S37b(Shot):
    """lavender flash"""
    t0, t1 = 1190 / 24, 1192 / 24

    def draw(self, fr, s):
        paper(fr)
        lavender_flash(fr, 0.95)


# ============================================================================ 38: riding along the beam
class S38(Shot):
    t0, t1 = 1192 / 24, 1201 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.blds = []
        for i in range(26):
            x = (-1) ** i * (9 + 14 * hash01(38, i))
            z = i * 14.0
            w = 7 + 6 * hash01(39, i)
            self.blds.append(Building(x - w / 2, x + w / 2, z, z + 9, 30 + 40 * hash01(40, i), base=-40, seed=380 + i,
                                      style='vstrips', win_density=0.6))
        self.cam = Cam(Ch(V(-3.0, 6.0, -10.0)).key(D, V(-2.5, 6.5, 70.0), 'lin'),
                       Ch(V(1.0, 4.0, 30.0)).key(D, V(1.5, 4.5, 110.0), 'lin'), fov=60, roll=Ch(-28.0).key(D, -22.0))
        self.cam.shake(0, 14, D, 30)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        violet_wash(fr, 0.42)
        draw_buildings(fr, cs, self.blds, fog_color=(0.62, 0.45, 0.8), fog_dist=160)
        set_blur(fr, self.cam, s, k=0.8, thresh=4, dist=20)
        cz = float(cs.pos[2])
        head = cz + 60 + 40 * s / D
        pts = [V(3.0, 3.0, z) for z in np.linspace(cz - 5, head, 30)]
        fx.beam(fr, cs, pts, 4.5, 'magenta', 1.0)
        qh = cs.proj(V(3.0, 3.0, cz + 25))
        for j in range(4):
            seed = int(s * 60) * 5 + j
            b = cs.proj(self.blds[(j * 3 + int(s * 30)) % len(self.blds)].center())
            if np.isfinite(b[0]):
                fx.bolt(fr, qh[:2], b[:2], seed, 'magenta', 2.0, 0.9, jag=0.25, branches=3)
        if s < 2 / 24:
            lavender_flash(fr, 0.8 * (1 - s / (2 / 24)))


# ============================================================================ 39: the beam passes, Sukuna on a far roof
class S39(Shot):
    t0, t1 = 1201 / 24, 1212 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk39'))
        # climbing up onto the roof edge: from crouched below the edge to standing
        k.k(0, yaw=math.pi, root=V(0.0, -0.4, 30.0), lean=0.8, foot_l=V(-0.15, -0.9, 30.2), foot_r=V(0.15, -0.6, 30.1),
            hand_lwb=1.0, hand_rwb=1.0, eye_glow=1.3, eye_fire=0.4)
        k.fig.set(hand_lw=V(-0.25, 0.0, 29.85), hand_rw=V(0.25, 0.0, 29.85))
        k.k(0.18, root=V(0.0, -0.3, 30.0))
        k.k(0.32, 'out', root=V(0.0, 0.55, 29.9), lean=0.6, foot_r=V(0.18, 0.0, 29.9), hand_lwb=0.6, hand_rwb=0.6)
        k.k(D, 'io', root=V(0.0, 0.88, 29.85), lean=0.25, foot_l=V(-0.18, 0.0, 29.95), hand_lwb=0.0, hand_rwb=0.0,
            hand_l=V(-0.1, -0.4, 0.15), hand_r=V(0.1, -0.4, 0.15))
        self.roof = Building(-12, 12, 29.8, 60, 50, base=-50, seed=391, style='vstrips', win_density=0.4)
        self.near = Building(-15, 15, -8, 2, 40, base=-41, seed=392, style='vstrips', win_density=0.4)
        self.blds = city_ring(39, y_top=-3, r0=60)
        self.cam = Cam(Ch(V(4.0, 0.9, -1.0)).key(D, V(3.6, 0.85, 0.2)), Ch(V(-6.0, 3.0, 40.0)).key(0.18, V(0.2, 0.9, 30.0), 'out'), fov=Ch(50).key(D, 40))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        violet_wash(fr, 0.32)
        fx.light_wash(fr, -200, H * 0.3, 900, MAG['mid'], 0.35 + 0.4 * s, layer='g')
        draw_buildings(fr, cs, self.blds + [self.roof], fog_color=(0.6, 0.45, 0.78), fog_dist=200)
        self.near.draw(fr, cs, fog_dist=300)
        draw_actors(fr, self.cam, s, s, [self.k])
        if s < 0.15:
            u = s / 0.15
            pts = [V(-30 + 40 * u, 6 - 2 * u, z) for z in np.linspace(10, 70, 12)]
            fx.beam(fr, cs, pts, 2.0 * (1 - u), 'magenta', 1.0 - u)
            fx.bolt(fr, (W * 0.15, 0), (W * 0.3, H * 0.6), int(s * 60), 'magenta', 3.0, 1 - u, branches=3)
        set_blur(fr, self.cam, s, k=0.5, thresh=20)


# ============================================================================ 40: Sukuna braces against it
class S40(Shot):
    t0, t1 = 1212 / 24, 1224 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk40'))
        k.k(0, yaw=math.pi + 0.35, root=V(0, 0.6, 0), lean=0.55, twist=0.25, foot_l=V(-0.35, 0, 0.35), foot_r=V(0.3, 0, -0.45),
            hand_r=V(-0.05, 0.12, 0.55), hand_l=V(0.25, -0.05, 0.4), hshape_r=shape('open'), hshape_l=shape('claw'),
            hroll_r=-1.6, elbow_r=V(0.7, -0.6, -0.2), eye_glow=1.5, eye_fire=0.8, hpitch=-0.15)
        k.k(0.25, 'out', hand_r=V(-0.05, 0.14, 0.62), lean=0.62, root=V(0.0, 0.57, -0.03))
        k.k(D, hand_r=V(-0.04, 0.15, 0.63), lean=0.66, root=V(0.0, 0.55, -0.08), hpitch=-0.22)
        k.d.wind = V(0.2, 0.1, -1.0)
        J = k.fig.pose(0.3)
        self.W0 = J['Wr']
        F = J['Rp'] @ V(0, 0, 1)
        Rr = J['Rp'] @ V(1, 0, 0)
        Hh = J['H']
        self.cam = Cam(Ch(Hh + F * 0.68 - Rr * 0.22 + V(0, -0.16, 0)).key(D, Hh + F * 0.6 - Rr * 0.2 + V(0, -0.16, 0)),
                       Ch(Hh + V(0, -0.14, 0) + F * 0.2), fov=64)
        self.cam.shake(0, 10, D, 25)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        u = s / D
        paper(fr)
        violet_wash(fr, 0.35 + 0.2 * u)
        d3.line3(fr, cs, V(-10, 0, 1.0), V(10, 0, 1.0), w_m=0.02)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, self.k.fig.pose(s), self.k.fig, 0.8)
        # the light floods in from the left
        fx.light_wash(fr, -300 + 500 * u, H * 0.45, 700 + 1600 * u ** 1.5, MAG['mid'], 0.4 + 0.9 * u ** 1.5, layer='g')
        fx.light_wash(fr, -300 + 400 * u, H * 0.45, 400 + 1100 * u ** 2, MAG['core'], 0.2 + 0.9 * u ** 2, layer='g')
        if u > 0.65:
            lavender_flash(fr, ((u - 0.65) / 0.35) ** 1.5 * 0.9)


# ============================================================================ 41: explosion on the facade
class S41(Shot):
    t0, t1 = 1224 / 24, 1242 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.bld = Building(-12, 8, 6, 20, 26, base=-30, seed=41, style='grid', win_density=0.9)
        self.C = V(-5.0, -2.0, 5.0)
        self.burst = fx.Burst(self.C, 0.0, 'magenta', n=120, speed=12.0, size=2.2, life=1.5, seed=41, up=1.5, amp=0.42)
        self.smoke = [(V((hash01(41, i) - 0.5) * 6, (hash01(42, i) - 0.3) * 4, -1.0), 0.6 + 0.8 * hash01(43, i)) for i in range(9)]
        self.cam = Cam(Ch(V(3.0, -16.0, -9.0)).key(D, V(2.6, -15.5, -8.0)), Ch(V(-3.0, -4.0, 6.0)), fov=60, roll=Ch(10).key(D, 12))
        self.cam.shake(0.0, 16, 0.6).shake(0.18, 10, 0.5)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        violet_wash(fr, 0.3)
        q0 = cs.proj(self.C)
        fx.light_wash(fr, q0[0], q0[1], 800 + 600 * min(1.0, s * 2), (0.85, 0.55, 1.0), 0.45)
        self.bld.draw(fr, cs, fog_dist=300, occlude_glow=False)
        # dark smoke inside the fireball (ink-violet puffs) gives the explosion depth
        for (o, r) in self.smoke:
            age = s
            p = self.C + o * (0.4 + 0.8 * (1 - math.exp(-age * 2))) + V(0, age * 1.0, 0)
            q = cs.proj(p)
            rr = r * (0.6 + 1.2 * (1 - math.exp(-age * 2))) * cs.scale(q[2])
            fr.b.drawCircle(q[0], q[1], rr, paint((0.22, 0.06, 0.32), 0.85 * min(1.0, age * 6), blur=rr * 0.25))
        fx.render_flames(fr, cs, [self.burst], s, fscale=0.2, warp=2.2)
        q = cs.proj(self.C)
        if 0.12 < s < 0.45:
            for j in range(2):
                seed = int(s * 30) * 3 + j
                fx.bolt(fr, (q[0], q[1]), (W + 50, q[1] + (hash01(seed, 1) - 0.4) * 400), seed, 'magenta', 3.0, 1.0, branches=3)
                fx.bolt(fr, (q[0], q[1]), (-50, q[1] + (hash01(seed, 2) - 0.2) * 300), seed + 9, 'magenta', 2.5, 0.8, branches=2)
        if s < 3 / 24:
            lavender_flash(fr, 0.9 * (1 - s / (3 / 24)))
        fx.light_wash(fr, q[0], q[1], 1100, MAG['glow'], 0.12, layer='g')


SHOTS = [S37, S37b, S38, S39, S40, S41]
SEGMENTS = [(S37.t0, S41.t1)]
