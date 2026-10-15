# Design specification - HomeMade2F140 v2

All dimensions in mm, angles in rad unless noted. Frame = `robotiq_140_base_link`:
X = pivot axes, Y = opening direction, Z = away from the flange; base bottom at Z = 0.
The single source of truth is `scripts/design.py` (numbers) and
`scripts/parts.py` (part geometry); the Fusion model is generated from them.

## 1. Kinematics (identical to the simulation URDF)

| Item | Value |
|---|---|
| Outer knuckle pivots | Y = +-30.601, Z = 54.905 |
| Inner knuckle pivots | Y = +-12.7, Z = 61.42 |
| Link (pivot to distal pivot) | (99.9754, -2.2185) in the knuckle frame, both links -> exact parallelogram |
| Knuckle roll at q = 0 | pi/2 + 0.725 |
| Outer knuckle -> outer finger (fixed) | (18.2200, 26.0018) |
| Pad (simulation) | 14 x 76 x 6, centre (44.5, -26.9) in the inner-finger frame |
| Sim range | q = 0 (open) .. 0.7 (closed) |
| Mechanical stops | q = -0.03 .. 0.705 |
| Pad aperture | 135.2 (stop) / 130.7 (q=0) / 2.0 (q=0.7) / 1.0 (closing stop) |

Fusion follows the URDF fingertip position within 0.001 mm over the whole stroke
(`docs/verification/verification_sweep_36poses.json`).

## 2. Layers along X

| Part | X range |
|---|---|
| Outer knuckles + sync gears | -4.75 .. 4.75 |
| Tower side walls | 5.0 .. 11.0 (both sides) |
| Inner knuckle prongs (straddle the tower) | 11.5 .. 19.0 (both sides) |
| Outer finger, inner knuckle body | -12 .. 12 (forks: 10.0 gap for the outer knuckle, 15.5 gap for the inner finger) |
| Inner finger | -7.5 .. 7.5 |
| Fingertip | -7 .. 7 |
| Crank (on servo horn) | 14 .. 19 |
| Rod | 19.5 .. 24.5 |

The 2F-140 places its inner-knuckle prongs at 12 .. 19.5. They are shifted
0.5 mm inwards here so that they ride on a washer against the tower wall. This
has no kinematic effect.

## 3. Synchronization gears

- Teeth are cut into both outer knuckles, which mesh at the centre line.
- Module 1.8, 34 teeth (full-gear equivalent), pressure angle 20 deg.
- Pitch radius 30.6 (centre distance 61.2 against 61.202 between pivots).
- 0.20 mm thinned per tooth for FDM backlash.
- Measured flank clearance is 0.19 mm, constant over the stroke.
- 7 teeth per sector (k = -1..5). Contact ratio is about 1.7.
- Left and right parts differ only by a half-pitch tooth phase:
  `OuterKnuckle_L` and `OuterKnuckle_R`.
- Each gear has a kidney slot (R 19.05, width 3.5) that the inner pivot bolt
  passes through. The slot ends are the mechanical end stops. The bolt is
  supported by both tower walls (double shear).
- Tooth load at full servo stall is about 4.4 N m x 1.13 / 2 / 30.6 mm, about
  80 N. Lewis bending stress is about 14 MPa, roughly 3x margin in PETG.

## 4. Drive

- Servo DFRobot SER0062, envelope 40 x 20 x 40.5. Mounting ears with slots
  48.6 x 9.9 apart; flange 27.3 from the bottom.
- The servo lies in the base with the output axis along +X at Y = -14.70,
  Z = 17.5. Body: X -32 .. 8.5, Y -24.5 .. 15.5, Z 7.5 .. 27.5.
- Horn face at X = 14. The crank is a blank to drill using the real metal horn
  as the template; it has a 7.2 mm centre clearance.
- Crank radius 16, rod 43.71 between centres, ear radius 18 on the left inner
  knuckle (ear at 200 deg at q = 0).
- At mid stroke the crank is horizontal and the rod vertical. Transmission
  angles stay within 90 +- 25 deg, with no toggle and no dead centre.
- Torque at the inner knuckle is about 1.13 x servo torque.

### Servo calibration table (crank angle relative to its q = 0 position)

| q URDF | servo (deg) | aperture (mm) |
|---:|---:|---:|
| -0.030 | -1.96 | 135.2 |
| 0.000 | 0.00 | 130.7 |
| 0.100 | 6.50 | 114.8 |
| 0.200 | 12.96 | 97.8 |
| 0.300 | 19.41 | 79.8 |
| 0.400 | 25.85 | 61.0 |
| 0.500 | 32.32 | 41.7 |
| 0.600 | 38.82 | 21.9 |
| 0.700 | 45.39 | 2.0 |
| 0.705 | 45.72 | 1.0 |

The relation is close to linear: servo_deg is about 64.8 x q. Positive is
clockwise seen from +X, which closes the gripper.

Recommended setup:

1. Mount the horn so the crank points along -Y when the servo is near its
   centre command.
2. Set the software limits slightly inside the table above, for example
   q = 0 .. 0.70.
3. Start at 6 V with reduced command range.

DFRobot specifies 500..2500 us for 180 deg, so the full stroke is about
510 us of pulse width.

## 5. Base, wrist stack and fasteners

- **HousingBox:** printed upright with an open top. It has the floor, the
  walls, the servo bulkhead (two pillars carrying the 4 ear screws, nyloc on
  the ear side), 4 corner columns with captive-nut traps and a cable exit in
  the -X wall.
- **Tower:** printed with its plate on the bed. Plate Z 36..40 with openings
  for the gear sweep and the rod. Two walls hold the 4 pivots. The O-pivot
  heads are counterbored (left on +X, right on -X) because the inner-knuckle
  ear passes over them.
- **Wrist stack:** flange -> CameraMount (Z -83.8..-72.2) -> SpacerA
  (-72.2..-35) -> SpacerB (-35..0) -> gripper. This matches
  `real_sim_wara_ur10e.urdf`: gripper base at tool_eef + 77.2, rotated 90 deg
  from the camera support.
- 4 x M6 x 70 on the UR pattern (circle 50 mm, at -22.5 / 67.5 / 157.5 /
  247.5 deg in the gripper frame) go from the 14 mm deep Ø11 counterbores in
  the top of SpacerB, through the stack, into the flange, with about 6.8 mm
  of thread.
- The box is screwed to SpacerB with 4 x M3 x 12 into captive nyloc nuts.
  The tower is screwed to the box with 4 x M3 x 12 into captive nyloc nuts.
- Fingertip: 2 x M3 x 16 from the outer face of the inner finger into captive
  nyloc nuts. The grip face stays closed.

## 6. Tolerances (initial, tune with test prints)

- Pivot holes Ø3.3 (M3 shank as pin), clearance holes Ø3.4.
- Rotating side gaps 0.25 per side; 0.5 mm M3 washers where two parts rotate
  against each other.
- Nut traps: hex 5.7 across flats, 4.2 deep, with insertion slot.
- Distal forks are cut to the swept volume of the inner finger + 0.5 mm.
- Do not scale parts to compensate for shrinkage; drill or ream the pivot
  holes instead.

## 7. Printing

- Material PETG, ASA or PA-CF for every structural part. A TPU skin can be
  glued on the fingertip grip face (it changes the closed gap).
- The STLs in `print/parts` are already oriented: largest flat face on
  the bed.
  - Outer fingers and inner knuckles lie on their long flat side. Their fork
    slots become vertical, so no support is needed.
  - Fingertips print grip face down.
  - SpacerA and CameraMount print upside down.
- Supports are only needed for the horizontal pivot holes, if your printer
  bridges 3.3 mm poorly. The nut slots in SpacerB bridge 5.7 mm.

## 8. Assembly order

1. SpacerB, SpacerA and CameraMount onto the flange with 4 x M6 x 70. Put the
   M3 nuts into the SpacerB traps first.
2. Box onto SpacerB (4 x M3 x 12 from inside the box). Nuts into the column
   traps.
3. Crank on the horn, then the rod on the crank (M3 x 16, washers, nyloc).
   Tighten on the bench while holding the head.
4. Set the servo near its centre command. Fit the horn with the crank pointing
   -Y and the rod vertical. Drop the servo into the bulkhead from above and fit
   4 x M3 x 16.
5. Tower onto the box with the rod through its slot (4 x M3 x 12).
6. Outer knuckles: mesh both gears in the q = 0 pose (sector ends symmetric),
   then fit the O pivot bolts (M3 x 30).
7. Fit the inner knuckles:
   - Put the M3 nyloc into the left ear pocket first.
   - Fit the I pivot bolts (M3 x 50) through prong, washer, wall, the gear
     kidney slots, wall, washer and prong.
8. Rod to ear: M3 x 12 from the rod side into the captive nut.
9. Outer fingers to outer knuckles (2 x M3 x 30 each).
10. Inner fingers (P1 and P2, M3 x 30).
11. Fingertips (2 x M3 x 16 each).

## 9. Not validated yet (requires the physical parts)

- Real horn hole pattern. The crank is a drilling blank.
- D435i thread depth: the camera screw engages 3.5 mm.
- UR flange thread depth: needs at least 7 mm.
- Print tolerances of holes, forks and gear backlash on your printer.
- Strength under repeated stall and fatigue of the printed teeth and ear:
  verify with a current-limited test before full 8.4 V.
