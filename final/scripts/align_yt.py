"""match every drawing of the recording (work/u960.npy) to a frame of the YouTube original:
normalised correlation of 160x90 thumbnails, then a monotonic path (drawings are in time order)."""
import numpy as np
S = "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad"
Y = np.load(S + "/yt/thumbs_yt.npy").astype(np.float32); U = np.load(S + "/yt/thumbs_u.npy").astype(np.float32)
def norm(X):
    X = X.reshape(len(X), -1); X = X - X.mean(1, keepdims=True)
    n = np.linalg.norm(X, axis=1, keepdims=True); flat = n[:, 0] < 1e-3
    X = X / np.maximum(n, 1e-3); return X, flat
Yn, yflat = norm(Y); Un, uflat = norm(U)
C = Un @ Yn.T                                              # (drawings, yt frames) correlation
# flat frames (all black / all white): compare mean brightness instead
ym = Y.reshape(len(Y), -1).mean(1); um = U.reshape(len(U), -1).mean(1)
for i in np.where(uflat)[0]:
    C[i] = np.where(yflat, 1 - np.abs(ym - um[i]) / 255, 0.0)
# monotonic path: j(u) non-decreasing, small penalty for jumping far ahead
nu, ny = C.shape
best = np.full((nu, ny), -1e9, np.float32); back = np.zeros((nu, ny), np.int32)
best[0] = C[0]
for i in range(1, nu):
    cm = np.maximum.accumulate(best[i - 1]); am = np.zeros(ny, np.int32)
    run = 0
    for j in range(ny):
        if best[i - 1, j] >= best[i - 1, run]: run = j
        am[j] = run
    best[i] = cm + C[i]; back[i] = am
path = np.zeros(nu, np.int32); path[-1] = int(np.argmax(best[-1]))
for i in range(nu - 1, 0, -1):
    path[i - 1] = back[i, path[i]]
sc = C[np.arange(nu), path]
np.save(S + "/yt/u2yt.npy", path); np.save(S + "/yt/u2yt_score.npy", sc)
print("matched drawing 0 ->", path[0], "(", round(path[0] / 24, 2), "s ), last ->", path[-1], "(", round(path[-1] / 24, 2), "s )")
print("score: median %.3f  p5 %.3f  p1 %.3f  min %.3f" % (np.median(sc), np.percentile(sc, 5), np.percentile(sc, 1), sc.min()))
print("drawings with score < 0.8:", int((sc < 0.8).sum()), " < 0.6:", int((sc < 0.6).sum()))
# is it the best match overall too (not forced by the path)?
print("path pick == global best for", float((path == C.argmax(1)).mean()).__round__(3), "of drawings")
