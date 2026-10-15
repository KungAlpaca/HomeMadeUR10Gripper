"""Fusion builder for HomeMade2F140 v2. Executed inside Fusion through the MCP add-in (execute_code).

Usage from a call:   exec(open(FBUILD).read()); build_part('Rod')
Every call re-imports design/parts so edits on disk are picked up.
`python fx.py file scripts/<x>.py` sets HM_SCRIPTS (this folder) automatically.
"""
import adsk.core, adsk.fusion, math, sys, importlib, traceback, time

SCR = globals().get('HM_SCRIPTS')
if not SCR:
    raise RuntimeError("Set HM_SCRIPTS to this repository's scripts folder (fx.py 'file' mode sets it automatically)")
if SCR not in sys.path:
    sys.path.insert(0, SCR)
import design as _design, parts as _parts
importlib.reload(_design); importlib.reload(_parts)
D, PP = _design, _parts

DOC_NAME = 'HomeMade2F140_v2'
app = adsk.core.Application.get()
_doc = [d for d in app.documents if d.name == DOC_NAME]
assert _doc, 'v2 document not open'
if app.activeDocument.name != DOC_NAME:
    _doc[0].activate()
des = adsk.fusion.Design.cast(_doc[0].products.itemByProductType('DesignProductType'))
root = des.rootComponent
P3 = adsk.core.Point3D.create
VI = adsk.core.ValueInput.createByReal
CM = 0.1
FO = adsk.fusion.FeatureOperations


# ------------------------------------------------------------------ components
def occ_of(name, idx=0):
    occs = [o for o in root.occurrences if o.component.name in (name, name + ' (1)')]
    return occs[idx] if len(occs) > idx else None


def rz180():
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.pi, adsk.core.Vector3D.create(0, 0, 1), P3(0, 0, 0))
    return m


def get_comp(name, create=True, mirrored=False):
    o = occ_of(name)
    if o:
        return o.component, o
    if not create:
        return None, None
    o = root.occurrences.addNewComponent(rz180() if mirrored else adsk.core.Matrix3D.create())
    o.component.name = name
    return o.component, o


def add_twin(name):
    """Right-side instance: 180 deg about Z."""
    if occ_of(name, 1):
        return occ_of(name, 1)
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.pi, adsk.core.Vector3D.create(0, 0, 1), P3(0, 0, 0))
    return root.occurrences.addExistingComponent(occ_of(name).component, m)


# ------------------------------------------------------------------ sketch helpers
_PL = {}


def plane(comp, axis, off):
    key = (comp.name, axis, round(off, 4))
    if key in _PL and _PL[key].isValid:
        return _PL[key]
    base = {'x': comp.yZConstructionPlane, 'y': comp.xZConstructionPlane, 'z': comp.xYConstructionPlane}[axis]
    if abs(off) < 1e-9:
        _PL[key] = base
        return base
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, VI(off * CM))
    pl = comp.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    pl.name = f'{axis}{off:+.2f}'
    _PL[key] = pl
    return pl


class SK:
    def __init__(self, comp, axis, off, name):
        self.axis, self.off = axis, off
        self.sk = comp.sketches.add(plane(comp, axis, off))
        self.sk.name = name
        self.sk.isComputeDeferred = True
        self.lines = self.sk.sketchCurves.sketchLines
        self.arcs = self.sk.sketchCurves.sketchArcs

    def mp(self, p):
        a, b = p
        if self.axis == 'x':
            q = P3(self.off * CM, a * CM, b * CM)
        elif self.axis == 'z':
            q = P3(a * CM, b * CM, self.off * CM)
        else:
            q = P3(a * CM, self.off * CM, b * CM)
        return self.sk.modelToSketchSpace(q)

    def line(self, p, q):
        if math.dist(p, q) > 1e-4:
            self.lines.addByTwoPoints(self.mp(p), self.mp(q))

    def arc3(self, p, m, q):
        self.arcs.addByThreePoints(self.mp(p), self.mp(m), self.mp(q))

    def circle(self, c, r):
        self.sk.sketchCurves.sketchCircles.addByCenterRadius(self.mp(c), r * CM)

    def poly(self, pts):
        for i in range(len(pts)):
            self.line(pts[i], pts[(i + 1) % len(pts)])

    def arc_ccw(self, c, r, a0, a1):
        sw = (a1 - a0) % (2 * math.pi)
        if sw < 1e-6:
            return
        pm = (c[0] + r * math.cos(a0 + sw / 2), c[1] + r * math.sin(a0 + sw / 2))
        self.arc3((c[0] + r * math.cos(a0), c[1] + r * math.sin(a0)), pm, (c[0] + r * math.cos(a0 + sw), c[1] + r * math.sin(a0 + sw)))

    def fitted(self, pts):
        oc = adsk.core.ObjectCollection.create()
        for p in pts:
            oc.add(self.mp(p))
        self.sk.sketchCurves.sketchFittedSplines.add(oc)

    def done(self):
        self.sk.isComputeDeferred = False
        return self.sk


def hull_sequence(circles):
    """Convex hull of circles -> list of (index) in CCW order (sampling)."""
    pts = []
    for i, (c, r) in enumerate(circles):
        n = 360 if r > 0 else 1
        for k in range(n):
            a = 2 * math.pi * k / n
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), i))
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    seq = []
    for p in h:
        if not seq or seq[-1] != p[2]:
            seq.append(p[2])
    while len(seq) > 1 and seq[0] == seq[-1]:
        seq.pop()
    return seq


def draw_hull(s, circles):
    circles = [((float(c[0]), float(c[1])), float(r)) for c, r in circles]
    seq = hull_sequence(circles)
    if len(seq) == 1:
        c, r = circles[seq[0]]
        s.circle(c, r)
        return
    n = len(seq)
    tang = []  # for edge i (seq[i] -> seq[i+1]): (angle, pt_i, pt_j)
    for i in range(n):
        (ci, ri), (cj, rj) = circles[seq[i]], circles[seq[(i + 1) % n]]
        d = (cj[0] - ci[0], cj[1] - ci[1])
        L = math.hypot(*d)
        phi = math.atan2(d[1], d[0])
        al = math.acos(max(-1.0, min(1.0, (ri - rj) / L)))
        a = phi - al
        tang.append((a, (ci[0] + ri * math.cos(a), ci[1] + ri * math.sin(a)), (cj[0] + rj * math.cos(a), cj[1] + rj * math.sin(a))))
    for i in range(n):
        a, p, q = tang[i]
        s.line(p, q)
        # arc on circle seq[i+1] from this edge's normal to the next edge's normal (CCW)
        c, r = circles[seq[(i + 1) % n]]
        if r > 0:
            s.arc_ccw(c, r, a, tang[(i + 1) % n][0])


def draw_gear(s, phase):
    O = D.O
    a0, a1 = D.GEAR_SECTOR
    a0 += phase * D.GEAR_PITCH
    a1 += phase * D.GEAR_PITCH
    rf, rb = D.GEAR_RF, D.GEAR_RP * math.cos(D.GEAR_PA)

    def pol(r, a):
        return (O[0] + r * math.cos(a), O[1] + r * math.sin(a))
    s.line(O, pol(rf, a0))
    prev = a0
    for k in range(D.GEAR_K[0], D.GEAR_K[1] + 1):
        c = (k + phase) * D.GEAR_PITCH
        right, left = D.gear_tooth_flanks(c)
        ar = math.atan2(right[0][1] - O[1], right[0][0] - O[0])
        al = math.atan2(left[0][1] - O[1], left[0][0] - O[0])
        s.arc_ccw(O, rf, prev, ar)
        if rf < rb:
            s.line(pol(rf, ar), right[0])
        s.fitted(right)
        s.arc3(right[-1], pol(D.GEAR_RA, c), left[-1])
        s.fitted(list(reversed(left)))
        if rf < rb:
            s.line(left[0], pol(rf, al))
        prev = al
    s.arc_ccw(O, rf, prev, a1)
    s.line(pol(rf, a1), O)


def draw(s, shape):
    k = shape[0]
    if k == 'circle':
        s.circle(shape[1], shape[2])
    elif k == 'hull':
        draw_hull(s, shape[1])
    elif k == 'poly':
        s.poly(shape[1])
    elif k == 'rect':
        _, y0, z0, y1, z1 = shape
        s.poly([(y0, z0), (y1, z0), (y1, z1), (y0, z1)])
    elif k == 'hex':
        _, c, af, ang = shape
        R = af / math.sqrt(3)
        s.poly([(c[0] + R * math.cos(ang + math.pi / 6 + i * math.pi / 3), c[1] + R * math.sin(ang + math.pi / 6 + i * math.pi / 3)) for i in range(6)])
    elif k == 'wedge':
        _, c, r, a0, a1 = shape
        p0 = (c[0] + r * math.cos(a0), c[1] + r * math.sin(a0))
        p1 = (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1))
        s.line(c, p0)
        s.arc_ccw(c, r, a0, a1)
        s.line(p1, c)
    elif k == 'kidney':
        _, c, R, a0, a1, hw = shape
        e0 = (c[0] + R * math.cos(a0), c[1] + R * math.sin(a0))
        e1 = (c[0] + R * math.cos(a1), c[1] + R * math.sin(a1))
        s.arc_ccw(c, R + hw, a0, a1)
        s.arc_ccw(e1, hw, a1, a1 + math.pi)
        s.arc3((c[0] + (R - hw) * math.cos(a1), c[1] + (R - hw) * math.sin(a1)),
               (c[0] + (R - hw) * math.cos((a0 + a1) / 2), c[1] + (R - hw) * math.sin((a0 + a1) / 2)),
               (c[0] + (R - hw) * math.cos(a0), c[1] + (R - hw) * math.sin(a0)))
        s.arc_ccw(e0, hw, a0 + math.pi, a0 + 2 * math.pi)
    elif k == 'gear':
        draw_gear(s, shape[1])
    else:
        raise ValueError(k)


AX = {'x': adsk.core.Vector3D.create(1, 0, 0), 'y': adsk.core.Vector3D.create(0, 1, 0), 'z': adsk.core.Vector3D.create(0, 0, 1)}


def extrude(comp, sk, axis, v0, v1, op, body, name):
    profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
    if not profs:
        raise RuntimeError(f'{name}: sketch has no profile')
    prof = max(profs, key=lambda p: p.areaProperties().area)
    m = sk.transform
    nz = adsk.core.Vector3D.create(m.getCell(0, 2), m.getCell(1, 2), m.getCell(2, 2))
    sgn = 1 if nz.dotProduct(AX[axis]) > 0 else -1
    opn = {'new': FO.NewBodyFeatureOperation, 'add': FO.JoinFeatureOperation, 'cut': FO.CutFeatureOperation}[op]
    ei = comp.features.extrudeFeatures.createInput(prof, opn)
    ext = adsk.fusion.DistanceExtentDefinition.create(VI(abs(v1 - v0) * CM))
    ei.setOneSideExtent(ext, adsk.fusion.ExtentDirections.PositiveExtentDirection if sgn > 0 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    if body is not None and op != 'new':
        ei.participantBodies = [body]
    f = comp.features.extrudeFeatures.add(ei)
    f.name = name
    sk.isVisible = False
    return f


def main_body(comp, name):
    for b in comp.bRepBodies:
        if b.name == name:
            return b
    return None


def part_bodies(comp, name):
    return [b for b in comp.bRepBodies if b.name == name or b.name.startswith(name + '_frag')]


def build_features(comp, bname, feats, axis, tag):
    for i, (v0, v1, op, shape) in enumerate(feats):
        bodies = part_bodies(comp, bname)
        if not bodies and op == 'cut':
            continue
        s = SK(comp, axis, v0, f'{tag}{i:02d}_{op}_{shape[0]}')
        draw(s, shape)
        sk = s.done()
        o = 'new' if not bodies and op == 'add' else op
        f = extrude_multi(comp, sk, axis, v0, v1, o, bodies, f'{tag}{i:02d}_{op}_{shape[0]}')
        names = {b.name for b in part_bodies(comp, bname)}
        for j, b in enumerate(f.bodies):
            if b.name not in names and b.name != bname:
                b.name = bname if not part_bodies(comp, bname) else f'{bname}_frag{i}_{j}'
    frags = part_bodies(comp, bname)
    if len(frags) > 1:
        raise RuntimeError(f'{bname}: {len(frags)} disjoint bodies after {tag} features')
    if frags:
        frags[0].name = bname
    return main_body(comp, bname)


def extrude_multi(comp, sk, axis, v0, v1, op, bodies, name):
    profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
    if not profs:
        raise RuntimeError(f'{name}: sketch has no profile')
    prof = max(profs, key=lambda p: p.areaProperties().area)
    m = sk.transform
    nz = adsk.core.Vector3D.create(m.getCell(0, 2), m.getCell(1, 2), m.getCell(2, 2))
    sgn = 1 if nz.dotProduct(AX[axis]) > 0 else -1
    opn = {'new': FO.NewBodyFeatureOperation, 'add': FO.JoinFeatureOperation, 'cut': FO.CutFeatureOperation}[op]
    ei = comp.features.extrudeFeatures.createInput(prof, opn)
    ext = adsk.fusion.DistanceExtentDefinition.create(VI(abs(v1 - v0) * CM))
    ei.setOneSideExtent(ext, adsk.fusion.ExtentDirections.PositiveExtentDirection if sgn > 0 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    if op != 'new':
        ei.participantBodies = list(bodies)
    f = comp.features.extrudeFeatures.add(ei)
    f.name = name
    sk.isVisible = False
    return f


def delete_part(name):
    for o in [o for o in root.occurrences if o.component.name == name]:
        o.deleteMe()
    return name + ' deleted'


def build_part(name, hardware=True):
    t0 = time.time()
    p = PP.PARTS[name]
    comp, occ = get_comp(name, mirrored=bool(p.get('mirror')))
    if comp.bRepBodies.count:
        return f'{name}: already built ({comp.bRepBodies.count} bodies)'
    body = None
    if p.get('feats'):
        body = build_features(comp, name, p['feats'], 'x', 'X')
    if p.get('zfeats'):
        body = build_features(comp, name, p['zfeats'], 'z', 'Z')
    if p.get('yfeats'):
        body = build_features(comp, name, p['yfeats'], 'y', 'Y')
    if comp.name != name:
        comp.name = name
    if p.get('twin'):
        add_twin(name)
    b = main_body(comp, name)
    return f'{name}: solid={b.isSolid if b else None} vol={b.volume * 1000 if b else 0:.0f} mm3  faces={b.faces.count if b else 0}  {time.time() - t0:.1f}s'


# ------------------------------------------------------------------ hardware, appearances, reset
def build_hardware():
    done = []
    for h in PP.HW_CAD:
        comp, occ = get_comp(h['carrier'], create=False)
        if comp is None or main_body(comp, h['name']):
            continue
        body = None
        for i, (v0, v1, shape) in enumerate(h['segs']):
            s = SK(comp, h['axis'], v0, f"{h['name']}_{i}")
            if shape[0] == 'circle':
                s.circle(h['c'], shape[1])
            else:
                draw(s, ('hex', h['c'], shape[1], shape[2] if len(shape) > 2 else 0.0))
            sk = s.done()
            f = extrude_multi(comp, sk, h['axis'], v0, v1, 'new' if body is None else 'add', [body] if body else [], f"{h['name']}_{i}")
            if body is None:
                body = f.bodies.item(0)
                body.name = h['name']
            body = main_body(comp, h['name'])
        done.append(h['name'])
    return len(done)


def appearance(name):
    a = des.appearances.itemByName(name)
    if a:
        return a
    lib = app.materialLibraries.itemByName('Fusion Appearance Library')
    return des.appearances.addByCopy(lib.appearances.itemByName(name), name)


def apply_colors():
    for o in root.occurrences:
        c = o.component
        for b in c.bRepBodies:
            key = 'HW' if b.name.startswith('HW_') else c.name
            if key in PP.COLORS:
                b.appearance = appearance(PP.COLORS[key])


def delete_all():
    for ml in list(root.motionLinks):
        ml.deleteMe()
    for j in list(root.asBuiltJoints):
        j.deleteMe()
    for o in list(root.occurrences):
        o.deleteMe()
    for s in list(root.sketches):
        s.deleteMe()
    return root.occurrences.count, len(list(des.allComponents))


def build_list(names):
    out = []
    for n in names:
        out.append(build_part(n))
    for o in root.occurrences:
        if o.isGroundToParent:
            o.isGroundToParent = False
    return out


def delete_hw(prefixes):
    n = 0
    for o in root.occurrences:
        c = o.component
        for f in list(c.features.extrudeFeatures):
            if any(f.name.startswith(p) for p in prefixes):
                f.deleteMe(); n += 1
        for sk in list(c.sketches):
            if any(sk.name.startswith(p) for p in prefixes):
                sk.deleteMe()
    return n


def append_features(name, which, start):
    """Build PARTS[name][which][start:] on the existing body (additive edits keep component names)."""
    p = PP.PARTS[name]
    comp, occ = get_comp(name, create=False)
    axis = {'feats': 'x', 'zfeats': 'z', 'yfeats': 'y'}[which]
    tag = {'feats': 'X', 'zfeats': 'Z', 'yfeats': 'Y'}[which]
    feats = p[which]
    for i in range(start, len(feats)):
        v0, v1, op, shape = feats[i]
        s = SK(comp, axis, v0, f'{tag}{i:02d}_{op}_{shape[0]}')
        draw(s, shape)
        sk = s.done()
        extrude_multi(comp, sk, axis, v0, v1, op, part_bodies(comp, name), f'{tag}{i:02d}_{op}_{shape[0]}')
    b = main_body(comp, name)
    return f'{name}: vol={b.volume * 1000:.0f}'


def append_list(name, axis, feats, start_index):
    comp, occ = get_comp(name, create=False)
    tag = axis.upper()
    for k, (v0, v1, op, shape) in enumerate(feats):
        i = start_index + k
        s = SK(comp, axis, v0, f'{tag}{i:02d}_{op}_{shape[0]}')
        draw(s, shape)
        sk = s.done()
        extrude_multi(comp, sk, axis, v0, v1, op, part_bodies(comp, name), f'{tag}{i:02d}_{op}_{shape[0]}')
    b = main_body(comp, name)
    return f'{name}: vol={b.volume * 1000:.0f} bodies={len(part_bodies(comp, name))}'
