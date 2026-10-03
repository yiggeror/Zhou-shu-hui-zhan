"""Pilot part 2: street close combat, original shots 42-49 (51.75 s - 56.54 s)."""
import math
import numpy as np
from engine.mathx import V, norm, hash01, clamp, smoothstep
from engine.anim import Ch
from engine.rig import Figure, GOJO, SUKUNA
from engine.camera import Cam
from engine.shot import Shot, Actor, draw_actors, cam_blur, set_blur
from engine.env import draw_buildings, contact_shadow
from engine.moves import bake_run, feet, fwd, right
from engine import fx
from films import street

GY, SY = math.pi / 2, -math.pi / 2
SET = None


def street_set():
    global SET
    if SET is None:
        SET = street.build()
    return SET


def purple_wash(k, col=(0.75, 0.25, 1.0)):
    """tint toward purple: a single per-pixel 3x4 colour matrix"""
    import cv2
    c = np.array(col, np.float32) * 1.25
    M = np.zeros((3, 4), np.float32)
    for i in range(3):
        M[i, :3] = c[i] * np.array([0.3, 0.5, 0.2], np.float32) * k
        M[i, i] += 1 - k
        M[i, 3] = col[i] * 0.06 * k
    return lambda img: cv2.transform(img, M)


class FightShot(Shot):
    def draw_set(self, fr, cs, win_mult=1.0):
        sky, ground, blds = street_set()
        sky.draw(fr, cs)
        ground.draw(fr, cs)
        draw_buildings(fr, cs, blds, fog_color=(0.55, 0.60, 0.70), fog_dist=170, win_mult=win_mult)

    def shadows(self, fr, cs, tau, actors):
        for a in actors:
            contact_shadow(fr, cs, a.fig.pose(tau), a.fig.k)


# ============================================================================ shot 42
class S42(FightShot):
    """Gojo dashes in, Sukuna slides in with a low kick, fist meets foot."""
    t0, t1 = 1242 / 24, 1264 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        self.C = C = V(-0.10, 0.92, 0.0)        # contact point
        self.T = T = 0.50                        # clash time
        # ---------------- Gojo: sprint in from the left, fist cocked low behind
        g.k(0, yaw=GY, twist=-0.45, hyaw=0.25, hpitch=0.1, eye_glow=1.0, eye_fire=0.25)
        g.k(0, hand_r=V(0.18, -0.36, -0.26), elbow_r=V(0.5, 0.3, -0.8), fist_r=1.0,
            hand_l=V(-0.02, -0.08, 0.38), elbow_l=V(-0.7, -0.5, 0.0), fist_l=1.0)
        xg = Ch(-12.0).key(0.10, -8.6, 'lin').key(0.40, -2.2, 'lin').key(0.47, -1.05, 'out')
        path = lambda t: V(float(xg(t)), 0, 0.02)
        bake_run(g, -0.1, 0.40, path, GY, freq=3.3, stride_lead=0.45, lift=0.36, base_h=0.84, bob=0.06,
                 lean=0.55, stance_frac=0.24)
        g.k(0.40, foot_l=V(-1.9, 0.30, 0.16))
        g.k(0.45, 'out', foot_l=V(-0.50, 0.0, 0.16))
        g.k(0.40, foot_r=V(-2.35, 0.0, -0.12)).k(0.44, foot_r=V(-2.35, 0.0, -0.12))
        g.k(0.49, 'out', foot_r=V(-1.75, 0.0, -0.14))
        # plant into the lunge
        g.k(0.40, hand_r=V(0.18, -0.30, -0.30))
        g.k(0.44, hand_r=V(0.18, -0.10, -0.38), twist=-0.6)
        g.k(T - 0.02, root=V(-1.0, 0.76, 0.0), lean=0.62)
        g.k(0.40, hand_l=V(-0.0, -0.05, 0.36))
        g.k(T - 0.01, hand_l=V(0.08, -0.16, 0.06), twist=0.5, hpitch=0.25, hyaw=0.0)
        # the punch: blend to a world target
        g.fig.set(hand_rw=C + V(-0.06, 0.06, 0))
        g.k(0, hand_rwb=0.0).k(0.445, hand_rwb=0.0).k(T, 'in', hand_rwb=1.0)
        # pressing (fist grinds forward a little)
        g.k(T + 0.06, root=V(-0.97, 0.75, 0.0), lean=0.66)
        g.k(0.74, root=V(-0.90, 0.74, 0.0), lean=0.70, twist=0.55, hand_rwb=1.0)
        # follow-through: fist drives down and across, body turns over it
        g.k(0.74, 'lin', hand_rwb=1.0)
        g.k(0.80, 'in', hand_rwb=0.0)
        g.k(0.74, hand_r=V(-0.10, -0.10, 0.62))
        g.k(0.86, 'out', hand_r=V(-0.30, -0.42, 0.40), twist=1.05, lean=0.85, root=V(-0.55, 0.70, 0.02),
            foot_r=V(-1.45, 0.12, -0.1))
        g.k(0.917, hand_r=V(-0.34, -0.48, 0.32), twist=1.12, lean=0.88, root=V(-0.48, 0.69, 0.02), foot_r=V(-1.0, 0.0, -0.12))
        # ---------------- Sukuna: sliding kick from the right
        s.k(0, yaw=SY, eye_glow=1.0, eye_fire=0.35, fist_l=1.0, fist_r=1.0)
        r0 = V(5.4, 1.15, -0.02)
        r1 = V(1.02, 0.98, 0.0)
        s.k(0.0, root=r0).k(0.34, root=r0).k(T, 'out3', root=r1)
        s.k(0.0, lean=-0.45, bend=0.25, twist=0.30, hpitch=-0.10, hyaw=-0.35)
        s.k(T, lean=-0.50, bend=0.30, twist=0.40)
        kick = C + V(0.14, -0.14, 0.0)
        s.k(0.34, foot_l=r0 + (kick - r1) * 0.92)
        s.k(T, 'out3', foot_l=kick)
        s.k(0.34, foot_r=r0 + V(0.25, -0.55, 0.18)).k(T, 'out3', foot_r=r1 + V(0.22, -0.52, 0.18))
        s.k(T + 0.10, foot_r=r1 + V(0.30, -0.98, 0.18))
        s.k(0.0, knee_l=V(0, 0.4, 1), knee_r=V(0.2, 0.6, 1))
        s.k(0.0, hand_l=V(0.05, -0.30, -0.30), elbow_l=V(-0.6, 0.2, -0.8), hand_r=V(0.05, -0.05, 0.30), elbow_r=V(0.6, -0.6, -0.2))
        # pressed
        s.k(T + 0.06, root=r1 + V(0.03, -0.04, 0.0), foot_l=kick + V(0.02, 0, 0))
        s.k(0.74, root=r1 + V(0.10, -0.08, 0.0), foot_l=kick + V(0.07, 0.0, 0.0), lean=-0.55)
        # blown away, spinning
        s.k(0.917, 'out', root=V(2.6, 1.05, 0.35), foot_l=V(2.1, 0.75, 0.0), foot_r=V(3.0, 0.35, 0.6), yaw=SY + 1.5,
            lean=-0.25, twist=-0.4, hand_l=V(0.2, 0.25, -0.2), hand_r=V(-0.1, 0.3, 0.2), hyaw=0.4)
        # ---------------- effects
        self.hitstop(T, frames=4, catch=0.10)
        G, S = g.fig, s.fig
        self.flames = [
            fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.085, rise=0.8, src2=lambda t: G.pose(t)['Er'], seg=(0.65, 1.0), seed=1),
            fx.Flame(lambda t: S.pose(t)['Tl'], 'red', size=0.075, rise=0.8, src2=lambda t: S.pose(t)['Al'], seg=(0.0, 1.0), seed=2,
                     amount=Ch(0.0).key(0.33, 0.0).key(0.40, 1.0)),
        ]
        # ---------------- camera
        cam = self.cam = Cam(
            Ch(keys=[(-0.1, V(-6.6, 1.05, -5.0)), (0.0, V(-5.8, 1.05, -5.0))]).key(0.20, V(-4.8, 1.0, -4.8)).key(0.47, V(-1.4, 1.05, -4.0))
            .key(0.74, V(-0.8, 1.0, -3.4)).key(0.917, V(-0.6, 1.05, -3.2)),
            Ch(keys=[(-0.1, V(-14.0, 0.8, 6.0)), (0.0, V(-9.0, 0.8, 6.0), 'lin')]).key(0.16, V(-4.6, 0.95, 0.0), 'out').key(0.47, V(-0.6, 0.9, 0.0))
            .key(0.74, V(-0.15, 0.82, 0.0)).key(0.917, V(1.4, 1.05, 0.1), 'in'),
            fov=Ch(44.0).key(0.47, 42.0).key(0.74, 36.0).key(0.917, 38.0))
        cam.shake(T, amp=30, dur=0.45, freq=24).punch(T, 0.10, 0.03, 0.35)

    def draw(self, fr, s):
        tau = self.tw(s)
        cam = self.cam
        cs = cam.at(s)
        self.draw_set(fr, cs)
        set_blur(fr, cam, s)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        T = self.T
        a = s - T
        q = cs.proj(self.C)
        if a >= 0:
            if a < 0.12:
                fx.speed_lines(fr, q[0], q[1], int(s * 30), n=80, rin=260, alpha=0.55 * (1 - a / 0.12), width=4)
            fx.impact_burst(fr, q[0], q[1], a, size=220, pal='white', seed=3, spikes=11, life=0.10)
            fx.impact_burst(fr, q[0], q[1], a - 0.02, size=160, pal='purple', seed=4, spikes=7, life=0.09)
            fx.sparks(fr, cs, self.C, a, n=26, pal='cyan', speed=7.5, life=0.4, seed=5, dirv=V(-0.4, 0.6, 0), cone=1.1)
            fx.sparks(fr, cs, self.C, a, n=22, pal='red', speed=7.0, life=0.4, seed=6, dirv=V(0.5, 0.5, 0), cone=1.1)
            if a < 1 / 60:
                fr.impact = dict(bg=(0, 0, 0), fg=(1, 1, 1))
            elif a < 2 / 60:
                fr.impact = dict(bg=(0.80, 0.30, 0.95), fg=(0.02, 0.0, 0.04), energy=False)
            elif a < 0.30:
                fr.post.append(purple_wash(0.5 * (1 - (a - 2 / 60) / 0.27) ** 1.5))
            if a < 0.30:
                fr.post.append(fx.radial_warp(q[0], q[1], 60 + 900 * a, 40 + 60 * a, 12 * (1 - a / 0.3)))
        # crackling while they press against each other
        if T + 2 / 60 <= s < 0.76:
            seed = int(s * 30)
            pg, ps_ = cs.proj(self.g.fig.pose(tau)['Wr']), cs.proj(self.s.fig.pose(tau)['Tl'])
            k = 0.8 if s < T + 0.12 else 0.5
            fx.bolt(fr, pg[:2] + [0, -10], pg[:2] + [70 + 60 * hash01(seed, 1), -90 - 80 * hash01(seed, 2)], seed, 'cyan', 2.2, k)
            fx.bolt(fr, ps_[:2], ps_[:2] + [90 + 50 * hash01(seed, 3), 60 * hash01(seed, 4) - 10], seed + 7, 'red', 2.2, k)
            for j in range(3):
                te = T + 0.08 + 0.07 * j
                fx.sparks(fr, cs, self.C, s - te, n=8, pal='white', speed=5.0, life=0.25, seed=40 + j, dirv=V(0, 1, -0.3), cone=1.4, k=0.7)
        cam_blur(fr, cam, s)


def hit_fx(fr, cs, P, a, pal='cyan', k=1.0, seed=0, tone=None, lines=True, sparks_dir=None, size=200):
    """standard hit: flash + star + ring, sparks, focus lines, optional two-tone frame"""
    if a < 0:
        return
    q = cs.proj(P)
    if not np.isfinite(q[0]):
        return
    if lines and a < 0.10 * k + 0.02:
        fx.speed_lines(fr, q[0], q[1], int((a + seed) * 30), n=int(70 * k) + 10, rin=240, alpha=0.5 * k * (1 - a / (0.10 * k + 0.02)), width=4)
    fx.impact_burst(fr, q[0], q[1], a, size=size * (0.55 + 0.45 * k), pal='white', seed=seed, spikes=int(6 + 6 * k), life=0.09)
    fx.impact_burst(fr, q[0], q[1], a - 0.015, size=size * 0.75 * (0.55 + 0.45 * k), pal=pal, seed=seed + 1, spikes=6, life=0.08)
    fx.sparks(fr, cs, P, a, n=int(8 + 20 * k), pal=pal, speed=6.5 * (0.6 + 0.4 * k), life=0.35, seed=seed + 2,
              dirv=sparks_dir, cone=1.0 if sparks_dir is not None else 1.0)
    if tone is not None and a < 1 / 60:
        fr.impact = tone
    if a < 0.22 * k:
        fr.post.append(fx.radial_warp(q[0], q[1], 50 + 800 * a, 30 + 50 * a, 10 * k * (1 - a / (0.22 * k))))


BW = dict(bg=(0, 0, 0), fg=(1, 1, 1))
INV = dict(bg=(0.95, 0.95, 0.97), fg=(0.0, 0.0, 0.0), energy=True)


# ============================================================================ shot 43
class S43(FightShot):
    """Gojo's rising hook, Sukuna blocks high with his forearm."""
    t0, t1 = 1264 / 24, 1272 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        T = self.T = 0.10
        self.B = B = V(0.30, 1.86, -0.12)          # block point (Sukuna's forearm)
        fl, fr_ = feet((-0.55, 0.0), GY, 0.42, -0.42, 0.17, 'l')
        g.k(0, yaw=GY, root=V(-0.62, 0.78, 0.0), lean=0.55, twist=-0.35, hpitch=0.0, foot_l=fl, foot_r=fr_,
            eye_glow=1.0, eye_fire=0.3, fist_l=1.0, fist_r=1.0,
            hand_r=V(0.10, -0.45, 0.10), elbow_r=V(0.8, -0.2, -0.5), hand_l=V(0.06, -0.10, 0.25), elbow_l=V(-0.7, -0.6, 0))
        g.fig.set(hand_rw=B + V(-0.10, -0.02, -0.02))
        g.k(0, hand_rwb=0.0).k(0.03, hand_rwb=0.0).k(T, 'in', hand_rwb=1.0)
        g.k(T, root=V(-0.45, 0.92, 0.0), lean=0.25, twist=0.55, hpitch=-0.25, foot_r=fr_ + V(0.15, 0.0, 0.0))
        g.k(0.333, root=V(-0.40, 0.93, 0.0), lean=0.28, twist=0.62)
        sl, sr = feet((0.62, 0.0), SY, 0.32, -0.38, 0.17, 'l')
        s.k(0, yaw=SY, root=V(0.62, 0.88, 0.0), lean=0.05, twist=0.15, foot_l=sl, foot_r=sr, eye_glow=1.0, eye_fire=0.4,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.02, -0.05, 0.32), hand_r=V(-0.05, -0.15, 0.28),
            elbow_l=V(-0.7, -0.6, -0.1), elbow_r=V(0.7, -0.6, -0.2), hpitch=0.05)
        # high block with the right forearm (the near arm from this camera)
        s.k(0.07, 'out', hand_r=V(-0.12, 0.40, 0.30), elbow_r=V(0.8, 0.5, 0.6), twist=0.05)
        s.k(T, hand_r=V(-0.14, 0.42, 0.30))
        s.k(T + 0.06, 'out', root=V(0.74, 0.82, 0.0), lean=-0.18, hpitch=-0.25, hand_r=V(-0.10, 0.36, 0.22))
        s.k(0.333, root=V(0.78, 0.81, 0.0), lean=-0.12, hpitch=-0.15)
        self.hitstop(T, 3)
        G = g.fig
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.09, rise=0.8, src2=lambda t: G.pose(t)['Er'],
                                seg=(0.65, 1.0), seed=11)]
        cam = self.cam = Cam(Ch(V(-1.80, 1.38, -1.45)).key(0.333, V(-1.62, 1.42, -1.32)),
                             Ch(V(0.45, 1.45, 0.05)).key(0.333, V(0.42, 1.55, 0.05)), fov=44)
        cam.shake(T, 16, 0.3).punch(T, 0.05)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        self.draw_set(fr, cs)
        set_blur(fr, self.cam, s)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, self.cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        a = s - self.T
        hit_fx(fr, cs, self.B, a, 'cyan', k=0.75, seed=20, sparks_dir=V(0.3, 0.6, 0.2))
        if a > 0:
            # energy keeps splashing off the block while the fist grinds on it
            for j in range(4):
                fx.sparks(fr, cs, self.B, s - (self.T + 0.05 * j), n=6, pal='cyan', speed=4.0, life=0.22, seed=60 + j,
                          dirv=V(0.2, 1.0, 0.0), cone=1.2, k=0.8)


# ============================================================================ shot 44
class S44(FightShot):
    """Sukuna's red straight drives into Gojo's chest, Gojo is knocked back."""
    t0, t1 = 1272 / 24, 1284 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        T = self.T = 0.136
        fl, fr_ = feet((-0.55, 0.0), GY, 0.38, -0.40, 0.17, 'l')
        g.k(0, yaw=GY, root=V(-0.55, 0.90, 0.0), lean=0.15, twist=0.2, foot_l=fl, foot_r=fr_, eye_glow=1.0, eye_fire=0.2,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.05, -0.05, 0.30), hand_r=V(-0.04, -0.10, 0.25),
            elbow_l=V(-0.7, -0.6, 0), elbow_r=V(0.7, -0.6, 0), hpitch=0.0, eye_open=1.0)
        self.P = P = V(-0.42, 1.38, 0.02)   # Gojo's chest
        # recoil after the hit
        g.k(T, root=V(-0.55, 0.90, 0.0), lean=0.12, hpitch=0.05)
        g.k(T + 0.10, 'out', root=V(-0.88, 0.86, 0.02), lean=-0.38, hpitch=-0.55, twist=-0.15,
            hand_l=V(-0.20, 0.10, 0.25), hand_r=V(0.20, 0.05, 0.20), foot_r=fr_ + V(-0.25, 0, 0))
        g.k(0.5, root=V(-1.05, 0.84, 0.02), lean=-0.30, hpitch=-0.35, twist=-0.2)
        sl, sr = feet((0.70, 0.0), SY, 0.42, -0.42, 0.17, 'l')
        s.k(0, yaw=SY, root=V(0.82, 0.86, 0.0), lean=0.15, twist=-0.55, foot_l=sl, foot_r=sr, eye_glow=1.0, eye_fire=0.5,
            fist_l=1.0, fist_r=1.0, hand_r=V(0.12, -0.18, -0.12), elbow_r=V(0.6, -0.2, -0.8),
            hand_l=V(0.05, -0.05, 0.32), elbow_l=V(-0.7, -0.6, -0.1))
        s.fig.set(hand_rw=P + V(0.08, 0.0, 0.0))
        s.k(0, hand_rwb=0.0).k(0.02, hand_rwb=0.0).k(T, 'in', hand_rwb=1.0)
        s.k(T, root=V(0.64, 0.84, 0.0), lean=0.35, twist=0.55, hand_l=V(0.10, -0.15, 0.08))
        s.k(T + 0.10, hand_rwb=1.0)
        s.fig.set(hand_rw=Ch(P + V(0.08, 0, 0)).key(T + 0.10, P + V(-0.25, 0.02, 0.02), 'out'))
        s.k(0.40, hand_rwb=1.0).k(0.46, 'in', hand_rwb=0.0)
        s.k(0.40, hand_r=V(0.10, -0.10, 0.30)).k(0.48, 'out', hand_r=V(0.18, -0.25, -0.10), twist=-0.2, lean=0.2)
        self.hitstop(T, 3)
        S = s.fig
        self.flames = [fx.Flame(lambda t: S.pose(t)['Wr'], 'red', size=0.10, rise=0.8, src2=lambda t: S.pose(t)['Er'],
                                seg=(0.3, 1.0), seed=21)]
        # camera over Sukuna's right shoulder, looking at Gojo
        cam = self.cam = Cam(Ch(keys=[(-0.05, V(1.75, 1.55, 1.45)), (0.05, V(1.55, 1.50, 1.20), 'out')]).key(0.5, V(1.35, 1.45, 1.05)),
                             Ch(keys=[(-0.05, V(-0.2, 1.4, -0.4)), (0.05, V(-0.55, 1.35, 0.0), 'out')]).key(0.5, V(-0.75, 1.30, 0.0)),
                             fov=Ch(44).key(T, 40).key(0.5, 42))
        cam.shake(T, 22, 0.35).punch(T, 0.07)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        self.draw_set(fr, cs)
        set_blur(fr, self.cam, s)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, self.cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        a = s - self.T
        hit_fx(fr, cs, self.P, a, 'red', k=1.0, seed=30, tone=dict(bg=(0, 0, 0), fg=(1, 0.92, 0.92)),
               sparks_dir=V(-0.8, 0.3, -0.3))
        if 0 <= a < 2 / 60 and a >= 1 / 60:
            fr.impact = dict(bg=(0.85, 0.05, 0.12), fg=(0.0, 0.0, 0.0), energy=False)
        cam_blur(fr, self.cam, s)


# ============================================================================ shot 45
class S45(FightShot):
    """Reverse angle: Sukuna's back in the foreground, Gojo recovers and ignites his fist."""
    t0, t1 = 1284 / 24, 1293 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        fl, fr_ = feet((-1.05, 0.0), GY, 0.40, -0.45, 0.18, 'l')
        g.k(0, yaw=GY, root=V(-1.05, 0.85, 0.02), lean=-0.25, hpitch=-0.25, twist=-0.15, foot_l=fl, foot_r=fr_,
            eye_glow=1.0, eye_fire=0.3, fist_l=1.0, fist_r=1.0, hand_l=V(-0.15, 0.05, 0.25), hand_r=V(0.18, 0.0, 0.18),
            elbow_l=V(-0.7, -0.6, 0), elbow_r=V(0.7, -0.6, 0))
        # recover forward, sink and cock the right fist
        g.k(0.14, 'io', lean=0.30, hpitch=0.15, twist=-0.1, root=V(-1.0, 0.80, 0.02), hand_l=V(0.04, -0.06, 0.32))
        g.k(0.30, 'io', lean=0.42, twist=-0.65, root=V(-1.02, 0.74, 0.02), hand_r=V(0.20, 0.05, -0.28),
            elbow_r=V(0.6, 0.0, -0.8), hpitch=0.2)
        g.k(0.375, lean=0.48, twist=-0.45, root=V(-0.92, 0.75, 0.02), hand_r=V(0.16, 0.0, -0.10))
        sl, sr = feet((0.55, 0.0), SY, 0.32, -0.40, 0.18, 'l')
        s.k(0, yaw=SY, root=V(0.55, 0.88, 0.0), lean=0.05, twist=0.25, foot_l=sl, foot_r=sr, eye_glow=1.0,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.10, 0.30, 0.25), hand_r=V(-0.10, 0.42, 0.22),
            elbow_l=V(-0.8, 0.3, 0.3), elbow_r=V(0.8, 0.4, 0.3))
        s.k(0.375, root=V(0.53, 0.87, 0.0), twist=0.15, hand_l=V(0.08, 0.36, 0.25), hand_r=V(-0.08, 0.46, 0.22))
        G = g.fig
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.10, rise=0.9, src2=lambda t: G.pose(t)['Er'],
                                seg=(0.65, 1.0), seed=31, amount=Ch(0.0).key(0.18, 0.0).key(0.27, 1.0, 'out'))]
        self.cam = Cam(Ch(V(1.95, 1.62, -0.95)).key(0.375, V(1.75, 1.58, -0.85)),
                       Ch(V(-0.65, 1.25, 0.0)).key(0.375, V(-0.75, 1.25, 0.0)), fov=42)
        self.g.fig.set(eye_glow=Ch(0.8).key(0.18, 0.8).key(0.27, 1.2))

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        self.draw_set(fr, cs)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, self.cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)


# ============================================================================ shot 46
class S46(FightShot):
    """Seen from the other side: Gojo's cyan straight lands, Sukuna folds back in slow motion."""
    t0, t1 = 1293 / 24, 1307 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        T = self.T = 0.035
        self.P = P = V(0.40, 1.42, 0.02)      # Sukuna's upper chest
        fl, fr_ = feet((-0.45, 0.0), GY, 0.48, -0.45, 0.17, 'l')
        g.k(-0.08, yaw=GY, root=V(-0.70, 0.80, 0.0), lean=0.45, twist=-0.45, foot_l=fl, foot_r=fr_, eye_glow=1.1, eye_fire=0.5,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.06, -0.08, 0.30), elbow_l=V(-0.7, -0.6, 0), hand_r=V(0.16, 0.0, -0.10),
            elbow_r=V(0.6, -0.1, -0.8))
        g.fig.set(hand_rw=Ch(P + V(-0.06, 0, 0)).key(T, P + V(-0.06, 0, 0)).key(T + 0.12, P + V(0.28, -0.12, 0.0), 'out')
                  .key(0.58, P + V(0.62, -0.22, 0.0)))
        g.k(-0.08, hand_rwb=0.0).k(T, 'in', hand_rwb=1.0)
        g.k(T, root=V(-0.45, 0.80, 0.0), lean=0.50, twist=0.55, hand_l=V(0.12, -0.18, 0.05))
        g.k(0.583, 'out', root=V(-0.12, 0.78, 0.0), lean=0.60, twist=0.70, foot_r=fr_ + V(0.30, 0, 0))
        sl, sr = feet((0.70, 0.0), SY, 0.34, -0.42, 0.17, 'l')
        s.k(-0.08, yaw=SY, root=V(0.62, 0.88, 0.0), lean=0.05, twist=0.15, foot_l=sl, foot_r=sr, eye_glow=1.0, eye_fire=0.4,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.10, 0.20, 0.22), hand_r=V(-0.10, 0.30, 0.20),
            elbow_l=V(-0.8, 0.0, 0.3), elbow_r=V(0.8, 0.0, 0.3))
        s.k(T, root=V(0.62, 0.88, 0.0), lean=0.05, hpitch=0.0)
        # folds around the fist: chest pushed back, head snaps forward-down, knees buckle (slow)
        s.k(T + 0.12, 'out', root=V(1.02, 0.80, 0.0), lean=0.38, curve=-0.6, hpitch=0.40, twist=0.3,
            hand_l=V(0.05, -0.30, 0.10), hand_r=V(-0.05, -0.25, 0.15), foot_l=sl + V(0.25, 0, 0))
        s.k(0.583, root=V(1.45, 0.72, 0.0), lean=0.50, hpitch=0.55, twist=0.45, foot_r=sr + V(0.55, 0, 0), foot_l=sl + V(0.42, 0, 0))
        self.hitstop(T, 3)
        G = g.fig
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.13, rise=0.6, src2=lambda t: G.pose(t)['Er'],
                                seg=(0.35, 1.0), seed=41, trail=0.45)]
        # camera on the far side: Gojo screen-right, Sukuna screen-left
        self.cam = Cam(Ch(V(0.45, 1.25, 3.4)).key(0.45, V(0.30, 1.28, 3.0)).key(0.583, V(-0.25, 1.45, 2.6), 'in'),
                       Ch(V(0.35, 1.20, 0.0)).key(0.45, V(0.35, 1.22, 0.0)).key(0.583, V(-0.35, 1.45, 0.0), 'in'), fov=42)
        self.cam.shake(T, 20, 0.3).punch(T, 0.06)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        self.draw_set(fr, cs)
        set_blur(fr, self.cam, s)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, self.cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        hit_fx(fr, cs, self.P, s - self.T, 'cyan', k=0.9, seed=40, tone=BW, sparks_dir=V(1, 0.3, 0))
        cam_blur(fr, self.cam, s)


# ============================================================================ shot 47
class S47(FightShot):
    """Close: Gojo's fist smashes Sukuna's face; slow-motion aftermath; dark wipe."""
    t0, t1 = 1307 / 24, 1322 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        T = self.T = 0.095
        self.P = P = V(0.36, 1.66, -0.02)     # Sukuna's face
        fl, fr_ = feet((-0.40, 0.0), GY, 0.45, -0.42, 0.17, 'l')
        g.k(0, yaw=GY, root=V(-0.55, 0.84, 0.0), lean=0.30, twist=0.45, foot_l=fl, foot_r=fr_, eye_glow=1.1, eye_fire=0.5,
            fist_l=1.0, fist_r=1.0, hand_r=V(-0.05, -0.15, 0.25), elbow_r=V(0.7, -0.6, 0),
            hand_l=V(-0.30, -0.05, -0.05), elbow_l=V(-0.8, 0.2, -0.4))
        # left hook to the face
        g.fig.set(hand_lw=P + V(-0.08, 0.0, -0.04))
        g.k(0, hand_lwb=0.0).k(0.01, hand_lwb=0.0).k(T, 'in', hand_lwb=1.0)
        g.k(T, root=V(-0.40, 0.84, 0.0), lean=0.32, twist=-0.45, hand_r=V(0.10, -0.15, 0.10))
        g.k(T + 0.25, 'out', hand_lwb=0.75, root=V(-0.32, 0.86, 0.0), twist=-0.55)
        g.k(0.625, hand_lwb=0.2, hand_l=V(-0.10, 0.35, 0.20), root=V(-0.30, 0.88, 0.0), lean=0.2, twist=-0.35)
        sl, sr = feet((0.62, 0.0), SY, 0.34, -0.42, 0.17, 'l')
        s.k(0, yaw=SY, root=V(0.60, 0.86, 0.0), lean=0.15, twist=0.0, foot_l=sl, foot_r=sr, eye_glow=1.0, eye_fire=0.4,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.05, -0.20, 0.20), hand_r=V(-0.05, -0.20, 0.20),
            elbow_l=V(-0.8, -0.3, 0.2), elbow_r=V(0.8, -0.3, 0.2), hyaw=0.0)
        # head whips away, body follows slowly (slow motion)
        s.k(T, hyaw=0.0, hroll=0.0, twist=0.0)
        s.k(T + 0.08, 'out', hyaw=0.85, hroll=0.35, hpitch=-0.2, twist=0.35, root=V(0.70, 0.85, -0.05), lean=-0.05)
        s.k(0.625, hyaw=1.15, hroll=0.5, twist=0.75, root=V(1.05, 0.80, -0.14), lean=-0.22, bend=-0.32,
            hand_l=V(-0.15, 0.0, 0.15), hand_r=V(0.20, -0.30, -0.05))
        self.hitstop(T, 3)
        G = g.fig
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wl'], 'cyan', size=0.10, rise=0.7, src2=lambda t: G.pose(t)['El'],
                                seg=(0.6, 1.0), seed=51)]
        self.cam = Cam(Ch(keys=[(-0.04, V(-1.4, 1.75, -2.2)), (0.04, V(-0.55, 1.62, -1.95), 'out')]).key(0.625, V(-0.45, 1.58, -1.8)),
                       Ch(keys=[(-0.04, V(-1.5, 1.6, 0.0)), (0.04, V(0.15, 1.55, 0.0), 'out')]).key(0.625, V(0.25, 1.50, 0.0)),
                       fov=46)
        self.cam.shake(T, 24, 0.35).punch(T, 0.08)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        self.draw_set(fr, cs)
        set_blur(fr, self.cam, s)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, self.cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        a = s - self.T
        hit_fx(fr, cs, self.P, a, 'cyan', k=1.0, seed=50, tone=BW, sparks_dir=V(1, 0.2, 0.4))
        if a > 0:
            # cyan motes hanging in the air after the blow (slow, short-lived)
            fx.sparks(fr, cs, self.P + V(0.15, 0, 0), a, n=30, pal='cyan', speed=1.6, life=0.5, seed=55, dirv=V(1, 0.2, 0),
                      cone=1.3, gravity=-0.3, length=0.02, width=2.0, k=0.8)
        cam_blur(fr, self.cam, s)
        # dark wipe at the end (something dark sweeping across the lens)
        w0 = 0.46
        if s > w0:
            u = (s - w0) / (0.583 - w0)
            from engine.canvas import paint, poly_path
            x = -400 + u * 2600
            pts = [(-4000, -50), (x + 300, -50), (x + 700, 1130), (-4000, 1130)]
            fr.b.drawPath(poly_path(pts, closed=True), paint((0.01, 0.012, 0.02), 1.0, blur=30))
            fr.g.drawPath(poly_path(pts, closed=True), paint((0, 0, 0), 1.0, erase=True))
            if s > 0.583:
                fr.b.clear(paint((0.01, 0.012, 0.02)).getColor4f())
                fr.G[...] = 0


# ============================================================================ shot 48
class S48(FightShot):
    """Gojo's barrage into Sukuna's body (after-images), ending on a two-tone close-up of
    Sukuna's four eyes."""
    t0, t1 = 1322 / 24, 1336 / 24
    HITS = [(0.065, 'r'), (0.135, 'l'), (0.202, 'r'), (0.270, 'l'), (0.341, 'r'), (0.410, 'l')]

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        fl, fr_ = feet((-0.42, 0.0), GY, 0.42, -0.42, 0.18, 'l')
        g.k(0, yaw=GY, root=V(-0.48, 0.80, 0.0), lean=0.38, twist=0.0, foot_l=fl, foot_r=fr_, eye_glow=1.2, eye_fire=0.6,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.05, -0.08, 0.26), hand_r=V(-0.05, -0.10, 0.22),
            elbow_l=V(-0.8, -0.5, -0.1), elbow_r=V(0.8, -0.5, -0.1), hand_lwb=0.0, hand_rwb=0.0)
        sl, sr = feet((0.62, 0.0), SY, 0.32, -0.42, 0.18, 'l')
        s.k(0, yaw=SY, root=V(0.58, 0.86, 0.0), lean=0.12, twist=0.1, foot_l=sl, foot_r=sr, eye_glow=1.0, eye_fire=0.5,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.10, -0.25, 0.10), hand_r=V(-0.10, -0.20, 0.10), hpitch=0.15,
            elbow_l=V(-0.8, -0.3, 0.2), elbow_r=V(0.8, -0.3, 0.2))
        tgt = {'l': Ch(V(0, 0, 0)), 'r': Ch(V(0, 0, 0))}
        self.pts = []
        for i, (th, side) in enumerate(self.HITS):
            P = V(0.42 + 0.03 * (i % 2), 1.18 + 0.12 * math.sin(i * 2.1), 0.10 * math.cos(i * 1.7))
            self.pts.append(P)
            tgt[side].key(th - 0.06, P + V(-0.06, 0, 0), 'hold').key(th, P + V(-0.06, 0, 0), 'lin')
            nm = 'hand_%swb' % side
            g.k(th - 0.045, **{nm: 0.0}).k(th, 'in', **{nm: 1.0}).k(th + 0.012, **{nm: 1.0}).k(th + 0.055, 'out', **{nm: 0.0})
            # shoulders swing into each punch
            g.k(th, twist=(0.35 if side == 'r' else -0.35), lean=0.42)
            self.hitstop(th, 1, catch=0.02)
            # Sukuna is jolted back a little with each blow
            s.k(th, root=V(0.58 + 0.05 * i, 0.86 - 0.01 * i, 0.0), lean=0.12 + 0.03 * i, hpitch=0.15)
            s.k(th + 0.03, 'out', root=V(0.62 + 0.05 * i, 0.85 - 0.01 * i, 0.0), lean=0.20 + 0.04 * i, hpitch=0.32,
                twist=0.1 + (0.12 if side == 'r' else -0.12))
        g.fig.set(hand_lw=tgt['l'], hand_rw=tgt['r'])
        g.k(0.50, twist=0.0, lean=0.4)
        G = g.fig
        gh = lambda t: [(0.018, 0.32, (0.55, 0.95, 1.0)), (0.036, 0.20, (0.35, 0.85, 1.0)), (0.054, 0.10, (0.2, 0.7, 1.0))]
        g.draw_opts = dict(ghosts=gh)
        self.flames = [fx.Flame(lambda t: G.pose(t)['Wr'], 'cyan', size=0.06, rise=0.6, src2=lambda t: G.pose(t)['Er'], seg=(0.8, 1.0), seed=61, trail=0.2, life=0.18),
                       fx.Flame(lambda t: G.pose(t)['Wl'], 'cyan', size=0.06, rise=0.6, src2=lambda t: G.pose(t)['El'], seg=(0.8, 1.0), seed=62, trail=0.2, life=0.18)]
        self.cam = Cam(Ch(V(0.35, 1.32, 2.35)).key(0.48, V(0.25, 1.30, 2.05)),
                       Ch(V(0.25, 1.22, 0.0)).key(0.48, V(0.30, 1.20, 0.0)), fov=42)
        for th, _ in self.HITS:
            self.cam.shake(th, 9, 0.12)
        # close-up camera for the final impact frames: Sukuna's face
        Hh = s.fig.pose(0.5)['H']
        self.cu = Cam(Ch(Hh + V(-0.62, -0.30, -0.30)).key(0.583, Hh + V(-0.55, -0.27, -0.26)), Ch(Hh + V(0, -0.02, 0)), fov=38)
        self.cu.shake(0.49, 14, 0.1)

    def draw(self, fr, s):
        tau = self.tw(s)
        close = s >= 0.49
        cam = self.cu if close else self.cam
        cs = cam.at(s)
        self.draw_set(fr, cs)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        for i, (th, side) in enumerate(self.HITS):
            # combo hits: lighter than a single blow
            hit_fx(fr, cs, self.pts[i], s - th, 'cyan', k=0.42, seed=70 + 5 * i, lines=(i == len(self.HITS) - 1),
                   sparks_dir=V(1, 0.3, 0), size=150)
        if close:
            a = s - 0.49
            Hh = self.s.fig.pose(tau)['H']
            q = cs.proj(Hh + V(-0.2, -0.05, 0))
            fx.impact_burst(fr, q[0], q[1], a, size=420, pal='cyan', seed=80, spikes=12, life=0.08)
            fx.sparks(fr, cs, Hh + V(-0.15, 0, 0), a, n=24, pal='cyan', speed=3.0, life=0.2, seed=81, dirv=V(1, 0.2, 0), cone=1.2)
            if a < 2 / 60:
                fr.impact = dict(bg=(0.02, 0.04, 0.06), fg=(0.9, 1.0, 1.0), energy=True)
            elif a > 0.07:
                # quick pink-white smear into the next shot
                u = (a - 0.07) / 0.023
                fx.flash(fr, (1.0, 0.55, 0.65), 0.6 * min(1.0, u))


# ============================================================================ shot 49
class S49(FightShot):
    """Sukuna's red backhand sweeps over Gojo, who ducks under it; slow-motion hold."""
    t0, t1 = 1336 / 24, 1357 / 24

    def setup(self):
        g = self.g = Actor(Figure(GOJO, 1.06, 'gojo'))
        s = self.s = Actor(Figure(SUKUNA, 1.0, 'sukuna'))
        T = self.T = 0.06
        fl, fr_ = feet((-0.35, 0.0), GY, 0.38, -0.45, 0.20, 'l')
        g.k(0, yaw=GY, root=V(-0.38, 0.84, 0.0), lean=0.3, foot_l=fl, foot_r=fr_, eye_glow=1.0, eye_fire=0.3,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.05, -0.08, 0.28), hand_r=V(-0.05, -0.10, 0.22),
            elbow_l=V(-0.8, -0.5, -0.1), elbow_r=V(0.8, -0.5, -0.1), hpitch=0.0)
        # drop under the sweep: deep crouch, right hand down to the ground, head tucked then looking up
        ground = V(-0.25, 0.0, -0.32)
        g.fig.set(hand_rw=ground)
        g.k(0.0, hand_rwb=0.0).k(0.10, 'out', hand_rwb=1.0)
        g.k(0.07, 'out3', root=V(-0.55, 0.42, 0.0), lean=0.75, hpitch=0.35, twist=0.1,
            foot_l=fl + V(0.15, 0, 0.05), foot_r=fr_ + V(-0.3, 0, -0.05), hand_l=V(0.10, 0.05, 0.25))
        g.k(0.30, root=V(-0.72, 0.40, 0.0), lean=0.62, hpitch=-0.35)
        g.k(0.875, root=V(-1.05, 0.38, 0.02), lean=0.50, hpitch=-0.55, eye_glow=1.4, twist=-0.15,
            hand_l=V(0.12, 0.10, 0.32))
        sl, sr = feet((0.75, 0.0), SY, 0.38, -0.40, 0.20, 'l')
        s.k(0, yaw=SY, root=V(0.75, 0.88, 0.0), lean=0.1, twist=0.75, foot_l=sl, foot_r=sr, eye_glow=1.0, eye_fire=0.5,
            fist_l=1.0, fist_r=1.0, hand_l=V(0.05, -0.15, 0.20), elbow_l=V(-0.8, -0.4, 0.2),
            hand_r=V(-0.45, 0.02, 0.30), elbow_r=V(0.4, -0.3, -0.8))
        # backhand sweep: right arm swings from across the body out to the side
        s.k(T, 'in', hand_r=V(0.05, 0.08, 0.62), twist=0.0)
        s.k(T + 0.07, 'out', hand_r=V(0.42, 0.10, 0.42), twist=-0.55, lean=0.05)
        s.k(0.875, hand_r=V(0.58, 0.02, 0.10), twist=-1.0, root=V(0.86, 0.90, 0.02), hpitch=0.35, lean=0.0)
        self.hitstop(T, 2)
        S, G = s.fig, g.fig
        self.flames = [fx.Flame(lambda t: S.pose(t)['Wr'], 'red', size=0.11, rise=0.7, src2=lambda t: S.pose(t)['Er'],
                                seg=(0.55, 1.0), seed=91, trail=0.55)]
        # low camera on the far side: Sukuna screen-left, Gojo low on the right
        self.cam = Cam(Ch(V(0.55, 0.75, 3.1)).key(0.875, V(-0.05, 0.62, 2.45)),
                       Ch(V(0.05, 1.05, 0.0)).key(0.875, V(-0.1, 0.95, 0.0)), fov=Ch(44.0).key(0.875, 40.0))
        self.cam.shake(T, 12, 0.25)

    def draw(self, fr, s):
        tau = self.tw(s)
        cs = self.cam.at(s)
        self.draw_set(fr, cs)
        actors = [self.g, self.s]
        self.shadows(fr, cs, tau, actors)
        draw_actors(fr, self.cam, s, tau, actors)
        fx.render_flames(fr, cs, self.flames, tau)
        a = s - self.T
        if 0 <= a < 0.12:
            q = cs.proj(self.s.fig.pose(tau)['Wr'])
            fx.streak_lines(fr, 0.0, int(s * 30), n=26, alpha=0.45 * (1 - a / 0.12), width=3, band=(q[1] - 160, q[1] + 120))


SHOTS = [S42, S43, S44, S45, S46, S47, S48, S49]
SEGMENTS = [(S42.t0, S49.t1)]
