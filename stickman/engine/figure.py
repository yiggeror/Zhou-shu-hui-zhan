"""Draw a posed stick figure: depth-sorted limb chains with a dark separation outline,
filled head with hair spikes, glowing eyes (emissive), and motion smears for fast limbs."""
import math
import numpy as np
import skia
from .mathx import V, norm, clamp, hash01, fbm1, Ry, Rx
from .canvas import paint, poly_path, smooth_path

from .theme import T as THEME

INK = THEME['ink']
HEAD_FILL = THEME['head_fill']

# hair spikes in head frame: (direction, length, half-width angle)
def _sp(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    return V(math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p))

HAIR = {
    # Gojo: tall white spikes standing up and swept slightly back
    'gojo': [(_sp(-100, 30), 0.95, 0.36), (_sp(-70, 52), 1.25, 0.38), (_sp(-35, 68), 1.5, 0.40),
             (_sp(0, 74), 1.6, 0.40), (_sp(35, 68), 1.5, 0.40), (_sp(70, 52), 1.25, 0.38),
             (_sp(100, 30), 0.95, 0.36), (_sp(180, 62), 1.45, 0.42), (_sp(140, 48), 1.25, 0.40),
             (_sp(-140, 48), 1.25, 0.40), (_sp(180, 30), 1.0, 0.40), (_sp(0, 35), 0.9, 0.36)],
    # Sukuna: spikes swept back into a mane
    'sukuna': [(_sp(-150, 55), 1.0, 0.36), (_sp(150, 55), 1.0, 0.36), (_sp(180, 40), 1.25, 0.40),
               (_sp(-125, 30), 1.05, 0.36), (_sp(125, 30), 1.05, 0.36), (_sp(180, 12), 1.15, 0.40),
               (_sp(-160, 75), 0.85, 0.36), (_sp(160, 75), 0.85, 0.36), (_sp(-105, 10), 0.8, 0.32),
               (_sp(105, 10), 0.8, 0.32), (_sp(-150, -5), 0.9, 0.34), (_sp(150, -5), 0.9, 0.34)],
}


HAIR['fushiguro'] = [(_sp(a, p), l, 0.30) for (a, p, l) in [
    (-110, 20, 0.95), (-80, 45, 1.15), (-50, 62, 1.2), (-20, 75, 1.25), (15, 72, 1.3), (45, 60, 1.2), (80, 45, 1.15),
    (110, 20, 0.95), (150, 40, 1.15), (180, 55, 1.2), (-150, 40, 1.15), (130, 70, 1.0), (-130, 70, 1.0), (0, 40, 0.8)]]
HAIR['short'] = []
HAIR['old'] = [(_sp(a, p), l, 0.45) for (a, p, l) in [(180, 70, 0.75), (165, 60, 0.6), (-165, 60, 0.6)]]
HAIR['mahoraga'] = [(_sp(a, p), l, 0.22) for (a, p, l) in [(-100, 10, 1.3), (100, 10, 1.3), (-95, 35, 1.0), (95, 35, 1.0)]]


def _eyes(style):
    if getattr(style, 'no_eyes', False) or 'blindfold' in getattr(style, 'extras', ()):
        return []
    if style.four_eyes:
        # main eyes, then the two small eyes underneath
        return [(-0.40, 0.14, 0.92, -1), (0.40, 0.14, 0.92, 1), (-0.33, -0.17, 0.55, -1), (0.33, -0.17, 0.55, 1)]
    return [(-0.40, 0.06, 1.0, -1), (0.40, 0.06, 1.0, 1)]


def chains(fig, J):
    """limb chains as lists of 3D points, plus width multipliers"""
    S = fig.L
    out = []
    # torso: pelvis -> mid -> chest -> neck (bezier sampled)
    P, M, C, N = J['P'], J['M'], J['C'], J['N']
    tor = []
    for i in range(7):
        u = i / 6
        tor.append((1 - u) ** 2 * P + 2 * (1 - u) * u * (2 * M - (P + C) / 2) + u * u * C)
    tor.append(N)
    out.append(('torso', tor, 1.12))
    for s in 'lr':
        out.append(('arm' + s, [J['S' + s], J['E' + s], J['W' + s]], 1.0))
        out.append(('leg' + s, [J['Hp' + s], J['K' + s], J['A' + s], J['T' + s]], 1.05))
    return out


class FigDraw:
    def __init__(self, fig):
        self.fig = fig

    def project_chains(self, cs, J):
        k = self.fig.k
        res = []
        for name, pts, wm in chains(self.fig, J):
            P = cs.proj_many(np.array(pts))
            if np.any(P[:, 2] < 0.05):
                continue
            depth = float(np.mean(P[:, 2]))
            wpx = self.fig.style.width * wm * cs.scale(depth)
            res.append(dict(name=name, P=P, depth=depth, w=wpx))
        return res

    # ------------------------------------------------------------------
    def draw(self, fr, cs, t, cam_at=None, shutter=1 / 80, smear=1.0, alpha=1.0, line_k=1.0,
             outline=True, eyes=True, glow_k=1.0, silhouette=None, ghosts=None):
        """cam_at(t) -> CamState for sub-frame times (for smears); defaults to cs.
        ghosts: callable(t) -> list of (dt, alpha, colour): faint after-images of earlier poses"""
        fig = self.fig
        self._t = t
        J = fig.pose(t)
        if J['visible'] * alpha <= 0.001:
            return J
        a_all = J['visible'] * alpha
        line = INK if silhouette is None else silhouette
        outline = False   # one solid colour, no separation strokes: joints never show gaps
        if ghosts is not None:
            for (dt, ga, gc) in ghosts(t):
                if ga > 0.01:
                    Jg = fig.pose(t - dt)
                    csg = cam_at(t - dt) if cam_at else cs
                    self._draw_lines(fr, csg, Jg, gc, ga * a_all, outline=False, smear=True)
        # ---- motion smear: the area each limb swept during the shutter, filled as one soft shape
        if smear > 0 and shutter > 0:
            self._swept_smear(fr, cs, t, shutter, cam_at, line, a_all * smear * line_k)
        self._draw_lines(fr, cs, J, line, a_all * line_k, outline=outline)
        if eyes:
            self.draw_eyes(fr, cs, J, t, a_all * glow_k)
        return J

    def _swept_smear(self, fr, cs, t, shutter, cam_at, line, a):
        fig = self.fig
        n = 10
        times = [t - shutter * (1 - i / n) for i in range(n + 1)]
        poses = [fig.pose(tt) for tt in times]
        cams = [cam_at(tt) if cam_at else cs for tt in times]
        wref = fig.style.width * cs.scale(max(cs.to_cam(poses[-1]['C'])[2], 0.2))
        chains = [('El', 'Wl'), ('Sl', 'El'), ('Er', 'Wr'), ('Sr', 'Er'), ('Kl', 'Al'), ('Hpl', 'Kl'), ('Al', 'Tl'),
                  ('Kr', 'Ar'), ('Hpr', 'Kr'), ('Ar', 'Tr')]
        c = fr.b
        drew = False
        for (ka, kb) in chains:
            Pa = [cams[i].proj(poses[i][ka]) for i in range(n + 1)]
            Pb = [cams[i].proj(poses[i][kb]) for i in range(n + 1)]
            if any(p[2] < 0.05 for p in Pa + Pb):
                continue
            dist = max(np.hypot(*(Pa[-1][:2] - Pa[0][:2])), np.hypot(*(Pb[-1][:2] - Pb[0][:2])))
            if dist < wref * 1.2:
                continue
            if not drew:
                c.saveLayerAlpha(None, int(max(0, min(255, 255 * a * 0.55))))
                drew = True
            for i in range(n):
                u = (i + 1) / n
                pts = [Pa[i][:2], Pb[i][:2], Pb[i + 1][:2], Pa[i + 1][:2]]
                c.drawPath(poly_path(pts, closed=True), paint(line, 0.15 + 0.85 * u ** 1.5))
        if drew:
            c.restore()

    # ------------------------------------------------------------------
    def _draw_lines(self, fr, cs, J, line, a, outline=True, smear=False):
        fig = self.fig
        items = self.project_chains(cs, J)
        # head
        hc = cs.proj(J['H'])
        if hc[2] > 0.05:
            hr = fig.L['head'] * fig.style.head_k * cs.scale(hc[2])
            items.append(dict(name='head', depth=float(hc[2]) - fig.L['head'] * 0.5, c=hc, r=hr))
        # hands
        for s in 'lr':
            wc = cs.proj(J['W' + s])
            if wc[2] > 0.05:
                rr = (0.030 + 0.022 * J['fist_' + s]) * fig.k * cs.scale(wc[2])
                items.append(dict(name='fist' + s, depth=float(wc[2]) - 0.01, c=wc, r=rr, side=s))
        if fig.style.hair == 'long' and hc[2] > 0.05:
            items.append(dict(name='hairback', depth=float(hc[2]) + fig.L['head'] * 1.2))
        items.sort(key=lambda d: -d['depth'])
        c = fr.b
        if a < 0.999:
            # draw the whole figure into a layer so overlapping strokes do not double up
            c.saveLayerAlpha(None, int(max(0, min(255, a * 255))))
            a_draw = 1.0
        else:
            a_draw = a
        for it in items:
            nm = it['name']
            if nm == 'head':
                self._head(fr, cs, J, it, line, a_draw, outline, smear)
                continue
            if nm == 'hairback':
                self._long_hair(fr, cs, J, line, a_draw)
                continue
            if nm.startswith('fist'):
                self._hand(c, cs, J, it, line, a_draw)
                continue
            P = it['P'][:, :2]
            w = max(it['w'], 1.2)
            path = smooth_path(P) if nm == 'torso' else poly_path(P)
            if outline:
                gap = max(2.0, w * 0.32)
                # skip the first stretch of the chain so the attachment point is not notched
                Po = P
                if nm != 'torso':
                    d0 = w * 0.9
                    seg = P[1] - P[0]
                    L = float(np.hypot(*seg))
                    if L > d0 + 1:
                        Po = np.vstack([P[0] + seg * (d0 / L), P[1:]])
                    else:
                        Po = P[1:]
                if len(Po) >= 2:
                    po = smooth_path(Po) if nm == 'torso' else poly_path(Po)
                    c.drawPath(po, paint(INK, a_draw, stroke=w + 2 * gap))
            c.drawPath(path, paint(line, a_draw, stroke=w))
        if a < 0.999:
            c.restore()

    def _hand(self, c, cs, J, it, line, a):
        fig = self.fig
        s = it['side']
        hk = fig.k * fig.style.hand_k
        size_px = 0.17 * hk * cs.scale(it['c'][2])
        if size_px < 12:
            c.drawCircle(it['c'][0], it['c'][1], it['r'], paint(line, a))
            return
        from .hand import hand_frame, draw_hand, SHAPES
        sh = J['hs_' + s]
        if sh is None:
            f = clamp(J['fist_' + s], 0, 1)
            sh = np.array(SHAPES['relax']) * (1 - f) + np.array(SHAPES['fist']) * f
        side = 1 if s == 'r' else -1
        R = hand_frame(J['E' + s], J['W' + s], J['hroll_' + s], J['Rc'] @ V(side, 0, 0))
        draw_hand(c, cs, J['W' + s], R, sh, side, line, a, hk, width_m=0.0125)

    def _head(self, fr, cs, J, it, line, a, outline, smear):
        fig = self.fig
        c = fr.b
        x, y, r = it['c'][0], it['c'][1], it['r']
        rw = max(fig.style.head_w * cs.scale(it['c'][2]), 1.2)
        # hair: union of spike triangles, outlined once, behind the head disk
        Rh, Hc = J['Rh'], J['H']
        R = fig.L['head'] * fig.style.head_k
        hair = None
        ex = fig.style.extras
        if 'ears' in ex:
            for sx in (-1, 1):
                ep = cs.proj(Hc + Rh @ V(sx * 0.72, 0.78, -0.1) * R)
                if ep[2] > 0.05:
                    c.drawCircle(ep[0], ep[1], R * 0.42 * cs.scale(ep[2]), paint(line, a))
        if 'wheel' in ex:
            self._wheel(fr, cs, J, line, a)
        if 'scarf' in ex:
            self._scarf(fr, cs, J, line, a)
        for i, (d, ln, hw) in enumerate(HAIR.get(fig.style.hair) or []):
            dw = Rh @ d
            side = norm(np.cross(dw, cs.f))
            if np.linalg.norm(side) < 1e-6:
                side = cs.r
            b1 = Hc + norm(dw + side * hw * 1.3) * R * 0.9
            b2 = Hc + norm(dw - side * hw * 1.3) * R * 0.9
            tip = Hc + dw * R * (1.0 + 0.85 * ln)
            pts = cs.proj_many(np.array([b1, tip, b2]))
            if np.any(pts[:, 2] < 0.05):
                continue
            tri = poly_path(pts[:, :2], closed=True)
            hair = tri if hair is None else (skia.Op(hair, tri, skia.PathOp.kUnion_PathOp) or hair)
        if hair is not None:
            c.drawPath(hair, paint(line, a))
        # solid head (the face is where the eyes glow)
        c.drawCircle(x, y, r + rw * 0.5, paint(line, a))
        if HEAD_FILL != line and not smear:
            c.drawCircle(x, y, r - rw * 0.5, paint(HEAD_FILL, a))
        if smear:
            return
        if 'beard' in ex:
            pts = [Hc + Rh @ V(-0.45, -0.55, 0.75) * R, Hc + Rh @ V(0, -1.75, 0.55) * R, Hc + Rh @ V(0.45, -0.55, 0.75) * R]
            P = cs.proj_many(np.array(pts))
            if np.all(P[:, 2] > 0.05):
                c.drawPath(poly_path(P[:, :2], closed=True), paint(line, a))
        paper = THEME['bg']
        if 'glasses' in ex:
            for sx in (-1, 1):
                ctr = Hc + Rh @ V(sx * 0.38, 0.05, 0.93) * R
                ring = [ctr + (Rh @ V(math.cos(th) * 0.27, math.sin(th) * 0.2, 0)) * R for th in np.linspace(0, 2 * math.pi, 20)]
                P = cs.proj_many(np.array(ring))
                n = Rh @ V(0, 0, 1)
                if float(n @ norm(cs.pos - ctr)) > 0.05 and np.all(P[:, 2] > 0.05):
                    c.drawPath(poly_path(P[:, :2], closed=True), paint(paper, a * 0.9, stroke=max(1.2, rw * 0.6)))
        if 'blindfold' in ex:
            band = []
            for th in np.linspace(-1.9, 1.9, 24):
                band.append(Hc + Rh @ V(math.sin(th), 0.08, math.cos(th)) * R * 1.01)
            for th in np.linspace(1.9, -1.9, 24):
                band.append(Hc + Rh @ V(math.sin(th), -0.30, math.cos(th)) * R * 1.01)
            P = cs.proj_many(np.array(band))
            vis = [float((Rh @ V(math.sin(th), 0, math.cos(th))) @ norm(cs.pos - Hc)) for th in np.linspace(-1.9, 1.9, 24)]
            if np.all(P[:, 2] > 0.05):
                c.save()
                hp = skia.Path(); hp.addCircle(x, y, r + rw * 0.5)
                c.clipPath(hp, skia.ClipOp.kIntersect, True)
                c.drawPath(poly_path(P[:, :2], closed=True), paint(paper, a * 0.92))
                c.restore()

    def _wheel(self, fr, cs, J, line, a):
        """Mahoraga's dharma wheel floating above the head, turning slowly"""
        R = self.fig.L['head'] * self.fig.style.head_k
        Rh, Hc = J['Rh'], J['H']
        C = Hc + Rh @ V(0, 2.4, -0.5) * R
        up = Rh @ norm(V(0, 1, -0.9))
        aa = norm(np.cross(up, V(0, 0, 1)) if abs(up[2]) < 0.95 else np.cross(up, V(1, 0, 0)))
        bb = np.cross(up, aa)
        rad = 1.6 * R
        rot = getattr(self, '_t', 0.0) * 0.6 + getattr(self, 'wheel_turn', 0.0)
        ring = [C + (aa * math.cos(th) + bb * math.sin(th)) * rad for th in np.linspace(0, 2 * math.pi, 48)]
        Q = cs.proj_many(np.array(ring))
        if np.any(Q[:, 2] < 0.05):
            return
        wpx = max(1.5, 0.028 * self.fig.k * cs.scale(float(np.mean(Q[:, 2]))))
        c = fr.b
        c.drawPath(poly_path(Q[:, :2], closed=True), paint(line, a, stroke=wpx))
        cp = cs.proj(C)
        for i in range(8):
            th = rot + i * math.pi / 4
            d = aa * math.cos(th) + bb * math.sin(th)
            p1 = cs.proj(C + d * rad)
            p2 = cs.proj(C + d * rad * 1.28)
            c.drawLine(cp[0], cp[1], p1[0], p1[1], paint(line, a, stroke=wpx * 0.8))
            c.drawCircle(p2[0], p2[1], rad * 0.17 * cs.scale(p2[2]), paint(line, a))
        c.drawCircle(cp[0], cp[1], rad * 0.2 * cs.scale(cp[2]), paint(line, a))

    def _scarf(self, fr, cs, J, line, a):
        """scarf: a thick wrap around the neck and two short cloth tails behind it that wave in
        the wind (a travelling ripple), filled as tapered shapes"""
        from .draw3d import ribbon
        fig = self.fig
        t = getattr(self, '_t', 0.0)
        k = fig.k
        wind = np.asarray(getattr(self, 'wind', V(0.0, 0.0, 0.0)), float)
        wm = float(np.linalg.norm(wind))
        N, Rc = J['N'], J['Rc']
        collar = [N + Rc @ V(math.sin(th) * 0.08, -0.04 + 0.012 * math.cos(th), math.cos(th) * 0.065) * k
                  for th in np.linspace(-math.pi, math.pi, 16)]
        ribbon(fr, cs, collar, 0.06 * k, line, a, taper=0.0)
        back = Rc @ V(0, 0, -1)
        flow = norm(wind * 1.0 + V(0, -0.9, 0) * (1.2 - min(1.0, wm)) + back * 0.3)
        side_v = norm(np.cross(flow, cs.f)) if np.linalg.norm(np.cross(flow, cs.f)) > 1e-6 else cs.r
        for sd, ph, ln in ((-1, 0.0, 7), (1, 2.1, 6)):
            base = N + Rc @ V(0.03 * sd, -0.06, -0.06) * k
            cen = []
            for j in range(ln):
                u = j / (ln - 1)
                wave = math.sin(t * 11.0 + ph - j * 0.9) * 0.025 * j * min(1.0, 0.3 + wm)
                cen.append(base + flow * (0.055 * j * k) + side_v * wave * k + V(0, 0.02 * sd * j, 0) * k * wm * 0.3)
            P = cs.proj_many(np.array(cen))
            if np.any(P[:, 2] < 0.05):
                continue
            d = float(np.mean(P[:, 2]))
            wpx0 = 0.065 * k * cs.scale(d)
            left, right = [], []
            for j in range(ln):
                a0 = P[max(0, j - 1), :2]
                a1 = P[min(ln - 1, j + 1), :2]
                tg = a1 - a0
                nn = np.array([-tg[1], tg[0]]) / (np.hypot(*tg) + 1e-6)
                w = wpx0 * (1 - 0.65 * j / (ln - 1)) * 0.5
                left.append(P[j, :2] + nn * w)
                right.append(P[j, :2] - nn * w)
            pts = left + right[::-1]
            fr.b.drawPath(smooth_path(pts, closed=True), paint(line, a))

    def _long_hair(self, fr, cs, J, line, a):
        """long hair: locks from the crown falling behind the head to the shoulders and out to the
        sides; each point follows where the head was a little earlier, so the hair trails and swings"""
        fig = self.fig
        t = getattr(self, '_t', 0.0)
        R = fig.L['head'] * fig.style.head_k
        n_str, n_pt = 8, 7
        wind = np.asarray(getattr(self, 'wind', V(0.0, 0.0, 0.0)), float)
        locks = []
        for si in range(n_str):
            u = -1 + 2 * si / (n_str - 1)
            ang = u * 1.9
            pts = []
            for j in range(n_pt):
                lag = j * 0.04
                Jp = fig.pose(t - lag) if lag > 0 else J
                Rh, Hc = Jp['Rh'], Jp['H']
                root = Hc + Rh @ V(math.sin(ang) * 0.9, 0.45, -math.cos(ang) * 0.75) * R
                out = Rh @ V(math.sin(ang) * 0.045 * j, -0.085 * j, -0.035 * j) * fig.k
                sway = V(fbm1(t * 1.3 + si * 0.4, 70) * 0.018 * j, 0, fbm1(t * 1.1 + si * 0.4, 90) * 0.018 * j) * fig.k
                pts.append(root + out + sway + wind * (j * 0.06) * fig.k)
            P = cs.proj_many(np.array(pts))
            if np.any(P[:, 2] < 0.05):
                continue
            locks.append(P)
        if not locks:
            return
        d = float(np.mean([L[:, 2].mean() for L in locks]))
        wpx = max(1.2, 0.035 * fig.k * cs.scale(d))
        c = fr.b
        for L in locks:
            c.drawPath(smooth_path(L[:4, :2]), paint(line, a, stroke=wpx * 1.3))
            c.drawPath(smooth_path(L[2:, :2]), paint(line, a, stroke=wpx * 0.5))

    # ------------------------------------------------------------------
    def eye_shapes(self, cs, J):
        """projected almond outlines for each visible eye -> list of (pts Nx2, facing, size_px, scale)"""
        fig = self.fig
        R = fig.L['head'] * fig.style.head_k
        Rh, Hc = J['Rh'], J['H']
        op = clamp(J['eye_open'], 0, 1)
        sq = J['eye_squint']
        res = []
        for (yaw, pitch, sc, side) in _eyes(fig.style):
            d = V(math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch))
            n = Rh @ d
            E = Hc + n * R * 1.0
            tocam = norm(cs.pos - E)
            facing = float(n @ tocam)
            if facing < 0.12:
                continue
            up = Rh @ V(0, 1, 0)
            t1 = norm(np.cross(up, n))   # along the eye (toward head's right)
            t2 = np.cross(n, t1)
            slant = (0.30 if fig.style.four_eyes else 0.08) * side
            ca, sa = math.cos(slant), math.sin(slant)
            u1 = t1 * ca + t2 * sa
            u2 = t2 * ca - t1 * sa
            w = 0.074 * fig.k * sc
            h = (0.021 if fig.style.four_eyes else 0.021) * fig.k * sc * op * (1 - 0.45 * sq) * max(0.05, J['eye_l'] if side < 0 else J['eye_r'])
            # almond: 2 corners + upper/lower arcs (sampled)
            pts = []
            for i in range(9):
                u = -1 + 2 * i / 8
                pts.append(E + u1 * (u * w / 2) + u2 * (h * (1 - u * u) * (1.0 if not fig.style.four_eyes else 0.85)))
            for i in range(9):
                u = 1 - 2 * i / 8
                pts.append(E + u1 * (u * w / 2) - u2 * (h * 0.75 * (1 - u * u)))
            P = cs.proj_many(np.array(pts))
            if np.any(P[:, 2] < 0.05):
                continue
            size = float(np.hypot(*(P[0, :2] - P[8, :2])))
            res.append(dict(P=P[:, :2], facing=facing, size=size, sc=sc, E=cs.proj(E), h=h, n=n,
                            mult=J['eye_l'] if side < 0 else J['eye_r']))
        return res

    def draw_eyes(self, fr, cs, J, t, a=1.0):
        fig = self.fig
        st = fig.style
        op = clamp(J['eye_open'], 0, 1)
        glow = J['eye_glow'] * a
        if op <= 0.01 or a <= 0:
            return
        if J['eye_glow'] <= 0.01:
            b = 1.0
        eyes = self.eye_shapes(cs, J)
        # brightness follows the opening of the eye
        b = op ** 1.5
        for e in eyes:
            P, size = e['P'], e['size']
            vis = clamp((e['facing'] - 0.12) / 0.22, 0, 1) * e.get('mult', 1.0)
            if vis <= 0.01:
                continue
            k = vis * a
            cx, cy = float(e['E'][0]), float(e['E'][1])
            if size < 5.0:
                rr = max(1.3, size * 0.32) * (0.5 + 0.5 * op)
                fr.b.drawCircle(cx, cy, rr, paint(st.eye_core, k * b))
                fr.g.drawCircle(cx, cy, rr * 1.6, paint(st.eye, k * b * glow * 0.9, blur=rr * 1.2, add=True))
                fr.g.drawCircle(cx, cy, rr * 0.8, paint(st.eye_core, k * b * glow * 0.6, add=True))
                continue
            path = poly_path(P, closed=True)
            if J['eye_glow'] <= 0.01:
                fr.b.drawPath(path, paint(st.eye, k * 0.9))
                continue
            if size >= 34.0:
                self._eye_detail(fr, e, P, size, cx, cy, k, b, glow, op, t)
                if J['eye_fire'] > 0.01:
                    self._eye_fire(fr, e, t, k * J['eye_fire'] * b)
                continue
            # crisp body of the eye
            fr.b.drawPath(path, paint(st.eye, k))
            # hot core (smaller almond)
            core = (P - [cx, cy]) * 0.62 + [cx, cy]
            fr.b.drawPath(poly_path(core, closed=True), paint(st.eye_core, k * b))
            # tight rim glow hugging the outline + light inside
            hpx = max(2.0, size * 0.22)
            fr.g.drawPath(path, paint(st.eye, k * b * glow * 1.3, blur=hpx * 0.45, add=True))
            fr.g.drawPath(path, paint(st.eye, k * b * glow * 0.55, blur=hpx * 1.1, add=True))
            fr.g.drawPath(poly_path(core, closed=True), paint(st.eye_core, k * b * glow * 0.8, add=True))
            if J['eye_fire'] > 0.01:
                self._eye_fire(fr, e, t, k * J['eye_fire'] * b)

    def _eye_detail(self, fr, e, P, size, cx, cy, k, b, glow, op, t):
        """close-up eye: dark almond, glowing iris clipped by the lids, pupil and glint, white
        upper-lid line in the same stroke style as the figure, tight rim light"""
        st = self.fig.style
        path = poly_path(P, closed=True)
        c = fr.b
        c.drawPath(path, paint((0.015, 0.015, 0.02), k))
        # iris centre follows the almond centre (slightly toward the upper lid)
        top, bot = P[4], P[13]
        ix, iy = (top[0] + bot[0]) / 2 * 0.5 + cx * 0.5, (top[1] + bot[1]) / 2 * 0.5 + cy * 0.5
        rr = size * 0.30
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        g = skia.GradientShader.MakeRadial(skia.Point(ix, iy), rr,
                                           [skia.Color4f(*st.eye_core, 1.0), skia.Color4f(*st.eye, 1.0),
                                            skia.Color4f(st.eye[0] * 0.35, st.eye[1] * 0.35, st.eye[2] * 0.35, 1.0)],
                                           [0.0, 0.55, 1.0])
        pi = skia.Paint(AntiAlias=True)
        pi.setShader(g)
        pi.setAlphaf(float(k * (0.35 + 0.65 * b)))
        c.drawCircle(ix, iy, rr, pi)
        # pupil: Gojo a small bright point, Sukuna a dark slit
        if st.four_eyes:
            pp = skia.Path()
            pp.addOval(skia.Rect(ix - rr * 0.16, iy - rr * 0.62, ix + rr * 0.16, iy + rr * 0.62))
            c.drawPath(pp, paint((0.05, 0.0, 0.0), k * 0.9))
        else:
            c.drawCircle(ix, iy, rr * 0.22, paint((0.02, 0.06, 0.10), k * 0.8))
        c.drawCircle(ix - rr * 0.35, iy - rr * 0.35, rr * 0.16, paint((1, 1, 1), k * (0.4 + 0.6 * b)))
        c.restore()
        # light: iris glow into the emissive layer (clipped to the eye) + tight rim
        fr.g.save()
        fr.g.clipPath(path, skia.ClipOp.kIntersect, True)
        fr.g.drawCircle(ix, iy, rr * 1.05, paint(st.eye, k * b * glow * 0.9, add=True, blur=rr * 0.25))
        fr.g.drawCircle(ix, iy, rr * 0.45, paint(st.eye_core, k * b * glow * 0.7, add=True, blur=rr * 0.15))
        fr.g.restore()
        fr.g.drawPath(path, paint(st.eye, k * b * glow * 0.75, stroke=max(2.0, size * 0.035), add=True, blur=size * 0.035))
        # lids in the figure's line style
        lw = max(2.0, size * 0.055)
        up = poly_path(P[0:9])
        lo = poly_path(P[9:18])
        lid = tuple(min(1.0, 0.55 * ch + 0.45) for ch in st.eye)
        c.drawPath(up, paint(lid, k, stroke=lw))
        c.drawPath(lo, paint(lid, k * 0.7, stroke=lw * 0.55))

    def _eye_fire(self, fr, e, t, a):
        """small flame tongues and sparks kept inside / right on the eye"""
        st = self.fig.style
        P = e['P']
        size = e['size']
        cx, cy = float(e['E'][0]), float(e['E'][1])
        top = P[1:8]  # upper arc points
        seed = int(abs(cx) * 7 + abs(cy) * 13) % 997
        for i, q in enumerate(top):
            f = fbm1(t * 9.0 + i * 1.7, seed + i)
            hgt = size * (0.10 + 0.16 * (0.5 + 0.5 * f)) * (1 - abs(i - 3) / 5.0)
            if hgt <= 0.5:
                continue
            sway = size * 0.05 * fbm1(t * 6 + i, seed + 31 + i)
            base_w = size * 0.07
            tip = (q[0] + sway, q[1] - hgt)
            pth = skia.Path()
            pth.moveTo(q[0] - base_w, q[1] + 1)
            pth.quadTo(q[0] - base_w * 0.3, q[1] - hgt * 0.6, tip[0], tip[1])
            pth.quadTo(q[0] + base_w * 0.3, q[1] - hgt * 0.6, q[0] + base_w, q[1] + 1)
            pth.close()
            fr.g.drawPath(pth, paint(st.eye, a * 0.85, add=True, blur=max(0.6, size * 0.02)))
            fr.g.drawPath(pth, paint(st.eye_core, a * 0.35, add=True))
        # a few embers that live and die on the eye
        for j in range(4):
            ph = (t * 2.2 + hash01(seed, j)) % 1.0
            ex = cx + (hash01(seed, j, 3) - 0.5) * size * 0.8
            ey = cy - size * 0.05 - ph * size * 0.28
            al = a * math.sin(math.pi * ph)
            fr.g.drawCircle(ex, ey, max(0.8, size * 0.025), paint(st.eye_core, al, add=True))
