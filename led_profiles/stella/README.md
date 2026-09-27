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

[`wled/stella-gled2.svg`](wled/stella-gled2.svg) projects the two tetrahedra
into a six-pointed star: 12 paths × 23 pixels, grouped by `all`, `tetra1`,
`tetra2`, and electrical edge. The native **Stellar scan** project is in
[`wled/gled2/projects/`](wled/gled2/projects/) with its Art-Net device in
[`wled/gled2/output_devices/`](wled/gled2/output_devices/). Synchronized soft
cyan and ember bands sweep from top to bottom across the two tetrahedra at
35% output.

For GLED2 2.28.5, copy those two JSON files into the matching
`~/.local/share/gled2/` asset directories (keep the filenames), restart GLED,
and load **Stella / Stellar scan**. GLED needs its standard asset library for
the built-in Stripes 2.0 animation and Linear curve. GLED starts in blackout;
turn **Blackout** off and check that both scene tiles show green pause icons
(click play on either inactive tile). Otherwise only one tetrahedron scans.
The project embeds the SVG; after changing the standalone SVG, reimport it
into the project. Output routes GLED universes 2–3 to STAR-TENT's
Art-Net universes 2–3 (`192.168.8.243:6454`). WLED uses Multi RGB
starting at DMX channel 1; universe 3 begins at LED 170. This setup
does not edit saved WLED
presets; WLED resumes its preset after the realtime stream stops.

The measured LED ranges, endpoint directions, and tetrahedron corner
pairings are recorded in [`wled/mapping.md`](wled/mapping.md). That mapping
is embedded in the GLED project via `wled/stella-gled2.svg`.

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
