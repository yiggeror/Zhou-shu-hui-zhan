"""Register supplementary K keyframes (single 16:9 redraws) to their source frames."""
import cv2, numpy as np, json, sys, os
S = sys.argv[1]; D = sys.argv[2]
U = np.load(S + "/work/u960.npy", mmap_mode="r"); fmap = np.load(S + "/work/fmap.npy")
reg = json.load(open(S + "/work/reg.json"))
man = json.load(open(D + "/manifest_reg.json"))["images"]
sift = cv2.SIFT_create(nfeatures=6000); bf = cv2.BFMatcher(cv2.NORM_L2)
def prep(im):
    return cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
def ncc(a, b, mask):
    a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 3)[mask]; b = cv2.GaussianBlur(b.astype(np.float32), (0, 0), 3)[mask]
    a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-6))
os.makedirs(S + "/regK", exist_ok=True)
for it in man:
    key = it["id"]; f = int(it["source_frame"])
    pan = cv2.imread(os.path.join(D, it["image_file"]))
    cv2.imwrite(f"{S}/panels/{key}.png", pan)
    F = np.ascontiguousarray(U[fmap[f]])
    s0 = 960 / pan.shape[1]
    g = cv2.resize(pan, (960, int(round(pan.shape[0] * s0))), interpolation=cv2.INTER_AREA)
    ga, fa = prep(g), prep(F)
    cands = {"ident": np.float32([[1, 0, 0], [0, 1, (540 - g.shape[0]) / 2]])}
    k1, d1 = sift.detectAndCompute(ga, None); k2, d2 = sift.detectAndCompute(fa, None)
    ninl = 0
    if d1 is not None and d2 is not None and len(k1) > 10 and len(k2) > 10:
        good = [m for m, n in (x for x in bf.knnMatch(d1, d2, k=2) if len(x) == 2) if m.distance < 0.8 * n.distance]
        if len(good) >= 8:
            p1 = np.float32([k1[m.queryIdx].pt for m in good]); p2 = np.float32([k2[m.trainIdx].pt for m in good])
            M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=5, maxIters=5000, confidence=0.999)
            ninl = int(inl.sum()) if inl is not None else 0
            if M is not None and ninl >= 6: cands["sift"] = M.astype(np.float32)
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
            # reject degenerate ECC solutions (extreme scale/shear)
            det = abs(np.linalg.det(Me[:, :2]))
            if sc2 > sc and 0.5 < det < 2.0: sc, M0, name = sc2, Me, name + "+ecc"
        except cv2.error:
            pass
        if best is None or sc > best[0]: best = (sc, M0, name)
    sc, M0, name = best
    Mfull = (np.diag([2, 2, 1]) @ (np.vstack([M0, [0, 0, 1]]) @ np.diag([s0, s0, 1])))[:2]
    reg[key] = dict(shot=it["shot"], panel="single", frame=f, M=Mfull.tolist(), score=sc, method=name, inliers=ninl,
                    cover=float((cv2.warpAffine(np.ones(pan.shape[:2], np.uint8), Mfull, (1920, 1080)) > 0).mean()), size=[pan.shape[1], pan.shape[0]])
    w = cv2.warpAffine(g, M0, (960, 540))
    cv2.imwrite(f"{S}/regK/{key}.jpg", np.hstack([cv2.resize(F, (320, 180)), cv2.resize(w, (320, 180)), cv2.resize(cv2.addWeighted(F, .5, w, .5, 0), (320, 180))]), [cv2.IMWRITE_JPEG_QUALITY, 70])
    print(key, it["shot"], f, name, ninl, round(sc, 3), flush=True)
json.dump(reg, open(S + "/work/reg.json", "w"), indent=1)
