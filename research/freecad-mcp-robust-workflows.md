# Robust FreeCAD MCP workflows

**Scope.** This note complements `freecad-mcp-usage.md`: it concentrates on
choosing the right document reliably and on the execution and verification
boundaries that keep a FreeCAD/MCP operation recoverable. Technical statements
are drawn only from upstream `neka-nat/freecad-mcp` and official FreeCAD
documentation or source.

## Document identity: never infer the lookup key

Treat these as three separate values:

| Value | Meaning | Safe use |
|---|---|---|
| Internal `Name` | FreeCAD's loaded-document identifier. It is the key in `App.listDocuments()` and the value accepted by `App.getDocument(name)`. | Use for document-tool arguments and subsequent script lookup. |
| `Label` | A user-facing tree label. For a new document it is displayed in the Tree View and may be replaced by the document name after reopening. | Display it or deliberately resolve it to exactly one loaded document; never assume it is a lookup key. |
| `FileName` / filesystem path | The saved document's full path; it is blank until the document is saved. | Check the file before opening, then retain the returned document's actual `Name`. |

The `App` Python binding implements `listDocuments()` as a dictionary whose
keys are each document's internal `getName()`. In contrast, `getDocument(name)`
performs that lookup and raises `NameError("Unknown document '…'")` when no
loaded document has that key. Therefore an unknown-document failure means that
the supplied string is absent from the current document map; it is not evidence
that a document with that *label* or filename is open. [FreeCAD application
binding: `listDocuments`](https://github.com/FreeCAD/FreeCAD/blob/main/src/App/ApplicationPy.cpp#L785-L810),
[`getDocument`](https://github.com/FreeCAD/FreeCAD/blob/main/src/App/ApplicationPy.cpp#L358-L373),
[Std New document properties](https://wiki.freecad.org/Std_New#Properties),
[Std Open scripting](https://wiki.freecad.org/Std_Open#Scripting)

Names can be sanitised or de-duplicated at creation; FreeCAD's object-name
rules describe the analogous identifier behavior explicitly. The MCP addon's
`create_document` implementation consequently returns `doc.Name`, and
`list_documents` returns the `FreeCAD.listDocuments()` keys. Store those
returned values as the only identifiers for later MCP calls. [FreeCAD object
names](https://wiki.freecad.org/Object_name#Names), [MCP document handlers](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L431-L434),
[create-document result](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L480-L484)

### Exact resolution sequence

Run this in `execute_code` (the GUI-thread mode) before any mutation. It makes
the live document map authoritative, requires exactly one explicit selector
when selecting by internal name or path, returns an already loaded document
when its canonical saved path matches, uses the active document only when no
selector was supplied and the caller explicitly allowed that policy, and
verifies the actual name after opening a new path.

```python
from pathlib import Path
import FreeCAD as App


def resolve_document(*, internal_name=None, path=None, allow_active=False):
    if internal_name is not None and path is not None:
        raise ValueError("Pass either internal_name or path, not both")

    documents = App.listDocuments()  # {actual internal Name: Document}
    loaded_names = ", ".join(sorted(documents)) or "<none>"

    if internal_name is not None:
        doc = documents.get(internal_name)
        if doc is not None:
            return doc
        raise LookupError(
            f"No loaded document with internal Name {internal_name!r}; "
            f"loaded Names: {loaded_names}"
        )

    if path is not None:
        file_path = Path(path).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"FreeCAD file does not exist: {file_path}")

        for doc in documents.values():
            if doc.FileName and Path(doc.FileName).expanduser().resolve() == file_path:
                return doc

        opened = App.openDocument(str(file_path))
        actual_name = opened.Name
        documents = App.listDocuments()
        doc = documents.get(actual_name)
        if doc is None:
            raise RuntimeError(
                f"FreeCAD opened {file_path!s}, returned Name {actual_name!r}, "
                "but that Name is absent from App.listDocuments()"
            )
        return doc

    if allow_active:
        doc = App.ActiveDocument
        if doc is not None:
            return doc

    raise LookupError(
        "No document selector supplied and no active document is available; "
        f"loaded Names: {loaded_names}"
    )
```

`App.openDocument(path)` creates and returns a document from an existing file;
if loading fails, FreeCAD reports an I/O exception. The explicit map check
above prevents a failed or unexpected open from silently becoming a later
`getDocument` failure. `App.ActiveDocument` may be `None` when there is no open
document, so it must remain an explicit fallback rather than an implicit target.
[Std Open scripting](https://wiki.freecad.org/Std_Open#Scripting), [FreeCAD
application binding: active document](https://github.com/FreeCAD/FreeCAD/blob/main/src/App/ApplicationPy.cpp#L345-L356)

For a deliberate label-based UI choice, resolve from the same authoritative map
and reject zero or multiple matches; retain `doc.Name` after resolving. Do not
call `App.getDocument(label)`.

```python
def resolve_unique_label(label):
    matches = [doc for doc in App.listDocuments().values() if doc.Label == label]
    if len(matches) != 1:
        names = [doc.Name for doc in matches]
        raise LookupError(
            f"Expected one loaded document labelled {label!r}; "
            f"matching internal Names: {names}"
        )
    return matches[0]  # subsequent calls use this document's Name
```

FreeCAD documents can coexist, and the active document is only the one shown
in the current 3D view. Labels are presentation values, whereas FreeCAD's
identifier guidance recommends using an internal `Name` rather than a label to
guarantee the intended object; the same separation is the safe policy for
loaded-document selection. [Document structure](https://wiki.freecad.org/Document_structure),
[FreeCAD name-versus-label guidance](https://wiki.freecad.org/Object_name#Labels)

### Create and reopen patterns

The high-level MCP sequence is `create_document` → retain returned
`document_name` → pass that exact value to subsequent tools. When scripting,
retain `doc.Name` immediately rather than the requested spelling. Likewise,
after `openDocument`, retain the returned `opened.Name`; never derive it from
the path stem.

```python
# GUI-thread execute_code
import FreeCAD as App

created = App.newDocument("Pump Housing")
doc_name = created.Name              # actual key; do not assume the request
created.Label = "Pump housing v2"    # presentation only

# Later: map lookup first, not App.getDocument("Pump housing v2").
doc = App.listDocuments().get(doc_name)
if doc is None:
    raise LookupError(f"Document {doc_name!r} is no longer loaded")
```

The MCP addon follows this same rule for object creation: it returns the created
object's actual `Name`, because FreeCAD can sanitise or de-duplicate the
requested name. Use that returned object name for `get_object` and
`edit_object` as well. [MCP object factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py#L80-L119),
[FreeCAD object-name rules](https://wiki.freecad.org/Object_name#Name)

## Execution boundaries and recovery

### Select one execution mode per operation

- **GUI dispatcher — default for document work.** `execute_code`, document and
  object tools, queries, recompute, save, and view access run through the
  addon's GUI dispatcher. It serializes GUI tasks in FIFO order and defers work
  while a modal dialog, popup, or mouse drag is active. Use this mode for every
  mutation of `App` documents or `Gui` views. [MCP execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#choose-an-execution-mode),
  [GUI dispatcher](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/gui_dispatch.py#L1-L23),
  [FreeCAD App/Gui separation](https://wiki.freecad.org/FreeCAD_Scripting_Basics#Built-in_modules)
- **Async — geometry only until commit.** `execute_code_async` runs the worker
  off the GUI thread. Build independent OCCT shapes there, but hand every
  document/view write, recompute, and save to `commit(fn, timeout=...)`; the
  helper runs `fn` on the GUI thread and reports a dispatch failure as a
  `RuntimeError`. Poll `get_async_status(job_id)` for failed-job errors and
  tracebacks. [MCP execution guide: document and view access](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#document-and-view-access),
  [async/commit implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L62-L89),
  [async status contract](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#background-jobs)
- **Headless — isolated, self-contained work.** `execute_code_headless` writes
  a temporary script and runs it in a separate `freecadcmd` process. That script
  has no shared namespace and must import what it uses, open/create the
  document, and save its own output. Its paths are on the MCP-server machine;
  a native crash is isolated to the helper process. [MCP headless guidance](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#headless-execution),
  [headless implementation](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/headless.py#L1-L9)

A GUI operation that has begun cannot be safely cancelled. After a timeout,
query GUI-independent `get_rpc_status`, inspect the target document and Report
View, and retry only after deciding whether the timed-out operation completed
or left a partial edit. Do not replay the mutation merely because its response
was lost. [MCP timeout recovery](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#recover-from-a-stuck-gui-operation),
[GUI timeout implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/gui_dispatch.py#L178-L195)

### Inspect errors where they occur

Open **View → Panels → Report View** after an exception, timeout, or substantial
build. It displays messages from FreeCAD's internal `Console`; `PrintError` is
for a failure that prevents an operation, while warnings and logs are distinct
message classes. The MCP dispatcher writes a GUI-task exception and traceback
to that console, and failed async jobs expose their exception and traceback via
`get_async_status`. [FreeCAD Report View](https://wiki.freecad.org/Report_View#Messages),
[GUI dispatcher exception handling](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/gui_dispatch.py#L137-L161),
[MCP async status](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#background-jobs)

## Construction policy: editable first, simple only on purpose

Use a native parametric type when the model needs later dimensional editing:
for example, `Part::Box` has `Length`, `Width`, `Height`, and `Placement`
properties, and the official scripting pattern creates it with
`doc.addObject("Part::Box", name)` before assigning properties and recomputing.
The MCP `create_object` path uses the same `doc.addObject` mechanism for
generic types and recomputes and validates the created result. [Part Box
scripting](https://wiki.freecad.org/Part_Box#Scripting), [Part Box
properties](https://wiki.freecad.org/Part_Box#Properties), [MCP object
factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py#L80-L119)

A `Part::Feature` is a simple displayable object whose `Shape` property stores
a `Part TopoShape`. Assigning a final shape to a plain `Part::Feature` does not
retain the construction parameters of a native primitive or a sketch/feature
history. It is appropriate for explicitly imported, reference, or intentionally
final geometry; prefer the native feature when that design intent is required
and use a simple assigned shape only when that loss is intentional. [Part Feature](https://wiki.freecad.org/Part_Feature#Introduction),
[Part Feature Shape property](https://wiki.freecad.org/Part_Feature#Properties),
[FreeCAD scripting basics: creating objects](https://wiki.freecad.org/FreeCAD_Scripting_Basics#Creating_objects)

## Layered validation and persistence gate

A successful RPC response is not a geometry proof: upstream explicitly states
that async script success does not certify geometry validity. Use every relevant
layer below after a meaningful edit. [MCP execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#background-jobs)

1. **Health and identity.** Call `get_rpc_status`, resolve the document from
   `App.listDocuments()`, and record its actual `Name`, `Label`, and `FileName`.
   The status tool does not use the GUI thread, while document queries do.
   [MCP tools](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md),
   [MCP timeout recovery](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#recover-from-a-stuck-gui-operation)
2. **Recompute and semantic inspection.** Run `doc.recompute()` after scripted
   edits, then query affected objects and properties with `get_object` or
   `get_objects`. The MCP object factory recomputes and regards invalid, error,
   or still-touched states—or a failing `isValid()` check—as a failed creation or
   edit rather than a success. [FreeCAD recompute scripting](https://wiki.freecad.org/Std_Refresh#Scripting),
   [MCP object validation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_validation.py)
3. **Visual inspection.** Request `get_view` (or a tool screenshot) in the
   relevant orientation and inspect the intended shape and visibility. The MCP
   tools document the available view orientations and that `get_view` is the
   explicit screenshot operation. Treat this as complementary to property and
   validity checks, not a replacement. [MCP screenshot options](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md#screenshot-options)
4. **Save and verify the path.** Save the recomputed, validated document with
   `doc.save()` or `doc.saveAs(path)`, then record the non-empty `doc.FileName`.
   A new document's file name is blank until it has been saved. [FreeCAD new
   document properties](https://wiki.freecad.org/Std_New#Properties), [FreeCAD
   new-document scripting example](https://wiki.freecad.org/Std_New#Scripting)
5. **Reload after external/headless writes.** If headless code changed an
   `.FCStd` that is also open in the GUI, call `reload_document` with the actual
   internal name, then resolve it again from the live map and repeat recompute,
   object, and visual checks. The addon refuses a reload when the document is
   not loaded, has no saved path, or that path is missing; it closes and opens
   the document from disk. [MCP headless guidance](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#headless-execution),
   [MCP reload implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L510-L535)

For a final round trip that intentionally closes the document, save before
closing and preserve the `Name` returned by the new open:

```python
# GUI-thread execute_code; only after the caller has approved closing this document.
doc.recompute()
doc.save()
saved_path = doc.FileName
if not saved_path:
    raise RuntimeError("Refusing round trip: document has no saved file path")

old_name = doc.Name
App.closeDocument(old_name)
reopened = App.openDocument(saved_path)
actual_name = reopened.Name
if App.listDocuments().get(actual_name) is None:
    raise RuntimeError(f"Reopened document {actual_name!r} is absent from the map")
reopened.recompute()
```

## Source list

- [FreeCAD `ApplicationPy.cpp`](https://github.com/FreeCAD/FreeCAD/blob/main/src/App/ApplicationPy.cpp)
- [FreeCAD Scripting Basics](https://wiki.freecad.org/FreeCAD_Scripting_Basics)
- [FreeCAD Std New](https://wiki.freecad.org/Std_New), [Std Open](https://wiki.freecad.org/Std_Open), and [Std Refresh](https://wiki.freecad.org/Std_Refresh)
- [FreeCAD Object name](https://wiki.freecad.org/Object_name), [Document structure](https://wiki.freecad.org/Document_structure), and [Report View](https://wiki.freecad.org/Report_View)
- [FreeCAD Part Box](https://wiki.freecad.org/Part_Box) and [Part Feature](https://wiki.freecad.org/Part_Feature)
- [freecad-mcp tools guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md) and [execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md)
- [freecad-mcp RPC server](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py), [GUI dispatcher](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/gui_dispatch.py), [object factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py), and [object validation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_validation.py)
- [freecad-mcp headless implementation](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/headless.py)
