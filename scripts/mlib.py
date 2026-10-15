"""Geometry + LEGO-style renderer for the HomeMade2F140 assembly manual."""
import math, os, struct
import numpy as np
import design as D
import parts as P

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')

RZ = np.diag([-1.0, -1.0, 1.0])   # 180 deg about Z (right-side twins)

COL = {
    'Tower': (0.66, 0.67, 0.70), 'Box': (0.66, 0.67, 0.70), 'OK': (0.98, 0.76, 0.12), 'OF': (0.22, 0.38, 0.78),
    'IK': (0.20, 0.62, 0.32), 'IF': (0.22, 0.38, 0.78), 'FT': (0.17, 0.17, 0.19), 'Crank': (0.86, 0.20, 0.15),
    'Rod': (0.86, 0.20, 0.15), 'SpA': (0.93, 0.93, 0.90), 'SpB': (0.93, 0.93, 0.90), 'Cam': (0.98, 0.58, 0.14),
    'Servo': (0.13, 0.13, 0.14), 'Horn': (0.30, 0.48, 0.90), 'D435': (0.34, 0.34, 0.37), 'Flange': (0.48, 0.49, 0.52),
    'bolt': (0.74, 0.75, 0.78), 'nut': (0.58, 0.60, 0.64), 'washer': (0.86, 0.87, 0.90),
}


# ---------------------------------------------------------------- meshes
def load_stl(name):
    d = open(os.path.join(RAW, name + '.stl'), 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return a['v'].reshape(-1, 3, 3).astype(float)


def _frame(axis):
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    t = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(a, t); u /= np.linalg.norm(u)
    v = np.cross(a, u)
    return a, u, v


def cylinder(p0, p1, r, n=28, r_in=0.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    a, u, v = _frame(p1 - p0)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v
    o0, o1 = p0 + r * ring, p1 + r * ring
    T = []
    for i in range(n):
        j = (i + 1) % n
        T += [(o0[i], o0[j], o1[j]), (o0[i], o1[j], o1[i])]
        if r_in > 0:
            i0, i1 = p0 + r_in * ring, p1 + r_in * ring
            T += [(i0[j], i0[i], i1[i]), (i0[j], i1[i], i1[j])]
            T += [(o0[j], o0[i], i0[i]), (o0[j], i0[i], i0[j]), (o1[i], o1[j], i1[j]), (o1[i], i1[j], i1[i])]
        else:
            T += [(p0, o0[j], o0[i]), (p1, o1[i], o1[j])]
    return np.array(T)


def hexprism(p0, p1, af, ang0=0.0, r_in=0.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    a, u, v = _frame(p1 - p0)
    R = af / math.sqrt(3)
    ang = ang0 + np.pi / 6 + np.arange(6) * np.pi / 3
    ring = np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v
    o0, o1 = p0 + R * ring, p1 + R * ring
    T = []
    for i in range(6):
        j = (i + 1) % 6
        T += [(o0[i], o0[j], o1[j]), (o0[i], o1[j], o1[i]), (p0, o0[j], o0[i]), (p1, o1[i], o1[j])]
    T = np.array(T)
    if r_in > 0:   # dark hole disc on both faces (visual only)
        pass
    return T


def bolt_mesh(head_c, axis, head_d, head_h, shank_d, length):
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    hb = np.asarray(head_c, float)                   # head bottom (contact face) centre
    head = cylinder(hb - a * head_h, hb, head_d / 2)
    sock = cylinder(hb - a * (head_h + 0.05), hb - a * (head_h * 0.45), head_d * 0.22, n=6)
    shank = cylinder(hb, hb + a * length, shank_d / 2, n=20)
    return np.concatenate([head, shank]), sock


# ---------------------------------------------------------------- assembly items
class Item:
    def __init__(self, key, tris, kind, label, group='static', color=None, extra=None):
        self.key, self.tris, self.kind, self.label, self.group = key, tris, kind, label, group
        self.color = color or COL.get(kind, (0.7, 0.7, 0.7))
        self.extra = extra       # optional dark socket mesh
        self.anchor = tris.reshape(-1, 3).mean(0)
        self.axis = None


def _pt(axis, c, v):
    if axis == 'x':
        return np.array([v, c[0], c[1]])
    if axis == 'z':
        return np.array([c[0], c[1], v])
    return np.array([c[0], v, c[1]])


def hw_items(entry, mirror, group):
    """Split one modelled fastener stack into bolt / nut / washer items (world coords at q = 0)."""
    ax, c, segs = entry['axis'], entry['c'], entry['segs']
    name = entry['name'] + ('_R' if mirror else '')
    size = entry['name'].split('_')[1]                       # e.g. M3x30
    head = segs[0]
    rest = segs[1:]
    shank = min([s for s in rest if s[2][0] == 'circle'], key=lambda s: s[2][1])
    hc = (head[0] + head[1]) / 2
    sc = (shank[0] + shank[1]) / 2
    sgn = 1.0 if sc > hc else -1.0
    unit = {'x': np.array([1.0, 0, 0]), 'y': np.array([0, 1.0, 0]), 'z': np.array([0, 0, 1.0])}[ax] * sgn
    head_bottom = head[1] if sgn > 0 else head[0]
    tip = shank[1] if sgn > 0 else shank[0]
    L = abs(tip - head_bottom)
    hd = head[2][1] * 2
    shd = shank[2][1] * 2
    M = RZ if mirror else np.eye(3)
    out = []
    tr, sock = bolt_mesh(_pt(ax, c, head_bottom), unit, hd, abs(head[1] - head[0]), shd, L)
    it = Item(f'{name}:bolt', tr @ M.T, 'bolt', size, group, extra=sock @ M.T)
    it.axis = unit @ M.T
    it.entry = (_pt(ax, c, head_bottom)) @ M.T        # where the shank enters
    it.tipw = _pt(ax, c, tip) @ M.T
    out.append(it)
    k_n = k_w = 0
    for s in rest:
        if s is shank:
            continue
        g = s[2]
        p0, p1 = _pt(ax, c, s[0]), _pt(ax, c, s[1])
        mid = (s[0] + s[1]) / 2
        side = 1.0 if (mid - (head_bottom + tip) / 2) * sgn > 0 else -1.0
        if g[0] == 'circle' and abs(s[1] - s[0]) <= 0.6 + 1e-6:
            t = max(abs(s[1] - s[0]), 0.8)
            m = (p0 + p1) / 2
            tri = cylinder(m - unit * t / 2, m + unit * t / 2, g[1], r_in=1.65)
            it = Item(f'{name}:w{k_n + k_w}', tri @ M.T, 'washer', 'Arandela M3', group)
            k_w += 1
        else:
            af = g[1] if g[0] == 'hex' else D.NUT_AF
            ang = g[2] if (g[0] == 'hex' and len(g) > 2) else 0.0
            tri = hexprism(p0, p1, af, ang)
            it = Item(f'{name}:nut{k_n}', tri @ M.T, 'nut', 'Tuerca M3 nyloc', group)
            k_n += 1
        it.axis = unit @ M.T
        it.side = side
        out.append(it)
    return out


def head_washer(entry, mirror, group):
    """Extra washer under a head that sits on plastic (not in the CAD stack)."""
    ax, c, segs = entry['axis'], entry['c'], entry['segs']
    head = segs[0]
    shank = min([s for s in segs[1:] if s[2][0] == 'circle'], key=lambda s: s[2][1])
    sgn = 1.0 if (shank[0] + shank[1]) > (head[0] + head[1]) else -1.0
    unit = {'x': np.array([1.0, 0, 0]), 'y': np.array([0, 1.0, 0]), 'z': np.array([0, 0, 1.0])}[ax] * sgn
    hb = _pt(ax, c, head[1] if sgn > 0 else head[0])
    tri = cylinder(hb - unit * 0.8, hb, 3.5, r_in=1.65)
    M = RZ if mirror else np.eye(3)
    it = Item(entry['name'] + ('_R' if mirror else '') + ':hw', tri @ M.T, 'washer', 'Arandela M3', group)
    it.axis = unit @ M.T
    it.side = -1.0
    return it


def build_items():
    I = {}

    def add(key, stl, kind, label, group, mirror=False):
        t = load_stl(stl)
        if mirror:
            t = t @ RZ.T
        I[key] = Item(key, t, kind, label, group)

    add('Tower', 'Tower', 'Tower', 'Torre', 'static')
    add('Box', 'HousingBox', 'Box', 'Caja', 'static')
    add('SpA', 'SpacerA', 'SpA', 'Espaciador A', 'static')
    add('SpB', 'SpacerB', 'SpB', 'Espaciador B', 'static')
    add('Cam', 'CameraMount', 'Cam', 'Camera mount', 'static')
    add('D435', 'RealSense_D435i_Ref', 'D435', 'RealSense D435i', 'static')
    add('Servo', 'Servo_D5545GS', 'Servo', 'Servo D5545GS', 'static')
    add('Horn', 'ServoHorn_Ref', 'Horn', 'Horn metalico', 'crank')
    add('Crank', 'Crank', 'Crank', 'Manivela', 'crank')
    add('Rod', 'Rod', 'Rod', 'Biela', 'rod')
    add('OK_L', 'OuterKnuckle_L', 'OK', 'OuterKnuckle_L', 'OK_L')
    add('OK_R', 'OuterKnuckle_R', 'OK', 'OuterKnuckle_R', 'OK_R', mirror=True)
    for side, m in (('L', False), ('R', True)):
        add(f'OF_{side}', 'OuterFinger', 'OF', 'OuterFinger', f'OK_{side}', m)
        add(f'IK_{side}', 'InnerKnuckle', 'IK', 'InnerKnuckle', f'IK_{side}', m)
        add(f'IF_{side}', 'InnerFinger', 'IF', 'InnerFinger', f'IF_{side}', m)
        add(f'FT_{side}', 'Fingertip', 'FT', 'Fingertip', f'IF_{side}', m)
    # robot flange stand-in
    fl = np.concatenate([cylinder((0, 0, -100), (0, 0, D.STACK['flange'] - 6.5), 31.5, n=64),
                         cylinder((0, 0, -130), (0, 0, -100), 37.5, n=64)])
    I['Flange'] = Item('Flange', fl, 'Flange', 'Brida UR10e', 'static')
    # hardware
    carrier_group = {'Tower': 'static', 'HousingBox': 'static', 'SpacerB': 'static', 'CameraMount': 'static',
                     'Rod': 'rod', 'Crank': 'crank', 'OuterFinger': 'OK', 'InnerFinger': 'IF'}
    twin = {'OuterFinger', 'InnerFinger'}
    for e in P.HW_CAD:
        sides = [(False, '_L'), (True, '_R')] if e['carrier'] in twin else [(False, '')]
        for mirror, sfx in sides:
            g = carrier_group[e['carrier']]
            g = g + sfx if g in ('OK', 'IF') else g
            for it in hw_items(e, mirror, g):
                I[it.key] = it
            if any(t in e['name'] for t in ('Tower', 'Base', 'Pad')):
                hw = head_washer(e, mirror, g)
                I[hw.key] = hw
    # the rod-ear nut is captive in the left inner knuckle
    I['HW_M3x12_PinK:nut0'].group = 'IK_L'
    return I


# ---------------------------------------------------------------- posing (finger_joint q)
def _rx(a, p0):
    c, s = math.cos(a), math.sin(a)
    R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    p0 = np.array([0.0, p0[0], p0[1]])
    return R, p0 - R @ p0


def group_tf(group, q):
    if group == 'static':
        return np.eye(3), np.zeros(3)
    if group in ('OK_L', 'OK_R'):
        return _rx(-q, D.O) if group == 'OK_L' else _rx(q, (-D.O[0], D.O[1]))
    if group in ('IK_L', 'IK_R'):
        return _rx(-q, D.I) if group == 'IK_L' else _rx(q, (-D.I[0], D.I[1]))
    if group in ('IF_L', 'IF_R'):
        d = np.subtract(D.p1_at(q), D.P1)
        return np.eye(3), np.array([0.0, d[0] if group == 'IF_L' else -d[0], d[1]])
    if group == 'crank':
        return _rx(D.crank_angle(q) - D.crank_angle(0), D.S)
    if group == 'rod':
        c0, k0, c1, k1 = D.c_at(0), D.K0, D.c_at(q), D.k_at(q)
        a = math.atan2(k1[1] - c1[1], k1[0] - c1[0]) - math.atan2(k0[1] - c0[1], k0[0] - c0[0])
        R, t = _rx(a, c0)
        return R, t + np.array([0.0, c1[0] - c0[0], c1[1] - c0[1]])
    raise ValueError(group)


# ---------------------------------------------------------------- renderer
def view_matrix(az, el):
    az, el = math.radians(az), math.radians(el)
    z = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    up = np.array([0, 0, 1.0])
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z])


class Camera:
    def __init__(self, az, el, W, H, fit_pts, margin=0.06, ss=2):
        self.R = view_matrix(az, el)
        self.W, self.H, self.ss = W, H, ss
        p = np.asarray(fit_pts) @ self.R.T
        lo, hi = p[:, :2].min(0), p[:, :2].max(0)
        span = np.maximum(hi - lo, 1e-6)
        self.scale = min(W * (1 - 2 * margin) / span[0], H * (1 - 2 * margin) / span[1])
        self.c = (lo + hi) / 2

    def project(self, P):
        """world (N,3) -> final-image pixel coords (x right, y down) and depth."""
        p = np.asarray(P, float) @ self.R.T
        x = (p[..., 0] - self.c[0]) * self.scale + self.W / 2
        y = self.H / 2 - (p[..., 1] - self.c[1]) * self.scale
        return np.stack([x, y], -1), p[..., 2]


LIGHT = np.array([-0.35, 0.55, 0.76]); LIGHT /= np.linalg.norm(LIGHT)


def render(scene, cam, line=(0.08, 0.08, 0.10), bg=(1, 1, 1)):
    """scene: list of (tris (N,3,3) world, rgb). Returns HxWx3 float image."""
    ss = cam.ss
    W, H = cam.W * ss, cam.H * ss
    zb = np.full((H, W), -1e30, dtype=np.float32)
    ib = np.full((H, W), -1, dtype=np.int16)
    cb = np.empty((H, W, 3), dtype=np.uint8)
    cb[:] = (np.array(bg) * 255).astype(np.uint8)
    nb = np.zeros((H, W, 3), dtype=np.int8)        # normals x 127
    for oid, (tris, rgb) in enumerate(scene):
        if tris is None or len(tris) == 0:
            continue
        pc = tris.reshape(-1, 3) @ cam.R.T
        X = ((pc[:, 0] - cam.c[0]) * cam.scale + cam.W / 2) * ss
        Y = (cam.H / 2 - (pc[:, 1] - cam.c[1]) * cam.scale) * ss
        Z = pc[:, 2]
        X, Y, Z = X.reshape(-1, 3), Y.reshape(-1, 3), Z.reshape(-1, 3)
        n = np.cross(pc.reshape(-1, 3, 3)[:, 1] - pc.reshape(-1, 3, 3)[:, 0], pc.reshape(-1, 3, 3)[:, 2] - pc.reshape(-1, 3, 3)[:, 0])
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        ok = ln[:, 0] > 1e-12
        n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 1e-12)
        n[n[:, 2] < 0] *= -1
        shade = 0.60 + 0.40 * np.clip(n @ LIGHT, 0, 1)
        col = (np.clip(np.outer(shade, rgb), 0, 1) * 255).astype(np.uint8)
        n8 = np.round(n * 127).astype(np.int8)
        for t in np.nonzero(ok)[0]:
            x0, x1, x2 = X[t]; y0, y1, y2 = Y[t]
            xmin = max(int(math.floor(min(x0, x1, x2))), 0); xmax = min(int(math.ceil(max(x0, x1, x2))), W - 1)
            ymin = max(int(math.floor(min(y0, y1, y2))), 0); ymax = min(int(math.ceil(max(y0, y1, y2))), H - 1)
            if xmax < xmin or ymax < ymin:
                continue
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9:
                continue
            xs = np.arange(xmin, xmax + 1) + 0.5
            ys = np.arange(ymin, ymax + 1)[:, None] + 0.5
            w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
            w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
            w2 = 1 - w0 - w1
            ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not ins.any():
                continue
            z = w0 * Z[t, 0] + w1 * Z[t, 1] + w2 * Z[t, 2]
            sub = zb[ymin:ymax + 1, xmin:xmax + 1]
            m = ins & (z > sub)
            if not m.any():
                continue
            sub[m] = z[m]
            ib[ymin:ymax + 1, xmin:xmax + 1][m] = oid
            cb[ymin:ymax + 1, xmin:xmax + 1][m] = col[t]
            nb[ymin:ymax + 1, xmin:xmax + 1][m] = n8[t]
    # outlines: object boundaries, creases, depth jumps (row bands to keep memory low)
    e = np.zeros((H, W), bool)
    thr = int(127 * 127 * math.cos(math.radians(28)))
    band = 256
    for y0 in range(0, H, band):
        y1 = min(H, y0 + band + 1)
        I_ = ib[y0:y1]; N_ = nb[y0:y1].astype(np.int32); Z_ = zb[y0:y1]
        for dy, dx in ((0, 1), (1, 0)):
            hh, ww = I_.shape[0] - dy, I_.shape[1] - dx
            if hh <= 0:
                continue
            a_id = I_[:hh, :ww]; b_id = I_[dy:dy + hh, dx:dx + ww]
            diff = a_id != b_id
            same = (~diff) & (a_id >= 0)
            crease = same & ((N_[:hh, :ww] * N_[dy:dy + hh, dx:dx + ww]).sum(-1) < thr)
            dz = same & (np.abs(Z_[:hh, :ww] - Z_[dy:dy + hh, dx:dx + ww]) > 2.5)
            e[y0:y0 + hh, :ww] |= diff | crease | dz
    del nb, zb, ib
    k = max(1, ss)
    ee = e.copy()
    for s in range(1, k):
        ee[s:, :] |= e[:-s, :]; ee[:, s:] |= e[:, :-s]
    cb[ee] = (np.array(line) * 255).astype(np.uint8)
    img = cb.reshape(cam.H, ss, cam.W, ss, 3).mean((1, 3), dtype=np.float32) / 255.0
    return img
