# Third-party notices and trademarks

## Robotiq 2F-140 kinematic parameters

The finger kinematics of this gripper reproduce the public ROS description of
the Robotiq 2F-140, so that the printed gripper matches existing simulations:

- base pivot positions;
- link offsets and joint origins;
- joint range of `finger_joint`.

Only these numerical parameters are used, in `scripts/design.py`. No Robotiq
meshes, drawings or other files are included in this repository. All part
geometry was designed from scratch for this project.

The description these parameters come from is distributed under the following
license:

```
BSD 3-Clause License

Copyright (c) 2026, Robotiq
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Purchased components

The servo (DFRobot SER0062 / D5545GS) and the RealSense D435i camera are
commercial products that you buy separately. In this repository they appear
only as simplified envelope blocks drawn from their published outer
dimensions. No manufacturer drawings or CAD files are included.

Standard interfaces used:

- ISO 9409-1-50-4-M6 robot flange pattern;
- ISO 4762 / ISO 10511 / ISO 7089 fasteners.

## Trademarks

These names are trademarks of their respective owners:

- Robotiq and 2F-140: Robotiq Inc.
- Universal Robots, UR10 and UR10e: Universal Robots A/S.
- DFRobot: DFRobot.
- Intel and RealSense: Intel Corporation.
- Autodesk and Fusion: Autodesk, Inc.

They are used here only to describe compatibility and the components used.
This project is independent and is not affiliated with, sponsored by or
endorsed by any of these companies.
