"""output time (= time in the user's music edit) -> source time tau on the 96 s timeline"""
import numpy as np
p = np.load("music/pairs.npy")                     # (user t, tau, score) at each new drawing
p = p[(p[:, 0] < 91.2) & (p[:, 0] > 0.1)]
t, d = p[:, 0], p[:, 1] - p[:, 0]
T = np.arange(0, 2852) / 30.0
ds = np.full_like(T, np.nan)
for i, x in enumerate(T):
    if x > 91.2:
        continue
    m = np.abs(t - x) < 0.5
    tt, dd = t[m], d[m]
    if len(tt) < 5:
        continue
    for _ in range(2):                              # robust: refit without outliers
        k, b = np.polyfit(tt - x, dd, 1)
        r = np.abs(dd - (k * (tt - x) + b)); keep = r < max(0.03, 2.5 * np.median(r))
        tt, dd = tt[keep], dd[keep]
    ds[i] = b
ok = ~np.isnan(ds)
# ending (white -> grey -> black) aligned on the brightness curve
endT = np.array([91.4, 92.2, 93.2]); endTau = np.array([94.06, 94.90, 95.93])
KT = np.r_[T[ok], endT]; KTau = np.r_[T[ok] + ds[ok], endTau]
o = np.argsort(KT); KT, KTau = KT[o], KTau[o]
ta = np.interp(T, KT, KTau)
ta = np.maximum.accumulate(np.clip(ta, 0, 95.984))
np.save("music/tmap30.npy", np.stack([T, ta], 1))
res = p[:, 1] - np.interp(t, T, ta)
print("residual |tau - map| ms: median %.1f  p90 %.1f  p99 %.1f" % tuple(np.percentile(np.abs(res) * 1000, [50, 90, 99])))
FPS = 60; NF = int(round(2852 / 30 * FPS))
tn = np.arange(NF) / FPS
tmap = np.interp(tn, T, ta)
np.save("full/tmap.npy", tmap)
sl = np.diff(tmap) * FPS
print("frames", NF, "speed p1 %.3f p99 %.3f min %.3f max %.3f" % (np.percentile(sl, 1), np.percentile(sl, 99), sl[tn[1:] < 93].min(), sl.max()))
bad = np.where(((sl > 1.4) | (sl < 0.65)) & (tn[1:] < 93))[0]
print("odd-speed frames:", len(bad), (bad[:20] / 60).round(2))
