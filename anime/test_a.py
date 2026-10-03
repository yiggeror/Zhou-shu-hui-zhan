"""Test A preview: shot 5 (Gojo close-up, eyes lift and light up), frames 219-268 at 24 fps,
from Limo's cels in collab/from_limo/002/test_A/.  Usage: python3 anime/test_a.py OUT.mp4"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
import numpy as np
from anime import comp as C

SRC = 'collab/from_limo/002/test_A'
F0, F1 = 219, 269
# exposure sheet: (first frame, drawing).  A02 / A03 / A05 / A06 not drawn yet -> held neighbours
SHEET = [(219, 'A01'), (240, 'A04'), (256, 'A07')]
EYE = (0.25, 0.85, 1.0)


def temp_background():
    """placeholder until Limo paints A_bg: overcast sky high above the city, a dark block
    out of focus on the left, the city soft at the bottom"""
    yy, xx = np.mgrid[0:C.H, 0:C.W].astype(np.float32)
    sky = np.zeros((C.H, C.W, 3), np.float32)
    t = yy / C.H
    sky[:] = (0.80, 0.83, 0.86)
    sky = sky * (1 - 0.35 * t[..., None]) + np.array((0.05, 0.06, 0.08)) * 0.0
    cloud = cv2.GaussianBlur(np.random.default_rng(5).random((C.H // 16, C.W // 16)).astype(np.float32), (0, 0), 3)
    cloud = cv2.resize(cloud, (C.W, C.H), interpolation=cv2.INTER_CUBIC)
    sky *= (0.9 + 0.15 * cloud)[..., None]
    img = sky
    blk = np.zeros((C.H, C.W), np.float32)
    cv2.fillPoly(blk, [np.array([[0, 1080], [60, 110], [250, 60], [330, 1080]], np.int32)], 1.0)
    for x, h in ((380, 820), (520, 900), (700, 860), (900, 930), (1100, 880)):
        cv2.rectangle(blk, (x, h), (x + 140, 1080), 0.8, -1)
    blk = cv2.GaussianBlur(blk, (0, 0), 14)
    img = img * (1 - 0.85 * blk[..., None]) + np.array((0.10, 0.11, 0.14)) * 0.85 * blk[..., None]
    return img


def drawing_at(f):
    name = SHEET[0][1]
    for ff, n in SHEET:
        if f >= ff:
            name = n
    return name


def main(out):
    cels = {}
    for _, n in SHEET:
        cels[n] = C.key(C.load(f'{SRC}/{n}_char.png'))
    ref = cels['A01']
    for n in cels:
        if n != 'A01':
            cels[n] = C.match(cels[n], ref)
    masks = {n: C.glow_mask(c) for n, c in cels.items()}
    bg = temp_background()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{C.W}x{C.H}', '-r', '24',
                          '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(F0, F1):
        u = (f - F0) / (F1 - F0)
        n = drawing_at(f)
        # camera: very slow push-in with a slight drift (the drawing itself is untouched)
        cam = dict(scale=1.0 + 0.045 * u, tx=-14 * u, ty=6 * u, rot=-0.3 * u)
        cel = C.place(cels[n], **cam)
        bgc = C.place(np.concatenate([bg, np.ones(bg.shape[:2] + (1,), np.float32)], -1), scale=1.0 + 0.02 * u, tx=-6 * u)[..., :3]
        img = C.over(bgc, cel)
        # eye light: grows from the moment the eyes open
        k = float(np.interp(f, [239, 240, 252, 262, 268], [0.0, 0.35, 0.6, 0.9, 1.0]))
        if k > 0:
            m = C.place(np.repeat(masks[n][..., None], 4, -1), **cam)[..., 0]
            img = img + C.glow(m, EYE, k * 0.55, radii=(3, 10, 30), weights=(0.8, 0.45, 0.2))
        p.stdin.write(C.to8(C.tonemap(img)).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    main(sys.argv[1])
