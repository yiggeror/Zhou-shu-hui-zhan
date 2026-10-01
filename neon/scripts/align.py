import numpy as np
Sm = np.load("music/Sim30.npy"); uq = np.load("work/uniq.npy"); ts = np.load("ts.npy")
NQ, NR = Sm.shape
TU = ts[uq]                          # time of each unique drawing on the 96 s timeline
# monotone DP: unique index advances 0..5 per user frame (30 fps)
MAXS = 5
D = np.full((NQ, NR), -1e9, np.float32); B = np.zeros((NQ, NR), np.int8)
D[0] = Sm[0] - 0.002 * np.arange(NR)   # prefer starting near the beginning
for i in range(1, NQ):
    best = np.full(NR, -1e9, np.float32); arg = np.zeros(NR, np.int8)
    for s in range(MAXS + 1):
        prev = np.full(NR, -1e9, np.float32); prev[s:] = D[i - 1, :NR - s] if s else D[i - 1]
        pen = 0.0 if s in (1, 2) else (0.02 if s in (0, 3) else 0.06)
        cand = prev - pen
        m = cand > best; best[m] = cand[m]; arg[m] = s
    D[i] = best + Sm[i]; B[i] = arg
j = np.zeros(NQ, np.int64); j[-1] = int(np.argmax(D[-1]))
for i in range(NQ - 1, 0, -1):
    j[i - 1] = j[i] - B[i, j[i]]
sc = Sm[np.arange(NQ), j]
tu = np.arange(NQ) / 30.0
np.save("music/path.npy", np.stack([tu, TU[j], sc, j], 1))
# anchor pairs: user time where a NEW drawing first appears  <->  that drawing's start time
ch = np.where(np.diff(j) > 0)[0] + 1
pairs = np.stack([tu[ch], TU[j[ch]], sc[ch]], 1)
pairs = pairs[pairs[:, 2] > 0.85]
np.save("music/pairs.npy", pairs)
print("frames", NQ, "pairs", len(pairs), "low-score frames", int((sc < 0.85).sum()))
d = pairs[:, 1] - pairs[:, 0]
for k in range(0, len(pairs), max(1, len(pairs) // 40)):
    print("%6.2f -> %6.2f  (d %+.2f)" % tuple(pairs[k, :2]) + " " + "%+.2f" % d[k])
