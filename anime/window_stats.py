"""Per-frame comparison of a rendered window with the original (review aid, not a pass/fail gate): mean luminance
difference (ours - original), the difference of their frame-to-frame changes, and the largest offenders.
usage: JJK_SRC=... python3 anime/window_stats.py RENDER_DIR A B"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as FR  # noqa: E402

d, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
orig = FR.frames(a, b)
dl, ch, prev = {}, [], None
for n in range(a, b):
    lo = cv2.cvtColor(cv2.resize(orig[n], (1672, 941), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(float).mean()
    lu = cv2.cvtColor(cv2.imread(os.path.join(d, f'R_n{n}.png')), cv2.COLOR_BGR2GRAY).astype(float).mean()
    dl[n] = lu - lo
    if prev:
        ch.append(abs((lu - prev[1]) - (lo - prev[0])))
    prev = (lo, lu)
v = np.abs(np.array(list(dl.values())))
print(f'[{a},{b}) mean |luminance diff| {v.mean():.2f}, max {v.max():.2f}; frame-change diff mean {np.mean(ch):.2f}, '
      f'max {np.max(ch):.2f}')
for n, x in sorted(dl.items(), key=lambda kv: -abs(kv[1]))[:10]:
    print(f'  n{n} {x:+.1f}')
