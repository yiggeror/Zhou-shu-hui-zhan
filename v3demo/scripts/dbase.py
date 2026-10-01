"""cache crisp base frames for the demo. usage: dbase.py W NW"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from dsched import *
from crisp import render_crisp2
import stage2, pipe, basefrac as bf
OUT = os.path.dirname(os.path.abspath(__file__)) + "/dbase"; os.makedirs(OUT, exist_ok=True)
wk, nw = int(sys.argv[1]), int(sys.argv[2])
jobs = {}
for fi in range(NF):
    i, x = seg_at(fi / FPS); d, k, a, b = SEG[i]
    if k == "act":
        jobs[f"f{fi:04d}"] = tau_at(fi / FPS)
for i, (d, k, a, b) in enumerate(SEG):          # transition endpoints: last/first crisp frame of the neighbours
    if k != "act":
        jobs[f"e{i:02d}a"] = SEG[i - 1][3] - 1e-4 if i > 0 else a
        jobs[f"e{i:02d}b"] = SEG[i + 1][2] + 1e-4 if i + 1 < len(SEG) else b
for key in sorted(jobs)[wk::nw]:
    fn = f"{OUT}/{key}.png"
    if os.path.exists(fn):
        continue
    tau = jobs[key]
    ui = bf.locate(tau)[0]
    keep = set()
    for j in (ui - 1, ui, ui + 1):
        if 0 <= j < len(stage2.units):
            keep |= {kk for kk, _ in stage2.units[j]["anchors"]}
    for cache in (stage2._chain_cache, pipe._asset_cache):
        for kk in [kk for kk in cache if kk not in keep]:
            del cache[kk]
    img, k, q, fld = render_crisp2(tau, 14, "auto")
    cv2.imwrite(fn, (img * 255 + 0.5).astype(np.uint8))
    np.save(f"{OUT}/{key}_fld.npy", cv2.resize(fld, (240, 135), interpolation=cv2.INTER_AREA).astype(np.float16) * np.float16(0.25))
    print(key, k, round(q, 2), flush=True)
print("done", wk)
