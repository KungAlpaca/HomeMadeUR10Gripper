import json


def set_limits():
    def lim(n, lo, hi):
        m = joint_by_name(n).jointMotion.rotationLimits
        m.isMinimumValueEnabled = True
        m.minimumValue = lo
        m.isMaximumValueEnabled = True
        m.maximumValue = hi
    s0 = -(D.crank_angle(D.Q_OPEN_STOP) - D.crank_angle(0))
    s1 = -(D.crank_angle(D.Q_CLOSE_STOP) - D.crank_angle(0))
    lim('Servo_Horn', s0, s1)
    for n in ('Pivot_O_L', 'Pivot_O_R'):
        lim(n, D.Q_OPEN_STOP, D.Q_CLOSE_STOP)
    return s0, s1


def interference(include_hw=True):
    bs = adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        for b in o.bRepBodies:
            if not include_hw and b.name.startswith('HW_'):
                continue
            bs.add(b)
    ii = des.createInterferenceInput(bs)
    ii.areCoincidentFacesIncluded = False
    res = des.analyzeInterference(ii)
    out = []
    for r in res:
        a, b = r.entityOne, r.entityTwo
        na = (a.assemblyContext.name if a.assemblyContext else '') + '/' + a.name
        nb = (b.assemblyContext.name if b.assemblyContext else '') + '/' + b.name
        out.append((na, nb, round(r.interferenceBody.volume * 1000, 4)))
    return out


def sweep(targets, path=None):
    rep = []
    for t in targets:
        v = drive_servo(t)
        s = snapshot()
        gap = -2 * (s['IF_L_P1'][1] + 29.9)
        rep.append(dict(servo_cmd=t, servo=round(v, 5), q=round(q_now(), 5), pad_gap_mm=round(gap, 3),
                        IF_L_P1=s['IF_L_P1'], IF_R_P1=s['IF_R_P1'], interferences=interference()))
    if path:
        open(path, 'w').write(json.dumps(rep, indent=1))
    return rep
