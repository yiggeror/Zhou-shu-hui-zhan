"""Frame buffers (float, HDR) and skia paint helpers.
B = base picture (opaque things), G = emissive light (added on top, blooms)."""
import numpy as np
import skia

W, H = 1920, 1080


class Frame:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.B = np.zeros((h, w, 4), np.float32)
        self.G = np.zeros((h, w, 4), np.float32)
        self.sB = skia.Surface(self.B, colorType=skia.kRGBA_F32_ColorType, alphaType=skia.kPremul_AlphaType)
        self.sG = skia.Surface(self.G, colorType=skia.kRGBA_F32_ColorType, alphaType=skia.kPremul_AlphaType)
        self.b = self.sB.getCanvas()
        self.g = self.sG.getCanvas()
        self.post = []      # callables(img)->img applied after compositing (impact frames etc.)
        self.bloom = 1.0
        self.exposure = 1.0
        self.impact = None   # dict(mode='bw'|'inv', bg=, fg=, energy=True) -> two-tone impact frame

    def blur_layers(self, dx, dy, k=1.0):
        """directional blur of what has been drawn so far (e.g. the set during a fast pan,
        before the characters are drawn on top)"""
        from .fx import whip_blur
        dx, dy = dx * k, dy * k
        if abs(dx) + abs(dy) < 2:
            return
        fn = whip_blur(dx, dy)
        self.B[...] = fn(self.B)
        self.G[...] = fn(self.G)


def col(c, a=1.0, k=1.0):
    return skia.Color4f(float(c[0]) * k, float(c[1]) * k, float(c[2]) * k, float(a))


def paint(c=(1, 1, 1), a=1.0, k=1.0, stroke=None, cap='round', blur=0.0, add=False, erase=False, aa=True):
    p = skia.Paint(Color4f=col(c, a, k), AntiAlias=aa)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(float(stroke))
        p.setStrokeCap(skia.Paint.kRound_Cap if cap == 'round' else skia.Paint.kButt_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0.3:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, float(blur)))
    if add:
        p.setBlendMode(skia.BlendMode.kPlus)
    if erase:
        p.setBlendMode(skia.BlendMode.kDstOut)
    return p


def poly_path(pts, closed=False):
    p = skia.Path()
    p.moveTo(float(pts[0][0]), float(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(float(q[0]), float(q[1]))
    if closed:
        p.close()
    return p


def smooth_path(pts, closed=False):
    """quadratic smoothing through midpoints"""
    pts = [(float(x), float(y)) for x, y in pts]
    p = skia.Path()
    if len(pts) < 3:
        return poly_path(pts, closed)
    if closed:
        m0 = ((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)
        p.moveTo(*m0)
        for i in range(len(pts)):
            a = pts[i]; b = pts[(i + 1) % len(pts)]
            p.quadTo(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        p.close()
    else:
        p.moveTo(*pts[0])
        for i in range(1, len(pts) - 1):
            a = pts[i]; b = pts[i + 1]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            if i == len(pts) - 2:
                mx, my = b
            p.quadTo(a[0], a[1], mx, my)
    return p
