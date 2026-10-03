"""Global look.  'paper': warm paper background, ink-black stick figures (one solid colour,
no separation outlines, so joints never show gaps), colour only from energy and eyes.
'black': the same on black with white figures."""
import os

NAME = os.environ.get('STICK_THEME', 'paper')

PAPER = dict(
    bg=(0.925, 0.900, 0.845),
    ground=(0.885, 0.858, 0.800),
    ground_far=(0.905, 0.880, 0.825),
    env_line=(0.66, 0.635, 0.59),
    env_fill=(0.865, 0.838, 0.780),
    env_edge=(0.72, 0.695, 0.65),
    window=(0.80, 0.775, 0.72),
    ink=(0.085, 0.085, 0.095),
    head_fill=(0.085, 0.085, 0.095),
    shadow_alpha=0.16,
    speed=(0.08, 0.08, 0.09),
    flash=(1.0, 1.0, 1.0),
    tone_bg=(0.93, 0.90, 0.845), tone_fg=(0.06, 0.06, 0.07),
)
BLACK = dict(
    bg=(0.0, 0.0, 0.0),
    ground=(0.035, 0.035, 0.04),
    ground_far=(0.02, 0.02, 0.025),
    env_line=(0.30, 0.30, 0.33),
    env_fill=(0.05, 0.05, 0.06),
    env_edge=(0.22, 0.22, 0.25),
    window=(0.16, 0.16, 0.18),
    ink=(0.94, 0.94, 0.96),
    head_fill=(0.03, 0.03, 0.035),
    shadow_alpha=0.0,
    speed=(1.0, 1.0, 1.0),
    flash=(1.0, 1.0, 1.0),
    tone_bg=(0.0, 0.0, 0.0), tone_fg=(1.0, 1.0, 1.0),
)
T = PAPER if NAME == 'paper' else BLACK
PAPER_MODE = NAME == 'paper'
