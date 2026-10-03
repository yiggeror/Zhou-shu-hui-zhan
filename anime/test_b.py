"""Test B: shot 0 (Gojo's burning fist thrown at the lens), frames 73-91 at 24 fps, from Limo's
paired drawings in collab/from_limo/002/test_B/ (Bxx_char = no flame, Bxx_char_fx = same drawing
with flame).  Usage: python3 anime/test_b.py OUT.mp4"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
import numpy as np
from anime import comp as C

SRC = 'collab/from_limo/002/test_B'
F0, F1 = 73, 91
# exposure: on twos, the last two drawings on ones so the shot keeps its 18 frames
SHEET = [(73, 'B01'), (75, 'B02'), (77, 'B03'), (79, 'B04'), (81, 'B05'), (83, 'B06'), (85, 'B07'), (87, 'B08'),
         (89, 'B09'), (90, 'B10')]
CYAN = (0.25, 0.85, 1.0)


def flame_layer(fx, ch):
    """premultiplied flame layer from a 'with flame' / 'without flame' pair: pixels that changed a
    lot or are strongly cyan, cleaned of thin line-jitter differences, feathered by a pixel"""
    a_fx, a_ch = fx[..., 3], ch[..., 3]
    d = np.abs(fx[..., :3] - ch[..., :3]).max(-1)
    changed = (d > 0.16).astype(np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    c = fx[..., :3] / np.maximum(a_fx[..., None], 1e-4)
    cyan = ((np.minimum(c[..., 1], c[..., 2]) - c[..., 0] > 0.28) & (c[..., 2] > 0.55) & (a_fx > 0.5)).astype(np.uint8)
    m = cv2.morphologyEx(changed | cyan, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # flame strokes are big shapes: drop tiny islands left by line boil
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] > 120
    m = keep[lab].astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 0.8) * np.clip(a_fx, 0, 1)
    return fx * (m / np.maximum(a_fx, 1e-4))[..., None] * (a_fx > 0)[..., None], cyan.astype(np.float32) * m


def drawing_at(f):
    name = SHEET[0][1]
    for ff, n in SHEET:
        if f >= ff:
            name = n
    return name


def main(out):
    ch, fl, glowm = {}, {}, {}
    ref = None
    for _, n in SHEET:
        c = C.key(C.to_canvas(C.load(f'{SRC}/{n}_char.png')))
        x = C.key(C.to_canvas(C.load(f'{SRC}/{n}_char_fx.png')))
        if ref is None:
            ref = c
        else:
            c = C.match(c, ref)
            x = C.match(x, ref)
        ch[n] = c
        fl[n], glowm[n] = flame_layer(x, c)
    eyes = {n: C.glow_mask(c) for n, c in ch.items()}
    b = C.load(f'{SRC}/B_bg.png')[..., :3]
    b = cv2.GaussianBlur(b, (0, 0), 2.0)
    bg = cv2.resize(b * np.array((0.75, 0.8, 0.95)), (C.W, C.H), interpolation=cv2.INTER_LANCZOS4)
    bg4 = np.concatenate([bg, np.ones(bg.shape[:2] + (1,), np.float32)], -1)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{C.W}x{C.H}', '-r', '24',
                          '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(F0, F1 + 1):
        n = drawing_at(f)
        u = (f - F0) / (F1 - F0)
        # camera: a small push as the fist arrives (B03), then held; a short shake on arrival
        sh = 0.0
        if 77 <= f <= 80:
            k = (80 - f) / 3
            sh = 9 * k
        cam = dict(scale=1.0 + 0.03 * min(1, max(0, (f - 75) / 3)) + 0.01 * u, tx=sh * (1 if f % 2 else -1), ty=sh * 0.6 * (1 if f % 3 else -1))
        img = C.place(bg4, scale=1.02 + 0.01 * u, tx=cam['tx'] * 0.4, ty=cam['ty'] * 0.4)[..., :3]
        # night grade on the character, then the cyan fire lights the fist and face
        c = C.place(ch[n], **cam)
        a = c[..., 3:4]
        lit = c[..., :3] * np.array((0.55, 0.6, 0.78), np.float32)
        gm = C.place(np.repeat(glowm[n][..., None], 4, -1), **cam)[..., 0]
        light = cv2.GaussianBlur(gm, (0, 0), 60)
        light = np.clip(light * 1.3, 0, 1)[..., None]
        # fire light: tints toward cyan on the lit side, never lifts skin to white
        lit = lit * (1 - 0.35 * light) + c[..., :3] * light * np.array((0.10, 0.32, 0.45), np.float32) + a * light * np.array((0.0, 0.05, 0.08), np.float32)
        img = img * (1 - a) + lit
        # the flame on top (drawn cel flame), then its light
        fx = C.place(fl[n], **cam)
        img = C.over(img, fx)
        img = img + C.glow(gm, CYAN, 0.55, radii=(4, 14, 40), weights=(0.6, 0.4, 0.25))
        if n in ('B08', 'B09', 'B10'):
            em = C.place(np.repeat(eyes[n][..., None], 4, -1), **cam)[..., 0]
            img = img + C.glow(em, CYAN, 0.6, radii=(2, 6, 16), weights=(0.8, 0.5, 0.2))
        # fade up from black over the first frames (the original opens out of black)
        if f < 75:
            img = img * ((f - 73 + 1) / 3)
        img = C.grade(img, tint=(0.97, 0.99, 1.03), desat=0.05)
        p.stdin.write(C.to8(C.tonemap(img)).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    main(sys.argv[1])
