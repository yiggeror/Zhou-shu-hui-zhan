"""Shared street set for the close-combat shots (original shots 42-49)."""
import math
import numpy as np
from engine.mathx import V
from engine.env import Sky, Ground, Building

LINE = (0.66, 0.70, 0.77)


def corner(cx, cz, r, a0, a1, n=10):
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append(V(cx + r * math.cos(a), 0, cz + r * math.sin(a)))
    return pts


def build():
    sky = Sky()
    lines = []
    # far curb with a rounded corner into a side street at x = 5
    lines.append((V(-80, 0, 5), V(2.5, 0, 5), 0.10, 0.9))
    arc = corner(2.5, 7.5, 2.5, -math.pi / 2, 0.0)
    for a, b in zip(arc[:-1], arc[1:]):
        lines.append((a, b, 0.10, 0.9))
    lines.append((V(5, 0, 7.5), V(5, 0, 80), 0.10, 0.9))
    arc2 = corner(11.5, 7.5, 2.5, -math.pi, -math.pi / 2)
    lines.append((V(9, 0, 80), V(9, 0, 7.5), 0.10, 0.9))
    for a, b in zip(arc2[:-1], arc2[1:]):
        lines.append((a, b, 0.10, 0.9))
    lines.append((V(11.5, 0, 5), V(80, 0, 5), 0.10, 0.9))
    # near curb
    lines.append((V(-80, 0, -5), V(80, 0, -5), 0.10, 0.9))
    # faint centre dashes
    for i in range(-20, 20):
        x = i * 4.0
        lines.append((V(x, 0, 0.0), V(x + 1.8, 0, 0.0), 0.08, 0.35))
    ground = Ground(lines=lines)
    blds = []
    xs = [-60, -46, -36, -27, -18, -10, -3, 1.5]
    hs = [34, 22, 40, 28, 46, 30, 38]
    for i in range(len(xs) - 1):
        blds.append(Building(xs[i] + 0.4, xs[i + 1] - 0.4, 8.0, 22.0, hs[i], seed=10 + i, style='vstrips',
                             win=(0.93, 0.95, 1.0), win_density=0.62, win_k=0.75, color=(0.21, 0.25, 0.33)))
    xs2 = [12.5, 20, 30, 41, 55]
    hs2 = [42, 30, 36, 26]
    for i in range(len(xs2) - 1):
        blds.append(Building(xs2[i] + 0.4, xs2[i + 1] - 0.4, 8.0, 22.0, hs2[i], seed=30 + i, style='vstrips',
                             win=(0.93, 0.95, 1.0), win_density=0.6, win_k=0.75, color=(0.21, 0.25, 0.33)))
    # side street far end
    blds.append(Building(4, 13, 40, 52, 50, seed=50, style='vstrips', win_density=0.5, win_k=0.75, color=(0.21, 0.25, 0.33), win=(0.93, 0.95, 1.0)))
    # near side (seen when the camera turns)
    xs3 = [-60, -40, -25, -12, 0, 12, 26, 44, 60]
    hs3 = [30, 44, 26, 38, 32, 40, 28, 36]
    for i in range(len(xs3) - 1):
        blds.append(Building(xs3[i] + 0.4, xs3[i + 1] - 0.4, -24.0, -8.0, hs3[i], seed=70 + i, style='vstrips',
                             win=(0.93, 0.95, 1.0), win_density=0.55, win_k=0.7, color=(0.21, 0.25, 0.33)))
    return sky, ground, blds
