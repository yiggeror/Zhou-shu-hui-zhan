"""The whole film: shots 0-125, frames 73-3272 of the original (3.04 s - 136.33 s)."""
from films import p_open, seq_b, seq_c, seq_d, p_fight, seq_f, seq_g, seq_h, seq_i, seq_j, seq_k, seq_l

PARTS = [p_open, seq_b, seq_c, seq_d, p_fight, seq_f, seq_g, seq_h, seq_i, seq_j, seq_k, seq_l]
SHOTS = [S for m in PARTS for S in m.SHOTS]
SEGMENTS = [(73 / 24, 3272 / 24)]
