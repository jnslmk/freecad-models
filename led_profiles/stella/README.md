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
