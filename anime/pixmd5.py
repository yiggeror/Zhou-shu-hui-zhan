"""md5 of the decoded pixels (BGR uint8 array) of every R_n<n>.png in a render directory, independent of how the PNG
was compressed.  usage: python3 anime/pixmd5.py DIR [A B]  ->  lines 'n<n> <md5>'"""
import glob
import hashlib
import os
import re
import sys

import cv2

d = sys.argv[1]
a, b = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (None, None)
for p in sorted(glob.glob(os.path.join(d, 'R_n*.png')), key=lambda p: int(re.findall(r'R_n(\d+)', p)[0])):
    n = int(re.findall(r'R_n(\d+)', p)[0])
    if a is None or a <= n < b:
        print(f'n{n} {hashlib.md5(cv2.imread(p).tobytes()).hexdigest()}')
