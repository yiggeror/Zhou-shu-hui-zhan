"""Check the original video before any run: sha256, stream parameters, frame count, and that the zero-based frame
numbers match the reference PNGs exported earlier (collab/to_limo/*_ref/n<n>.png), so no source frame is off by one.
usage: JJK_SRC=/path/to/original.mp4 python3 anime/source_check.py [N ...]   (default: a spread of reference frames)"""
import glob
import hashlib
import os
import re
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as FR  # noqa: E402

EXPECT_SHA = '9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    h = hashlib.sha256()
    with open(FR.SRC, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    sha = h.hexdigest()
    print(f'source {FR.SRC}\n  sha256 {sha} ' + ('OK' if sha == EXPECT_SHA else f'MISMATCH (expected {EXPECT_SHA})'))
    info = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                           'stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_packets', '-of', 'compact=p=0',
                           FR.SRC], capture_output=True, text=True, check=True).stdout.strip()
    want = {'codec_name': 'av1', 'width': '2560', 'height': '1440', 'pix_fmt': 'yuv420p', 'r_frame_rate': '24/1',
            'nb_read_packets': '3499'}
    got = dict(kv.split('=', 1) for kv in info.split('|'))
    stream_ok = all(got.get(k) == v for k, v in want.items())
    print(f'  {info}  ' + ('OK' if stream_ok else f'MISMATCH (expected {want})'))
    refs = {int(re.findall(r'n(\d+)\.png', p)[0]): p for p in glob.glob(os.path.join(REPO, 'collab/to_limo/*_ref/n*.png'))}
    ns = [int(x) for x in sys.argv[1:]] or sorted(refs)[::40]
    bad = 0
    for n in ns:
        a = FR.frame(n)
        b = cv2.imread(refs[n])
        d = int(np.abs(a.astype(int) - b).max())
        near = {k: float(np.abs(FR.frame(k).astype(int) - b).mean()) for k in (n - 1, n + 1) if k >= 0} if d else {}
        bad += d > 0
        print(f'  n{n}: decoded vs {os.path.relpath(refs[n], REPO)}: max diff {d}' + (f'  neighbours {near}' if d else ''))
    ok = sha == EXPECT_SHA and stream_ok and not bad
    print('RESULT: ' + ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
