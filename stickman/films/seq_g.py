"""Sequence G: shots 62-71 (frames 1560-1924): the domain."""
from films.common import *
from engine.env import Building, draw_buildings
from films.seq_b import city_ring

RED = (0.86, 0.16, 0.20)
RED_D = (0.55, 0.05, 0.09)


def shrine(fr, cs, o=V(0, 0, 0), s=1.0, fill=RED, edge=PAPER, alpha=1.0, horns=True):
    """the Malevolent Shrine: a platform, pillars, a dark mouth, two curved roof tiers with
    upturned eaves and crescent horns"""
    def P(x, y, z):
        return o + V(x, y, z) * s
    d3.box(fr, cs, P(-6, 0, -3), P(6, 1.2, 3), fill=fill, edge=edge, w_m=0.05 * s, alpha=alpha)
    for x in (-4.5, -1.5, 1.5, 4.5):
        d3.box(fr, cs, P(x - 0.3, 1.2, -2.2), P(x + 0.3, 6.0, -1.6), fill=fill, edge=edge, w_m=0.04 * s, alpha=alpha)
    mouth = [P(-1.2, 1.2, -2.25), P(1.2, 1.2, -2.25), P(1.0, 4.2, -2.25), P(-1.0, 4.2, -2.25)]
    d3.poly3(fr, cs, mouth, fill=INK, alpha=alpha)
    for tier, (y, half, depth, lift) in enumerate(((6.0, 8.0, 4.2, 2.2), (9.0, 5.5, 3.2, 1.8))):
        front, back = [], []
        for i in range(17):
            u = -1 + 2 * i / 16
            x = u * half
            yy = y + lift * u ** 4 + 0.4 * (1 - u * u)
            front.append(P(x, yy, -depth))
            back.append(P(x * 0.8, yy + 2.6, 0.5))
        d3.poly3(fr, cs, front + back[::-1], fill=fill, edge=edge, w_m=0.05 * s, alpha=alpha)
        # eave edge line
        d3.poly3(fr, cs, front + [P(half, y + lift - 0.4, -depth), P(-half, y + lift - 0.4, -depth)][::-1], fill=None, edge=edge,
                 w_m=0.04 * s, alpha=alpha)
        if horns:
            for sx in (-1, 1):
                base = P(sx * half * 0.92, y + lift * 0.9, -depth)
                pts = []
                for j in range(9):
                    a = j / 8
                    pts.append(base + V(sx * (0.6 * a), 2.6 * a, -0.2 * a * a) * s * (1 - 0.15 * tier) + V(sx * 0.35 * math.sin(a * 3), 0, 0) * s)
                inner = [p + V(-sx * 0.35 * (1 - j / 8), -0.15, 0) * s for j, p in enumerate(pts)]
                d3.poly3(fr, cs, pts + inner[::-1], fill=edge if fill != edge else fill, edge=None, alpha=alpha)
    # spire
    d3.poly3(fr, cs, [P(-0.6, 10.8, -1.2), P(0.6, 10.8, -1.2), P(0, 13.5, -1.0)], fill=fill, edge=edge, w_m=0.04 * s, alpha=alpha)


def radial_streaks(fr, cx, cy, t, n=120, color=PAPER, alpha=0.8, speed=1.6, seed=62, layer='b'):
    """lines rushing outward from a point (the domain's pull)"""
    c = fr.b if layer == 'b' else fr.g
    R = math.hypot(W, H)
    for i in range(n):
        ang = hash01(seed, i) * 2 * math.pi
        ph = (t * speed * (0.6 + 0.8 * hash01(seed, i, 1)) + hash01(seed, i, 2)) % 1.0
        r0 = R * (0.08 + ph ** 1.6 * 0.9)
        L = R * (0.06 + 0.25 * ph)
        wd = 1.5 + 5 * hash01(seed, i, 3) * ph
        ca, sa = math.cos(ang), math.sin(ang)
        c.drawLine(cx + ca * r0, cy + sa * r0, cx + ca * (r0 + L), cy + sa * (r0 + L), paint(color, alpha * math.sin(math.pi * ph), stroke=wd))


# ============================================================================ 62: the shrine
class S62(Shot):
    t0, t1 = 1560 / 24, 1631 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo62'))
        stand(g, 0, -4.2, -17.0, 0.3, width=0.18)
        g.k(0, hand_r=V(-0.08, 0.22, 0.2), elbow_r=V(0.6, -0.6, 0.2), hshape_r=shape('two'), hand_l=V(-0.05, -0.45, 0.1),
            eye_glow=1.3, hpitch=-0.2, hyaw=0.1, visible=0.0)
        g.k(4 / 24, visible=0.0).k(5 / 24, visible=1.0)
        g.k(1.2, hpitch=-0.25, hyaw=0.05)
        g.k(D, hpitch=-0.22, hyaw=0.12, hand_r=V(-0.07, 0.24, 0.2))
        self.cam = Cam(Ch(V(-5.6, 1.3, -19.6)).key(D, V(-5.2, 1.35, -19.0)), Ch(V(1.0, 6.5, 0)).key(D, V(0.8, 6.6, 0)), fov=54, roll=Ch(-8).key(D, -6))
        self.motes = [(hash01(620, i), hash01(621, i), hash01(622, i)) for i in range(40)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr, INK)
        q = cs.proj(V(0, 5, 0))
        radial_streaks(fr, q[0], q[1], s, n=150, color=(0.75, 0.70, 0.78), alpha=0.6)
        shrine(fr, cs, V(0, 0, 0), 1.0)
        for (a, b, c) in self.motes:
            x = (a * W + s * 40 * (c - 0.5)) % W
            y = (b * H - s * 30 * c) % H
            fr.g.drawCircle(x, y, 2 + 4 * c, paint(fx.PAL['red']['mid'], 0.8, add=True, blur=3))
        draw_actors(fr, self.cam, s, s, [self.g], silhouette=PAPER)


# ============================================================================ 63: the black sphere over the city
class S63(Shot):
    t0, t1 = 1631 / 24, 1668 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.city = []
        for i in range(-5, 6):
            for j in range(-5, 6):
                if abs(i) + abs(j) < 1:
                    continue
                h = 10 + 30 * hash01(63, i, j)
                self.city.append(Building(i * 14 - 5, i * 14 + 5, j * 14 - 5, j * 14 + 5, h, base=0, seed=630 + i * 11 + j,
                                          style='grid', win_density=0.3))
        self.r = Ch(4.0).key(D, 22.0, 'in')
        self.cam = Cam(Ch(V(0.5, 160, -20)).key(D, V(0.3, 70, -8), 'io'), Ch(V(0, 0, 0)), fov=48, roll=Ch(0).key(D, 75, 'io'))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=400)
        q = cs.proj(V(0, 8, 0))
        rp = float(self.r(s)) * cs.scale(q[2])
        fr.b.drawCircle(q[0], q[1], rp, paint(INK))
        fr.b.drawCircle(q[0], q[1], rp * 1.15, paint(INK, 0.25, blur=rp * 0.15))
        set_blur(fr, self.cam, s, k=0.7, thresh=6, dist=60)


# ============================================================================ 64: the sphere cracks
class S64(Shot):
    t0, t1 = 1668 / 24, 1696 / 24

    def setup(self):
        D = self.t1 - self.t0
        self.cam = Cam(Ch(V(0, 2.0, -9.0)).key(D, V(0, 2.1, -8.6)), Ch(V(0, 4.0, 0)), fov=50, roll=-4)
        # crack tree: (start time, a, b) in screen space
        self.cracks = []
        rnd = lambda *k: hash01(64, *k)
        def grow(x, y, ang, L, t, depth, idx):
            if depth > 4 or L < 30:
                return
            n = 4
            pts = [(x, y)]
            cx, cy = x, y
            for j in range(n):
                a = ang + (rnd(idx, j) - 0.5) * 0.9
                cx += math.cos(a) * L / n
                cy += math.sin(a) * L / n
                pts.append((cx, cy))
            self.cracks.append((t, pts, 6 - depth))
            for b in range(2):
                grow(cx, cy, ang + (rnd(idx, 9, b) - 0.5) * 1.6, L * 0.62, t + 0.08 + 0.05 * rnd(idx, 7, b), depth + 1, idx * 3 + b + 1)
        grow(W * 0.45, H * 0.18, math.radians(110), 260, 4 / 24, 0, 1)
        grow(W * 0.55, H * 0.2, math.radians(60), 300, 10 / 24, 1, 50)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # buildings behind, the dome filling the lower frame
        for i in range(8):
            x0 = i * 260 - 80
            fr.b.drawRect(skia.Rect(x0, 0, x0 + 150, H), paint(d3.FILL, 0.9))
            fr.b.drawRect(skia.Rect(x0, 0, x0 + 150, H), paint(d3.PENCIL, 0.6, stroke=2))
        cx, cy, R = W * 0.5, H * 1.35, W * 0.78
        fr.b.drawCircle(cx, cy, R, paint(INK))
        for (t_on, pts, wd) in self.cracks:
            a = s - t_on
            if a <= 0:
                continue
            u = min(1.0, a / 0.12)
            k = max(2, int(len(pts) * u))
            sub = pts[:k]
            if len(sub) >= 2:
                fr.b.drawPath(poly_path(sub), paint(PAPER, 1.0, stroke=wd))
                fr.g.drawPath(poly_path(sub), paint((1, 1, 1), 0.3, stroke=wd * 3, add=True, blur=wd))


# ============================================================================ 65: the shell falls away
class S65(Shot):
    t0, t1 = 1696 / 24, 1707 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk65'))
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo65'))
        stand(k, 0, 0.8, -1.0, 0.1, width=0.18)
        k.k(0, hand_l=V(0.0, 0.2, 0.25), hand_r=V(-0.05, 0.22, 0.25), hshape_l=shape('flat'), hshape_r=shape('flat'), eye_glow=1.2)
        stand(g, 0, -1.5, 6.0, math.pi + 0.2, width=0.2, h=0.15)
        g.k(0, lean=0.4, eye_glow=1.3, hand_l=V(-0.15, -0.3, 0.2), hand_r=V(0.15, -0.3, 0.2)).k(D, lean=0.45)
        self.cam = Cam(Ch(V(1.6, 1.5, -2.6)).key(5 / 24, V(1.0, 1.4, -2.0), 'io').key(D, V(-0.6, 1.3, 2.0), 'in'),
                       Ch(V(-0.5, 1.2, 4.0)).key(D, V(-1.5, 1.2, 6.0)), fov=50, roll=Ch(0).key(D, -12, 'in'))
        self.blds = [Building(-12, -4, 9, 16, 30, seed=651, style='vstrips'), Building(3, 12, 9, 16, 26, seed=652, style='vstrips')]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=200)
        d3.line3(fr, cs, V(-10, 0, 8), V(10, 0, 8), w_m=0.03)
        draw_actors(fr, self.cam, s, s, [self.g, self.k])
        # the ink shell recedes from the edges
        u = smoothstep(0.0, 6 / 24, s)
        if u < 1:
            p = skia.Path()
            p.addRect(skia.Rect(-10, -10, W + 10, H + 10))
            p.addOval(skia.Rect(W / 2 - W * 1.2 * u, H / 2 - H * 1.2 * u, W / 2 + W * 1.2 * u, H / 2 + H * 1.2 * u))
            p.setFillType(skia.PathFillType.kEvenOdd)
            fr.b.drawPath(p, paint(INK))
        set_blur(fr, self.cam, s, k=0.5, thresh=15)


# ============================================================================ 66: the cut on his neck
class S66(Shot):
    t0, t1 = 1707 / 24, 1772 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo66'))
        stand(g, 0, 0, 0, math.pi - 0.45)
        g.k(0, hroll=0.25, hpitch=0.1, hyaw=0.1, eye_glow=1.2, eye_open=0.95, idle=0.5)
        g.k(0.5, eye_open=1.15, hroll=0.28)
        g.k(D, hroll=0.3, hpitch=0.12, hyaw=0.14, eye_open=1.1)
        J = g.fig.pose(0.5)
        self.H = J['H']
        self.N = J['N']
        self.cam = Cam(Ch(self.H + V(0.25, -0.18, -0.75)).key(D, self.H + V(0.22, -0.17, -0.68)), Ch(self.H + V(-0.05, -0.12, 0)), fov=46)
        self.drops = [(hash01(66, i), hash01(67, i), hash01(68, i)) for i in range(26)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        if s < 3 / 24:
            # white slash flash across a dark frame
            paper(fr, INK)
            u = s / (3 / 24)
            fr.b.drawLine(-100, H * 0.1, W + 100, H * 0.95, paint((1, 1, 1), 1.0, stroke=120 * (1 - u) + 20))
            fr.g.drawLine(-100, H * 0.1, W + 100, H * 0.95, paint((0.9, 0.95, 1.0), 0.6, stroke=260, add=True, blur=60))
            return
        paper(fr)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        # the cut: a thin red line across the neck, blood spraying back along it
        a = cs.proj(J['N'] + V(0.25, 0.08, -0.05))
        b = cs.proj(J['N'] + V(-0.18, -0.06, -0.05))
        R_ = fx.PAL['red']
        fr.b.drawLine(a[0], a[1], b[0], b[1], paint((0.85, 0.05, 0.1), 1.0, stroke=6))
        age = s - 3 / 24
        for i, (u, v, w) in enumerate(self.drops):
            t = u
            px = a[0] + (b[0] - a[0]) * t
            py = a[1] + (b[1] - a[1]) * t
            d = (60 + 300 * v) * (1 - math.exp(-age * 4))
            ang = math.radians(200 + 30 * (w - 0.5))
            x, y = px + math.cos(ang) * d, py + math.sin(ang) * d + 40 * age * age * w
            rr = 3 + 9 * w * (1 - 0.3 * min(1, age))
            vx, vy = math.cos(ang), math.sin(ang)
            fr.b.drawCircle(x, y, rr, paint((0.8, 0.04, 0.09), 0.95))
            fr.b.drawLine(x, y, x - vx * rr * 3.5, y - vy * rr * 3.5, paint((0.8, 0.04, 0.09), 0.9, stroke=rr * 1.1))


# ============================================================================ 67: he touches the cut, it heals
class S67(Shot):
    t0, t1 = 1772 / 24, 1781 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo67'))
        stand(g, 0, 0, 0, math.pi)
        g.k(0, hand_r=V(-0.02, 0.10, 0.12), elbow_r=V(0.8, -0.5, 0.1), hshape_r=shape('relax'), hand_l=V(-0.1, -0.3, 0.2),
            eye_glow=1.4, eye_open=1.15, hpitch=0.05)
        g.k(D, hand_r=V(0.0, 0.12, 0.10), hshape_r=shape('open'))
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.0, -0.2, -0.0)).key(1 / 24, H + V(0.05, -0.25, -0.95), 'out').key(D, H + V(0.05, -0.25, -0.9)),
                       Ch(H + V(0, -0.15, 0)), fov=46)
        self.blds = [Building(-12, -3, 6, 14, 30, seed=671, style='vstrips'), Building(3, 12, 6, 14, 26, seed=672, style='vstrips')]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.blds, fog_dist=200)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        mouth(fr, cs, J, self.g.fig, 1.0, smile=0.8, width=0.45)
        q = cs.proj(J['Wr'])
        for i in range(18):
            ang = hash01(670, i) * 6.28
            r = (20 + 120 * hash01(671, i)) * min(1.0, s * 8)
            fr.g.drawCircle(q[0] + math.cos(ang) * r, q[1] + math.sin(ang) * r * 0.6 - 30 * s,
                            2 + 3 * hash01(672, i), paint(fx.PAL['cyan']['mid'], 0.9, add=True))
        fx.light_wash(fr, q[0], q[1], 160, fx.PAL['cyan']['glow'], 0.45, layer='g')
        if s < 1 / 24:
            fr.post.append(fx.whip_blur(200, 40))


# ============================================================================ 68 / 70: red-black shrine inserts
class ShrineInsert(Shot):
    roll = 0.0

    def setup(self):
        D = self.t1 - self.t0
        self.cam = Cam(Ch(V(-3, 3, -14)).key(D, V(3, 3.5, -12)), Ch(V(0, 6, 0)), fov=60, roll=Ch(self.roll).key(D, self.roll + 6))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr, (0.86, 0.04, 0.08))
        shrine(fr, cs, V(0, 0, 0), 1.0, fill=INK, edge=INK)
        for i in range(10):
            a = hash01(68, i) * math.pi
            x = W * hash01(69, i)
            fr.b.drawLine(x - math.cos(a) * 900, H / 2 - math.sin(a) * 900, x + math.cos(a) * 900, H / 2 + math.sin(a) * 900,
                          paint(INK, 1.0, stroke=6 + 20 * hash01(70, i)))
        d3.letterbox(fr, 0.08)


class S68(ShrineInsert):
    t0, t1 = 1781 / 24, 1794 / 24
    roll = -10.0


class S70(ShrineInsert):
    t0, t1 = 1845 / 24, 1865 / 24
    roll = 12.0


# ============================================================================ 69: Sukuna's smile behind his hands
class S69(Shot):
    t0, t1 = 1794 / 24, 1845 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk69'))
        stand(k, 0, 0, 0, math.pi + 0.9)
        k.k(0, hand_l=V(0.045, 0.16, 0.26), hand_r=V(-0.045, 0.16, 0.26), hshape_l=shape('flat'), hshape_r=shape('flat'),
            hup_l=V(0, 1, 0.1), hup_r=V(0, 1, 0.1), hback_l=V(-1, 0, 0), hback_r=V(1, 0, 0), eye_glow=1.5, eye_fire=0.9, hpitch=0.1,
            elbow_l=V(-0.6, -0.8, 0), elbow_r=V(0.6, -0.8, 0))
        k.k(D, hpitch=0.05, hyaw=-0.1, hand_l=V(0.045, 0.18, 0.26), hand_r=V(-0.045, 0.18, 0.26))
        self.smile = Ch(0.6).key(D, 1.0)
        H = k.fig.pose(0)['H']
        F = k.fig.pose(0)['Rp'] @ V(0, 0, 1)
        Rr = k.fig.pose(0)['Rp'] @ V(1, 0, 0)
        self.cam = Cam(Ch(H + F * 0.75 + Rr * 0.3 + V(0, -0.12, 0)).key(D, H + F * 0.68 + Rr * 0.28 + V(0, -0.12, 0)),
                       Ch(H + F * 0.1 + V(0, -0.12, 0)), fov=48)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr, (1.0, 1.0, 1.0))
        for i in range(9):
            y = H * (0.05 + 0.1 * i) + 30 * math.sin(s * 2 + i)
            fr.b.drawLine(-50, y + 150, W * (0.35 + 0.2 * hash01(69, i)), y - 120, paint((0.85, 0.08, 0.14), 0.95, stroke=30 + 40 * hash01(70, i)))
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.9)
        mouth(fr, cs, J, self.k.fig, 1.0, smile=float(self.smile(s)), width=0.55)
        d3.letterbox(fr, 0.08)


# ============================================================================ 71: one eye in the red and black
class S71(Shot):
    t0, t1 = 1865 / 24, 1924 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo71'))
        stand(g, 0, 0, 0, math.pi - 0.25)
        g.k(0, eye_glow=1.6, eye_open=1.1, eye_l=0.0, hroll=-0.2, idle=0.4)
        g.k(D, hroll=-0.22)
        H = g.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(0.05, 0.0, -0.55)).key(D - 4 / 24, H + V(0.05, 0.0, -0.5)).key(D, H + V(0.08, 0.02, -0.18), 'in'),
                       Ch(H + V(0.08, 0.02, 0)), fov=44, roll=-10)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr, (1.0, 1.0, 1.0))
        fr.b.drawRect(skia.Rect(0, 0, W * 0.62, H), paint((0.82, 0.06, 0.12)))
        for i in range(7):
            x = W * (0.05 + 0.09 * i)
            fr.b.drawLine(x, -20, x + 120 * hash01(71, i), H + 20, paint(INK, 1.0, stroke=40 + 50 * hash01(72, i)))
        draw_actors(fr, self.cam, s, s, [self.g])
        d3.letterbox(fr, 0.08)
        if s > D - 3 / 24:
            u = (s - (D - 3 / 24)) / (3 / 24)
            fr.post.append(lambda img, u=u: img * (1 - 0.7 * u) + np.array(fx.PAL['cyan']['mid'], np.float32) * 0.7 * u)


SHOTS = [S62, S63, S64, S65, S66, S67, S68, S69, S70, S71]
SEGMENTS = [(S62.t0, S71.t1)]
