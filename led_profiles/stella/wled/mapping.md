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
mapping as an elevation map for vertical scans. SVG Y is derived from the
actual exported diffuser centreline after Beamhouse's shared centering and
fixture transform, not from ideal connector vertices. All horizontal runs
remain level; sloping profile ends do not meet horizontal profile ends
because CAD roll/offsets and inset sample centres are preserved. It is not a
perspective view; screen-left/right is a chosen layout, not measured azimuth.
GLED sends RGB over Art-Net universes 2–3 to STAR-TENT;
universe 3 begins at LED 170. For future rewiring, run `calibrate_stella.py`
with GLED closed and update both the SVG and the project's embedded SVG.

`gled2/stella_octangula.json` is a readable alias for the native GLED project.
GLED requires UUID filenames inside `gled2/projects/`, so keep that file in
place; the alias points to it rather than duplicating the project.

`beamhouse/stella_octangula.bhs` previews the selected native
`StellaOctangula.FCStd` assembly, not idealized cylinders. Its 12 profiles
retain their 1500 mm length, roll, end hardware, 30.75 mm crossing offsets,
eight integrated connector cores and 24 clamps. Each core is exported only
with the first electrical run incident to its vertex; each clamp belongs
to its own profile. Per-run body/diffuser GLBs keep texture +X pointing
from the recorded first vertex to the last.

The whole CAD assembly is rigidly rotated: room up is CAD `(1,1,1)/sqrt(3)`,
room right is `(1,-1,0)/sqrt(2)`, and room depth is `(-1,-1,2)/sqrt(6)`.
Base CAD vertex 0 becomes the top apex; offset CAD vertex 1 becomes the
bottom apex. The native core placements give level bases while actual
profile offsets remain intact. Horizontal rotation and correspondence
between named corners and native CAD vertex labels are illustrative:
azimuth was not measured. CAD contains no individual LED centres, so 23
equal texture bins cover each diffuser; their physical pitch/end inset
is not claimed as measured.

GLED's `leds_on_path` samples 23 points including both SVG path endpoints
(`path_length / (23 - 1)`); therefore those endpoints represent the first
and last equal diffuser-bin centres, at local fractions `0.5/23` and
`22.5/23`, not the ends of the material. Every intermediate SVG sample then
matches the same Beamhouse bin centre. The global sampled world-Y range
`-953.726761..935.973237 mm` maps inversely to SVG Y `378..22`.
T1 sloping material ends span `-262.146746..962.598125 mm` and its horizontal
diffusers lie at `-347.656071 mm`; T2 sloping ends span
`-980.351650..244.393221 mm` and its horizontal diffusers lie at
`365.409583 mm`. These are derived CAD visualization coordinates, not
physical LED-centre measurements. `mesh_provenance.json` records all 276
chosen sample heights. Run `beamhouse/export_stella.py --sync-svg` to update
only the SVG, its native project's embedded copy and elevation provenance
from existing meshes; full export performs this synchronization too.

GLED Art-Net Port-Addresses 2–3 arrive as Beamhouse universes 3–4; the
LED-170 split remains inside T2-E2. Use `iso` and `underside` camera views
for the two bases. `beamhouse/mesh_provenance.json` records every native
instance, linked source, vertex direction, source hash and exported asset.
