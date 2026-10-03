"""Design board for close-ups (no shots; rendered as stills by board())."""
import math
import numpy as np
from engine.mathx import V
from engine.anim import Ch
from engine.rig import Figure, GOJO, SUKUNA
from engine.camera import Cam
from engine.shot import Shot, Actor, draw_actors
from engine.canvas import paint
from engine import fx


class Head(Shot):
    t0, t1 = 0.0, 1.0
    def __init__(self, style, yaw=0.0, pitch=0.0, open_=1.0, fire=0.0, dist=0.75, glow=1.0, side=0.0, up=0.0, fov=36, bg=None, k=1.0):
        self.a = Actor(Figure(style, k))
        self.a.k(0, yaw=math.pi + yaw, hpitch=pitch, eye_open=open_, eye_fire=fire, eye_glow=glow, lean=0.0)
        J = self.a.fig.pose(0.0)
        H = J['H']
        F = J['Rh'] @ V(0, 0, 1)
        R = J['Rh'] @ V(1, 0, 0)
        self.cam = Cam(H + F * dist + R * side + V(0, up, 0), H + V(0, -0.02, 0), fov=fov)
        self.bg = bg
        super().__init__()

    def draw(self, fr, s):
        from engine.theme import T as THEME
        fr.b.clear(paint(self.bg or THEME['bg']).getColor4f())
        draw_actors(fr, self.cam, s, s, [self.a])


SHOTS = []
SEGMENTS = []
