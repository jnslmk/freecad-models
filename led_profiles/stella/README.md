# Stella models

The selected compact PETG assembly is [`StellaOctangula.FCStd`](StellaOctangula.FCStd).
It links the following native source documents in this directory:

- [`StellaCore.FCStd`](StellaCore.FCStd) — four base cores
- [`StellaOffsetCore.FCStd`](StellaOffsetCore.FCStd) — four offset variants of the integrated organic `StellaCore` saddle, with the 30.75 mm crossing offset
- [`StellaProfileClamp.FCStd`](StellaProfileClamp.FCStd) — 24 counter-clamps

The assembly also contains its profile components and 96 internal links. Keep
these four `.FCStd` files together so the relative external links resolve.

All 24 counter-clamps are positioned on the corresponding core's M3 through-hole axes.
Both core variants have through M3 heat-insert holes for longer screws. The
offset core retains its native web, transition loft, and integrated saddles;
its old separate bosses and channel cuts are gone.

Earlier review files were removed from the working tree; tracked versions remain
available in Git history.

`create_stella_octangula.py` is a legacy generator for the earlier arm-based
assembly. It does not rebuild this selected compact model.

**Fabrication is not yet validated:** PETG insert fit, clamping force, screw
length, and sustained load still need physical tests.

## Lighting (WLED)

Controller **STAR-TENT**: `http://wled-a52a34.local/` (observed at
192.168.8.243). WLED 16.0.1 drives 276 WS2811 elements on two data lines:
GPIO16 serves LEDs 0–137 (tetra 1), and GPIO4 serves LEDs 138–275 (tetra 2).
Each line has six consecutive runs of 23 elements.

Segments 0–5 are `T1-E1` through `T1-E6`; segments 6–11 are `T2-E1` through
`T2-E6`. Segment 12 spans tetra 1, segment 13 spans tetra 2, and segment 14
spans the whole star. The three overview segments overlap the edge segments
and are disabled in edge presets.

Presets: 1 **Android** (original effect, segment normalized to ID 0);
2 **Stella Android** (boot); 3 **Tetra Breathe**; 6 **Edge Scanner**;
7 **Twinkle Gold**; 8 **Fireworks**; 9 **Warm Glow**; 10 **Night Light**;
11 **Theater Rainbow**; 12 **Off**; 13 **Edge Relay**. IDs 4 and 5 are unused
in the saved snapshot. Loading preset 1 restores a single-segment layout;
loading 2, 3, 6–11, and 13 restores all 15 segments. Preset 13 disables the
individual edges and uses Scan on the all-star segment with groups of 23 LEDs,
so successive electrical-chain edges light as units, alternating blue and red.
It requires [`wled/palette0.json`](wled/palette0.json) on the controller as
custom palette 200; upload that file before restoring `wled/presets.json`.
Preset 12 turns the output off without changing the current segment layout.
Tetra Breathe uses synchronized, opposite-direction fades: tetra 1 cyan and
tetra 2 magenta trade brightness while their 12 edge segments stay disabled.
Presets retain WLED's transition setting. Stella Android includes a one-shot
zero-duration switch (`tt:0`), but an orange flash has still been reported
when loading it from the web UI.

[`wled/current-preset.json`](wled/current-preset.json) is a standalone snapshot
of the active scene, not a complete `/presets.json` restore file.

Edge numbers follow electrical chain order, not geometric edge labels; verify
physical edge order and direction visually.

### GLED2 spatial show

[`wled/gled2/stella_octangula.svg`](wled/gled2/stella_octangula.svg) is an
elevation-only map of 12 paths × 23 pixels, grouped by `all`, `tetra1`,
`tetra2`, and electrical edge. Its Y coordinates match the native CAD
diffuser's equal-bin pixel centres in the Beamhouse preview; horizontal
X is illustrative, not perspective or measured azimuth.
The native **Exhibition loop** project is in
[`wled/gled2/projects/`](wled/gled2/projects/), with its editable WGSL animation
in [`wled/gled2/animations/`](wled/gled2/animations/). Seven individually editable
animation tiles cycle at 35% output: **Edge build**, **Tetra breath**, **Edge chase**,
**Stellar scan**, **Vertex echoes**, **Counterflow**, and **Aurora**. They share one
WGSL pattern asset, with each tile selecting its own fixed pattern and twelve
mapped edge effects. Each tile lasts 40 seconds, including a six-second smooth
crossfade into the next; the 4 minute 40 second sequence repeats without resetting
incoming animation phases. The original two scan tiles remain available,
disabled during exhibition playback, in the expanded 3 × 3 grid.

Run with the installed GLED2 2.28.5 and its standard asset library:

```sh
python wled/gled2/exhibition.py                 # localhost preview only
python wled/gled2/exhibition.py --live          # exhibition output to STAR-TENT
python wled/gled2/exhibition.py --mode chase    # inspect one animation
python wled/gled2/exhibition.py --hold 60 --transition 8 --live
```

The stdlib runner starts GLED, restores the project, waits for all seven
twelve-edge tiles, releases startup blackout, and supplies a local 30 Hz OSC clock.
It cycles native tile activation and complementary scene opacities; only the
current and incoming tiles render during a fade. GLED's native beat curves repeat
every four beats, so the runner is required for real-time animation and cycling;
opening the JSON alone does not run the show. `--mode chase` runs only Edge chase.
Close GLED or press Ctrl-C in the runner to stop. No separate playlist server
or modified GLED executable is needed. This is unattended playback, not an
OS-level locked-down kiosk or login autostart configuration.

The runner uses an isolated home and asset repository under
`~/.local/state/stella-exhibition/`; personal GLED projects/settings are not
overwritten. `--profile PATH` selects another isolated profile. Do not launch
two instances on the same OSC port (default 18765), save the running clock
into the native project, or run a second stream to the sculpture.
`--duration SECONDS` and `--start-at SECONDS` support bounded inspections.
The isolated copy derives each edge's shader endpoints from the embedded
SVG at startup, preserving CAD elevation updates and electrical direction.
Sloping chases run physically low-to-high; level base chases follow the
recorded first-to-last direction. Separate edge groups prevent overlapping
elevation paths from being mistaken for the same tube.

The show includes the existing **Colorful → Blurple** palette in
[`wled/gled2/palettes/`](wled/gled2/palettes/) and uses its purple/cyan colors by
default. The runner also imports every palette from the personal GLED asset
library into the isolated profile without overwriting existing palette edits.
Switch colors by selecting a palette in the project's palette tree. To edit one,
open **Assets → Palettes**, adjust **Primary color** or **Secondary color**, click
**Save**, then reselect that palette in the project (GLED copies colors on selection).
Leave **Overwrite Palette** unchecked for tiles that should follow the project colors.

Preview output goes only to `127.0.0.1:6454`; open
`wled/beamhouse/stella_octangula.bhs` in Beamhouse to view it.
`--live` instead routes GLED universes 2–3 to STAR-TENT's Art-Net universes
2–3 (`192.168.8.243:6454`). WLED uses Multi RGB starting at DMX channel 1;
universe 3 begins at LED 170. Neither mode edits saved WLED presets or
controller configuration; WLED resumes its preset after the realtime stream stops.

The dependency-free scheduler regression can also run without GLED or a GPU:

```sh
python wled/gled2/check_exhibition.py --schedule-only
```

For a development-only GPU behavior check (requires a GLED source checkout):
```sh
uv run --with wgpu python wled/gled2/check_exhibition.py --gled-source /path/to/gled2
```

This executes the actual WGSL on all 276 mapped samples and checks edge
sequencing, reciprocal fades, chase direction, connected vertex echoes, RGB
bounds, native tile pattern selection, and scheduled RGB arithmetic. Scheduler
checks cover all seven tile boundaries, complementary smoothstep weights, wrap,
midfade starts, and fixed modes. These checks do not exercise GLED's native output
mixer or physical LEDs. The playback runner itself has no Python dependencies.

The measured LED ranges, endpoint directions, and tetrahedron corner
pairings are recorded in [`wled/mapping.md`](wled/mapping.md). That mapping
is embedded in the GLED project via `wled/gled2/stella_octangula.svg`.

To identify the actual wiring, close GLED and run
`python wled/calibrate_stella.py` from this directory. It streams one dim run
at a time: **green** marks the first three LEDs and **magenta** the last three.
On a horizontal edge, four LEDs at each sloping edge's base corner also light
up: **blue/yellow/cyan** identify T1-E1/E2/E6 or T2-E1/E4/E5, respectively.
Record which corner color meets each end of the horizontal edge; no camera
orientation is required. Press Enter for the next edge.
Press `q` to stop; no WLED preset or LED configuration is written. If
rewired, update the SVG paths and reimport the project into GLED.
Do not run the probe alongside a GLED stream.

### Beamhouse native CAD preview

Load [`wled/beamhouse/stella_octangula.bhs`](wled/beamhouse/stella_octangula.bhs)
with its sibling `meshes/` directory intact. The body assets contain the
selected CAD extrusion, endcaps, glands, cable stubs, integrated vertex cores
and clamps; separate diffuser assets receive RGB along electrical first→last
+X. All 128 visible native link instances occur once. These are derived
meshes, not changes to the authoritative CAD or WLED presets.

`wled/beamhouse/export_stella.py` exports the saved assembly and its linked
sources read-only; it does not run the legacy CAD generator, rebuild geometry,
or save any native document. It rewrites only the derived GLBs, scene's
asset/definition/placement fields, provenance manifest, GLED SVG elevation
and native project's embedded SVG. Other project effects and routes remain
unchanged. Mesh exports are staged and validated before publication;
a failed mesh export leaves live assets intact.
Publication is atomic per file, not across the bundle: do not load the scene
concurrently with regeneration. With FreeCAD Python modules installed,
regenerate and check from this directory:

```sh
PYTHONPATH=/usr/lib/freecad/lib /usr/bin/python wled/beamhouse/export_stella.py
PYTHONPATH=/usr/lib/freecad/lib /usr/bin/python wled/beamhouse/export_stella.py --check
PYTHONPATH=/usr/lib/freecad/lib /usr/bin/python wled/beamhouse/export_stella.py --sync-svg
python wled/test_gled2_mapping.py
```

The module path above is this workstation's installation; adjust it elsewhere.
The read-only check reports source hashes, component ownership, mesh integrity,
dimensions and universe mapping. Electrical corner names, vertical alignment,
and the unavoidable unmeasured azimuth/LED-centre choices are documented in
[`wled/mapping.md`](wled/mapping.md). Meshes use 0.2 mm CAD tessellation
deflection, Z-up local coordinates and metres; the exporter compensates the
loader's shared body/diffuser centering so owning a connector cannot shift a
profile out of its native assembly position.
