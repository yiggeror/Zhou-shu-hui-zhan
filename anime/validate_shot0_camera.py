"""Independent check of the shot-0 camera: frames 80, 84 and 88 are left out of every camera estimation step
(HOLDOUT), then distinct panel features are followed from n86 into those frames by plain template matching
(normalised correlation, not the optical flow the camera uses), and the camera's prediction is compared.

The features are Limo's nine candidate points (from_limo/018/registration_notes.md, 2560-wide coordinates),
scaled to 1672x941.  Limo flagged D (parallel fold lines) as ambiguous and E/F/G as near the flame.

usage: python3 anime/validate_shot0_camera.py [OUT.md]"""
import os
import sys

os.environ.setdefault('HOLDOUT', '80,84,88')
import cv2  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flowcam  # noqa: E402
import layered as S0  # noqa: E402

K = 1672 / 2560
# the fade frames are not left out (they are tied to n78 by their own flow similarity), but they are checked the
# same independent way; in them only the drawing seen through the bright flame (E, F, D) is clearly visible
EXTRA_EARLY = [74, 75, 76, 77]
POINTS = {'A speed line, upper': (925, 707), 'B speed line, lower': (862, 859), 'C sleeve seam cross': (723, 1218),
          'D sleeve fold (ambiguous)': (526, 995), 'E thumb nail': (1363, 1142), 'F finger corner': (1350, 1300),
          'G right white region bend': (1760, 961), 'H pale block, top': (1350, 241), 'I right vertical lines': (1710, 635)}


def track(g_ref, g_n, p, half=30, search=70):
    x, y = int(round(p[0])), int(round(p[1]))
    t = g_ref[y - half:y + half + 1, x - half:x + half + 1]
    win = g_n[y - half - search:y + half + search + 1, x - half - search:x + half + search + 1]
    if t.shape != (2 * half + 1,) * 2 or win.shape[0] < t.shape[0] + 2 or win.shape[1] < t.shape[1] + 2:
        return None, 0.0
    r = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
    _, mx, _, (bx, by) = cv2.minMaxLoc(r)
    dx = dy = 0.0
    if 0 < bx < r.shape[1] - 1 and 0 < by < r.shape[0] - 1:     # sub-pixel peak
        a, b, c = r[by, bx - 1], r[by, bx], r[by, bx + 1]
        dx = 0.5 * (a - c) / (a - 2 * b + c + 1e-9)
        a, b, c = r[by - 1, bx], r[by, bx], r[by + 1, bx]
        dy = 0.5 * (a - c) / (a - 2 * b + c + 1e-9)
    return np.array([x - search + bx + dx, y - search + by + dy]), float(mx)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    S0.configure('s0')
    O = {n: S0.orig(n) for n in range(S0.F0, S0.F1)}
    F = S0.camera_fields(O)
    G = {n: cv2.GaussianBlur(flowcam.prep(O[n]).astype(np.float32), (0, 0), 1.0) for n in O}
    lines = [f'# shot 0 camera check on left-out frames {sorted(S0.HOLDOUT)} (reference n86, 1672x941 px)', '',
             'For each feature: its position in frame n found by template matching from n86, then mapped back to n86 '
             'by the camera; the error is the distance to where the feature really is in n86.  Correlation < 0.6: '
             'the match itself is doubtful.', '',
             '| feature | ' + ' | '.join(f'n{n} error (corr)' for n in EXTRA_EARLY + sorted(S0.HOLDOUT) + [82, 90]) + ' |',
             '|---|' + '---|' * (len(EXTRA_EARLY) + len(S0.HOLDOUT) + 2)]
    for name, p in POINTS.items():
        p86 = np.array(p, float) * K
        row = []
        for n in EXTRA_EARLY + sorted(S0.HOLDOUT) + [82, 90]:
            q, c = track(G[86], G[n], p86)
            if q is None:
                row.append('-')
                continue
            back = q + F[n][int(round(q[1])), int(round(q[0]))]
            row.append(f'{np.hypot(*(back - p86)):.1f} ({c:.2f})')
        lines.append(f'| {name} | ' + ' | '.join(row) + ' |')
    text = '\n'.join(lines) + '\n'
    print(text)
    if out:
        open(out, 'w').write(text)


if __name__ == '__main__':
    main()
