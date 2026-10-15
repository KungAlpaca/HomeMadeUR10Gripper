"""HomeMade2F140 v2 - single source of truth for the geometry (mm, gripper base frame).

Frame (= robotiq_140_base_link): X = pivot axes, Y = opening direction, Z = away from the flange.
Every part is described at the reference pose q = 0 (URDF open pose) as a list of prismatic features
(x0, x1, op, shape) where the 2-D shape lives in the YZ plane. The same description feeds
  * check2d.py  - fast layer-by-layer sweep with shapely
  * the Fusion builder - true lines/arcs/splines
Left-side parts (Y < 0) are described; right-side twins are the 180 deg rotation about Z (Y -> -Y, X -> -X).
"""
import math

# ---------------------------------------------------------------- Robotiq 2F-140 kinematics (URDF)
TH0 = math.pi / 2 + 0.725                       # outer/inner knuckle frame roll at q = 0
O = (-30.601, 54.905)                           # left outer knuckle pivot
I = (-12.7, 61.42)                              # left inner knuckle pivot
J_LOC = (18.21998610742, 26.0018192872234)      # outer knuckle -> outer finger (fixed)
F_LOC = (81.7554015893473, -28.2203446692936)   # outer finger -> inner finger pivot
LV = (J_LOC[0] + F_LOC[0], J_LOC[1] + F_LOC[1])  # pivot-to-distal-pivot vector, same for both cranks
PAD_C = (44.5, -26.9)                           # pad centre in the inner finger frame (simulation pad)
PAD_SIZE = (76.0, 6.0, 14.0)                    # along u, along v (thickness), along x
Q_OPEN_STOP, Q_CLOSE_STOP = -0.03, 0.705        # mechanical stops (sim range 0..0.7)


def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def knuckle_pt(origin, uv, q=0.0):
    """Point given in a knuckle frame (u along the link) -> global YZ for the left side."""
    return add(origin, rot(uv, TH0 - q))


def unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


J = knuckle_pt(O, J_LOC)
J2_LOC = add(J_LOC, tuple(10.0 * c for c in unit(F_LOC)))
J2 = knuckle_pt(O, J2_LOC)
P1 = knuckle_pt(O, LV)          # outer finger / inner finger pivot
P2 = knuckle_pt(I, LV)          # inner knuckle / inner finger pivot


def if_pt(uv, p1=P1):
    """Inner finger frame (constant roll pi/2): u -> +Z, v -> -Y."""
    return (p1[0] - uv[1], p1[1] + uv[0])


def p1_at(q):
    return knuckle_pt(O, LV, q)


# ---------------------------------------------------------------- layers along X (mm)
X_OK = 4.75            # outer knuckle |x| <= X_OK (centre layer, carries the sync gear)
X_WALL = (5.0, 11.0)   # tower side walls
X_PRONG = (11.5, 19.0)  # inner knuckle proximal prongs
X_IKBODY = 12.0        # inner knuckle body, outer finger body |x| <= 12
X_IFGAP = 7.75         # distal fork gap (inner finger is |x| <= 7.5)
X_IF = 7.5
X_OFGAP = 5.0          # outer finger proximal fork gap (outer knuckle is |x| <= 4.75)
X_CRANK = (14.0, 19.0)
X_ROD = (19.5, 24.5)

# ---------------------------------------------------------------- hardware (ISO 4762 M3, ISO 10511 nyloc, ISO 7089 washer)
M3_HOLE = 3.3          # pivot holes (snug on the M3 shank, ream if needed)
M3_CLR = 3.4           # clearance holes
M3_HEAD = (5.5, 3.0)   # head dia, height
M3_CBORE = (6.2, 3.3)  # counterbore dia, depth
NYLOC = (6.4, 4.0)     # across corners (round envelope), height
NUT_AF = 5.5           # nut trap across flats (+0.2 clearance added where used)
WASHER = (7.0, 0.5)

# ---------------------------------------------------------------- sync gears on the outer knuckles
GEAR_Z = 34
GEAR_M = 1.8           # pitch radius 30.6 -> centre distance 61.2 (pivots are 61.202 apart)
GEAR_PA = math.radians(20.0)
GEAR_BACKLASH = 0.20   # removed from each tooth thickness at the pitch circle (FDM)
GEAR_RP = GEAR_Z * GEAR_M / 2
GEAR_RA = GEAR_RP + GEAR_M
GEAR_RF = GEAR_RP - 1.25 * GEAR_M
GEAR_PITCH = 2 * math.pi / GEAR_Z
GEAR_K = (-1, 5)       # tooth indices (centre at k * pitch from the mesh direction, global angle at q=0);
                       # contact (ratio ~1.7) only spans +-9 deg around the mesh line, so q in [-1.7, 40.4] deg needs k=-1..5
GEAR_SECTOR = ((GEAR_K[0] - 0.5) * GEAR_PITCH, (GEAR_K[1] + 0.5) * GEAR_PITCH)
SLOT_R = math.dist(O, I)                        # inner pivot bolt seen from the outer knuckle
SLOT_A0 = math.atan2(I[1] - O[1], I[0] - O[0])  # its angle at q = 0
SLOT_HALFW = 1.75                               # bolt r 1.5 + 0.25
WEB_R = 24.0                                    # solid web radius around the kidney slot
WEB_A1 = math.radians(76.0)


def slot_caps():
    """Kidney slot cap centres (gear frame = global at q=0). The ends double as the mechanical stops:
    the cap radius exceeds the bolt by 0.25 mm, so the centres sit 0.25/R before each stop angle."""
    d = 0.25 / SLOT_R
    return SLOT_A0 + Q_OPEN_STOP + d, SLOT_A0 + Q_CLOSE_STOP - d


def inv(a):
    return math.tan(a) - a


def gear_tooth_flanks(center_angle, n=7):
    """Return (right_flank, left_flank) point lists (global YZ about O, q=0), root->tip."""
    rb = GEAR_RP * math.cos(GEAR_PA)
    s = math.pi * GEAR_M / 2 - GEAR_BACKLASH
    psi_p = s / (2 * GEAR_RP)
    r0 = max(rb, GEAR_RF)
    rs = [r0 + (GEAR_RA - r0) * i / (n - 1) for i in range(n)]
    right, left = [], []
    for r in rs:
        ar = math.acos(min(1.0, rb / r))
        psi = psi_p + inv(GEAR_PA) - inv(ar)
        right.append(add(O, (r * math.cos(center_angle - psi), r * math.sin(center_angle - psi))))
        left.append(add(O, (r * math.cos(center_angle + psi), r * math.sin(center_angle + psi))))
    return right, left


def gear_outline(phase):
    """Closed outline of the toothed wedge (apex at O) for tooth centres at (k + phase) * pitch."""
    pts = [O]
    a0, a1 = GEAR_SECTOR
    pts.append(add(O, (GEAR_RF * math.cos(a0 + phase * GEAR_PITCH), GEAR_RF * math.sin(a0 + phase * GEAR_PITCH))))
    for k in range(GEAR_K[0], GEAR_K[1] + 1):
        c = (k + phase) * GEAR_PITCH
        rf, lf = gear_tooth_flanks(c)
        rb = GEAR_RP * math.cos(GEAR_PA)
        if GEAR_RF < rb:  # radial dedendum below the base circle
            ang = math.atan2(rf[0][1] - O[1], rf[0][0] - O[0])
            pts.append(add(O, (GEAR_RF * math.cos(ang), GEAR_RF * math.sin(ang))))
        pts += rf
        pts += list(reversed(lf))
        if GEAR_RF < rb:
            ang = math.atan2(lf[0][1] - O[1], lf[0][0] - O[0])
            pts.append(add(O, (GEAR_RF * math.cos(ang), GEAR_RF * math.sin(ang))))
    pts.append(add(O, (GEAR_RF * math.cos(a1 + phase * GEAR_PITCH), GEAR_RF * math.sin(a1 + phase * GEAR_PITCH))))
    return pts


# ---------------------------------------------------------------- drive: servo crank -> rod -> ear on left inner knuckle
RK = 18.0                       # ear radius on the inner knuckle
EAR_A0 = math.radians(200.0)    # ear angle (global) at q = 0; 180 deg at mid stroke
RC = 16.0                       # crank radius
S_Z = 17.5                      # servo output axis height
K0 = add(I, (RK * math.cos(EAR_A0), RK * math.sin(EAR_A0)))
K_MID = add(I, (RK * math.cos(EAR_A0 - 0.3375), RK * math.sin(EAR_A0 - 0.3375)))
S = (K_MID[0] + RC, S_Z)        # crank horizontal (pointing -Y) and rod vertical at mid stroke
ROD_L = K_MID[1] - S_Z
BOSS_R = 5.0                    # rod / crank eye radius


def k_at(q):
    return add(I, (RK * math.cos(EAR_A0 - q), RK * math.sin(EAR_A0 - q)))


def crank_angle(q):
    """Crank angle phi (C = S + RC*(cos, sin)) for knuckle angle q (branch around pi)."""
    k = k_at(q)
    d = math.dist(S, k)
    a = math.atan2(k[1] - S[1], k[0] - S[0])
    # triangle S-C-K: |SC| = RC, |CK| = ROD_L
    cosb = (RC * RC + d * d - ROD_L * ROD_L) / (2 * RC * d)
    b = math.acos(max(-1, min(1, cosb)))
    cands = [a + b, a - b]
    return min(cands, key=lambda p: abs(((p - math.pi + math.pi) % (2 * math.pi)) - math.pi))


def c_at(q):
    p = crank_angle(q)
    return (S[0] + RC * math.cos(p), S[1] + RC * math.sin(p))


# ---------------------------------------------------------------- servo DFRobot SER0062 (envelope, measured drawing)
SERVO = dict(L=40.0, W=20.0, H=40.5, axis_from_end=9.8, flange_from_bottom=27.3, flange_t=3.2,
             ear_len=54.0, slot_pitch_L=48.6, slot_pitch_W=9.9, top_to_horn_face=5.5, horn_d=25.0)
SERVO_XTOP = X_CRANK[0] - SERVO['top_to_horn_face']     # body top face (output side)
SERVO_XBOT = SERVO_XTOP - SERVO['H']
SERVO_Y = (S[0] - SERVO['axis_from_end'], S[0] - SERVO['axis_from_end'] + SERVO['L'])
SERVO_Z = (S_Z - SERVO['W'] / 2, S_Z + SERVO['W'] / 2)
SERVO_FLANGE_X = (SERVO_XBOT + SERVO['flange_from_bottom'], SERVO_XBOT + SERVO['flange_from_bottom'] + SERVO['flange_t'])
SERVO_YC = (SERVO_Y[0] + SERVO_Y[1]) / 2
SERVO_SLOTS = [(SERVO_YC + sy * SERVO['slot_pitch_L'] / 2, S_Z + sz * SERVO['slot_pitch_W'] / 2)
               for sy in (-1, 1) for sz in (-1, 1)]

# ---------------------------------------------------------------- housing / tower / wrist stack
BOX_X = (-36.0, 34.0)
BOX_Y = 40.5
BOX_T = 3.0
FLOOR_T = 4.0
BOX_TOP = 36.0
PLATE_T = 4.0                        # tower base plate Z 36..40
TOWER_TOP = 88.0
TOWER_Y = 38.0
TOWER_FLAT = 14.0                    # top flat half-width
BULK_X = (SERVO_FLANGE_X[1], SERVO_FLANGE_X[1] + 5.0)
GEAR_SLOT_Y = 26.0                   # opening in the tower plate for the gear sweep
STACK = dict(spacer_b=(-35.0, 0.0), spacer_a=(-72.2, -35.0), cam=(-83.8, -72.2), flange=-77.2)
CAM_ROT = -math.pi / 2               # camera-support frame = gripper frame rotated -90 deg about Z
UR_PCD = 50.0
UR_ANGLES_G = [math.radians(a) for a in (-22.5, 67.5, 157.5, 247.5)]   # in the gripper frame
UR_DOWEL_G = math.radians(-157.5)
BASE_SCREWS = [(26.8, 11.1), (-11.1, 26.8), (-18.0, -28.5), (11.1, -26.8)]  # XY, box floor -> spacer B
TOWER_SCREWS = [(-29.0, -31.0), (-29.0, 31.0), (27.0, 31.0), (27.0, -10.0)]  # XY, tower plate -> box columns


if __name__ == '__main__':
    print('J', J, 'J2', J2, 'P1', P1, 'P2', P2)
    print('pad face y at q=0', p1_at(0)[0] + 29.9, 'aperture', -2 * (p1_at(0)[0] + 29.9))
    for q in (Q_OPEN_STOP, 0, 0.35, 0.7, Q_CLOSE_STOP):
        print(f'q={q:6.3f} K={k_at(q)} C={c_at(q)} phi={math.degrees(crank_angle(q)):.2f} '
              f'gap={-2 * (p1_at(q)[0] + 29.9):.2f}')
    print('S', S, 'ROD_L', ROD_L, 'servo Y', SERVO_Y, 'Z', SERVO_Z, 'X', SERVO_XBOT, SERVO_XTOP, 'flange', SERVO_FLANGE_X)
    print('slots', SERVO_SLOTS)
    print('slot R', SLOT_R, 'A0', math.degrees(SLOT_A0), 'caps', [math.degrees(a) for a in slot_caps()])
    print('gear rp ra rf', GEAR_RP, GEAR_RA, GEAR_RF, 'sector deg', [math.degrees(a) for a in GEAR_SECTOR])
