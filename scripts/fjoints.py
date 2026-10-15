"""Joints for HomeMade2F140 v2 (as-built joints at q = 0). Exec after fbuild.py in the same call."""

GROUNDED = ['Tower', 'HousingBox', 'Servo_D5545GS', 'SpacerB', 'SpacerA', 'CameraMount', 'RealSense_D435i_Ref']


def mirror_yz(p):
    return (-p[0], p[1])


def ref_sketch():
    for s in root.sketches:
        if s.name == 'JointRefs':
            return s
    s = root.sketches.add(root.yZConstructionPlane)
    s.name = 'JointRefs'
    return s


def jcircle(p):
    s = ref_sketch()
    c = s.sketchCurves.sketchCircles.addByCenterRadius(s.modelToSketchSpace(P3(0, p[0] * CM, p[1] * CM)), 0.1)
    s.isVisible = False
    return c


def joint_by_name(n):
    for j in root.asBuiltJoints:
        if j.name == n:
            return j
    return None


def find_circle_edge(occ, p, rmax=4.0):
    """Circular edge of occ (assembly context) whose axis is X and centre is at global YZ p."""
    best = None
    for b in occ.bRepBodies:
        for e in b.edges:
            g = e.geometry
            if g.curveType != adsk.core.Curve3DTypes.Circle3DCurveType:
                continue
            if abs(abs(g.normal.x) - 1) > 1e-6 or g.radius * 10 > rmax:
                continue
            d = math.hypot(g.center.y / CM - p[0], g.center.z / CM - p[1])
            if d < 0.01 and (best is None or g.radius < best[0]):
                best = (g.radius, e)
    return best[1] if best else None


def asbuilt(name, occ1, occ2, p, kind='rev'):
    if joint_by_name(name):
        return joint_by_name(name)
    e = find_circle_edge(occ1, p) or find_circle_edge(occ2, p)
    if e is None:
        raise RuntimeError(f'{name}: no circular edge at {p}')
    g = adsk.fusion.JointGeometry.createByCurve(e, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
    ji = root.asBuiltJoints.createInput(occ1, occ2, g)
    if kind == 'rev':
        ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    else:
        ji.setAsRigidJointMotion()
    j = root.asBuiltJoints.add(ji)
    j.name = name
    return j


def build_joints():
    for n in GROUNDED:
        occ_of(n).isGrounded = True
    o = lambda n, i=0: occ_of(n, i)
    out = []
    out.append(asbuilt('Servo_Horn', o('Crank'), o('Servo_D5545GS'), D.S))
    out.append(asbuilt('Horn_Fix', o('ServoHorn_Ref'), o('Crank'), D.S, 'rigid'))
    out.append(asbuilt('Pin_C', o('Rod'), o('Crank'), D.c_at(0)))
    out.append(asbuilt('Pin_K', o('Rod'), o('InnerKnuckle'), D.K0))
    out.append(asbuilt('Pivot_I_L', o('InnerKnuckle'), o('Tower'), D.I))
    out.append(asbuilt('Pivot_I_R', o('InnerKnuckle', 1), o('Tower'), mirror_yz(D.I)))
    out.append(asbuilt('Pivot_O_L', o('OuterKnuckle_L'), o('Tower'), D.O))
    out.append(asbuilt('Pivot_O_R', o('OuterKnuckle_R'), o('Tower'), mirror_yz(D.O)))
    out.append(asbuilt('Fix_OF_L', o('OuterFinger'), o('OuterKnuckle_L'), D.J, 'rigid'))
    out.append(asbuilt('Fix_OF_R', o('OuterFinger', 1), o('OuterKnuckle_R'), mirror_yz(D.J), 'rigid'))
    out.append(asbuilt('Pivot_P1_L', o('InnerFinger'), o('OuterFinger'), D.P1))
    out.append(asbuilt('Pivot_P1_R', o('InnerFinger', 1), o('OuterFinger', 1), mirror_yz(D.P1)))
    out.append(asbuilt('Fix_Tip_L', o('Fingertip'), o('InnerFinger'), D.P1, 'rigid'))
    out.append(asbuilt('Fix_Tip_R', o('Fingertip', 1), o('InnerFinger', 1), mirror_yz(D.P1), 'rigid'))
    out.append(asbuilt('Pivot_P2_L', o('InnerFinger'), o('InnerKnuckle'), D.P2))
    out.append(asbuilt('Pivot_P2_R', o('InnerFinger', 1), o('InnerKnuckle', 1), mirror_yz(D.P2)))
    res = []
    for j in out:
        rv = getattr(j.jointMotion, 'rotationAxisVector', None)
        res.append((j.name, tuple(round(v, 3) for v in (rv.x, rv.y, rv.z)) if rv else 'rigid'))
    return res


def gear_link(reversed_=True):
    for ml in root.motionLinks:
        if ml.name == 'Gear_Sync':
            ml.deleteMe()
    mi = root.motionLinks.createInput(joint_by_name('Pivot_O_L'), joint_by_name('Pivot_O_R'))
    mi.valueOne = adsk.core.ValueInput.createByString('1 deg')
    mi.valueTwo = adsk.core.ValueInput.createByString('1 deg')
    mi.isReversed = reversed_
    ml = root.motionLinks.add(mi)
    ml.name = 'Gear_Sync'
    return ml


def jval(n):
    return joint_by_name(n).jointMotion.rotationValue


def occ_pos(name, idx, p):
    """Where the (q=0) point p of an occurrence currently is (global YZ, mm)."""
    m = occ_of(name, idx).transform2 if hasattr(occ_of(name, idx), 'transform2') else occ_of(name, idx).transform
    pt = P3(0, p[0] * CM, p[1] * CM) if idx == 0 or name.endswith('_R') else P3(0, -p[0] * CM, p[1] * CM)
    if name.endswith('_R'):
        pt = P3(0, p[0] * CM, p[1] * CM)
    pt.transformBy(m)
    return (round(pt.y / CM, 3), round(pt.z / CM, 3))
