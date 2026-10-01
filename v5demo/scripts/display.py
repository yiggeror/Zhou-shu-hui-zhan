"""decide what each unique frame displays.
  self   : itself (crisp drawing moved by the measured motion)
  hold   : nearest clear drawing of the same shot (pose not covered by any drawing, original sharp)
  rigid  : camera-only move of the best drawing (no clear neighbour to hold)
  whip   : the original whips into / out of the shot here (blurred, content not matching any
           drawing): the shot's first/last clear frame with a designed directional whip whose
           strength fades toward the clear frame"""
import json, glob, os, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
sys.path.insert(0, S + "/work")
from stage2 import unit_us, units
from pipe import frame
SHARP = np.load(S + "/v3/coverage.npy")[:, 2]
QG = 0.5; MAXH = 3
log = {}
for f in glob.glob(HERE + "/log_*.json"):
    log.update({int(k): v for k, v in json.load(open(f)).items()})
def bad(u): return log[u]["q"] < QG
def blurry(u): return SHARP[u] < 10
def gshift(a, b):
    ga = cv2.resize(cv2.cvtColor(frame(a), cv2.COLOR_BGR2GRAY), (240, 135)).astype(np.float32)
    gb = cv2.resize(cv2.cvtColor(frame(b), cv2.COLOR_BGR2GRAY), (240, 135)).astype(np.float32)
    (dx, dy), r = cv2.phaseCorrelate(ga, gb)
    return dx * 8, dy * 8, r
disp, rigid = {}, []
for ui, un in enumerate(units):
    us = [u for u in unit_us(un) if u in log]
    if not us:
        continue
    lead = 0
    while lead < len(us) and lead < 5 and bad(us[lead]) and blurry(us[lead]): lead += 1
    trail = 0
    while trail < len(us) - lead and trail < 5 and bad(us[-1 - trail]) and blurry(us[-1 - trail]): trail += 1
    for j, u in enumerate(us):
        if j < lead or j >= len(us) - trail:
            into = j < lead
            ref = us[lead] if into else us[len(us) - trail - 1]
            run = us[:lead + 1] if into else us[len(us) - trail - 1:]
            dx, dy, _ = gshift(run[0], run[-1]) if len(run) > 1 else (0.0, 0.0, 0)
            k = (lead - j) / lead if into else (j - (len(us) - trail) + 1) / trail
            disp[u] = ["whip", ref, round(float(k), 3), round(float(dx), 1), round(float(dy), 1)]
            continue
        if not bad(u) or blurry(u):                 # blurred flight frames keep moving (no hold)
            disp[u] = ["self", u]; continue
        prev = [us[k] for k in range(j - 1, max(-1, j - 1 - MAXH), -1) if not bad(us[k])]
        nxt = [us[k] for k in range(j + 1, min(len(us), j + 1 + MAXH)) if not bad(us[k])]
        if prev: disp[u] = ["hold", prev[0]]
        elif nxt: disp[u] = ["hold", nxt[0]]
        else: disp[u] = ["rigid", u]; rigid.append([ui, u])
json.dump(disp, open(HERE + "/display.json", "w")); json.dump(rigid, open(HERE + "/rigid_jobs.json", "w"))
from collections import Counter
print(Counter(v[0] for v in disp.values()))
