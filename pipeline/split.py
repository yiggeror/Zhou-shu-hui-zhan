"""Split an encoded MP4 into parts under a size cap, cutting only on IDR keyframes
with stream copy (no re-encode), then prove the parts rejoin bit-exactly.
usage: split.py FULL.mp4 OUTDIR BASENAME [cap_MB]
"""
import sys, os, subprocess, json, math, hashlib
full, outdir, base = sys.argv[1], sys.argv[2], sys.argv[3]
cap = float(sys.argv[4]) if len(sys.argv) > 4 else 90.0
os.makedirs(outdir, exist_ok=True)
size = os.path.getsize(full) / 1e6
n = max(1, math.ceil(size / cap))

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout

def md5s(args):
    out = run(["ffmpeg", "-v", "error"] + args + ["-map", "0:v", "-f", "framemd5", "-"])
    return [l.split(",")[-1].strip() for l in out.splitlines() if l and not l.startswith("#")]
# keyframe timestamps (ffmpeg only: decode keyframes, read showinfo)
import re
err = subprocess.run(["ffmpeg", "-hide_banner", "-skip_frame", "nokey", "-i", full, "-vf", "showinfo",
                      "-f", "null", "-"], capture_output=True, text=True).stderr
kf = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", err)]
def duration(path):
    return len(md5s(["-i", path])) / 60.0
if n == 1:
    print("fits in one file", round(size, 1), "MB"); sys.exit(0)
# choose keyframes closest to equal-size split points
dur = duration(full)
targets = [dur * k / n for k in range(1, n)]
cuts = [min(kf, key=lambda t: abs(t - x)) for x in targets]
seg = ",".join(f"{c:.6f}" for c in cuts)
pat = os.path.join(outdir, f"{base}_part%d.mp4")
run(["ffmpeg", "-y", "-v", "error", "-i", full, "-map", "0", "-c", "copy", "-f", "segment",
     "-segment_times", seg, "-reset_timestamps", "1", "-segment_start_number", "1",
     "-segment_format", "mp4", "-segment_format_options", "movflags=+faststart", pat])
parts = sorted((p for p in os.listdir(outdir) if p.startswith(base + "_part") and p.endswith(".mp4")),
               key=lambda s: int(s[len(base) + 5:-4]))
lst = os.path.join(outdir, f"{base}_parts.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))

a = md5s(["-i", full])
b = md5s(["-f", "concat", "-safe", "0", "-i", lst])
info = []
for p in parts:
    fp = os.path.join(outdir, p)
    nf = len(md5s(["-i", fp])); d = nf / 60.0
    info.append((p, round(os.path.getsize(fp) / 1e6, 1), round(d, 3), nf))
print(json.dumps(dict(full_MB=round(size, 1), cuts=cuts, parts=info,
                      frames_full=len(a), frames_joined=len(b), identical=(a == b))))
