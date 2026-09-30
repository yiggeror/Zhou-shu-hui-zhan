import cv2,numpy as np,sys
S=sys.argv[1]
U=np.load(S+"/work/u960.npy",mmap_mode="r")
n=len(U)
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
def g(i): return cv2.cvtColor(cv2.resize(np.ascontiguousarray(U[i]),(480,270),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2GRAY)
res=np.zeros(n); raw=np.zeros(n)
H,W=270,480
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
prev=g(0)
for i in range(1,n):
    cur=g(i)
    fl=dis.calc(cur,prev,None)  # cur->prev
    wp=cv2.remap(prev,xx+fl[...,0],yy+fl[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    r=np.abs(cur.astype(np.float32)-wp).astype(np.float32)
    r=cv2.blur(r,(9,9))  # structural residual
    res[i]=np.percentile(r,75); raw[i]=np.abs(cur.astype(np.float32)-prev).mean()
    prev=cur
np.save(S+"/work/ures.npy",res); np.save(S+"/work/uraw.npy",raw)
print("done")
