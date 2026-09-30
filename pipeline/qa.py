"""Per-frame agreement between the render and the reference (structure + colour),
to find the weakest frames/units for targeted fixes."""
import numpy as np, cv2, json, os, sys
S = os.environ.get("SCR", "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad")
U = np.load(S + "/work/u960.npy", mmap_mode="r")
units = json.load(open(S + "/work/units.json"))
fmap = np.load(S + "/work/fmap.npy"); uniq = np.load(S + "/work/uniq.npy")
wm = np.ones((135, 240), np.float32); wm[88:106, 55:114] = 0
def prep(im):
    s = cv2.resize(im, (240, 135), interpolation=cv2.INTER_AREA).astype(np.float32)
    return s
res = {}
for un in units:
    a = int(fmap[un["start"]]); b = int(fmap[un["end"] - 1])
    if uniq[a] < un["start"]: a += 1
    for u in range(a, b + 1):
        p = f"{S}/render/u{u:05d}.jpg"
        if not os.path.exists(p): continue
        r = prep(cv2.imread(p)); s = prep(np.ascontiguousarray(U[u]))
        gr = cv2.GaussianBlur(cv2.cvtColor(r, cv2.COLOR_BGR2GRAY), (0, 0), 1.5)
        gs = cv2.GaussianBlur(cv2.cvtColor(s, cv2.COLOR_BGR2GRAY), (0, 0), 1.5)
        x = (gr - gr[wm > 0].mean()) * wm; y = (gs - gs[wm > 0].mean()) * wm
        ncc = float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum() + 1e-6))
        col = float(np.abs(cv2.GaussianBlur(r, (0, 0), 6) - cv2.GaussianBlur(s, (0, 0), 6))[wm > 0].mean())
        res[u] = (un["id"], ncc, col)
json.dump({str(k): v for k, v in res.items()}, open(S + "/work/qa.json", "w"))
by = {}
for u, (sid, n, c) in res.items():
    by.setdefault(sid, []).append(n)
worst = sorted(by.items(), key=lambda kv: np.mean(kv[1]))
print("frames", len(res), "mean ncc", round(np.mean([v[1] for v in res.values()]), 3),
      "frac<0.6", round(np.mean([v[1] < 0.6 for v in res.values()]), 3))
for sid, v in worst[:25]:
    print(sid, len(v), round(float(np.mean(v)), 3), round(float(np.min(v)), 3))
