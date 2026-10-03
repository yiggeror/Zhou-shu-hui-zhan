"""Small math helpers: vectors, rotations, easing, hashing noise."""
import math
import numpy as np

V = lambda *a: np.array(a, dtype=np.float64)


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v * 0.0


def lerp(a, b, u):
    return a + (b - a) * u


def clamp(x, a, b):
    return a if x < a else b if x > b else x


def smoothstep(e0, e1, x):
    u = clamp((x - e0) / (e1 - e0), 0.0, 1.0) if e1 != e0 else float(x >= e1)
    return u * u * (3 - 2 * u)


# ---- rotations: frames are 3x3 matrices whose columns are (right, up, forward)
def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float64)


def Rx(a):  # positive = tilt the up vector toward forward (lean forward / look down)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float64)


def Rz(a):  # positive = tilt the up vector toward right
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], dtype=np.float64)


def yaw_of(v):
    return math.atan2(v[0], v[2])


# ---- easing (u in 0..1)
def _back(u, s=1.70158):
    return u * u * ((s + 1) * u - s)


EASE = {
    'lin': lambda u: u,
    'in': lambda u: u * u,
    'in3': lambda u: u * u * u,
    'out': lambda u: 1 - (1 - u) ** 2,
    'out3': lambda u: 1 - (1 - u) ** 3,
    'out4': lambda u: 1 - (1 - u) ** 4,
    'outexp': lambda u: 1.0 if u >= 1 else 1 - 2 ** (-10 * u),
    'io': lambda u: u * u * (3 - 2 * u),
    'io3': lambda u: 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    'inback': lambda u: _back(u),
    'outback': lambda u: 1 - _back(1 - u),
    'outback2': lambda u: 1 - _back(1 - u, 2.6),
    'hold': lambda u: 0.0 if u < 1 else 1.0,
}


# ---- deterministic noise
def hash01(*xs):
    h = 0x9E3779B97F4A7C15
    for x in xs:
        h ^= (int(x) & 0xFFFFFFFF) + 0x9E3779B9 + ((h << 6) & 0xFFFFFFFFFFFFFFFF) + (h >> 2)
        h &= 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xff51afd7ed558ccd) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    return (h & 0xFFFFFF) / float(0x1000000)


def vnoise1(x, seed=0):
    """smooth 1D value noise in -1..1"""
    i = math.floor(x)
    f = x - i
    a = hash01(i, seed) * 2 - 1
    b = hash01(i + 1, seed) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def fbm1(x, seed=0, oct=3):
    s, a, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        s += a * vnoise1(x * (2 ** o), seed + 17 * o)
        tot += a
        a *= 0.5
    return s / tot
