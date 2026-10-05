"""Recover the selected D74 with verified existing code/art, in four sequential low-memory windows.

Run from any directory. --repo is a checkout containing anime/ and the published
collab/from_limo/066/batchD_P*/selected files. --package contains D34_selected.json
(exposure sheet), manifest_D34_selected.json (asset manifest),
verified_code_manifest.json, and optionally native_BGR_PIXEL_MD5SUMS.
--validate-only checks code/art/source/config without rendering or creating output.
The original video is a private local input and is never uploaded.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

WINDOWS = [(58,1485,1504),(59,1504,1521),(60,1521,1540),(61,1540,1559)]
SOURCE_SHA = '9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447'
FROZEN_SHA = 'd0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853'
RUNTIME_FILES = ['action_window.py','frames.py','layered.py','review_window.py','flowcam.py','matte_key.py',
                 'subsheet.py','measure.py','join_verify.py']

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',required=True,type=Path)
    ap.add_argument('--package',required=True,type=Path)
    ap.add_argument('--source',required=True,type=Path)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--frozen298',type=Path)
    ap.add_argument('--validate-only',action='store_true')
    a=ap.parse_args();repo=a.repo.resolve();pkg=a.package.resolve();source=a.source.resolve()
    sheet_path=pkg/'D34_selected.json'; manifest_path=pkg/'manifest_D34_selected.json'
    sheet=json.loads(sheet_path.read_text());manifest=json.loads(manifest_path.read_text())
    code=json.loads((pkg/'verified_code_manifest.json').read_text());bycode={Path(v['path']).name:v for v in code['files']}
    for filename in RUNTIME_FILES:
        assert sha(repo/'anime'/filename)==bycode[filename]['sha256'],('Code mismatch',filename)
    assert sha(source)==SOURCE_SHA,'Original source hash mismatch'
    states=manifest['states'];assert len(states)==len({s['id'] for s in states})==34
    assert [n for s in states for n in range(s['start'],s['end'])]==list(range(1485,1559))
    import cv2
    import numpy as np
    for state in states:
        p=repo/state['path'];assert sha(p)==state['output_sha256'],('Selected art hash mismatch',state['id'])
        im=cv2.imread(str(p),cv2.IMREAD_UNCHANGED);assert im.dtype==np.uint8 and list(im.shape[:2][::-1])==state['native_dimensions'] and im.shape[2]==3
        assert state['start']<=state['source_n']<state['end']
        for n in range(state['start'],state['end']):
            spec=sheet['frames_sheet'][str(n)];assert spec['id']==state['id'] and spec.get('full',spec.get('drawing'))==state['path']
            assert not any(k in spec for k in ['black','white','mix','wipe','white_wash','fx_drawn'])
            if 'hold' in spec:
                assert spec['ref']==state['source_n'] and spec['camera_only']=='none' and spec['zoom']==1 and spec['light']=='fixed' and spec['mode']=='full'
    assert sheet['frames']==[1485,1559] and len(sheet['frames_sheet'])==74
    assert sheet['grade']['grade_at']['D_G06']==[1512,1512]
    assert sheet['grade']['grade_at']['D_S06']==[1528,1531]
    assert sheet['grade']['grade_at']['D_S06b']==[1532,1536]
    assert sheet['grade']['keep_sat']=={x:[.35,.6] for x in ['D_S04','D_S05','D_S06','D_S06b']}
    if a.frozen298:assert sha(a.frozen298.resolve())==FROZEN_SHA,'Frozen master mismatch'
    print('Input verification: PASS;34 exact selected assets,74 exposures, verified runtime/source/grade',flush=True)
    if a.validate_only:return
    if not a.out:ap.error('--out is required unless --validate-only')
    out=a.out.resolve();assert not out.exists(),'Choose a new output path';out.mkdir(parents=True)
    env=os.environ.copy();env['JJK_SRC']=str(source)
    def call(args,log=None):
        if log:
            with log.open('xb') as f:subprocess.run(args,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
        else:subprocess.run(args,cwd=repo,env=env,check=True)
    native=out/'native';native.mkdir();videos=out/'video_inputs';videos.mkdir();vpaths=[];sources=[];pix={}
    for shot,start,end in WINDOWS:
        sub=out/f'shot{shot}.json';r=out/f'shot{shot}'
        call([sys.executable,str(repo/'anime/subsheet.py'),str(sheet_path),str(start),str(end),str(sub)])
        call([sys.executable,str(repo/'anime/measure.py'),sys.executable,str(repo/'anime/action_window.py'),str(sub),str(r)],out/f'shot{shot}.log')
        for n in range(start,end):
            p=r/f'R_n{n}.png';im=cv2.imread(str(p));assert im.shape==(941,1672,3) and im.max()>0
            pix[f'n{n}']=hashlib.md5(im.tobytes()).hexdigest();shutil.copyfile(p,native/p.name)
        v=videos/f'shot{shot}.mp4';shutil.copyfile(r/'redraw_24fps_once.mp4',v);vpaths.append(v)
        sources.extend(x for x in (r/'sources.md').read_text().splitlines() if x.startswith('- n'))
    expected=pkg/'native_BGR_PIXEL_MD5SUMS'
    if expected.exists():
        want={line.split()[1]:line.split()[0] for line in expected.read_text().splitlines() if line.strip()}
        assert pix==want,'Native pixel mismatch against selected delivery; inspect pinned environment before proceeding'
    (native/'sources.md').write_text('# D selected source records\n\n'+'\n'.join(sources)+'\n')
    (native/'native_BGR_PIXEL_MD5SUMS').write_text(''.join(f'{v}  {k}\n' for k,v in pix.items()))
    d=out/'redraw_74frames_24fps_once.mp4'
    call([sys.executable,str(repo/'anime/join_verify.py'),str(d),*[str(p) for p in vpaths]],out/'join_D74.log')
    if a.frozen298:
        join=out/'joined372';join.mkdir();frozen=a.frozen298.resolve()
        call([sys.executable,str(repo/'anime/join_verify.py'),str(join/'redraw_372frames_24fps_once.mp4'),str(frozen),str(d)],out/'join372.log')
        assert sha(frozen)==FROZEN_SHA,'Frozen input changed'
    print(f'Recovery finished: {out}; read run logs and join proofs. Video bytes may vary across FFmpeg versions.')

if __name__=='__main__':main()
