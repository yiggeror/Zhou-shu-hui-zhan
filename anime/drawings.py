"""Find which frames of a shot are new drawings and which are the same drawing under a camera
move: align each frame to the previous one with a similarity transform (ECC on a blurred,
downscaled grey image, watermark area masked) and look at what is left over.
Usage: python3 anime/drawings.py START END   (half-open interval of original frame numbers n)"""
import sys, os, subprocess
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from anime.frames import SRC

W, H = 640, 360


def load(start, end):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'select=between(n\\,{start}\\,{end - 1}),scale={W}:{H}',
                          '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32) / 255.0


def analyse(start, end):
    F = load(start, end)
    mask = np.ones((H, W), np.uint8)
    mask[int(H * 0.30):int(H * 0.45), int(W * 0.10):int(W * 0.40)] = 0      # the watermark
    out = []
    for i in range(1, len(F)):
        a = cv2.GaussianBlur(F[i - 1], (0, 0), 1.2)
        b = cv2.GaussianBlur(F[i], (0, 0), 1.2)
        warp = np.eye(2, 3, dtype=np.float32)
        try:
            _, warp = cv2.findTransformECC(a, b, warp, cv2.MOTION_AFFINE,
                                           (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5), mask, 3)
        except cv2.error:
            pass
        al = cv2.warpAffine(a, warp, (W, H), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        raw_d = float(np.abs(a - b)[mask > 0].mean())
        res = float(np.abs(al - b)[mask > 0].mean())
        sc = float(np.sqrt(abs(np.linalg.det(warp[:, :2]))))
        out.append((start + i, raw_d, res, sc, float(warp[0, 2]), float(warp[1, 2])))
    return out


if __name__ == '__main__':
    s, e = int(sys.argv[1]), int(sys.argv[2])
    print(' n   raw   resid  scale   dx    dy')
    for n, raw_d, res, sc, dx, dy in analyse(s, e):
        tag = 'NEW' if res > 0.012 else ''
        print(f'{n:4d} {raw_d:.4f} {res:.4f} {sc:.4f} {dx:+6.2f} {dy:+6.2f} {tag}')
