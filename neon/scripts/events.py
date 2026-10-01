"""effect events on the source timeline (tau). 'auto' bursts snap to the biggest brightness jump."""
import numpy as np, json
LC = np.load("lumcurve.npy"); T, L, E = LC[:, 0], LC[:, 1], LC[:, 2]
def jump(a, b):
    m = np.where((T >= a) & (T <= b))[0]
    if len(m) < 2:
        return (a + b) / 2
    d = np.diff(L[m[0] - 1:m[-1] + 1]) if m[0] > 0 else np.diff(L[m])
    k = int(np.argmax(d[-len(m):]))
    return float(T[m[k]])
PUR = [1.0, 0.45, 0.95]; RED = [0.25, 0.25, 1.0]; BLUE = [1.0, 0.6, 0.25]; CYAN = [1.0, 0.92, 0.35]
ORANGE = [0.35, 0.65, 1.0]; WHITE = [1.0, 0.92, 1.0]
ev = []
def add(kind, t0, t1, **kw):
    ev.append(dict(kind=kind, t0=round(float(t0), 4), t1=round(float(t1), 4), **kw))
add("clash", 1.231, 1.931, col=WHITE, n=5000)
for g, tg in enumerate([1.727, 1.832, 1.856]):
    add("glyph", tg, tg + 0.3, col=PUR, group=g)
add("rise", 30.75, 31.66, col=RED)
add("arcs", 32.29, 32.91, col=PUR, n=3)
add("burst", 32.91, 33.61, col=PUR, n=6000)
b = jump(33.85, 34.2); add("burst", b, b + 0.7, col=PUR, n=4500)
b = jump(40.7, 41.5); add("burst", b, b + 0.6, col=WHITE, n=2500)
add("rise", 43.80, 45.88, col=ORANGE)
b = jump(47.2, 47.78); add("burst", b, b + 0.6, col=WHITE, n=2500)
b = jump(70.0, 70.7); add("burst", b, b + 0.6, col=ORANGE, n=3000)
add("orb", 72.06, 74.29, col=RED, spin=1)
add("burst", 74.29, 74.99, col=RED, n=6000)
add("clash", 74.92, 75.62, col=RED, n=4000)
add("arcs", 74.95, 75.44, col=RED, n=3)
add("pulse", 76.07, 76.51, col=WHITE)
add("orb", 80.94, 84.17, col=BLUE, spin=-1)
add("burst", 82.99, 83.69, col=BLUE, n=4000)
add("arcs", 84.64, 85.20, col=CYAN, n=2)
add("rise", 85.20, 87.57, col=RED)
b = jump(89.0, 89.65); add("burst", b, b + 0.7, col=PUR, n=4000)
add("arcs", 88.9, 89.65, col=PUR, n=2)
b = jump(91.87, 92.6); add("burst", b, b + 0.9, col=PUR, n=8000)
add("rise", 91.87, 93.85, col=PUR)
json.dump(ev, open("events.json", "w"), indent=1, ensure_ascii=False)
for e in ev:
    print(e["kind"], e["t0"], e["t1"])
