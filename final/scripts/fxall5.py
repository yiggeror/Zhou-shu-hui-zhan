"""Full film, both versions (fifth pass): fxall4 (shot-by-shot cue sheet) with these changes from review:
  * eyes in shots 6, 14, 16, 17, 56, 66, 123: no particles (their drift fought the camera); the eyes are
    placed by hand (TRACK keyframes, snapped to the glowing pixels each frame) and get a glow with a hot
    core and a small cursed flame that licks upward from the eye and moves with it
  * Hollow Purple, gathering: no invented orbiting balls; the original Red and Blue balls (shot 121) are
    tracked and get a glow, a light trail along their own path, arcs between them as they close in, and
    the purple light where they fuse; shot 37 keeps only the purple glow and arcs at the hand
  * explosion shots 41 and 124 use the motion-captured redraw (v4): exact original timing, sharper and
    less blown out (the newer redraw drifted from the original there); no hit-stop frames inserted in the
    final explosion; sparks and lightning only in the explosion shots, never over the faces
  * new: Sukuna waking (shot 11): pulsing red rim light on his outline, cursed flames licking up from it,
    heat haze, a few embers rising off his body
  * new: opening clash and title (shots 2-3): arcs and light at the clash point; the title pulses with
    each glyph, a shock ring when it completes, a sheen across the white outlines, glowing red drips
  * everything else as fxall4
Base pictures: near-lossless videos on the 60 fps grid (base/A_*.mp4, base/B.mp4), render_v4 for V4_SHOTS.
usage: fxall5.py MODE WORKER NWORKERS     (env ONLY_CHUNK=i, TEST_AT=t96 TEST_N=frames, RANGE=a,b)
"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
MODE, WK, NW = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, S + "/pilot"); sys.path.insert(0, HERE)
import numpy as np, cv2
from fx import (W, H, XX, YY, Noise, Particles, camera, shake, chroma, shockwave, bloom, speed_lines,
                lightning, draw_bolts, finish, to8, impact, grade, energy_mask)
from eyedet import eyes as find_eyes

FPS = 60; DT = 1.0 / FPS; NSRC = 5760
ts = np.load(S + "/ts.npy"); fmap = np.load(S + "/work/fmap.npy")
units = json.load(open(S + "/work/units.json"))
SEGDIR = f"{HERE}/seg5{MODE}"; os.makedirs(SEGDIR, exist_ok=True)

C = dict(r=np.float32([0.28, 0.22, 1.0]), c=np.float32([1.0, 0.92, 0.35]), w=np.float32([1, 1, 1]),
         o=np.float32([0.3, 0.65, 1.0]), p=np.float32([1.0, 0.45, 0.95]), b=np.float32([1.0, 0.6, 0.25]))
WHITE = C["w"]; PURPLE = np.float32([1.0, 0.35, 0.85]); PINK = np.float32([1.0, 0.7, 1.0])
HITS = {  # 96 s timeline -> colour of the blow
    1.231: "w", 32.91: "p", 34.10: "p",
    35.40: "r", 35.95: "c", 36.40: "c", 36.83: "c", 36.93: "c", 37.03: "c", 37.22: "r",
    40.80: "w", 41.36: "r", 47.25: "w",
    55.79: "r", 56.07: "r", 56.35: "r", 56.92: "w", 57.61: "r",
    67.83: "c", 68.27: "c", 69.96: "o", 71.08: "c",
    73.14: "r", 74.29: "r", 75.01: "r", 78.69: "r", 80.85: "r", 82.99: "b", 89.63: "p",
}
HS = 3
MINOR = set(h for a, h in zip(sorted(HITS), sorted(HITS)[1:]) if h - a < 0.15)
# first-pass continuous events (full/events.json) minus the embers rising over the red sky (30.75 s)
EV = [e for e in json.load(open(S + "/full/events.json"))
      if e["kind"] in ("rise", "arcs", "orb", "pulse") and not (e["kind"] == "rise" and e["t0"] in (30.75, 91.87))]   # no screen-wide embers over the red sky or the final blast
SPIN = [(71.78, 74.05, "r", 1.0), (80.94, 83.38, "c", -1.0), (85.20, 86.35, "r", 1.0)]
ORB_T = [(71.78, 74.29, "r"), (80.94, 84.17, "c"), (85.20, 86.35, "r")]        # aura / arcs / haze
MERGE = [(32.29, 32.91, (0.47, 0.66)), (88.52, 89.65, None)]                   # Red + Blue -> purple
BLAST = [(32.91, 34.43), (89.65, 93.85)]
WHITEOUT = (93.85, 96.01)
A_FOR_B = set()
V4_SHOTS = {41, 124}                                    # explosions: motion-captured redraw (v4), both versions
BLAST_FX = {38, 39, 41, 124}                            # sparks / lightning of the blast only in these shots
# cue sheet: shot index (work/units.json) -> effect.  Every shot was looked at; shots not listed get only
# the timed events (hits, cut flash, Red/Blue/Purple, rising embers, pulse).
FIST = {0: "c", 1: "r", 2: "cr", 32: "c", 33: "c", 34: "c", 42: "c", 43: "c", 44: "r", 45: "c", 46: "c",
        47: "c", 48: "c", 49: "r", 67: "c", 72: "c", 73: "c", 74: "r", 75: "cr", 76: "cr", 77: "r", 88: "c",
        89: "c", 90: "c", 101: "r", 103: "r", 107: "r", 108: "r", 110: "r", 117: "c"}
LOOSE = {0, 1, 2, 42, 43, 44, 45, 46, 47, 48, 49, 67, 74, 75, 76, 77, 88, 89, 90, 107, 108, 110, 117}   # big fists
# eyes: colour, how many glowing eyes are in frame, strength (1 glow, 2-3 cursed energy in the eyes)
EYES = {8: "c11", 18: "r21",
        37: "c22", 40: "r21", 44: "c11", 45: "c22", 46: "r11", 50: "c22", 51: "r42", 54: "c23",
        59: "c23", 60: "r22", 61: "r32", 67: "c22", 69: "r22", 72: "c11", 75: "c11", 77: "r21",
        79: "c22", 80: "c12r22", 83: "c22", 86: "r11", 94: "c12", 96: "c23", 97: "c11", 102: "c13",
        111: "c12", 113: "c12", 116: "r22", 119: "c21",}
EYE_FROM = {14: 14.45}
# hand-placed eyes: shot -> [(colour, strength, radius px, [(t, x, y) keyframes at 1080p])]
# shots in EYE_LIFT only brighten the eye's own pixels (no light spilling out), fading in as the eyes open
EYE_LIFT = {14: (14.30, 14.62, 0.45), 17: (17.0, 17.0, 0.2), 66: (48.2, 48.2, 0.3), 106: (76.6, 76.6, 0.3), 122: (89.66, 89.66, 0.3)}   # (fade-in from, to, tight glow); 17 = silhouette
TRACK = {
    6: [("c", 1.0, 14, [(5.55, 840, 440), (5.72, 835, 435), (5.85, 840, 445), (5.98, 845, 425), (6.11, 845, 420), (6.25, 845, 445),
                        (6.38, 845, 425), (6.51, 850, 415), (6.64, 850, 420)]),
        ("c", 0.55, 10, [(5.55, 735, 455), (5.85, 730, 465), (6.25, 740, 465), (6.64, 745, 460)])],
    14: [("r", 1.0, 20, [(14.32, 700, 495), (14.40, 690, 500), (14.55, 720, 490), (14.69, 730, 500), (14.84, 690, 490), (14.98, 680, 470),
                         (15.13, 640, 470), (15.27, 530, 410)]),
         ("r", 1.0, 20, [(14.32, 1170, 490), (14.40, 1170, 490), (14.55, 1180, 490), (14.69, 1180, 490), (14.84, 1180, 480), (14.98, 1210, 470),
                         (15.13, 1210, 476), (15.27, 1330, 390)]),
         ("r", 0.45, 11, [(14.32, 570, 570), (14.98, 560, 560), (15.13, 520, 520)]),
         ("r", 0.45, 11, [(14.32, 1320, 590), (14.98, 1300, 560), (15.13, 1300, 530)])],
    16: [("c", 1.0, 16, [(16.76, 1140, 305), (16.79, 1180, 345), (16.83, 1210, 355), (16.86, 1220, 360), (16.90, 1225, 360),
                         (16.97, 1225, 370), (17.00, 1225, 375)]),
         ("c", 0.8, 13, [(16.79, 1385, 310), (16.86, 1385, 310), (16.90, 1400, 330), (17.00, 1390, 335)])],
    17: [("c", 1.0, 14, [(17.02, 1235, 370), (17.09, 1235, 370), (17.15, 1240, 375), (17.49, 1240, 380)]),
         ("c", 0.9, 12, [(17.02, 1405, 345), (17.09, 1405, 350), (17.15, 1405, 355), (17.49, 1410, 360)])],
    56: [("r", 1.0, 12, [(40.22, 930, 430), (40.26, 925, 425), (40.33, 915, 370), (40.39, 910, 365), (40.46, 910, 365), (40.60, 905, 370)]),
         ("r", 1.0, 12, [(40.22, 1020, 432), (40.26, 1015, 430), (40.33, 1020, 375), (40.39, 1025, 370), (40.46, 1020, 370), (40.60, 1020, 375)]),
         ("r", 0.4, 8, [(40.26, 895, 430), (40.33, 878, 373), (40.60, 868, 375)]),
         ("r", 0.4, 8, [(40.26, 1045, 435), (40.33, 1060, 380), (40.60, 1062, 378)])],
    66: [("c", 1.0, 18, [(48.22, 1210, 300), (48.50, 1225, 300), (48.74, 1230, 300), (48.98, 1235, 305), (49.23, 1240, 310),
                         (49.71, 1250, 310), (49.95, 1250, 310)]),
         ("c", 0.7, 10, [(48.22, 1410, 410), (48.50, 1405, 410), (49.95, 1410, 410)])],
    106: [("c", 1.0, 9, [(76.62, 1110, 400), (76.83, 1112, 400), (76.98, 1116, 400), (77.87, 1120, 400), (78.08, 1116, 406)]),
          ("c", 1.0, 9, [(76.62, 1244, 446), (76.83, 1244, 450), (77.87, 1240, 450), (78.08, 1244, 454)])],
    122: [("r", 1.0, 12, [(89.66, 1396, 304), (89.85, 1396, 304), (90.04, 1400, 300), (90.23, 1404, 300), (90.41, 1410, 290), (90.60, 1418, 284)]),
          ("r", 0.9, 8, [(89.66, 1480, 340), (89.85, 1480, 340), (90.04, 1486, 336), (90.23, 1490, 334), (90.41, 1494, 330), (90.60, 1502, 330)]),
          ("r", 0.5, 6, [(89.66, 1210, 216), (89.85, 1204, 212), (90.04, 1196, 210), (90.13, 1196, 206)])],
    123: [("c", 1.0, 26, [(90.72, 1115, 415), (90.88, 1120, 410), (91.05, 1120, 390), (91.21, 1120, 380), (91.37, 1115, 360),
                          (91.53, 1110, 350), (91.70, 1110, 335), (91.86, 1060, 325)])],
}
# the original Red and Blue balls of the final gathering (shot 121), keyframes snapped to the balls each frame
BALLS = {"r": [(88.52, 750, 186), (88.79, 812, 192), (89.06, 864, 194), (89.29, 920, 184), (89.42, 930, 175), (89.52, 955, 172)],
         "b": [(88.52, 1160, 175), (88.67, 1132, 190), (88.79, 1106, 198), (89.06, 1056, 194), (89.29, 1010, 185), (89.42, 995, 172),
               (89.52, 965, 172)]}
FUSE_T = 89.52
WAKE = -1                                               # (rim-light treatment of Sukuna waking: dropped)
FIRSTPASS = {5, 9, 11, 19}                              # Gojo's eyes opening, Sukuna's markings / waking / red eyes: first-pass look
FP_ROI = {19: [[(18.50, 1050, 500), (18.69, 1057, 472), (19.08, 1042, 442), (19.47, 1017, 440)],     # only around the eyes
               [(18.50, 1550, 535), (18.69, 1525, 522), (19.08, 1522, 480), (19.47, 1533, 465)]]}  # (not the red sky)
CLASH, TITLE = 2, 3
TITLE_BEATS = [1.670, 1.727, 1.808, 1.854]              # each glyph lands; the last completes the title

def ease(x):
    x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def eout(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3
def inside(t, segs):
    return next((s for s in segs if s[0] <= t < s[1]), None)
def src_i(t):
    return max(0, int(np.searchsorted(ts, t + 1e-6, side="right")) - 1)
UNIT_OF_SRC = np.zeros(len(ts), np.int32)
for j, x in enumerate(units):
    UNIT_OF_SRC[x["start"]:x["end"]] = j
def unit_of_t(t):
    return int(UNIT_OF_SRC[src_i(t)])
def eye_spec(ui, t):
    e = EYES.get(ui, "")
    if not e or t < EYE_FROM.get(ui, 0): return {}
    return {e[i]: (int(e[i + 1]), int(e[i + 2])) for i in range(0, len(e), 3)}

# ---------------------------------------------------------------- timeline + chunks (as fxall.py)
timeline = []
pending = sorted(HITS)
for n in range(NSRC):
    t = n / FPS
    while pending and pending[0] <= t:
        h = pending.pop(0)
        for k in range(1 if h in MINOR else HS):
            timeline.append((n, t, k if h not in MINOR else 2, h))
    timeline.append((n, t, -1, None))
chunks = []; start = 0
for i in range(1, len(timeline) + 1):
    if i == len(timeline) or (unit_of_t(timeline[i][1]) != unit_of_t(timeline[i - 1][1]) and i - start >= 150):
        chunks.append((start, i)); start = i
loads = [0] * NW; mine = []
for ci in sorted(range(len(chunks)), key=lambda c: -(chunks[c][1] - chunks[c][0])):
    j = int(np.argmin(loads)); loads[j] += chunks[ci][1] - chunks[ci][0]
    if j == WK: mine.append(ci)

# ---------------------------------------------------------------- base pictures (sequential decode)
A_FILES = [(k * 1920, min(NSRC, (k + 1) * 1920), f"{HERE}/base/A_{k}.mp4") for k in range(3)]
B_FILES = [(0, NSRC, f"{HERE}/base/B.mp4")]
class Reader:
    def __init__(self, files):
        self.files = files; self.p = None; self.n = None
    def _open(self, n):
        if self.p: self.p.kill()
        a, b, f = next(x for x in self.files if x[0] <= n < x[1])
        self.lim = b
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{(n - a - 0.4) / FPS:.5f}", "-i", f,
                                   "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
        self.n = n - 1
    def get(self, n):
        if self.p is None or n <= self.n or n > self.n + 30 or n >= self.lim:
            self._open(n)
        while self.n < n:
            buf = self.p.stdout.read(W * H * 3); self.n += 1
        return np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    def close(self):
        if self.p: self.p.kill()

# ---------------------------------------------------------------- energy detection (no backdrops)
def hue_mask(hsv, kind):
    h, s, v = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    if kind == "c":
        hm = np.clip(1 - np.abs(h - 93) / 20, 0, 1)
    else:
        hm = np.clip(1 - np.minimum(np.abs(h - 0), np.abs(h - 180)) / 13, 0, 1)
    return hm * np.clip((s - 0.35) / 0.3, 0, 1) * np.clip((v - 0.35) / 0.3, 0, 1)

def energy(img, loose=False):
    """-> {c, r}: energy masks at 1080p; coloured areas that span the frame are left out
    (loose: shots with huge energy fists, only areas covering most of the frame are left out)"""
    small = cv2.resize(np.clip(img, 0, 1), (480, 270), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor((small * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    A = 480 * 270; out = {}
    for kind in ("c", "r"):
        m = hue_mask(hsv, kind)
        n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0.3).astype(np.uint8), 8)
        keep = np.ones(n, np.float32); keep[0] = 0
        for j in range(1, n):
            x, y, w, h, area = st[j]
            touch = int(x == 0) + int(y == 0) + int(x + w >= 480) + int(y + h >= 270)
            if area > 0.4 * A or w > 0.85 * 480 or (not loose and ((touch >= 2 and area > 0.1 * A) or (y == 0 and w > 0.45 * 480 and h < 0.5 * 270))):
                keep[j] = 0
        km = cv2.dilate(keep[lab], np.ones((5, 5), np.uint8))
        mm = cv2.GaussianBlur(m * km, (0, 0), 0.8)
        out[kind] = cv2.resize(mm, (W, H), interpolation=cv2.INTER_LINEAR)
    return out

def centroid(m):
    s = float(m.sum()); return None if s < 80 else (float((m * XX).sum() / s), float((m * YY).sum() / s))

def orb_blob(m):
    b = (cv2.resize(m, (480, 270)) > 0.3).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(b, 8)
    if n < 2: return None
    j = 1 + int(np.argmax(st[1:, 4])); x, y, w, h, area = st[j]
    if area < 120 or area / (np.pi * (max(w, h) / 2) ** 2 + 1e-6) < 0.45: return None
    return float(cen[j][0] * 4), float(cen[j][1] * 4), float(max(w, h) * 4 * 0.55)

def spin(out, blob, ang):
    cx, cy, r = blob
    M = cv2.getRotationMatrix2D((cx, cy), float(np.degrees(ang)), 1.0)
    rot = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = np.clip((r - np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)) / (0.25 * r), 0, 1)[..., None]
    return out * (1 - a) + rot * a

def haze(img, cx, cy, r, tout, amp):
    """heat distortion in a ring around an energy source"""
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    m = np.exp(-((d - r) / (r * 0.8 + 40)) ** 2) * amp
    dx = NX.field(tout * 2.0, (0, -1), 160) * m; dy = NY.field(tout * 2.0 + 5.0, (0, -1), 160) * m
    return cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def eye_glow(glints, col, t):
    """soft glow around glowing eyes, half resolution"""
    lay = np.zeros((H // 2, W // 2), np.float32); acc = np.zeros((H // 2, W // 2, 3), np.float32)
    for k, (x, y, r, s) in enumerate(glints):
        lay[:] = 0
        cv2.circle(lay, (int(x / 2), int(y / 2)), max(1, int(r * 0.35)), 1.0, -1, cv2.LINE_AA)
        fl = 0.9 + 0.1 * np.sin(t * 7 + k * 1.9)
        g = cv2.GaussianBlur(lay, (0, 0), 2 + r * 0.35) * 0.9 + cv2.GaussianBlur(lay, (0, 0), 7 + r * 0.9) * 0.7
        acc += g[..., None] * col * fl
    return cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)

def purple_center(img, prev, anchor=None):
    """where Hollow Purple is gathering: the compact bright magenta light (else the shot's anchor)"""
    hsv = cv2.cvtColor((np.clip(cv2.resize(img, (480, 270)), 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    m = np.clip(1 - np.abs(hsv[..., 0] - 148) / 18, 0, 1) * np.clip((hsv[..., 1] / 255 - 0.25) / 0.2, 0, 1) * np.clip((hsv[..., 2] / 255 - 0.6) / 0.2, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 4)
    if m.sum() < 30 or (m > 0.3).mean() > 0.12:
        if anchor is not None:
            c = (anchor[0] * W, anchor[1] * H)
            return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)
        return bright_center(img, prev)
    y, x = np.unravel_index(int(np.argmax(m)), m.shape)
    c = (float(x * 4), float(y * 4))
    return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)

def bright_center(img, prev):
    """centre of the blinding light; keeps the previous one when the whole frame is white"""
    g = cv2.cvtColor(np.clip(cv2.resize(img, (480, 270)), 0, 1), cv2.COLOR_BGR2GRAY)
    b = np.clip((g - 0.85) / 0.1, 0, 1)
    if b.mean() > 0.85 or b.sum() < 20:
        return prev if prev is not None else (W / 2, H * 0.4)
    yy, xx = np.mgrid[0:270, 0:480]
    c = (float((b * xx).sum() / b.sum() * 4), float((b * yy).sum() / b.sum() * 4))
    return c if prev is None else (prev[0] * 0.8 + c[0] * 0.2, prev[1] * 0.8 + c[1] * 0.2)

def kf(keys, t):
    ts_ = [k[0] for k in keys]
    return float(np.interp(t, ts_, [k[1] for k in keys])), float(np.interp(t, ts_, [k[2] for k in keys]))

def snap(img, kind, p, R=44):
    """centre of the glowing pixels of colour `kind` near p -> (x, y), visibility 0..1"""
    x0, y0 = max(0, int(p[0] - R)), max(0, int(p[1] - R)); x1, y1 = min(W, int(p[0] + R)), min(H, int(p[1] + R))
    if x1 - x0 < 8 or y1 - y0 < 8:
        return p, 0.0
    q = np.clip(img[y0:y1, x0:x1], 0, 1); Bc, Gc, Rc = q[..., 0], q[..., 1], q[..., 2]; V = q.max(-1)
    if kind == "c":
        tint = (np.minimum(Bc, Gc) - Rc) / (V + 0.05)
    elif kind == "r":
        tint = (Rc - np.maximum(Gc, Bc)) / (V + 0.05)
    elif kind == "rb":                                   # pink-red ball
        tint = (Rc - Bc) / (V + 0.05) + 0.2
    else:                                                # blue-violet ball
        tint = (Bc - Rc) / (V + 0.05) + 0.2
    w = np.clip((tint - 0.15) / 0.3, 0, 1) * np.clip((V - 0.3) / 0.3, 0, 1)
    w = np.clip(w - cv2.GaussianBlur(w, (0, 0), 12), 0, None)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    w = w * np.exp(-((xx - p[0]) ** 2 + (yy - p[1]) ** 2) / (2 * (R * 0.6) ** 2))
    sw = float(w.sum())
    if sw < 3:
        return p, 0.0
    return (float((w * xx).sum() / sw), float((w * yy).sum() / sw)), min(1.0, sw / 25)

_r = np.random.default_rng(5)
_n = np.tile(_r.standard_normal((256, 256)).astype(np.float32), (3, 3))     # blur a tiled copy -> seamless wrap
NT = cv2.GaussianBlur(_n, (0, 0), 6)[256:512, 256:512].copy()
NT = (NT - NT.mean()) / (NT.std() + 1e-6)

def eye_lift(img, kind, p, rad, s, glow=0.45):
    """brighten the glowing eye's own pixels plus a tight glow -> (add to picture, add to light) at 1080p"""
    R = int(rad * 2.4) + 6
    x0, y0 = max(0, int(p[0] - R)), max(0, int(p[1] - R)); x1, y1 = min(W, int(p[0] + R)), min(H, int(p[1] + R))
    a = np.zeros((H, W, 3), np.float32); g = np.zeros((H, W, 3), np.float32)
    if x1 - x0 < 8 or y1 - y0 < 8 or s <= 0.01:
        return a, g
    q = np.clip(img[y0:y1, x0:x1], 0, 1); Bc, Gc, Rc = q[..., 0], q[..., 1], q[..., 2]; V = q.max(-1)
    tint = (np.minimum(Bc, Gc) - Rc) / (V + 0.05) if kind == "c" else (Rc - np.maximum(Gc, Bc)) / (V + 0.05)
    m = np.clip((tint - 0.15) / 0.3, 0, 1) * np.clip((V - 0.25) / 0.3, 0, 1)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    m = m * np.exp(-((xx - p[0]) ** 2 + (yy - p[1]) ** 2) / (2 * (rad * 1.3) ** 2))
    a[y0:y1, x0:x1] = q * m[..., None] * 0.8 * s
    g[y0:y1, x0:x1] = cv2.GaussianBlur(m, (0, 0), 2.5)[..., None] * C[kind] * glow * s
    return a, g

def eye_fire(eyes, t):
    """glow + hot core + a small flame licking upward from each eye, drawn in the eye's own frame"""
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for k, (x, y, r, s, col) in enumerate(eyes):
        if s <= 0.02:
            continue
        r2 = r / 2.0; P = int(r2 * 7) + 8; cx, cy = int(x / 2), int(y / 2)
        yy, xx = np.mgrid[-P:P, -P:P].astype(np.float32)
        core = np.exp(-(xx ** 2 + (yy * 1.25) ** 2) / (2 * (r2 * 0.45) ** 2))
        halo = np.exp(-(xx ** 2 + yy ** 2) / (2 * (r2 * 1.5) ** 2))
        up = np.exp(-(xx ** 2) / (2 * (r2 * 1.0) ** 2)) * np.where(yy < 0, np.exp(-(yy ** 2) / (2 * (r2 * 3.2) ** 2)), np.exp(-(yy ** 2) / (2 * (r2 * 0.7) ** 2)))
        mx = ((xx / (r2 * 2.2) + k * 31.0) * 6) % 256; my = ((yy / (r2 * 2.2) + t * 2.6 + k * 17.0) * 6) % 256
        nz = cv2.remap(NT, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        flame = up * np.clip(0.55 + 0.45 * nz, 0, 1.3) * (1 - 0.6 * core)
        fl = 0.9 + 0.1 * np.sin(t * 9.0 + k * 2.1)
        patch = core[..., None] * (WHITE * 0.35 + col * 0.65) * 0.8 + halo[..., None] * col * 0.65 + flame[..., None] * col * 0.8
        patch = cv2.GaussianBlur(patch, (0, 0), 0.8) * s * fl
        ya, xa = cy - P, cx - P; yb, xb = ya + 2 * P, xa + 2 * P
        ys0, xs0 = max(0, -ya), max(0, -xa); ya, xa = max(0, ya), max(0, xa); yb, xb = min(H // 2, yb), min(W // 2, xb)
        if yb > ya and xb > xa:
            lay[ya:yb, xa:xb] += patch[ys0:ys0 + yb - ya, xs0:xs0 + xb - xa]
    return cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)

def v4_frame(t):
    u = int(fmap[src_i(t)])
    return cv2.imread(f"{S}/render_v4/u{u:05d}.jpg").astype(np.float32) / 255

def wake_masks(img):
    """Sukuna against the red backdrop: silhouette and its outline (rim) at 480x270"""
    sm = cv2.GaussianBlur(cv2.resize(np.clip(img, 0, 1), (480, 270), interpolation=cv2.INTER_AREA), (0, 0), 1.2)
    hsv = cv2.cvtColor((sm * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    s_, v = hsv[..., 1] / 255, hsv[..., 2] / 255
    back = (s_ > 0.8) & (v > 0.06)                        # the backdrop is far more saturated than he is
    dark = ((v < 0.09) & ~back).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, 8)
    ground = np.zeros(dark.shape, bool)
    for j in range(1, n):
        x, y, w, h, area = st[j]
        if y + h >= 268 and w > 200:
            ground |= lab == j
    body = (~back & ~ground).astype(np.uint8)
    body = cv2.morphologyEx(body, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(body, 8)
    if n < 2:
        return None
    j = 1 + int(np.argmax(st[1:, 4]))
    if st[j, 4] < 2000 or st[j, 4] > 0.5 * 480 * 270:
        return None
    body = cv2.morphologyEx((lab == j).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)).astype(np.float32)
    rim = np.clip(cv2.dilate(body, np.ones((5, 5), np.uint8)) - body, 0, 1) * back
    rim[176:212, 100:240] = 0                              # never outline the watermark
    return body, rim

def shoulder(out, k0=0.72, top=0.94):
    """compress highlights smoothly so the explosion keeps its texture instead of clipping to white"""
    L = out.max(-1, keepdims=True)
    over = np.maximum(L - k0, 0)
    newL = k0 + (top - k0) * (1 - np.exp(-over / (top - k0)))
    return out * np.where(L > k0, newL / (L + 1e-6), 1.0)

# ---------------------------------------------------------------- chunk renderer
NX, NY = Noise(41), Noise(42)

def render_chunk(ci, a0=None, a1=None, fn=None):
    if a0 is None:
        a0, a1 = chunks[ci]; fn = f"{SEGDIR}/c{ci:03d}.mp4"
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        return
    rng = np.random.default_rng(100 + ci)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-threads", "1", "-crf", "14",
                            "-tune", "animation", "-pix_fmt", "yuv420p", "-g", "120", fn + ".tmp.mp4"], stdin=subprocess.PIPE)
    main = Reader(A_FILES if MODE == "A" else B_FILES); alt = Reader(A_FILES) if MODE == "B" else None
    embers, sparks, swirl, burst, eyeP = Particles(), Particles(), Particles(), Particles(), Particles()
    trailE = None; last_unit = None; hit_state = {}; cut_n = -99; last_n = None; img0 = None; pc = None
    eyeS = {}; ballH = {"r": [], "b": []}
    for idx in range(a0, a1):
        n, t, hk, hkey = timeline[idx]
        tout = idx * DT
        ui = unit_of_t(t)
        if n != last_n:
            img0 = v4_frame(t) if ui in V4_SHOTS else main.get(n); last_n = n
        img = img0.copy()
        if ui != last_unit:
            if last_unit is not None: cut_n = idx
            trailE = None; embers = Particles(); swirl = Particles(); eyeP = Particles(); burst = Particles(); last_unit = ui
            eyeS = {}; ballH = {"r": [], "b": []}
        merge, blast = inside(t, MERGE), inside(t, BLAST)
        whiteout = WHITEOUT[0] <= t < WHITEOUT[1]
        en = energy(img, ui in LOOSE)
        mc, mr = en["c"], en["r"]
        E = np.zeros((H, W), np.float32)
        for k_ in FIST.get(ui, ""):
            E = np.maximum(E, en[k_])
        fp = ui in FIRSTPASS
        if fp:                                                     # first-pass detector and strengths
            E = np.maximum(energy_mask(img, "c"), energy_mask(img, "r"))
            if ui in FP_ROI:
                roi = np.zeros((H, W), np.float32)
                for keys in FP_ROI[ui]:
                    cx_, cy_ = kf(keys, t)
                    roi = np.maximum(roi, np.exp(-((XX - cx_) ** 2 + (YY - cy_) ** 2) / (2 * 110.0 ** 2)))
                E = E * roi
        ef = float(E.mean())
        extra = np.zeros((H, W, 3), np.float32)
        zoom, sh, chrom, bl = 1.0, (0.0, 0.0), 0.0, 1.0
        if 0.001 < ef < 0.25:                                     # cursed energy keeps burning
            m = cv2.GaussianBlur(cv2.dilate(E, np.ones((21, 21), np.uint8)), (0, 0), 10)
            fa = 6 if fp else 7
            dx = NX.field(tout * 1.4, (0, -1), 110) * fa * m; dy = (NY.field(tout * 1.4 + 3.1, (0, -1), 110) - 0.8) * fa * m
            img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        orb = inside(t, ORB_T); blob = None
        if orb:                                                   # Red / Blue: spin, aura, arcs, haze
            blob = orb_blob(mr if orb[2] == "r" else mc)
            if blob is not None:
                img = haze(img, blob[0], blob[1], blob[2] * 1.3, tout, 3.5)
                for t0, t1, ck, sg in SPIN:
                    if t0 <= t < t1:
                        img = spin(img, blob, sg * 5.0 * (t - t0))
        wm = wake_masks(img0) if ui == WAKE else None
        if wm is not None:
            aura = cv2.resize(cv2.GaussianBlur(cv2.dilate(wm[1], np.ones((9, 9), np.uint8)), (0, 0), 4), (W, H))
            m = np.clip(aura * 2.5, 0, 1)
            dx = NX.field(tout * 1.8, (0, -1), 140) * 3.5 * m; dy = (NY.field(tout * 1.8 + 2.0, (0, -1), 140) - 0.6) * 3.5 * m
            img = cv2.remap(img, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out = grade(img, sat=1.1)
        out = np.clip((out - 0.5) * 1.05 + 0.5, 0, None)
        ener = img * E[..., None] * float(ef < 0.25)
        trailE = ener * 0.6 if trailE is None else (trailE * 0.78 + ener * 0.4 if fp else trailE * 0.8 + ener * 0.42)
        out = out + np.maximum(trailE - ener * 1.5, 0) * (0.55 if fp else 0.7)   # afterimage of the moving energy
        out = out + cv2.GaussianBlur(ener, (0, 0), 24) * (0.25 if fp else 0.35) * max(0.0, 1 - ef * 4)
        if 0.001 < ef < 0.25 and hk < 0:                                   # embers from the energy
            pw = cv2.resize(E ** 2, (240, 135), interpolation=cv2.INTER_AREA).ravel().astype(np.float64)
            if pw.sum() > 0:
                k = int(min(60, 4000 * ef) if fp else min(80, 5000 * ef)); sel = rng.choice(len(pw), k, p=pw / pw.sum()); py, px = np.divmod(sel, 240)
                p = (np.stack([px, py], 1) * 8 + rng.uniform(0, 8, (k, 2))).astype(np.float32)
                cols = np.clip(img[np.clip(p[:, 1].astype(int), 0, H - 1), np.clip(p[:, 0].astype(int), 0, W - 1)] * 1.3, 0, 1.6)
                a = rng.normal(-np.pi / 2, 0.8, k); sp = rng.uniform(80, 320, k)
                embers.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cols, rng.uniform(0.3, 0.9, k), rng.uniform(0.8, 1.7, k))
        if blob is not None:                                      # orb aura + crackle
            col = C[orb[2]]; d = np.sqrt((XX - blob[0]) ** 2 + (YY - blob[1]) ** 2)
            extra += (np.exp(-((d - blob[2]) / (blob[2] * 0.35 + 10)) ** 2) * 0.45 + np.exp(-(d / (blob[2] * 2.2)) ** 2) * 0.25)[..., None] * col
            if idx % 3 == 0:
                for j in range(2):
                    a = rng.uniform(0, 2 * np.pi); r0 = blob[2] * 0.9; L = blob[2] * rng.uniform(1.2, 2.6)
                    p0 = (blob[0] + np.cos(a) * r0, blob[1] + np.sin(a) * r0)
                    extra += draw_bolts(lightning(p0, (blob[0] + np.cos(a) * (r0 + L), blob[1] + np.sin(a) * (r0 + L)), idx * 13 + j, depth=5, branches=2),
                                        tuple(float(v) for v in col), 1, 6) * 0.7
        # ---- eyes: soft glow
        for k_, (ne, lv) in eye_spec(ui, t).items():
            g = find_eyes(img0, k_, ne)
            if not g:
                continue
            extra += eye_glow(g, C[k_], tout) * ((0.5 if blast else 1.0) * (0.75 if lv == 1 else 1.0))
            if lv >= 2 and hk < 0:                                 # small flames and embers off the eyes
                for (ex, ey, er, _) in g:
                    k = 3 if lv == 2 else 7                         # sparks leave from around the eye
                    ra = rng.uniform(0, 2 * np.pi, k); rr = er * rng.uniform(0.7, 1.5, k)
                    p = np.stack([ex + np.cos(ra) * rr, ey + np.sin(ra) * rr * 0.6], 1)
                    a = rng.normal(-np.pi / 2, 0.6, k) * 0.6 + ra * 0.4 * 0 + rng.normal(0, 0.3, k)
                    a = np.where(np.sin(ra) < 0, -np.pi / 2 + (ra + np.pi / 2) * 0.5, -np.pi / 2 + rng.normal(0, 0.9, k))
                    sp = rng.uniform(120, 330, k) * (1 + 0.004 * er)
                    cc = (C[k_][None] * 0.85 + WHITE[None] * 0.15) * rng.uniform(0.9, 1.3, (k, 1))
                    sz = rng.uniform(1.1, 2.0, k) if lv == 2 else rng.uniform(1.4, 2.6, k) * (1 + 0.006 * er)
                    eyeP.emit(p, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.4, 0.9, k), sz)
                if lv == 3:
                    em = np.zeros((H // 4, W // 4), np.float32)
                    for (ex, ey, er, _) in g:
                        cv2.circle(em, (int(ex / 4), int(ey / 4)), max(3, int(er * 1.4 / 4)), 1.0, -1)
                    em = cv2.resize(cv2.GaussianBlur(em, (0, 0), 5), (W, H))
                    dx = NX.field(tout * 1.6, (0, -1), 90) * 6 * em; dy = (NY.field(tout * 1.6 + 2.0, (0, -1), 90) - 0.8) * 6 * em
                    out = cv2.remap(out, (XX + dx).astype(np.float32), (YY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # ---- hand-placed eyes: glow + flame that moves with the eye
        if ui in TRACK:
            fe = []
            for j, (kc_, st_, rad, keys) in enumerate(TRACK[ui]):
                if not (keys[0][0] - 0.03 <= t <= keys[-1][0] + 0.03):
                    continue
                p, vis = snap(img0, kc_, kf(keys, t))
                prev = eyeS.get(j)
                if prev is not None:
                    p = (prev[0][0] * 0.4 + p[0] * 0.6, prev[0][1] * 0.4 + p[1] * 0.6); vis = prev[1] * 0.5 + vis * 0.5
                eyeS[j] = (p, vis)
                if ui in EYE_LIFT:                                 # only the eye itself lights up, fading in as it opens
                    f0, f1, gl_ = EYE_LIFT[ui]
                    a_, g_ = eye_lift(img0, kc_, p, rad, st_ * vis * float(np.clip((t - f0) / max(f1 - f0, 1e-3), 0, 1)), gl_)
                    out = out + a_; extra += g_
                    continue
                fe.append((p[0], p[1], rad, st_ * vis * (0.5 if blast else 1.0), C[kc_]))
            if fe:
                extra += eye_fire(fe, tout)
        # ---- Sukuna waking: rim light, flames off the outline, embers
        if wm is not None:
            body, rim = wm
            ph = (t * 1.6) % 1.0                                   # heartbeat: thump-thump
            pulse = 0.6 + 0.4 * (np.exp(-ph / 0.12) + 0.6 * np.exp(-((ph - 0.28) % 1.0) / 0.12))
            rimF = cv2.resize(cv2.GaussianBlur(rim, (0, 0), 0.8), (W, H))
            glow = cv2.GaussianBlur(rimF, (0, 0), 3) * 1.4 + cv2.GaussianBlur(rimF, (0, 0), 12) * 1.3 + cv2.GaussianBlur(rimF, (0, 0), 30) * 0.8
            extra += glow[..., None] * np.float32([0.18, 0.3, 1.0]) * pulse
            fla = cv2.resize(cv2.GaussianBlur(cv2.dilate(rim, np.ones((7, 7), np.uint8)), (0, 0), 3), (W, H))
            nz = np.clip(NX.field(tout * 2.2, (0, -1), 160) * 0.7 + 0.35, 0, 1)
            fdx = NY.field(tout * 2.2 + 4.0, (0, -1), 160) * 10; fdy = 18 + NX.field(tout * 2.2 + 7.0, (0, -1), 160) * 8
            flame = cv2.remap(fla * nz, (XX + fdx).astype(np.float32), (YY + fdy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            extra += cv2.GaussianBlur(flame, (0, 0), 2)[..., None] * np.float32([0.12, 0.22, 1.0]) * 0.9 * pulse
            if hk < 0:
                ys_, xs_ = np.nonzero(rim > 0.5)
                if len(xs_):
                    k = 4; sel = rng.integers(0, len(xs_), k)
                    p = np.stack([xs_[sel] * 4 + rng.uniform(0, 4, k), ys_[sel] * 4 + rng.uniform(0, 4, k)], 1).astype(np.float32)
                    embers.emit(p, np.stack([rng.normal(0, 25, k), rng.uniform(-170, -60, k)], 1),
                                np.float32([0.3, 0.45, 1.0])[None] * rng.uniform(0.8, 1.3, (k, 1)), rng.uniform(0.5, 1.1, k), rng.uniform(1.0, 1.8, k))
        # ---- opening clash: light and arcs where the two fists meet
        if ui == CLASH:
            sr = np.argwhere(cv2.resize(mr, (240, 135)) > 0.3); sc_ = np.argwhere(cv2.resize(mc, (240, 135)) > 0.3)
            if len(sr) > 5 and len(sc_) > 5:
                sr = sr[:: max(1, len(sr) // 300)]; sc_ = sc_[:: max(1, len(sc_) // 300)]
                dm = ((sr[:, None, :] - sc_[None, :, :]) ** 2).sum(-1); i0, j0 = np.unravel_index(int(np.argmin(dm)), dm.shape)
                if dm[i0, j0] < 30 ** 2:
                    c = (float(sr[i0, 1] + sc_[j0, 1]) * 4, float(sr[i0, 0] + sc_[j0, 0]) * 4)
                    d = np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2)
                    extra += (np.exp(-(d / 60) ** 2) * 1.0 + np.exp(-(d / 200) ** 2) * 0.4)[..., None] * np.float32([1.0, 0.6, 1.0]) * (0.8 + 0.2 * np.sin(tout * 40))
                    if idx % 2 == 0:
                        for j, colr in enumerate((C["r"], C["c"], WHITE)):
                            a_ = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 360)
                            extra += draw_bolts(lightning(c, (c[0] + np.cos(a_) * L, c[1] + np.sin(a_) * L), idx * 19 + j, depth=6, branches=2),
                                                tuple(float(v) for v in colr), 1, 7) * 0.8
        # ---- title: pulse on each glyph, shock ring when complete, sheen, glowing drips
        if ui == TITLE:
            for tb in TITLE_BEATS:
                dtb = t - tb
                if 0 <= dtb < 0.14:
                    f_ = 1 - dtb / 0.14
                    Lp = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY)
                    out = out + (np.clip((Lp - 0.65) / 0.25, 0, 1) * 0.35 * f_)[..., None] * np.float32([1.0, 0.45, 0.9]) + 0.05 * f_
                    chrom = max(chrom, 0.014 * f_)
                    sh = shake(tout, 7 * f_ if tb == TITLE_BEATS[-1] else 3 * f_, 5)
            dtb = t - TITLE_BEATS[-1]
            if 0 <= dtb < 0.45:
                out, ring = shockwave(out, W / 2, H * 0.48, 1700 * eout(dtb / 0.45), 70, 26 * (1 - ease(dtb / 0.45)))
                extra += ring * np.float32([1.0, 0.55, 0.95]) * 0.9 * (1 - ease(dtb / 0.45))
            Lb = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY)
            if 1.88 <= t < 2.08:
                sx = (t - 1.88) / 0.2 * 1.5 - 0.25
                band = np.exp(-(((XX / W) * 0.75 + (YY / H) * 0.45) / 1.2 - sx) ** 2 / (2 * 0.05 ** 2))
                extra += (band * np.clip((Lb - 0.65) / 0.2, 0, 1))[..., None] * np.float32([1.0, 0.75, 1.0]) * 0.9
            q = np.clip(img0, 0, 1)
            red = np.clip(((q[..., 2] - np.maximum(q[..., 1], q[..., 0])) - 0.25) / 0.2, 0, 1) * np.clip((q[..., 2] - 0.4) / 0.2, 0, 1)
            red = np.clip(red - cv2.GaussianBlur(red, (0, 0), 20), 0, None)
            extra += (cv2.GaussianBlur(red, (0, 0), 3) * 2.6 + cv2.GaussianBlur(red, (0, 0), 12) * 2.2)[..., None] * C["r"] * (0.85 + 0.15 * np.sin(tout * 12))
            pur = np.clip(1 - np.abs(cv2.cvtColor((q * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)[..., 0].astype(np.float32) - 140) / 15, 0, 1) * np.clip((q.max(-1) - 0.45) / 0.2, 0, 1)
            pur = np.clip(pur - cv2.GaussianBlur(pur, (0, 0), 15), 0, None)
            extra += cv2.GaussianBlur(pur, (0, 0), 4)[..., None] * PURPLE * 1.5
        # ---- first-pass continuous events
        for ev in EV:
            if not (ev["t0"] <= t < ev["t1"]):
                continue
            col = np.float32(ev.get("col", [1.0, 0.85, 1.0]))
            if ev["kind"] == "rise" and idx % 2 == 0:
                m_ = 30; p = np.stack([rng.uniform(0, W, m_), rng.uniform(H * 0.45, H, m_)], 1)
                embers.emit(p, np.stack([rng.normal(0, 30, m_), rng.uniform(-280, -90, m_)], 1), col[None] * rng.uniform(0.5, 1.2, (m_, 1)), rng.uniform(0.8, 1.8, m_), 1.3)
            elif ev["kind"] == "arcs" and idx % 2 == 0:
                c = (pc if (merge and pc is not None) else None) or centroid(np.maximum(mc, mr))
                if c is not None:
                    for j in range(int(ev.get("n", 2))):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(120, 420)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 11 + j, depth=6, branches=2), tuple(float(v) for v in col), 1, 7) * 0.8
            elif ev["kind"] == "orb":
                c = (blob[0], blob[1]) if blob is not None else None    # only around a found orb
                if c is not None:
                    rr = blob[2]
                    m_ = 160; a = rng.uniform(0, 2 * np.pi, m_); r0 = rr * rng.uniform(0.9, 2.2, m_)
                    p = np.stack([c[0] + np.cos(a) * r0, c[1] + np.sin(a) * r0], 1)
                    tang = np.stack([-np.sin(a), np.cos(a)], 1) * rng.uniform(300, 800, (m_, 1)) * ev.get("spin", 1)
                    swirl.emit(p, tang, col[None] * rng.uniform(0.6, 1.3, (m_, 1)), rng.uniform(0.25, 0.6, m_), rng.uniform(0.9, 1.6, m_))
            elif ev["kind"] == "pulse":
                x = (t - ev["t0"]) / (ev["t1"] - ev["t0"]); d = np.sqrt((XX - W / 2) ** 2 + (YY - H / 2) ** 2)
                for k3 in range(3):
                    ph = (x * 3 + k3 / 3) % 1
                    extra += (np.exp(-((d - 120 - 900 * ph) / 6.0) ** 2) * (1 - ph) * 0.6)[..., None] * col
        # ---- Hollow Purple, gathering: glow at the hand (shot 37) / the original Red and Blue balls (shot 121)
        if merge:
            x = (t - merge[0]) / (merge[1] - merge[0])
            if merge[2] is not None:                               # shot 37: the light gathering at the hand
                pc = purple_center(img, pc, merge[2]); c = pc
                d = np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2)
                extra += (np.exp(-(d / (40 + 180 * x)) ** 2) * (0.3 + 0.7 * x ** 2))[..., None] * PURPLE
            else:                                                  # shot 121: track the two balls
                pos = {}
                for kb, kind, col in (("r", "rb", np.float32([0.75, 0.35, 1.0])), ("b", "bb", np.float32([1.0, 0.55, 0.45]))):
                    p, vis = snap(img0, kind, kf(BALLS[kb], min(t, FUSE_T)), R=40)
                    ballH[kb].append(p); ballH[kb] = ballH[kb][-16:]; pos[kb] = p
                    lay = np.zeros((H // 2, W // 2, 3), np.float32)
                    pts = ballH[kb]
                    for j in range(1, len(pts)):                     # light trail along the ball's own path
                        f_ = j / len(pts)
                        cv2.line(lay, (int(pts[j - 1][0] / 2), int(pts[j - 1][1] / 2)), (int(pts[j][0] / 2), int(pts[j][1] / 2)),
                                 tuple(float(v) * f_ for v in col), max(1, int(5 * f_)), cv2.LINE_AA)
                    cv2.circle(lay, (int(p[0] / 2), int(p[1] / 2)), 6, tuple(float(v) for v in (col * 0.5 + WHITE * 0.5)), -1, cv2.LINE_AA)
                    extra += cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.0) * 1.2 + cv2.GaussianBlur(lay, (0, 0), 5) * 2.2 + cv2.GaussianBlur(lay, (0, 0), 16) * 1.4,
                                        (W, H), interpolation=cv2.INTER_LINEAR)
                dd = float(np.hypot(pos["r"][0] - pos["b"][0], pos["r"][1] - pos["b"][1]))
                c = ((pos["r"][0] + pos["b"][0]) / 2, (pos["r"][1] + pos["b"][1]) / 2); pc = c
                if dd < 300 and idx % 2 == 0:                      # arcs jump between them as they close in
                    for j in range(2):
                        extra += draw_bolts(lightning(pos["r"], pos["b"], idx * 23 + j, jag=0.15, depth=5, branches=0), (1.0, 0.55, 1.0), 1, 6) * (0.35 + 0.5 * (1 - dd / 300))
                fuse = float(np.clip(1 - dd / 250, 0, 1)) if t < FUSE_T else 1.0
                d = np.sqrt((XX - c[0]) ** 2 + (YY - c[1]) ** 2)
                extra += (np.exp(-(d / (30 + 160 * fuse)) ** 2) * (0.15 + 0.8 * fuse ** 2))[..., None] * PURPLE
            bl *= 0.6
        # ---- Hollow Purple: the blast
        if blast or whiteout:
            pc = bright_center(img, pc)
            out = shoulder(out)
            if blast:
                c = pc
                Lm = float(cv2.resize(cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_BGR2GRAY), (96, 54)).mean())
                core = float((cv2.cvtColor(np.clip(cv2.resize(img, (96, 54)), 0, 1), cv2.COLOR_BGR2GRAY) > 0.85).mean())
                if 0.01 < core < 0.6 and ui in BLAST_FX:           # sparks thrown from a visible core
                    m_ = 14; a = rng.uniform(0, 2 * np.pi, m_); sp = rng.uniform(200, 650, m_); r0 = rng.uniform(40, 160, (m_, 1))
                    cc = np.where(rng.random((m_, 1)) < 0.3, PINK[None], PURPLE[None]) * rng.uniform(0.8, 1.4, (m_, 1))
                    burst.emit(np.float32(c)[None] + np.stack([np.cos(a), np.sin(a)], 1) * r0, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.2, 0.4, m_), rng.uniform(1.8, 3.0, m_))
                if idx % 2 == 0 and Lm < 0.82 and core > 0.01 and ui in BLAST_FX:           # never over the faces
                    for j in range(2):
                        a = rng.uniform(0, 2 * np.pi); L = rng.uniform(200, 520)
                        extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 5 + j, depth=6, branches=3), (1.0, 0.45, 0.95), 2, 9) * 0.75
            bl *= 0.35
        # ---- hits
        if hkey is not None:
            ck = HITS[hkey]; col = C[ck]
            if hkey not in hit_state:
                m = mc if ck in "cb" else (mr if ck in "ro" else None)
                c = (centroid(m) if m is not None else None) or bright_center(img, None)
                hit_state[hkey] = dict(xy=c, n=idx)
                m_ = 400 if ck == "p" else (700 if hkey in MINOR else 2500); a = rng.uniform(0, 2 * np.pi, m_); sp = rng.uniform(400, 2400, m_)
                cc = np.where(rng.random((m_, 1)) < 0.2, WHITE[None] * 1.2, col[None] * rng.uniform(0.7, 1.3, (m_, 1)))
                r0 = rng.uniform(20, 90, (m_, 1))
                sparks.emit(np.float32(c)[None] + np.stack([np.cos(a), np.sin(a)], 1) * r0, np.stack([np.cos(a) * sp, np.sin(a) * sp], 1), cc, rng.uniform(0.2, 0.8, m_), rng.uniform(0.9, 2.2, m_))
            if ck == "p":                                           # Hollow Purple: purple flash, no white
                if hk == 0:
                    out = out * 0.55 + PURPLE * 0.38
                elif hk == 1:
                    two = impact(out, "bw", True, 0.5)
                    out = two * PURPLE * 0.92 + (1 - two) * np.float32([0.08, 0.0, 0.06])
            else:
                if hk == 0:
                    out = out * 0.2 + 0.95
                elif hk == 1:
                    two = impact(out, "bw", True, 0.42)
                    out = two * (col if ck != "w" else np.float32([0.9, 0.9, 0.95])) + (1 - two) * np.float32([0.03, 0.0, 0.05])
            sh = shake(tout, 22, 3)
        for hk2, st in hit_state.items():
            dt = (idx - st["n"]) * DT
            if dt > 0.7:
                continue
            col = C[HITS[hk2]]; c = st["xy"]
            out, ring = shockwave(out, c[0], c[1], 1800 * eout(dt / 0.55), 80, 34 * (1 - ease(dt / 0.55)))
            extra += ring * col * 1.4 * (1 - ease(dt / 0.55))
            if dt < 0.22:
                extra += speed_lines(c[0], c[1], tout, n=130, inner=220, color=tuple(float(v) for v in (WHITE * 0.6 + col * 0.4))) * 0.7 * (1 - dt / 0.22)
            if dt < 0.3 and idx % 2 == 0:
                for j in range(3):
                    a = rng.uniform(0, 2 * np.pi); L = rng.uniform(250, 650)
                    extra += draw_bolts(lightning(c, (c[0] + np.cos(a) * L, c[1] + np.sin(a) * L), idx * 7 + j), tuple(float(v) for v in col), 2, 9) * (1 - dt / 0.3)
            if hkey is None:
                sh = shake(tout, 18 * (1 - ease(dt / 0.35)), 4)
            zoom *= 1 + 0.05 * (1 - eout(dt / 0.3))
            chrom = max(chrom, 0.012 * (1 - ease(dt / 0.35))); bl += (0.25 if hk2 in MINOR else 0.5) * (1 - ease(dt / 0.35))
        kc = idx - cut_n                                          # soft flash on hard cuts
        if 0 <= kc < 2 and hkey is None and not (blast or whiteout):
            out = out + (0.16 if kc == 0 else 0.05); chrom = max(chrom, 0.008 * (1 - kc / 2))
        embers.step(DT, 0.95, (0, -60)); sparks.step(DT, 0.955, (0, 140)); swirl.step(DT, 0.9, (0, 0)); burst.step(DT, 0.93, (0, 0)); eyeP.step(DT, 0.97, (0, -70))
        if len(embers.p): extra += embers.render(glow=3.5, gain=1.1)
        if len(sparks.p): extra += sparks.render(glow=4.0, gain=0.75)
        if len(swirl.p): extra += swirl.render(glow=3.5, gain=0.85)
        if len(burst.p): extra += burst.render(glow=4.0, gain=0.8)
        if len(eyeP.p): extra += eyeP.render(glow=3.0, gain=1.0)
        out = out + extra
        if zoom != 1.0 or sh != (0.0, 0.0):
            out = camera(out, zoom, W / 2, H / 2, 0.0, sh, cv2.BORDER_REFLECT)
        if chrom > 0:
            out = chroma(out, W / 2, H / 2, chrom * 0.5)
        mL = float(cv2.resize(np.clip(out, 0, 1), (96, 54)).mean())
        bl *= float(np.clip((0.8 - mL) / 0.35, 0.2, 1.0))              # already-bright frames: less glare
        out = bloom(out, 0.85, 0.4 * min(bl, 1.7))
        if blast or whiteout:
            out = shoulder(out, 0.8, 0.96)
        out = finish(out, grain=0.008, vignette=0.28, t=tout)
        enc.stdin.write(to8(out).tobytes())
    enc.stdin.close(); enc.wait()
    main.close()
    if alt is not None: alt.close()
    os.replace(fn + ".tmp.mp4", fn)

if os.environ.get("RANGE"):
    a0, a1 = (int(v) for v in os.environ["RANGE"].split(","))
    f = f"{SEGDIR}/range_{a0}_{a1}.mp4"
    if os.path.exists(f): os.remove(f)
    render_chunk(0, a0, a1, f); print("range", f); sys.exit(0)
if os.environ.get("TEST_AT"):
    a0 = next(i for i, x in enumerate(timeline) if x[1] >= float(os.environ["TEST_AT"]))
    a1 = min(len(timeline), a0 + int(os.environ.get("TEST_N", "60")))
    f = f"{SEGDIR}/test_{a0}.mp4"
    if os.path.exists(f): os.remove(f)
    render_chunk(0, a0, a1, f); print("test", f); sys.exit(0)
if os.environ.get("ONLY_CHUNK"):
    mine = [int(os.environ["ONLY_CHUNK"])]
    f = f"{SEGDIR}/c{mine[0]:03d}.mp4"
    if os.path.exists(f): os.remove(f)
json.dump(dict(frames=len(timeline), chunks=chunks), open(f"{SEGDIR}/plan.json", "w"))
for ci in sorted(mine):
    render_chunk(ci)
    print("chunk", ci, chunks[ci], flush=True)
print("done", WK)
