"""Assemble rendered unique frames onto an exact 60 fps / 96.000 s timeline and encode.

Frame n (t = n/60) shows whatever source frame was on screen at t in the
reference video (variable timestamps honoured), so every cut and hold lands
where the original has it.
usage: assemble.py OUT.mp4 WIDTH HEIGHT CRF [preset]
"""
import sys, subprocess, numpy as np, cv2, os
S = os.environ.get("SCR", "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad")
out, OW, OH, crf = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
preset = sys.argv[5] if len(sys.argv) > 5 else "slow"
FPS, DUR = 60, 96.0
NF = int(round(FPS * DUR))
ts = np.load(S + "/ts.npy"); fmap = np.load(S + "/work/fmap.npy")
seq = []
for n in range(NF):
    t = n / FPS
    i = max(0, int(np.searchsorted(ts, t + 1e-6, side="right")) - 1)
    seq.append(int(fmap[i]))
np.save(S + "/work/seq60.npy", np.array(seq))
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
       "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
       "-c:v", "libx264", "-preset", preset, "-crf", crf, "-tune", "animation",
       "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
       "-g", "120", "-keyint_min", "60", "-sc_threshold", "40",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
       "-movflags", "+faststart", "-t", f"{DUR:.3f}", out]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
last_u, last = None, None
for n, u in enumerate(seq):
    if u != last_u:
        im = cv2.imread(f"{S}/render/u{u:05d}.jpg")
        if (im.shape[1], im.shape[0]) != (OW, OH):
            im = cv2.resize(im, (OW, OH), interpolation=cv2.INTER_AREA)
        last, last_u = im, u
    p.stdin.write(last.tobytes())
    if n % 600 == 0:
        print(n, flush=True)
p.stdin.close(); p.wait()
print("done", out, p.returncode)
