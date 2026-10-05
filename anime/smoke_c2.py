"""Low-resource check of the compositing path on the real C2 drawings (not stand-ins), against the delivered C2:
  1. the original video's sha256 and frame numbering (anime/source_check.py);
  2. window [1437,1438): Q5, native 1671x941, padded by one column on the left (no resize);
  3. window [1474,1485): L9, B1, B3 shown early for the blocked B2 (hold [1476,1478)), R1, R2, R3 held [1480,1483)
     with the black wipe at 1482, black 1483, Z1 1484 - both blocked states' approximations;
  4. the native frames' pixel md5 compared with anime/expected/C2_native_pixmd5.txt.
Optional --compare also renders plan A (B1 held over 1476) and the two gap comparison sheets/clips.
Writes only into OUT_DIR, which must not exist yet.  Peak memory about 1.8 GB, a few minutes.
usage: JJK_SRC=/path/to/original.mp4 python3 anime/smoke_c2.py OUT_DIR [--compare]   (run from the repository root)"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = 'anime/sheets/batchC2_1411_1485.json'
WINDOWS = {'q5': (1437, 1438), 'gaps': (1474, 1485)}


def run(*cmd):
    print('$', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def pixmd5(d):
    out = subprocess.run([sys.executable, 'anime/pixmd5.py', d], capture_output=True, text=True, check=True, cwd=ROOT).stdout
    return dict(ln.split() for ln in out.splitlines())


def main():
    out = os.path.abspath(sys.argv[1])
    if os.path.exists(out):
        sys.exit(f'{out} exists: use a new, empty directory')
    os.makedirs(out)
    py = sys.executable
    run(py, 'anime/source_check.py')
    expect = dict(ln.split() for ln in open(os.path.join(ROOT, 'anime/expected/C2_native_pixmd5.txt')) if not ln.startswith('#'))
    bad = []
    for name, (a, b) in WINDOWS.items():
        sheet = os.path.join(out, f'sheet_{name}.json')
        run(py, 'anime/subsheet.py', SHEET, str(a), str(b), sheet)
        run(py, 'anime/measure.py', py, 'anime/action_window.py', sheet, os.path.join(out, name))
        got = pixmd5(os.path.join(out, name))
        for n in range(a, b):
            k = f'n{n}'
            ok = got.get(k) == expect[k]
            bad += [] if ok else [k]
            print(f'  {k}: {"identical to the delivered C2" if ok else "DIFFERENT from the delivered C2"}')
    if '--compare' in sys.argv:
        g = os.path.join(out, 'gaps')
        run(py, 'anime/measure.py', py, 'anime/action_window.py', 'anime/sheets/batchC2_planA_1475_1479.json',
            os.path.join(out, 'planA'))
        run(py, 'anime/gap_compare.py', os.path.join(out, 'b2_planB_used_vs_planA_n1474-1478'), '1474', '1479', '1.8',
            f'plan B, used={g}', f'plan A={os.path.join(out, "planA")};1474={g}/R_n1474.png')
        run(py, 'anime/gap_compare.py', os.path.join(out, 'r4_wipe_vs_nowipe_n1478-1484'), '1478', '1485', '1.8',
            f'used, wipe at 1482={g}', f'no wipe={g};1482={g}/R_n1481.png')
    print('RESULT: ' + ('PASS' if not bad else f'FAIL {bad}'))
    sys.exit(0 if not bad else 1)


if __name__ == '__main__':
    main()
