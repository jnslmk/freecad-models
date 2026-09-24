# StellaCoreSimple — rounded clamp transition

Historical stage before the subsequent inner-channel clearance; see
`channel-clearance-2026-09-23.md` for the current Body tip.

The post-crash `StellaCoreSimple.FCStd` saved at 20:24 was newer than its 20:22
`.FCBak` and reopened as one valid native solid. Its untouched pre-edit state is
preserved as `StellaCoreSimple-before-clamp-sweep-20260923.FCStd`.

The three grips were moved 5 mm **along their angled profile axes**, in the
direction marked by the user (`OrganicStarParams.ProfileEndShift`: 40 → 35 mm).
The two editable web sketches now use six blocked B-spline curves each: three
inward-bowed sides and three rounded ends. `OrganicWebLoft` sweeps between them;
the planar Z = 68 mm print face remains. The six saddle/web seams have a native
2 mm `PartDesign::Fillet`. `OrganicRootBlend` remains the sole Body tip.

After recompute and save/close/reload: all objects reported valid, the Body has
one solid (110172.776 mm³), and the single planar print face is 6506.477 mm².
Changing `PrintFaceZ` from 68 to 68.5 mm changed the geometry; restoring 68 mm
restored the original volume without running an external builder. For each of
the three mating directions, the nominal aluminium engagement was 77.069 mm³;
the diffuser, near endcap, near gland and near cable had zero overlap. The
minimum nominal gaps were 1.25 mm to diffuser and 0.56 mm to near endcap.

The highest saddle rim is at Z = 67.856 mm, 0.144 mm below the flat print face.
An exact-Z prototype was possible but its seam fillet lost validity when the
print-face height changed. The user chose to retain this robust, parametric
version rather than pursue strict geometric coincidence.

See the sibling isometric, top and front PNGs. These are nominal CAD checks,
not verification of print tolerance, grip force, structural strength or
physical fit. No assembly model or print export was changed.
