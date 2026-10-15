# Fusion 360 model and build scripts

## Opening the model

Open `cad/HomeMade2F140_v2.f3d` in Autodesk Fusion. In the Data Panel use
**Upload** (or File > Open > Open from my computer). Open it in the **Design**
workspace.

`cad/HomeMade2F140_v2_assembly.step` is the full assembly for other CAD tools.
It contains the gripper, wrist stack, servo/camera envelopes and the modelled
hardware.

## Moving the mechanism

The design already contains all the joints. Fusion has no separate "assembly
mode" to switch on.

There are three ways to move it:

- **Drag:** left-click and drag the red **Crank** or the blue metal horn disc.
  The rod, both knuckles, the gears and both fingers follow.
- **Drive by angle:** Browser > **Joints** > right-click `Servo_Horn` >
  **Drive Joints**.
  - Range: -1.96 deg (open stop) to 45.72 deg (closing stop).
  - 0 deg is the simulation's q = 0 (open); 45.39 deg is q = 0.7 (closed).
- **Animation:** right-click `Servo_Horn` > **Animate Joint**, or ASSEMBLE >
  **Motion Study**.

After dragging, Fusion offers **Capture position** or **Revert**. Choose
**Revert** to keep the reference pose (q = 0).

Joint limits on `Servo_Horn`, `Pivot_O_L` and `Pivot_O_R` match the mechanical
stops. If you drag a finger very fast, the crank four-bar can jump to its other
branch. In that case Revert, or use Drive Joints.

| Joint | Between | Note |
|---|---|---|
| `Servo_Horn` | Crank - Servo | driver |
| `Pin_C`, `Pin_K` | Rod - Crank, Rod - InnerKnuckle:1 | crank-rod-ear four-bar |
| `Pivot_I_L/R`, `Pivot_O_L/R` | knuckles - Tower | base pivots |
| `Pivot_P1_L/R`, `Pivot_P2_L/R` | InnerFinger - OuterFinger / InnerKnuckle | parallelogram closures |
| `Fix_OF_*`, `Fix_Tip_*`, `Horn_Fix` | rigid | |
| Motion link `Gear_Sync` | `Pivot_O_L` <-> `Pivot_O_R`, 1:1 | represents the gear mesh (the teeth are real geometry) |

Grounded parts: Tower, HousingBox, Servo, SpacerA, SpacerB, CameraMount and
the D435i.

## Scripts (`scripts/`)

| File | Purpose |
|---|---|
| `design.py` | All numbers: URDF kinematics, layers, gears, drive, servo, wrist stack. |
| `parts.py` | Geometry of every part as prismatic features (single source of truth). |
| `check2d.py` | Fast layer-by-layer clearance sweep: `python scripts/check2d.py 30` must print `pairs with interference: 0`. |
| `viz2d.py` | Plots the layers at several poses (`layers.png`). |
| `fx.py` | Client for the Fusion360MCP add-in (TCP 127.0.0.1:9876). |
| `fbuild.py`, `fjoints.py`, `fprobe.py`, `fcheck.py`, `fexport.py` | Build the Fusion model, its joints and limits; sweep interferences; export STL. |
| `orient.py` | Orients the exported STLs for printing: `python scripts/orient.py scripts/raw print`. |
| `mlib.py`, `manual.py`, `manual_i18n.py` | LEGO-style PDF manual. `python scripts/manual.py out.pdf` gives Spanish; add `--lang=en` for English. |
| `raw/` | Component-space meshes exported from Fusion; used by `orient.py` and `manual.py`. |

### Rebuilding the Fusion model

1. Install and run the Fusion360MCP add-in (Shift+S > Add-Ins > Run). It listens
   on `localhost:9876`.
2. Create an empty design and save it as `HomeMade2F140_v2`.
3. Run these through `fx.py file ...` (it sets `HM_SCRIPTS` automatically). If
   you use `fx.py code "..."`, define `HM_SCRIPTS = r'<repo>\scripts'` first.
   - `exec(fbuild.py)`
   - `build_list([...])` for all parts in `parts.PARTS`
   - `build_hardware()`
   - `apply_colors()`
   - `exec(fjoints.py)`
   - `build_joints()`
   - `gear_link(False)`
   - `exec(fcheck.py)`
   - `set_limits()`
4. Verify with `sweep([...])`. Expect 0 interferences at every pose.

Fusion API pitfalls found while building:

- The first occurrence created in a design is `isGroundToParent=True`, which
  locks any loop it is in. The builder clears it.
- Build joint geometry from the parts' own hole edges, not from points in a
  root sketch.
- Deleted component names stay reserved inside a document. Rebuild in a fresh
  document.
- The add-in bridge times out after 30 s but Fusion keeps running the
  command, so poll instead of re-sending.
