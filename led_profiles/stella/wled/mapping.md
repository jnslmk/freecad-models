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

`gled2/stella_octangula.svg` and its embedded copy in `gled2/projects/` implement this
mapping as an elevation map for vertical scans: all three corners of each
level base share a Y coordinate. Base edges overlap in the SVG, so it is not a
perspective view; screen-left/right is a chosen layout, not a measured camera
orientation. GLED sends RGB over Art-Net universes 2–3 to STAR-TENT;
universe 3 begins at LED 170. For future rewiring, run `calibrate_stella.py`
with GLED closed and update both the SVG and the project's embedded SVG.

`gled2/stella_octangula.json` is a readable alias for the native GLED project.
GLED requires UUID filenames inside `gled2/projects/`, so keep that file in
place; the alias points to it rather than duplicating the project.

`beamhouse/stella_octangula.bhs` previews the same 12 electrical runs as 1.5 m
edges of two regular tetrahedra with level bases and pointed top/bottom.
Its horizontal rotation is illustrative, not a measured camera alignment.
GLED Art-Net Port-Addresses 2–3 arrive as Beamhouse universes 3–4; the
LED-170 split is inside T2-E2. The scene uses Beamhouse's built-in strip
geometry, with `iso` and `underside` camera views for the two bases.
