import cv2, numpy as np, sys
S=sys.argv[1]
cap=cv2.VideoCapture(S+"/src/shinjuku_96s_muted_lossless_retime.mp4")
N=8298; W,H=960,540
d=np.load(S+"/diffs.npy")
uniq=[i for i in range(N) if i==0 or d[i]>=0.2]
print("unique",len(uniq))
mm=np.lib.format.open_memmap(S+"/work/u960.npy",mode="w+",dtype=np.uint8,shape=(len(uniq),H,W,3))
fmap=np.zeros(N,np.int32); u=-1; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if i==0 or d[i]>=0.2:
        u+=1
        mm[u]=cv2.resize(f[:,268:268+2134],(W,H),interpolation=cv2.INTER_AREA)
    fmap[i]=u; i+=1
mm.flush(); np.save(S+"/work/fmap.npy",fmap); np.save(S+"/work/uniq.npy",np.array(uniq))
print(i,u)
