"""which new keys would cover the poorly-covered drawings: direct flow warp test, greedy set cover"""
import numpy as np, cv2, json, sys
u960 = np.load("work/u960.npy", mmap_mode="r")
A = np.load("v3/coverage.npy"); q, C, sharp, mot, uo, t96, fr = A.T
uo = uo.astype(int)
units = json.load(open("work/units.json"))
QT = float(sys.argv[1]) if len(sys.argv) > 1 else 0.75
need = (q < QT) & (sharp >= 8)
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
cache = {}
def gray(u):
    if u not in cache:
        g = cv2.cvtColor(np.ascontiguousarray(u960[u]), cv2.COLOR_BGR2GRAY)
        cache[u] = cv2.resize(g, (480, 270), interpolation=cv2.INTER_AREA)
    return cache[u]
YY, XX = np.mgrid[0:270, 0:480].astype(np.float32)
def qual(f, g):
    a, b = gray(f), gray(g)
    fl = dis.calc(b, a, None)                       # for each pixel of g: where it is in f
    w = cv2.remap(a, XX + fl[..., 0], YY + fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    bg = b.astype(np.float32)
    err = cv2.blur(np.abs(bg - w), (5, 5))
    conf = np.exp(-err / 25.0)
    sw = cv2.GaussianBlur(np.abs(cv2.Sobel(bg, cv2.CV_32F, 1, 0)) + np.abs(cv2.Sobel(bg, cv2.CV_32F, 0, 1)), (0, 0), 3) + 1e-3
    return float((conf * sw).sum() / sw.sum())
R = 8
keys = []; covmap = {}
for ui in range(len(units)):
    idx = np.where(uo == ui)[0]
    todo = [int(u) for u in idx if need[u]]
    if not todo:
        continue
    cand = [int(u) for u in idx if sharp[u] >= 8]
    cov = {}
    for f in cand:
        s = {f} if need[f] else set()
        for g in todo:
            if g != f and abs(g - f) <= R and qual(f, g) >= QT:
                s.add(g)
        cov[f] = s
    left = set(todo)
    while left:
        f = max(cov, key=lambda c: (len(cov[c] & left), sharp[c]))
        gain = cov[f] & left
        if not gain:
            for g in sorted(left):                  # nothing helps: the frame needs its own key
                keys.append(g); covmap[g] = [g]
            break
        keys.append(f); covmap[f] = sorted(gain); left -= gain
    cache.clear()
keys = sorted(keys)
json.dump({"QT": QT, "keys": keys, "cov": {str(k): v for k, v in covmap.items()}}, open(f"v3/keys_{QT}.json", "w"))
print("need", int(need.sum()), "keys", len(keys))
