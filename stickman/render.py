"""Render a film module to video, in resumable 1-second chunks (60 frames), several
worker processes in parallel.  Usage:
  python3 render.py pilot OUTDIR [--workers 4] [--stills t1,t2,...] [--only a:b]"""
import argparse
import importlib
import os
import subprocess
import sys
import time
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.comp import composite  # noqa: E402

FPS = 60
CHUNK = 30


def frame_times(film):
    ts = []
    for (a, b) in film.SEGMENTS:
        n = int(round((b - a) * FPS))
        ts += [a + i / FPS for i in range(n)]
    return ts


class Film:
    def __init__(self, mod):
        self.mod = mod
        self.shots = [S() for S in mod.SHOTS]

    def shots_at(self, t):
        return [s for s in self.shots if s.t0 - 1e-6 <= t < s.t1 - 1e-6]

    def one(self, s, t):
        fr = s.frame(t)
        return composite(fr, vignette=getattr(s, 'vignette', 0.22))

    def render(self, t):
        act = self.shots_at(t)
        if not act:
            from engine.theme import T as THEME
            img = np.zeros((1080, 1920, 3), np.uint8)
            img[:] = (np.array(THEME['bg']) * 255).astype(np.uint8)
            return img
        if len(act) == 1:
            return self.one(act[0], t)
        # overlapping shots = a dissolve: blend across the overlap
        act.sort(key=lambda s: s.t0)
        a, b = act[0], act[-1]
        u = (t - b.t0) / max(1e-6, a.t1 - b.t0)
        u = min(1.0, max(0.0, u))
        ia = self.one(a, t).astype(np.float32)
        ib = self.one(b, t).astype(np.float32)
        mode = getattr(b, 'xmode', 'mix')
        if mode == 'add':      # luminous dissolve (light passes through)
            out = ia * (1 - u) + ib * u + np.minimum(ia, ib) * 0.0
        else:
            out = ia * (1 - u) + ib * u
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def render_chunk(args):
    modname, k, ts, outdir = args
    out = os.path.join(outdir, 'chunk_%04d.mp4' % k)
    if os.path.exists(out):
        return k, 0.0
    mod = importlib.import_module('films.' + modname)
    film = Film(mod)
    tmp = out + '.tmp.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
           '-pix_fmt', 'yuv420p', '-g', '60', '-bf', '2', tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for t in ts:
        img = film.render(t)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    os.replace(tmp, out)
    return k, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('film')
    ap.add_argument('outdir')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--stills', default='')
    ap.add_argument('--still_scale', type=float, default=0.5)
    ap.add_argument('--final', default='')
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    mod = importlib.import_module('films.' + args.film)
    if args.stills:
        film = Film(mod)
        for tok in args.stills.split(','):
            t = float(tok)
            img = film.render(t)
            if args.still_scale != 1:
                img = cv2.resize(img, None, fx=args.still_scale, fy=args.still_scale, interpolation=cv2.INTER_AREA)
            cv2.imwrite(os.path.join(args.outdir, 'still_%07.3f.png' % t), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return
    ts = frame_times(mod)
    jobs = [(args.film, k, ts[k * CHUNK:(k + 1) * CHUNK], args.outdir) for k in range((len(ts) + CHUNK - 1) // CHUNK)]
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(args.workers) as pool:
        for k, dt in pool.imap_unordered(render_chunk, jobs):
            print('chunk %d done %.1fs (elapsed %.0fs)' % (k, dt, time.time() - t0), flush=True)
    lst = os.path.join(args.outdir, 'chunks.txt')
    with open(lst, 'w') as f:
        for k in range(len(jobs)):
            f.write("file 'chunk_%04d.mp4'\n" % k)
    final = args.final or os.path.join(args.outdir, args.film + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    '-movflags', '+faststart', final], check=True)
    print('wrote', final, len(ts), 'frames')


if __name__ == '__main__':
    main()
