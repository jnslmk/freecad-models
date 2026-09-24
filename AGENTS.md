# Agent Guidelines

## Source of truth

- The `.FCStd` document is the authoritative editable model. Inspect its current state before changing geometry.
- Use FreeCAD MCP for normal interactive creation, editing, inspection, recompute, save, and reload.
- Persist design intent in native features, constraints, expressions, and `App::VarSet`; MCP call history is not documentation.
- Add a sibling Python script only for intentionally generated models, repeatable operations across documents, or migrations that need a reusable procedure. Record its scope and whether it rebuilds or edits an existing document; preserve unrelated and unsaved user work.
- Avoid partial builder scripts that duplicate the document and drift out of sync. Keep one-off diagnostic and editing snippets out of the repository.

## Diagnostic screenshots

- Save agent-captured debugging or inspection screenshots under `.codex-tmp/screenshots/<task-name>/` in this workspace. Create the directory before capture; `.codex-tmp/` is ignored by Git.
- Keep screenshot paths out of tracked model/documentation directories. Use the native `.FCStd` and written measurements for durable design evidence; only add an image to Git when the user explicitly requests a published visual artifact.

## One-document CAD review loop

1. Identify the selected, authoritative `.FCStd` for each affected part and assembly, inspect its native tree and linked sources, and record `git status` plus any unsaved FreeCAD state. Treat pre-existing changes as user-owned. If the target or its baseline is ambiguous, resolve that before editing.
2. Keep **one active document per part or assembly** and iterate in place, including during concept work. Extend its native sketches, constraints, and references rather than rebuilding from a screenshot. Change linked source documents only when the assembly needs them. Use `.codex-tmp/` for disposable experiments and recovery checkpoints; create a separate published concept file only when the user explicitly asks for a parallel alternative.
3. Before the first mutation, establish a reversible checkpoint for every file the agent will change. A clean tracked file can use its Git revision; for a dirty file, preserve its exact pre-agent state under ignored `.codex-tmp/` after reconciling unsaved GUI work. Use small FreeCAD transactions and validate each edit before saving. Never use a blanket reset, stash, or restore over unrelated or intervening user work.
4. Present the changed document as **pending review** with measured interfaces, relevant isometric and close-up/section views, native-feature validity, and explicit tradeoffs. Ask whether to accept or reject it; a technically valid concept is not automatically an accepted design. On acceptance, stage and commit only the agreed files. On rejection, roll back only the agent's changes to the recorded baseline, then reopen and verify the restored native document. If the user has edited it meanwhile, reconcile those edits before rollback. Leave undecided work uncommitted and clearly identified.

### Live Sketcher collaboration

- If `Gui.activeDocument().getInEdit()` names a sketch, checkpoint its in-memory state with `doc.saveCopy(...)` and continue in that sketch through small native MCP edits. Preserve its edit mode, camera, and selection rather than reopening the saved file.
- Model a requested mirror with Sketcher symmetry constraints about the chosen axis, not merely mirrored coordinates. Check the closed wire, remaining degrees of freedom, and dependent solid.
- After aborting or undoing a sketch edit, compare geometry, constraints, and degrees of freedom with the checkpoint before retrying; rollback can lose an unrelated constraint.
- Measure dependent interfaces on the resulting solid (for example, pilot depth from the actual material face, not just `Pocket.Length`). Ask before changing an unrequested mating interface.
- During active iteration, seek accept/reject at a natural design milestone rather than after each tweak. An explicit request to commit accepts the agreed files, not unrelated unsaved work.

Before altering layout, mating geometry, cable paths, optical openings, or structural support, distinguish fixed interfaces from design freedom and ask about consequential tradeoffs. For product-form work, inspect the whole assembly and the user's marked viewpoint; check silhouette, surface hierarchy, seam placement, and continuity at the joins, not just whether features fuse. Nominal CAD clearance or interference does not establish a PETG print fit or holding force.

## FreeCAD modeling

- Prefer native parametric FreeCAD modeling over final BREP or scripted-only geometry.
- Use `App::VarSet` as the model-level parameter container when targeting FreeCAD 1.0 or newer. Give it a stable name such as `StellaParams` and use typed properties (`App::PropertyLength`, `App::PropertyAngle`, `App::PropertyInteger`, `App::PropertyFloat`, `App::PropertyBool`, `App::PropertyString`, or `App::PropertyEnumeration`).
- Drive native feature properties and named Sketcher constraints with FreeCAD expressions such as `StellaParams.CoreHeight`; preserve units and recompute to verify dependency updates.
- Use named Sketcher constraints for sketch-local design intent. Use spreadsheets only for tabular calculations, ranges, reports, or FreeCAD 0.21 compatibility.
- Keep editable sketches and dependent native operations in the document tree. Use a final `Part::Feature` only for explicitly imported or reference-only geometry.
- Apply a repeated-feature budget: for identical additions or cuts, use one constrained multi-profile sketch and one native operation or pattern; retain a separate feature only for an independent design parameter, operation type, or validation measurement.
  Keep required `Part::*` geometry that cannot live in a `PartDesign::Body` at document scope and feed it to one final Body BaseFeature; do not bridge that boundary with a PartDesign Boolean.
- Use stable internal names and descriptive labels; query actual object names rather than inferring them from labels or screenshots.
- Prefer origin planes, datum geometry, sketches, and named references over incidental `Face7` or `Edge12` identities.
- Recompute before measuring, exporting, or making geometry claims.

## Verification

After a geometry change, verify the affected model before delivery:

1. Recompute and check for invalid or error-state objects and failed features.
2. Measure the requested dimensions and clearances; check expected native object types, expressions, dependencies, final Body tip, and the deliberate native feature counts/types. Reject duplicate printable solids; reference-only `Part::Feature` objects are permitted.
3. For parametric changes, record a central parameter's original value and a dependent measurement, change it within the intended range, and confirm the expected geometry change without rerunning an external script. Restore the original value and recompute before saving.
4. Save and repeat the relevant state and geometry checks against the persisted file. If no user sketch is being edited, close and reload it; otherwise keep the edit session open and inspect the saved `.FCStd` in a separate headless FreeCAD process. Preserve unsaved user work.
5. Inspect an isometric view and any orthographic or section views needed to prove the visible shape; confirm the intended objects, visibility, and body tip. Screenshots complement measurements; they do not replace them.

For an assembly, check the saved links and every repeated joint, including fasteners, profile crossings, diffuser/cable openings, and actual support contacts. For FEM or topology work, establish the real load path, joints, supports, material and print orientation before interpreting a result; validate the baseline solve and mesh, and label studies with assumed clip stiffness or untested fits as conditional rather than a safe-service design.

## FreeCAD MCP

Use the running FreeCAD MCP service as the default GUI bridge. Before any MCP
document or view operation, read `.agents/skills/freecad-mcp/SKILL.md`; it owns
execution-mode selection, health checks, transactions, recovery, and persistence.

### Failure-resistant scripting

- Resolve a target by its internal `Name` from `App.listDocuments()`; `Label` is presentation-only and `FileName` is the expected saved path. Require an existing expected path and fail unless the normalized `doc.FileName` matches it after both the Name lookup and any open; preserve FreeCAD's returned `doc.Name` for every later lookup.
- Save the owner document before assigning any cross-document `App::Link.LinkedObject`; verify every source document has a non-empty `FileName`.
- Treat `App::Link` view providers as capability-limited: guard optional display properties such as `ShapeColor` and `Transparency` with `hasattr`.
- Use `activeView().fitAll()` for scripted view fitting; `fitSelection()` is not available on every FreeCAD view provider.
- After a GUI timeout or exception, follow the recovery sequence in `.agents/skills/freecad-mcp/SKILL.md` before retrying; it must establish whether a partial mutation occurred.
- Optional `IfcOpenShell` warnings from the BIM workbench are environmental and do not validate or invalidate model geometry; do not retry a model operation because of them.

## References

- Consult `research/freecad-variables.md` when choosing parameter containers or migrating spreadsheet parameters.
- Consult `research/freecad-mcp-usage.md` for upstream API evidence, installation details, or failure-mode investigation beyond the MCP runbook.
