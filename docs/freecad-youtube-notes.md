# FreeCAD Video Notes

Source videos are from [Deltahedra](https://www.youtube.com/@Deltahedra3D). The notes below condense the practical workflow and configuration lessons from the four videos watched.

## Videos

1. [STOP using FreeCAD WRONG! Do this INSTEAD (Workflow & Tips)](https://www.youtube.com/watch?v=JjFh8vtMBC8) — workflow, stability, and interface advice.
2. [New to FreeCAD? Start HERE (Ultimate Beginner Tutorial)](https://www.youtube.com/watch?v=KmtqNaGPiiQ) — beginner Part Design tutorial modeling a bike stem.
3. [25 FreeCAD Hacks (You probably don't know)](https://www.youtube.com/watch?v=vwXklzvvxIA) — shortcuts, workarounds, and productivity tips.
4. [Engineers don't use FreeCAD... Until NOW!](https://www.youtube.com/watch?v=1tC7O7Dja40) — complete engineering workflow for a bicycle pedal.

The available transcripts were auto-generated captions, so occasional words may be mistranscribed.

## Core workflow

- Start ordinary solid modeling in **Part Design**.
- Use a **Body** as the container for sketches and features.
- Treat **Sketcher** as the foundation: dimensions and constraints define design intent.
- Fully constrain sketches where practical.
- Prefer origin planes and stable early geometry over faces produced by fragile late features.
- Build a simple base shape, then refine it with Pads, Pockets, Holes, Patterns, Mirrors, Fillets, and Chamfers.
- Use `Through all` when a cut should remain through-going after dimensions change.
- Use `Up to face` plus a face offset when a cut should track another surface.
- Use section view when a solid hides the sketch.
- Use external geometry for references, then convert projected geometry to construction geometry when it should guide rather than cut.
- Rename bodies and features as the tree grows.
- Save frequently.

## Part Design versus Part

Part Design keeps a feature history inside a Body and is the recommended starting point for beginners. Its additive and subtractive features modify the Body's solid.

The Part workbench creates separate solids and generally requires explicit Boolean operations. It remains useful for advanced workflows and mixed-workbench modeling, but it is not necessary for the initial learning path.

## Sketcher lessons

- Watch the constraint symbols near the cursor; automatic constraints can create redundancy unexpectedly.
- Use symmetry constraints and dimensions tied to axes instead of hard-coding unrelated distances.
- Use construction geometry for reference lines.
- Keep profiles as clean closed loops.
- For multiple closed profiles, FreeCAD 1.1's internal-face option can make selected profile faces available to Pocket operations.
- External geometry is useful for locating features on existing solids.
- Master sketches and variables can centralize important dimensions and drive multiple features or bodies.
- Avoid abrupt, large parameter changes in fragile models; change values incrementally.

## Stability and dependency management

- Fillets are among the most fragile operations. Apply them late when possible.
- When a 3D fillet is unstable, put the round directly into the sketch if that expresses the design correctly.
- Avoid attaching important sketches to faces created by fillets or other late operations.
- Use Set tip to insert a feature at an earlier point in a feature history, then restore the final tip afterward.
- Suppress a feature when testing alternatives instead of deleting it.
- Use SubShapeBinder to reference geometry from another Body without breaking Body isolation.
- For assemblies, create deliberate Local Coordinate Systems (LCS) at robust reference locations rather than relying only on automatically generated references.

## Add-ons and workbenches

- **Fasteners**: use standard bolts, nuts, inserts, and washers instead of modeling them manually.
- **Assembly4**: use LCS-based placement for robust assemblies and explicit part organization.
- **TechDraw**: create manufacturing drawings, thread callouts, tolerances, exploded views, and bills of materials.
- **Spreadsheet/variables**: use for parameter sets and configurable designs.
- **Curves**: useful for advanced surfacing and 3D curve workflows.
- **Draft Path Array** plus SubShapeBinder can solve path-pattern tasks that are awkward in Part Design.
- Add-ons should be installed when a project needs them, not preemptively.

## Interface and performance

- The Open theme was recommended for a cleaner interface.
- Keep only frequently used workbenches visible to reduce clutter.
- The navigation style is preference-dependent; consistency matters more than copying the author's exact choice.
- Render cache can remain on Auto.
- Anti-aliasing around 2–4 is a reasonable balance; higher settings cost performance.
- OpenGL VBO may help systems with suitable graphics hardware, but it should be tested rather than enabled blindly.
- Visibility can be toggled quickly with the Spacebar.
- Starting a Fillet tool before selecting many edges avoids losing the whole selection after a misclick.

## Engineering workflow demonstrated

The pedal project showed an end-to-end path:

1. Measure or reverse-engineer standard components.
2. Model custom and revolved parts parametrically.
3. Reuse standard hardware from Fasteners.
4. Prepare LCS references and assemble the parts.
5. Adjust the design while checking fit and clearances.
6. Create TechDraw drawings with dimensions, thread specifications, and tolerances.
7. Export manufacturing documentation.
8. Test critical printed fits with a small calibration coupon before printing the complete part.
9. Account for material behavior, shrinkage, press fits, wall thickness, infill, and print orientation.
10. Assemble and physically test the finished part.

The important lesson is that FreeCAD can cover design, assembly, documentation, manufacturing handoff, and validation when the model is built around stable references and explicit design intent.

## Practical beginner checklist

- [ ] Start in Part Design.
- [ ] Create a Body.
- [ ] Choose an origin plane deliberately.
- [ ] Fully constrain the first sketch.
- [ ] Prefer dimensions and symmetry over freehand placement.
- [ ] Use stable references and construction geometry.
- [ ] Rename important bodies and features.
- [ ] Delay fragile fillets.
- [ ] Use Fasteners for standard hardware.
- [ ] Add TechDraw when the part needs manufacturing documentation.
- [ ] Test critical fits before committing to a full print.
