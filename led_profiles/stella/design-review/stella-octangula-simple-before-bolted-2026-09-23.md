# Stella octangula with integrated simple cores

The selected, editable assembly is `StellaOctangula-Simple.FCStd`. It is a **separate** document; `../StellaOctangula.FCStd` and `../StellaCoreSimple.FCStd` were not replaced. It links four instances of `../StellaCoreSimple.FCStd` and four of the new native `StellaCoreSimple-Offset.FCStd`. Twelve 1500 mm lamp assemblies each contain aluminium, diffuser, two endcaps, two glands, and two cable stubs. The exact profile-component STEP shapes are imported as eight hidden **reference-only** `Part::Feature` objects in the assembly; no old arm or separate clamp instances remain.

## Approved layout

- The second tetrahedron keeps the previously accepted 30.75 mm outward face offset. Its separate integrated-clamp core has three saddle and clearance sections moved radially by `30.75 * sqrt(2/3) = 25.107270 mm`; the native organic web sketches were enlarged to join them. The offset core retains an editable Body, sketches, additive loft, pad, polar pattern, fillet, pocket, and final polar pattern. Its final tip is `ThreeChannelClearances`.
- Each lamp engages both integral-clamp ends equally with `StellaAssemblyParams.ClampInsertion = 40 mm`. `SideReduction = 2 * ClampInsertion = 80 mm`, so the tetrahedron side is `1613.330945 mm` rather than `1693.330945 mm`. Native `App::Link` placement-coordinate expressions refer to these assembly parameters; changing insertion updates both core and profile locations without rebuilding from a script.
- The offset core's `OffsetSeatRadial` drives the clamp and clearance-sketch positions. The organic web spline control points are native but fixed for the approved 30.75 mm crossing offset; changing that offset materially requires reshaping both web sections and rechecking the root fillet.

## Verification after save, close and reload

- Both core source Bodies have one valid solid and valid final tips. Offset core final volume: `190236.779230 mm^3`. Perturbing `OrganicStarParams.PrintFaceZ` from 68 to 68.5 mm changed its final volume, and restoring 68 mm restored the original geometry.
- Assembly has 104 valid `App::Link` instances: 8 cores plus 12 × 8 lamp components. All links resolve after reopening, with 8 hidden reference-only source features. No old arm/clamp links or duplicate printable Body objects are in the assembly document.
- Perturbing `ClampInsertion` from 40 to 39 mm increased `TetrahedronSide` by 2 mm and moved dependent core and lamp links; restoring 40 mm restored the measured placements before saving.
- At all 24 core/profile ends: aluminium distance `0`, **nominal intersection volume `68.878866 mm^3` per joint**; diffuser gap `1.25 mm`, endcap gap `0.56 mm`, gland gap `14.632925 mm`, cable-stub gap `40.807414 mm`, with zero intersection volumes for those latter four component classes. The aluminium intersection is an unresolved physical-fit/tolerance issue, not proof of a press or snap fit.
- All six opposed lamp crossings: combined aluminium/diffuser minimum distance `0.25 mm`, intersection volume `0`.
- Isometric, front, and top screenshots are adjacent to this note. They complement, not replace, the geometry measurements.

## Boundary

This is a native placement/layout assembly, not a manufactured-fit, print-tolerance, structural-strength, cable-routing, fastener, or electrical validation. In particular, the small aluminium/core collision should be resolved or deliberately qualified before fabrication.
