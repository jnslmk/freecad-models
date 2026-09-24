# Stella octangula — integrated cores with bolted counter-clamps

The current editable assembly is `StellaOctangula-Simple.FCStd`. It contains four links to `../StellaCoreSimple.FCStd`, four links to `StellaCoreSimple-Offset.FCStd`, twelve complete 1500 mm lamp assemblies (eight exact components each), and **24 links to the existing native M3 `../StellaProfileClamp.FCStd` counter-clamp**. No legacy arm instances are present. The eight imported STEP source shapes in the assembly are hidden, reference-only `Part::Feature` objects. The accepted `../StellaOctangula.FCStd` and the clamp source were not changed.

Before this revision, copies were saved as `StellaCoreSimple-before-bolted-clamps-20260923.FCStd`, `StellaCoreSimple-Offset-before-bolted-clamps-20260923.FCStd`, `StellaOctangula-Simple-before-bolted-clamps-20260923.FCStd`, and `stella-octangula-simple-before-bolted-2026-09-23.md`.

## Native design

- The lower channel of each integrated saddle is opened by the existing native `ClampChannelPocket` plus threefold pattern. Its editable Sketcher profile now has a fixed lower R13.2 arc and a 16.5 mm open mouth. Against the exact aluminium extrusion's 13.05 mm half-width, it gives a **0.15 mm nominal minimum CAD gap**, replacing the prior 68.878866 mm³ collision at every end.
- Each core Body adds one two-circle boss sketch and native Pad, patterned threefold, plus one two-circle Ø3.3 mm hole sketch and native Pocket, also patterned threefold. The boss and bore sketches have six named constraints each and follow `OrganicSaddleSection` through placement expressions. `OrganicStarParams` drives the M3 pitch (40.17 mm), boss radius (4.5 mm), bore diameter (3.3 mm), boss depth (10 mm), and axial hole station (13 mm). The Body tip is `ThreeFastenerThroughPairs`.
- Each separate cap is the existing `ProfileClampBody`, with two counterbored Ø3.25 mm M3 clearance holes. Cap link placements stay registered to their core bosses through expressions on `StellaAssemblyParams.SideReduction`.
- The approved `ClampInsertion = 40 mm` and `SideReduction = 80 mm` retain a `1613.330945 mm` side for both tetrahedra. The second tetrahedron retains its 30.75 mm outward crossing offset and its distinct native offset core. Both core variants still have a planar Z68 print face and the organic web-to-saddle transition.

## Recompute and saved/reloaded geometry checks

All three changed documents were saved, closed, reopened, recomputed, and checked without broken links or invalid objects. The assembly has **128 valid `App::Link` instances**: 8 cores + 96 lamp components + 24 counter-clamps. The two core Bodies each have one valid solid. Their final volumes are approximately 112349.92549 mm³ (base) and 192441.80087 mm³ (offset).

At **each of 24 ends**, `distToShape` and `common(...).Volume` give:

| Interface | Minimum nominal gap | Intersection volume |
| --- | ---: | ---: |
| Core / aluminium | 0.150000 mm | 0 mm³ |
| Core / counter-clamp boss face | 0 mm | 0 mm³ |
| Counter-clamp / aluminium | 0.083926 mm | 0 mm³ |
| Counter-clamp / diffuser | 0.083926 mm | 0 mm³ |
| Core / diffuser | 1.258968 mm | 0 mm³ |
| Core / near/far endcap | 0.760000 mm | 0 mm³ |
| Core / gland | 14.729647 mm | 0 mm³ |
| Core / cable stub | 40.855171 mm | 0 mm³ |
| Counter-clamp / endcap | 4.260117 mm | 0 mm³ |

All 24 pairs of counter-clamps sharing a vertex remain separate, and all six opposed aluminium/diffuser crossings retain **0.25 mm gap and zero overlap**. Counter-clamps have no overlap with the other checked lamp components.

For both core sources, perturbing `PrintFaceZ`, `ProfileEndShift`, `FastenerPitch`, and `FastenerBossDepth` changed the dependent native geometry and restored a valid solid at the original values without rerunning a builder. Perturbing assembly `ClampInsertion` from 40 to 39 mm moved core, lamp, and counter-clamp links while keeping the cap registered to its boss; restoring 40 mm restored the original side and placements.

Isometric, front, top, and joint-closeup views were inspected. Their diagnostic
screenshots are not retained in Git; the native documents and measurements above
remain available.

## Important mechanical boundary

This resolves **nominal rigid-body collisions**, not structural retention. The existing cap has about 0.084 mm clearance to the aluminium and diffuser, while the lower saddle has 0.15 mm clearance to aluminium; tightening the cap to the boss face therefore does **not** establish a calculated friction preload. Bolts and nuts are required but are not modeled. Exact fastener length, nut access, profile axial stops, material/print orientation, assembly tolerances, sustained load, heat, fatigue, and any overhead safety requirement must be verified before fabrication or use. The counter-clamp is a mechanically closed concept, not a certified load-bearing joint.
