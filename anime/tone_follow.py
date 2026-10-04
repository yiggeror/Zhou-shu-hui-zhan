"""Make a redraw's large-scale brightness follow the original frame by frame (a grade, not a redraw).

    gain_n = (LP(O_n) + eps) / (LP(O_ref) + eps)  *  (LP(R_ref) + eps) / (LP(R_n) + eps)
    R'_n   = R_n * gain_n

LP = grey level blurred with a Gaussian of sigma 18 px at 1672x941; ref = an approved redraw.  In words: the
redraw keeps the approved frame's local lift over the original, and its exposure then follows the
original's own frame-to-frame ramp.  The approved frame itself comes out unchanged (gain exactly 1).
Lines and screentone (a few px) pass through untouched; only exposure at the scale of a sleeve or a face
is corrected.  It fixes brightness pulses, not lines or hatching that change from frame to frame.

usage: python3 anime/tone_follow.py DELIVERY_DIR REF_N F0 F1 OUT_DIR"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_window import original  # noqa: E402

EPS = 4.0
SIGMA = 18


def lp(im):
    return cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), SIGMA) + EPS


def follow(r, o, r_ref, o_ref):
    gain = np.clip(lp(o) / lp(o_ref) * lp(r_ref) / lp(r), 0.4, 2.5)[..., None]
    return np.clip(r.astype(np.float32) * gain + 0.5, 0, 255).astype(np.uint8)


def main():
    src, ref, f0, f1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    os.makedirs(out, exist_ok=True)
    rd = lambda n: cv2.imread(os.path.join(src, f'R_n{n:04d}.png'))
    r_ref = rd(ref)
    h, w = r_ref.shape[:2]
    o_ref = original(ref, (w, h))
    for n in range(f0, f1):
        cv2.imwrite(os.path.join(out, f'R_n{n:04d}.png'), follow(rd(n), original(n, (w, h)), r_ref, o_ref))


if __name__ == '__main__':
    main()
