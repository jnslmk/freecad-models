# StellaCoreSimple — inner clamp channel clearance

The user identified a small web protrusion inside one clamp channel. The
unchanged pre-edit file is preserved as
`StellaCoreSimple-before-channel-clearance-20260923.FCStd`.

The native Body now adds one `Sketcher::SketchObject` semicircle matching the
existing clamp's nominal R13 inner channel, one `PartDesign::Pocket` through
the 30 mm grip length, and one `PartDesign::PolarPattern` for the other two
channels. The sketch follows the original saddle-section placement expressions;
the Pocket length follows `OrganicStarParams.SaddleLength`. No clamp radius,
outer web, flat print face, or assembly source was changed. The final Body tip
is `ThreeChannelClearances`.

The operation removed 27.892 mm³ total, about 9.297 mm³ per channel. After
recompute and save/close/reload, the Body remained one valid solid with volume
110144.884 mm³. All three nominal R13 channels have zero residual overlap.
The planar Z68 print face retained its 6506.477 mm² area. Changing
`PrintFaceZ` from 68 to 68.5 mm changed the final geometry; restoring 68 mm
restored the exact pre-test volume without rerunning a script.

Nominal comparisons against the unchanged profile references found
68.879 mm³ aluminium overlap per direction (down from 77.069 mm³ before the
clearance cut), no diffuser/endcap/gland/cable overlap, and minimum gaps of
1.25 mm to the diffuser and 0.56 mm to the near endcap. These are CAD checks,
not physical-fit, tolerance, grip-force, or strength validation.

See the sibling close-up, isometric, top and front PNGs. No print export was
updated.
