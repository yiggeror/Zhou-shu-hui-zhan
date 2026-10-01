"""Pilot v2: procedural effects riding on the continuous-motion base layer.

usage: pilot2.py clean|neon OUTDIR
Motion = source motion (sub-frame interpolated, speed-ramped); effects are
emitted from / anchored to what moves in each frame.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pipeline"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # fx.py
import numpy as np, cv2
from fx import *
from tsched import *
import basefrac as bf

STYLE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
BD = HERE + "/base"
DT = 1.0 / FPS
rng = np.random.default_rng(11)
CYAN = np.float32([1.0, 0.92, 0.35]); RED = np.float32([0.28, 0.22, 1.0]); WHITE = np.float32([1, 1, 1])
PURPLE = np.float32([1.0, 0.35, 0.85])
NX, NY = Noise(21), Noise(22)

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3

_bcache = {}
def base(key):
    if key not in _bcache:
        if len(_bcache) > 6:
            _bcache.pop(next(iter(_bcache)))
        img = cv2.imread(f"{BD}/{key}.jpg").astype(np.float32) / 255
        z = np.load(f"{BD}/{key}.npz")
        C = cv2.resize(z["C"].astype(np.float32), (W, H))
        vel = z["vel"].astype(np.float32) * 4.0          # 1080p px per source frame, at 480x270 grid
        _bcache[key] = (img, C, vel)
    return _bcache[key]

def style(img):
    return neon(img) if STYLE == "neon" else grade(img, sat=1.1)

def masks(img):
    return energy_mask(img, "c"), energy_mask(img, "r")

def ink_map(img):
    g = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY)
    return np.clip((cv2.GaussianBlur(g, (0, 0), 3) - g) * 8, 0, 1)

def sample_points(weight, n):
    w = cv2.resize(weight, (480, 270), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
    if w.sum() <= 0 or n <= 0:
        return np.zeros((0, 2), np.float32)
    w /= w.sum()
    idx = rng.choice(len(w), n, p=w)
    ys, xs = np.divmod(idx, 480)
    return (np.stack([xs, ys], 1) * 4 + rng.uniform(0, 4, (n, 2))).astype(np.float32)

def vel_at(vel, pts):
    x = np.clip((pts[:, 0] / 4).astype(np.int32), 0, 479); y = np.clip((pts[:, 1] / 4).astype(np.int32), 0, 269)
    return vel[y, x]

def dtau_frame(t):
    s = seg_at(t)
    return 0.0 if s[3] is None else (s[4] - s[3]) / (s[1] - s[0]) * DT

SRC_DT = 1 / 34.0                                       # mean source time between drawings

# ---------------------------------------------------------------- title: one crisp drawing, one camera
# Everything in the title (particle targets, glyph reveal, background wipe) lives in
# S004 anchor space and goes through the SAME camera matrix, so it can never double.
S4 = asset("S004")
GA = np.load(HERE + "/title_groups.npy").astype(np.float32)          # 0 呪 1 術 2 廻 3 戦 4 furigana (with outline)
GAB = np.stack([cv2.GaussianBlur(g, (0, 0), 16) for g in GA])
CORE = np.load(HERE + "/title_core_grp.npy")
LAND_G = np.float32([8.15, 8.40, 8.72, 9.00, 9.16])                 # glyph ignition times (left -> right)
cy_, cx_ = np.where(CORE >= 0)
TPTS = np.stack([cx_, cy_], 1).astype(np.float32); TGRP = CORE[cy_, cx_].astype(np.int32)
TC = TPTS.mean(0)
RD = np.hypot(XX - TC[0], YY - TC[1]).astype(np.float32)
T_WIPE = 9.22
def cam_M(t):
    """slow push-in through the title (the source camera also closes in), about frame centre"""
    s = 1.0 + 0.075 * ease((t - 7.80) / 1.7) + 0.035 * ease((t - 9.5) / 1.4)
    return np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]])

# procedural black blades closing over the title (the source closes with black shards)
BLADES = [  # (normal angle deg, offset from centre px, width px, start t, travel sign)
    (62, -380, 150, 9.86, 1), (-28, 300, 120, 9.93, -1), (14, -150, 210, 10.00, 1),
    (-71, 520, 260, 10.06, -1), (37, 120, 300, 10.12, 1), (-12, -330, 340, 10.18, -1),
    (81, -60, 420, 10.24, 1), (-48, 40, 600, 10.31, -1), (25, 260, 900, 10.38, 1),
    (-35, -300, 1100, 10.44, -1),
]
def blades(t):
    cover = np.zeros((H, W), np.float32); rim = np.zeros((H, W), np.float32)
    hits = 0
    for ang, off, w, ts, sg in BLADES:
        if t < ts:
            continue
        a = np.radians(ang); nx, ny = np.cos(a), np.sin(a)
        d = (XX - W / 2) * nx + (YY - H / 2) * ny - off            # across the blade
        s_ = ((XX - W / 2) * -ny + (YY - H / 2) * nx) * sg          # along the blade
        tip = -1250 + 2700 * eout((t - ts) / 0.17)
        along = np.clip((tip - s_) / 40.0, 0, 1)                    # leading edge (moving -> soft)
        band = np.clip((w / 2 - np.abs(d)) / 1.5 + 0.5, 0, 1) * along
        cover = np.maximum(cover, band)
        k = np.exp(-((np.abs(d) - w / 2) / 2.2) ** 2) * along * (1 - ease((t - ts - 0.05) / 0.35))
        rim = np.maximum(rim, k)
        hits += int(t - ts < DT * 1.5)
    return cover, rim, hits

# ---------------------------------------------------------------- particle field for pull/vortex/title
class Field:
    def __init__(self, cap=200000):
        self.p = np.zeros((0, 2), np.float32); self.c = np.zeros((0, 3), np.float32); self.kind = np.zeros(0, np.int8)
    def emit(self, pts, cols):
        b, r = cols[:, 0], cols[:, 2]
        kind = np.where(b > r + 0.1, 0, np.where(r > b + 0.1, 1, 2)).astype(np.int8)
        self.p = np.vstack([self.p, pts]); self.c = np.vstack([self.c, cols]); self.kind = np.concatenate([self.kind, kind])
    def setup_orbits(self, cen_c, cen_r):
        n = len(self.p); k = self.kind
        self.cen0 = np.where(k[:, None] == 0, np.float32(cen_c), np.where(k[:, None] == 1, np.float32(cen_r), np.float32([W / 2, H / 2]))).astype(np.float32)
        self.cen1 = np.float32([[W * 0.34, H * 0.52], [W * 0.66, H * 0.48], [W * 0.5, H * 0.5]])[k]
        u = rng.random(n).astype(np.float32)
        self.R = np.where(k == 2, 420 + 280 * u, 50 + 370 * np.sqrt(u)).astype(np.float32)
        spin = np.float32([1.0, -1.0, 0.45])[k]
        self.omega = spin * (1.6 + 3.2 * np.clip(1 - self.R / 450, 0, 1))
        d = self.p - self.cen0
        cur = np.arctan2(d[:, 1], d[:, 0]).astype(np.float32)
        arm = rng.integers(0, 2, n).astype(np.float32)
        armang = arm * np.pi + self.R * 0.02 * np.sign(spin) + rng.normal(0, 0.28, n).astype(np.float32)
        self.phi0 = np.where(k == 2, cur, armang).astype(np.float32)
        # left (cyan) galaxy pours into the left glyphs, right (red) galaxy into the right ones
        left = np.where(TPTS[:, 0] < TC[0])[0]; right = np.where(TPTS[:, 0] >= TC[0])[0]
        pick = np.where(k == 0, left[rng.integers(0, len(left), n)],
                        np.where(k == 1, right[rng.integers(0, len(right), n)], rng.integers(0, len(TPTS), n)))
        self.tgt = TPTS[pick] + rng.normal(0, 0.6, (n, 2)).astype(np.float32)
        self.land = LAND_G[TGRP[pick]] + rng.uniform(-0.14, 0.06, n).astype(np.float32)
        self.c0 = self.c.copy()
    def orbit(self, t):
        m = ease((t - 6.60) / 0.9)[..., None] if np.isscalar(t) else None
        cen = self.cen0 * (1 - m) + self.cen1 * m
        ang = self.phi0 + self.omega * (t - 6.60)
        return cen + np.stack([np.cos(ang) * self.R, np.sin(ang) * self.R * 0.72], 1)
    def render(self, gain):
        lay = np.zeros((H, W, 3), np.float32)
        ok = (self.p[:, 0] >= 0) & (self.p[:, 0] < W - 1) & (self.p[:, 1] >= 0) & (self.p[:, 1] < H - 1)
        np.add.at(lay, (self.p[ok, 1].astype(np.int32), self.p[ok, 0].astype(np.int32)), self.c[ok] * gain)
        return lay

embers = Particles(); sparks = Particles(); field = Field()
trailE = np.zeros((H, W, 3), np.float32); trailP = np.zeros((H, W, 3), np.float32)
last = {}; impact_done = False
T_IMP = 4.80 + (TAU_IMPACT - 1.226) / (1.236 - 1.226) * 0.30

def emit_embers(mask, col, n, speed=(70, 240)):
    pts = sample_points(mask ** 2, n)
    if len(pts) == 0:
        return
    m = len(pts); ang = rng.normal(-np.pi / 2, 0.6, m); sp = rng.uniform(*speed, m)
    vel = np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1) + rng.normal(0, 40, (m, 2))
    embers.emit(pts, vel, col[None] * rng.uniform(0.6, 1.25, (m, 1)), rng.uniform(0.5, 1.3, m), rng.uniform(1.1, 2.4, m))

def swirl(p, t):
    return np.stack([np.sin(p[:, 1] / 57 + t * 3) * 140, np.cos(p[:, 0] / 63 + t * 2.3) * 90 - 60], 1).astype(np.float32)

def fist_shot(key, t, lt, col_c, col_r, amp=7, flame_on=True):
    """styled base + living flames + energy afterimages + embers"""
    global trailE
    img, C, vel = base(key)
    mc, mr = masks(img)
    if flame_on:
        img = flame(img, np.maximum(mc, mr), t, NX, NY, amp=amp)
    sty = style(img)
    energy = img * np.maximum(mc, mr)[..., None]
    trailE = trailE * 0.82 + energy * 0.4
    sty = sty + np.maximum(trailE - energy * 1.8, 0) * 0.75      # afterimage behind the moving fist
    if col_c is not None: emit_embers(mc, col_c, int(40 + 90 * lt))
    if col_r is not None: emit_embers(mr, col_r, int(40 + 90 * lt), (100, 300))
    return sty, img, mc, mr

import pickle
SNAP = f"{HERE}/snap_{STYLE}.pkl"; SNAP_FI = 468
F_START = 0
if os.environ.get("RESUME") and os.path.exists(SNAP):
    with open(SNAP, "rb") as fh:
        st_ = pickle.load(fh)
    embers, sparks, field, trailE, trailP, last, impact_done = st_["state"]
    rng.bit_generator.state = st_["rng"]; F_START = SNAP_FI
for fi in range(F_START, NF):
    t = fi * DT
    if fi == SNAP_FI and F_START == 0:
        with open(SNAP, "wb") as fh:
            pickle.dump(dict(state=(embers, sparks, field, trailE, trailP, last, impact_done), rng=rng.bit_generator.state), fh)
    t0, t1, lab, ta, tb = seg_at(t)
    lt = (t - t0) / (t1 - t0)
    img = np.zeros((H, W, 3), np.float32); extra = np.zeros((H, W, 3), np.float32)
    bloom_s, chrom, fcx, fcy, cam_z, cam_sh = 0.6, 0.0, W / 2, H / 2, 1.0, (0.0, 0.0)
    key = f"f{fi:04d}"

    if lab == "ignite":
        b, _, _ = base("f0021")
        cx, cy = centroid(energy_mask(b, "c"))
        if fi == 6:
            n = 900; ang = rng.uniform(0, 2 * np.pi, n); sp = rng.uniform(50, 600, n)
            embers.emit(np.tile([cx, cy], (n, 1)), np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1), CYAN[None] * rng.uniform(0.6, 1.3, (n, 1)), rng.uniform(0.3, 1.0, n), 1.4)
        core = np.exp(-((XX - cx) ** 2 + (YY - cy) ** 2) / (2 * (8 + 160 * ease(lt)) ** 2))[..., None]
        img = core * CYAN * (0.2 + 1.2 * ease(lt)) + style(b) * ease((t - 0.22) / 0.13)
        embers.step(DT, 0.95, (0, -40), lambda p: swirl(p, t)); bloom_s = 1.3

    elif lab == "S001":
        sty, raw, mc, mr = fist_shot(key, t, lt, CYAN, None)
        img = sty
        cam_z = 1.0 + 0.05 * ease(lt); cam_sh = shake(t, 10 * ease((lt - 0.82) / 0.18))
        bloom_s = 0.7 + 0.8 * lt; chrom = 0.006 * ease((lt - 0.82) / 0.18)
        embers.step(DT, 0.97, (0, -60), lambda p: swirl(p, t))

    elif lab == "cut1":
        b, _, _ = base("tau_0.6350")
        img = np.ones((H, W, 3), np.float32) if fi < round(2.20 * FPS) + 2 else impact(style(b), "bw", True, 0.35)
        embers.step(DT, 0.97, (0, -60), lambda p: swirl(p, t)); bloom_s = 0.2; trailE *= 0.5

    elif lab == "S002":
        sty, raw, mc, mr = fist_shot(key, t, lt, None, RED, amp=8)
        img = sty
        cam_z = 1.04 - 0.04 * ease(lt); cam_sh = shake(t, 3 + 10 * ease((lt - 0.8) / 0.2), 2)
        if lt > 0.8:
            extra += speed_lines(W / 2, H / 2, t, n=120, inner=380) * 0.5 * ease((lt - 0.8) / 0.2)
        bloom_s = 0.7 + 0.7 * lt; chrom = 0.008 * ease((lt - 0.8) / 0.2)
        embers.step(DT, 0.97, (0, -80), lambda p: swirl(p, t))

    elif lab in ("whip", "jump"):
        a_key, b_key = f"tau_{ta:.4f}", f"tau_{tb:.4f}"
        A = style(base(a_key)[0]); B = style(base(b_key)[0])
        s = 0.5 if lab == "whip" else 0.3
        img = zoom_blur(A, W / 2, H / 2, s * ease(lt / 0.5), 9) if lt < 0.5 else zoom_blur(B, W / 2, H / 2, s * (1 - ease((lt - 0.5) / 0.5)), 9)
        extra += speed_lines(W / 2, H / 2, t, n=160, inner=220) * 0.65
        embers.step(DT, 0.9, (0, 0)); bloom_s = 0.9; trailE *= 0.6

    elif lab in ("S003a", "clash1", "clash2", "clash3", "pull"):
        flame_amp = 7
        sty, raw, mc, mr = fist_shot(key, t, 0.6, CYAN, RED, amp=flame_amp)
        img = sty
        cc, cr = centroid(mc), centroid(mr)
        contact = ((cc[0] + cr[0]) / 2, (cc[1] + cr[1]) / 2)
        bloom_s = 0.8
        if lab == "S003a":
            cam_z = 1.0 + 0.04 * ease(lt); cam_sh = shake(t, 2 + 4 * lt, 3)
            if fi % 5 == 0 and rng.random() < 0.6:
                for c0, col in ((cc, CYAN), (cr, RED)):
                    ang = rng.uniform(0, 2 * np.pi); L = rng.uniform(110, 240)
                    extra += draw_bolts(lightning(c0, (c0[0] + np.cos(ang) * L, c0[1] + np.sin(ang) * L), fi * 7 + int(col[0] * 9), depth=5, branches=1), tuple(float(x) for x in col), 1, 6) * 0.7
        if lab.startswith("clash"):
            dt_imp = t - T_IMP
            cam_z = 1.0 + 0.10 * ease((t - 4.42) / 0.5) * (1 - ease(dt_imp / 0.6))
            # anticipation: crackling arc between the two fists, tightening before contact
            if dt_imp < 0 and fi % 2 == 0:
                extra += draw_bolts(lightning(cc, cr, fi * 13, jag=0.25, depth=6, branches=2), (1.0, 0.75, 1.0), 2, 8) * ease((t - 4.5) / 0.4)
            if dt_imp >= 0:
                if not impact_done:
                    impact_done = True
                    n = 5000; ang = rng.uniform(0, 2 * np.pi, n); sp = rng.uniform(250, 2100, n)
                    col = np.where(rng.random((n, 1)) < 0.5, CYAN[None], RED[None]) * rng.uniform(0.7, 1.5, (n, 1))
                    col[rng.random(n) < 0.15] = WHITE * 1.3
                    sparks.emit(np.tile(contact, (n, 1)), np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1), col, rng.uniform(0.3, 1.2, n), rng.uniform(0.8, 2.0, n))
                    last["contact"] = contact
                cxy = last["contact"]
                if dt_imp < 2 * DT:
                    img = img * 0.15 + 1.0
                elif dt_imp < 4 * DT:
                    img = impact(sty, "red", True, 0.4) * 0.8 + img * 0.2
                img, ring = shockwave(img, cxy[0], cxy[1], 1700 * eout(dt_imp / 0.7), 70, 34 * (1 - ease(dt_imp / 0.7)))
                extra += ring * np.float32([1.0, 0.9, 1.0]) * 1.3 * (1 - ease(dt_imp / 0.7))
                if dt_imp < 0.55 and fi % 2 == 0:
                    for j in range(4):
                        ang = rng.uniform(0, 2 * np.pi); L = rng.uniform(300, 800)
                        extra += draw_bolts(lightning(cxy, (cxy[0] + np.cos(ang) * L, cxy[1] + np.sin(ang) * L), fi * 10 + j), tuple(float(x) for x in (CYAN if j % 2 == 0 else RED)), 2, 9) * (1 - dt_imp / 0.55)
                cam_sh = shake(t, 26 * (1 - ease(dt_imp / 0.8)), 4)
                bloom_s = 0.8 + 1.2 * (1 - ease(dt_imp / 0.5)); chrom = 0.016 * (1 - ease(dt_imp / 0.5))
                fcx, fcy = cxy
        if lab == "pull":
            # the image starts to shed particles that ride the measured motion
            _, C, vel = base(key)
            ramp = ease(lt)
            wgt = 3.0 * np.maximum(mc, mr) + 1.5 * ink_map(raw) + 0.05
            pts = sample_points(wgt, int(200 + 2600 * ramp))
            if len(pts):
                cols = np.clip(sty[np.clip(pts[:, 1].astype(int), 0, H - 1), np.clip(pts[:, 0].astype(int), 0, W - 1)] * 1.3, 0, 1.6)
                field.emit(pts, cols)
            if len(field.p):
                k = dtau_frame(t) / SRC_DT
                field.p += vel_at(vel, field.p) * k
                d = field.p - np.float32([W / 2, H / 2])
                field.p += np.stack([-d[:, 1], d[:, 0]], 1) * (0.012 * ramp) + d * (0.006 * ramp)
            trailP = trailP * 0.82 + field.render(0.45)
            img = img * (1 - 0.55 * ramp) + (1 - np.exp(-trailP * 1.1))
            last["cc"], last["cr"] = cc, cr
            last["pull_img"] = img
        embers.step(DT, 0.96, (0, -40), lambda p: swirl(p, t)); sparks.step(DT, 0.93, (0, 120))

    elif lab == "vortex":
        if not hasattr(field, "R"):
            field.setup_orbits(last["cc"], last["cr"])
        O = field.orbit(t)
        pull = min(1.0, 7 * DT * (0.25 + 0.75 * ease((t - 6.60) / 0.5)))
        field.p += (O - field.p) * pull
        trailP = trailP * 0.86 + field.render(0.45)
        img = 1 - np.exp(-trailP * 1.1)
        fade = 1 - ease((t - 6.60) / 0.35)
        if fade > 0:
            img = img + last["pull_img"] * fade * 0.45
        embers.step(DT, 0.94, (0, -40)); sparks.step(DT, 0.93, (0, 120)); bloom_s = 1.2

    elif lab == "title":
        M = cam_M(t)
        # glyph ignition: each glyph's own crisp pixels appear where its particles land
        A = np.zeros((H, W), np.float32); glow = np.zeros((H, W), np.float32)
        for g in range(5):
            A += GA[g] * float(ease((t - LAND_G[g] - 0.03) / 0.2))
            glow += GAB[g] * float(np.exp(-((t - LAND_G[g] - 0.06) / 0.11) ** 2))
            if LAND_G[g] <= t < LAND_G[g] + DT:                       # ignition sparks off the glyph
                sel = np.where(TGRP == g)[0]; sel = sel[rng.integers(0, len(sel), 700)]
                pp = (np.c_[TPTS[sel], np.ones(len(sel))] @ M.T).astype(np.float32)
                ang = rng.uniform(0, 2 * np.pi, len(sel)); sp = rng.uniform(60, 520, len(sel))
                col = np.where(rng.random((len(sel), 1)) < 0.5, WHITE[None] * 1.2, PURPLE[None])
                sparks.emit(pp, np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1), col, rng.uniform(0.25, 0.7, len(sel)), rng.uniform(0.8, 1.6, len(sel)))
                cam_sh = shake(t, 5, 7)
        # then the whole drawing is revealed by a ring of light expanding from the title
        xw = float(np.clip((t - T_WIPE) / 0.8, 0, 1)); R = 2300 * (1 - (1 - xw) ** 2) if t >= T_WIPE else 0.0
        wipe = np.clip((R - RD) / 70.0, 0, 1) if R > 0 else np.zeros((H, W), np.float32)
        alpha = np.maximum(A, wipe)
        ring = np.exp(-((RD - R) / 16.0) ** 2) * (1 - float(ease((t - T_WIPE) / 0.8))) if R > 0 else np.zeros((H, W), np.float32)
        comp = S4 * alpha[..., None]
        lit = glow[..., None] * np.float32([1.0, 0.8, 1.0]) * 0.9 + (ring * 1.4)[..., None] * np.float32([1.0, 0.85, 1.0])
        comp = cv2.warpAffine(comp, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        lit = cv2.warpAffine(lit.astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
        sty = style(comp) if (R > 0 or A.max() > 0) else np.zeros((H, W, 3), np.float32)
        # particles stream from the two galaxies into their glyphs, then hand over
        tg = (np.c_[field.tgt, np.ones(len(field.tgt))] @ M.T).astype(np.float32)
        O = field.orbit(t)
        k = ease((t - (field.land - 0.65)) / 0.65)[:, None]
        goal = O * (1 - k) + tg * k
        field.p += (goal - field.p) * (0.12 + 0.6 * k)
        mix = ease((t - field.land + 0.25) / 0.3)[:, None]
        field.c = field.c0 * (1 - mix) + np.float32([1.0, 0.92, 1.0]) * mix
        gain = 0.45 * (1 - ease((t - field.land - 0.02) / 0.3))[:, None]
        lay = np.zeros((H, W, 3), np.float32)
        ok = (gain[:, 0] > 1e-3) & (field.p[:, 0] >= 0) & (field.p[:, 0] < W - 1) & (field.p[:, 1] >= 0) & (field.p[:, 1] < H - 1)
        np.add.at(lay, (field.p[ok, 1].astype(np.int32), field.p[ok, 0].astype(np.int32)), (field.c * gain)[ok])
        trailP = trailP * 0.7 + lay
        parts = (1 - np.exp(-trailP * 1.0)) * 1.1
        if STYLE == "neon":                                  # neon bloom is hotter: keep the ignition from clipping
            parts = parts * 0.6; lit = lit * 0.6
        img = sty + lit + parts
        if t >= BLADES[0][3]:
            cover, rim, hits = blades(t)
            img = img * (1 - cover[..., None]) + rim[..., None] * np.float32([1.0, 0.8, 1.0]) * 1.6
            if hits:
                cam_sh = shake(t, 9, 5)
        if fi % 2 == 0:
            n = 22; pos = np.stack([rng.uniform(0, W, n), rng.uniform(H * 0.55, H, n)], 1)
            embers.emit(pos, np.stack([rng.normal(0, 30, n), rng.uniform(-160, -60, n)], 1), PURPLE[None] * rng.uniform(0.5, 1.1, (n, 1)), rng.uniform(1.0, 2.2, n), 1.0)
        embers.step(DT, 0.99, (0, -10), lambda p: swirl(p, t) * 0.3); sparks.step(DT, 0.9, (0, 60))
        bloom_s = 0.7

    else:                                                    # end
        img = np.zeros((H, W, 3), np.float32)
        embers.step(DT, 0.95, (0, -10))

    out = img + extra + embers.render(glow=4.0, gain=1.3) + sparks.render(glow=5, gain=1.2)
    if cam_z != 1.0 or cam_sh != (0.0, 0.0):
        out = camera(out, cam_z, W / 2, H / 2, 0.0, cam_sh, cv2.BORDER_REFLECT)
    if chrom > 0:
        out = chroma(out, fcx, fcy, chrom * 0.42)
    out = bloom(out, 0.8 if STYLE == "clean" else 0.55, bloom_s * (0.55 if STYLE == "clean" else 0.7))
    fade_end = 1 - ease((t - 10.55) / 0.4)
    out = finish(out * fade_end, grain=0.025, vignette=0.4, t=t)
    cv2.imwrite(f"{OUT}/f{fi:04d}.jpg", to8(out), [cv2.IMWRITE_JPEG_QUALITY, 94])
    if fi % 60 == 0:
        print(STYLE, fi, round(t, 2), flush=True)
print("done", STYLE)
