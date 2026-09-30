import torch,torch.nn as nn,torch.nn.functional as F,cv2,numpy as np,glob,os,sys,time
torch.set_num_threads(int(os.environ.get("TH","2")))
class SRVGG(nn.Module):
    def __init__(s,nf=64,nc=16,up=4):
        super().__init__(); s.up=up
        b=[nn.Conv2d(3,nf,3,1,1),nn.PReLU(nf)]
        for _ in range(nc): b+=[nn.Conv2d(nf,nf,3,1,1),nn.PReLU(nf)]
        b+=[nn.Conv2d(nf,3*up*up,3,1,1)]
        s.body=nn.ModuleList(b); s.ps=nn.PixelShuffle(up)
    def forward(s,x):
        o=x
        for l in s.body: o=l(o)
        return s.ps(o)+F.interpolate(x,scale_factor=s.up,mode="nearest")
m=SRVGG(); sd=torch.load(sys.argv[1]+"/sr/realesr-animevideov3.pth",map_location="cpu")
m.load_state_dict(sd.get("params",sd)); m.eval()
S=sys.argv[1]
os.makedirs(S+"/panels2x",exist_ok=True)
files=sorted(glob.glob(S+"/panels/*.png"))
for f in files:
    out=S+"/panels2x/"+os.path.basename(f)
    if os.path.exists(out): continue
    t=time.time()
    im=cv2.imread(f)[:,:,::-1].astype(np.float32)/255
    x=torch.from_numpy(np.ascontiguousarray(im.transpose(2,0,1)))[None]
    # tile to bound memory
    _,_,h,w=x.shape; T=400; P=16; y=torch.zeros(1,3,h*4,w*4)
    with torch.no_grad():
        for i in range(0,h,T):
            for j in range(0,w,T):
                i0,j0=max(i-P,0),max(j-P,0); i1,j1=min(i+T+P,h),min(j+T+P,w)
                o=m(x[:,:,i0:i1,j0:j1])
                y[:,:,i*4:min(i+T,h)*4,j*4:min(j+T,w)*4]=o[:,:,(i-i0)*4:(i-i0+min(T,h-i))*4,(j-j0)*4:(j-j0+min(T,w-j))*4]
    y=y[0].clamp(0,1).numpy().transpose(1,2,0)[:,:,::-1]*255
    y2=cv2.resize(y,(w*2,h*2),interpolation=cv2.INTER_AREA)
    cv2.imwrite(out,np.clip(y2+0.5,0,255).astype(np.uint8),[cv2.IMWRITE_PNG_COMPRESSION,3])
    print(os.path.basename(f),round(time.time()-t,1),flush=True)
