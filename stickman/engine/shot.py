"""Shot base class + Actor helper for keying many channels at once."""
import numpy as np
from .anim import Ch, TimeWarp
from .figure import FigDraw
from .canvas import Frame


class Actor:
    def __init__(self, fig):
        self.fig = fig
        self.d = FigDraw(fig)
        self.c = {}

    def k(self, t, ease='sm', **vals):
        for name, v in vals.items():
            ch = self.c.get(name)
            if ch is None:
                ch = self.c[name] = Ch()
                self.fig.set(**{name: ch})
            ch.key(t, v, ease)
        return self

    def ke(self, t, spec):
        """spec: dict name -> value or (value, ease)"""
        for name, v in spec.items():
            if isinstance(v, tuple) and len(v) == 2 and isinstance(v[1], str):
                self.k(t, v[1], **{name: v[0]})
            else:
                self.k(t, **{name: v})
        return self

    def at(self, t, name):
        return self.fig.g(name, t)

    def J(self, t):
        return self.fig.pose(t)


class Shot:
    t0 = 0.0
    t1 = 0.0
    name = ''

    def __init__(self):
        self.tw = TimeWarp()
        self.setup()

    def setup(self):
        pass

    def hitstop(self, t, frames=3, catch=None):
        h = frames / 60.0
        self.tw.add(t, h, catch if catch is not None else h * 2.0)

    def draw(self, fr, s):
        raise NotImplementedError

    def frame(self, t):
        """t = time on the original film timeline"""
        fr = Frame()
        self.draw(fr, t - self.t0)
        return fr


def draw_actors(fr, cam, s, tau, actors, shutter=1 / 75, **kw):
    """draw several actors far-to-near; smears sample earlier poses with matching cameras"""
    cs = cam.at(s)
    order = []
    for a in actors:
        J = a.fig.pose(tau)
        d = float(cs.to_cam(J['C'])[2])
        order.append((d, a))
    order.sort(key=lambda x: -x[0])
    for _, a in order:
        opts = dict(kw)
        opts.update(getattr(a, 'draw_opts', {}))
        for k_, v_ in list(opts.items()):
            if k_ in ('line_k', 'alpha', 'glow_k', 'smear') and callable(v_):
                opts[k_] = float(v_(s))
        a.d.draw(fr, cs, tau, cam_at=lambda tt: cam.at(s - (tau - tt)), shutter=shutter, **opts)
    return cs


def cam_motion(cam, s, pt=None, dist=12.0):
    """screen displacement (px per frame) of a world point (default: a point `dist` ahead)"""
    import numpy as np
    c1, c0 = cam.at(s), cam.at(s - 1 / 60)
    pt = pt if pt is not None else c1.pos + c1.f * dist
    p1, p0 = c1.proj(pt), c0.proj(pt)
    if not (np.isfinite(p1[0]) and np.isfinite(p0[0])):
        return 0.0, 0.0
    return p1[0] - p0[0], p1[1] - p0[1]


def set_blur(fr, cam, s, k=0.55, thresh=10.0, dist=14.0):
    """blur the set (already drawn) by the camera motion; characters drawn afterwards stay sharp"""
    dx, dy = cam_motion(cam, s, dist=dist)
    if abs(dx) + abs(dy) > thresh:
        fr.blur_layers(dx, dy, k)


def cam_blur(fr, cam, s, k=0.5, thresh=45.0, pt=None):
    """whole-frame blur only for real whip pans (camera rotating fast; tracking moves of the
    camera position do not count)"""
    from .fx import whip_blur
    dx, dy = cam_motion(cam, s, pt=pt, dist=400.0)
    if abs(dx) + abs(dy) > thresh:
        fr.post.insert(0, whip_blur(dx * k, dy * k))
