"""Cut an exposure sheet down to a small window [a, b) for a low-resource check run through the same compositor
code path.  Every hold that touches the window must lie wholly inside it (a hold's grade, registration and shutter
are fitted over all of its frames, so a cut hold would not reproduce the full run).
usage: python3 anime/subsheet.py SHEET.json A B OUT.json"""
import json
import sys


def cut(sheet, a, b):
    fs = sheet['frames_sheet']
    groups = {}
    for k, e in fs.items():
        if 'hold' in e:
            groups.setdefault(e['hold'], []).append(int(k))
    for name, ns in groups.items():
        inside = [a <= n < b for n in ns]
        if any(inside) and not all(inside):
            sys.exit(f'hold {name} {min(ns)}-{max(ns)} is cut by [{a}, {b}); choose a window that holds it whole')
    out = dict(sheet)
    out['name'] = f'{sheet.get("name", "sheet")} | check window [{a}, {b})'
    out['frames'] = [a, b]
    out['frames_sheet'] = {k: e for k, e in fs.items() if a <= int(k) < b}
    missing = [n for n in range(a, b) if str(n) not in out['frames_sheet']]
    if missing:
        sys.exit(f'frames without an entry {missing}')
    return out


if __name__ == '__main__':
    src, a, b, dst = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    json.dump(cut(json.load(open(src)), a, b), open(dst, 'w'), indent=1, ensure_ascii=False)
    print(f'{dst}: [{a}, {b})')
