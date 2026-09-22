---
name: freecad-mcp
description: Operate FreeCAD through neka-nat/freecad-mcp. Use before document or view operations, async/headless execution, timeout recovery, or save/reload verification.
---

# FreeCAD MCP runbook

Use the upstream server as a bridge between an MCP client and a running FreeCAD
GUI. Follow `AGENTS.md` for document ownership, modeling policy, and geometry
acceptance criteria. Consult `research/freecad-mcp-usage.md` only for upstream
API evidence, installation details, or failure investigation beyond this runbook.

## Start with health

1. Ensure FreeCAD has the **MCP Addon** workbench and its RPC server running.
   The default bridge is the local XML-RPC listener at `127.0.0.1:9875`.
2. Check `get_rpc_status` before changing a model. If available, confirm the
   external `ping()` and inspect the Report View when startup fails.
3. Keep MCP client transport separate from the addon bridge: the client launches
   `freecad-mcp` over stdio; port `9875` is not an HTTP/SSE MCP endpoint.
4. Use localhost by default. Remote mode requires a narrow allow-list and an
   explicit `--host`; distinguish the GUI host from the MCP server's file host.

## Choose one execution mode

- **GUI thread (`execute_code`, object/document tools):** default for document,
  view, property, recompute, and save mutations. GUI calls are serialized; use
  explicit finite timeouts for genuinely slow imports or exports.
- **Async (`execute_code_async`):** only for independent, heavy geometry that
  does not touch a document or view. Build shapes in the worker, then use the
  provided `commit(fn, timeout=...)` helper for document/view writes, recompute,
  and save.
- **Headless (`execute_code_headless`):** use for isolated, crash-prone or
  batch OpenCascade work. Make the script self-contained: import its modules,
  open/create the document, save the artifact, and use paths visible to the MCP
  server machine. Use a separate output path when the GUI has unsaved changes;
  reconcile those changes before replacing or reloading its document.

Never access `App` documents, `Gui`, `ViewObject`, recompute, or save from an
async worker. Never blindly retry a GUI call after a timeout: it may still be
running.

## Edit the authoritative document

1. Resolve the target before mutation. Internal `Name` is the `App.listDocuments()` dictionary key; `Label` is presentation-only; `FileName` is its saved path. Retain names returned by FreeCAD rather than requested spellings:

   ```python
   from pathlib import Path

   expected = Path(expected_path).expanduser().resolve()
   if not expected.is_file():
       raise FileNotFoundError(expected)

   documents = App.listDocuments()
   doc = documents.get(internal_name)
   if doc is not None and (
       not doc.FileName
       or Path(doc.FileName).expanduser().resolve() != expected
   ):
       raise RuntimeError("loaded Name belongs to another path")
   if doc is None:
       opened = App.openDocument(str(expected))
       doc = App.listDocuments().get(opened.Name)
       if doc is None or not doc.FileName:
           raise RuntimeError("opened document is absent or unsaved")
       if Path(doc.FileName).expanduser().resolve() != expected:
           raise RuntimeError("opened document path mismatch")
   ```

   A matching `Name` is only a candidate: canonical expected-path validation is
   required after both that lookup and opening, and a mismatch fails before any
   mutation. Preserve the validated `doc.Name` for every later call. Resolve a
   label only by an explicit exactly-one match; do not call `App.getDocument(label)`.
   Active-document fallback requires an explicit caller decision and the same
   expected-path validation.
2. Make small, coherent edits through GUI-thread Python or document tools. Follow the repository's modeling contract; a persistent builder script is optional, not a prerequisite. If a scoped reusable script exists, inspect it before executing it against a live document.
3. Wrap each coherent document mutation in a transaction. Recompute and check
   the affected objects before committing; abort on exceptions or failed
   validation. Keep saving outside the transaction so failed edits are not
   persisted.

   ```python
   doc.openTransaction("descriptive change")
   try:
       # Apply the intended document edits.
       doc.recompute()
       # Check affected objects; raise if validation fails.
       doc.commitTransaction()
   except Exception:
       doc.abortTransaction()
       raise
   ```

4. Query the affected properties and validity. Use `get_view` or an enabled
   per-call screenshot for visual evidence, alongside the geometry checks in
   `AGENTS.md`.
5. Save validated changes with `doc.save()` or `doc.saveAs(...)` to the known
   `.FCStd` path. One-off editing and diagnostic snippets need not be retained.

## Verify and recover

For geometry changes, apply the repository's verification gate. Record the actual
document/object names, recompute state, affected-object validity, saved path,
reload result, and required views. Inspect the Report View after an exception,
timeout, or substantial build; its messages and tracebacks are recovery evidence.
A successful tool response alone is not geometry proof.

Save, close/reload, and inspect again before delivery. Preserve unsaved user
work before closing or reloading; a headless output must not silently replace it.

If a GUI operation times out, query `get_rpc_status` from a separate client and
open the Report View. Wait for a healthy dispatcher, then inspect the resolved
target document, its native tree, and affected geometry for completed or partial
mutations before deciding whether to retry. After a FreeCAD-side exception,
inspect the Report View and newly created `FeaturePython` objects (including
whether their `Proxy` exists) before mutating or deleting them. Do not repeat an
operation merely because its response was lost. If the dispatcher stays stuck,
restarting FreeCAD is a last resort: warn about unsaved-work loss and obtain
approval when it cannot be preserved. GUI work cannot be safely force-cancelled.

Avoid workflows that depend on unobservable modal dialogs or irreversible UI
steps. Prefer scriptable APIs and stop for human intervention when MCP cannot
observe the required state.

## References

- Repository findings and issue evidence: `research/freecad-mcp-usage.md`
- Upstream README: https://github.com/neka-nat/freecad-mcp
- Upstream execution guide: https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md
- Upstream tools guide: https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md
- Upstream installation/configuration: https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md and https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md
- Upstream demos and integrations: https://github.com/neka-nat/freecad-mcp/blob/main/docs/examples.md
