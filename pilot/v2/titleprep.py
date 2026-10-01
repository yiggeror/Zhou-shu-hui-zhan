"""title layer prep (S004 anchor space, 1080p): title-less plate, glyph groups, land-time map"""
import numpy as np, cv2
a = cv2.imread("s004_asset.jpg")
g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
m = np.load("title_mask.npy")
n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
# glyph groups by component centroid x: 0=呪 1=術 2=廻 3=戦 4=furigana
grp = np.full(n, -1, np.int32)
for i in range(1, n):
    x, y = cen[i]
    ci = (lab == i).astype(np.uint8)
    ring = (cv2.dilate(ci, np.ones((15, 15), np.uint8)) > 0) & (cv2.dilate(ci, np.ones((5, 5), np.uint8)) == 0)
    if g[ci > 0].mean() / 255 >= 0.15 or g[ring].mean() / 255 <= 0.6:
        continue                             # background pocket / blob, not ink with a white outline
    if 255 <= st[i, 1] and st[i, 1] + st[i, 3] <= 300 and st[i, 0] >= 1370:
        continue                             # furigana handled below
    grp[i] = 0 if x < 530 else 1 if x < 935 else 2 if x < 1320 else 3
G = np.where(lab > 0, grp[lab], -1).astype(np.int32)
fur = np.zeros_like(m); fur[255:298, 1370:1712] = (g[255:298, 1370:1712] < 110)
G[(fur > 0) & (G < 0)] = 4
core = (G >= 0).astype(np.uint8)
# nearest-group labelling for the halo ring
ys, xs = np.where(core > 0)
dist, lbl = cv2.distanceTransformWithLabels(1 - core, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
lut = np.full(lbl.max() + 1, -1, np.int32)
lut[lbl[ys, xs]] = G[ys, xs]
Gh = lut[lbl]
halo = (dist <= 9).astype(np.uint8)            # glyph + its white outline
plate = cv2.inpaint(a, cv2.dilate(halo, np.ones((5, 5), np.uint8)), 9, cv2.INPAINT_TELEA)
cv2.imwrite("s004_notitle.png", plate)
GA = np.zeros((5, 1080, 1920), np.float32)
for k in range(5):
    GA[k] = cv2.GaussianBlur(((Gh == k) & (halo > 0)).astype(np.float32), (0, 0), 1.2)
np.save("title_groups.npy", GA.astype(np.float16))
np.save("title_core_grp.npy", np.where(core > 0, G, -1).astype(np.int8))
v = plate.copy(); cv2.imwrite("plate_half.jpg", cv2.resize(v, (960, 540), interpolation=cv2.INTER_AREA))
col = np.float32([[0, 0, 255], [0, 255, 0], [255, 0, 0], [0, 255, 255], [255, 0, 255]])
ov = a.astype(np.float32) * 0.4
for k in range(5):
    ov += GA[k][..., None] * col[k] * 0.6
cv2.imwrite("groups_half.jpg", cv2.resize(ov.astype(np.uint8), (960, 540), interpolation=cv2.INTER_AREA))
print([int((Gh[halo > 0] == k).sum()) for k in range(5)])
