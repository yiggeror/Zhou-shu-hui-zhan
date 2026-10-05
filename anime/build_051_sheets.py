"""Exposure sheets for the batches written up front for Limo: A [1202,1248) and B [1293,1357) (collab/to_limo/051),
C1 [1357,1411) and C2 [1411,1485) (collab/to_limo/057), from the drawings Limo delivers as
collab/from_limo/<msg>/batch<name>*/<ID>_n<source>.png.  Usage: python3 anime/build_051_sheets.py A|B|C1|C2"""
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

# batch C1: shots 50-54 [1357,1411) (collab/to_limo/057)
C1 = [
    ('G1', 1357, [1357], 'single', {}),
    ('G2', 1358, [1358], 'single', {}),
    ('G3', 1359, [1359], 'single', {}),
    ('G4', 1360, [1360], 'single', {}),
    ('G5', 1361, [1361, 1362], 'views', {}),
    ('G6', 1364, [1363, 1364, 1365, 1366], 'hold', {}),
    ('Y1', 1368, [1367, 1368, 1369, 1370, 1371], 'hold', {}),
    ('Y2', 1372, [1372], 'single', {}),
    ('F1', 1373, [1373], 'single', {}),
    ('U1', 1374, [1374, 1375], 'views', {}),
    ('U2', 1376, [1376, 1377], 'views', {}),
    ('U3', 1378, [1378, 1379], 'views', {}),
    ('U4', 1380, [1380], 'single', {}),
    ('V1', 1381, [1381], 'single', {}),
    ('V2', 1382, [1382], 'single', {}),
    ('V3', 1383, [1383], 'single', {}),
    ('V4', 1384, [1384], 'single', {}),
    ('D1', 1385, [1385, 1386], 'views', {}),
    ('V5', 1387, [1387], 'single', {}),
    ('V6', 1388, [1388], 'single', {}),
    ('U5', 1389, [1389, 1390], 'views', {}),
    ('U6', 1391, [1391], 'single', {}),
    ('M1', 1392, [1392], 'single', {}),
    ('M2', 1393, [1393], 'single', {}),
    ('M3', 1394, [1394, 1395], 'views', {}),
    ('M4', 1396, [1396, 1397], 'views', {}),
    ('M5', 1398, [1398], 'single', {}),
    ('M6', 1399, [1399], 'single', {}),
    ('M7', 1400, [1400], 'single', {}),
    ('N1', 1401, [1401], 'single', {}),
    ('N2', 1402, [1402], 'single', {}),
    ('N3', 1403, [1403, 1404], 'views', {}),
    ('N4', 1405, [1405, 1406], 'views', {}),
    ('N5', 1407, [1407, 1408], 'views', {}),
    ('N6', 1409, [1409, 1410], 'views', {}),
]
C1_FLAT = {}

# batch C2: shots 55-57 [1411,1485) (collab/to_limo/057)
C2 = [
    ('P1', 1411, [1411], 'single', {}),
    ('P2', 1412, [1412], 'single', {}),
] + [(f'P{i}', n, [n, n + 1], 'views', {}) for i, n in zip(range(3, 12), range(1413, 1431, 2))] + [
    ('Q1', 1431, [1431, 1432], 'views', {}),
    ('Q2', 1433, [1433, 1434], 'views', {}),
    ('Q3', 1435, [1435], 'single', {}),
    ('Q4', 1436, [1436], 'single', {}),
    ('Q5', 1437, [1437], 'single', {}),
    ('Q6', 1438, [1438], 'single', {}),
    # 1439-1452 the original pushes in ~25 %: three drawings of the same pose, each framed on the WIDEST frame of its
    # exposures, so the measured push only enlarges (no edge fill) and by at most ~10 %
    ('Q7a', 1439, [1439, 1440], 'hold', {}),
    ('Q7a2', 1441, [1441], 'single', {}),       # the push is steepest here (1439 -> 1441 ~16 %)
    ('Q7b', 1442, [1442, 1443, 1444, 1445], 'hold', {}),
    ('Q8', 1446, list(range(1446, 1453)), 'hold', {}),
    ('W0', 1453, [1453], 'single', {}),
    ('T1', 1454, [1454, 1455], 'views', {}),
    ('T2', 1456, [1456, 1457], 'views', {}),
] + [(f'L{i}', n, [n, n + 1], 'chain', {'chain': ('L', 1458, 'none')} if i == 1 else
      {'chain': ('L', 1458, 'none'), 'wb_from': 'L1'}) for i, n in zip(range(1, 8), range(1458, 1472, 2))] + [
    ('L8', 1472, [1472, 1473, 1474], 'chain', {'chain': ('L', 1458, 'none'), 'wb_from': 'L1'}),
    ('B1', 1475, [1475], 'single', {}),
    ('B2', 1476, [1476], 'single', {}),
    ('B3', 1477, [1477], 'single', {}),
    ('R1', 1478, [1478], 'single', {}),
    ('R2', 1479, [1479], 'single', {}),
    ('R3', 1480, [1480, 1481], 'views', {}),
    ('R4', 1482, [1482], 'single', {}),
    ('Z1', 1484, [1484], 'single', {}),
]
C2_FLAT = {1483: 'black'}

def b45():
    """batch B as locked by Limo (from_limo/051/msg_008, B45_exposure_table_001.csv): 45 states, each in its own
    source geometry; holds are discrete (no camera: Limo found the earlier 5 deg fit to be figure motion, not camera)"""
    import csv
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'collab/from_limo/051/B45_exposure_table_001.csv'),
                                    encoding='utf-8-sig')))
    out = []
    for r in rows:
        src, a, b = int(r['source_n']), int(r['start']), int(r['end'])
        ns = list(range(a, b))
        out.append((r['id'], src, ns, 'single' if len(ns) == 1 else 'still', {} if len(ns) == 1 else
                    {'grade_at': [src, src]}))
    return out


def from_csv(path):
    """a batch as locked by Limo in an exposure table (id, source_n, start, end): every state in its own source
    geometry; holds are discrete (no camera), graded at their source frame"""
    import csv
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, path), encoding='utf-8-sig')):
        src, a, b = int(r['source_n']), int(r['start']), int(r['end'])
        ns = list(range(a, b))
        out.append((r['id'], src, ns, 'single' if len(ns) == 1 else 'still', {} if len(ns) == 1 else
                    {'grade_at': [src, src]}))
    return out


BATCHES = {'A': (A, A_FLAT, [1202, 1248], '051', 'anime/sheets/batchA_1202_1248.json'),
           'B': (None, {1319: 'black'}, [1293, 1357], '051', 'anime/sheets/batchB_1293_1357.json'),
           'C1': (C1, C1_FLAT, [1357, 1411], '057', 'anime/sheets/batchC1_1357_1411.json'),
           'C2': (C2, C2_FLAT, [1411, 1485], '057', 'anime/sheets/batchC2_1411_1485.json')}


def build(name, table, flat, frames, out, d=None, msg='051'):
    d = d or os.path.join('collab', 'from_limo', msg, f'batch{name}')
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
                e['white_wash'] = {'sigma': 40, 'color': 'source', 'lo': 0.45, 'hi': 0.90, 'blend': 'screen', 'veil_max': 0.6}
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
                       'grade_at': grade_at, 'wb_same': wb_same, 'wb_from': wb_from, 'glow_hold': glow,
                       **({} if name == 'A' else {'keep_highlights': [0.7, 0.9]})},
             'encode': {'sws_flags': 'accurate_rnd+full_chroma_int'},
             **({} if name == 'A' else {'keep_highlights_note': 'msg_008: enhanced glows kept as drawn'}),
             'frames_sheet': {k: fs[k] for k in sorted(fs, key=int)}}
    missing_frames = [n for n in range(*frames) if str(n) not in fs]
    if missing_frames:
        sys.exit(f'batch {name}: frames without an entry {missing_frames}')
    json.dump(sheet, open(os.path.join(ROOT, out), 'w'), indent=1, ensure_ascii=False)
    print(f'{out}: {len(fs)} frames, {len(ids)} drawings')


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'A'
    d, out = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else (None, None)     # a test directory / sheet path
    table, flat, frames, msg, default_out = BATCHES[which]
    if which == 'B':
        table = b45()
    elif which == 'C1' and os.path.exists(os.path.join(ROOT, 'collab/from_limo/057/C1_43_exposure_table_001.csv')):
        table = from_csv('collab/from_limo/057/C1_43_exposure_table_001.csv')    # Limo's lock, 057/msg_001
    build(which, table, flat, frames, out or default_out, d, msg)
