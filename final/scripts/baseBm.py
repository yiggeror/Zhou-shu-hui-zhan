"""B base on the music edit's timing: output frame k (60 fps) shows the restored source frame on screen at
tau = tmap[k] (96 s timeline, measured from the user's music edit)."""
import sys, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
import numpy as np, cv2
cv2.setNumThreads(2)
ts = np.load(S + "/ts.npy")
SW, SH = 2670, 1200
def enhance(img):
    crop = img[:, 268:268 + 2134]
    f = cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_AREA)
    f = cv2.bilateralFilter(f, 5, 12, 3)
    lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0]; blur = cv2.GaussianBlur(L, (0, 0), 1.4)
    L = L + 0.7 * (L - blur); L = (L - 128) * 1.04 + 128
    lab[..., 0] = np.clip(L, 0, 255); lab[..., 1:] = (lab[..., 1:] - 128) * 1.08 + 128
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", S + "/src/shinjuku_96s_muted_lossless_retime.mp4", "-vsync", "0",
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, bufsize=SW * SH * 3 * 2)
TMAP = np.load(HERE + "/tmap.npy")
fn = f"{HERE}/base/Bm.mp4"
enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1920x1080", "-r", "60",
                        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-threads", "1", "-crf", "10", "-pix_fmt", "yuv420p",
                        "-g", "60", fn + ".tmp.mp4"], stdin=subprocess.PIPE)
cur_i, cur = -1, None
for n in range(len(TMAP)):
    want = max(0, int(np.searchsorted(ts, TMAP[n] + 1e-6, side="right")) - 1)
    while cur_i < want:
        buf = dec.stdout.read(SW * SH * 3)
        if len(buf) < SW * SH * 3: break
        cur_i += 1
        if cur_i == want:
            cur = enhance(np.frombuffer(buf, np.uint8).reshape(SH, SW, 3))
    enc.stdin.write(cur.tobytes())
    if n % 600 == 0: print(n, flush=True)
enc.stdin.close(); enc.wait(); dec.kill(); os.replace(fn + ".tmp.mp4", fn)
print("done Bm", len(TMAP))
