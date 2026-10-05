"""Check C2 recovery windows without modifying inputs or invoking the compositor.

Usage: python verify_run.py --repo REPO --source ORIGINAL
    --window 1437:1438:OUTPUT --window 1474:1485:OUTPUT --report NEW_REPORT.json
The optional report path must not already exist. --source performs a full source decode count.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from fractions import Fraction
import cv2

def run(args):
    return subprocess.run(args, capture_output=True, check=True).stdout

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',required=True,type=Path)
    ap.add_argument('--source',type=Path)
    ap.add_argument('--window',action='append',required=True,help='START:END:render directory')
    ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    if args.report and args.report.exists(): ap.error('Report exists; choose a new path')
    expected=dict(line.split() for line in (args.repo/'anime/expected/C2_native_pixmd5.txt').read_text().splitlines() if line and not line.startswith('#'))
    result={'windows':[],'result':'PASS'}
    if args.source:
        h=digest(args.source)
        assert h=='9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447','Original SHA256 mismatch'
        info=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames,color_space,color_range','-of','json',str(args.source)]))['streams'][0]
        for key,value in dict(codec_name='av1',width=2560,height=1440,pix_fmt='yuv420p',r_frame_rate='24/1',nb_read_frames='3499',color_space='bt709',color_range='tv').items():
            assert info.get(key)==value,(key,info.get(key),value)
        result['source']={'sha256':h,'stream':info}
    for window in args.window:
        start,end,directory=window.split(':',2);start,end=int(start),int(end);directory=Path(directory)
        assert end>start
        files=list(directory.glob('R_n*.png'))
        assert sorted(int(p.stem[3:]) for p in files)==list(range(start,end)),'Wrong or missing native frame numbers'
        native={}
        for n in range(start,end):
            im=cv2.imread(str(directory/f'R_n{n:04d}.png'))
            assert im is not None and im.shape==(941,1672,3),(n,'Wrong native geometry')
            md5=hashlib.md5(im.tobytes()).hexdigest()
            assert md5==expected[f'n{n}'],(n,'Native pixel mismatch',md5)
            native[f'n{n}']=md5
        video=directory/'redraw_24fps_once.mp4'
        probe=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_streams','-show_frames','-of','json',str(video)]))
        s=probe['streams'][0];frames=probe['frames'];tb=Fraction(s['time_base'])
        assert (s['width'],s['height'],s['pix_fmt'],s['r_frame_rate'])==(1672,942,'yuv420p','24/1')
        assert len(frames)==int(s['nb_read_frames'])==end-start
        assert all(int(f['best_effort_timestamp'])*tb==Fraction(i,24) for i,f in enumerate(frames)),'PTS discontinuity'
        run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'])
        result['windows'].append({'frames':[start,end],'native_bgr_md5':native,'main_video_sha256':digest(video),'video_frame_count':len(frames),'full_decode':'PASS','exact_24fps_pts':'PASS'})
    text=json.dumps(result,indent=2)+'\n'
    if args.report:
        with args.report.open('x') as f: f.write(text)
    print(text,end='')

if __name__=='__main__': main()
