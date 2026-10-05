"""Join frozen video segments and a new segment by stream copy (no re-encode, moov atom first) and verify the result:
  - the H.264 SPS / PPS of every input and of the output are identical (md5 of the parameter-set NAL units);
  - the decoded RGB of every output frame equals the inputs' decoded frames in order (ffmpeg framemd5, rgb24);
  - PTS run 0, 1/24, 2/24, ... with every step 1/24;
  - frame size / count / duration and the output's sha256.
Writes OUT, OUT_DIR/join_check.md and one decoded_rgb_md5_<name>.txt per input plus the joined one.
A frozen segment is never re-rendered: it enters only here, as a file.
usage: python3 anime/join_verify.py OUT.mp4 SEG1.mp4 SEG2.mp4 [...]
       python3 anime/join_verify.py --verify-only JOINED.mp4 SEG1.mp4 SEG2.mp4 [...]   (no join, just the checks)"""
import hashlib
import os
import re
import subprocess
import sys
import tempfile


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def framemd5(p):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:v:0', '-pix_fmt', 'rgb24', '-f', 'framemd5', '-'],
                         capture_output=True, text=True, check=True).stdout
    return [ln.split(',')[-1].strip() for ln in out.splitlines() if ln and not ln.startswith('#')]


def param_sets(p):
    with tempfile.NamedTemporaryFile(suffix='.h264') as t:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', p, '-map', '0:v:0', '-c', 'copy', '-bsf:v', 'h264_mp4toannexb',
                        '-f', 'h264', t.name], check=True)
        data = open(t.name, 'rb').read()
    sets = {7: set(), 8: set()}
    for nal in re.split(b'\x00\x00\x00\x01|\x00\x00\x01', data):
        if nal and (nal[0] & 31) in sets:
            sets[nal[0] & 31].add(hashlib.md5(nal.rstrip(b'\x00')).hexdigest()[:12])
    return sorted(sets[7]), sorted(sets[8])


def pts(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pts_time', '-of',
                          'csv=p=0', p], capture_output=True, text=True, check=True).stdout
    return [float(x.strip(',')) for x in out.split()]


def stream_info(p):
    return subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                           'stream=width,height,pix_fmt,r_frame_rate,duration,nb_read_frames', '-of', 'compact=p=0', p],
                          capture_output=True, text=True, check=True).stdout.strip()


def main():
    args = sys.argv[1:]
    verify_only = args[0] == '--verify-only'
    if verify_only:
        args = args[1:]
    out, segs = os.path.abspath(args[0]), [os.path.abspath(s) for s in args[1:]]
    odir = os.path.dirname(out)
    if not verify_only:
        if os.path.exists(out):
            sys.exit(f'{out} exists; refusing to overwrite (frozen masters are never overwritten)')
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as lst:
            for s in segs:
                lst.write(f"file '{s}'\n")
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst.name, '-c', 'copy', '-movflags', '+faststart', out], check=True)
        os.unlink(lst.name)
    lines = [f'# join check: {os.path.basename(out)}', '', 'inputs (ffmpeg -f concat -c copy, in this order):']
    md5s, ok = [], True
    for s in segs:
        m = framemd5(s)
        md5s += m
        name = os.path.splitext(os.path.basename(s))[0]
        open(os.path.join(odir, f'decoded_rgb_md5_{name}.txt'), 'w').write('\n'.join(m) + '\n')
        lines.append(f'- {s}: {len(m)} frames, sha256 {sha256(s)}')
    joined = framemd5(out)
    open(os.path.join(odir, 'decoded_rgb_md5_joined.txt'), 'w').write('\n'.join(joined) + '\n')
    ps = {s: param_sets(s) for s in segs + [out]}
    same_ps = len({(tuple(a), tuple(b)) for a, b in ps.values()}) == 1
    t = pts(out)
    steps = all(abs((y - x) - 1 / 24) < 1e-4 for x, y in zip(t, t[1:]))
    ident = joined == md5s
    ok = same_ps and steps and ident and abs(t[0]) < 1e-9
    lines += ['', f'SPS / PPS md5 (12 hex): ' + '; '.join(f'{os.path.basename(s)} {a}/{b}' for s, (a, b) in ps.items())
              + (' -> IDENTICAL' if same_ps else ' -> DIFFERENT'),
              f'decoded RGB per-frame md5: concatenated inputs ({len(md5s)}) == joined ({len(joined)}): '
              + ('IDENTICAL' if ident else 'DIFFERENT'),
              f'PTS: {len(t)} frames, first {t[0]:.6f} s, last {t[-1]:.6f} s, every step 1/24: {steps}',
              f'stream: {stream_info(out)}', f'output sha256 {sha256(out)}', '', 'RESULT: ' + ('PASS' if ok else 'FAIL')]
    open(os.path.join(odir, 'join_check.md'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
