"""Animation channels: keyed values with easing / smooth splines, time warps (hit-stops)
and second-order dynamics for follow-through."""
import bisect
import math
import numpy as np
from .mathx import EASE


def _arr(v):
    return np.asarray(v, dtype=np.float64) if isinstance(v, (list, tuple, np.ndarray)) else float(v)


class Ch:
    """Keyed channel.  keys: (t, value, ease) where `ease` shapes the segment that ENDS at
    this key.  ease 'sm' = C1 Hermite spline through neighbouring keys (monotone-clamped),
    other names come from mathx.EASE."""

    def __init__(self, v=None, keys=None):
        self.t, self.v, self.e = [], [], []
        if keys:
            for k in keys:
                self.key(*k)
        elif v is not None:
            self.key(0.0, v)

    def key(self, t, v, ease='sm'):
        v = _arr(v)
        i = bisect.bisect_right(self.t, t)
        self.t.insert(i, float(t)); self.v.insert(i, v); self.e.insert(i, ease)
        self._tan = None
        return self

    # chained helpers -------------------------------------------------------
    def to(self, dt, v, ease='sm'):
        """add key dt seconds after the last key"""
        return self.key(self.t[-1] + dt, v, ease)

    def hold(self, dt):
        return self.key(self.t[-1] + dt, self.v[-1], 'lin')

    @property
    def last(self):
        return self.t[-1], self.v[-1]

    # ----------------------------------------------------------------------
    def _tangents(self):
        n = len(self.t)
        tans = []
        for j in range(n):
            if j == 0 or j == n - 1:
                tans.append(self.v[j] * 0.0)
                continue
            d0 = (self.v[j] - self.v[j - 1]) / max(self.t[j] - self.t[j - 1], 1e-9)
            d1 = (self.v[j + 1] - self.v[j]) / max(self.t[j + 1] - self.t[j], 1e-9)
            m = (self.v[j + 1] - self.v[j - 1]) / max(self.t[j + 1] - self.t[j - 1], 1e-9)
            d0a, d1a, ma = np.atleast_1d(d0), np.atleast_1d(d1), np.atleast_1d(m).copy()
            same = (d0a * d1a) > 0
            ma[~same] = 0.0
            lim = 3.0 * np.minimum(np.abs(d0a), np.abs(d1a))
            ma = np.clip(ma, -lim, lim)
            # a key adjacent to a non-spline segment gets a flat tangent on that side
            if self.e[j] != 'sm' or self.e[j + 1] != 'sm':
                ma = ma * 0.0
            tans.append(ma if np.ndim(self.v[j]) else float(ma[0]))
        self._tan = tans

    def __call__(self, t):
        T = self.t
        if t <= T[0] or len(T) == 1:
            return self.v[0]
        if t >= T[-1]:
            return self.v[-1]
        i = bisect.bisect_right(T, t) - 1
        t0, t1 = T[i], T[i + 1]
        h = t1 - t0
        u = (t - t0) / h if h > 0 else 1.0
        e = self.e[i + 1]
        v0, v1 = self.v[i], self.v[i + 1]
        if e == 'sm':
            if self._tan is None:
                self._tangents()
            m0, m1 = self._tan[i] * h, self._tan[i + 1] * h
            u2, u3 = u * u, u * u * u
            return ((2 * u3 - 3 * u2 + 1) * v0 + (u3 - 2 * u2 + u) * m0 +
                    (-2 * u3 + 3 * u2) * v1 + (u3 - u2) * m1)
        return v0 + (v1 - v0) * EASE[e](u)


def const(v):
    return Ch(v)


def as_fn(x):
    """channel, callable or constant -> callable(t)"""
    if callable(x):
        return x
    c = _arr(x)
    return lambda t: c


class TimeWarp:
    """In-place hit-stops: the action clock freezes `hold` seconds at each hit, then runs
    faster for `catch` seconds so that everything after is back on the original timing."""

    def __init__(self, stops=()):
        self.stops = sorted(stops)  # (t_hit, hold, catch)

    def add(self, t, hold, catch=None):
        self.stops.append((t, hold, catch if catch is not None else hold * 2.0))
        self.stops.sort()
        return self

    def __call__(self, t):
        tau = t
        for (th, hold, catch) in self.stops:
            if t <= th:
                break
            if t < th + hold:
                tau -= (t - th)
            elif t < th + hold + catch:
                u = (t - th - hold) / catch
                # lag goes from `hold` back to 0 smoothly
                lag = hold * (1 - u * u * (3 - 2 * u))
                tau -= lag
        return tau

    def frozen(self, t):
        for (th, hold, catch) in self.stops:
            if th <= t < th + hold:
                return True
        return False


class Dyn:
    """Second-order follow-through of a channel (f = natural freq Hz, z = damping, r = response).
    Pre-integrated on a fixed grid between t0 and t1."""

    def __init__(self, src, t0, t1, f=3.0, z=0.6, r=0.0, rate=600.0):
        src = as_fn(src)
        self.t0, self.dt = t0, 1.0 / rate
        n = int(math.ceil((t1 - t0) * rate)) + 3
        k1 = z / (math.pi * f)
        k2 = 1 / ((2 * math.pi * f) ** 2)
        k3 = r * z / (2 * math.pi * f)
        x_prev = np.asarray(src(t0), dtype=np.float64)
        y = x_prev.copy()
        yd = y * 0.0
        out = [y.copy()]
        T = self.dt
        k2s = max(k2, 1.1 * (T * T / 4 + T * k1 / 2))
        for i in range(1, n):
            x = np.asarray(src(t0 + i * T), dtype=np.float64)
            xd = (x - x_prev) / T
            x_prev = x
            y = y + T * yd
            yd = yd + T * (x + k3 * xd - y - k1 * yd) / k2s
            out.append(y.copy())
        self.buf = np.array(out)

    def __call__(self, t):
        x = (t - self.t0) / self.dt
        i = int(math.floor(x))
        if i <= 0:
            return self.buf[0]
        if i >= len(self.buf) - 1:
            return self.buf[-1]
        f = x - i
        return self.buf[i] * (1 - f) + self.buf[i + 1] * f
