# HomeMade UR10 Gripper (HomeMade2F140)

**Versión en español: [README.es.md](README.es.md)**

> **Language note:** the author is a native Spanish speaker, but the
> documentation and instructions in this repository are written in English.
> A Spanish version of this README, of the assembly manual and of the shopping
> list is included.

A 3D-printable two-finger gripper for a UR10e. It reproduces the finger
kinematics of the Robotiq 2F-140 used in our WARA challenge simulation and is
driven by a single DFRobot SER0062 (D5545GS) 45 kg-cm PWM servo.

| Open | Closed |
|---|---|
| ![open](docs/images/v2_side_open.png) | ![closed](docs/images/v2_side_closed.png) |

## Highlights

- **Same finger geometry as the simulation.**
  - Pivots, 100 mm parallelogram links, pad and `finger_joint` range come from
    the Robotiq URDF.
  - The CAD fingertip follows the URDF within 0.001 mm over the whole stroke.
  - Pad aperture is 130.7 mm at q = 0 and 2.0 mm at q = 0.7, like the sim.
- **Mechanically synchronized fingers.** Two gear sectors cut into the outer
  knuckles keep the fingers exact mirror images.
- **Strong, simple drive.**
  - The servo sits inside the base and drives the left inner knuckle through
    a crank and rod.
  - 45.7 deg of servo travel covers the full stroke.
  - Every servo load goes through steel pins; no printed tooth is driven by the
    servo.
- **Built-in end stops.** The inner pivot bolt rides in a kidney slot in each
  gear, so the pads never collide.
- **Verified in Fusion.** Zero interferences in 36 poses over the full stroke,
  including all modelled screws, nuts and washers.
- **Mostly printed, few screw types.** 17 printed pieces, M3 hardware in 5
  lengths, plus 4 x M6 for the robot flange.

## About the wrist spacers and the camera mount

Spacer A, Spacer B and the Camera mount reproduce the real wrist assembly of
the UR10e used in the WARA challenge cell:

- RealSense D435i camera mount.
- Two cylindrical spacers.
- Bolted to the flange with the UR pattern (4 x M6 on a 50 mm circle).

They are included so the printed gripper sits at the same height and
orientation as in our simulation (gripper base at tool flange + 77.2 mm).
**They are not part of the gripper itself.**

The gripper starts at the housing box, which bolts onto Spacer B with
4 x M3 x 12. To use the gripper on another robot you need an adapter between
your flange and the housing box. Spacer B on its own, with shorter M6 screws,
is the obvious starting point; this is not validated.

## Complete parts list

### Printed parts

STL files are in `print/parts`, already oriented for printing. The `_xN`
suffix is the quantity.

| Qty | Part | Group |
|---:|---|---|
| 1 | Housing box | gripper |
| 1 | Tower | gripper |
| 1 | Crank (drilling blank for the servo horn) | gripper |
| 1 | Rod | gripper |
| 1 | Outer knuckle L (gear) | gripper |
| 1 | Outer knuckle R (gear, not interchangeable with L) | gripper |
| 2 | Outer finger | gripper |
| 2 | Inner knuckle | gripper |
| 2 | Inner finger | gripper |
| 2 | Fingertip | gripper |
| 1 | Spacer B | wrist stack |
| 1 | Spacer A | wrist stack |
| 1 | Camera mount | wrist stack |

That makes 17 pieces: 14 for the gripper and 3 for the wrist stack.
`print/plates` has the full set in one STL and split into three 250 x 250 mm
plates. Recommended material: PETG, ASA or PA-CF.

### Purchased parts

| Qty | Item |
|---:|---|
| 1 | DFRobot SER0062 (D5545GS) 45 kg-cm servo, 180 deg PWM, with its metal horn |
| 1 | Regulated 6-8.4 V power supply / BEC for the servo peak current, plus a fuse |
| 1 | RealSense D435i (only if you build the camera mount) |

### Hardware

ISO 4762 socket head cap screws, steel 8.8 or A2:

| Item | Gripper | Wrist stack | Total |
|---|---:|---:|---:|
| M3 x 8 | 4 (horn, if its holes are M3) | 2 (camera) | **6** |
| M3 x 12 | 5 | 4 | **9** |
| M3 x 16 | 9 | - | **9** |
| M3 x 30 | 10 | - | **10** |
| M3 x 50 | 2 | - | **2** |
| M6 x 70 | - | 4 | **4** |
| M3 nyloc nut (ISO 10511) | 26 | 4 | **30** |
| M3 washer (ISO 7089, 7 x 0.5 mm) | 46 | 4 | **50** |
| 6 x 12 mm dowel pin (optional) | - | 1 | **1** |

Tools: 2.5 mm and 5 mm hex keys, and a 5.5 mm wrench.

`docs/BOM.md` says where each screw goes. Ready-to-send shopping lists are in
`docs/shopping_list/`.

## How to build it

1. **Print** the parts in `print/parts`, or the plates in `print/plates`.
   - Use 3 or more walls and 25-40 % infill.
   - The parts are already oriented. Only the horizontal pivot holes may need
     support if your printer bridges poorly.
2. **Buy** the hardware listed above.
3. **Assemble** following the LEGO-style manual in `docs/manual/`. It has 26
   steps, each with a parts box and exploded views.
   - English: `HomeMade2F140_Assembly_Manual_EN.pdf`
   - Spanish: `HomeMade2F140_Manual_de_ensamble_ES.pdf`
4. **Wire and calibrate** following `docs/WIRING.md` and the servo table below.
   Start at 6 V with a current limit.

### Servo calibration

Angle of the crank relative to its assembly position. Positive closes the
gripper.

| Simulation q (rad) | Servo (deg) | Pad aperture (mm) |
|---:|---:|---:|
| 0.0 | 0.0 | 130.7 |
| 0.2 | 13.0 | 97.8 |
| 0.4 | 25.9 | 61.0 |
| 0.6 | 38.8 | 21.9 |
| 0.7 | 45.4 | 2.0 |

The relation is close to linear: servo_deg is about 64.8 x q. Mechanical stops
are at -2.0 deg and +45.7 deg. With DFRobot's 500-2500 us = 180 deg, the
whole stroke is about 510 us of pulse width.

## Repository layout

```
cad/        Fusion 360 model (.f3d) and full assembly STEP
print/      print-oriented STL: parts/ (one file per part), plates/ (full set, 250x250 plates)
docs/       BOM, design specification, wiring, Fusion guide, manuals (EN/ES),
            shopping lists (EN/ES), images, verification data
scripts/    Python generator of the whole design (geometry, Fusion build, checks, STL, manual)
LICENSE, LICENSES/, THIRD_PARTY_NOTICES.md   licensing (see below)
```

- `docs/DESIGN_SPEC.md`: kinematics, layers, gears, drive, tolerances,
  assembly order and open points.
- `docs/FUSION.md`: how to move the mechanism in Fusion (drag the crank or
  *Drive Joints* on `Servo_Horn`) and how to regenerate everything.

## Status

- **Designed and verified in CAD:** geometry, joints, full-stroke interference
  check, print orientation and assembly manual.
- **Still to be checked on the physical parts:**
  - the hole pattern of the real servo horn (the crank is a drilling blank);
  - the thread depth of the UR flange (at least 7 mm) and of the D435i;
  - print tolerances of pivots, forks and gear backlash;
  - long-term strength at full 8.4 V stall.

## Safety

This is experimental DIY hardware. The design has not been tested for
strength, fatigue or safety.

- A 45 kg-cm servo can pinch hard. Keep fingers and cables clear.
- Do the first tests at 6 V with a current limit, without the robot moving.
- Never power the servo from a microcontroller's 5 V rail.

You build and use it **at your own risk**. See the warranty and liability
disclaimers in the licenses.

## License

This is open-source hardware.

| What | License |
|---|---|
| Hardware design and documentation: `cad/`, `print/`, `docs/`, READMEs | [CERN-OHL-P-2.0](LICENSE) (CERN Open Hardware Licence v2, permissive) |
| Software: everything in `scripts/` | [MIT](scripts/LICENSE) |

Copyright (c) 2026 Alejandro Garcia.

> This source describes Open Hardware and is licensed under the CERN-OHL-P v2.
> You may redistribute and modify this documentation and make products using it
> under the terms of the CERN-OHL-P v2 (https://cern.ch/cern-ohl). This
> documentation is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
> INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
> PARTICULAR PURPOSE. Please see the CERN-OHL-P v2 for applicable conditions.

All part geometry in this repository is an original design. The finger
kinematics reproduce the numerical parameters of Robotiq's public ROS
description (BSD-3-Clause) so that the gripper matches existing simulations.
No Robotiq files are included. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Robotiq, 2F-140, Universal Robots, UR10e, DFRobot, Intel RealSense, Autodesk
and Fusion are trademarks of their respective owners. They are used only to
describe compatibility. This project is independent and is not affiliated with
or endorsed by any of these companies.
