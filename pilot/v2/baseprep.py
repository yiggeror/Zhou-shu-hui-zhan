"""Stage A: render and cache the continuous-motion base layer for every output
frame of the pilot (sub-frame interpolated). usage: baseprep.py WORKER NWORKERS"""
import sys, os
sys.path.insert(0, "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad/work")
import numpy as np, cv2
import basefrac as bf
from tsched import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base")
os.makedirs(OUT, exist_ok=True)
wk, nw = int(sys.argv[1]), int(sys.argv[2])
jobs = {}
for fi in range(NF):
    t = fi / FPS
    lab = seg_at(t)[2]
    if lab in ("whip", "jump"):               # these only need their two end frames
        a, b = seg_at(t)[3], seg_at(t)[4]
        jobs[f"tau_{a:.4f}"] = a; jobs[f"tau_{b:.4f}"] = b
    elif needs_base(t):
        jobs[f"f{fi:04d}"] = tau_at(t)
jobs["tau_0.6350"] = 0.635                    # last cyan-fist state (impact frames)
keys = sorted(jobs)[wk::nw]
for k in keys:
    fn = f"{OUT}/{k}.jpg"
    if os.path.exists(fn):
        continue
    img, C, vel = bf.render_at(jobs[k])
    cv2.imwrite(fn, (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 97])
    np.savez(f"{OUT}/{k}.npz", C=cv2.resize(C, (480, 270), interpolation=cv2.INTER_AREA).astype(np.float16),
             vel=cv2.resize(vel, (480, 270), interpolation=cv2.INTER_AREA).astype(np.float16) * np.float16(0.5))
    print(k, flush=True)
print("done", wk)
