"""Opening reinterpretation pilot (~11 s, 1920x1080, 60 fps).

usage: pilot.py clean|neon OUTDIR
Each frame is built from a clean key drawing with rigid camera moves only (no
per-pixel tracking), then animated with procedural effects.
"""
import sys, os
import numpy as np, cv2
from fx import *

STYLE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FPS, DUR = 60, 11.0
NF = int(DUR * FPS)
DT = 1.0 / FPS

def ease(x):  # smootherstep
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3
def lin(a, b, x):
    return a + (b - a) * x

KEYS = ["S001", "S002", "S003A", "K001", "S003B", "S004"]
RAW = {k: asset(k) for k in KEYS}
MC = {k: energy_mask(RAW[k], "c") for k in KEYS}
MR = {k: energy_mask(RAW[k], "r") for k in KEYS}

def style(img):
    if STYLE == "neon":
        return neon(img)
    out = grade(img, sat=1.12)
    # keep white fabric from blooming: slight tone-down of highlights outside energy
    return out
BASE = {k: style(RAW[k]) for k in KEYS}
NX, NY = Noise(11), Noise(12)
CYAN = np.float32([1.0, 0.92, 0.35]); RED = np.float32([0.28, 0.22, 1.0]); WHITE = np.float32([1, 1, 1])
PURPLE = np.float32([1.0, 0.35, 0.85])

def pts_from_mask(m, thr=0.5):
    ys, xs = np.where(m > thr)
    return np.stack([xs, ys], 1).astype(np.float32)
EMIT = {k: (pts_from_mask(MC[k]), pts_from_mask(MR[k])) for k in KEYS}
CC = {k: centroid(MC[k]) for k in KEYS}; CR = {k: centroid(MR[k]) for k in KEYS}
def contact(k):
    return ((CC[k][0] + CR[k][0]) / 2, (CC[k][1] + CR[k][1]) / 2)

TITLE = np.load(os.path.join(os.path.dirname(__file__) or ".", "title_mask.npy"))
TITLE = cv2.dilate(TITLE.astype(np.uint8), np.ones((3, 3), np.uint8))
TPTS = pts_from_mask(TITLE.astype(np.float32))

embers = Particles(); sparks = Particles()
rng = np.random.default_rng(5)

def cam_matrix(zoom, cx, cy, rot, sh):
    M = cv2.getRotationMatrix2D((cx, cy), rot, zoom)
    M[0, 2] += (W / 2 - cx) + sh[0]; M[1, 2] += (H / 2 - cy) + sh[1]
    return M

def emit_embers(key, which, M, n, speed=(80, 260), col=None, spread=40):
    pts = EMIT[key][0 if which == "c" else 1]
    if len(pts) == 0 or n <= 0:
        return
    sel = pts[rng.integers(0, len(pts), n)]
    sel = (np.c_[sel, np.ones(n)] @ M.T).astype(np.float32)
    ang = rng.normal(-np.pi / 2, 0.55, n)
    sp = rng.uniform(*speed, n)
    vel = np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1) + rng.normal(0, spread, (n, 2))
    c = (CYAN if which == "c" else RED)[None] * rng.uniform(0.6, 1.2, (n, 1))
    embers.emit(sel, vel, c, rng.uniform(0.5, 1.4, n), rng.uniform(1.2, 2.6, n))

def swirl(p, t=0.0):
    # curl-ish wobble for embers
    return np.stack([np.sin(p[:, 1] / 57 + t * 3) * 140, np.cos(p[:, 0] / 63 + t * 2.3) * 90 - 60], 1).astype(np.float32)

def shot(key, t, zoom, cx, cy, rot, sh, amp, flow=(0, -1)):
    img = BASE[key]
    m = np.maximum(MC[key], MR[key])
    img = flame(img, m, t, NX, NY, amp=amp, flow=flow)
    M = cam_matrix(zoom, cx, cy, rot, sh)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT), M

# ---------------------------------------------------------------- data-art state
DATA = None
trail = np.zeros((H, W, 3), np.float32)

def init_data(snap, center):
    """sample particles mostly from characters and cursed energy, give each an orbit and a glyph target"""
    g = cv2.cvtColor(np.clip(snap, 0, 1).astype(np.float32), cv2.COLOR_BGR2GRAY)
    ink = np.clip((cv2.GaussianBlur(g, (0, 0), 3) - g) * 8, 0, 1)
    en = np.maximum(energy_mask(np.clip(snap, 0, 1), "c"), energy_mask(np.clip(snap, 0, 1), "r"))
    bright = np.clip((g - 0.6) * 3, 0, 1)
    w = 0.08 * (g + 0.02) + 2.0 * en + 1.2 * ink + 0.8 * bright
    w = w.ravel() / w.sum()
    n = 160000
    idx = rng.choice(len(w), n, p=w)
    ys, xs = np.divmod(idx, W)
    p = np.stack([xs, ys], 1).astype(np.float32) + rng.uniform(-0.5, 0.5, (n, 2)).astype(np.float32)
    c = np.clip(snap.reshape(-1, 3)[idx].astype(np.float32) * 1.3, 0, 1.6)
    b, r = c[:, 0], c[:, 2]
    kind = np.where(b > r + 0.1, 0, np.where(r > b + 0.1, 1, 2))
    d = p - np.float32(center)[None]
    dn = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-3)
    v = dn * rng.uniform(150, 1100, (n, 1)).astype(np.float32)
    u = rng.random(n).astype(np.float32)
    R = np.where(kind == 2, 400 + 300 * u, 50 + 370 * np.sqrt(u)).astype(np.float32)
    spin = np.float32([1.0, -1.0, 0.45])[kind]
    omega = spin * (1.6 + 3.2 * np.clip(1 - R / 450, 0, 1))
    phi0 = rng.uniform(0, 2 * np.pi, n).astype(np.float32)
    cen = np.float32([[W * 0.34, H * 0.52], [W * 0.66, H * 0.48], [W * 0.5, H * 0.5]])[kind]
    tgt = TPTS[rng.integers(0, len(TPTS), n)] + rng.normal(0, 0.8, (n, 2)).astype(np.float32)
    # two log-spiral arms per vortex (galaxy look); neutrals stay a loose ring
    arm = rng.integers(0, 2, n).astype(np.float32)
    arms = arm * np.pi + R * 0.02 * np.sign(spin) + rng.normal(0, 0.28, n).astype(np.float32)
    phi0 = np.where(kind == 2, phi0, arms).astype(np.float32)
    delay = (0.3 * rng.random(n)).astype(np.float32)
    return dict(p=p, v=v, c=c, c0=c.copy(), kind=kind, R=R, omega=omega, phi0=phi0, cen=cen, tgt=tgt, delay=delay)

def orbit_pos(D, t):
    ang = D["phi0"] + D["omega"] * (t - 6.45) + D["R"] * 0.011 * np.sign(D["omega"])
    return D["cen"] + np.stack([np.cos(ang) * D["R"], np.sin(ang) * D["R"] * 0.72], 1)

def step_data(D, t):
    if t < 6.45:                                    # shatter outward
        D["v"] *= 0.90
        D["p"] = D["p"] + D["v"] * DT
        return
    O = orbit_pos(D, t)
    pull = min(1.0, 7 * DT * (0.2 + 0.8 * ease((t - 6.45) / 0.4)))
    P_orbit = D["p"] + (O - D["p"]) * pull if t < 7.55 else O
    if t < 7.55:
        D["p"] = P_orbit
        return
    k = ease((t - 7.55 - D["delay"]) / 0.35)[:, None]
    goal = O * (1 - k) + D["tgt"] * k
    D["p"] = D["p"] + (goal - D["p"]) * (0.18 + 0.5 * k)      # lands fully before the reveal
    mix = ease((t - 7.7) / 0.5)
    D["c"] = D["c0"] * (1 - mix) + np.float32([0.98, 0.9, 1.0]) * mix

def render_data(D, gain=1.0):
    lay = np.zeros((H, W, 3), np.float32)
    p = D["p"]
    ok = (p[:, 0] >= 0) & (p[:, 0] < W - 1) & (p[:, 1] >= 0) & (p[:, 1] < H - 1)
    x = p[ok, 0].astype(np.int32); y = p[ok, 1].astype(np.int32)
    np.add.at(lay, (y, x), D["c"][ok] * gain)
    return lay

# ---------------------------------------------------------------- timeline
last = {}
for fi in range(NF):
    t = fi * DT
    img = np.zeros((H, W, 3), np.float32)
    bloom_s, chrom, fcx, fcy = 0.6, 0.0, W / 2, H / 2
    extra = np.zeros((H, W, 3), np.float32)

    if t < 0.5:                                             # ignition
        cx, cy = CC["S001"]
        if fi == 7:
            n = 900; ang = rng.uniform(0, 2 * np.pi, n); sp = rng.uniform(50, 600, n)
            embers.emit(np.tile([cx, cy], (n, 1)), np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1),
                        CYAN[None] * rng.uniform(0.6, 1.3, (n, 1)), rng.uniform(0.3, 1.0, n), 1.2)
        core = np.exp(-((XX - cx) ** 2 + (YY - cy) ** 2) / (2 * (8 + 140 * ease(t / 0.5)) ** 2))[..., None]
        img = core * CYAN * (0.2 + 1.2 * ease(t / 0.5))
        embers.step(DT, 0.95, (0, -40), lambda p: swirl(p, t))
        bloom_s = 1.5

    elif t < 2.10:                                          # cyan fist
        lt = (t - 0.5) / 1.6
        cx, cy = CC["S001"]
        z = lin(1.04, 1.16, ease(lt)); ccx = lin(W / 2, cx, 0.35); ccy = lin(H / 2, cy, 0.35)
        sh = shake(t, 11 * ease((lt - 0.75) / 0.25))
        img, M = shot("S001", t, z, ccx, ccy, -1.5 * lt, sh, 9 + 9 * lt)
        emit_embers("S001", "c", M, int(60 + 120 * lt))
        embers.step(DT, 0.97, (0, -60), lambda p: swirl(p, t))
        fade = ease((t - 0.5) / 0.18)
        img = img * fade + (1 - fade) * 0.0
        if t < 0.62:
            img = img * (1 + 0.8 * (1 - (t - 0.5) / 0.12))
        bloom_s = 0.7 + 1.0 * lt; chrom = 0.006 * ease((lt - 0.75) / 0.25)
        fcx, fcy = W / 2, H / 2
        last["S001"] = img

    elif t < 2.18:                                          # impact frames
        img = np.ones((H, W, 3), np.float32) if t < 2.10 + 2 * DT else impact(last["S001"], "bw", True, 0.35)
        bloom_s = 0.2
        embers.step(DT, 0.97, (0, -60), lambda p: swirl(p, t))

    elif t < 3.70:                                          # red fist
        lt = (t - 2.18) / 1.52
        cx, cy = CR["S002"]
        z = lin(1.18, 1.05, ease(lt)); ccx = lin(W / 2, cx, 0.35); ccy = lin(H / 2, cy, 0.35)
        sh = shake(t, 4 + 12 * ease((lt - 0.8) / 0.2), seed=2)
        img, M = shot("S002", t, z, ccx, ccy, 1.5 * lt, sh, 10 + 8 * lt)
        emit_embers("S002", "r", M, int(70 + 110 * lt), speed=(120, 320))
        embers.step(DT, 0.97, (0, -80), lambda p: swirl(p, t))
        if lt > 0.8:
            a = ease((lt - 0.8) / 0.2)
            extra += speed_lines(W / 2, H / 2, t, n=120, inner=380) * 0.55 * a
        bloom_s = 0.8 + 0.8 * lt; chrom = 0.008 * ease((lt - 0.8) / 0.2)
        last["S002"] = img

    elif t < 3.80:                                          # whip zoom transition
        lt = (t - 3.70) / 0.10
        if lt < 0.5:
            img = zoom_blur(last["S002"], W / 2, H / 2, 0.45 * ease(lt / 0.5), n=9)
        else:
            a, _ = shot("S003A", t, 1.08, W / 2, H / 2, 0, (0, 0), 10)
            img = zoom_blur(a, W / 2, H / 2, 0.45 * (1 - ease((lt - 0.5) / 0.5)), n=9)
        extra += speed_lines(W / 2, H / 2, t, n=160, inner=200) * 0.7
        embers.step(DT, 0.9, (0, 0))
        bloom_s = 1.0

    elif t < 4.55:                                          # top-down approach
        lt = (t - 3.80) / 0.75
        c = contact("S003A")
        z = lin(1.08, 1.17, ease(lt)) + 0.06 * ease((lt - 0.8) / 0.2)
        sh = shake(t, 3 + 9 * ease((lt - 0.7) / 0.3), seed=3)
        img, M = shot("S003A", t, z, lin(W / 2, c[0], 0.3), lin(H / 2, c[1], 0.3), 2.5 * lt, sh, 12)
        emit_embers("S003A", "c", M, 70, speed=(60, 200)); emit_embers("S003A", "r", M, 70, speed=(60, 200))
        embers.step(DT, 0.96, (0, -30), lambda p: swirl(p, t))
        if fi % 5 == 0 and rng.random() < 0.6:
            for key_c, col in ((CC["S003A"], CYAN), (CR["S003A"], RED)):
                p0 = (np.c_[np.float32([key_c]), [[1]]] @ M.T)[0]
                ang = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 260)
                extra += draw_bolts(lightning(p0, p0 + [np.cos(ang) * L, np.sin(ang) * L], int(t * 1000) + int(col[0] * 10), depth=5, branches=1), tuple(float(x) for x in col), 1, 6) * 0.8
        bloom_s = 1.0; chrom = 0.004 * lt
        last["S003A"] = img

    elif t < 5.60:                                          # CLASH
        c = contact("K001")
        if t < 4.55 + 2 * DT:
            img = np.ones((H, W, 3), np.float32); bloom_s = 0
        elif t < 4.55 + 5 * DT:
            img = impact(BASE["K001"], "red", True, 0.4); bloom_s = 0.2
        else:
            lt = (t - (4.55 + 5 * DT)) / (5.60 - 4.55 - 5 * DT)
            if "clash" not in last:
                last["clash"] = True
                n = 5000; ang = rng.uniform(0, 2 * np.pi, n); sp = rng.uniform(250, 2200, n)
                col = np.where(rng.random((n, 1)) < 0.5, CYAN[None], RED[None]) * rng.uniform(0.7, 1.5, (n, 1))
                col[rng.random(n) < 0.15] = WHITE * 1.3
                sparks.emit(np.tile(c, (n, 1)), np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1), col, rng.uniform(0.25, 1.1, n), rng.uniform(0.8, 2.0, n))
            ze = eout(lt / 0.55)
            z = lin(1.30, 1.0, ze)
            sh = shake(t, 30 * (1 - ease(lt / 0.7)), seed=4)
            img, M = shot("K001", t, z, c[0], c[1], 4 * (1 - ze), sh, 14)
            cs = (np.c_[np.float32([c]), [[1]]] @ M.T)[0]
            rad = 1700 * eout(lt / 0.6)
            img, ring = shockwave(img, cs[0], cs[1], rad, 70, 34 * (1 - ease(lt / 0.6)))
            extra += ring * np.float32([1.0, 0.9, 1.0]) * 1.4 * (1 - ease(lt / 0.6))
            if lt < 0.5 and fi % 2 == 0:
                for j in range(4):
                    ang = rng.uniform(0, 2 * np.pi); L = rng.uniform(300, 800)
                    col = CYAN if j % 2 == 0 else RED
                    extra += draw_bolts(lightning(cs, cs + [np.cos(ang) * L, np.sin(ang) * L], fi * 10 + j), tuple(float(x) for x in col), 2, 9) * (1 - lt / 0.5)
            emit_embers("K001", "c", M, 60); emit_embers("K001", "r", M, 60)
            bloom_s = 0.9 + 1.4 * (1 - ease(lt / 0.5)); chrom = 0.016 * (1 - ease(lt / 0.5))
            fcx, fcy = cs
            last["K001"] = img
        sparks.step(DT, 0.93, (0, 120)); embers.step(DT, 0.96, (0, -40), lambda p: swirl(p, t))

    elif t < 6.10:                                          # pull back to wide
        lt = (t - 5.60) / 0.5
        c = contact("S003B")
        img, M = shot("S003B", t, lin(1.14, 1.0, eout(lt)), c[0], c[1], lin(1.5, 0, eout(lt)), shake(t, 3, 5), 12)
        if lt < 0.25:
            a = ease(lt / 0.25); img = last["K001"] * (1 - a) + img * a
        emit_embers("S003B", "c", M, 40); emit_embers("S003B", "r", M, 40)
        sparks.step(DT, 0.93, (0, 120)); embers.step(DT, 0.96, (0, -40), lambda p: swirl(p, t))
        bloom_s = 0.9
        last["S003B"] = img

    elif t < 8.40:                                          # data-art: shatter -> twin vortices -> title
        if DATA is None:
            snap = np.clip(last["S003B"], 0, 1.2)
            DATA = init_data(snap, contact("S003B"))
        step_data(DATA, t)
        conv = ease((t - 7.6) / 0.55)
        decay = 0.86 * (1 - conv) + 0.55 * conv
        trail = trail * decay + render_data(DATA, 0.5)
        # soft saturation: dense regions glow white without clipping into a slab
        img = (1 - np.exp(-trail * (1.1 - 0.5 * conv))) * 1.15
        diss = 1 - ease((t - 6.10) / 0.3)
        if diss > 0:
            img = img * (1 - diss) + np.clip(last["S003B"], 0, 1.2) * diss
        if t > 8.18:                                        # formed title: brief pulse before the reveal
            img = img * (1 + 0.5 * np.sin((t - 8.18) / 0.22 * np.pi))
        sparks.step(DT, 0.93, (0, 120)); embers.step(DT, 0.94, (0, -40))
        bloom_s = 1.6 * (1 - conv) + 0.5 * conv; fcx, fcy = W / 2, H / 2

    else:                                                   # title
        lt = (t - 8.40) / 2.6
        img, M = shot("S004", t, lin(1.0, 1.06, ease(lt)), W / 2, H / 2 - 20, 0, shake(t, 2 * (1 - lt), 6), 4)
        if t < 8.40 + 2 * DT:
            img = np.ones((H, W, 3), np.float32)
        elif t < 8.75:
            a = ease((t - 8.43) / 0.32)
            trail = trail * 0.55 + render_data(DATA, 0.5)
            trail_img = (1 - np.exp(-trail * 0.6)) * 1.15
            img = trail_img * (1 - a) + img * a
        if fi % 2 == 0:
            n = 25; pos = np.stack([rng.uniform(0, W, n), rng.uniform(H * 0.55, H, n)], 1)
            embers.emit(pos, np.stack([rng.normal(0, 30, n), rng.uniform(-160, -60, n)], 1), PURPLE[None] * rng.uniform(0.5, 1.1, (n, 1)), rng.uniform(1.0, 2.2, n), 1.0)
        embers.step(DT, 0.99, (0, -10), lambda p: swirl(p, t) * 0.3)
        tg = cv2.GaussianBlur(TITLE.astype(np.float32), (0, 0), 14)[..., None]
        extra += tg * np.float32([0.6, 0.3, 1.0]) * (0.25 + 0.2 * np.sin(t * 5))
        bloom_s = 0.8
        fade = 1 - ease((t - 10.4) / 0.6)
        img = img * fade; extra = extra * fade

    # -------- compositing
    out = img + extra + embers.render(glow=4.0, gain=1.4) + sparks.render(glow=5, gain=1.2)
    if chrom > 0:
        out = chroma(out, fcx, fcy, chrom * 0.65)
    out = bloom(out, 0.8 if STYLE == "clean" else 0.55, bloom_s * (0.55 if STYLE == "clean" else 0.7))
    if STYLE == "clean":
        out = grade(out, gamma=1.04, gain=1.02)
    out = finish(out, grain=0.03, vignette=0.4, t=t)
    cv2.imwrite(f"{OUT}/f{fi:04d}.jpg", to8(out), [cv2.IMWRITE_JPEG_QUALITY, 94])
    if fi % 60 == 0:
        print(STYLE, fi, round(t, 2), flush=True)
print("done", STYLE)
