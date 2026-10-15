"""Part definitions for HomeMade2F140 v2 (see design.py for the frame and conventions).

Each part: dict(group, feats=[(x0, x1, op, shape)], extra=[non-X features for the CAD builder], twin=bool)
Shapes (YZ plane, mm): ('circle', c, r) ('hull', [(c, r), ...]) ('poly', [pts]) ('rect', y0, z0, y1, z1)
('wedge', c, r, a0, a1) ('kidney', c, R, a0, a1, hw) ('gear', phase)
twin=True: the part also exists on the right side as its 180 deg rotation about Z (same component).
"""
import math
from design import *

H = M3_HOLE / 2


def A(u, v=0.0, origin=I):
    return knuckle_pt(origin, (u, v))


def AL(u):
    """Point on the inner knuckle's true pivot-to-pivot line (I -> P2), u mm from I."""
    return lerp(I, P2, u / math.dist(I, P2))


def ifp(u, v):
    return if_pt((u, v))


cap0, cap1 = slot_caps()
SLOT = ('kidney', O, SLOT_R, cap0, cap1, SLOT_HALFW)


def outer_knuckle(phase):
    a0 = GEAR_SECTOR[0] + phase * GEAR_PITCH
    return [
        (-X_OK, X_OK, 'add', ('circle', O, 9.0)),
        (-X_OK, X_OK, 'add', ('hull', [(O, 8.0), (J, 6.0), (J2, 6.0)])),
        (-X_OK, X_OK, 'add', ('gear', phase)),
        (-X_OK, X_OK, 'add', ('wedge', O, WEB_R, a0, WEB_A1)),
        (-X_OK, X_OK, 'cut', SLOT),
        (-X_OK, X_OK, 'cut', ('circle', O, H)),
        (-X_OK, X_OK, 'cut', ('circle', J, H)),
        (-X_OK, X_OK, 'cut', ('circle', J2, H)),
    ]


# distal fork gaps: hulls that contain the mating inner finger over the whole stroke (+0.5 mm), see check2d.fork_report
OF_GAP = ('hull', [(knuckle_pt(O, (90.0, -2.0)), 7.8), (P1, 8.3)])
IK_GAP = ('hull', [(knuckle_pt(I, (90.0, -2.0)), 7.8), (P2, 8.3)])

PARTS = {
    # ------------------------------------------------------------------ moving, left side (+ twins)
    'OuterKnuckle_L': dict(group='OK_L', twin=False, feats=outer_knuckle(0.0)),
    'OuterKnuckle_R': dict(group='OK_R', twin=False, feats=outer_knuckle(0.5), mirror=True),
    'OuterFinger': dict(group='OK', twin=True, feats=[
        (-X_IKBODY, X_IKBODY, 'add', ('hull', [(J, 7.5), (P1, 6.5)])),
        (-X_OFGAP, X_OFGAP, 'cut', ('hull', [(O, 8.5), (J, 6.5), (J2, 6.5)])),
        (-X_IFGAP, X_IFGAP, 'cut', OF_GAP),
        (-X_IKBODY, X_IKBODY, 'cut', ('circle', J, H)),
        (-X_IKBODY, X_IKBODY, 'cut', ('circle', J2, H)),
        (-X_IKBODY, X_IKBODY, 'cut', ('circle', P1, H)),
    ]),
    'InnerKnuckle': dict(group='IK', twin=True, feats=[
        (X_PRONG[0], X_PRONG[1], 'add', ('hull', [(I, 6.5), (AL(52.0), 6.5)])),
        (-X_PRONG[1], -X_PRONG[0], 'add', ('hull', [(I, 6.5), (AL(52.0), 6.5)])),
        (X_PRONG[0], X_PRONG[1], 'add', ('hull', [(I, 6.5), (K0, BOSS_R + 0.5)])),
        (-X_PRONG[1], X_PRONG[1], 'add', ('hull', [(AL(42.0), 6.5), (AL(50.0), 6.5)])),
        (-X_IKBODY, X_IKBODY, 'add', ('hull', [(AL(42.0), 6.5), (P2, 6.5)])),
        (-X_IFGAP, X_IFGAP, 'cut', IK_GAP),
        (-X_PRONG[1], X_PRONG[1], 'cut', ('circle', I, H)),
        (-X_IKBODY, X_IKBODY, 'cut', ('circle', P2, H)),
        (X_PRONG[0], X_PRONG[1], 'cut', ('circle', K0, M3_CLR / 2)),
        (X_PRONG[1] - 4.2, X_PRONG[1], 'cut', ('hex', K0, NUT_AF + 0.2, 0.0)),
    ]),
    'InnerFinger': dict(group='IF', twin=True, feats=[
        (-X_IF, X_IF, 'add', ('hull', [(P1, 6.0), (P2, 6.0)])),
        (-X_IF, X_IF, 'add', ('hull', [(P2, 5.99), (ifp(44.5, -23.89), 0.0), (ifp(44.5, -11.9), 0.0)])),
        (-X_IF, X_IF, 'cut', ('circle', P1, H)),
        (-X_IF, X_IF, 'cut', ('circle', P2, H)),
        (-X_IF - 0.1, X_IF + 0.1, 'cut', ('rect', P1[0] + 23.9, P1[1] - 10.0, P1[0] + 26.0, P1[1] + 50.0)),
    ], extra=[('yhole_if', u, 3.4) for u in (20.0, 34.0)]),
    'Fingertip': dict(group='IF', twin=True, feats=[
        (-7.0, 7.0, 'add', ('poly', [ifp(6.5, -29.9), ifp(82.5, -29.9), ifp(82.5, -23.9), ifp(6.5, -23.9)])),
        (-7.0, 7.0, 'add', ('poly', [ifp(44.75, -23.9), ifp(82.5, -23.9), ifp(82.5, -21.4), ifp(44.75, -17.9)])),
    ], extra=[('pad_nut', u) for u in (20.0, 34.0)]),
    'Crank': dict(group='crank', twin=False, feats=[
        (X_CRANK[0], X_CRANK[1], 'add', ('hull', [(S, 13.0), (c_at(0), BOSS_R)])),
        (X_CRANK[0], X_CRANK[1], 'cut', ('circle', S, 3.6)),
        (X_CRANK[0], X_CRANK[1], 'cut', ('circle', c_at(0), H)),
    ]),
    'Rod': dict(group='rod', twin=False, feats=[
        (X_ROD[0], X_ROD[1], 'add', ('hull', [(c_at(0), BOSS_R), (K0, BOSS_R)])),
        (X_ROD[0], X_ROD[1], 'cut', ('circle', c_at(0), H)),
        (X_ROD[0], X_ROD[1], 'cut', ('circle', K0, H)),
    ]),
}


# ------------------------------------------------------------------ static parts
def tower_outline():
    return [(-TOWER_Y, BOX_TOP + PLATE_T), (TOWER_Y, BOX_TOP + PLATE_T), (TOWER_Y, 64.0),
            (TOWER_FLAT, TOWER_TOP), (-TOWER_FLAT, TOWER_TOP), (-TOWER_Y, 64.0)]


PARTS['Tower'] = dict(group='static', twin=False, feats=[
    (BOX_X[0], BOX_X[1], 'add', ('rect', -BOX_Y, BOX_TOP, BOX_Y, BOX_TOP + PLATE_T)),
    (-X_OK - 0.5, X_OK + 0.5, 'cut', ('rect', -GEAR_SLOT_Y, BOX_TOP - 1, GEAR_SLOT_Y, BOX_TOP + PLATE_T + 1)),
    (X_ROD[0] - 0.75, X_ROD[1] + 0.75, 'cut', ('rect', -37.0, BOX_TOP - 1, -21.0, BOX_TOP + PLATE_T + 1)),
    (X_WALL[0], X_WALL[1], 'add', ('poly', tower_outline())),
    (-X_WALL[1], -X_WALL[0], 'add', ('poly', tower_outline())),
    (-X_WALL[1], X_WALL[1], 'add', ('rect', -TOWER_FLAT, TOWER_TOP - 3.0, TOWER_FLAT, TOWER_TOP)),
    (-X_WALL[1], X_WALL[1], 'cut', ('circle', O, H)),
    (-X_WALL[1], X_WALL[1], 'cut', ('circle', (-O[0], O[1]), H)),
    (-X_WALL[1], X_WALL[1], 'cut', ('circle', I, H)),
    (-X_WALL[1], X_WALL[1], 'cut', ('circle', (-I[0], I[1]), H)),
    (X_WALL[1] - M3_CBORE[1], X_WALL[1], 'cut', ('circle', O, M3_CBORE[0] / 2)),            # O_L head on +X
    (-X_WALL[1], -X_WALL[1] + M3_CBORE[1], 'cut', ('circle', (-O[0], O[1]), M3_CBORE[0] / 2)),  # O_R head on -X
])

_bx0, _bx1 = BOX_X
_iy = BOX_Y - BOX_T
PARTS['HousingBox'] = dict(group='static', twin=False, feats=[
    (_bx0, _bx1, 'add', ('rect', -BOX_Y, 0.0, BOX_Y, FLOOR_T)),
    (_bx0, _bx0 + BOX_T, 'add', ('rect', -BOX_Y, 0.0, BOX_Y, BOX_TOP)),
    (_bx1 - BOX_T, _bx1, 'add', ('rect', -BOX_Y, 0.0, BOX_Y, BOX_TOP)),
    (_bx0, _bx1, 'add', ('rect', -BOX_Y, 0.0, -_iy, BOX_TOP)),
    (_bx0, _bx1, 'add', ('rect', _iy, 0.0, BOX_Y, BOX_TOP)),
    # servo bulkhead: two pillars carrying the ear screws
    (BULK_X[0], BULK_X[1], 'add', ('rect', -_iy, FLOOR_T, SERVO_Y[0] - 0.25, SERVO_Z[1])),
    (BULK_X[0], BULK_X[1], 'add', ('rect', SERVO_Y[1] + 0.25, FLOOR_T, _iy, SERVO_Z[1])),
] + [(BULK_X[0], BULK_X[1], 'cut', ('circle', s, M3_CLR / 2)) for s in SERVO_SLOTS])

# servo envelope + metal horn (reference, not printed)
PARTS['Servo_D5545GS'] = dict(group='static', twin=False, printed=False, feats=[
    (SERVO_XBOT, SERVO_XTOP, 'add', ('rect', SERVO_Y[0], SERVO_Z[0], SERVO_Y[1], SERVO_Z[1])),
    (SERVO_FLANGE_X[0], SERVO_FLANGE_X[1], 'add',
     ('rect', SERVO_YC - SERVO['ear_len'] / 2, SERVO_Z[0], SERVO_YC + SERVO['ear_len'] / 2, SERVO_Z[1])),
    (SERVO_XTOP, X_CRANK[0] - 3.0, 'add', ('circle', S, 3.0)),
] + [(SERVO_FLANGE_X[0] - 0.1, SERVO_FLANGE_X[1] + 0.1, 'cut', ('circle', sl, 2.25)) for sl in SERVO_SLOTS])
PARTS['ServoHorn_Ref'] = dict(group='crank', twin=False, printed=False, feats=[
    (X_CRANK[0] - 3.0, X_CRANK[0], 'add', ('circle', S, SERVO['horn_d'] / 2)),
])


# ------------------------------------------------------------------ hardware (checked for clearance too)
def bolt(name, group, c, x_head0, x_head1, x_tip, nut=None, washers=()):
    """Bolt along X: head between x_head0..x_head1, shank from the head to x_tip; optional nyloc (x0, x1)."""
    feats = [(min(x_head0, x_head1), max(x_head0, x_head1), 'add', ('circle', c, M3_HEAD[0] / 2))]
    s0, s1 = sorted((x_head1 if abs(x_head1 - x_tip) < abs(x_head0 - x_tip) else x_head0, x_tip))
    feats.append((s0, s1, 'add', ('circle', c, 1.45)))
    if nut:
        feats.append((nut[0], nut[1], 'add', ('circle', c, NYLOC[0] / 2)))
    for w in washers:
        feats.append((w[0], w[1], 'add', ('circle', c, WASHER[0] / 2)))
    return name, dict(group=group, twin=True, printed=False, feats=feats)


HW = dict([
    # outer pivot, head counterbored in the +X wall, nyloc on -X (M3x30)
    bolt('Bolt_O', 'static', O, X_WALL[1] - M3_CBORE[1] + 0.05, X_WALL[1] - M3_CBORE[1] + 0.05 + 3.0,
         X_WALL[1] - M3_CBORE[1] + 0.05 - 30, nut=(-X_WALL[1] - 4.5, -X_WALL[1] - 0.5),
         washers=[(-X_WALL[1] - 0.5, -X_WALL[1])]),
    # inner pivot, head on -X prong, nyloc on +X (M3x45)
    bolt('Bolt_I', 'static', I, -X_PRONG[1] - 3.5, -X_PRONG[1] - 0.5, -X_PRONG[1] - 0.5 + 45,
         nut=(X_PRONG[1] + 0.5, X_PRONG[1] + 4.5),
         washers=[(-X_PRONG[1] - 0.5, -X_PRONG[1]), (X_PRONG[1], X_PRONG[1] + 0.5),
                  (-X_PRONG[0], -X_WALL[1]), (X_WALL[1], X_PRONG[0])]),
    # outer knuckle / outer finger rigid bolts (M3x30), head -X, nyloc +X
    bolt('Bolt_J', 'OK', J, -X_IKBODY - 3.5, -X_IKBODY - 0.5, -X_IKBODY - 0.5 + 30,
         nut=(X_IKBODY + 0.5, X_IKBODY + 4.5), washers=[(-X_IKBODY - 0.5, -X_IKBODY), (X_IKBODY, X_IKBODY + 0.5)]),
    bolt('Bolt_J2', 'OK', J2, -X_IKBODY - 3.5, -X_IKBODY - 0.5, -X_IKBODY - 0.5 + 30,
         nut=(X_IKBODY + 0.5, X_IKBODY + 4.5), washers=[(-X_IKBODY - 0.5, -X_IKBODY), (X_IKBODY, X_IKBODY + 0.5)]),
    bolt('Bolt_P1', 'IF', P1, -X_IKBODY - 3.5, -X_IKBODY - 0.5, -X_IKBODY - 0.5 + 30,
         nut=(X_IKBODY + 0.5, X_IKBODY + 4.5), washers=[(-X_IKBODY - 0.5, -X_IKBODY), (X_IKBODY, X_IKBODY + 0.5)]),
    bolt('Bolt_P2', 'IF', P2, -X_IKBODY - 3.5, -X_IKBODY - 0.5, -X_IKBODY - 0.5 + 30,
         nut=(X_IKBODY + 0.5, X_IKBODY + 4.5), washers=[(-X_IKBODY - 0.5, -X_IKBODY), (X_IKBODY, X_IKBODY + 0.5)]),
])
# drive pins (left only): K head counterbored in the ear, C head under the crank (M3x16)
HW['Bolt_K'] = dict(group='rodK', twin=False, printed=False, feats=[
    (X_ROD[1] + 0.5, X_ROD[1] + 3.5, 'add', ('circle', K0, M3_HEAD[0] / 2)),        # M3x12 head on the rod side
    (X_ROD[1] + 0.5 - 12.0, X_ROD[1] + 0.5, 'add', ('circle', K0, 1.45)),
    (X_PRONG[1] - 4.0, X_PRONG[1], 'add', ('circle', K0, 2.75)),                     # nyloc inside the ear pocket
    (X_ROD[1], X_ROD[1] + 0.5, 'add', ('circle', K0, WASHER[0] / 2)),
    (X_PRONG[1], X_ROD[0], 'add', ('circle', K0, WASHER[0] / 2)),
])
HW['Bolt_C'] = dict(group='rodC', twin=False, printed=False, feats=[
    (X_CRANK[0] - 3.0, X_CRANK[0], 'add', ('circle', c_at(0), M3_HEAD[0] / 2)),
    (X_CRANK[0], X_CRANK[0] + 16.0, 'add', ('circle', c_at(0), 1.45)),
    (X_ROD[1] + 0.5, X_ROD[1] + 4.5, 'add', ('circle', c_at(0), NYLOC[0] / 2)),
    (X_ROD[1], X_ROD[1] + 0.5, 'add', ('circle', c_at(0), WASHER[0] / 2)),
    (X_CRANK[1], X_ROD[0], 'add', ('circle', c_at(0), WASHER[0] / 2)),
])


# ====================================================================== non-X features for the CAD builder
# zfeats: (z0, z1, op, shape-in-XY)   yfeats: (y0, y1, op, shape-in-XZ)
def _toward(c, target, length):
    d = unit(sub(target, c))
    return add(c, (d[0] * length, d[1] * length))


def nut_trap_z(c, z0, outward):
    """Hex pocket for an M3 nyloc (4 mm) plus an insertion slot along `outward` (unit XY)."""
    af = NUT_AF + 0.2
    end = add(c, (outward[0] * 30, outward[1] * 30))
    n = (-outward[1] * af / 2, outward[0] * af / 2)
    slot = ('poly', [add(c, n), add(end, n), sub(end, n), sub(c, n)])
    ang = math.atan2(outward[1], outward[0])
    return [(z0, z0 + 4.2, 'cut', ('hex', c, af, ang)), (z0, z0 + 4.2, 'cut', slot)]


def ur_points(r=UR_PCD / 2):
    return [(r * math.cos(a), r * math.sin(a)) for a in UR_ANGLES_G]


def cam(pt):
    """Camera-support frame XY -> gripper frame XY (rotation -90 deg about Z)."""
    return (pt[1], -pt[0])


PARTS['Tower']['zfeats'] = [(BOX_TOP - 0.1, BOX_TOP + PLATE_T + 0.1, 'cut', ('circle', s, M3_CLR / 2)) for s in TOWER_SCREWS]

_box_z = []
for s in TOWER_SCREWS:
    PARTS['HousingBox']['feats'].append((s[0] - 4.5, s[0] + 4.5, 'add', ('rect', s[1] - 4.5, FLOOR_T, s[1] + 4.5, BOX_TOP)))
    _box_z.append((BOX_TOP - 14.0, BOX_TOP + 0.1, 'cut', ('circle', s, M3_CLR / 2)))
    _box_z += nut_trap_z(s, BOX_TOP - 6.5, unit(sub((0.0, 0.0), s)))
for s in BASE_SCREWS:
    _box_z.append((-0.1, FLOOR_T + 0.1, 'cut', ('circle', s, M3_CLR / 2)))
PARTS['HousingBox']['zfeats'] = _box_z
# servo cable exit through the -X wall, next to the servo's far end
PARTS['HousingBox']['feats'].append((BOX_X[0] - 0.1, BOX_X[0] + BOX_T + 0.1, 'cut',
                                     ('hull', [((SERVO_Y[1] + 4.0, 12.5), 4.5), ((SERVO_Y[1] + 12.0, 12.5), 4.5)])))

PARTS['SpacerB'] = dict(group='static', twin=False, feats=[], zfeats=[
    (STACK['spacer_b'][0], STACK['spacer_b'][1], 'add', ('circle', (0.0, 0.0), 37.5)),
    (STACK['spacer_b'][0], STACK['spacer_b'][1], 'add', ('rect', 30.0, -15.0, 48.7, 15.0)),
] + [(STACK['spacer_b'][0] - 0.1, 0.1, 'cut', ('circle', p, 3.3)) for p in ur_points()]
  + [(-9.0, 0.1, 'cut', ('circle', p, 5.5)) for p in ur_points()]
  + [(-12.0, 0.1, 'cut', ('circle', s, M3_CLR / 2)) for s in BASE_SCREWS]
  + sum([nut_trap_z(s, -7.7, unit(s)) for s in BASE_SCREWS], []))

PARTS['SpacerA'] = dict(group='static', twin=False, feats=[], zfeats=[
    (STACK['spacer_a'][0] + 10.2, STACK['spacer_a'][1], 'add', ('circle', (0.0, 0.0), 32.15)),
    (STACK['spacer_a'][0], STACK['spacer_a'][0] + 10.2, 'add', ('circle', (0.0, 0.0), 31.6)),
    (STACK['spacer_a'][0] + 10.2, STACK['spacer_a'][1], 'add', ('rect', 28.0, -17.5, 46.44, 17.5)),
    (STACK['spacer_a'][0] - 0.1, STACK['spacer_a'][0] + 10.2, 'cut', ('circle', (0.0, 0.0), 12.55)),
] + [(STACK['spacer_a'][0] - 0.1, STACK['spacer_a'][1] + 0.1, 'cut', ('circle', p, 3.3)) for p in ur_points()])

_cz0, _cz1 = STACK['cam']
_ring = ('circle', (0.0, 0.0), 35.7)
_arm = ('rect', 0.0, -29.57, 107.1, 29.57)
PARTS['CameraMount'] = dict(group='static', twin=False, feats=[], zfeats=[
    (_cz0, _cz1, 'add', _ring), (_cz0, _cz1, 'add', _arm),
    (_cz0 - 0.1, STACK['flange'], 'cut', ('circle', (0.0, 0.0), 31.6)),
    (STACK['flange'] - 0.1, _cz1 + 0.1, 'cut', ('circle', (0.0, 0.0), 16.05)),
] + [(_cz0 - 0.1, _cz1 + 0.1, 'cut', ('circle', p, 3.3)) for p in ur_points()]
  + [(_cz0 - 0.1, _cz1 + 0.1, 'cut', ('circle', (25.0 * math.cos(UR_DOWEL_G), 25.0 * math.sin(UR_DOWEL_G)), 3.175))]
  + [(_cz0 - 0.1, _cz1 + 0.1, 'cut', ('circle', cam((cx, 100.36)), M3_CLR / 2)) for cx in (-22.41, 22.59)]
  + [(_cz0 - 0.1, _cz0 + 7.1, 'cut', ('circle', cam((cx, 100.36)), 3.1)) for cx in (-22.41, 22.59)])

PARTS['RealSense_D435i_Ref'] = dict(group='static', twin=False, printed=False, feats=[], zfeats=[
    (_cz1, _cz1 + 25.0, 'add', ('rect', 100.35 - 12.5, -45.0 - 0.1, 100.35 + 12.5, 45.0 - 0.1)),
] + [(_cz1 - 0.1, _cz1 + 5.0, 'cut', ('circle', cam((cx, 100.36)), r)) for r in (1.25, 1.5) for cx in (-22.41, 22.59)])

# pad screws: through the inner finger along Y (head on the outer face), nyloc trapped in the fingertip
_pu = (20.0, 34.0)
PARTS['InnerFinger']['yfeats'] = [(P1[0] + 11.9 - 0.1, P1[0] + 23.9 + 0.1, 'cut', ('circle', (0.0, P1[1] + u), M3_CLR / 2)) for u in _pu]
PARTS['Fingertip']['yfeats'] = sum([[(P1[0] + 23.9 - 0.1, P1[0] + 28.1, 'cut', ('hex', (0.0, P1[1] + u), NUT_AF + 0.2, 0.0)),
                                     (P1[0] + 23.9 - 0.1, P1[0] + 28.1, 'cut', ('circle', (0.0, P1[1] + u), M3_CLR / 2))]
                                    for u in _pu], [])



# ====================================================================== hardware bodies for the CAD model (not printed)
# dict(carrier, name, axis, c, segs=[(v0, v1, ('circle', r) | ('hex', af))]); c in the carrier's frame (YZ for x, XY for z, XZ for y)
def _from_feats(carrier, name, feats, mirror=False):
    out = []
    c = feats[0][3][1]
    segs = [(x0, x1, ('circle', sh[2])) for x0, x1, _, sh in feats]
    if mirror:
        c = (-c[0], c[1])
        segs = [(-x1, -x0, g) for x0, x1, g in segs]
    return dict(carrier=carrier, name=name, axis='x', c=c, segs=segs)


HW_CAD = [
    _from_feats('Tower', 'HW_M3x30_PivotO_L', HW['Bolt_O']['feats']),
    _from_feats('Tower', 'HW_M3x30_PivotO_R', HW['Bolt_O']['feats'], mirror=True),
    _from_feats('Tower', 'HW_M3x45_PivotI_L', HW['Bolt_I']['feats']),
    _from_feats('Tower', 'HW_M3x45_PivotI_R', HW['Bolt_I']['feats'], mirror=True),
    _from_feats('OuterFinger', 'HW_M3x30_J', HW['Bolt_J']['feats']),
    _from_feats('OuterFinger', 'HW_M3x30_J2', HW['Bolt_J2']['feats']),
    _from_feats('InnerFinger', 'HW_M3x30_P1', HW['Bolt_P1']['feats']),
    _from_feats('InnerFinger', 'HW_M3x30_P2', HW['Bolt_P2']['feats']),
    _from_feats('Rod', 'HW_M3x12_PinK', HW['Bolt_K']['feats']),
    _from_feats('Crank', 'HW_M3x16_PinC', HW['Bolt_C']['feats']),
]
for i, sl in enumerate(SERVO_SLOTS):
    HW_CAD.append(dict(carrier='HousingBox', name=f'HW_M3x16_ServoEar{i}', axis='x', c=sl, segs=[
        (BULK_X[1] + 0.5, BULK_X[1] + 3.5, ('circle', M3_HEAD[0] / 2)),
        (BULK_X[1], BULK_X[1] + 0.5, ('circle', WASHER[0] / 2)),
        (BULK_X[1] + 0.5 - 16.0, BULK_X[1] + 0.5, ('circle', 1.45)),
        (SERVO_FLANGE_X[0] - 0.5, SERVO_FLANGE_X[0], ('circle', WASHER[0] / 2)),
        (SERVO_FLANGE_X[0] - 4.5, SERVO_FLANGE_X[0] - 0.5, ('hex', NUT_AF))]))
for i, sc in enumerate(TOWER_SCREWS):
    HW_CAD.append(dict(carrier='Tower', name=f'HW_M3x12_Tower{i}', axis='z', c=sc, segs=[
        (BOX_TOP + PLATE_T, BOX_TOP + PLATE_T + 3.0, ('circle', M3_HEAD[0] / 2)),
        (BOX_TOP + PLATE_T - 12.0, BOX_TOP + PLATE_T, ('circle', 1.45)),
        (BOX_TOP - 6.4, BOX_TOP - 2.4, ('hex', NUT_AF, math.atan2(-sc[1], -sc[0])))]))
for i, sc in enumerate(BASE_SCREWS):
    HW_CAD.append(dict(carrier='HousingBox', name=f'HW_M3x12_Base{i}', axis='z', c=sc, segs=[
        (FLOOR_T, FLOOR_T + 3.0, ('circle', M3_HEAD[0] / 2)),
        (FLOOR_T - 12.0, FLOOR_T, ('circle', 1.45)),
        (-7.6, -3.6, ('hex', NUT_AF, math.atan2(sc[1], sc[0])))]))
for i, pt in enumerate(ur_points()):
    HW_CAD.append(dict(carrier='SpacerB', name=f'HW_M6x75_Flange{i}', axis='z', c=pt, segs=[
        (-9.0, -3.0, ('circle', 5.0)),
        (-84.0, -9.0, ('circle', 2.95))]))
for i, cx in enumerate((-22.41, 22.59)):
    pt = cam((cx, 100.36))
    HW_CAD.append(dict(carrier='CameraMount', name=f'HW_M3x8_Camera{i}', axis='z', c=pt, segs=[
        (_cz0 + 7.1 - 3.0, _cz0 + 7.1, ('circle', M3_HEAD[0] / 2)),
        (_cz0 + 7.1, _cz0 + 15.1, ('circle', 1.45))]))
for i, u in enumerate(_pu):
    HW_CAD.append(dict(carrier='InnerFinger', name=f'HW_M3x16_Pad{i}', axis='y', c=(0.0, P1[1] + u), segs=[
        (P1[0] + 11.9 - 3.0, P1[0] + 11.9, ('circle', M3_HEAD[0] / 2)),
        (P1[0] + 11.9, P1[0] + 27.9, ('circle', 1.45)),
        (P1[0] + 23.9, P1[0] + 27.9, ('hex', NUT_AF))]))

COLORS = {
    'Tower': 'Plastic - Matte (Gray)', 'HousingBox': 'Plastic - Matte (Gray)',
    'OuterKnuckle_L': 'Plastic - Matte (Yellow)', 'OuterKnuckle_R': 'Plastic - Matte (Yellow)',
    'OuterFinger': 'Plastic - Matte (Blue)', 'InnerKnuckle': 'Plastic - Matte (Green)',
    'InnerFinger': 'Plastic - Matte (Blue)', 'Fingertip': 'Plastic - Matte (Black)',
    'Crank': 'Plastic - Matte (Red)', 'Rod': 'Plastic - Matte (Red)',
    'SpacerA': 'Plastic - Matte (White)', 'SpacerB': 'Plastic - Matte (White)', 'CameraMount': 'Plastic - Matte (Yellow)',
    'Servo_D5545GS': 'Plastic - Glossy (Black)', 'ServoHorn_Ref': 'Aluminum - Anodized Glossy (Blue)',
    'RealSense_D435i_Ref': 'Aluminum - Anodized Glossy (Grey)', 'HW': 'Steel - Satin',
}
