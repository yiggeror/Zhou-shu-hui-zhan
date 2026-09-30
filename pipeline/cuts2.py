import json,numpy as np,sys
S=sys.argv[1]
tl=json.load(open(S+"/src/Opus_Animation_Reference_Pack/timeline.json"))
ts=np.load(S+"/ts.npy"); fmap=np.load(S+"/work/fmap.npy"); uniq=np.load(S+"/work/uniq.npy")
res=np.load(S+"/work/ures.npy"); raw=np.load(S+"/work/uraw.npy")
K=0.706445
def f_at(t): return int(np.searchsorted(ts,t*K-1e-6))
shots=tl["shots"]
out=[]
for k,sh in enumerate(shots):
    if k==0: continue
    b=sh["start"]
    pa=max(g["source_frame"] for g in shots[k-1]["generated_states"])
    na=min(g["source_frame"] for g in sh["generated_states"])
    lo=max(f_at(b-0.3),pa+1); hi=min(f_at(b+0.3),na)
    ulo=fmap[lo]; uhi=fmap[hi]
    if uniq[ulo]<lo: ulo+=1
    cand=list(range(ulo,uhi+1))
    r=res[cand]; j=cand[int(np.argmax(r))]
    s=np.sort(r)[::-1]
    out.append(dict(id=sh["id"],doc=f_at(b),cut=int(uniq[j]),u=j,res=float(res[j]),res2=float(s[1]) if len(s)>1 else 0.,
        med=float(np.median(res[max(0,j-15):j+15]))))
json.dump(out,open(S+"/work/cuts_auto.json","w"))
for o in out:
    flag="" if o["res"]>2.5*max(o["res2"],1e-3) and o["res"]>3*o["med"] else "  <-- ambiguous"
    print(o["id"],o["doc"],o["cut"],round(o["res"],1),round(o["res2"],1),round(o["med"],1),flag)
