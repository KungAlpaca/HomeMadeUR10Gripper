"""Orient the raw component-space STLs for FDM printing and build the combined print-set STL."""
import json, os, struct, sys
import numpy as np

# usage: python scripts/orient.py scripts/raw print   -> print/parts, print/plates, print/print_report.json
RAW = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'plates'), exist_ok=True)

# part -> (quantity, face to put on the bed as an outward normal in assembly coords, or 'auto_perp_x')
PLAN = {
    'Tower': (1, (0, 0, -1)),
    'HousingBox': (1, (0, 0, -1)),
    'SpacerB': (1, (0, 0, -1)),
    'SpacerA': (1, (0, 0, 1)),        # flipped: Ø25 bore opens upwards
    'CameraMount': (1, (0, 0, 1)),    # flipped: flange pocket and camera counterbores open upwards
    'Crank': (1, (-1, 0, 0)),         # horn face on the bed
    'Rod': (1, (-1, 0, 0)),
    'OuterKnuckle_L': (1, (-1, 0, 0)),
    'OuterKnuckle_R': (1, (-1, 0, 0)),
    'InnerFinger': (2, (-1, 0, 0)),
    'Fingertip': (2, (0, 1, 0)),      # grip face on the bed, nut pockets open upwards
    'OuterFinger': (2, 'of_side'),    # long flat side down: fork slots become vertical, no support
    'InnerKnuckle': (2, 'ik_side'),   # flat side without the ear down
}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math
import design as DD
_d = DD.unit(DD.sub(DD.P2, DD.I))
_pl = (-_d[1], _d[0])
_k = DD.sub(DD.K0, DD.I)
_s = 1 if _k[0] * _pl[0] + _k[1] * _pl[1] > 0 else -1
IK_DOWN = (0.0, -_s * _pl[0], -_s * _pl[1])
_dj = DD.sub(DD.P1, DD.J)
_phi = math.atan2(_dj[1], _dj[0]) + math.acos((7.5 - 6.5) / math.hypot(*_dj))
OF_DOWN = (0.0, math.cos(_phi), math.sin(_phi))


def load(p):
    d = open(p, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return a['v'].reshape(-1, 3, 3).astype(float)


def save(p, tris, name):
    tris = np.asarray(tris, dtype=float)
    nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    rec = np.zeros(len(tris), dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    rec['n'] = nrm
    rec['v'] = tris.reshape(-1, 9)
    hdr = name.encode()[:80].ljust(80, b' ')
    with open(p, 'wb') as f:
        f.write(hdr + struct.pack('<I', len(tris)) + rec.tobytes())


def rot_to(a, b):
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        if c > 0:
            return np.eye(3)
        axis = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
        axis = axis - a * np.dot(axis, a)
        axis /= np.linalg.norm(axis)
        return 2 * np.outer(axis, axis) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def largest_flat_normal_perp_x(t):
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    area = np.linalg.norm(n, axis=1) / 2
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    m = np.abs(n[:, 0]) < 1e-3
    keys = {}
    for nn, aa in zip(np.round(n[m], 3), area[m]):
        k = tuple(nn)
        keys[k] = keys.get(k, 0) + aa
    k = max(keys, key=keys.get)
    return np.array(k), keys[k]


report = {}
pieces = []
for name, (qty, down) in PLAN.items():
    t = load(os.path.join(RAW, name + '.stl'))
    if down == 'ik_side':
        down = IK_DOWN
    elif down == 'of_side':
        down = OF_DOWN
    R = rot_to(down, (0, 0, -1))
    p = t.reshape(-1, 3) @ R.T
    # align the longest planar direction with X
    xy = p[:, :2] - p[:, :2].mean(0)
    w, V = np.linalg.eigh(np.cov(xy.T))
    ax = V[:, np.argmax(w)]
    ang = -np.arctan2(ax[1], ax[0])
    Rz = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
    p = p @ Rz.T
    mn, mx = p.min(0), p.max(0)
    p = p - np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])
    tt = p.reshape(-1, 3, 3)
    # contact area on the bed (facets lying at z ~ 0 facing down)
    zf = (np.abs(tt[:, :, 2]).max(1) < 1e-3)
    contact = float(np.linalg.norm(np.cross(tt[zf, 1] - tt[zf, 0], tt[zf, 2] - tt[zf, 0]), axis=1).sum() / 2)
    vol = float(np.einsum('ij,ij->i', tt[:, 0], np.cross(tt[:, 1], tt[:, 2])).sum() / 6)
    fn = f'HomeMade2F140_{name}_x{qty}.stl'
    save(os.path.join(OUT, 'parts', fn), tt, f'HomeMade2F140 {name} qty {qty} mm print-oriented')
    size = (mx - mn)
    report[name] = dict(file='parts/' + fn, qty=qty, size_mm=[round(float(v), 1) for v in size],
                        volume_cm3=round(vol / 1000, 2), bed_contact_mm2=round(contact, 0))
    for _ in range(qty):
        pieces.append((name, tt))

# shelf packing for the combined print set (8 mm spacing, rows up to 300 mm)
pieces.sort(key=lambda it: -(it[1][:, :, 1].max() - it[1][:, :, 1].min()))
gap, row_w = 8.0, 300.0
x = y = 0.0
row_h = 0.0
out = []
for name, tt in pieces:
    w = tt[:, :, 0].max() - tt[:, :, 0].min()
    h = tt[:, :, 1].max() - tt[:, :, 1].min()
    if x > 0 and x + w > row_w:
        x = 0.0
        y += row_h + gap
        row_h = 0.0
    off = np.array([x - tt[:, :, 0].min(), y - tt[:, :, 1].min(), 0])
    out.append(tt + off)
    x += w + gap
    row_h = max(row_h, h)
allt = np.concatenate(out)
save(os.path.join(OUT, 'plates', 'HomeMade2F140_print_set_17pcs.stl'), allt, 'HomeMade2F140 v2 print set 17 pieces mm')
# plates for a 250 x 250 mm bed (first-fit shelves)
plates, cur, x, y, row_h = [], [], 0.0, 0.0, 0.0
for name, tt in sorted(pieces, key=lambda it: -(it[1][:, :, 1].max() - it[1][:, :, 1].min())):
    w = tt[:, :, 0].max() - tt[:, :, 0].min()
    h = tt[:, :, 1].max() - tt[:, :, 1].min()
    if x > 0 and x + w > 240:
        x, y, row_h = 0.0, y + row_h + gap, 0.0
    if y + h > 240:
        plates.append(cur); cur, x, y, row_h = [], 0.0, 0.0, 0.0
    cur.append((name, tt + np.array([x - tt[:, :, 0].min(), y - tt[:, :, 1].min(), 0])))
    x += w + gap
    row_h = max(row_h, h)
plates.append(cur)
report['_plates'] = []
for i, pl in enumerate(plates, 1):
    fn = f'HomeMade2F140_plate{i}_250x250.stl'
    save(os.path.join(OUT, 'plates', fn), np.concatenate([t for _, t in pl]), f'HomeMade2F140 plate {i}')
    report['_plates'].append(dict(file='plates/' + fn, parts=[n for n, _ in pl]))
report['_print_set'] = dict(file='plates/HomeMade2F140_print_set_17pcs.stl', pieces=len(pieces),
                            extent_mm=[round(float(v), 1) for v in (allt.reshape(-1, 3).max(0) - allt.reshape(-1, 3).min(0))])
json.dump(report, open(os.path.join(OUT, 'print_report.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))
