"""glowing-eye detector: small bright blobs (DoG peaks, not lines) with a cyan or red fringe"""
import numpy as np, cv2

def eyes(img, kind, k=2):
    """img float BGR 1080p -> [(x, y, r, score)] in 1080p coordinates, best first"""
    sm = cv2.resize(np.clip(img, 0, 1), (960, 540), interpolation=cv2.INTER_AREA)
    B, G, R = sm[..., 0], sm[..., 1], sm[..., 2]
    V = sm.max(-1)
    out = []
    for s1, s2 in ((1.5, 5.0), (3.0, 9.0), (5.0, 15.0)):                       # small and close-up eyes
        g1 = cv2.GaussianBlur(V, (0, 0), s1); dog = g1 - cv2.GaussianBlur(V, (0, 0), s2)
        if kind == "c":
            tint = (np.minimum(B, G) - R) / (V + 0.05)
        else:
            tint = (R - np.maximum(G, B)) / (V + 0.05)
        kk = int(s1 * 6) | 1                                          # white-hot eyes: the tint is in the glow around
        tint = cv2.GaussianBlur(cv2.dilate(tint, np.ones((kk, kk), np.float32)), (0, 0), s1 * 1.5)
        resp = np.maximum(dog, 0) * np.clip(tint * 2.5, 0, 1) * np.clip((g1 - 0.35) / 0.3, 0, 1)
        # Hessian: blobs curve in both directions, lines in one
        gh = cv2.GaussianBlur(V, (0, 0), s1 * 2.0)                      # rounder: white-hot eyes clip flat
        gxx = cv2.Sobel(gh, cv2.CV_32F, 2, 0, ksize=5); gyy = cv2.Sobel(gh, cv2.CV_32F, 0, 2, ksize=5); gxy = cv2.Sobel(gh, cv2.CV_32F, 1, 1, ksize=5)
        tr = gxx + gyy; dt = np.sqrt(np.maximum((gxx - gyy) ** 2 + 4 * gxy ** 2, 0))
        l1, l2 = (tr - dt) / 2, (tr + dt) / 2                        # l1 most negative
        iso = np.where((l1 < 0) & (l2 < 0), l2 / (l1 - 1e-6), 0)          # l2/l1: 1 = round blob, 0 = line
        resp = resp * np.clip((iso - 0.15) / 0.35, 0, 1)
        mx = cv2.dilate(resp, np.ones((int(s2 * 2) | 1, int(s2 * 2) | 1), np.float32))
        ys, xs = np.nonzero((resp >= mx) & (resp > 0.02))
        for y, x in zip(ys, xs):
            if 0.06 * 960 < x < 0.94 * 960 and 0.07 * 540 < y < 0.93 * 540:
                out.append((float(x * 2), float(y * 2), float(s1 * 4 + 2), float(resp[y, x])))
    out.sort(key=lambda g: -g[3])
    res = []
    for g in out:                                                    # merge the two scales
        if all((g[0] - h[0]) ** 2 + (g[1] - h[1]) ** 2 > max(70.0, max(g[2], h[2]) * 4.0) ** 2 for h in res):
            res.append(g)
    if not res: return []
    best = res[0][3]
    return [g for g in res[:k] if g[3] >= 0.4 * best]
