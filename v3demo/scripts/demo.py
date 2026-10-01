"""v3 demo compositor: crisp drawings + bold effects, slow motion on the fight.
usage: demo.py clean|neon OUTDIR"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, S + "/pilot"); sys.path.insert(0, S + "/full")
import numpy as np, cv2
from fx import (W, H, XX, YY, Noise, Particles, camera, shake, zoom_blur, chroma, shockwave, bloom,
                speed_lines, lightning, draw_bolts, finish, to8, energy_mask, grade, impact)
from dsched import *
STYLE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
if STYLE == "neon":
    from nstyle import neon2
DT = 1.0 / FPS
rng = np.random.default_rng(5)
CYAN = np.float32([1.0, 0.92, 0.35]); RED = np.float32([0.3, 0.25, 1.0]); WHITE = np.float32([1, 1, 1])
NX, NY = Noise(31), Noise(32)

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3

def load(key):
    img = cv2.imread(f"{HERE}/dbase/{key}.png").astype(np.float32) / 255
    f = np.load(f"{HERE}/dbase/{key}_fld.npy").astype(np.float32) * 4.0      # 960-scale px, 240x135 grid
    return img, f

def style(img):
    if STYLE == "neon":
        return neon2(img)[0]
    out = grade(img, sat=1.12)
    return np.clip((out - 0.5) * 1.06 + 0.5, 0, None)       # a touch more punch, nothing soft

def masks(img):
    return energy_mask(img, "c"), energy_mask(img, "r")

def centroid(m):
    s = float(m.sum())
    return None if s < 50 else (float((m * XX).sum() / s), float((m * YY).sum() / s))

def sample(weight, n):
    w = cv2.resize(weight, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
    if n <= 0 or w.sum() <= 1e-6:
        return np.zeros((0, 2), np.float32)
    w /= w.sum(); idx = rng.choice(len(w), n, p=w); ys, xs = np.divmod(idx, 240)
    return (np.stack([xs, ys], 1) * 8 + rng.uniform(0, 8, (n, 2))).astype(np.float32)

def par_lines(vx, vy, t, n=80, color=(1.0, 0.95, 1.0)):
    r = np.random.default_rng(int(t * 60) + 9)
    lay = np.zeros((H, W, 3), np.float32)
    d = np.array([vx, vy]); d = d / (np.linalg.norm(d) + 1e-6); nrm = np.array([-d[1], d[0]])
    for _ in range(n):
        c = np.array([W / 2, H / 2]) + nrm * r.uniform(-1200, 1200) + d * r.uniform(-900, 900)
        L = r.uniform(250, 1000); p0 = c - d * L / 2; p1 = c + d * L / 2
        cv2.line(lay, tuple(int(v) for v in p0), tuple(int(v) for v in p1), color, int(r.integers(1, 3)), cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 1.0)

HIT_T = [(t_of_tau(tau), kind) for tau, kind in HITS]
embers, sparks = Particles(), Particles()
trailE = None; prev_f = None; prev_seg = None; hit_xy = {}
for fi in range(NF):
    t = fi * DT
    si, x = seg_at(t); d, kind, ta, tb = SEG[si]
    extra = np.zeros((H, W, 3), np.float32)
    zoom, sh, chrom, bl = 1.0, (0.0, 0.0), 0.0, 1.0
    if si != prev_seg:
        trailE = None; prev_f = None
        if kind != "act":
            embers = Particles()
    if kind == "act":
        img, f = load(f"f{fi:04d}")
        vel = np.zeros_like(f) if prev_f is None else -(f - prev_f) * 2.0        # 1080p px per output frame
        prev_f = f
        mc, mr = masks(img)
        E = np.maximum(mc, mr)
        if E.mean() > 0.001:
            m = cv2.GaussianBlur(cv2.dilate(E, np.ones((25, 25), np.uint8)), (0, 0), 12)
            dx = NX.field(t * 1.6, (0, -1), 120) * 9 * m; dy = (NY.field(t * 1.6 + 3.1, (0, -1), 120) - 1.0) * 9 * m
            img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        sty = style(img)
        energy = img * E[..., None]
        trailE = energy * 0.5 if trailE is None else trailE * 0.86 + energy * 0.42
        sty = sty + np.maximum(trailE - energy * 1.6, 0) * 0.55                  # afterimage behind the moving fist
        sty = sty + cv2.GaussianBlur(energy, (0, 0), 22) * 0.3                   # energy lights its surroundings
        for mk, col in ((mc, CYAN), (mr, RED)):
            if mk.mean() > 0.001:
                pts = sample(mk ** 2, 70)
                if len(pts):
                    vv = np.stack([cv2.resize(vel[..., 0], (W // 8, H // 8))[np.clip((pts[:, 1] / 8).astype(int), 0, H // 8 - 1), np.clip((pts[:, 0] / 8).astype(int), 0, W // 8 - 1)],
                                   cv2.resize(vel[..., 1], (W // 8, H // 8))[np.clip((pts[:, 1] / 8).astype(int), 0, H // 8 - 1), np.clip((pts[:, 0] / 8).astype(int), 0, W // 8 - 1)]], 1) * FPS * 0.4
                    a = rng.normal(-np.pi / 2, 0.8, len(pts)); sp = rng.uniform(80, 320, len(pts))
                    embers.emit(pts, vv + np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), col[None] * rng.uniform(0.7, 1.4, (len(pts), 1)), rng.uniform(0.3, 0.9, len(pts)), rng.uniform(0.9, 1.8, len(pts)))
        # speed streaks while the energy is moving fast
        if E.mean() > 0.001:
            ev = np.array([(vel[..., 0] * cv2.resize(E, (240, 135))).sum(), (vel[..., 1] * cv2.resize(E, (240, 135))).sum()]) / (cv2.resize(E, (240, 135)).sum() + 1e-6)
            spd = float(np.hypot(*ev))
            if spd > 10:
                extra += par_lines(ev[0], ev[1], t, n=50) * float(np.clip((spd - 10) / 25, 0, 0.4))
        out = sty
        # ---- hits
        for k, (th, hk) in enumerate(HIT_T):
            if th is None or not (0 <= t - th < 0.7):
                continue
            dt = t - th; col = CYAN if hk == "c" else RED
            if k not in hit_xy:
                c = centroid(mc if hk == "c" else mr) or (W / 2, H / 2)
                hit_xy[k] = c
                n = 3500; a = rng.uniform(0, 2 * np.pi, n); sp = rng.uniform(300, 2200, n)
                cc = np.where(rng.random((n, 1)) < 0.35, WHITE[None] * 1.4, col[None] * rng.uniform(0.8, 1.5, (n, 1)))
                sparks.emit(np.tile(c, (n, 1)), np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.25, 0.9, n), rng.uniform(0.9, 2.2, n))
            c = hit_xy[k]
            if dt < 2 * DT:
                out = out * 0.2 + 0.95
            elif dt < 5 * DT:
                two = impact(sty, "bw", True, 0.42)
                out = two * (col if hk == "r" else np.float32([1.0, 0.9, 0.55])) + (1 - two) * np.float32([0.03, 0.0, 0.05])
            out, ring = shockwave(out, c[0], c[1], 1800 * eout(dt / 0.6), 80, 40 * (1 - ease(dt / 0.6)))
            extra += ring * col * 1.6 * (1 - ease(dt / 0.6))
            if dt < 0.3:
                extra += speed_lines(c[0], c[1], t, n=140, inner=200, color=tuple(float(v) for v in (WHITE * 0.6 + col * 0.4))) * 0.8 * (1 - dt / 0.3)
            if dt < 0.4 and fi % 2 == 0:
                for j in range(3):
                    a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 650)
                    extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), fi * 7 + j), tuple(float(v) for v in col), 2, 9) * (1 - dt / 0.4)
            sh = shake(t, 26 * (1 - ease(dt / 0.5)), 3)
            zoom *= 1 + 0.06 * (1 - eout(dt / 0.35))
            chrom = max(chrom, 0.014 * (1 - ease(dt / 0.4))); bl += 1.0 * (1 - ease(dt / 0.4))
    elif kind == "whip":
        A = style(load(f"e{si:02d}a")[0]); B = style(load(f"e{si:02d}b")[0])
        out = zoom_blur(A, W / 2, H / 2, 0.45 * ease(x / 0.5), 9) if x < 0.5 else zoom_blur(B, W / 2, H / 2, 0.45 * (1 - ease((x - 0.5) / 0.5)), 9)
        out = out + np.float32([1, 0.95, 1]) * 0.6 * float(np.exp(-((x - 0.5) / 0.15) ** 2))
        extra += speed_lines(W / 2, H / 2, t, n=170, inner=220) * 0.7; bl = 1.3
    else:                                                       # black body-wipe with a glowing edge
        A = style(load(f"e{si:02d}a")[0]); B = style(load(f"e{si:02d}b")[0])
        edge = -300 + (W + 600) * ease(x)
        sx = XX + (YY - H / 2) * 0.35
        k1 = np.clip((sx - edge) / 3, 0, 1)[..., None]              # right of the edge: old shot
        k2 = np.clip((edge - 260 - sx) / 3, 0, 1)[..., None]        # trailing edge reveals the new shot
        out = A * k1 + B * k2
        glow = np.exp(-((sx - edge) / 6) ** 2) + np.exp(-((sx - edge + 260) / 6) ** 2)
        extra += glow[..., None] * CYAN * 1.4
    prev_seg = si
    embers.step(DT, 0.95, (0, -60)); sparks.step(DT, 0.955, (0, 140))
    if len(embers.p):
        extra += embers.render(glow=3.5, gain=1.2)
    if len(sparks.p):
        extra += sparks.render(glow=5.0, gain=1.3)
    out = out + extra
    if zoom != 1.0 or sh != (0.0, 0.0):
        out = camera(out, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
    if chrom > 0:
        out = chroma(out, W / 2, H / 2, chrom * 0.5)
    out = bloom(out, 0.85 if STYLE == "clean" else 0.65, bl * (0.45 if STYLE == "clean" else 0.5))
    out = finish(out, grain=0.012, vignette=0.32, t=t)
    cv2.imwrite(f"{OUT}/f{fi:04d}.png", to8(out))
    if fi % 60 == 0:
        print(STYLE, fi, flush=True)
print("done", STYLE)
