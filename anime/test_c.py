"""Test C: shot 1 (Sukuna's burning red fist at the lens, his grin revealed), frames 91-108 at
24 fps, from Limo's paired drawings in collab/from_limo/002/test_C/.
Usage: python3 anime/test_c.py OUT.mp4"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
import numpy as np
from anime import comp as C
from anime.test_b import flame_layer

SRC = 'collab/from_limo/002/test_C'
F0, F1 = 91, 108
SHEET = [(91 + 2 * i, f'C{i + 1:02d}') for i in range(9)]
FX = {'C01': 'C01_char_fx_v2', 'C09': 'C09_char_fx_v2'}
RED = (1.0, 0.16, 0.22)


def red_flame_layer(fx, ch):
    """like flame_layer, but the fire is red: strongly red pixels count as flame"""
    a_fx, a_ch = fx[..., 3], ch[..., 3]
    d = np.abs(fx[..., :3] - ch[..., :3]).max(-1)
    changed = (d > 0.16).astype(np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    c = fx[..., :3] / np.maximum(a_fx[..., None], 1e-4)
    red = ((c[..., 0] - np.maximum(c[..., 1], c[..., 2]) > 0.35) & (a_fx > 0.5)).astype(np.uint8)
    m = cv2.morphologyEx(changed | red, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] > 120
    m = keep[lab].astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 0.8) * np.clip(a_fx, 0, 1)
    # fire that crosses in front of the fist / body is drawn a little see-through
    m = m * (1 - 0.15 * (a_ch > 0.9))
    lay = fx * (m / np.maximum(a_fx, 1e-4))[..., None] * (a_fx > 0)[..., None]
    return lay, red.astype(np.float32) * m


def eye_mask(ch):
    """Sukuna's red irises on the clean drawing (upper right of the frame, where his face is)"""
    a = ch[..., 3]
    c = ch[..., :3] / np.maximum(a[..., None], 1e-4)
    m = np.clip((c[..., 0] - np.maximum(c[..., 1], c[..., 2]) - 0.35) / 0.2, 0, 1) * a
    h, w = m.shape
    roi = np.zeros_like(m)
    roi[: int(h * 0.42), int(w * 0.55):] = 1
    return (m * roi).astype(np.float32)


def drawing_at(f):
    name = SHEET[0][1]
    for ff, n in SHEET:
        if f >= ff:
            name = n
    return name


def main(out):
    ch, fl, glowm, eyes = {}, {}, {}, {}
    ref = None
    for _, n in SHEET:
        c = C.key(C.to_canvas(C.load(f'{SRC}/{n}_char.png')))
        x = C.key(C.to_canvas(C.load(f'{SRC}/{FX.get(n, n + "_char_fx")}.png')))
        if ref is None:
            ref = c
        else:
            c = C.match(c, ref)
            x = C.match(x, ref)
        ch[n] = c
        fl[n], glowm[n] = red_flame_layer(x, c)
        eyes[n] = eye_mask(c)
    b = C.load(f'{SRC}/C_bg.png')[..., :3]
    b = cv2.GaussianBlur(b, (0, 0), 2.0)
    bg = cv2.resize(b * np.array((0.75, 0.8, 0.95)), (C.W, C.H), interpolation=cv2.INTER_LANCZOS4)
    bg4 = np.concatenate([bg, np.ones(bg.shape[:2] + (1,), np.float32)], -1)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{C.W}x{C.H}', '-r', '24',
                          '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(F0, F1 + 1):
        n = drawing_at(f)
        u = (f - F0) / (F1 - F0)
        # slow push in, held hand-held drift; a short shake as the shot cuts in (the punch lands)
        sh = 8 * max(0, (94 - f) / 3)
        cam = dict(scale=1.02 + 0.025 * u, tx=sh * (1 if f % 2 else -1) - 6 * u, ty=sh * 0.5 * (1 if f % 3 else -1))
        img = C.place(bg4, scale=1.03 + 0.01 * u, tx=cam['tx'] * 0.4, ty=cam['ty'] * 0.4)[..., :3]
        c = C.place(ch[n], **cam)
        a = c[..., 3:4]
        gm = C.place(np.repeat(glowm[n][..., None], 4, -1), **cam)[..., 0]
        light = np.clip(cv2.GaussianBlur(gm, (0, 0), 60) * 0.9, 0, 1)[..., None]
        lit = c[..., :3] * np.array((0.6, 0.58, 0.72), np.float32)
        lit = lit * (1 - 0.35 * light) + c[..., :3] * light * np.array((0.45, 0.14, 0.12), np.float32) + a * light * np.array((0.08, 0.0, 0.0), np.float32)
        img = img * (1 - a) + lit
        img = C.over(img, C.place(fl[n], **cam))
        img = img + C.glow(gm, RED, 0.2, radii=(6, 24, 60), weights=(0.35, 0.3, 0.2))
        k_eye = float(np.interp(f, [91, 99, 105, 108], [0.25, 0.45, 0.8, 0.9]))
        em = C.place(np.repeat(eyes[n][..., None], 4, -1), **cam)[..., 0]
        img = img + C.glow(em, RED, 0.6 * k_eye, radii=(2, 6, 16), weights=(0.8, 0.5, 0.2))
        img = C.grade(img, tint=(1.0, 0.98, 1.02), desat=0.05)
        p.stdin.write(C.to8(C.tonemap(img)).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    main(sys.argv[1])
