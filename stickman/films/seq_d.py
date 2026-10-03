"""Sequence D: the first Hollow Purple, shots 37-41 (frames 1170-1242)."""
from films.common import *
from engine.env import Building, draw_buildings
from films.seq_b import city_ring
from films.purple_fx import violet_wash, lavender_flash, wisp, light_body, god_rays, ink_box, mixc3

MAG = fx.PAL['magenta']


# ============================================================================ 37: the charge in his fingers
class S37(Shot):
    """close on the face and both hands: the eyes open, a point of purple forms in the pinched
    fingers, lightning climbs over the face, a level flare, then the light bursts"""
    t0, t1 = 1170 / 24, 1190 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO_S, 1.06, 'gojo37'))
        stand(g, 0, 0, 0, math.pi, width=0.18)
        # right hand: open claw by the cheek; left hand: pinched fingers in front of the chin
        g.k(0, hand_r=V(0.10, -0.30, 0.12), hshape_r=shape('claw'), hup_r=V(0.25, 1, 0.1), hback_r=V(0, 0, 1),
            hand_l=V(0.10, -0.30, 0.22), hshape_l=shape('pinch'), hup_l=V(0.0, 1, 0.3), hback_l=V(0, 0.2, 1),
            hpitch=0.22, eye_open=0.12, eye_glow=0.5, lean=0.08, idle=0.6)
        g.k(4 / 24, 'out', hand_r=V(0.10, -0.04, 0.16), hand_l=V(0.10, -0.12, 0.30), hpitch=0.08, eye_open=1.0, eye_glow=1.4)
        g.k(11 / 24, 'io', hand_r=V(0.10, -0.02, 0.17), hand_l=V(0.10, -0.10, 0.31), hpitch=0.04, eye_glow=1.8, eye_fire=0.4)
        # a small draw-in before the release, then the fingers spring open toward the lens
        g.k(16 / 24, 'io', hand_r=V(0.10, -0.04, 0.15), hand_l=V(0.10, -0.13, 0.28), hpitch=0.07, lean=0.06)
        g.k(19 / 24, 'outexp', hand_l=V(0.11, -0.08, 0.40), hand_r=V(0.12, 0.0, 0.16), lean=0.14, hpitch=0.0, eye_fire=0.8,
            hshape_l=shape('open'))
        g.k(D, hand_l=V(0.11, -0.07, 0.41))
        g.follow(['hand_r', 'hand_l', 'hpitch'], 0, D)
        g.d.wind = V(0.0, 0.3, -0.6)
        self.H = H0 = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H0 + V(0.06, -0.16, -1.10)).key(D, H0 + V(0.05, -0.16, -0.98)), Ch(H0 + V(0.0, -0.17, 0)), fov=46)
        self.cam.shake(19 / 24, 18, 0.25)
        self.cam.punch(19 / 24, 0.05, 0.03, 0.2)
        self.blds = city_ring(37, y_top=-4)

    def tip(self, t):
        J = self.g.fig.pose(t)
        return J['Wl'] + J['hup_l'] * 0.11

    def draw(self, fr, s):
        cs = self.cam.at(s)
        f = s * 24
        paper(fr)
        violet_wash(fr, 0.12 + 0.55 * smoothstep(4, 18, f))
        draw_buildings(fr, cs, self.blds, fog_dist=150)
        p = self.tip(s)
        q = cs.proj(p)
        rp = float(np.interp(f, [0, 4, 6, 9, 12, 14, 16, 17, 18, 19, 19.6, 20], [0, 0, 4, 10, 18, 26, 36, 50, 90, 220, 700, 1300]))
        if rp > 0:
            fx.light_wash(fr, q[0], q[1], 220 + 6 * rp, (0.75, 0.5, 1.0), 0.35 * smoothstep(4, 15, f))
        draw_actors(fr, self.cam, s, s, [self.g])
        if rp > 0:
            light_body(fr, q[0], q[1], rp)
        # lightning: one climbing over the face first, then more arcs flicking out as it builds
        if f >= 8:
            slot = int(f / 2)
            n = 1 + int(4 * smoothstep(9, 18, f))
            for j in range(n):
                seed = slot * 11 + j
                if j == 0:
                    e = (q[0] + (hash01(seed, 1) - 0.5) * 160, q[1] - 380 - 200 * hash01(seed, 2))
                else:
                    ang = hash01(seed, 3) * 2 * math.pi
                    L = (160 + 30 * rp) * (0.5 + hash01(seed, 4))
                    e = (q[0] + math.cos(ang) * L, q[1] + math.sin(ang) * L * 0.7)
                fx.bolt(fr, q[:2], e, seed, 'magenta', 1.6 + 0.04 * rp, 0.85, jag=0.3, branches=2)
        # the level flare through the light
        fl = smoothstep(12, 15, f)
        if fl > 0:
            L = min(1600, 260 + 14 * rp)
            wisp(fr.g, q[0] - L, q[1] + 2, q[0] + L, q[1] - 2, 6 + 0.3 * rp, (0.95, 0.7, 1.0), 0.9 * fl)
        if f > 18:
            u = (f - 18) / 2
            lavender_flash(fr, 0.85 * u ** 2)


class S37b(Shot):
    """lavender flash"""
    t0, t1 = 1190 / 24, 1192 / 24

    def draw(self, fr, s):
        paper(fr)
        lavender_flash(fr, 0.95)


# ============================================================================ 38: the light ploughs through the city
class S38(Shot):
    """the camera chases the sphere of light down a street between towers, dutch angle; arcs
    jump from it to the buildings it passes"""
    t0, t1 = 1192 / 24, 1201 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.P = lambda t: V(1.5, 7.0, 24.0 + 150.0 * t)
        self.blds = []
        for i in range(44):
            side = -1 if i % 2 else 1
            x = side * (11 + 9 * hash01(38, i))
            z = (i // 2) * 11.0 + 4 * hash01(37, i)
            w = 7 + 6 * hash01(39, i)
            self.blds.append(Building(x - w / 2, x + w / 2, z, z + 9, 30 + 45 * hash01(40, i), base=-40, seed=380 + i,
                                      style='vstrips', win_density=0.6))
        self.cam = Cam(lambda t: self.P(t) + V(-6.5, 4.5, -17.0), lambda t: self.P(t) + V(0.8, -1.5, 12.0), fov=64,
                       roll=Ch(-26.0).key(D, -19.0))
        self.cam.drift = 0.2
        self.cam.shake(0, 12, D, 30)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        p = self.P(s)
        q = cs.proj(p)
        rp = 5.0 * cs.scale(q[2])
        violet_wash(fr, 0.95)
        fx.light_wash(fr, q[0], q[1], rp * 5, (0.92, 0.5, 1.0), 0.45)
        order = sorted(self.blds, key=lambda b: -float(np.linalg.norm(b.center() - cs.pos)))
        for b in order:
            x0, x1, z0, z1 = b.b
            d = float(np.linalg.norm(b.center() - p))
            lit = clamp(1.4 - d / 30.0, 0, 1)
            colr = mixc3((0.30, 0.12, 0.42), (0.62, 0.30, 0.85), lit)
            ink_box(fr, cs, x0, x1, z0, z1, b.base, b.base + b.h, colr, grid=(mixc3((0.55, 0.28, 0.75), (0.98, 0.70, 1.0), lit), 3.2, 2.4))
        set_blur(fr, self.cam, s, k=0.8, thresh=4, dist=20)
        # the street it has burned behind it
        for k in range(10, 0, -1):
            a, b = cs.proj(self.P(s - k * 0.025)), cs.proj(self.P(s - (k - 1) * 0.025))
            if np.isfinite(a[0]) and np.isfinite(b[0]):
                fr.g.drawLine(a[0], a[1], b[0], b[1], paint((0.85, 0.45, 1.0), 0.05 * (1 - k / 11), k=5.0,
                                                            stroke=rp * 1.5 * (1 - k / 12), add=True, blur=rp * 0.4))
        light_body(fr, q[0], q[1], rp)
        # arcs to the towers alongside (they flicker every two frames)
        slot = int(s * 12)
        near = sorted(self.blds, key=lambda b: abs(float(b.center()[2]) - float(p[2])))[:6]
        for j in range(3):
            b = near[(j * 2 + slot) % len(near)]
            x0, x1, z0, z1 = b.b
            tgt = V(x0 if b.center()[0] > 0 else x1, b.base + b.h * (0.3 + 0.5 * hash01(slot, j)), (z0 + z1) / 2)
            e = cs.proj(tgt)
            if np.isfinite(e[0]):
                fx.bolt(fr, q[:2], e[:2], slot * 7 + j, 'magenta', 2.4, 0.9, jag=0.28, branches=3)
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
            qp = (W * (0.10 - 0.35 * u), H * (0.22 + 0.06 * u))
            light_body(fr, qp[0], qp[1], 260 * (1 - 0.3 * u))
            fx.bolt(fr, qp, (W * 0.3, H * 0.6), int(s * 60), 'magenta', 3.0, 1 - u, branches=3)
        set_blur(fr, self.cam, s, k=0.5, thresh=20)


# ============================================================================ 40: Sukuna braces against it
class S40(Shot):
    """facing the light (and the lens), feet wide, both palms thrust out against it; it shoves
    him back and he turns lavender in it until it floods the frame"""
    t0, t1 = 1212 / 24, 1224 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk40'))
        k.k(0, yaw=math.pi, root=V(0, 0.80, 0), lean=0.22, twist=0.05, foot_l=V(0.34, 0, 0.12), foot_r=V(-0.36, 0, -0.10),
            knee_l=V(0.5, 0, 1), knee_r=V(-0.5, 0, 1),
            hand_l=V(-0.05, -0.16, 0.30), hand_r=V(0.05, -0.14, 0.30), hshape_l=shape('open'), hshape_r=shape('open'),
            hup_l=V(-0.25, 1, 0.1), hup_r=V(0.25, 1, 0.1), hback_l=V(0, 0, -1), hback_r=V(0, 0, -1),
            eye_glow=1.5, eye_fire=0.8, hpitch=0.05)
        k.k(3 / 24, 'outexp', hand_l=V(-0.16, 0.0, 0.54), hand_r=V(0.16, 0.02, 0.53), lean=0.30, root=V(0, 0.76, 0.02))
        k.k(8 / 24, 'io', root=V(0, 0.74, 0.10), lean=0.36, hand_l=V(-0.15, -0.01, 0.51), hand_r=V(0.15, 0.01, 0.50), hpitch=0.12,
            foot_l=V(0.34, 0, 0.16), foot_r=V(-0.36, 0, -0.05))
        k.k(5 / 24, eye_glow=1.5)
        k.k(D, eye_glow=0.35, eye_fire=0.2)   # his eyes sink into the light with the rest of him
        k.k(D, root=V(0, 0.72, 0.18), lean=0.40, hand_l=V(-0.14, -0.02, 0.49), hand_r=V(0.14, 0.0, 0.48), hpitch=0.16,
            foot_l=V(0.34, 0, 0.21), foot_r=V(-0.36, 0, 0.0))
        k.follow(['hand_l', 'hand_r', 'hpitch'], 0, D, f=3.6)
        k.d.wind = V(0.0, 0.1, 1.0)
        Hh = k.fig.pose(4 / 24)['H']
        self.cam = Cam(Ch(Hh + V(0.16, -0.22, -1.02)).key(D, Hh + V(0.13, -0.20, -0.94)), Ch(Hh + V(0.0, -0.16, 0)), fov=56)
        self.cam.shake(3 / 24, 14, 0.25).shake(0.2, 7, D, 22)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        u = s / D
        paper(fr)
        violet_wash(fr, 0.45 + 0.45 * u)
        d3.line3(fr, cs, V(-10, 0, 1.2), V(10, 0, 1.2), w_m=0.02)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, self.k.fig.pose(s), self.k.fig, 0.8)
        lit = smoothstep(0.15, 0.85, u)
        if lit > 0:
            fr.b.saveLayerAlpha(None, int(255 * 0.9 * lit))
            draw_actors(fr, self.cam, s, s, [self.k], silhouette=(0.90, 0.74, 1.0), eyes=False)
            fr.b.restore()
        fx.light_wash(fr, W * 0.5, H * 0.6, 700 + 1600 * u ** 1.4, (0.85, 0.45, 1.0), 0.04 + 0.12 * u ** 1.4, layer='g')
        if u > 0.6:
            lavender_flash(fr, ((u - 0.6) / 0.4) ** 1.5 * 0.92)


# ============================================================================ 41: explosion on the facade
class S41(Shot):
    t0, t1 = 1224 / 24, 1242 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.bld = Building(-12, 8, 6, 20, 26, base=-30, seed=41, style='grid', win_density=0.9)
        self.C = V(-5.0, -2.0, 5.0)
        self.burst = fx.Burst(self.C, 0.0, 'magenta', n=120, speed=12.0, size=2.2, life=1.5, seed=41, up=1.5, amp=0.42)
        self.burst2 = fx.Burst(self.C + V(0.5, 1.0, -0.5), 0.28, 'magenta', n=70, speed=7.0, size=1.6, life=1.0, seed=42, up=1.2, amp=0.4)
        self.smoke = [(V((hash01(41, i) - 0.5) * 6, (hash01(42, i) - 0.3) * 4, -1.0), 0.3 + 0.4 * hash01(43, i)) for i in range(9)]
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
        fx.render_flames(fr, cs, [self.burst, self.burst2], s, fscale=0.2, warp=2.2)
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
