"""onset envelope + tempo + beat grid + strongest accents of the song (time in the user's edit)"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, find_peaks
sr, x = wavfile.read("audio.wav"); x = x.astype(np.float32) / 32768
f, t, Z = stft(x, sr, nperseg=1024, noverlap=1024 - 256)
M = np.log1p(np.abs(Z) * 100)
flux = np.maximum(np.diff(M, axis=1), 0)
low = flux[f < 200].sum(0); allb = flux.sum(0)
env = allb / (allb.max() + 1e-9); envl = low / (low.max() + 1e-9)
tt = t[1:]
hop = tt[1] - tt[0]
# tempo by autocorrelation of the onset envelope (60..180 bpm)
e = env - env.mean()
ac = np.correlate(e, e, "full")[len(e) - 1:]
lags = np.arange(len(ac)) * hop
ok = (lags > 60 / 180) & (lags < 60 / 60)
L = lags[ok][np.argmax(ac[ok])]
print("tempo ~ %.1f bpm (period %.3f s)" % (60 / L, L))
# beat phase: maximise envelope sum on the grid
best = None
for ph in np.arange(0, L, hop):
    g = np.arange(ph, tt[-1], L)
    s = np.interp(g, tt, env).sum()
    if best is None or s > best[0]:
        best = (s, ph)
grid = np.arange(best[1], tt[-1], L)
# strongest accents: onset peaks well above local level (drums / hits)
loc = np.convolve(env, np.ones(int(1.5 / hop)) / int(1.5 / hop), "same")
pk, pr = find_peaks(env, height=loc * 2.2 + 0.08, distance=int(0.18 / hop))
acc = tt[pk]
print("accents:", len(acc))
print(np.round(acc[:60], 2))
np.save("env.npy", np.stack([tt, env, envl], 1))
np.save("grid.npy", grid); np.save("accents.npy", acc)
