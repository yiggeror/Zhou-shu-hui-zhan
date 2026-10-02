"""A base on the 96 s / 60 fps grid (crisp60.render_n for every n), stored as near-lossless video
segments so the effects pass can be re-run cheaply. usage: baseA60.py WORKER NWORKERS"""
import sys, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
sys.path.insert(0, S + "/v5")
import crisp60, stage2, pipe
from crisp60 import bf
NF = 5760; wk, nw = int(sys.argv[1]), int(sys.argv[2])
step = (NF + nw - 1) // nw; n0, n1 = wk * step, min(NF, (wk + 1) * step)
fn = f"{HERE}/base/A_{wk}.mp4"
enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1920x1080", "-r", "60",
                        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-threads", "1", "-crf", "10", "-pix_fmt", "yuv420p",
                        "-g", "60", fn + ".tmp.mp4"], stdin=subprocess.PIPE)
for n in range(n0, n1):
    ui = bf.locate(n / 60)[0]; _, u0, u1, _ = bf.locate(n / 60)
    keep = {k for uu in (u0, u1) if uu is not None for k, _ in bf.cands_for(ui, uu)}
    for cache in (stage2._chain_cache, pipe._asset_cache):
        for k in [k for k in cache if k not in keep]:
            del cache[k]
    img, _ = crisp60.render_n(n)
    enc.stdin.write(img.tobytes())
    if n % 120 == 0: print(n, flush=True)
enc.stdin.close(); enc.wait(); os.replace(fn + ".tmp.mp4", fn)
print("done", wk, n0, n1)
