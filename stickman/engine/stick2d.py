"""Two-dimensional stick figures, posed like a hand-drawn stickman animation.

Every bone has a fixed length (proportions of the body height), so a pose is a set of angles:
nothing can stretch.  Angles are absolute screen angles in degrees: 0 points straight down,
90 points to screen right, 180 straight up, -90 to screen left.  Foreshortening is the
animator's cheat: a bone can be shortened on purpose (k_*), and a hand drawn bigger.

A pose (all optional except at / s):
  at      (x, y) pelvis position, percent of the frame (x of the width, y of the height)
  s       body height (head top to heel, standing) in percent of the frame height
  torso   spine angle (0 upright, + leaning toward screen right)
  head    head tilt (deg, + toward screen right), face: -1 looks screen-left .. 0 front .. 1 right,
          back=True seen from behind (no face)
  ual/fal/uar/far   upper arm / forearm angles, left and right arm ('l' = character's left)
  thl/shl/thr/shr   thigh / shin angles
  k_ual ... k_shr   length factors (foreshortening), hk_l / hk_r hand size factors
  hand_l / hand_r   'fist' 'open' 'point' 'claw' 'flat' 'two' 'none'
  front   limbs drawn over the torso (default: ('r_arm', 'r_leg')), the others go behind
  brow    + frowning / angry, - worried;  mouth 'none' 'flat' 'grit' 'open' 'smile' 'frown' 'shout'
  eyes    'open' 'narrow' 'closed' 'wide';  glow  0..2 (eye light)
"""
import math
import numpy as np
import skia
from .canvas import paint, poly_path, smooth_path
from .theme import T as THEME
from .camera import W, H

INK = THEME['ink']
PAPER = THEME['bg']

# proportions of the standing height
PROP = dict(head=0.095, neck=0.035, torso=0.30, ua=0.165, fa=0.155, th=0.225, sh=0.215, foot=0.075, width=0.034, sho=0.0)


class Char:
    """a character's look: hair, eye colour, extras"""

    def __init__(self, hair='short', eye=(1.0, 1.0, 1.0), eye_core=(1.0, 1.0, 1.0), four_eyes=False, marks=False,
                 extras=(), coloured_eyes=True):
        self.hair, self.eye, self.eye_core = hair, eye, eye_core
        self.four_eyes, self.marks, self.extras = four_eyes, marks, tuple(extras)
        self.coloured_eyes = coloured_eyes


GOJO = Char('gojo', (0.25, 0.85, 1.0), (0.88, 1.0, 1.0))
SUKUNA = Char('sukuna', (1.0, 0.16, 0.22), (1.0, 0.86, 0.84), four_eyes=True, marks=True)
SHOKO = Char('long', coloured_eyes=False)
UTAHIME = Char('pony', coloured_eyes=False)
GAKUGANJI = Char('old', coloured_eyes=False, extras=('beard',))
IJICHI = Char('short', coloured_eyes=False, extras=('glasses',))
PLAIN = Char('short', coloured_eyes=False)


def _dir(a):
    r = math.radians(a)
    return np.array([math.sin(r), math.cos(r)])       # screen: +x right, +y down; 0 deg = down


def P(p):
    return np.array([p[0] * W / 100.0, p[1] * H / 100.0])


class Pose:
    def __init__(self, **kw):
        self.d = dict(kw)

    def g(self, k, d=None):
        return self.d.get(k, d)


def joints(pose):
    """screen positions (pixels) of every joint for a pose"""
    g = pose.g
    tor = g('torso', 0.0)
    up = -_dir(tor)                                  # spine direction (toward the head)
    hang = g('head', tor)
    if g('head_at') is not None:
        B = g('head_r') * H / 100.0 / (PROP['head'] * g('k_head', 1.0))
        L = {k: v * B for k, v in PROP.items()}
        Hc0 = P(g('head_at'))
        N0 = Hc0 + _dir(hang) * L['head']
        C0 = N0 + _dir(hang) * L['neck']
        Pv = C0 - up * L['torso'] * g('k_torso', 1.0)
    else:
        B = g('s') * H / 100.0
        L = {k: v * B for k, v in PROP.items()}
        Pv = P(g('at'))
    C = Pv + up * L['torso'] * g('k_torso', 1.0)
    N = C + (-_dir(hang)) * L['neck']
    Hc = N + (-_dir(hang)) * L['head']
    J = dict(P=Pv, C=C, N=N, H=Hc, B=B, L=L, head_ang=hang)
    for s in 'lr':
        ua, fa = g('ua' + s, 0.0), g('fa' + s, 0.0)
        E = C + _dir(ua) * L['ua'] * g('k_ua' + s, 1.0)
        Wr = E + _dir(fa) * L['fa'] * g('k_fa' + s, 1.0)
        J['E' + s], J['W' + s] = E, Wr
        th, sh = g('th' + s, 0.0), g('sh' + s, 0.0)
        K = Pv + _dir(th) * L['th'] * g('k_th' + s, 1.0)
        A = K + _dir(sh) * L['sh'] * g('k_sh' + s, 1.0)
        J['K' + s], J['A' + s] = K, A
    return J


def _chain(c, pts, w, colr, a=1.0):
    p = skia.Path()
    p.moveTo(*map(float, pts[0]))
    for q in pts[1:]:
        p.lineTo(*map(float, q))
    pt = paint(colr, a, stroke=w)
    c.drawPath(p, pt)


def _hand(c, Wp, d, kind, size, w, colr, a, side):
    """2D hands: d is the forearm direction (unit), size the hand length in px"""
    if kind == 'none':
        return
    n = np.array([-d[1], d[0]]) * (1 if side == 'r' else -1)
    if kind == 'fist':
        c.drawCircle(float(Wp[0] + d[0] * size * 0.25), float(Wp[1] + d[1] * size * 0.25), size * 0.42, paint(colr, a))
        return
    palm = Wp + d * size * 0.35
    c.drawCircle(float(palm[0]), float(palm[1]), size * 0.32, paint(colr, a))
    fw = max(1.5, w * 0.42)
    if kind in ('open', 'claw', 'flat'):
        spread = {'open': 22, 'claw': 26, 'flat': 6}[kind]
        for i in range(4):
            ang = math.atan2(d[1], d[0]) + math.radians((i - 1.5) * spread / 1.5)
            u = np.array([math.cos(ang), math.sin(ang)])
            base = palm + u * size * 0.25
            tip = base + u * size * (0.55 if kind != 'claw' else 0.42)
            if kind == 'claw':
                tip2 = tip + (u * 0.4 + n * 0.6) * size * 0.2
                _chain(c, [base, tip, tip2], fw, colr, a)
            else:
                _chain(c, [base, tip], fw, colr, a)
        th = palm + n * size * 0.28
        _chain(c, [palm, th, th + (d * 0.6 + n * 0.5) * size * 0.3], fw, colr, a)
    elif kind in ('point', 'two'):
        k = 1 if kind == 'point' else 2
        for i in range(k):
            off = n * (i - (k - 1) / 2) * size * 0.16
            _chain(c, [palm + off, palm + off + d * size * 0.75], fw, colr, a)


HAIR2D = {
    # (angle from head-up in deg, length in head radii, half width in deg): spikes around the crown
    'gojo': [(-80, 0.55, 14), (-55, 0.85, 13), (-30, 1.05, 12), (-8, 1.15, 12), (15, 1.1, 12), (38, 0.95, 13), (62, 0.75, 14), (85, 0.45, 14)],
    'sukuna': [(-70, 0.45, 16), (-40, 0.6, 15), (-12, 0.7, 14), (15, 0.7, 14), (45, 0.65, 15), (75, 0.6, 16), (100, 0.5, 16)],
    'short': [],
    'megumi': [(-75, 0.5, 15), (-50, 0.7, 14), (-25, 0.8, 13), (0, 0.85, 13), (25, 0.8, 13), (50, 0.7, 14), (75, 0.5, 15), (100, 0.35, 16), (-100, 0.35, 16)],
    'old': [],
}


def _head(c, J, pose, ch, colr, a):
    g = pose.g
    Hc = J['H']
    R = J['L']['head'] * g('k_head', 1.0)
    ang = J['head_ang']
    upv = -_dir(ang)
    rt = np.array([-upv[1], upv[0]])                  # head's screen-right
    face = g('face', 0.0)
    back = g('back', False)
    # hair behind / around the crown
    spikes = HAIR2D.get(ch.hair)
    if ch.hair == 'long':
        # straight hair down the back of the head to the shoulders (on the side away from the face)
        back = -1.0 if face >= 0 else 1.0
        pts = [Hc + upv * R * 1.02 - rt * back * R * 0.3, Hc + rt * back * R * 1.1 + upv * R * 0.3,
               Hc + rt * back * R * 1.25 - upv * R * 2.2, Hc + rt * back * R * 0.2 - upv * R * 2.3,
               Hc - rt * back * R * 0.15 - upv * R * 0.6]
        c.drawPath(smooth_path(pts, closed=True), paint(colr, a))
    if ch.hair == 'pony':
        side = -1.0 if face >= 0 else 1.0
        knot = Hc + upv * R * 0.55 + rt * side * R * 0.75
        tail = [knot, knot + rt * side * R * 0.7 - upv * R * 0.6, knot + rt * side * R * 0.55 - upv * R * 2.4]
        c.drawPath(smooth_path([tail[0], tail[1], tail[2]]), paint(colr, a, stroke=R * 0.45))
        c.drawCircle(float(knot[0]), float(knot[1]), R * 0.32, paint(colr, a))
    if spikes and g('top', False):
        # seen from straight above: the spikes stand out all round the crown
        n = len(spikes) + 4
        spikes = [(-180 + 360 * i / n + 11, 0.55 * spikes[i % len(spikes)][1], 16) for i in range(n)]
    if spikes:
        path = None
        for (aa, ln, hw) in spikes:
            th = math.radians(aa) + (math.radians(25) * face if ch.hair == 'sukuna' else 0)
            dv = upv * math.cos(th) + rt * math.sin(th)
            th1, th2 = th - math.radians(hw), th + math.radians(hw)
            b1 = Hc + (upv * math.cos(th1) + rt * math.sin(th1)) * R * 0.92
            b2 = Hc + (upv * math.cos(th2) + rt * math.sin(th2)) * R * 0.92
            tip = Hc + dv * R * (1.0 + ln)
            tri = poly_path([b1, tip, b2], closed=True)
            path = tri if path is None else (skia.Op(path, tri, skia.PathOp.kUnion_PathOp) or path)
        c.drawPath(path, paint(colr, a))
    if ch.hair == 'old':
        top = Hc + upv * R * 0.85
        c.drawCircle(float(top[0]), float(top[1]), R * 0.35, paint(colr, a))
    c.drawCircle(float(Hc[0]), float(Hc[1]), R, paint(colr, a))
    if 'beard' in ch.extras and not back:
        ctr = Hc - upv * R * 0.55 + rt * face * R * 0.3
        c.drawPath(poly_path([ctr + rt * R * 0.45, ctr - upv * R * 1.0 + rt * face * R * 0.2, ctr - rt * R * 0.45], closed=True), paint(colr, a))
    return Hc, R, upv, rt, face, back


def _face(fr, J, pose, ch, a, t=0.0):
    """eyes (glowing for the two leads), brows and mouth in paper over the black head"""
    g = pose.g
    Hc = J['H']
    R = J['L']['head'] * g('k_head', 1.0)
    upv = -_dir(J['head_ang'])
    rt = np.array([-upv[1], upv[0]])
    face = g('face', 0.0)
    if g('back', False) or g('noface', False):
        return
    c = fr.b
    ecx = Hc + rt * face * R * 0.42 + upv * R * g('look_up', 0.08)
    sep = R * 0.40 * (1 - 0.45 * abs(face))
    eyes = g('eyes', 'open')
    glow = g('glow', 1.0 if ch.coloured_eyes else 0.0)
    ew = R * 0.40 * g('eye_k', 1.0)
    eh = {'open': 0.13, 'narrow': 0.06, 'closed': 0.0, 'wide': 0.19}[eyes] * R * g('eye_k', 1.0)
    brow = g('brow', 0.0)
    lst = [(-1, 0.0, 1.0), (1, 0.0, 1.0)]
    if ch.four_eyes:
        lst += [(-1, -0.32, 0.6), (1, -0.32, 0.6)]
    for (sx, dy, sc) in lst:
        if abs(face) > 0.75 and sx * face < 0 and sc == 1.0 and abs(face) > 0.9:
            continue
        e = ecx + rt * sx * sep * (0.85 if sc < 1 else 1.0) + upv * dy * R
        w_, h_ = ew * sc * (1 - 0.3 * abs(face)), eh * sc
        tilt = sx * math.radians(12 if ch.four_eyes else 4) + math.radians(-brow * 6 * sx)
        u1 = rt * math.cos(tilt) + upv * math.sin(tilt)
        u2 = upv * math.cos(tilt) - rt * math.sin(tilt)
        if eyes == 'closed' or h_ < 1.0:
            _chain(c, [e - u1 * w_ / 2, e - u2 * w_ * 0.08, e + u1 * w_ / 2], max(2.0, R * 0.05), PAPER, a)
            continue
        pts = []
        for i in range(9):
            u = -1 + 2 * i / 8
            pts.append(e + u1 * (u * w_ / 2) + u2 * (h_ * (1 - u * u)))
        for i in range(9):
            u = 1 - 2 * i / 8
            pts.append(e + u1 * (u * w_ / 2) - u2 * (h_ * 0.8 * (1 - u * u)))
        path = poly_path(pts, closed=True)
        if ch.coloured_eyes and glow > 0:
            c.drawPath(path, paint(ch.eye, a))
            core = [(p - e) * 0.55 + e for p in pts]
            c.drawPath(poly_path(core, closed=True), paint(ch.eye_core, a))
            fr.g.drawPath(path, paint(ch.eye, 0.12 * glow * a, k=4.0, add=True, blur=max(2.0, w_ * 0.25)))
        else:
            c.drawPath(path, paint(PAPER, a))
        # brow: a paper stroke above the eye, slanting down toward the nose when angry
        if abs(brow) > 0.05 and sc == 1.0:
            # inner end (toward the nose) drops when angry, rises when worried
            inner = e - rt * sx * w_ * 0.55 + upv * (h_ + R * 0.13 - brow * R * 0.11)
            outer = e + rt * sx * w_ * 0.55 + upv * (h_ + R * 0.13 + brow * R * 0.07)
            _chain(c, [inner, outer], max(2.0, R * 0.08), PAPER, a)
    if ch.marks:
        for sx in (-1, 1):
            e = ecx + rt * sx * sep
            m0 = e - upv * R * 0.12 + rt * sx * R * 0.05
            _chain(c, [m0, m0 - upv * R * 0.35 + rt * sx * R * 0.05], max(1.5, R * 0.035), (0.75, 0.1, 0.12), a)
    mouth = g('mouth', 'none')
    if mouth != 'none':
        m = Hc + rt * face * R * 0.40 - upv * R * 0.48
        mw = R * 0.34 * (1 - 0.35 * abs(face))
        lw = max(2.0, R * 0.06)
        if mouth == 'flat':
            _chain(c, [m - rt * mw / 2, m + rt * mw / 2], lw, PAPER, a)
        elif mouth == 'smile':
            _chain(c, [m - rt * mw / 2 + upv * R * 0.06, m - upv * R * 0.04, m + rt * mw / 2 + upv * R * 0.06], lw, PAPER, a)
        elif mouth == 'frown':
            _chain(c, [m - rt * mw / 2 - upv * R * 0.05, m + upv * R * 0.04, m + rt * mw / 2 - upv * R * 0.05], lw, PAPER, a)
        elif mouth == 'grit':
            pts = [m - rt * mw / 2 + upv * R * 0.05, m + rt * mw / 2 + upv * R * 0.05, m + rt * mw / 2 - upv * R * 0.07, m - rt * mw / 2 - upv * R * 0.07]
            c.drawPath(poly_path(pts, closed=True), paint(PAPER, a))
            for i in range(1, 4):
                x = m - rt * mw / 2 + rt * mw * i / 4
                _chain(c, [x + upv * R * 0.05, x - upv * R * 0.07], max(1.0, lw * 0.4), INK, a)
        elif mouth in ('open', 'shout'):
            k = 1.0 if mouth == 'open' else 1.6
            c.save()
            c.translate(float(m[0]), float(m[1]))
            c.rotate(math.degrees(math.atan2(rt[1], rt[0])))
            c.drawOval(skia.Rect(-mw * 0.45 * k, -R * 0.09 * k, mw * 0.45 * k, R * 0.13 * k), paint(PAPER, a))
            c.restore()


def _extras(c, J, pose, ch, colr, a):
    g = pose.g
    Hc = J['H']
    R = J['L']['head'] * g('k_head', 1.0)
    upv = -_dir(J['head_ang'])
    rt = np.array([-upv[1], upv[0]])
    face = g('face', 0.0)
    if 'glasses' in ch.extras and not g('back', False):
        for sx in (-1, 1):
            e = Hc + rt * (face * R * 0.42 + sx * R * 0.40 * (1 - 0.45 * abs(face))) + upv * R * 0.08
            c.drawCircle(float(e[0]), float(e[1]), R * 0.2, paint(PAPER, a, stroke=max(1.5, R * 0.05)))
    if 'glasses' in ch.extras and g('back', False):
        e = Hc + rt * R * 0.95 + upv * R * 0.1
        _chain(c, [e, e + rt * R * 0.12], max(1.5, R * 0.05), colr, a)


def draw(fr, pose, ch, colr=None, a=1.0, t=0.0):
    """draw one stick figure (ink on the base layer, eye light on the light layer)"""
    colr = INK if colr is None else colr
    c = fr.b
    J = joints(pose)
    g = pose.g
    w = J['B'] * PROP['width'] * g('k_w', 1.0)
    hide = set(g('hide', ()))
    front = set(g('front', ('r_arm', 'r_leg')))
    limbs = []
    for s in 'lr':
        limbs.append((s + '_leg', [J['P'], J['K' + s], J['A' + s]], s))
        limbs.append((s + '_arm', [J['C'], J['E' + s], J['W' + s]], s))
    if a < 0.999:
        c.saveLayerAlpha(None, int(255 * a))
        a = 1.0

    def limb(name, pts, s):
        if name in hide:
            return
        _chain(c, pts, w * (g('kw_' + name, 1.0)), colr, a)
        if name.endswith('arm'):
            d = pts[2] - pts[1]
            d = d / (np.linalg.norm(d) + 1e-6)
            if g('hd' + s) is not None:
                d = _dir(g('hd' + s))
            _hand(c, pts[2], d, g('hand_' + s, 'fist'), J['B'] * 0.07 * g('hk_' + s, 1.0), w, colr, a, s)
        else:
            d = pts[2] - pts[1]
            d = d / (np.linalg.norm(d) + 1e-6)
            fd = g('foot' + s)
            if fd is None:
                side = 1.0 if g('face', 0.0) >= 0 else -1.0
                fdir = np.array([side, 0.0]) * 0.85 + d * 0.5
            else:
                fdir = _dir(fd)
            fdir = fdir / (np.linalg.norm(fdir) + 1e-6)
            _chain(c, [pts[2], pts[2] + fdir * J['L']['foot'] * g('k_foot' + s, 1.0)], w, colr, a)

    for (name, pts, s) in limbs:
        if name not in front:
            limb(name, pts, s)
    if 'torso' not in hide:
        _chain(c, [J['P'], J['C'], J['N']], w * 1.1, colr, a)
    if 'head' not in hide:
        _head(c, J, pose, ch, colr, a)
    for (name, pts, s) in limbs:
        if name in front:
            limb(name, pts, s)
    if 'head' not in hide:
        _extras(c, J, pose, ch, colr, a)
        _face(fr, J, pose, ch, a, t)
    if g('a', 1.0) < 0.999:
        c.restore()
    return J
