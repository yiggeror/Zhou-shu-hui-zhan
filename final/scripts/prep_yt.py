"""Version B base pictures from the YouTube original (2560x1440, 24 fps): every drawing the film needs,
taken from the frame of the original it was matched to (yt/align_yt.py, median correlation 0.999,
identical framing and colour), downscaled to 1920x1080 (area), a light line sharpening and the same
colour lift as before.  Flat frames that have no counterpart in the original (black start, white flash,
the closing white -> black fade) come from the recording.  The original's intro and credits are never used."""
import subprocess, numpy as np, cv2, os
S = "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad"
OUT = S + "/ytB/frames"; os.makedirs(OUT, exist_ok=True)
p = np.load(S + "/yt/u2yt.npy"); sc = np.load(S + "/yt/u2yt_score.npy")
need = [int(x) for x in open(S + "/srB2/need.txt").read().split()]
U = np.load(S + "/work/u960.npy", mmap_mode="r")
def look(f, sharpen):
    lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0]
    if sharpen:
        L = L + 0.35 * (L - cv2.GaussianBlur(L, (0, 0), 1.0))
    lab[..., 0] = np.clip((L - 128) * 1.04 + 128, 0, 255); lab[..., 1:] = (lab[..., 1:] - 128) * 1.08 + 128
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
want = {}
for u in need:
    if sc[u] >= 0.8:
        want.setdefault(int(p[u]), []).append(u)
    else:                                                  # flat frame: from the recording
        f = cv2.resize(np.asarray(U[u]), (1920, 1080), interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(f"{OUT}/u{u:05d}.jpg", look(f, False), [cv2.IMWRITE_JPEG_QUALITY, 93])
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", S + "/yt/新宿决战原版.mp4", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, bufsize=2560 * 1440 * 3 * 2)
j = 0; n = 0
while True:
    buf = dec.stdout.read(2560 * 1440 * 3)
    if len(buf) < 2560 * 1440 * 3: break
    if j in want:
        f = look(cv2.resize(np.frombuffer(buf, np.uint8).reshape(1440, 2560, 3), (1920, 1080), interpolation=cv2.INTER_AREA), True)
        for u in want[j]:
            cv2.imwrite(f"{OUT}/u{u:05d}.jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 93]); n += 1
    j += 1
dec.wait()
print("yt frames read", j, "written from original", n, "total", len(os.listdir(OUT)), "of", len(need))
