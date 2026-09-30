import cv2,numpy as np,json,sys
S=sys.argv[1]
P=S+"/src/Opus_Animation_Reference_Pack/"
tl=json.load(open(P+"timeline.json"))
U=np.load(S+"/work/u960.npy",mmap_mode="r"); fmap=np.load(S+"/work/fmap.npy")
sift=cv2.SIFT_create(nfeatures=6000)
bf=cv2.BFMatcher(cv2.NORM_L2)
def prep(im):
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    return cv2.createCLAHE(2.0,(8,8)).apply(g)
def ncc(a,b,mask=None):
    a=cv2.GaussianBlur(a.astype(np.float32),(0,0),3); b=cv2.GaussianBlur(b.astype(np.float32),(0,0),3)
    if mask is None: mask=np.ones(a.shape,bool)
    a=a[mask];b=b[mask]; a=a-a.mean(); b=b-b.mean()
    return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()+1e-6))
out={}
for sh in tl["shots"]:
    img=cv2.imread(P+sh["reference_file"])
    for st in sh["generated_states"]:
        if st["panel"]=="single": pan=img
        elif st["panel"]=="A": pan=img[0:652]
        else: pan=img[679:1329]
        key=f'{sh["id"]}{"" if st["panel"]=="single" else st["panel"]}'
        cv2.imwrite(f"{S}/panels/{key}.png",pan)
        F=np.ascontiguousarray(U[fmap[st["source_frame"]]])
        s0=960/pan.shape[1]
        g=cv2.resize(pan,(960,int(round(pan.shape[0]*s0))),interpolation=cv2.INTER_AREA)
        ga=prep(g); fa=prep(F)
        k1,d1=sift.detectAndCompute(ga,None); k2,d2=sift.detectAndCompute(fa,None)
        M=None;ninl=0
        if d1 is not None and d2 is not None and len(k1)>10 and len(k2)>10:
            ms=bf.knnMatch(d1,d2,k=2)
            good=[m for m,n in (x for x in ms if len(x)==2) if m.distance<0.8*n.distance]
            if len(good)>=8:
                p1=np.float32([k1[m.queryIdx].pt for m in good]); p2=np.float32([k2[m.trainIdx].pt for m in good])
                M,inl=cv2.estimateAffinePartial2D(p1,p2,method=cv2.RANSAC,ransacReprojThreshold=5,maxIters=5000,confidence=0.999)
                ninl=int(inl.sum()) if inl is not None else 0
        ident=np.float32([[1,0,0],[0,1,(540-g.shape[0])/2]])
        cands={"ident":ident}
        if M is not None and ninl>=6: cands["sift"]=M.astype(np.float32)
        best=None
        for name,M0 in cands.items():
            w=cv2.warpAffine(ga,M0,(960,540)); m=cv2.warpAffine(np.ones_like(ga),M0,(960,540))>0
            sc=ncc(w,fa,m) if m.mean()>0.3 else -1
            # ECC refine
            try:
                Me=M0.copy()
                a=cv2.GaussianBlur(fa,(0,0),2).astype(np.float32); b=cv2.GaussianBlur(ga,(0,0),2).astype(np.float32)
                _,Me=cv2.findTransformECC(a,b,cv2.invertAffineTransform(M0).astype(np.float32),cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-5),None,5)
                Me=cv2.invertAffineTransform(Me)
                w2=cv2.warpAffine(ga,Me,(960,540)); m2=cv2.warpAffine(np.ones_like(ga),Me,(960,540))>0
                sc2=ncc(w2,fa,m2) if m2.mean()>0.3 else -1
                if sc2>sc: sc,M0,name=sc2,Me,name+"+ecc"
            except cv2.error: pass
            if best is None or sc>best[0]: best=(sc,M0,name)
        sc,M0,name=best
        # express mapping from panel pixel coords -> 1920x1080 output coords
        Mfull=np.vstack([M0,[0,0,1]])@np.diag([s0,s0,1])
        Mfull=(np.diag([2,2,1])@Mfull)[:2]
        cov=float((cv2.warpAffine(np.ones(pan.shape[:2],np.uint8),Mfull,(1920,1080))>0).mean())
        out[key]=dict(shot=sh["id"],panel=st["panel"],frame=st["source_frame"],M=Mfull.tolist(),score=sc,method=name,inliers=ninl,cover=cov,size=[pan.shape[1],pan.shape[0]])
        print(key,st["source_frame"],name,ninl,round(sc,3),round(cov,3),flush=True)
        w=cv2.warpAffine(g,M0,(960,540))
        vis=np.hstack([cv2.resize(F,(480,270)),cv2.resize(w,(480,270)),cv2.resize(cv2.addWeighted(F,0.5,w,0.5,0),(480,270))])
        cv2.imwrite(f"{S}/reg/{key}.jpg",vis,[cv2.IMWRITE_JPEG_QUALITY,70])
json.dump(out,open(S+"/work/reg.json","w"),indent=1)
