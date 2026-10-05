"""Exposure sheets for batch A [1202,1248) and batch B [1293,1357) (collab/to_limo/051) from the drawings Limo
delivers as collab/from_limo/051/batch{A,B}/<ID>_n<source>.png.  Usage: python3 anime/build_051_sheets.py A|B"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (id, source frame, exposures, kind, extra)
#   kind 'single'   one exposure, the drawing shown as it is
#   kind 'views'    a hold over frames that are different views in the original (on twos over a fly-through or a
#                   fast pan): no camera, light held, each exposure's luminance curve fitted at its own original frame
#                   with one white balance (the drawing's own source frame)
#   kind 'hold'     a hold on the same view: the whole-frame camera and the light change measured on the original
#   kind 'still'    a hold, no camera, light held, graded at the frames given by grade_at
#   kind 'chain'    a chain of same-canvas edits (S2 -> S3 -> S4, E09a -> E09b, ...) held as ONE group: the base's
#                   registration, one camera path from the base's source frame ('measured', or 'none' = still), each
#                   frame showing its own image of the chain; light held when still
A = [   # as locked by Limo, from_limo/051/msg_003 (24 states)
    ('C1', 1202, [1202, 1203], 'views', {}),
    ('C2', 1204, [1204, 1205], 'views', {}),
    ('C3', 1206, [1206], 'single', {}),
    ('R1', 1208, [1207, 1208], 'views', {}),
    ('R2', 1210, [1209, 1210], 'views', {}),
    ('R3', 1211, [1211], 'single', {}),
    ('S1', 1212, [1212], 'single', {}),
    ('S2', 1213, [1213, 1214, 1215], 'hold', {}),
    ('S3', 1216, [1216, 1217], 'hold', {}),
    # 1219-1222: S4 under the white wash fitted to the original (n1222 is 84 % white with a faint pink/figure residue,
    # not a pure white frame)
    ('S4', 1218, [1218, 1219, 1220, 1221, 1222], 'still', {'wash': [1219, 1220, 1221, 1222], 'grade_at': [1218, 1218]}),
    ('W1', 1224, [1223, 1224], 'still', {'wash': [1223], 'grade_at': [1224, 1224]}),
    ('W2', 1225, [1225], 'single', {}),
    ('X1', 1226, [1226, 1227], 'views', {}),
    ('X2', 1228, [1228, 1229], 'views', {}),
    ('X3', 1230, [1230, 1231], 'views', {}),
    ('X4', 1232, [1232, 1233], 'views', {}),
    ('X5', 1234, [1234, 1235], 'views', {}),
    ('X6', 1236, [1236, 1237], 'views', {}),
    ('X7', 1238, [1238, 1239], 'views', {}),
    ('X8', 1240, [1240, 1241], 'views', {}),
    ('ST1', 1242, [1242, 1243], 'views', {}),
    ('ST2', 1244, [1244, 1245], 'views', {}),
    ('ST3a', 1246, [1246], 'single', {}),
    ('ST3b', 1247, [1247], 'single', {}),
]
A_FLAT = {}

B = [
    ('E07', 1293, [1293], 'single', {}),
    ('E08a', 1294, [1294], 'single', {}),
    ('E08', 1295, [1295], 'single', {}),
    # 1296-1299 the original's camera turns ~5 deg and drops ~88 px (impact shake): three drawings, each in its own
    # source framing, with the measured camera inside each short hold (052)
    ('E09a', 1296, [1296, 1297], 'hold', {}),
    ('E09m', 1298, [1298, 1299], 'hold', {}),
    ('E09b', 1301, [1300, 1301, 1302], 'hold', {}),
    ('E10', 1303, [1303], 'single', {}),
    ('E11', 1304, [1304], 'single', {}),
    ('E12', 1305, [1305], 'single', {}),
    ('E13', 1306, [1306], 'single', {}),
    ('E14', 1307, [1307], 'single', {}),
    ('E15', 1308, [1308], 'single', {}),
    ('E16', 1309, [1309], 'single', {}),
    ('E17a', 1310, [1310, 1311], 'chain', {'chain': ('E17', 1310, 'measured')}),
    ('E17b', 1313, [1312, 1313, 1314], 'chain', {'chain': ('E17', 1310, 'measured'), 'wb_from': 'E17a'}),
    ('E17c', 1316, [1315, 1316, 1317], 'chain', {'chain': ('E17', 1310, 'measured'), 'wb_from': 'E17a'}),
    ('E18', 1318, [1318], 'single', {}),
    ('E19', 1321, [1321], 'single', {}),
    ('E20', 1322, [1322], 'single', {}),
    ('E21', 1323, [1323], 'single', {}),
    ('B1', 1324, [1324, 1328, 1332], 'loop', {}),
    ('B2', 1325, [1325, 1329, 1333], 'loop', {}),
    ('B3', 1326, [1326, 1330], 'loop', {}),
    ('B4', 1327, [1327, 1331], 'loop', {}),
    ('E26', 1334, [1334], 'single', {}),
    ('E27', 1335, [1335], 'single', {}),
    ('E28', 1336, [1336], 'single', {}),
    ('E29', 1337, [1337], 'single', {}),
    ('E30', 1338, [1338], 'single', {}),
    # the original pulls back slowly (~14 % over 1339-1356): one drawing chain cannot cover that without wide edge
    # fill, so the chain is held still (a known approximation)
    ('H1', 1340, [1339, 1340], 'chain', {'chain': ('H', 1340, 'none')}),
    ('H2', 1342, [1341, 1342], 'chain', {'chain': ('H', 1340, 'none'), 'wb_from': 'H1'}),
    ('H3a', 1344, [1343, 1344, 1345, 1346], 'chain', {'chain': ('H', 1340, 'none'), 'wb_from': 'H1'}),
    ('H3b', 1348, [1347, 1348, 1349, 1350], 'chain', {'chain': ('H', 1340, 'none'), 'wb_from': 'H1'}),
    ('H3c', 1352, [1351, 1352, 1353, 1354], 'chain', {'chain': ('H', 1340, 'none'), 'wb_from': 'H1'}),
    ('H4', 1355, [1355, 1356], 'views', {}),
]
B_FLAT = {1319: 'black', 1320: 'black'}


def build(name, table, flat, frames, out, d=None):
    d = d or os.path.join('collab', 'from_limo', '051', f'batch{name}')
    path, missing = {}, []
    for did, src, _, _, _ in table:
        hits = sorted(glob.glob(os.path.join(ROOT, d + '*', f'{did}_n{src}*.png')))   # batchA, batchA_city, ...
        if hits:
            path[did] = os.path.relpath(hits[-1], ROOT)          # the last version if several (…_v2 sorts after)
        else:
            missing.append(f'{did}_n{src}')
    if missing:
        sys.exit(f'batch {name}: missing drawings {missing}')
    fs, grade_at, wb_same, wb_from, glow = {}, {}, [], {}, {}
    for did, src, ns, kind, ex in table:
        for n in ns:
            if kind in ('single', 'loop'):
                e = {'drawing': path[did], 'id': did}
            elif kind == 'chain':
                cname, cref, cam = ex['chain']
                base = next(t[0] for t in table if t[4].get('chain', (None,))[0] == cname)
                e = {'hold': cname, 'id': did, 'mode': 'full', 'full': path[did], 'ref': cref}
                if did != base:
                    e['register_with'] = path[base]
                if cam == 'none':
                    e.update(camera_only='none', zoom=1.0, light='fixed')
            else:
                e = {'hold': did, 'id': did, 'mode': 'full', 'full': path[did], 'ref': src}
                if kind in ('views', 'still'):
                    e.update(camera_only='none', zoom=1.0, light='fixed')
            if n in ex.get('wash', []):
                e['white_wash'] = {'sigma': 40}
            fs[str(n)] = e
        if kind == 'views' and len(ns) > 1:
            other = [n for n in ns if n != src]
            grade_at[did] = [src, other[0]]
            wb_same.append(did)
            glow[did] = [0.55, 0.85]
        if ex.get('grade_at'):
            grade_at[did] = ex['grade_at']
        if ex.get('wb_from'):
            wb_from[did] = ex['wb_from']
    for n, what in flat.items():
        fs[str(n)] = {what: True, 'id': what}
    ids = [t[0] for t in table]
    sheet = {'name': f'batch {name} {frames}: 051 drawing table', 'frames': frames,
             'state_label': 'generated/edited picture states (character, effect and background views)',
             'grade': {'strength': 1.0, 'sigma': 4.0, 'modes': {i: 'luma' for i in ids}, 'white_protect': [0.85, 0.97],
                       'grade_at': grade_at, 'wb_same': wb_same, 'wb_from': wb_from, 'glow_hold': glow},
             'encode': {'sws_flags': 'accurate_rnd+full_chroma_int'},
             'frames_sheet': {k: fs[k] for k in sorted(fs, key=int)}}
    missing_frames = [n for n in range(*frames) if str(n) not in fs]
    if missing_frames:
        sys.exit(f'batch {name}: frames without an entry {missing_frames}')
    json.dump(sheet, open(os.path.join(ROOT, out), 'w'), indent=1, ensure_ascii=False)
    print(f'{out}: {len(fs)} frames, {len(ids)} drawings')


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'A'
    d, out = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else (None, None)     # a test directory / sheet path
    if which == 'A':
        build('A', A, A_FLAT, [1202, 1248], out or 'anime/sheets/batchA_1202_1248.json', d)
    else:
        build('B', B, B_FLAT, [1293, 1357], out or 'anime/sheets/batchB_1293_1357.json', d)
