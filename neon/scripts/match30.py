import numpy as np, cv2
u = np.load("work/u960.npy", mmap_mode="r"); uq = np.load("work/uniq.npy"); ts = np.load("ts.npy")
def thumb(g):
    t = cv2.resize(g, (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32).ravel()
    t -= t.mean(); return t / (np.linalg.norm(t) + 1e-3)
R = np.stack([thumb(cv2.cvtColor(np.ascontiguousarray(u[i]), cv2.COLOR_BGR2GRAY)) for i in range(len(u))])
np.save("music/R.npy", R)
a = np.fromfile("music/frames30.raw", np.uint8).reshape(-1, 90, 160)
Q = np.stack([thumb(f) for f in a])
Sm = (Q @ R.T).astype(np.float32)
np.save("music/Sim30.npy", Sm)
print(Sm.shape)
