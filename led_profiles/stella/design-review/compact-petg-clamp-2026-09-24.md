# Compact PETG clamp — selected reversible assembly, pending print fit

The user specified **M3 4 × 5 mm heat-set inserts** and permitted a change to
the tetrahedron edge length. This selected native variant is stored in the
parent `stella/` directory; the
pre-existing `StellaCoreSimple.FCStd`, `StellaProfileClamp.FCStd`, and
`StellaOctangula-Simple.FCStd` files were not overwritten.

## Native concept files

- `../StellaCoreSimple-Compact-PETG.FCStd`: 12 mm axial saddles instead of 30 mm;
  12 × 12 mm square paired bosses instead of round Ø9 bosses; six blind M3
  insert pilots, Ø3.8 × 5.5 mm, from the accessible mating faces. Native pad,
  pocket and polar-pattern features remain, with a valid single-solid Body tip.
  The rounded web B-spline sections are scaled to 90% as a reversible concept.
- `../StellaCoreSimple-Offset-Compact-PETG.FCStd`: equivalent 12 mm saddle/boss/
  pilot operations for the offset core, with its larger web scaled to 94% to
  retain a one-solid fusion.
- `../StellaProfileClamp-Compact-PETG.FCStd`: the existing 12 mm counter-clamp with
  a fully constrained native opening sketch. Its inner arch radius is driven by
  `StellaClampParams.NominalPreload = 0.1 mm`, yielding R12.95 instead of R13.15.
  It intentionally produces nominal diffuser contact. The user confirmed that
  slight diffuser clamping is permitted.
- `../StellaOctangula-Simple-Compact-PETG.FCStd`: a separate native assembly
  linked to the three concept sources above. It has 8 core links, 24 counter-
  clamp links and the original 12 full lamp assemblies. The previously selected
  simple assembly remains unchanged.

Ø3.8 mm is only a starting CAD pilot for the user's nominal Ø4 mm insert, not
a verified PETG fit. Actual inserts and print settings need a test coupon.
[CNC Kitchen's insert study](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong)
shows that printed hole size and best pilot diameter depend on the specific
insert and print process.

## Native geometry and assembly verification

After save/close/reload, all three concept Bodies were valid single solids with
valid final tips and no invalid/error-state objects. Base and offset core tip
volumes were respectively 89,258.318 and 166,862.479 mm³. Perturbing
`OrganicStarParams.PrintFaceZ` from 68 to 68.5 mm changed each Body volume;
restoring 68 mm restored the originals. The counter-clamp's named arch-radius
constraint likewise responded to `NominalPreload` 0.10 → 0.15 → 0.10 mm.

The separate assembly was saved, closed, reloaded and checked again. With
`ClampInsertion = 45 mm`, the tetrahedron side is **1603.330945 mm**, 10 mm
smaller than the prior simple assembly and 90 mm below the original reference
side. Perturbing insertion to 44 mm increased the side by exactly 2 mm and
moved the native dependent links; restoring 45 mm restored the placements.

All **24 joints**: cap/boss distance 0 and overlap 0; both M3 clearance axes
align with their insert-pilot axes; core/aluminium minimum gap 0.15 mm with no
overlap; cap/aluminium nominal overlap 0.916518 mm³; and the approved light
cap/diffuser nominal overlap 159.357186 mm³. Neither core nor cap intersects
its adjacent endcap: minimum gaps are respectively 1.527351 and 4.110170 mm.
At all six opposed profile crossings, the aluminium/diffuser combined gap is
0.25 mm with zero overlap. The linked objects remained valid after reload.

Native-model section and isometric FreeCAD GUI views were inspected: the cap
arch contacts the diffuser above the aluminium cradle. All
assembly `App::Part` and `App::Link` objects intended for display were visible
after GUI save/reload; hidden reference-only source features remain hidden.
Diagnostic screenshots are not retained in Git; these visual checks supplement,
not replace, the measured geometry.

This is **nominal CAD squeeze, not verified grip force or physical fit**. Print
a PETG pilot coupon with the actual insert and a clamp/profile/diffuser test
piece before fabricating all parts. Verify installed M3 screw length and insert
bottom clearance; the old M3 × 8 screw envelope has not been qualified for the
new 4 × 5 mm insert stack.

The FreeCAD MCP client tools were unavailable in this session. Native documents
were edited and checked with FreeCAD 1.1.3 Python in isolated processes; the
core and full assembly were additionally inspected in FreeCAD GUI isometric
views. Native links and all joint/crossing distances were checked after reload.
