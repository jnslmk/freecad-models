# Accepted Stella assembly and offset-core crossing fix

The authoritative `../StellaOctangula.FCStd` now uses the accepted 12 mm
core-seating layout with 24 clamps. The earlier main assembly is retained as
`StellaOctangula-before-12mm-acceptance.FCStd`; the accepted clamped working
copy remains `StellaOctangula-12mm-clamps.FCStd`.

The crossing solution follows the placement principle in
`../../../../build123d-models/models/led_profiles/assemblies/stella_octangula.py`
and `../../../../build123d-models/models/led_profiles/stella_core.py`, adapted
to the existing FreeCAD arm and organic core:

- Both tetrahedra now have equal **1693.330945 mm** sides and retain twelve
  **1500 mm** profiles.
- The offset tetrahedron's six edges move outward along their cube-face normals
  by **30.75 mm**. Four links use the original `StellaCore.CoreBody`; four use
  the new native `StellaOffsetCore.CoreBody`.
- The larger core's three seat/key/pilot clusters move radially by
  `EdgeOffset * sqrt(2/3)` = **25.107270 mm**. Its organic outline is enlarged
  for this nominal offset. `StellaParams.SeatCentreRadius` is expression-driven;
  the outline itself is a fixed editable sketch and must be revised if the
  offset is changed substantially.
- `create_stella_octangula.py` is the repeatable assembly generator. It checks
  source parameters, all 24 arm/core joints and clamps, 1500 mm spans, and all
  six aluminium/diffuser crossings. It refuses to overwrite an existing file.

## Verification

The generated assembly was recomputed, saved, closed, and reloaded at the main
path. All **152** links resolve: four base cores, four offset cores, 24 arms,
24 clamps, and 96 lamp-component links. No object reports `Error`; all linked
shapes are valid. Every arm/core pair has zero seating gap and zero volumetric
overlap; clamps have zero material overlap with arms, aluminium, and diffusers.
All six crossings have **0 mm³** material overlap and a minimum nominal
aluminium/diffuser clearance of **0.25 mm**. A full broad-phase pair audit of
the 128 non-cable physical links found no other material intersections except
the 24 modeled endcap/gland mating pairs. The offset core has one valid closed
native solid, tip `RadialSeatPattern`; a small `EdgeOffset` perturbation moved
the dependent seats/pilots, was restored, and survived save/reload.

Isometric, front, and top FreeCAD views were inspected after the change.
The diagnostic screenshots are not retained in Git; the native documents and
recorded measurements remain the durable evidence.

## Still unresolved

The axial cable stubs still intersect the arms by up to **316.417 mm³** and
`CableRouteClear` remains `False`. The 0.25 mm crossing gap is a CAD nominal
clearance, not a physical print-fit or installation tolerance. Physical fit,
print orientation/supports, staged assembly access, and suspended-use strength
remain unverified.
