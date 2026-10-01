"""decide what each unique frame displays: itself, a held neighbour (same shot), or a rigid camera-only render"""
import json, glob, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
sys.path.insert(0, S + "/work")
from stage2 import unit_us, units
QG = 0.5; MAXH = 3
log = {}
for f in glob.glob(HERE + "/log_*.json"):
    log.update({int(k): v for k, v in json.load(open(f)).items()})
disp, rigid = {}, []
for ui, un in enumerate(units):
    us = [u for u in unit_us(un) if u in log]
    for j, u in enumerate(us):
        if log[u]["q"] >= QG:
            disp[u] = ["self", u]; continue
        prev = [us[k] for k in range(j - 1, max(-1, j - 1 - MAXH), -1) if log[us[k]]["q"] >= QG]
        nxt = [us[k] for k in range(j + 1, min(len(us), j + 1 + MAXH)) if log[us[k]]["q"] >= QG]
        if prev: disp[u] = ["hold", prev[0]]
        elif nxt: disp[u] = ["hold", nxt[0]]
        else: disp[u] = ["rigid", u]; rigid.append([ui, u])
json.dump(disp, open(HERE + "/display.json", "w")); json.dump(rigid, open(HERE + "/rigid_jobs.json", "w"))
from collections import Counter
print(Counter(v[0] for v in disp.values()))
