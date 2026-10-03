"""Close-up design board: how face / eye close-ups are drawn in the stick-figure style."""
import math
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.mathx import V
from engine.rig import GOJO, SUKUNA
from engine.comp import composite
from engine.camera import Cam
from engine.anim import Ch
from engine import fx
from films.closeup_board import Head

FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'


def panel(h, t=0.5, extra=None):
    fr = h.frame(t)
    if extra:
        extra(h, fr)
    return composite(fr)


def main(out):
    tiles = []
    # 1 Gojo: eyes glow inside the solid head, thin bright lids, tight rim light
    tiles.append((panel(Head(GOJO, open_=1.0, fire=0.0, glow=1.2)), '五条：黑色实心头，两只蓝眼本身发亮，外圈贴边微光'))
    # 2 Sukuna: four eyes (two main, two small below), contained embers at tense moments
    tiles.append((panel(Head(SUKUNA, open_=1.0, fire=0.8, glow=1.3)), '宿傩：四只红眼（两主两小），紧张时眼里有收着的火星'))
    # 3 eye opening: the light comes up with the lids (three stages side by side)
    stages = []
    for op in (0.12, 0.5, 1.0):
        im = panel(Head(GOJO, open_=op, glow=0.4 + 0.8 * op, dist=0.95))
        stages.append(im[:, 480:1440])
    st = np.hstack(stages)
    st = cv2.resize(st, (1920, 1080 * 1920 // st.shape[1]))
    pad = np.zeros((1080, 1920, 3), np.uint8)
    pad[:] = st[0, 0]
    y0 = (1080 - st.shape[0]) // 2
    pad[y0:y0 + st.shape[0]] = st
    tiles.append((pad, '睁眼：光随眼睑张开慢慢变亮，不会突然冒出来'))
    # 4 backlit silhouette (as in shot 123): one eye open, purple light swelling behind
    def back(h, fr):
        pass
    hb = Head(GOJO, open_=1.0, fire=0.4, glow=1.5, dist=0.9)
    hb.a.fig.set(eye_r=0.08)
    fr = hb.frame(0.5)
    fr.b.clear(fr.b.getSurface() and __import__('skia').Color4f(0.925, 0.9, 0.845, 1))
    fx.light_wash(fr, 960, 560, 1100, (0.50, 0.15, 0.95), 0.75)
    fx.light_wash(fr, 960, 560, 700, (0.85, 0.65, 1.0), 0.55)
    from engine.shot import draw_actors
    draw_actors(fr, hb.cam, 0.5, 0.5, [hb.a])
    tiles.append((composite(fr), '逆光剪影：受伤只亮一只眼，紫光在身后变强，人物保持黑色剪影'))
    # assemble 2x2 with captions
    W2, H2 = 960, 540
    board = Image.new('RGB', (W2 * 2, (H2 + 64) * 2), (236, 230, 216))
    dr = ImageDraw.Draw(board)
    font = ImageFont.truetype(FONT, 26)
    for i, (im, cap) in enumerate(tiles):
        x, y = (i % 2) * W2, (i // 2) * (H2 + 64)
        tile = Image.fromarray(cv2.resize(im, (W2, H2), interpolation=cv2.INTER_AREA))
        board.paste(tile, (x, y))
        dr.text((x + 18, y + H2 + 16), cap, fill=(30, 30, 34), font=font)
    board.save(out)


if __name__ == '__main__':
    main(sys.argv[1])
