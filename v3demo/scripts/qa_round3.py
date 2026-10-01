"""QA of a round-3 keyframe pack: registration fit vs the source frame, improvement over existing keys,
sharpness, and comparison sheets. Does not modify the pipeline's registration data."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/work")
import numpy as np, cv2
D = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
S = "/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad"
U = np.load(S + "/work/u960.npy", mmap_mode="r"); fmap = np.load(S + "/work/fmap.npy"); ts = np.load(S + "/ts.npy")
req = {r["id"]: r for r in json.load(open(S + "/v3/round3/keyframe_requests_round3.json"))}
man = json.load(open(D + "/manifest.json"))
from crisp import render_crisp2
sift = cv2.SIFT_create(nfeatures=6000); bfm = cv2.BFMatcher(cv2.NORM_L2)
def prep(im): return cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
def ncc(a, b, mask):
    a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 3)[mask]; b = cv2.GaussianBlur(b.astype(np.float32), (0, 0), 3)[mask]
    a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-6))
def edge_fit(src, img):
    """share of the source's strong edges that have an edge of the image within 3 px (960x540)"""
    es = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY), (0, 0), 1.2), 50, 130) > 0
    ei = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 1.2), 50, 130).astype(np.uint8)
    near = cv2.dilate(ei, np.ones((7, 7), np.uint8)) > 0
    return float((es & near).sum() / max(es.sum(), 1))
def register(pan, F):
    s0 = 960 / pan.shape[1]
    g = cv2.resize(pan, (960, int(round(pan.shape[0] * s0))), interpolation=cv2.INTER_AREA)
    ga, fa = prep(g), prep(F)
    cands = {"ident": np.float32([[1, 0, 0], [0, 1, (540 - g.shape[0]) / 2]])}
    k1, d1 = sift.detectAndCompute(ga, None); k2, d2 = sift.detectAndCompute(fa, None)
    if d1 is not None and d2 is not None and len(k1) > 10 and len(k2) > 10:
        good = [m for m, n in (x for x in bfm.knnMatch(d1, d2, k=2) if len(x) == 2) if m.distance < 0.8 * n.distance]
        if len(good) >= 8:
            p1 = np.float32([k1[m.queryIdx].pt for m in good]); p2 = np.float32([k2[m.trainIdx].pt for m in good])
            M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=5, maxIters=5000, confidence=0.999)
            if M is not None and inl is not None and inl.sum() >= 6: cands["sift"] = M.astype(np.float32)
    best = None
    for name, M0 in cands.items():
        m0 = cv2.warpAffine(np.ones_like(ga), M0, (960, 540)) > 0
        sc = ncc(cv2.warpAffine(ga, M0, (960, 540)), fa, m0) if m0.mean() > 0.3 else -1
        try:
            a = cv2.GaussianBlur(fa, (0, 0), 2).astype(np.float32); b = cv2.GaussianBlur(ga, (0, 0), 2).astype(np.float32)
            _, Me = cv2.findTransformECC(a, b, cv2.invertAffineTransform(M0).astype(np.float32), cv2.MOTION_AFFINE,
                                         (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), None, 5)
            Me = cv2.invertAffineTransform(Me)
            m2 = cv2.warpAffine(np.ones_like(ga), Me, (960, 540)) > 0
            sc2 = ncc(cv2.warpAffine(ga, Me, (960, 540)), fa, m2) if m2.mean() > 0.3 else -1
            if sc2 > sc and 0.5 < abs(np.linalg.det(Me[:, :2])) < 2.0: sc, M0, name = sc2, Me, name + "+ecc"
        except cv2.error:
            pass
        if best is None or sc > best[0]: best = (sc, M0, name)
    sc, M0, name = best
    return cv2.warpAffine(g, M0, (960, 540), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), sc, name
rows = []; tiles = []
for it in sorted(man, key=lambda r: r["id"]):
    k = it["id"]; f = int(it["source_frame"]); r = req.get(k)
    ok_frame = r is not None and r["source_frame"] == f
    pan = cv2.imread(os.path.join(D, it["file"]))
    F = np.ascontiguousarray(U[fmap[f]])
    w, sc, name = register(pan, F)
    old, okey, oq, _ = render_crisp2(float(ts[f]), 14, "auto")
    old = cv2.resize((old * 255).astype(np.uint8), (960, 540), interpolation=cv2.INTER_AREA)
    m = np.ones((540, 960), bool)
    sc_old = ncc(prep(old), prep(F), m)
    ef_new, ef_old = edge_fit(F, w), edge_fit(F, old)
    lap = float(cv2.Laplacian(cv2.cvtColor(pan, cv2.COLOR_BGR2GRAY).astype(np.float32), cv2.CV_32F).var())
    rows.append(dict(id=k, shot=it["shot"], frame=f, frame_ok=ok_frame, size=f"{pan.shape[1]}x{pan.shape[0]}", reg=name,
                     ncc_new=round(sc, 3), ncc_old=round(sc_old, 3), edge_new=round(ef_new, 3), edge_old=round(ef_old, 3), sharp=round(lap, 0), old_key=okey))
    def lab(a, t):
        a = cv2.resize(a, (400, 225), interpolation=cv2.INTER_AREA).copy()
        cv2.rectangle(a, (0, 0), (399, 17), (0, 0, 0), -1); cv2.putText(a, t, (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA); return a
    ov = cv2.addWeighted(F, 0.5, w, 0.5, 0)
    tiles.append(np.hstack([lab(F, f"{k} {it['shot']} original f{f}"), lab(w, f"{k} new  fit {sc:.2f} edge {ef_new:.2f}"),
                            lab(old, f"old {okey} fit {sc_old:.2f} edge {ef_old:.2f}"), lab(ov, "original/new 50% overlay")]))
    print(k, it["shot"], f, ok_frame, name, round(sc, 2), round(sc_old, 2), round(ef_new, 2), round(ef_old, 2), flush=True)
json.dump(rows, open(OUT + "/qa.json", "w"), ensure_ascii=False, indent=1)
for s in range(0, len(tiles), 8):
    cv2.imwrite(f"{OUT}/qa_{s // 8 + 1:02d}.jpg", np.vstack(tiles[s:s + 8]), [cv2.IMWRITE_JPEG_QUALITY, 85])
