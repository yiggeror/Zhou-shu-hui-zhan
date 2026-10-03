"""Purple light shared by both Hollow Purples: the violet wash on the paper, the flash that
stays purple, the layered sphere of light, lit wisps and light shafts."""
import cv2
from films.common import *
from engine.env import Building, clip_poly_near


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


def wisp(c, x0, y0, x1, y1, w, colr, a):
    """a long thin lens-shaped streak of lit cloud"""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    p = skia.Path()
    p.moveTo(x0, y0)
    p.quadTo(mx + nx * 2, my + ny * 2, x1, y1)
    p.quadTo(mx - nx * 2, my - ny * 2, x0, y0)
    p.close()
    c.drawPath(p, paint(colr, a * 0.35, k=2.6, add=True, blur=max(1.0, w * 0.35)))


def sky_streaks(fr, q, scale, k, seed, n=36):
    """the sky lit by the purple: long wisps streaming out from the light, nearly level and
    leaning in toward it (they sit with the light, so they move with the camera)"""
    if k <= 0:
        return
    for i in range(n):
        side = -1 if hash01(seed, i, 1) < 0.5 else 1
        dx = side * (0.15 + 1.5 * hash01(seed, i, 2)) * scale
        dy = (hash01(seed, i, 3) - 0.62) * 0.75 * scale
        L = (0.35 + 1.1 * hash01(seed, i, 4)) * scale
        ang = math.atan2(dy * 0.35, dx) - 0.10
        cx, cy = q[0] + dx, q[1] + dy
        x0, y0 = cx - math.cos(ang) * L / 2, cy - math.sin(ang) * L / 2
        x1, y1 = cx + math.cos(ang) * L / 2, cy + math.sin(ang) * L / 2
        w = (4 + 12 * hash01(seed, i, 5)) * scale / 900
        wisp(fr.g, x0, y0, x1, y1, w, (0.95, 0.72, 1.0), k * (0.25 + 0.45 * hash01(seed, i, 6)))


def light_body(fr, x, y, rp, heat=1.0, ref=None):
    """the purple light itself: layered from a lavender-white heart through pink-lavender to a
    violet rim (never a flat white disc), a tight halo, and light on top that blooms.
    ref: once the sphere is bigger than the screen, its colour bands keep this size in pixels
    (white-lavender centre, violet toward the corners) instead of stretching off screen"""
    if rp < 0.5:
        return
    f = 1.0 if ref is None or rp <= ref else ref / rp
    fr.g.drawCircle(x, y, rp * 1.25, paint((0.62, 0.22, 1.0), 0.10 * heat, k=3.0, stroke=rp * 0.55, add=True, blur=rp * 0.3))
    pb = skia.Paint(AntiAlias=True)
    pb.setShader(skia.GradientShader.MakeRadial(
        skia.Point(x, y), rp,
        [col((1.0, 0.97, 1.0)), col((0.99, 0.92, 1.0)), col((0.95, 0.78, 1.0)), col((0.86, 0.55, 1.0)),
         col((0.74, 0.32, 0.98)), col((0.66, 0.22, 0.95), 0.0)],
        [0.0, 0.45 * f, 0.7 * f, 0.85 * f, 0.95 * f + 0.0001, 1.0]))
    fr.b.drawCircle(x, y, rp, pb)
    fr.g.drawCircle(x, y, rp * 0.72, paint((0.45, 0.36, 0.52), 0.06 * heat, k=8.0, add=True, blur=rp * 0.3))
    fr.g.drawCircle(x, y, rp * 0.9, paint((0.85, 0.55, 1.0), 0.08 * heat, k=4.0, stroke=max(2.0, rp * 0.05), add=True, blur=max(1.0, rp * 0.04)))


def god_rays(cx, cy, k, tint=(0.80, 0.50, 1.0), n=12, spread=0.28, thr=0.95):
    """light streaming out from the hottest part of the picture (radial smear away from the
    source), so it falls over the buildings in shafts"""
    def fn(img):
        if k <= 0:
            return img
        h, w = img.shape[:2]
        s = 4
        sw, sh = w // s, h // s
        sm = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA)
        lum = sm.max(-1)
        src = np.ascontiguousarray(np.clip(lum - thr, 0, None) * 3.0, np.float32)
        acc = np.zeros_like(src)
        c0, c1 = cx / s, cy / s
        for i in range(n):
            sc = 1.0 + spread * (i + 1) / n
            M = np.float32([[sc, 0, c0 * (1 - sc)], [0, sc, c1 * (1 - sc)]])
            acc += cv2.warpAffine(src, M, (sw, sh), borderMode=cv2.BORDER_CONSTANT)
        acc = cv2.GaussianBlur(acc / n, (0, 0), 1.2)
        acc = cv2.resize(acc, (w, h), interpolation=cv2.INTER_LINEAR)
        acc = acc[..., None]
        return img + acc * np.array(tint, np.float32) * k
    return fn


def ink_box(fr, cs, x0, x1, z0, z1, y0, y1, colr, grid=None):
    """flat silhouette of a block; grid=(colour, floor_h, bay_w) draws faint window lines on the
    face toward the camera (only for blocks right in front of the lens)"""
    cs_pos = cs.pos
    corners = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], np.float64)
    P = cs.proj_many(corners)
    if (P[:, 2] > 0.5).all():
        if P[:, 0].max() < -20 or P[:, 0].min() > W + 20 or P[:, 1].max() < -20 or P[:, 1].min() > H + 20:
            return
        hull = cv2.convexHull(P[:, :2].astype(np.float32)).reshape(-1, 2)
        path = poly_path(hull, closed=True)
        fr.b.drawPath(path, paint(colr, 1.0))
        fr.g.drawPath(path, paint((0, 0, 0), 1.0, erase=True))
    else:
        b = Building(x0, x1, z0, z1, y1 - y0, base=y0, ink=True, color=colr)
        for name, quad, nrm in b.faces():
            if np.dot(nrm, cs_pos - quad[0]) <= 0:
                continue
            Q = clip_poly_near(cs, quad, near=0.05)
            if Q is None:
                continue
            path = poly_path(Q, closed=True)
            fr.b.drawPath(path, paint(colr, 1.0))
            fr.g.drawPath(path, paint((0, 0, 0), 1.0, erase=True))
    if grid is not None and cs_pos[2] < z0:
        gc, fh, bw = grid
        d = max(0.3, z0 - cs_pos[2])
        wpx = max(1.0, 0.10 * cs.scale(d))
        y = y0 + fh
        while y < y1:
            seg = cs.clip_seg(V(x0, y, z0), V(x1, y, z0))
            if seg is not None:
                fr.b.drawLine(seg[0][0], seg[0][1], seg[1][0], seg[1][1], paint(gc, 0.9, stroke=wpx))
            y += fh
        x = x0 + bw
        while x < x1:
            seg = cs.clip_seg(V(x, y0, z0), V(x, y1, z0))
            if seg is not None:
                fr.b.drawLine(seg[0][0], seg[0][1], seg[1][0], seg[1][1], paint(gc, 0.9, stroke=wpx * 0.8))
            x += bw


def mixc3(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
