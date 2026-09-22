# Suggested Stella model changes

> **Plan only — no model changes were made.** This file proposes later work on the
> authoritative `.FCStd` documents; it does not authorize deletion or replace
> any model evidence.

## Evidence and common gate

`research/stella-history-simplification.md` records valid, up-to-date Arm and
Clamp documents, but no proof that apparently duplicated printable solids are
equivalent. It also records that the Arm's degree-8 document-level
`Part::Loft` features match the source where `PartDesign::AdditiveLoft` did not.

Before any deletion, save a baseline and measure the current candidate and
replacement in the same recomputed document: requested overall dimensions,
volume, bounding box, mating clearances/interference, screw and insert centre
positions and diameters, and the assembly fit. Record the final Body tip and
native feature counts/types; inspect isometric and relevant section views.
Change one central `App::VarSet` value, confirm the dependent measurement,
restore it, then save, close/reload, and repeat the checks. Delete only when
those measurements and the printable-solid count show one authoritative,
equivalent result; keep explicit reference witnesses when they are not
printable.

## Stella Core

**Proposed change.** Rebuild the Core as one `CoreBody`: four constrained,
named organic-outline section sketches on named datum/origin planes at the four
source Z levels → AdditiveLoft; one radial-seat cut patterned three times; one
revolved suspension-bore profile/cut preserving the explicit R2 toroidal contact
at both mouths; and one six-circle insert-pilot sketch/pocket.

**Evidence.** The source uses a four-level six-segment outline, one seat tool,
one revolved suspension-bore tool, and six identical insert pilots
(`research/stella-history-simplification.md`, lines 13–14 and 38).

**Decision boundary.** Consolidate only repeated, identical operations. Retain
separate features when their parameter, operation type, or validation
measurement differs. Before replacing a feature, measure all three seat
locations, both suspension-bore axes and diameters, both R2 toroidal
mouth/contact radii, all six pilot centres/diameters, wall thicknesses at the
openings, and their assembly clearances.

## Stella Arm

**Proposed change.** Preserve the two document-level degree-8 `Part::Loft`
features and named section sketches. Simplify only downstream repeated work:
replace paired back-mouth/final-access cuts with one multi-centre
`PartDesign::Hole` when its standard geometry matches; make the keeper lands a
two-profile sketch plus one Pad; make the insert pilots a two-circle sketch plus
one Pocket or Hole.

**Evidence.** The Arm requires the degree-8 `Part::Loft` for source fidelity;
`PartDesign::AdditiveLoft` produced a materially different volume. Its root and
saddle contain the identified repeated cuts and lands
(`research/stella-history-simplification.md`, lines 30–38 and 62–64).

**Decision boundary.** Do not move the required `Part::*` lofts into a
PartDesign Boolean: keep them document-level and feed the final Body
BaseFeature. Reject the Hole replacement unless the existing and proposed
back-mouth, driver-access, screw, and insert measurements match exactly,
including lead/counterbore geometry and mating clearance. If they differ,
retain the targeted pockets/lofts.

## Stella Profile Clamp

**Proposed change.** Keep only reference envelopes and one authoritative
`ProfileClampBody`, whose intended tree is outer-profile sketch → Pad →
profile-opening Pocket → two-hole clearance feature. Remove a top-level
primitive chain only after it is shown to be a duplicate rather than a required
reference witness.

**Evidence.** The current clamp has a native final `ProfileClampBody` and also
retains reference-only `Part::Feature` witnesses plus top-level primitive
operations; the body already has the simpler four-step shape
(`research/stella-history-simplification.md`, lines 12 and 39, and inference at
line 62).

**Decision boundary.** Names do not establish redundancy. Before deletion,
compare the Body final Shape against the candidate primitives; measure profile
opening width/height and mating clearance, clamp wall thickness, both M3
clearance/counterbore centres and diameters, M3 × 8 screw-envelope clearance,
and assembled interference. Keep the top-level object if it supplies a
non-printable reference, a distinct validation measurement, or any result that
does not match the Body.
