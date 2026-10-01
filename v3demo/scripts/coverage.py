"""per unique drawing: best existing-key warp quality (v4 logs), source sharpness, motion"""
import numpy as np, cv2, json, glob, os
u960 = np.load("work/u960.npy", mmap_mode="r"); uq = np.load("work/uniq.npy"); ts = np.load("ts.npy")
units = json.load(open("work/units.json"))
wm = np.load("wm_glyph.npy") if os.path.exists("wm_glyph.npy") else None
q = np.full(len(uq), np.nan); C = np.full(len(uq), np.nan)
for f in glob.glob("render_v4/log_*.json"):
    for k, v in json.load(open(f)).items():
        u = int(k); q[u] = max(v["q"]) if v["q"] else 0; C[u] = v["C"]
sharp = np.zeros(len(uq)); mot = np.zeros(len(uq))
prev = None
for u in range(len(uq)):
    g = cv2.cvtColor(np.ascontiguousarray(u960[u]), cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap = cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 1.0), cv2.CV_32F)
    if wm is not None:
        m = cv2.resize(wm.astype(np.uint8), (960, 540)) == 0
        sharp[u] = float(lap[m].var())
    else:
        sharp[u] = float(lap.var())
    s = cv2.resize(g, (240, 135), interpolation=cv2.INTER_AREA)
    mot[u] = 0 if prev is None else float(np.abs(s - prev).mean())
    prev = s
unit_of = np.zeros(len(uq), int)
for i, x in enumerate(units):
    unit_of[(uq >= x["start"]) & (uq < x["end"])] = i
np.save("v3/coverage.npy", np.stack([q, C, sharp, mot, unit_of, ts[uq], uq], 1))
print("frames", len(uq), "q<0.6", int((q < 0.6).sum()), "q<0.75", int((q < 0.75).sum()))
print("sharp pct", np.percentile(sharp, [10, 25, 50, 75, 90]).round(1))
