"""B base on the 96 s / 60 fps grid: the source frame on screen at n/60, restored (prepB.enhance)."""
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
N0 = int(os.environ.get("N0", "0"))                                   # >0: only the tail (base/B_tail.mp4)
fn = f"{HERE}/base/B.mp4" if N0 == 0 else f"{HERE}/base/B_tail.mp4"
enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1920x1080", "-r", "60",
                        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-threads", "1", "-crf", "10", "-pix_fmt", "yuv420p",
                        "-g", "60", fn + ".tmp.mp4"], stdin=subprocess.PIPE)
cur_i, cur = -1, None
for n in range(N0, 5760):
    want = max(0, int(np.searchsorted(ts, n / 60 + 1e-6, side="right")) - 1)
    while cur_i < want:
        buf = dec.stdout.read(SW * SH * 3)
        if len(buf) < SW * SH * 3: break
        cur_i += 1
        if cur_i == want:
            cur = enhance(np.frombuffer(buf, np.uint8).reshape(SH, SW, 3))
    enc.stdin.write(cur.tobytes())
    if n % 600 == 0: print(n, flush=True)
enc.stdin.close(); enc.wait(); dec.kill(); os.replace(fn + ".tmp.mp4", fn)
print("done B")
