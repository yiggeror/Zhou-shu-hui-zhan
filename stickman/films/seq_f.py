"""Sequence F: shots 50-61 (frames 1357-1560): Gojo's control, the flung building, Sukuna's
slashes, the signs."""
from films.common import *
from engine.env import Building, draw_buildings
from films.seq_b import city_ring

CY = fx.PAL['cyan']


def cyan_edges(fr, cs, b, k=1.0):
    """glowing outline on a building's edges (Gojo's control)"""
    x0, x1, z0, z1 = b.b
    y0, y1 = b.base, b.base + b.h
    corners = [V(x0, y0, z0), V(x1, y0, z0), V(x1, y0, z1), V(x0, y0, z1), V(x0, y1, z0), V(x1, y1, z0), V(x1, y1, z1), V(x0, y1, z1)]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    for a, c in edges:
        d3.line3(fr, cs, corners[a], corners[c], color=CY['glow'], w_m=0.9, alpha=0.35 * k, layer='g')
        d3.line3(fr, cs, corners[a], corners[c], color=CY['mid'], w_m=0.3, alpha=0.9 * k, layer='g')


class Moved(Building):
    """a building that can be carried: drawn through a moving transform"""


def moving_box(fr, cs, center, size, R, fill=None, edge=None, glow=0.0):
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    faces = [((0, 0, -1), [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)]),
             ((0, 0, 1), [(-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1)]),
             ((-1, 0, 0), [(-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)]),
             ((1, 0, 0), [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)]),
             ((0, -1, 0), [(-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)]),
             ((0, 1, 0), [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)])]
    S = np.array([hx, hy, hz])
    for n, q in faces:
        nw = R @ np.array(n, float)
        pts = [center + R @ (np.array(v, float) * S) for v in q]
        if np.dot(nw, cs.pos - pts[0]) <= 0:
            continue
        d3.poly3(fr, cs, pts, fill=fill or d3.FILL, edge=edge or d3.PENCIL, w_m=0.08)
        # window rows
        if abs(n[1]) < 0.5:
            for j in range(1, 9):
                y = -1 + 2 * j / 9
                a = center + R @ (np.array([q[0][0], y, q[0][2]], float) * S)
                b = center + R @ (np.array([q[1][0], y, q[1][2]], float) * S)
                d3.line3(fr, cs, a, b, w_m=0.05, alpha=0.6)
        if glow > 0:
            P = [cs.proj(p) for p in pts]
            path = poly_path([p[:2] for p in P], closed=True)
            fr.g.drawPath(path, paint(CY['glow'], 0.4 * glow, stroke=26, add=True, blur=12))
            fr.g.drawPath(path, paint(CY['mid'], 0.9 * glow, stroke=6, add=True))


# ============================================================================ 50: Gojo's beckoning sweep
class S50(Shot):
    t0, t1 = 1357 / 24, 1367 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo50'))
        stand(g, 0, 0, 0, math.pi - 0.3)
        g.k(0, hand_r=V(-0.02, 0.30, 0.12), elbow_r=V(0.6, 0.3, -0.6), hshape_r=shape('two'), hroll_r=-0.5,
            hand_l=V(-0.05, -0.4, 0.15), eye_glow=1.3, hpitch=0.0, hyaw=0.1)
        g.k(0.12, hand_r=V(0.00, 0.31, 0.14))
        g.k(0.26, 'outexp', hand_r=V(0.55, 0.12, 0.25), hshape_r=shape('open'), twist=-0.25, hyaw=0.0, lean=0.05)
        g.k(D, hand_r=V(0.60, 0.10, 0.20), twist=-0.3)
        g.follow(['hand_r', 'hyaw'], 0, D, f=3.5, z=0.5, r=1.6)
        self.flame = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.05, rise=0.3, trail=0.9, life=0.22, seed=50,
                              amount=Ch(0.0).key(0.12, 0.0).key(0.2, 1.0))
        H = g.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.45, -0.35, -1.05)).key(D, H + V(0.4, -0.33, -0.98)), Ch(H + V(0.15, -0.25, 0)), fov=48)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fx.light_wash(fr, 0, H * 0.3, 600, (0.9, 0.35, 0.35), 0.25)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.render_flames(fr, cs, [self.flame], s)
        mouth(fr, cs, J, self.g.fig, 1.0, smile=0.7, width=0.45)
        if s < 1.5 / 24:
            fr.post.append(fx.whip_blur(180 * (1 - s / (1.5 / 24)), 30))


# ============================================================================ 51: Sukuna's eyes widen
class S51(Shot):
    t0, t1 = 1367 / 24, 1373 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk51'))
        stand(k, 0, 0, 0, math.pi + 0.7)
        k.k(0, eye_open=0.75, eye_glow=1.3, hpitch=0.05).k(0.1, 'out', eye_open=1.15, hpitch=-0.05).k(D, eye_open=1.2, eye_glow=1.5)
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(-0.2, 0.0, -0.62)).key(D, H + V(-0.2, 0.0, -0.55)), Ch(H + V(0.05, 0.02, 0)), fov=40, roll=-8)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.6)
        D = self.t1 - self.t0
        if s > D - 1.5 / 24:
            fr.post.append(fx.whip_blur(0, 140))


# ============================================================================ 52: lifted and caught in the vortex
class S52(Shot):
    t0, t1 = 1373 / 24, 1392 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk52'))
        # floating, limbs flailing slowly, being pulled up and turned
        k.k(0, yaw=0.3, root=V(0, 6.0, 0), lean=-0.2, foot_l=V(-0.2, 5.25, 0.2), foot_r=V(0.25, 5.35, -0.15),
            knee_l=V(0, 0.4, 1), knee_r=V(0, 0.3, 1), hand_l=V(-0.45, 0.15, 0.1), hand_r=V(0.45, 0.05, 0.15),
            elbow_l=V(-0.6, 0.6, -0.2), elbow_r=V(0.6, 0.6, -0.2), eye_glow=1.2, hshape_l=shape('claw'), hshape_r=shape('claw'))
        k.k(0.25, root=V(0.0, 6.25, 0), foot_l=V(-0.25, 5.65, 0.3), foot_r=V(0.3, 5.5, -0.2), hand_l=V(-0.5, 0.25, 0.0), lean=-0.3)
        k.k(0.5, root=V(0.05, 6.45, 0), yaw=0.8, foot_l=V(-0.2, 5.8, 0.1), foot_r=V(0.2, 5.75, 0.25), hand_r=V(0.4, 0.3, 0.1), lean=0.1)
        k.k(D, root=V(0.1, 6.8, 0), yaw=1.3, foot_l=V(-0.1, 6.1, 0.2), foot_r=V(0.3, 6.0, 0.0), hand_l=V(-0.45, 0.35, 0.1), lean=-0.15)
        k.follow(['hand_l', 'hand_r', 'foot_l', 'foot_r'], 0, D, f=2.5, z=0.5, r=1.2)
        self.left = Building(-9, -2.5, -4, 6, 60, base=-50, seed=521, style='grid', win_density=0.6)
        self.right = Building(2.5, 10, -4, 6, 60, base=-50, seed=522, style='grid', win_density=0.6)
        self.cam = Cam(Ch(V(0.5, 4.2, -6.5)).key(D, V(0.3, 4.6, -5.6)), Ch(V(0, 6.3, 0)).key(D, V(0, 6.7, 0)), fov=50)
        self.vortex = (16 / 24 - 9 / 24, 15 / 24)   # 1382-1388 in shot time

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        if s < 1 / 24:
            # the red glint before the shot opens
            fr.g.drawCircle(W / 2, H / 2, 14, paint(fx.PAL['red']['core'], 1.0, add=True))
            fr.g.drawCircle(W / 2, H / 2, 60, paint(fx.PAL['red']['glow'], 0.7, add=True, blur=25))
            return
        draw_buildings(fr, cs, [self.left, self.right], fog_dist=200)
        draw_actors(fr, self.cam, s, s, [self.k])
        v0, v1 = 9 / 24, 15 / 24
        if s > v0:
            u = min(1.0, (s - v0) / (v1 - v0))
            fade = 1.0 if s < 15 / 24 else max(0.0, 1 - (s - 15 / 24) / (3 / 24))
            J = self.k.fig.pose(s)
            c = cs.proj(J['C'])
            R = (420 - 120 * u) * fade
            for i in range(22):
                a0 = hash01(52, i) * 6.28 + s * (7 + 3 * hash01(53, i))
                rr = R * (0.6 + 0.6 * hash01(54, i))
                pts = [(c[0] + math.cos(a0 + j * 0.12) * rr, c[1] + math.sin(a0 + j * 0.12) * rr * 0.8) for j in range(10)]
                fr.g.drawPath(poly_path(pts), paint(CY['mid'], 0.95 * fade * u, stroke=6 + 10 * hash01(55, i), add=True))
                fr.g.drawPath(poly_path(pts), paint(CY['glow'], 0.4 * fade * u, stroke=24, add=True, blur=10))
            fr.g.drawCircle(c[0], c[1], R * 0.9, paint(CY['glow'], 0.35 * fade * u, add=True, blur=R * 0.3))


# ============================================================================ 53: Gojo lifts a building
class S53(Shot):
    t0, t1 = 1392 / 24, 1401 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo53'))
        g.k(0, yaw=0.6, root=V(0, 40, 0), lean=0.25, foot_l=V(-0.15, 39.15, 0.1), foot_r=V(0.2, 39.25, -0.15),
            knee_l=V(0, 0.2, 1), hand_r=V(0.05, 0.40, 0.15), elbow_r=V(0.8, 0.3, -0.4), hshape_r=shape('open'),
            hand_l=V(-0.2, -0.3, 0.1), hpitch=-0.35, eye_glow=1.3)
        g.k(D, hand_r=V(0.04, 0.55, 0.08), hpitch=-0.45, root=V(0, 40.15, 0))
        self.bpos = Ch(V(-6, 32, 18)).key(D, V(-6, 36, 18))
        self.cam = Cam(Ch(V(1.3, 41.3, -1.5)).key(D, V(1.15, 41.4, -1.35)), Ch(V(-1.8, 38.5, 6)), fov=58, roll=-10)
        self.city = city_ring(53, y_top=0, r0=30, r1=110, base=-60)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=200)
        R = d3.rot3(0.4, 0.15 * s, 0.1)
        moving_box(fr, cs, self.bpos(s), (8, 20, 8), R, glow=1.0)
        draw_actors(fr, self.cam, s, s, [self.g])
        J = self.g.fig.pose(s)
        q = cs.proj(J['Wr'])
        fx.light_wash(fr, q[0], q[1], 120, CY['glow'], 0.6, layer='g')
        d3.line3(fr, cs, J['Wr'], J['Wr'] + V(0, 1.5, 0), color=CY['mid'], w_m=0.08, alpha=0.8, layer='g')


# ============================================================================ 54: the throw
class S54(Shot):
    t0, t1 = 1401 / 24, 1411 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo54'))
        g.k(0, yaw=math.pi / 2, root=V(0, 1.0, 0), lean=0.9, foot_l=V(-0.6, 0.55, 0.1), foot_r=V(-0.75, 0.75, -0.1),
            hand_r=V(0.10, 0.45, -0.25), elbow_r=V(0.6, 0.6, -0.6), hshape_r=shape('open'), hand_l=V(-0.1, -0.2, 0.3),
            hpitch=-0.6, eye_glow=1.4, eye_fire=0.4)
        g.k(0.12, hand_r=V(0.12, 0.48, -0.3))
        g.k(0.30, 'outexp', hand_r=V(-0.05, 0.05, 0.60), hshape_r=shape('claw'), twist=-0.5, lean=1.0, hpitch=-0.75)
        g.k(D, hand_r=V(-0.10, -0.05, 0.62), twist=-0.6)
        g.follow(['hand_r'], 0, D, f=3.5, z=0.5, r=1.6)
        self.smile = 0.9
        H = g.fig.pose(0.2)['H']
        self.cam = Cam(Ch(H + V(0.9, -0.15, -0.8)).key(D, H + V(0.85, -0.12, -0.7)), Ch(H + V(0.2, -0.2, 0)), fov=52)
        self.city = city_ring(54, y_top=-30, r0=30)
        self.flame = fx.Flame(lambda t: g.fig.pose(t)['Wr'], 'cyan', size=0.05, rise=0.2, trail=0.9, life=0.2, seed=54)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=200)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.render_flames(fr, cs, [self.flame], s)
        mouth(fr, cs, J, self.g.fig, 1.0, smile=0.9, width=0.5)
        if s < 2 / 24:
            fr.post.append(fx.whip_blur(160 * (1 - s / (2 / 24)), 0))


# ============================================================================ 55: the building falls, Sukuna leaps off
class S55(Shot):
    t0, t1 = 1411 / 24, 1436 / 24

    def setup(self):
        D = self.t1 - self.t0
        # the tower tumbles toward the city; Sukuna is on its roof and jumps
        self.bc = Ch(V(0, 10, 30)).key(D, V(0, -8, 60), 'in')
        self.br = Ch(V(0.0, 0.0, 0.0)).key(D, V(0.5, 0.25, 0.0))
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk55'))
        jump = 13 / 24
        top0 = lambda t: self.top(t)
        k.k(0, yaw=0.0, root=V(0, 0, 0), eye_glow=1.2)
        self.jump = jump
        self.cam = Cam(Ch(V(-4, 18, -2)).key(D, V(-3, 10, 20)), Ch(V(0, 14, 30)).key(D, V(0, 2, 60)), fov=54)
        self.cam.shake(0, 6, D, 12)
        self.city = city_ring(55, y_top=-12, r0=50, r1=150)
        # Sukuna's path: crouch on the roof, leap up and forward, fall
        self.sk_keys = None

    def top(self, t):
        R = d3.rot3(0.0, float(self.br(t)[0]), float(self.br(t)[1]))
        return np.asarray(self.bc(t)) + R @ V(0, 15, 0), R

    def place_sukuna(self):
        k = self.k
        D = self.t1 - self.t0
        for i in range(26):
            t = D * i / 25
            p, R = self.top(t)
            up = R @ V(0, 1, 0)
            if t < self.jump:
                crouch = min(1.0, t / self.jump)
                base = p + up * 0.02
                k.k(t, root=base + up * (0.85 - 0.35 * crouch), lean=0.2 + 0.5 * crouch, foot_l=base + V(-0.18, 0, 0.1),
                    foot_r=base + V(0.18, 0, -0.1), hand_l=V(-0.15, -0.35, 0.2), hand_r=V(0.15, -0.35, 0.2))
            else:
                a = t - self.jump
                p0, _ = self.top(self.jump)
                pos = p0 + V(0, 0.85, 0) + V(0, 9.0 * a - 9.8 * a * a, 7.0 * a)
                k.k(t, root=pos, lean=0.4 - 0.4 * min(1.0, a * 3), foot_l=pos + V(-0.2, -0.55, -0.25), foot_r=pos + V(0.2, -0.7, 0.1),
                    hand_l=V(-0.45, 0.2, 0.0), hand_r=V(0.45, 0.25, 0.0))

    def draw(self, fr, s):
        if self.sk_keys is None:
            self.place_sukuna()
            self.sk_keys = True
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=220)
        c = self.bc(s)
        R = d3.rot3(0.0, float(self.br(s)[0]), float(self.br(s)[1]))
        moving_box(fr, cs, np.asarray(c), (10, 30, 10), R, glow=0.8)
        # pyramid roof
        top, _ = self.top(s)
        corners = [np.asarray(c) + R @ V(x, 15, z) for (x, z) in ((-5, -5), (5, -5), (5, 5), (-5, 5))]
        apex = np.asarray(c) + R @ V(0, 21, 0)
        for i in range(4):
            d3.poly3(fr, cs, [corners[i], corners[(i + 1) % 4], apex], fill=d3.FILL, edge=d3.PENCIL, w_m=0.08)
            d3.line3(fr, cs, corners[i], apex, color=CY['mid'], w_m=0.25, alpha=0.9, layer='g')
        draw_actors(fr, self.cam, s, s, [self.k])
        set_blur(fr, self.cam, s, k=0.5, thresh=12)


# ============================================================================ 56: Sukuna's sign in mid-air
class S56(Shot):
    t0, t1 = 1436 / 24, 1453 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk56'))
        k.k(0, yaw=math.pi, root=V(0, 20, 0), lean=0.45, foot_l=V(-0.25, 19.3, 0.35), foot_r=V(0.25, 19.15, -0.2),
            knee_l=V(0, 0.5, 1), hand_l=V(0.08, 0.0, 0.25), hand_r=V(-0.08, 0.02, 0.25), hshape_l=shape('point'),
            hshape_r=shape('point'), hroll_l=1.4, hroll_r=-1.4, eye_glow=1.4, eye_fire=0.5, hpitch=-0.15)
        k.k(0.35, 'io', hand_l=V(0.1, 0.12, 0.28), hand_r=V(-0.1, 0.13, 0.28), hpitch=-0.25, lean=0.5)
        k.k(D, root=V(0, 19.6, 0), hand_l=V(0.1, 0.13, 0.29), hpitch=-0.28, foot_l=V(-0.25, 18.9, 0.3), foot_r=V(0.25, 18.8, -0.2))
        self.shout = Ch(0.2).key(0.4, 1.0, 'out').key(D, 1.0)
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.0, -0.9, -2.0)).key(D, H + V(0.0, -0.9, -1.6)), Ch(H + V(0, -0.45, 0)).key(D, H + V(0, -0.65, 0)), fov=46)
        self.city = city_ring(56, y_top=0, r0=30)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=200)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.8)
        mouth(fr, cs, J, self.k.fig, 1.0, smile=-0.2, width=0.55, open_=float(self.shout(s)))


# ============================================================================ 57: the net of slashes
class S57(Shot):
    t0, t1 = 1453 / 24, 1478 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk57'))
        k.k(0, yaw=0.2, root=V(0, 0.55, 0), lean=0.35, foot_l=V(-0.3, 0, 0.3), foot_r=V(0.3, 0, -0.2),
            hand_l=V(0.1, 0.05, 0.25), hand_r=V(-0.1, 0.05, 0.25), eye_glow=1.2)
        k.k(D, root=V(0, 0.52, 0), lean=0.4)
        # the camera is torn sideways on the last frames as the cut building comes apart (into 57b)
        self.cam = Cam(Ch(V(0.3, 3.0, -2.0)).key(D, V(0.25, 2.8, -1.8)),
                       Ch(V(0, 0.7, 0.3)).key(D - 3 / 24, V(0.02, 0.69, 0.3)).key(D, V(-2.2, 0.5, 0.6), 'in'), fov=48, roll=Ch(-20).key(D, -24))
        self.slashes = []
        for i in range(12):
            t_on = 5 / 24 + 11 / 24 * (i / 11) ** 1.2
            ang = hash01(57, i) * math.pi
            off = (hash01(58, i) - 0.5) * 900
            self.slashes.append((t_on, ang, off, 10 + 34 * hash01(59, i)))

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        if s < 1 / 24:
            # sketch flash: ink scribbles on white
            paper(fr, (1.0, 1.0, 1.0))
            for i in range(9):
                pts = [(W * hash01(570, i, j), H * hash01(571, i, j)) for j in range(4)]
                fr.b.drawPath(smooth_path(pts), paint(INK, 0.9, stroke=6 + 6 * hash01(572, i)))
            return
        paper(fr)
        # tilted rooftop surface
        d3.poly3(fr, cs, [V(-3, 0, -3), V(3, 0, -3), V(3, 0, 4), V(-3, 0, 4)], fill=d3.FILL, edge=d3.PENCIL, w_m=0.02)
        for x in np.arange(-3, 3.1, 0.75):
            d3.line3(fr, cs, V(x, 0, -3), V(x, 0, 4), w_m=0.01, alpha=0.6)
        draw_actors(fr, self.cam, s, s, [self.k])
        # slashes: each cuts across the whole frame in a flash and lingers as a thin line
        for (t_on, ang, off, wd) in self.slashes:
            a = s - t_on
            if a < 0:
                continue
            ca, sa = math.cos(ang), math.sin(ang)
            nx, ny = -sa, ca
            cx, cy = W / 2 + nx * off, H / 2 + ny * off
            L = 2400
            k = max(0.0, 1 - a / (6 / 24))
            w = wd * (0.25 + 0.75 * k)
            p0, p1 = (cx - ca * L, cy - sa * L), (cx + ca * L, cy + sa * L)
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint(INK, 0.95, stroke=w * 1.6 + 6))
            fr.b.drawLine(p0[0], p0[1], p1[0], p1[1], paint((1.0, 1.0, 1.0), 1.0, stroke=w))
            if a < 2 / 24:
                fr.g.drawLine(p0[0], p0[1], p1[0], p1[1], paint((0.9, 0.95, 1.0), 0.8, stroke=w * 3, add=True, blur=w))
        if s > 17 / 24:
            u = min(1.0, (s - 17 / 24) / (6 / 24))
            fr.post.append(lambda img, u=u: img * (1 - 0.85 * u) + np.array(INK, np.float32) * 0.85 * u)
        cam_blur(fr, self.cam, s, k=0.6, thresh=25.0)


class S57b(Shot):
    """the cut building bursts into blocks around him (red light), then black"""
    t0, t1 = 1478 / 24, 1485 / 24

    def setup(self):
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk57b'))
        k.k(0, yaw=0.2, root=V(0, 0.52, 0), lean=0.4, foot_l=V(-0.3, 0, 0.3), foot_r=V(0.3, 0, -0.2), hand_l=V(0.1, 0.05, 0.25),
            hand_r=V(-0.1, 0.05, 0.25))
        self.cam = Cam(V(0.25, 1.4, -2.2), V(0, 0.9, 0.5), fov=55)
        self.blocks = [(V((hash01(5, i) - 0.5) * 2, (hash01(6, i) - 0.3) * 2, (hash01(7, i)) * 4), 0.12 + 0.25 * hash01(8, i)) for i in range(70)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        if s > 5 / 24:
            paper(fr, INK)
            return
        paper(fr)
        fx.light_wash(fr, W * 0.5, H * 0.2, 900, (0.9, 0.35, 0.4), 0.45)
        for i, (p, sz) in enumerate(self.blocks):
            v = norm(p - V(0, 0.9, 0)) * (3.0 + 2 * hash01(9, i))
            pos = V(0, 0.9, 0) + p * 0.9 + v * s
            d3.cube(fr, cs, pos, sz, d3.rot3(s * 3 + i, s * 2 + i * 0.3, i), fill=INK)
        draw_actors(fr, self.cam, s, s, [self.k])
        if s > 3 / 24:
            u = (s - 3 / 24) / (2 / 24)
            wipe_diag(fr, min(1.0, u), ang=0.0)


# ============================================================================ 58: Gojo floating among the blocks
class S58(Shot):
    t0, t1 = 1485 / 24, 1502 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo58'))
        g.k(0, yaw=math.pi - 0.4, root=V(0, 30, 0), lean=0.1, foot_l=V(-0.15, 29.2, 0.1), foot_r=V(0.15, 29.3, -0.05),
            knee_l=V(0, 0.3, 1), hand_l=V(-0.1, -0.4, 0.1), hand_r=V(0.1, -0.35, 0.15), eye_glow=1.3, hpitch=0.1)
        g.k(D, yaw=math.pi - 0.15, root=V(0.1, 30.2, 0), hpitch=0.05, hyaw=0.2, foot_r=V(0.2, 29.45, 0.05))
        g.follow(['foot_l', 'foot_r', 'hyaw'], 0, D, f=1.5, z=0.6, r=1.0)
        self.cam = Cam(Ch(V(-2.0, 29.0, -9.0)).key(D, V(-1.4, 29.2, -8.0)), Ch(V(0.2, 30.0, 0)), fov=40)
        self.city = []
        for i in range(14):
            x = (hash01(58, i) - 0.5) * 50
            z = 10 + 50 * hash01(59, i)
            w = 4 + 5 * hash01(60, i)
            self.city.append(Building(x - w / 2, x + w / 2, z, z + w, 60 + 30 * hash01(61, i), base=-40, seed=580 + i,
                                      style='vstrips', win_density=0.6))
        self.blocks = [(V((hash01(62, i) - 0.5) * 16, 24 + 12 * hash01(63, i), 3 + 20 * hash01(64, i)), 0.3 + 0.9 * hash01(65, i)) for i in range(16)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fx.light_wash(fr, W * 0.2, 0, 900, (0.9, 0.45, 0.5), 0.3)
        draw_buildings(fr, cs, self.city, fog_dist=200)
        for i, (p, sz) in enumerate(self.blocks):
            pos = p + V(0.2 * math.sin(s + i), -0.6 * s, 0)
            d3.cube(fr, cs, pos, sz, d3.rot3(s * 0.8 + i, s * 0.5 + i, i * 0.7), fill=INK)
        draw_actors(fr, self.cam, s, s, [self.g])


# ============================================================================ 59: Gojo flies in, two-finger sign
class S59(Shot):
    t0, t1 = 1502 / 24, 1521 / 24

    def setup(self):
        D = self.t1 - self.t0
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo59'))
        g.k(0, yaw=math.pi, root=V(0.4, 1.0, 3.0), lean=0.6, foot_l=V(0.25, 0.4, 3.6), foot_r=V(0.6, 0.5, 3.5),
            hand_r=V(-0.05, -0.2, 0.25), hshape_r=shape('relax'), eye_glow=1.3, hpitch=-0.2)
        g.k(0.15, 'out', root=V(0.05, 1.0, 0.25), lean=0.15, foot_l=V(-0.1, 0.1, 0.4), foot_r=V(0.2, 0.15, 0.3))
        g.k(0.25, hand_r=V(-0.06, -0.15, 0.25))
        g.k(0.45, 'io', hand_r=V(-0.07, 0.18, 0.20), hshape_r=shape('two'), hroll_r=-0.4, hpitch=0.05, root=V(0, 1.0, 0.2))
        g.k(D, hand_r=V(-0.07, 0.20, 0.21), root=V(0, 1.0, 0.18), eye_glow=1.7, eye_fire=0.6)
        g.follow(['hand_r', 'hpitch'], 0, D, f=3.0, z=0.55, r=1.4)
        self.cam = Cam(Ch(V(0.35, 1.85, -1.0)).key(D, V(0.3, 1.85, -0.9)), Ch(V(0.0, 1.72, 0.2)), fov=46, roll=-6)
        self.city = city_ring(59, y_top=-3)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_buildings(fr, cs, self.city, fog_dist=200)
        J = self.g.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.g])
        if s > 0.25:
            mouth(fr, cs, J, self.g.fig, 1.0, smile=0.6, width=0.4)
        if 0.38 < s < 0.62:
            u = (s - 0.38) / 0.24
            y = H * 0.12
            fr.g.drawRect(skia.Rect(-10, y - 30, W * u, y + 30), paint(CY['glow'], 0.35 * (1 - u), add=True, blur=20))


# ============================================================================ 60: Sukuna's hand sign
class S60(Shot):
    t0, t1 = 1521 / 24, 1540 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk60'))
        stand(k, 0, 0, 0, math.pi + 0.6)
        k.k(0, hand_l=V(0.045, 0.08, 0.30), hand_r=V(-0.045, 0.08, 0.30), hshape_l=shape('flat'), hshape_r=shape('flat'),
            hup_l=V(0, 1, 0.15), hup_r=V(0, 1, 0.15), hback_l=V(-1, 0, 0), hback_r=V(1, 0, 0),
            hpitch=0.45, eye_glow=1.3, eye_fire=0.5, hyaw=-0.3)
        k.k(0.4, 'io', hand_l=V(0.045, 0.12, 0.31), hand_r=V(-0.045, 0.12, 0.31), hpitch=0.38)
        k.k(D, hand_l=V(0.045, 0.13, 0.31), hand_r=V(-0.045, 0.13, 0.31), hpitch=0.35, hyaw=-0.25, eye_glow=1.5)
        H = k.fig.pose(0)['H']
        self.cam = Cam(Ch(H + V(0.55, -0.15, -0.6)).key(D, H + V(0.5, -0.15, -0.52)), Ch(H + V(0.15, -0.2, 0)), fov=44)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        fx.light_wash(fr, W, H * 0.4, 800, (0.9, 0.35, 0.35), 0.15 + 0.25 * s)
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        face_marks(fr, cs, J, self.k.fig, 0.8)
        mouth(fr, cs, J, self.k.fig, 1.0, smile=0.7, width=0.5)


# ============================================================================ 61: the sign, ink floods the background
class S61(Shot):
    t0, t1 = 1540 / 24, 1560 / 24

    def setup(self):
        D = self.t1 - self.t0
        k = self.k = Actor(Figure(SUKUNA, 1.0, 'suk61'))
        stand(k, 0, 0, 0, math.pi + 0.3)
        k.k(0, hand_l=V(0.045, 0.06, 0.30), hand_r=V(-0.045, 0.06, 0.30), hshape_l=shape('flat'), hshape_r=shape('flat'),
            hup_l=V(0, 1, 0.15), hup_r=V(0, 1, 0.15), hback_l=V(-1, 0, 0), hback_r=V(1, 0, 0), hpitch=-0.15, eye_glow=1.5, eye_fire=0.8)
        k.k(D, hpitch=-0.2, hand_l=V(0.045, 0.10, 0.31), hand_r=V(-0.045, 0.10, 0.31))
        H = k.fig.pose(0)['H']
        self.H = H
        self.cam = Cam(Ch(H + V(0.0, 0.0, -0.4)).key(2 / 24, H + V(0.15, -0.55, -0.9), 'out').key(D, H + V(0.14, -0.6, -0.85)),
                       Ch(H + V(0.05, 0, 0)).key(2 / 24, H + V(0.0, -0.15, 0), 'out'), fov=48)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        D = self.t1 - self.t0
        paper(fr)
        fx.light_wash(fr, W * 0.8, H * 0.2, 900, (0.9, 0.35, 0.35), 0.3)
        # ink spreading in from the left behind him
        u = smoothstep(10 / 24, 18 / 24, s)
        ink = None
        if u > 0:
            R = 200 + 2200 * u
            ink = skia.Path()
            for i in range(9):
                cx = -200 + 300 * hash01(61, i)
                cy = H * hash01(62, i)
                ink.addCircle(cx, cy, R * (0.6 + 0.4 * hash01(63, i)))
            fr.b.drawPath(ink, paint(INK, 1.0))
        J = self.k.fig.pose(s)
        draw_actors(fr, self.cam, s, s, [self.k])
        if ink is not None:
            fr.b.save()
            fr.b.clipPath(ink, skia.ClipOp.kIntersect, True)
            draw_actors(fr, self.cam, s, s, [self.k], silhouette=PAPER, eyes=False, smear=0)
            fr.b.restore()
        face_marks(fr, cs, J, self.k.fig, 0.9)
        mouth(fr, cs, J, self.k.fig, 1.0, smile=0.9, width=0.5)
        if s < 2 / 24:
            fr.post.append(fx.whip_blur(0, 160 * (1 - s / (2 / 24))))


SHOTS = [S50, S51, S52, S53, S54, S55, S56, S57, S57b, S58, S59, S60, S61]
SEGMENTS = [(S50.t0, S61.t1)]
