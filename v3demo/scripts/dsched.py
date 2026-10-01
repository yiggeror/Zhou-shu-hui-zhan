"""demo timeline (fight S043-S052): output time -> source time, with slow motion on the action,
super-slow on every hit, and designed fast transitions replacing the source's whip-blur frames"""
FPS = 60
# (out_dur, kind, tau0, tau1)    kind: 'act' = rendered action, 'whip' = transition between two crisp frames
SEG = [
    (1.10, "act", 34.66, 35.00),
    (0.10, "whip", 35.00, 35.10),
    (0.55, "act", 35.10, 35.27),
    (0.08, "whip", 35.27, 35.39),
    (0.45, "act", 35.39, 35.45),     # red fist lands on the chest
    (0.40, "act", 35.45, 35.57),
    (0.08, "whip", 35.57, 35.70),
    (0.60, "act", 35.70, 35.89),
    (0.06, "whip", 35.89, 35.93),
    (0.50, "act", 35.93, 36.00),     # cyan straight punch
    (0.50, "act", 36.00, 36.25),
    (0.10, "whip", 36.25, 36.39),
    (0.45, "act", 36.39, 36.46),     # side hit
    (0.40, "act", 36.46, 36.63),
    (0.12, "black", 36.63, 36.80),
    (0.90, "act", 36.80, 37.12),     # rapid cyan punches
    (0.08, "whip", 37.12, 37.19),
    (1.20, "act", 37.19, 37.79),     # red sweep, low dodge
    (0.10, "whip", 37.79, 37.89),
    (0.60, "act", 37.89, 38.09),     # finger gesture
    (0.50, "act", 38.11, 38.14),     # Sukuna's eye
]
HITS = [(35.40, "r"), (35.95, "c"), (36.40, "c"), (36.83, "c"), (36.93, "c"), (37.03, "c"), (37.22, "r")]
T0 = [0.0]
for d, *_ in SEG:
    T0.append(T0[-1] + d)
DUR = T0[-1]; NF = int(round(DUR * FPS))
def seg_at(t):
    for i, (d, k, a, b) in enumerate(SEG):
        if T0[i] <= t < T0[i + 1]:
            return i, (t - T0[i]) / d
    return len(SEG) - 1, 1.0
def tau_at(t):
    i, x = seg_at(t); d, k, a, b = SEG[i]
    return a + (b - a) * x
def t_of_tau(tau):
    for i, (d, k, a, b) in enumerate(SEG):
        if k == "act" and a <= tau <= b:
            return T0[i] + (tau - a) / (b - a) * d
    return None
