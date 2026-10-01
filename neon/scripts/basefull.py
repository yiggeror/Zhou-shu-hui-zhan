"""Full film, stage A: continuous-motion base layer on the exact 96 s / 60 fps grid.

Output frame n is time n/60 of the user's music edit and shows source time
tau = tmap[n] (measured frame-by-frame against that edit), so every cut lands where the
song expects it; between source drawings the motion is interpolated (sub-frame).
usage: basefull.py WORKER NWORKERS
"""
import sys, os
sys.path.insert(0, "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad/work")
import numpy as np, cv2
import basefrac as bf
import stage2, pipe

def evict(tau):
    """keep memory bounded: only chains/assets of this shot and its neighbours stay cached"""
    ui = bf.locate(tau)[0]
    keep = set()
    for j in (ui - 1, ui, ui + 1):
        if 0 <= j < len(stage2.units):
            keep |= {k for k, _ in stage2.units[j]["anchors"]}
    for cache in (stage2._chain_cache, pipe._asset_cache):
        for k in [k for k in cache if k not in keep]:
            del cache[k]

FPS = 60
TMAP = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmap.npy"))
NF = len(TMAP)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base")
os.makedirs(OUT, exist_ok=True)
wk, nw = int(sys.argv[1]), int(sys.argv[2])
BL = 30
blocks = [list(range(b, min(b + BL, NF))) for b in range(0, NF, BL)]
for bi in range(wk, len(blocks), nw):
    for n in blocks[bi]:
        fn = f"{OUT}/n{n:04d}.jpg"
        if os.path.exists(fn) and os.path.exists(f"{OUT}/n{n:04d}.npy"):
            continue
        evict(float(TMAP[n]))
        img, C, vel = bf.render_at(float(TMAP[n]))
        np.save(f"{OUT}/n{n:04d}.npy", cv2.resize(vel, (240, 135), interpolation=cv2.INTER_AREA).astype(np.float16))
        cv2.imwrite(fn, (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print("block", bi, flush=True)
print("done", wk, flush=True)
