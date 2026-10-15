def tpt(occ, p_mm):
    """Transform a component-space point (x,y,z mm) by the occurrence's current transform -> global mm."""
    m = occ.transform2 if hasattr(occ, 'transform2') else occ.transform
    pt = P3(p_mm[0] * CM, p_mm[1] * CM, p_mm[2] * CM)
    pt.transformBy(m)
    return (round(pt.x / CM, 3), round(pt.y / CM, 3), round(pt.z / CM, 3))


def snapshot():
    o = occ_of
    return {
        'crank_C': tpt(o('Crank'), (0, *D.c_at(0))),
        'rod_K': tpt(o('Rod'), (0, *D.K0)),
        'IK_L_P2': tpt(o('InnerKnuckle'), (0, *D.P2)),
        'IK_R_P2': tpt(o('InnerKnuckle', 1), (0, *D.P2)),
        'OK_L_J': tpt(o('OuterKnuckle_L'), (0, *D.J)),
        'OK_R_J': tpt(o('OuterKnuckle_R'), (0, *D.J)),
        'IF_L_P1': tpt(o('InnerFinger'), (0, *D.P1)),
        'IF_R_P1': tpt(o('InnerFinger', 1), (0, *D.P1)),
    }


MOVING = ['Rod', 'Crank', 'ServoHorn_Ref', 'OuterKnuckle_L', 'OuterKnuckle_R', 'OuterFinger', 'InnerFinger', 'Fingertip', 'InnerKnuckle']


def reset_pose():
    rz = adsk.core.Matrix3D.create()
    rz.setToRotation(math.pi, adsk.core.Vector3D.create(0, 0, 1), P3(0, 0, 0))
    for o in root.occurrences:
        base = o.component.name
        if base not in MOVING:
            continue
        mirrored = o.transform2.getCell(0, 0) < 0
        o.transform2 = rz.copy() if mirrored else adsk.core.Matrix3D.create()
    adsk.doEvents()


def drive_servo(target, step=0.02):
    """Move the servo joint in small steps (keeps the four-bar on its assembly branch)."""
    j = joint_by_name('Servo_Horn')
    v = j.jointMotion.rotationValue
    if v > math.pi:
        v -= 2 * math.pi
    n = max(1, int(abs(target - v) / step + 0.999))
    for i in range(1, n + 1):
        j.jointMotion.rotationValue = v + (target - v) * i / n
        adsk.doEvents()
    r = j.jointMotion.rotationValue
    return r - 2 * math.pi if r > math.pi else r


def q_now():
    v = jval('Pivot_I_L')
    v = v - 2 * math.pi if v > math.pi else v
    return v   # left joints have axis -X: positive = clockwise = closing
