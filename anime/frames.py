"""Frame-exact access to the original video.  Convention used everywhere in this project:
n = zero-based decoded frame number, PTS = n / 24 s, intervals are [start, end)."""
import subprocess
import numpy as np

SRC = '/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/246ca686-706e-5160-9340-459ab573d49f/scratchpad/src/orig.mp4'


def frame(n, src=SRC, w=2560, h=1440):
    """decoded frame n (BGR uint8), selected by frame number, not by seeking to a time"""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def save(n, path, src=SRC):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', path],
                   check=True)
