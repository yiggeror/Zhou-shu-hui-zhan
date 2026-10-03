"""Shots 0-3 traced from the original (frames 73-148): fist at the lens (cyan), fist at the lens
(red), the top-down cross-counter, the title.  Poses are keyed in screen space from the
original frames (see engine/roto.py)."""
from films.common import *
from engine.roto import RotoActor, K, screen_cam, lift_pct, px

TITLE_FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'


def flame_on(actor, pal, size, seed, rise=0.45, life=0.24, trail=0.3, amount=1.0, side='r'):
    F = actor.fig
    return fx.Flame(lambda t: F.pose(t)['W' + side], pal, size=size, rise=rise, life=life,
                    src2=lambda t: F.pose(t)['E' + side], seg=(0.65, 1.0), seed=seed, trail=trail, amount=amount)


# ============================================================================ 0: cyan fist at the lens
class S0(Shot):
    """Gojo, seen from low in front: the right fist comes at the lens out of the dark and
    burns there; the left forearm points at us on the right, the head is cut by the top edge."""
    t0, t1 = 73 / 24, 91 / 24

    def setup(self):
        hide = ('legl', 'legr')
        keys = [
            K(73, H=(57, 3), r=9, pitch=12, yaw=-4, C=(59, 20), Sr=(46, 24), Sl=(71, 24), P=(63, 72), Er=(38, 99), Wr=(53, 86),
              El=(80, 80), Wl=(70, 76), hs_r='fist', hs_l='fist', palm_l='away', eye_glow=0.6, eye_open=0.8, hide=hide,
              z={'Wr': 2.4, 'Er': 1.2, 'P': 0.4, 'El': -0.3, 'Wl': -0.4}),
            K(74, Wr=(53, 81), Er=(33, 96), z={'Wr': 1.6, 'Er': 0.8, 'P': 0.4, 'El': -0.3, 'Wl': -0.4}),
            K(75, Wr=(54, 77), Er=(27, 92), El=(79, 75), Wl=(69, 72), z={'Wr': 0.8, 'Er': 0.3, 'P': 0.4, 'El': -0.3, 'Wl': -0.4}),
            K(77, Wr=(55, 72), Er=(22, 89), El=(77, 71), Wl=(67, 70), eye_glow=1.1, eye_open=1.0,
              z={'Wr': -0.75, 'Er': -0.45, 'Wl': -0.5, 'El': -0.45, 'P': 0.4}),
            K(80, H=(58, 4), Wr=(53, 72), Er=(19, 88), El=(76, 71), Wl=(66, 70)),
            K(83, Wr=(55, 72), Er=(18, 86), El=(78, 70), Wl=(67, 71)),
            K(86, H=(59, 4), Wr=(54, 73), Er=(17, 86), El=(79, 69), Wl=(67, 72)),
            K(89, H=(59, 5), Wr=(55, 72), Er=(18, 85), El=(80, 68), Wl=(68, 72)),
            K(91, H=(60, 5), Wr=(55, 71), Er=(18, 85)),
        ]
        self.g = RotoActor(GOJO, keys, self.t0, 'gojo_r0')
        self.cam = screen_cam()
        self.flames = [flame_on(self.g, 'cyan', 0.085, 3, rise=0.55, life=0.26, amount=Ch(0.35).key(1.5 / 24, 1.0, 'out'))]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.g])
        fx.render_flames(fr, cs, self.flames, s)


# ============================================================================ 1: red fist at the lens
class S1(Shot):
    """Sukuna: the burning right fist fills the middle of the frame, his forearm comes in from the
    lower right, the left arm is bent in at the left; his face is behind the fist and shows on
    its right as the fist drifts left."""
    t0, t1 = 91 / 24, 109 / 24

    def setup(self):
        hide = ('legl', 'legr')
        keys = [
            K(91, H=(60, 31), r=14, yaw=-12, pitch=4, C=(63, 62), P=(66, 100), Er=(76, 99), Wr=(52, 54), El=(26, 72), Wl=(37, 52),
              hs_r='fist', hs_l='fist', eye_glow=1.3, eye_fire=0.3, hide=hide, z={'Wr': -0.5, 'Er': -0.1, 'Wl': -0.25}),
            K(95, Wr=(51, 53), El=(27, 70), Wl=(37, 51), z={'Wr': -0.6, 'Er': -0.15, 'Wl': -0.25}),
            K(98, H=(61, 33), Wr=(49, 54), El=(29, 68), Wl=(38, 52)),
            K(101, H=(62, 35), Wr=(48, 55), El=(28, 66), Wl=(37, 52), eye_glow=1.5),
            K(104, H=(62, 36), Wr=(46, 56), El=(27, 65), Wl=(36, 52)),
            K(108, H=(63, 37), Wr=(46, 57), El=(26, 64), Wl=(35, 52), eye_fire=0.5),
            K(109, H=(63, 37), Wr=(46, 57)),
        ]
        self.k = RotoActor(SUKUNA, keys, self.t0, 'suk_r1')
        self.cam = screen_cam()
        self.flames = [flame_on(self.k, 'red', 0.052, 4, rise=0.22, life=0.26)]

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        draw_actors(fr, self.cam, s, s, [self.k])
        fx.render_flames(fr, cs, self.flames, s)


# ============================================================================ 2: top-down cross-counter
def _zoom(p, c, k):
    return (c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k)


class S2(Shot):
    """Straight down on the two of them: Gojo on the left, Sukuna on the right, heads almost
    touching; Gojo's burning right arm reaches down-left past Sukuna, Sukuna's burning right
    arm reaches up past Gojo's head; at the end the camera shoots up and they shrink."""
    t0, t1 = 109 / 24, 126 / 24

    def setup(self):
        # top view: heads tipped toward the lens (pitch -90), roll turns the face in the picture
        # from straight above the bodies are foreshortened to short stubs behind the heads; legs are under them
        g0 = dict(H=(40, 53), r=7.5, pitch=-90, roll=60, C=(36, 50), P=(29, 45), Sr=(37, 57), Sl=(33, 45), Er=(31, 70), Wr=(22, 88),
                  El=(29, 33), Wl=(36, 21), hs_r='fist', hs_l='fist', eye_glow=1.0, hide=('legl', 'legr'))
        s0 = dict(H=(59, 47), r=7.5, pitch=-90, roll=-115, C=(63, 50), P=(70, 52), Sr=(58, 42), Sl=(66, 57), Er=(53, 33), Wr=(61, 10),
                  El=(69, 71), Wl=(64, 87), hs_r='fist', hs_l='open', eye_glow=1.0, hide=('legl', 'legr'))
        g1 = dict(H=(39, 53), Er=(31, 72), Wr=(19, 92), Wl=(37, 19))
        s1 = dict(H=(59, 46), Er=(52, 30), Wr=(64, 5), Wl=(63, 89))
        c, k = (47, 48), 0.33
        pt = lambda v: isinstance(v, tuple) and len(v) == 2 and not isinstance(v[0], str)
        gz = {n: _zoom(v, c, k) for n, v in {**g0, **g1}.items() if pt(v)}
        sz = {n: _zoom(v, c, k) for n, v in {**s0, **s1}.items() if pt(v)}
        gk = [K(109, **{**g0, 'H': (34, 55), 'Wr': (20, 88)}), K(111.5, **g0), K(114, H=(40, 53), Wr=(25, 86)),
              K(118, H=(39, 53), Er=(32, 69), Wr=(24, 87)), K(122.5, **g1), K(123.5, **g1), K(125.5, **gz, r=6.5 * k)]
        sk = [K(109, **{**s0, 'H': (64, 46), 'Wr': (66, 14)}), K(111.5, **s0), K(114, H=(59, 47), Wr=(61, 11)),
              K(118, H=(59, 46), Er=(51, 32), Wr=(61, 10)), K(122.5, **s1), K(123.5, **s1), K(125.5, **sz, r=6.5 * k)]
        self.g = RotoActor(GOJO, gk, self.t0, 'gojo_r2')
        self.s = RotoActor(SUKUNA, sk, self.t0, 'suk_r2')
        self.cam = screen_cam()
        G, Sk = self.g.fig, self.s.fig
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.075, rise=0.3, life=0.26, src2=lambda t: G.pose(t)['Er'],
                                seg=(0.0, 1.0), seed=7, trail=0.45),
                       fx.Flame(lambda t: Sk.pose(t)['Wr'], 'red', size=0.075, rise=0.3, life=0.26, src2=lambda t: Sk.pose(t)['Er'],
                                seg=(0.0, 1.0), seed=8, trail=0.45)]
        self.zoom = lambda s: 1.0 + (k - 1.0) * smoothstep(123.5, 125.5, (self.t0 + s) * 24)

    def draw(self, fr, s):
        cs = self.cam.at(s)
        paper(fr)
        # the dark band of the road under them, as two light pencil edges (shrinks with the zoom)
        z = self.zoom(s)
        for yy in (35, 50):
            a, b = px(_zoom((-20, yy), (47, 48), z)), px(_zoom((120, yy), (47, 48), z))
            fr.b.drawLine(a[0], a[1], b[0], b[1], paint(THEME['env_edge'], 0.5, stroke=2.0))
        draw_actors(fr, self.cam, s, s, [self.g, self.s])
        fx.render_flames(fr, cs, self.flames, s)
        if s < 2 / 24:
            fr.post.append(fx.whip_blur(220 * (1 - s / (2 / 24)), 0))


# ============================================================================ 3: title
class S3(Shot):
    """Black shards with paper-white edges slash across the frame in a new arrangement every
    two frames; the four characters land one by one (130, 132, 134, 136) with the furigana on
    the last; from 142 black shards cover it, it flashes back once at 147, black at 148."""
    t0, t1 = 126 / 24, 148 / 24
    vignette = 0.1

    def setup(self):
        tf = skia.Typeface.MakeFromFile(TITLE_FONT, 0)
        self.font = skia.Font(tf, 560)
        self.small = skia.Font(tf, 30)
        self.chars = '呪術廻戦'
        # glyph boxes traced from frame 139 (percent): x centres, top / bottom
        self.cx = [17.5, 36.5, 55.5, 77.0]
        self.lands = [129.6, 131.6, 133.6, 135.6]

    def slabs(self, f):
        """the shard arrangement for this moment: a new set every two frames, each sliding"""
        out = []
        g = int(f // 2)
        u = (f - g * 2) / 2.0
        n = 7 + (g % 3) * 3 + (6 if f >= 142 else 0)
        for i in range(n):
            ang = math.radians(-35 + 70 * hash01(g, i, 1)) + (math.pi / 2 if hash01(g, i, 2) > 0.65 else 0)
            off = (hash01(g, i, 3) - 0.5) * 1400 + (u - 0.5) * 120 * (1 if hash01(g, i, 4) > 0.5 else -1)
            wd = 18 + 130 * hash01(g, i, 5) ** 2 + (260 * hash01(g, i, 6) if f >= 142 else 0)
            out.append((ang, off, wd))
        return out

    def band(self, c, ang, off, w, colr, a=1.0):
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        L = 2600
        cx, cy = W / 2 + nx * off, H / 2 + ny * off
        x0, y0, x1, y1 = cx - ca * L / 2, cy - sa * L / 2, cx + ca * L / 2, cy + sa * L / 2
        pts = [(x0 + nx * w / 2, y0 + ny * w / 2), (x1 + nx * w / 2, y1 + ny * w / 2), (x1 - nx * w / 2, y1 - ny * w / 2), (x0 - nx * w / 2, y0 - ny * w / 2)]
        c.drawPath(poly_path(pts, closed=True), paint(colr, a))

    def draw(self, fr, s):
        f = (self.t0 + s) * 24
        c = fr.b
        paper(fr)
        # under the shards: the city going by, as faint pencil verticals sliding left
        for i in range(14):
            x = (hash01(31, i) * 1.4 - 0.2) * W - s * 900 * (0.6 + 0.8 * hash01(32, i))
            x = (x % (W * 1.4)) - W * 0.2
            y0 = H * (0.15 + 0.4 * hash01(33, i))
            c.drawLine(x, y0, x, H, paint(THEME['env_edge'], 0.35, stroke=2.0))
        sl = self.slabs(f)
        edge = tuple(min(1.0, ch * 1.07) for ch in THEME['bg'])
        for (ang, off, wd) in sl:
            self.band(c, ang, off, wd + 14, edge)          # paper-white rim
        for (ang, off, wd) in sl:
            self.band(c, ang, off, wd, INK)
        # the title
        if f < 142 or 146.6 < f < 147.6:
            zoom = 1.0 + 0.012 * (f - 136)
            for i, ch in enumerate(self.chars):
                a = f - self.lands[i]
                if a < 0:
                    continue
                pop = 1.0 + 0.22 * math.exp(-a * 3.0)
                cx, cy = (50 + (self.cx[i] - 50) * zoom) * W / 100, (57 + 0.12 * (f - 136)) * H / 100
                if a < 1.5:
                    # the landing clears the shards around it for a moment
                    rr = 330 * (0.6 + 0.6 * a / 1.5)
                    c.drawCircle(cx, cy, rr, paint(THEME['bg'], 1.0 - a / 1.5, blur=rr * 0.25))
                self._glyph(fr, ch, cx, cy, pop * zoom)
            if f >= self.lands[3]:
                blob = skia.TextBlob.MakeFromString('じゅじゅつかいせん', self.small)
                x0, y0 = (50 + (72 - 50) * zoom) * W / 100, 26 * H / 100
                c.drawTextBlob(blob, x0, y0, paint(THEME['bg'], 1.0, stroke=6))
                c.drawTextBlob(blob, x0, y0, paint(INK, 1.0))
        if f >= 147.6:
            paper(fr, INK)

    def _glyph(self, fr, ch, cx, cy, k):
        c = fr.b
        path = self.font.getPath(self.font.textToGlyphs(ch)[0])
        b = path.getBounds()
        c.save()
        c.translate(cx, cy)
        # the logo's characters are tall and narrow: about half the frame high
        sy = k * 0.49 * H / b.height()
        c.scale(sy * 0.72, sy)
        c.translate(-(b.left() + b.right()) / 2, -(b.top() + b.bottom()) / 2)
        # paper-white rim, then the black glyph thickened with round strokes, red at the stroke ends
        c.drawPath(path, paint(THEME['bg'], 1.0, stroke=60))
        sh = skia.GradientShader.MakeLinear([skia.Point(0, b.top()), skia.Point(0, b.bottom())],
                                            [col(INK), col(INK), col((0.55, 0.04, 0.07))], [0.0, 0.9, 1.0])
        p = paint(INK, 1.0)
        p.setShader(sh)
        c.drawPath(path, p)
        ps = paint(INK, 1.0, stroke=10)
        ps.setShader(sh)
        c.drawPath(path, ps)
        c.restore()


def shifted(keys, dx_fn, dy_fn=None):
    """add a camera pan (percent offsets as functions of the frame) to every traced point"""
    out = []
    state = {}
    for f, d in sorted(keys, key=lambda k: k[0]):
        state = {**state, **d}          # resolve what each key inherits before shifting it
        dx, dy = dx_fn(f), (dy_fn(f) if dy_fn else 0.0)
        e = {}
        for n, v in state.items():
            if isinstance(v, tuple) and len(v) == 2 and not isinstance(v[0], str):
                e[n] = (v[0] + dx, v[1] + dy)
            else:
                e[n] = v
        out.append((f, e))
    return out


def pencil(fr, pts, a=0.55, w=2.0, closed=False):
    P = [px(p) for p in pts]
    fr.b.drawPath(poly_path(P, closed=closed), paint(THEME['env_edge'], a, stroke=w))


def ink_poly(fr, pts, colr=None):
    P = [px(p) for p in pts]
    fr.b.drawPath(poly_path(P, closed=True), paint(INK if colr is None else colr, 1.0))


# ============================================================================ 4: the morgue
from films.seq_b import SHOKO, UTAHIME


class S4(Shot):
    """the camera trucks right out from behind a man's back (his dark back wipes off to the
    left): Gojo sits hunched on a gurney among the body drawers, Shoko smokes on the right"""
    t0, t1 = 148 / 24, 219 / 24

    def setup(self):
        pan = lambda f: float(np.interp(f, [148, 152, 157, 162, 170, 190, 210, 219], [44, 30, 12, 3, 0, 1, -2, -3]))
        self.pan = pan
        g = [K(148, H=(47, 38), r=4.6, yaw=-15, pitch=28, roll=4, C=(44, 46), Sr=(37, 46), Sl=(51, 46), P=(47, 66), Er=(35, 62),
               Wr=(41, 78), El=(53, 62), Wl=(46, 75), Kl=(55, 73), Al=(57, 90), Kr=(50, 73), Ar=(49, 90), hs_r='flat', hs_l='flat',
               palm_r='away', palm_l='away', eye_glow=0.0, eye_open=0.35, hide=('legl', 'legr')),
             K(160, H=(47, 37)), K(170, H=(44, 37), pitch=30), K(180, H=(46, 39), roll=6), K(190, H=(45, 40), pitch=33),
             K(200, H=(46, 40), eye_open=0.25), K(210, H=(44, 40), pitch=30, eye_open=0.5), K(219, H=(44, 40))]
        k = [K(148, H=(89, 40), r=4.2, yaw=-40, pitch=8, C=(89, 48), Sr=(87, 49), Sl=(92, 49), P=(90, 68), Er=(84, 56), Wr=(88, 44),
               El=(94, 60), Wl=(88, 65), Kl=(91, 83), Al=(91, 99), Kr=(88, 83), Ar=(88, 99), hs_r='two', hd_r=100, hs_l='relax',
               eye_open=0.6),
             K(175, H=(89, 41), Wr=(88, 45)), K(190, H=(88, 41), Wr=(87, 46)), K(205, H=(89, 40), Wr=(88, 44)), K(219, H=(89, 41))]
        m = [K(148, H=(21, -3), r=8, yaw=180, C=(20, 14), Sl=(8, 16), Sr=(32, 16), P=(19, 82), El=(5, 46), Wl=(6, 72), Er=(34, 46),
               Wr=(33, 70), hide=('legl', 'legr'), eye_open=0.0),
             K(170, H=(20, -3)), K(219, H=(19, -2))]
        self.g = RotoActor(GOJO, shifted(g, pan), self.t0, 'gojo_r4')
        self.k = RotoActor(SHOKO, shifted(k, pan), self.t0, 'shoko_r4')
        self.m = RotoActor(PLAIN, shifted(m, pan), self.t0, 'man_r4')
        self.cam = screen_cam()

    def draw(self, fr, s):
        f = (self.t0 + s) * 24
        dx = self.pan(f)
        paper(fr)
        # the wall of body drawers, in perspective, and the gurney
        TL, TR, BR, BL = (30, 8), (102, -5), (102, 93), (30, 78)
        lerp = lambda a, b, u: (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        sh = lambda p: (p[0] + dx, p[1])
        for i in range(5):
            u = i / 4
            pencil(fr, [sh(lerp(TL, TR, u * 0.98)), sh(lerp(BL, BR, u * 0.98))], 0.8)
        for j in range(6):
            v = j / 5
            pencil(fr, [sh(lerp(TL, BL, v)), sh(lerp(TR, BR, v))], 0.8)
        for i in range(4):
            for j in range(5):
                u, v = (i + 0.5) / 4, (j + 0.3) / 5
                top = lerp(lerp(TL, TR, u), lerp(BL, BR, u), v)
                pencil(fr, [sh((top[0] - 2.2, top[1])), sh((top[0] + 2.2, top[1] - 0.6))], 0.9, 3.0)
        pencil(fr, [sh((27, 82)), sh((70, 88)), sh((74, 80)), sh((35, 77)), sh((27, 82))], 0.7, 2.5)
        pencil(fr, [sh((29, 84)), sh((29, 100))], 0.6, 2.5)
        pencil(fr, [sh((66, 89)), sh((66, 100))], 0.6, 2.5)
        pencil(fr, [sh((30, 93)), sh((66, 97))], 0.5, 2.0)
        # cigarette smoke curling up from Shoko's hand
        J = self.k.fig.pose(s)
        q = self.cam.at(s).proj(J['Wr'])
        pts = [(q[0] + 10 * math.sin(f * 0.35 + i * 0.9) * (i / 8), q[1] - 30 - i * 22) for i in range(9)]
        fr.b.drawPath(smooth_path(pts), paint(THEME['env_edge'], 0.45, stroke=2.5))
        draw_actors(fr, self.cam, s, s, [self.g, self.k])
        draw_actors(fr, self.cam, s, s, [self.m])
        # his dark back right in front of the lens wipes off to the left as the camera moves out
        if f < 158:
            u = (f - 148) / 10.0
            x0 = W * (0.98 - 1.02 * u ** 0.8)
            fr.b.drawPath(poly_path([(-10, -10), (x0 + 120, -10), (x0, H + 10), (-10, H + 10)], closed=True), paint(INK, 1.0))


# ============================================================================ 5: Gojo, close
class S5(Shot):
    """his face fills the frame, tilted, looking down past the lens; the eyes glow"""
    t0, t1 = 212 / 24, 268 / 24

    def setup(self):
        keys = [K(212, H=(55, 41), r=44, roll=16, yaw=4, pitch=10, eye_glow=1.3, eye_open=0.8, eye_k=0.6,
                  hide=('torso', 'arml', 'armr', 'legl', 'legr')),
                K(230, H=(55, 40), eye_glow=1.5), K(250, H=(54, 41), roll=17), K(268, H=(53, 41), roll=17)]
        self.g = RotoActor(GOJO, keys, self.t0, 'gojo_r5')
        self.cam = screen_cam()

    def draw(self, fr, s):
        paper(fr)
        # the blurred block behind his shoulder on the left
        pencil(fr, [(4, 100), (8, 12), (15, 10), (21, 100)], 0.35, 3.0)
        draw_actors(fr, self.cam, s, s, [self.g])


# ============================================================================ 6: the three of them
class S6(Shot):
    """waist-up, three side by side: the old man with the guitar case on his back, Gojo in the
    middle with his head down, Utahime on the right"""
    t0, t1 = 252 / 24, 298 / 24

    def setup(self):
        o = [K(252, H=(14, 45), r=9, yaw=-25, pitch=25, C=(17, 62), P=(20, 120), eye_open=0.3, hide=('legl', 'legr')),
             K(275, H=(14, 46)), K(298, H=(13, 46))]
        g = [K(252, H=(44, 30), r=13, yaw=12, pitch=30, roll=4, C=(48, 58), P=(52, 130), eye_glow=0.8, eye_open=0.5,
               hide=('legl', 'legr')),
             K(272, H=(43, 31), eye_glow=1.0), K(288, H=(43, 32)), K(298, H=(43, 33), eye_open=0.6)]
        u = [K(252, H=(82, 37), r=6.5, yaw=-30, pitch=15, C=(82, 52), P=(83, 95), Er=(78, 70), Wr=(80, 86), El=(87, 70), Wl=(86, 86),
               eye_open=0.6, hide=('legl', 'legr')),
             K(275, H=(82, 38)), K(298, H=(82, 37))]
        self.o = RotoActor(OLDMAN, o, self.t0, 'old_r6')
        self.g = RotoActor(GOJO, g, self.t0, 'gojo_r6')
        self.u = RotoActor(UTAHIME, u, self.t0, 'uta_r6')
        self.cam = screen_cam()

    def draw(self, fr, s):
        paper(fr)
        for x in (2, 6, 10, 13):
            pencil(fr, [(x, 58), (x, 100)], 0.3, 2.0)
        draw_actors(fr, self.cam, s, s, [self.u, self.o])
        # the guitar case on the old man's back
        ink_poly(fr, [(16, 21), (27, 14), (33, 90), (21, 100)])
        draw_actors(fr, self.cam, s, s, [self.g])


SHOTS = [S0, S1, S2, S3, S4, S5, S6]
SEGMENTS = [(S0.t0, S6.t1)]
