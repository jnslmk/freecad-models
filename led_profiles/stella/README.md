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

Presets: 1 **Android** (original effect, segment normalized to ID 0); 2 **Stella Android** (boot);
3 **Tetra Breathe**; 4 **Rainbow Flow**; 5 **Edge Meteor**;
6 **Edge Scanner**; 7 **Twinkle Gold**; 8 **Fireworks**; 9 **Warm Glow**;
10 **Night Light**; 11 **Theater Rainbow**; 12 **Off**. Loading preset 1
restores the original one-segment layout; loading 2–11 restores all 15 segments.
Preset 12 turns the output off without changing the current segment layout.
Edge numbers follow electrical chain order, not geometric edge labels; verify
physical edge order and direction visually.
