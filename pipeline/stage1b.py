# recompute chains with a wider margin for anchors next to dissolve boundaries
import sys,json,time,os
import numpy as np
from pipe import *
units=json.load(open(S+"/work/units.json"))
N=len(UNIQ); MARG=int(sys.argv[1])
def unit_us(un):
    a=int(FMAP[un["start"]]); b=int(FMAP[un["end"]-1])
    if UNIQ[a]<un["start"]: a+=1
    return a,b
for i in map(int,sys.argv[2:]):
    un=units[i]; a,b=unit_us(un)
    us=list(range(max(0,a-MARG),min(N-1,b+MARG)+1))
    for k,f in un["anchors"]:
        fn=f"{S}/chains/{k}.npz"
        if os.path.exists(fn) and len(np.load(fn)["us"])>=len(us): continue
        t=time.time(); ua=int(FMAP[f]); ch=chain(ua,us)
        fl=np.stack([cv2.resize(ch[u][0],(480,270),interpolation=cv2.INTER_AREA)*0.5 for u in us]).astype(np.float16)
        cf=np.stack([(np.clip(cv2.resize(ch[u][1],(480,270),interpolation=cv2.INTER_AREA),0,1)*255).astype(np.uint8) for u in us])
        sc=np.array([ch[u][2] for u in us],np.float32)
        np.savez(fn[:-4]+".part.npz",us=np.array(us),fl=fl,cf=cf,sc=sc,ua=ua); os.replace(fn[:-4]+".part.npz",fn)
        print(k,len(us),round(time.time()-t,1),flush=True)
