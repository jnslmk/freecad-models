# Agent Guidelines

## Source of truth

- The `.FCStd` document is the authoritative editable model. Inspect its current state before changing geometry.
- Use FreeCAD MCP for normal interactive creation, editing, inspection, recompute, save, and reload.
- Persist design intent in native features, constraints, expressions, and `App::VarSet`; MCP call history is not documentation.
- Add a sibling Python script only for intentionally generated models, repeatable operations across documents, or migrations that need a reusable procedure. Record its scope and whether it rebuilds or edits an existing document; preserve unrelated and unsaved user work.
- Avoid partial builder scripts that duplicate the document and drift out of sync. Keep one-off diagnostic and editing snippets out of the repository.
- Existing Stella arm geometry and its accompanying script are outside instruction-maintenance work; leave their migration to a separately requested task.

## Diagnostic screenshots

- Save agent-captured debugging or inspection screenshots under `.codex-tmp/screenshots/<task-name>/` in this workspace. Create the directory before capture; `.codex-tmp/` is ignored by Git.
- Keep screenshot paths out of `design-review/` and other tracked model/documentation directories. Use the native `.FCStd` and written measurements for durable design evidence; only add an image to Git when the user explicitly requests a published visual artifact.

## Concept and implementation work

- In concept mode, preserve the user's original and create clearly named alternatives with a short note stating what differs.
- In implementation mode, extend the selected native sketch, constraints, and reference geometry rather than rebuilding from a screenshot.
- Once a concept is selected, hide rejected alternatives and leave the selected result unambiguous and editable.

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
4. Save, close, reload, and repeat the relevant state and geometry checks. Preserve unsaved user work before closing or reloading.
5. Inspect an isometric view and any orthographic or section views needed to prove the visible shape; confirm the intended objects, visibility, and body tip. Screenshots complement measurements; they do not replace them.

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
