"""Measure the camera move of a shot whose artwork is one drawing under a push / pan: match
SIFT features outside the animated energy (strongly coloured pixels) and the watermark,
fit a similarity transform per frame relative to a reference frame.
transforms(start, end, ref) -> {n: 2x3 matrix mapping ref-frame pixels -> frame-n pixels} (2560x1440)"""
import sys, os, subprocess
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from anime.frames import SRC

FW, FH = 2560, 1440


def load(start, end, scale=0.5):
    w, h = int(FW * scale), int(FH * scale)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'select=between(n\\,{start}\\,{end - 1}),scale={w}:{h}',
                          '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def static_mask(img):
    """pixels that belong to the still artwork: not strongly coloured light, not the watermark"""
    f = img.astype(np.float32) / 255
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    sat = np.max(f, -1) - np.min(f, -1)
    m = (sat < 0.28).astype(np.uint8)
    m = cv2.erode(m, np.ones((9, 9), np.uint8))
    h, w = m.shape
    m[int(h * 0.62):int(h * 0.80), int(w * 0.08):int(w * 0.40)] = 0
    return m * 255


def transforms(start, end, ref, scale=0.5):
    F = load(start, end, scale)
    sift = cv2.SIFT_create(4000)
    g = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    kr, dr = sift.detectAndCompute(g(F[ref - start]), static_mask(F[ref - start]))
    bf = cv2.BFMatcher()
    out = {}
    for i in range(len(F)):
        n = start + i
        if n == ref:
            out[n] = (np.eye(2, 3), 1.0, len(kr))
            continue
        k, d = sift.detectAndCompute(g(F[i]), static_mask(F[i]))
        if d is None or dr is None:
            out[n] = (None, 0, 0)
            continue
        ms = [a for a, b in bf.knnMatch(dr, d, k=2) if a.distance < 0.75 * b.distance]
        if len(ms) < 8:
            out[n] = (None, 0, len(ms))
            continue
        p = np.float32([kr[m.queryIdx].pt for m in ms])
        q = np.float32([k[m.trainIdx].pt for m in ms])
        M, inl = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC, ransacReprojThreshold=2.0)
        M = M.astype(np.float64)
        M[:, 2] /= scale
        out[n] = (M, float(inl.mean()) if inl is not None else 0, len(ms))
    return out


if __name__ == '__main__':
    s, e, r = map(int, sys.argv[1:4])
    for n, (M, inl, nm) in sorted(transforms(s, e, r).items()):
        if M is None:
            print(n, 'FAIL', nm)
            continue
        sc = float(np.sqrt(abs(np.linalg.det(M[:, :2]))))
        ang = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
        print(f'{n:4d} scale {sc:.4f} rot {ang:+.2f} tx {M[0, 2]:+8.1f} ty {M[1, 2]:+8.1f} inliers {inl:.2f} matches {nm}')
