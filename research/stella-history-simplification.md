# Stella creation, simplification, and native-feature findings

**Scope.** Read-only review on 2026-09-22 of the current repository, accessible retained session records, Git history, source geometry, and the live FreeCAD session. No model was changed.

## Observed evidence

### History and current artifacts

- Git records four Stella milestones: initial import (`c592fc5`), assembly-rebuild hardening (`435d2ab`), clamp creation (`dba4fbb`), and `refactor(stella): simplify profile clamp tree` (`d3e3281`). The last commit changes only the binary `led_profiles/stella/StellaProfileClamp.FCStd`; its object-level simplification cannot be recovered from the Git diff.
- The original reconstruction first produced static `Part::Feature` BREP results with no editable operation history (`memory://5f92e2cf9e5c72a8`, assistant response 4). A later retained record documents the current editable Arm graph: `ConnectorBody` plus document-level `Part::Loft`/Sketcher sections, `Part::MultiFuse`, then `ArmBody.BaseFeature` and downstream PartDesign operations (`memory://6b5b8a630dbe2a1d`, paragraph 1).
- The live `StellaArm` document is loaded from `led_profiles/stella/StellaArm.FCStd`. Its `ArmBody` tip is `DriverAccess`; its feature tree contains 20 Sketcher section/profile objects, two `PartDesign::AdditiveLoft`, three `PartDesign::SubtractiveLoft`, eight downstream PartDesign operations (three Pads and four Pockets plus one SubtractiveLoft), two document-level `Part::Loft`, and one `Part::MultiFuse`. All inspected modeled objects are `Up-to-date`, their Shapes are valid, and the document has no object in `Error` state. This was a non-mutating MCP inspection.
- The loaded clamp presents both reference-only `Part::Feature` witnesses and a native `ProfileClampBody`; its visible final tree is `ClampOuterProfile` → `ClampPad` → `ProfileOpeningPocket` → `CounterboredM3Clearance`. It also retains document-level primitive operations such as `OuterProfileArch`, `InnerProfileClearance`, `LowerArchCut`, and individual mating-foot/screw-boss primitives. `M3ScrewEnvelopes` identifies clamp-side M3 × 8 insertion into arm heat-set inserts. (Live MCP object inspection, 2026-09-22.)
- The source arm is intentionally complex: it builds a ruled shoulder/key loft and individual root bores (`../build123d-models/models/led_profiles/stella/arm.py:78-164`), generates a profile-following U-section from lines and arcs (`:202-327`), lofts seven transition sections and seven root-blend sections (`:330-361`), then joins them and applies the saddle/cuts (`:364-460`). Its final build fuses root/saddle and subtracts final access tools (`:481-499`).
- The source core is much more compressible: one six-segment organic outline is lofted through four Z levels (`../build123d-models/models/led_profiles/stella/core.py:47-89`); one seat tool and one revolved suspension-bore tool are patterned/subtracted, with six identical insert pilots (`:92-180`).
- The repository contract already requires native parametric features, one typed `App::VarSet`, named Sketcher constraints, reference-only use of final `Part::Feature`, and recompute/measurement/round-trip/view verification (`AGENTS.md:20-37`). It names `.FCStd` as authoritative and prohibits a duplicate partial builder script (`AGENTS.md:5-10`).

### Supplied `App.getDocument('StellaArm')` error

- The supplied historical FreeCAD report records `NameError: Unknown document 'StellaOctangula'` from `App.getDocument(...)` before the assembly was created (`memory://011a169d5a201d47`, lines 270-290). The same API behavior applies to the supplied `StellaArm` error.
- This review independently observed that an inspection call using `App.getDocument('StellaCore')` failed with `NameError: Unknown document 'StellaCore'` because only `StellaArm` and `StellaProfileClamp` were currently open. The failure occurred before any result could be returned.
- The current assembly script avoids this failure: it stores `documents = App.listDocuments()` (`led_profiles/stella/create_stella_octangula.py:261-263`), retrieves an optional source with `documents.get(name) or App.openDocument(path)` (`:235-243`), and calls that helper for both sources (`:272-276`).
- The existing repository rule states the same behavior explicitly: `App.getDocument(name)` raises for an unknown name; use `App.listDocuments()` and `.get(name)` before a rebuild (`AGENTS.md:45-48`).

## Root cause

`App.getDocument('StellaArm')` is an exception-raising lookup, **not** a nullable lookup. At the time of the supplied failure, no open document had the internal name `StellaArm` (it may have been closed, not yet opened, renamed/suffixed, or only present on disk). Consequently FreeCAD raised `NameError`; no `None` value existed for the caller to test. This is observed API behavior, not a geometry failure.

## Recommended simplification direction

### Preserve exact arm fidelity only where it is necessary

The seven-section smooth arm loft is the exception. The retained reconstruction record reports that `PartDesign::AdditiveLoft` could not set `MaxDegree=8` and produced a materially different volume, while native `Part::Loft` with `MaxDegree=8` matched the source (`memory://6b5b8a630dbe2a1d`, paragraph 1). Keep the two document-level `Part::Loft` features and their named Sketcher sections if exact source fidelity remains an acceptance criterion. Keep them outside a PartDesign Boolean: the historical report records out-of-allowed-scope warnings for that arrangement (`memory://011a169d5a201d47`, lines 1-14).

Everything downstream should be consolidated where the physical result and validation measurements remain unchanged:

1. **Arm root:** replace the paired `BackMouth0`/`BackMouth1` and separate final access pockets with one point/sketch-driven multi-hole `PartDesign::Hole` where its standard counterbore/countersink geometry exactly covers the existing paths. The clamp already demonstrates one Hole feature driven by two centres (live `StellaProfileClamp.CounterboredM3Clearance`).
2. **Arm saddle:** retain one named U-section and one Pad; make the two keeper lands one two-profile sketch and one Pad, then make both insert pilots one two-circle sketch and one Pocket/Hole. Do not add helper solids when a sketch can carry the repeated geometry.
3. **Core:** use a single `CoreBody`: four named, constrained organic-outline section sketches on datum/origin planes at the source Z levels → AdditiveLoft; a single radial seat cut patterned three times; one revolved suspension-bore profile/cut reproducing the source's R2 toroidal mouth contacts; and one six-circle insert-pilot sketch/pocket. This follows the source’s repeated-tool structure (`core.py:149-180`) while reducing its native tree to the fewest independently editable features.
4. **Clamp:** retain only the reference envelopes plus one authoritative `ProfileClampBody`. Its final Body already expresses the intended clamp as two sketches, one Pad, one Pocket, and one two-hole feature. Before deleting any top-level primitive chain, compare the Body's final Shape, clearance, and screw-envelope results against it; then remove any duplicate construction representation that is not a reference witness.

## Concrete guidance changes

1. **Replace the existing broad lookup bullet** at `AGENTS.md:47` with the executable rule below; this records the important distinction that `getDocument` must not be used as a presence test:

   ```python
   documents = App.listDocuments()
   doc = documents.get(name)
   if doc is None:
       doc = App.openDocument(expected_path)
   ```

   Require callers to validate `doc.FileName` against `expected_path` after opening, as the assembly helper already does (`create_stella_octangula.py:235-243`). Use `App.getDocument` only after the document's actual internal name has just been obtained from `App.listDocuments()` or returned by FreeCAD.

2. **Add a feature-budget rule** under `AGENTS.md:20-27`: *for repeated identical cuts/additions, use one constrained sketch plus the native multi-profile operation or pattern; retain a separate feature only when it has an independent design parameter, operation type, or validation measurement.* This targets the root, saddle, core, and clamp duplication without forcing a different CAD style.

3. **Add an external-feature boundary rule:** *when required `Part::*` geometry cannot live in a `PartDesign::Body`, keep it document-level and feed one final Body BaseFeature; do not use a PartDesign Boolean across scope boundaries.* This preserves the warning-free arm topology established by the retained reconstruction record.

4. **Add an implementation acceptance check** to `AGENTS.md:33-37`: record the final Body tip plus the counts/types of deliberate native features, and reject duplicate printable solids. Continue measuring fit/interference, changing one central `App::VarSet` value, recomputing, saving/reloading, and viewing the model as already required.

## Inference and decision boundary

- **[INFERENCE]** The clamp's retained top-level primitive chain may be obsolete construction left alongside the simpler final `ProfileClampBody`; only a controlled comparison of final Shapes/clearances can establish that safely. Do not delete it solely from its names.
- **[INFERENCE]** Replacing current arm cuts with `PartDesign::Hole` is a valid simplification only if its generated lead/counterbore geometry exactly preserves the existing screw and driver-clearance measurements. If it does not, retain the current targeted pocket/loft.
- The evidence supports simplifying repeated native operations, not simplifying away the arm's degree-8 profile-shell loft while exact geometric equivalence remains required.
