"""Stand-ins for a planned window before any drawing exists: each state's source frame of the original, scaled to the
native 1672x941, written as <id>_n<source>.png, plus a manifest pointing at them, so the sheet, the holds and the edge
fill can be checked through the real compositor.  Stand-ins are never delivery input.
usage: JJK_SRC=... python3 anime/standins.py PLAN.json OUT_DIR
  PLAN.json: {"states": [{"id": "GF1", "source_n": 1485, "start": 1485, "end": 1486}, ...]}  (Limo's manifest works too)"""
import json
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as FR  # noqa: E402

plan, out = json.load(open(sys.argv[1])), os.path.abspath(sys.argv[2])
os.makedirs(out, exist_ok=True)
states = []
for st in plan['states']:
    p = os.path.join(out, f'{st["id"]}_n{st["source_n"]}.png')
    cv2.imwrite(p, cv2.resize(FR.frame(st['source_n']), (1672, 941), interpolation=cv2.INTER_AREA))
    states.append(dict(st, path=p))
json.dump({'schema': 'standin manifest (not delivery input)', 'states': states}, open(os.path.join(out, 'manifest_standin.json'), 'w'),
          indent=1, ensure_ascii=False)
print(f'{len(states)} stand-ins and manifest_standin.json in {out}')
