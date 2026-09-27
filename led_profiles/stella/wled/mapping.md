# Stella LED-to-vertex mapping

Measured with `calibrate_stella.py`: green marks each run's first three LEDs,
magenta its last three. Every run has 23 WS2811 pixels. GPIO16/T1 is the
upward-pointing tetrahedron (LEDs 0–137); GPIO4/T2 points down (138–275).

Each tetrahedron has one apex and a level triangular base. A base corner is
named for the sloping edge that joins it to that tetrahedron's apex. These
names specify electrical connectivity without assuming a camera viewpoint.

| Run | GPIO | LED range | First LED (green) | Last LED (magenta) |
| --- | --- | ---: | --- | --- |
| T1-E1 | 16 | 0–22 | E1 base corner | top apex |
| T1-E2 | 16 | 23–45 | top apex | E2 base corner |
| T1-E3 | 16 | 46–68 | E2 base corner | E1 base corner |
| T1-E4 | 16 | 69–91 | E1 base corner | E6 base corner |
| T1-E5 | 16 | 92–114 | E6 base corner | E2 base corner |
| T1-E6 | 16 | 115–137 | top apex | E6 base corner |
| T2-E1 | 4 | 138–160 | bottom apex | E1 base corner |
| T2-E2 | 4 | 161–183 | E1 base corner | E5 base corner |
| T2-E3 | 4 | 184–206 | E5 base corner | E4 base corner |
| T2-E4 | 4 | 207–229 | E4 base corner | bottom apex |
| T2-E5 | 4 | 230–252 | bottom apex | E5 base corner |
| T2-E6 | 4 | 253–275 | E4 base corner | E1 base corner |

`stella-gled2.svg` and its embedded copy in `gled2/projects/` implement this
mapping. Screen-left/right is a chosen projection, not a measured camera
orientation. GLED sends RGB over Art-Net universes 2–3 to STAR-TENT;
universe 3 begins at LED 170. For future rewiring, run `calibrate_stella.py`
with GLED closed and update both the SVG and the project's embedded SVG.
