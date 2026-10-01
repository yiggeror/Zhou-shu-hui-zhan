"""Speed-ramp schedule: output time t (s) -> source time tau (s, 96 s timeline).

Slow motion everywhere, super-slow at the fist crossing, fast whip-throughs over
the source's own transition blur frames.
"""
FPS = 60
DUR = 11.0
NF = int(DUR * FPS)
TAU_IMPACT = 1.231          # the two flaming fists cross (source frame 107)

# (t0, t1, label, tau0, tau1)
SEGS = [
    (0.00, 0.35, "ignite", None, None),
    (0.35, 2.20, "S001", 0.000, 0.635),
    (2.20, 2.27, "cut1", None, None),
    (2.27, 3.75, "S002", 0.655, 1.062),
    (3.75, 3.85, "whip", 1.062, 1.138),
    (3.85, 4.35, "S003a", 1.138, 1.158),
    (4.35, 4.42, "jump", 1.158, 1.196),
    (4.42, 4.80, "clash1", 1.196, 1.226),
    (4.80, 5.10, "clash2", 1.226, 1.236),
    (5.10, 5.42, "clash3", 1.236, 1.262),
    (5.42, 6.60, "pull", 1.262, 1.572),
    (6.60, 7.80, "vortex", 1.572, 1.578),
    (7.80, 10.70, "title", 1.700, 2.150),
    (10.70, 11.0, "end", None, None),
]

def seg_at(t):
    for s in SEGS:
        if s[0] <= t < s[1]:
            return s
    return SEGS[-1]

def tau_at(t):
    t0, t1, lab, a, b = seg_at(t)
    if a is None:
        return None
    x = (t - t0) / (t1 - t0)
    return a + (b - a) * x

def needs_base(t):
    lab = seg_at(t)[2]
    if lab in ("ignite", "cut1", "end"):
        return False
    if lab == "vortex":
        return t < 7.0
    return True
