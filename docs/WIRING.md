# Servo wiring

The selected DFRobot servo uses a PWM command and a separate high-current
6.0-8.4 V supply.

1. Connect servo power directly to a regulated supply/BEC capable of the
   measured peak current.
2. Connect servo ground to supply ground.
3. Connect controller ground to the same ground.
4. Connect the PWM signal to the controller output.
5. Begin testing at 6 V with a conservative current limit and reduced command
   range; expand the range only after mechanical end stops are verified.

DFRobot specifies a 500-2500 microsecond command span for 180 degrees. Software
limits must be calibrated to the assembled mechanism rather than assuming the
full electrical range is mechanically safe.

