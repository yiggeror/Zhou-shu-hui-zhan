"""Version B base: every unique frame of the original at full source resolution (2134x1200 active
area) -> 1920x1080, with a light restoration: mild denoise of compression noise, line sharpening
(unsharp mask on luminance only) and a small contrast/saturation lift. The watermark is kept
(a clean removal was not possible without leaving a ghost)."""
import sys, os, subprocess
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
cv2.setNumThreads(2)
uniq = np.load(S + "/work/uniq.npy")                      # source frame index of each unique drawing
want = {int(f): u for u, f in enumerate(uniq)}
OUT = HERE + "/base"; os.makedirs(OUT, exist_ok=True)
SW, SH = 2670, 1200
cmd = ["ffmpeg", "-loglevel", "error", "-i", S + "/src/shinjuku_96s_muted_lossless_retime.mp4",
       "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=SW * SH * 3 * 2)

def enhance(img):
    crop = img[:, 268:268 + 2134]
    f = cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_AREA)
    f = cv2.bilateralFilter(f, 5, 12, 3)                                  # compression noise only
    lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0]
    blur = cv2.GaussianBlur(L, (0, 0), 1.4)
    L = L + 0.7 * (L - blur)                                               # line sharpening
    L = (L - 128) * 1.04 + 128
    lab[..., 0] = np.clip(L, 0, 255)
    lab[..., 1:] = (lab[..., 1:] - 128) * 1.08 + 128
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

i = 0; done = 0
while True:
    buf = p.stdout.read(SW * SH * 3)
    if len(buf) < SW * SH * 3:
        break
    if i in want:
        u = want[i]; fn = f"{OUT}/u{u:05d}.jpg"
        if not os.path.exists(fn):
            img = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
            cv2.imwrite(fn, enhance(img), [cv2.IMWRITE_JPEG_QUALITY, 94])
        done += 1
        if done % 200 == 0:
            print(done, flush=True)
    i += 1
p.wait()
print("done", i, "frames read,", done, "unique written")
