# Bill of materials

Quantities are for one complete unit.

The **gripper** is everything from the housing box upwards. The **wrist stack**
(SpacerA, SpacerB and CameraMount) replicates the real UR10e wrist used in the
WARA challenge cell and is not part of the gripper itself; see the main README.

## Printed parts (`print/parts`, already oriented for printing)

### Gripper

| Qty | Part | File | Size on the bed (mm) | Notes |
|---:|---|---|---|---|
| 1 | Housing box | `HomeMade2F140_HousingBox_x1.stl` | 94.9 x 86.7 x 36.0 | servo bulkhead, captive-nut columns |
| 1 | Tower | `HomeMade2F140_Tower_x1.stl` | 82.7 x 71.9 x 52.0 | holds the 4 base pivots |
| 1 | Crank | `HomeMade2F140_Crank_x1.stl` | 34.0 x 26.0 x 5.0 | drilling blank; use the servo's metal horn as template |
| 1 | Rod | `HomeMade2F140_Rod_x1.stl` | 53.7 x 10.0 x 5.0 | |
| 1 | Outer knuckle L | `HomeMade2F140_OuterKnuckle_L_x1.stl` | 72.6 x 34.8 x 9.5 | gear sector, tooth phase A |
| 1 | Outer knuckle R | `HomeMade2F140_OuterKnuckle_R_x1.stl` | 72.2 x 34.5 x 9.5 | gear sector, tooth phase B (not interchangeable with L) |
| 2 | Outer finger | `HomeMade2F140_OuterFinger_x2.stl` | 100.5 x 24.0 x 15.0 | |
| 2 | Inner knuckle | `HomeMade2F140_InnerKnuckle_x2.stl` | 114.0 x 40.2 x 28.9 | same part on both sides; only the left one uses its ear |
| 2 | Inner finger | `HomeMade2F140_InnerFinger_x2.stl` | 56.4 x 31.0 x 15.0 | |
| 2 | Fingertip | `HomeMade2F140_Fingertip_x2.stl` | 76.0 x 14.2 x 12.0 | 14 x 76 x 6 pad of the simulation + rear rib |

### Wrist stack (not part of the gripper)

| Qty | Part | File | Size on the bed (mm) | Notes |
|---:|---|---|---|---|
| 1 | Spacer B | `HomeMade2F140_SpacerB_x1.stl` | 75.0 x 87.9 x 35.0 | UR bolt pattern + 4 captive M3 nuts for the housing box |
| 1 | Spacer A | `HomeMade2F140_SpacerA_x1.stl` | 64.3 x 81.5 x 37.2 | print upside down |
| 1 | Camera mount | `HomeMade2F140_CameraMount_x1.stl` | 143.2 x 71.4 x 11.6 | RealSense D435i on 2 x M3, print upside down |

All 17 pieces are also available as one file
(`print/plates/HomeMade2F140_print_set_17pcs.stl`) and split into three
250 x 250 mm plates. The total solid volume is about 655 cm³; with 3 walls and
25 % infill that is roughly 350-400 g of PETG.

## Purchased parts

| Qty | Item | Used in |
|---:|---|---|
| 1 | DFRobot SER0062 (D5545GS) 45 kg-cm servo, with its metal horn | gripper |
| 1 | Regulated 6-8.4 V supply / BEC sized for the servo peak current, plus a fuse | gripper (see `WIRING.md`) |

## Hardware

All screws are ISO 4762 / DIN 912 socket head cap screws, steel 8.8 or A2
stainless. Nuts are M3 nyloc (ISO 10511 / DIN 985). Washers are M3 flat
washers (ISO 7089, 7 mm OD x 0.5 mm).

| Item | Gripper | Wrist stack | Total | Where |
|---|---:|---:|---:|---|
| M3 x 8 | 4 | 2 | **6** | horn to crank (only if the horn holes are M3); camera |
| M3 x 12 | 5 | 4 | **9** | rod-to-ear pin (1), tower to box (4); box to Spacer B (4) |
| M3 x 16 | 9 | - | **9** | crank-rod pin (1), servo ears (4), fingertips (4) |
| M3 x 30 | 10 | - | **10** | outer pivots (2), outer knuckle to outer finger (4), inner finger pivots (4) |
| M3 x 45 | 2 | - | **2** | inner pivots (through prongs, walls and gear slots) |
| M6 x 75 | - | 4 | **4** | UR flange (ISO 9409-1-50-4-M6) through the whole wrist stack |
| M3 nyloc nut | 26 | 4 | **30** | 13 of them are captive in printed hex pockets |
| M3 washer | 46 | 4 | **50** | pivots, servo ears and under heads that sit on plastic |
| 6 x 12 mm dowel pin, ISO 8734 (optional) | - | 1 | **1** | flange centring hole in the camera mount |

Partially threaded M3 x 30 and M3 x 45 screws are preferred for the pivots.

**Tools:** hex keys of 2.5 mm and 5 mm, and a 5.5 mm wrench for the M3 nuts.

The shopping list is also in `docs/shopping_list/` (English and Spanish).
