"""Full film, stage B: neon line-art look + effects over the cached continuous-motion base.

Timing contract: output frame n is time n/60 of the user's music edit and shows source
time tau = TMAP[n] (frame-matched against that edit), so every cut, flash and hit stays
where the song has it.  Effects only ever add to a frame; transitions are centred on the
cut frame itself; music accents use the song's own beat times.
usage: fxfull.py WORKER NWORKERS [first_n last_n]
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(HERE)
sys.path.insert(0, S + "/pilot"); sys.path.insert(0, HERE)
import numpy as np, cv2
from fx import (W, H, XX, YY, Noise, Particles, camera, shake, chroma, shockwave, bloom, speed_lines,
                lightning, draw_bolts, finish, to8, energy_mask, impact)
from nstyle import neon2, sstep

FPS = 60
DT = 1.0 / FPS
TMAP = np.load(HERE + "/tmap.npy"); NF = len(TMAP)
OUT = HERE + "/out"
os.makedirs(OUT, exist_ok=True)
units = json.load(open(S + "/work/units.json"))
TS = np.load(S + "/ts.npy")
EV = json.load(open(HERE + "/events.json"))            # authored + detected events (tau based)
for e in EV:                                           # ...converted to output frames
    e["n0"] = int(np.searchsorted(TMAP, e["t0"], side="left"))
    e["n1"] = max(e["n0"] + 1, int(np.searchsorted(TMAP, e["t1"], side="left")))
BEATS = np.array(json.load(open(HERE + "/beats.json"))["accents"], np.float32).reshape(-1, 2)   # (t_out, strength)

def first_frame(src_idx):
    return int(np.searchsorted(TMAP, TS[src_idx], side="left")) if src_idx < len(TS) else NF
U0 = [first_frame(u["start"]) for u in units] + [NF]

def cut_kind(text):
    if any(k in text for k in ("白闪", "全白", "白色叠化", "白线", "白斜线", "白色刃", "白场")):
        return "flash"
    if any(k in text for k in ("红黑", "反相", "冲击帧", "负片", "红爆", "插镜")):
        return "impact"
    if any(k in text for k in ("甩", "擦", "急推", "急拉", "扫", "穿", "急近", "速度模糊")):
        return "whip"
    if "叠化" in text:
        return "dissolve"
    return "cut"
CUT_IN = ["cut"] + [cut_kind(units[i]["transition"]) for i in range(len(units) - 1)]   # how unit i is entered

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3

def load_base(n):
    img = cv2.imread(f"{HERE}/base/n{n:04d}.jpg").astype(np.float32) / 255
    vel = np.load(f"{HERE}/base/n{n:04d}.npy").astype(np.float32) * 2.0     # 1080p px per source frame, 240x135 grid
    return img, vel

def vel_at(vel, p):
    x = np.clip((p[:, 0] / 8).astype(np.int32), 0, 239); y = np.clip((p[:, 1] / 8).astype(np.int32), 0, 134)
    return vel[y, x]

def sample(weight, n, rng):
    w = cv2.resize(weight, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
    if n <= 0 or w.sum() <= 1e-6:
        return np.zeros((0, 2), np.float32)
    w /= w.sum(); idx = rng.choice(len(w), n, p=w)
    ys, xs = np.divmod(idx, 240)
    return (np.stack([xs, ys], 1) * 8 + rng.uniform(0, 8, (n, 2))).astype(np.float32)

def centroid(m):
    s = m.sum()
    if s < 1e-3:
        return None
    return float((m * XX).sum() / s), float((m * YY).sum() / s)

def glitch(img, n, amt, rng):
    """horizontal slice displacement + RGB split (digital cut accent)"""
    out = img.copy()
    for _ in range(int(6 + 10 * amt)):
        y0 = int(rng.integers(0, H - 20)); h = int(rng.integers(8, 70)); dx = int(rng.normal(0, 45 * amt))
        out[y0:y0 + h] = np.roll(out[y0:y0 + h], dx, axis=1)
    s = int(6 + 14 * amt)
    out[..., 2] = np.roll(out[..., 2], s, axis=1); out[..., 0] = np.roll(out[..., 0], -s, axis=1)
    return out

def dir_smear(img, vx, vy, length, n=8):
    acc = np.zeros_like(img)
    for i in range(n):
        f = (i / (n - 1) - 0.5) * length
        acc += cv2.warpAffine(img, np.float32([[1, 0, vx * f], [0, 1, vy * f]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / n

def par_lines(vx, vy, t, n=90, seed=5, color=(1.0, 0.9, 1.0)):
    """parallel speed streaks along the motion direction"""
    r = np.random.default_rng(seed + int(t * 60))
    lay = np.zeros((H, W, 3), np.float32)
    d = np.array([vx, vy]); d = d / (np.linalg.norm(d) + 1e-6); nrm = np.array([-d[1], d[0]])
    for _ in range(n):
        c = np.array([W / 2, H / 2]) + nrm * r.uniform(-1200, 1200) + d * r.uniform(-900, 900)
        L = r.uniform(200, 900)
        p0 = c - d * L / 2; p1 = c + d * L / 2
        cv2.line(lay, tuple(int(v) for v in p0), tuple(int(v) for v in p1), color, int(r.integers(1, 3)), cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 1.0)

def events_at(n, ui):
    """one-shot events (burst/clash/glyph) belong to the shot they start in and never re-fire
    after a cut; continuous ones (orb, rise, arcs, pulse) carry on across cuts"""
    return [e for e in EV if e["n0"] <= n < e["n1"] and
            (e["kind"] not in ("burst", "clash", "glyph") or U0[ui] <= e["n0"] < U0[ui + 1])]

# title glyphs (S004 anchor space) placed with the source camera for the ignition sparks
GA = np.load(S + "/pilot/title_groups.npy").astype(np.float32)
GLYPH_GROUPS = [[0, 1], [2], [3, 4]]
def glyph_mask(tau, groups):
    sys.path.insert(0, S + "/work")
    import basefrac as bf
    ui, u0, u1, a = bf.locate(tau)
    ch = bf.load_chain("S004")
    if u0 not in ch["idx"]:
        return GA[groups].sum(0)
    f = bf._field(ch, u0)
    ys, xs = np.mgrid[20:540:40, 20:960:40]
    p = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
    M, _ = cv2.estimateAffinePartial2D(p + f[ys.ravel(), xs.ravel()], p, method=cv2.LMEDS)
    M = M.astype(np.float32); M[:, 2] *= 2
    return cv2.warpAffine(GA[groups].sum(0), M, (W, H))

# end card (the edit holds black for the last ~1.9 s while the song finishes)
T_BLACK = 93.25
def end_card(t_out, rng):
    a = float(ease((t_out - (T_BLACK + 0.15)) / 0.5) * (1 - ease((t_out - 94.55) / 0.5)))
    if a <= 0:
        return None
    gm = (GA.sum(0) > 0.5).astype(np.uint8)
    edge = cv2.morphologyEx(gm, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32)
    edge = cv2.GaussianBlur(edge, (0, 0), 1.2)
    lay = edge[..., None] * np.float32([1.0, 0.55, 0.95]) * 1.2 + cv2.GaussianBlur(edge, (0, 0), 14)[..., None] * np.float32([1.0, 0.4, 0.8]) * 1.8
    txt = np.zeros((H, W, 3), np.uint8)
    cv2.putText(txt, "original animation: NinjaristicNinja", (W // 2 - 300, H - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (190, 178, 204), 1, cv2.LINE_AA)
    txt = txt.astype(np.float32) / 255
    return (lay + txt) * a

# ----------------------------------------------------------------------------- per-unit renderer
NX, NY = Noise(21), Noise(22)

def render_unit(ui):
    n0, n1 = U0[ui], U0[ui + 1]
    rng = np.random.default_rng(1000 + ui)
    embers, sparks, orb = Particles(), Particles(), Particles()
    trail = None; trailE = None; fired = set()
    kin = CUT_IN[ui]
    kout = CUT_IN[ui + 1] if ui + 1 < len(units) else "end"
    for n in range(n0, n1):
        fn = f"{OUT}/n{n:04d}.jpg"
        tau = float(TMAP[n]); t_out = n / FPS
        spd = float((TMAP[min(n + 1, NF - 1)] - TMAP[max(n - 1, 0)]) * FPS / 2) if 0 < n < NF - 1 else 1.0
        img, vel = load_base(n)
        k_in = n - n0; k_out = n1 - n          # frames since the cut in / until the cut out
        bloom_s, chrom, zoom, sh = 1.0, 0.0, 1.0, (0.0, 0.0)
        extra = np.zeros((H, W, 3), np.float32)
        # ---- living energy: flames lick, but never big backdrops of colour
        mc, mr = energy_mask(img, "c"), energy_mask(img, "r")
        E = np.maximum(mc, mr)
        frac = float(E.mean())
        if frac > 0.002:
            amp = 6.0 * float(np.clip((0.22 - frac) / 0.12, 0, 1))
            if amp > 0.3:
                m = cv2.GaussianBlur(cv2.dilate(E, np.ones((25, 25), np.uint8)), (0, 0), 12)
                dx = NX.field(tau, (0, -1), 90) * amp * m; dy = (NY.field(tau + 3.1, (0, -1), 90) - 0.9) * amp * m
                img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out, glow, efill = neon2(img)
        # ---- light trails: lines that move leave a fading neon streak (static lines leave none)
        if trail is None:
            trail = glow.copy()
        trail = np.maximum(trail * 0.74, glow)
        out = out + np.maximum(trail - glow, 0) * 0.65
        energy = img * E[..., None] * float(frac < 0.22)
        trailE = energy.copy() if trailE is None else trailE * 0.8 + energy * 0.35
        out = out + np.maximum(trailE - energy * 1.8, 0) * 0.6
        # ---- embers shed by moving energy
        if 0.002 < frac < 0.22:
            pts = sample(E ** 2, int(min(140, 9000 * frac)), rng)
            if len(pts):
                v = vel_at(vel, pts) * 35 * spd * 0.35
                cols = np.clip(img[np.clip(pts[:, 1].astype(int), 0, H - 1), np.clip(pts[:, 0].astype(int), 0, W - 1)] * 1.25, 0, 1.6)
                ang = rng.normal(-np.pi / 2, 0.7, len(pts)); sp = rng.uniform(60, 220, len(pts))
                embers.emit(pts, v + np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1), cols, rng.uniform(0.35, 0.9, len(pts)), rng.uniform(0.8, 1.6, len(pts)))
        # ---- authored / detected events
        for ev in events_at(n, ui):
            kd, key = ev["kind"], (ev["kind"], ev["t0"])
            col = np.float32(ev.get("col", [1.0, 0.85, 1.0]))
            x = (n - ev["n0"]) / max(ev["n1"] - ev["n0"], 1)
            dt = (n - ev["n0"]) * DT
            if kd in ("burst", "clash"):
                c = ev.get("xy") or centroid(np.maximum(E, efill * 0.5)) or (W / 2, H / 2)
                if key not in fired:
                    fired.add(key); ev["_xy"] = c
                    m = int(ev.get("n", 3500)); ang = rng.uniform(0, 2 * np.pi, m); sp = rng.uniform(200, 1900, m)
                    cc = np.where(rng.random((m, 1)) < 0.3, np.float32([1, 1, 1])[None] * 1.3, col[None] * rng.uniform(0.7, 1.4, (m, 1)))
                    sparks.emit(np.tile(c, (m, 1)), np.stack([np.cos(ang) * sp, np.sin(ang) * sp], 1), cc, rng.uniform(0.25, 1.0, m), rng.uniform(0.8, 2.0, m))
                c = ev["_xy"]
                if kd == "clash" and dt < 2 * DT:
                    out = out * 0.15 + 1.0
                elif kd == "clash" and dt < 4 * DT:
                    out = impact(out, "red", True, 0.4) * 0.85 + out * 0.15
                R = 1700 * eout(dt / 0.7)
                if dt < 0.7:
                    out, ring = shockwave(out, c[0], c[1], R, 70, 30 * (1 - ease(dt / 0.7)))
                    extra += ring * col * 1.2 * (1 - ease(dt / 0.7))
                if dt < 0.45 and n % 2 == 0:
                    for j in range(3):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 700)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), n * 7 + j), tuple(float(v) for v in col), 2, 9) * (1 - dt / 0.45)
                sh = shake(t_out, 22 * (1 - ease(dt / 0.6)), 4)
                bloom_s += 1.2 * (1 - ease(dt / 0.5)); chrom = max(chrom, 0.014 * (1 - ease(dt / 0.5)))
            elif kd == "arcs":
                c = centroid(np.maximum(E, efill * 0.5))
                if c is not None and n % 2 == 0:
                    for j in range(int(ev.get("n", 3))):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 420)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), n * 11 + j, depth=6, branches=2), tuple(float(v) for v in col), 1, 7) * 0.8
            elif kd == "orb":
                c = centroid(np.maximum(E, efill) ** 2)
                if c is not None:
                    m = 260; ang = rng.uniform(0, 2 * np.pi, m); r0 = rng.uniform(30, 160, m)
                    p = np.stack([c[0] + np.cos(ang) * r0, c[1] + np.sin(ang) * r0], 1)
                    tang = np.stack([-np.sin(ang), np.cos(ang)], 1) * rng.uniform(300, 900, (m, 1)) * ev.get("spin", 1)
                    orb.emit(p, tang + vel_at(vel, p) * 35 * spd * 0.5, col[None] * rng.uniform(0.6, 1.3, (m, 1)), rng.uniform(0.3, 0.8, m), rng.uniform(0.8, 1.5, m))
                    ev["_c"] = c
            elif kd == "rise":
                if n % 2 == 0:
                    m = 30; p = np.stack([rng.uniform(0, W, m), rng.uniform(H * 0.4, H, m)], 1)
                    embers.emit(p, np.stack([rng.normal(0, 30, m), rng.uniform(-260, -90, m)], 1), col[None] * rng.uniform(0.5, 1.2, (m, 1)), rng.uniform(0.8, 1.8, m), 1.2)
            elif kd == "pulse":
                c = ev.get("xy") or (W / 2, H / 2)
                d = np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2)
                for k in range(3):
                    ph = (x * 3 + k / 3) % 1
                    extra += (np.exp(-((d - 120 - 900 * ph) / 6.0) ** 2) * (1 - ph) * 0.7)[..., None] * col
            elif kd == "glyph":
                if key not in fired:
                    fired.add(key)
                    pts = sample(glyph_mask(tau, GLYPH_GROUPS[ev["group"]]), 900, rng)
                    if len(pts):
                        a = rng.uniform(0, 2 * np.pi, len(pts)); sp = rng.uniform(60, 500, len(pts))
                        sparks.emit(pts, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), np.where(rng.random((len(pts), 1)) < 0.5, np.float32([1.2, 1.2, 1.2])[None], col[None]), rng.uniform(0.25, 0.7, len(pts)), rng.uniform(0.8, 1.6, len(pts)))
                    sh = shake(t_out, 5, 7)
        # ---- cut accents, centred on the cut frame (the beat stays put)
        if kin == "flash" and k_in < 5:
            out = out + np.float32([1.0, 0.92, 1.0]) * [1.0, 0.75, 0.45, 0.25, 0.1][k_in]; bloom_s += 1.0
        if kout == "flash" and k_out <= 2:
            out = out + np.float32([1.0, 0.92, 1.0]) * [0.0, 0.5, 0.25][k_out]
        if kin == "impact" and k_in < 2:
            out = impact(out, "red" if "红" in units[ui - 1]["transition"] else "bw", True, 0.4) * 0.85 + out * 0.15 if k_in == 0 else out
            chrom = max(chrom, 0.012); sh = shake(t_out, 14, 2)
        if kin == "whip" and k_in < 4 or kout == "whip" and k_out <= 3:
            gv = np.median(vel.reshape(-1, 2), 0); sp = float(np.hypot(*gv))
            vx, vy = (gv / sp) if sp > 1 else (1.0, 0.0)
            w = 1.0 - (k_in / 4 if kin == "whip" and k_in < 4 else k_out / 4)
            out = dir_smear(out, vx, vy, 60 * w)
            extra += par_lines(vx, vy, t_out) * 0.5 * w
        if kin == "cut" and k_in < 3 and n0 > 0:
            out = glitch(out, n, [1.0, 0.55, 0.25][k_in], rng)
        if kin == "dissolve" and k_in < 8:
            bloom_s += 0.6 * (1 - k_in / 8)
        # ---- music accents: a soft glow kick and a tiny push on strong beats
        if len(BEATS):
            db = t_out - BEATS[:, 0]; m = (db >= -DT / 2) & (db < 0.3)
            if m.any():
                j = np.where(m)[0][-1]; kk = float(np.exp(-max(db[j], 0) / 0.09)) * float(BEATS[j, 1])
                bloom_s += 0.45 * kk; zoom *= 1 + 0.01 * kk
        # ---- particles
        embers.step(DT, 0.96, (0, -50)); sparks.step(DT, 0.965, (0, 120)); orb.step(DT, 0.9, (0, 0))
        for P, gl, gn in ((embers, 3.5, 1.1), (sparks, 5.0, 1.2), (orb, 4.0, 1.0)):
            if len(P.p):
                extra += P.render(glow=gl, gain=gn)
        img2 = out + extra
        if t_out > T_BLACK:
            ec = end_card(t_out, rng)
            if ec is not None:
                img2 = img2 + ec
        if zoom != 1.0 or sh != (0.0, 0.0):
            img2 = camera(img2, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
        if chrom > 0:
            img2 = chroma(img2, W / 2, H / 2, chrom * 0.5)
        img2 = bloom(img2, 0.55, 0.7 * bloom_s)
        img2 = finish(img2, grain=0.022, vignette=0.38, t=t_out)
        cv2.imwrite(fn, to8(img2), [cv2.IMWRITE_JPEG_QUALITY, 93])

if __name__ == "__main__":
    wk, nw = int(sys.argv[1]), int(sys.argv[2])
    lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, NF)
    todo = [i for i in range(len(units)) if U0[i] < hi and U0[i + 1] > lo]
    # balance by frame count: greedy longest-first
    loads = [0] * nw; mine = []
    for i in sorted(todo, key=lambda i: -(U0[i + 1] - U0[i])):
        j = int(np.argmin(loads)); loads[j] += U0[i + 1] - U0[i]
        if j == wk:
            mine.append(i)
    for i in sorted(mine):
        render_unit(i)
        print("unit", i, units[i]["id"], flush=True)
    print("done", wk, flush=True)
