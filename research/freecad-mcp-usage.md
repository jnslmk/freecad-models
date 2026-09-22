# freecad-mcp usage findings

**Scope.** This note covers the upstream `neka-nat/freecad-mcp` repository, its
current README/source/docs/examples, official FreeCAD documentation, and a small
set of upstream issues and FreeCAD Forum discussion. **Official** below means
repository or FreeCAD documentation; **Discussion** means a user report or
forum observation and is not treated as an API guarantee.

## Architecture, installation, and startup (official)

- The project has two processes/components: a FreeCAD addon and an MCP server
  launched by the MCP client. Install FreeCAD plus `uv`/`uvx`; the published
  server currently requires Python >=3.12, while the addon uses FreeCAD's bundled
  Python and must not be installed into that bundled environment. [README](https://github.com/neka-nat/freecad-mcp#quick-start),
  [installation guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#install-the-addon),
  [package metadata](https://github.com/neka-nat/freecad-mcp/blob/main/pyproject.toml)
- Clone the repository, copy `addon/FreeCADMCP` so that
  `Mod/FreeCADMCP/InitGui.py` is directly present, restart FreeCAD, select the
  **MCP Addon** workbench, and click **Start RPC Server**. The default listener
  is `127.0.0.1:9875`; the addon reports startup results in the status bar and
  Report View. [installation guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#start-the-rpc-server)
- Configure an MCP client with the stdio launcher (the minimal published form
  is `uvx freecad-mcp`), restart that client, and keep FreeCAD open with its RPC
  server running. From a checkout, use `uv sync`, `uv run freecad-mcp --help`,
  and the documented `uv --directory ... run freecad-mcp` configuration. [README](https://github.com/neka-nat/freecad-mcp#2-connect-claude-desktop),
  [run from source](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#run-from-source)
- A useful startup probe is an external XML-RPC `ping()` followed by
  `get_rpc_status()`; the guide explicitly says `ping()` should be `True` and
  status includes GUI-dispatch health. **Recommendation:** make this probe the
  first agent action and report a missing addon/RPC service before attempting
  modeling. [verification guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#verify-the-connection-on-windows),
  [RPC implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L101-L137)

## Transport and API shape

- The MCP-facing server is a Python `FastMCP` application with a console entry
  point named `freecad-mcp`; its CLI accepts `--host`, `--only-text-feedback`,
  and `--freecadcmd`. The MCP client-to-server launch channel is stdin/stdout;
  port 9875 is **not** an HTTP/SSE MCP endpoint. [server source](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/server.py),
  [CLI troubleshooting](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#windows-client-launch-troubleshooting),
  [package metadata](https://github.com/neka-nat/freecad-mcp/blob/main/pyproject.toml)
- The server-to-FreeCAD link is XML-RPC over HTTP using `xmlrpc.client.ServerProxy`
  to `http://<host>:9875`; the addon implements methods such as `ping`,
  `get_rpc_status`, document/object operations, code execution, screenshots,
  and reload. [client source](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/freecad_client.py),
  [addon RPC source](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py)
- The main tools are `create_document`, `list_documents`, `reload_document`,
  `create_object`, `edit_object`, `delete_object`, `get_objects`, `get_object`,
  `get_view`, `execute_code`, `execute_code_async`, `get_async_status`,
  `execute_code_headless`, `get_rpc_status`, parts-library operations, and
  `run_fem_analysis`. Most modeling tools can return screenshots; screenshots
  can be disabled per call or globally with `--only-text-feedback`. [tools guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md),
  [server registrations](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/server.py)
- The upstream examples include visual design demos (flange, toy car, and a
  part from a 2D drawing), a cantilever FEM script, and ADK/LangChain client
  integrations. **Recommendation:** use the small native-object workflow first;
  treat FEM and third-party agent examples as optional, environment-specific
  extensions. [examples guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/examples.md),
  [cantilever example](https://github.com/neka-nat/freecad-mcp/blob/main/examples/cantilever_fem.py)
- Remote mode is opt-in: the addon can bind all interfaces, filters clients by
  configured IP/CIDR allow-list, and the MCP server uses `--host`; headless
  execution still runs on the MCP-server machine. **Recommendation:** keep
  localhost unless remote control is required, then use a narrow allow-list and
  network controls. [remote configuration](https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md#remote-connections),
  [IP filter source](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/ip_filter.py)

## GUI-thread, async, and headless boundaries

- `execute_code` and document/object queries run through the addon's GUI
  dispatcher. GUI tasks are FIFO and serialized; the dispatcher avoids running
  while a modal dialog or mouse drag is active. `get_rpc_status` and async-job
  status are deliberately GUI-independent. [execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#choose-an-execution-mode),
  [GUI dispatcher](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/gui_dispatch.py)
- `execute_code_async` is for long, independent geometry work in a background
  thread. FreeCAD documents and Coin3D views are not thread-safe there: shape
  construction may happen in the worker, but document/view writes, recompute,
  save, and `ViewObject` access must be handed back through the injected
  `commit(fn, timeout=...)` helper. [execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#document-and-view-access),
  [RPC async contract](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L280-L370)
- `execute_code_headless` runs a temporary script in a separate `freecadcmd`
  process. The script must import what it needs and open/save its own files; it
  has no shared script namespace. It is intended for heavy or crash-prone
  OpenCascade work, and a native crash is isolated from the GUI process. [headless implementation](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/headless.py),
  [headless execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#headless-execution)
- Official FreeCAD documentation likewise separates core `App` functionality
  from GUI `Gui` functionality and states that command-line FreeCAD has no GUI.
  **Recommendation:** default to GUI-thread execution for document mutations;
  use async only for pure geometry followed by `commit`; use headless for
  isolated heavy work that explicitly saves an artifact. [FreeCAD scripting basics](https://wiki.freecad.org/FreeCAD_Scripting_Basics#The_App_and_Gui_objects),
  [Embedding FreeCAD](https://wiki.freecad.org/Embedding_FreeCAD#Using_FreeCAD_without_GUI)

## Document and object creation patterns

- The high-level sequence is: `create_document`; use `create_object` for native
  types such as `Part::Box`, `Part::Cylinder`, `Draft::*`, `PartDesign::*`, or
  `Fem::*`; pass typed property values in `obj_properties`; then inspect with
  `get_objects`/`get_object`. The addon applies properties, recomputes, and
  performs an object-validity check before reporting success. [tools guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md#available-tools),
  [server create-object contract](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/server.py#L105-L208),
  [object factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py)
- FreeCAD's native scripting pattern is `doc = App.newDocument(...)`,
  `doc.addObject(type, name)`, assignment to type-specific properties (for
  example `Part::Feature.Shape`), and `doc.recompute()`. Native document
  objects are preferable to a one-off final BREP when the model should remain
  editable. [FreeCAD scripting basics](https://wiki.freecad.org/FreeCAD_Scripting_Basics#The_Document_objects),
  [creating objects](https://wiki.freecad.org/FreeCAD_Scripting_Basics#Creating_objects),
  [recompute](https://wiki.freecad.org/Std_Refresh#Scripting)
- Object and document names may be sanitized or de-duplicated by FreeCAD (for
  example a requested name can return with a suffix). Follow-up calls must use
  the returned actual `document_name`/`object_name`, not assume the requested
  name. [RPC implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L143-L190),
  [object factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py#L73-L111)
- **Recommendation:** prefer explicit native feature history, stable names,
  units-aware properties/expressions, and a small create → recompute → inspect
  loop. Treat screenshots as visual evidence, not a substitute for querying
  object properties or validity.

## Recompute, save, reload, and verification workflow

1. **Health:** call `get_rpc_status`; stop if it is not healthy and inspect the
   FreeCAD Report View. The RPC status endpoint is GUI-independent, so it remains
   useful after a GUI operation timeout. [execution recovery](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#recover-from-a-stuck-gui-operation),
   [status tool](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md#available-tools)
2. **Build:** create the document and native objects, then explicitly run
   `doc.recompute()` in `execute_code` when using scripts. `create_object` and
   `edit_object` already recompute and validate their result. [FreeCAD recompute](https://wiki.freecad.org/Std_Refresh#Scripting),
   [object factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py#L92-L145)
3. **Inspect:** use `get_objects`/`get_object` for properties and validity, and
   `get_view` (or an enabled per-call screenshot) for visual confirmation. [tools guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md#screenshot-options)
4. **Persist:** save from the GUI-thread script (`doc.save()`/`doc.saveAs(...)`),
   or from the headless script itself. FreeCAD documents are the containers
   that can be saved to files; official scripting docs document opening and
   `saveCopy`, while the MCP headless guide explicitly requires the script to
   open/save. [FreeCAD scripting basics](https://wiki.freecad.org/FreeCAD_Scripting_Basics#The_Document_objects),
   [Std Open scripting](https://wiki.freecad.org/Std_Open#Scripting),
   [Std SaveCopy scripting](https://wiki.freecad.org/Std_SaveCopy/en#Scripting),
   [MCP headless guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#headless-execution)
5. **Round-trip:** after an external/headless process saves a file already open
   in the GUI, call `reload_document(doc_name)`; the tool closes and reopens the
   saved document so the GUI copy sees disk changes. Then repeat object queries,
   recompute/validity checks, and visual inspection. [reload tool](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md),
   [reload implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py#L213-L231)
6. **Delivery:** save, close, reload, and validate the final `.FCStd` before
   handing it off. This last gate is a project recommendation, not a claim that
   the MCP server itself automatically performs all six steps.

## Failure modes and practical discussion evidence

- **Wrong addon directory or nesting (Discussion + current official docs):**
  FreeCAD 1.1 uses versioned user paths on some platforms, and users report
  that copying into an unversioned Windows path or flattening the directory can
  make the workbench disappear. Resolve the authoritative location with
  `FreeCAD.getUserAppDataDir()` and ensure `Mod/FreeCADMCP/InitGui.py` exists.
  [official installation paths](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#addon-directory),
  [issue #116](https://github.com/neka-nat/freecad-mcp/issues/116),
  [issue #140](https://github.com/neka-nat/freecad-mcp/issues/140)
- **Python-version split (Discussion confirmed by official docs):** a Windows
  report found FreeCAD 1.1 bundled Python 3.11 while the external package
  required Python 3.12+, so installing into the bundled interpreter failed.
  Keep the environments separate. [installation guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md),
  [issue #140](https://github.com/neka-nat/freecad-mcp/issues/140)
- **MCP SDK/API skew:** issue #23 reports `FastMCP(... description=...)` failing
  with `mcp` 1.12.4; the maintainer fixed it on `main` and the reporter confirmed
  the fix. Prefer the current published package/checkout rather than applying
  that old workaround, and record package/addon revisions when diagnosing
  mismatches. [issue #23](https://github.com/neka-nat/freecad-mcp/issues/23),
  [current dependency range](https://github.com/neka-nat/freecad-mcp/blob/main/pyproject.toml)
- **GUI timeout/stuck state:** GUI work cannot be force-cancelled. A timeout can
  leave the operation running; later GUI calls fail fast while the dispatcher is
  stuck. Query `get_rpc_status`, wait for recovery, and restart FreeCAD if it
  does not return healthy. Use explicit positive finite timeouts (capped by the
  addon) for genuinely long GUI work; use async/headless instead where applicable.
  [execution guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#gui-dispatch-timeouts),
  [timeout issue](https://github.com/neka-nat/freecad-mcp/issues/141)
- **Modal dialogs:** a current open issue reports a CAM post-processor dialog
  that blocks the agent because it is not exposed through MCP. Avoid workflows
  that require unobservable modal UI; prefer scriptable/export APIs and require
  human confirmation for irreversible CAM output. This is a Discussion finding,
  not a general statement that every FreeCAD dialog is inaccessible. [issue #148](https://github.com/neka-nat/freecad-mcp/issues/148)
- **Headless executable/path:** `execute_code_headless` fails clearly when
  `freecadcmd` is absent; it auto-detects PATH/Flatpak and accepts an explicit
  `--freecadcmd` command. Its files live on the MCP-server machine, not
  necessarily the GUI host. [headless source](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/headless.py),
  [headless guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md#headless-execution)
- **Windows process spawning:** issue #140 reports an `EFTYPE` spawn failure in
  one libuv-based client and says `cmd /c freecad-mcp` worked; the installation
  guide documents this as a client-specific workaround, not a universal
  requirement. [installation workaround](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#windows-client-launch-troubleshooting),
  [issue #140](https://github.com/neka-nat/freecad-mcp/issues/140)

## Agent-facing instruction recommendations

**Recommended skill/instruction contract (derived from the official API and
clearly marked operational policy):**

1. Verify addon/RPC health (`ping`, `get_rpc_status`) before changing a model;
   identify the actual document/object names returned by each creation call.
2. Use native parametric objects and explicit units/properties; retain sketches,
   dependencies, and feature history. Recompute after scripted edits, then
   query properties/validity and request a screenshot when visual confirmation
   matters.
3. Serialize GUI/document mutations. Never touch `App` documents, `Gui`,
   `ViewObject`, recompute, or save directly inside async workers; use
   `commit()` for those operations.
4. Choose headless only for isolated heavy geometry or batch conversion. Make
   the headless script self-contained, save to a known path, then call
   `reload_document` before inspecting the GUI copy.
5. Keep GUI timeouts finite and explicit for slow imports/exports; after any
   timeout query status before retrying. Never blindly retry a possibly still
   running operation.
6. Treat Report View, object validity/error fields, recompute results, saved-file
   existence, reload success, and final screenshot as separate verification
   signals. Do not claim success from a tool response alone.
7. Avoid or pause for modal dialogs and irreversible operations (especially CAM
   posting); ask for human intervention when the required UI state is not
   observable through MCP.
8. For remote use, state which machine owns the GUI and which owns headless file
   paths; keep the allow-list narrow.

The FreeCAD Forum offers a useful but anecdotal perspective: one user reports
high productivity for FEM and general work, while another emphasizes that
results still require deliberate instructions, review, and testing rather than
blind delegation. Use that as workflow advice, not as evidence of guaranteed
model quality. [FreeCAD Forum discussion](https://forum.freecad.org/viewtopic.php?style=5&t=106599)

## Source list

- [freecad-mcp repository README](https://github.com/neka-nat/freecad-mcp)
- [Installation](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md)
- [Configuration](https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md)
- [Tools](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md)
- [Code execution](https://github.com/neka-nat/freecad-mcp/blob/main/docs/execution.md)
- [Demos and examples](https://github.com/neka-nat/freecad-mcp/blob/main/docs/examples.md)
- [MCP server source](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/server.py)
- [XML-RPC client source](https://github.com/neka-nat/freecad-mcp/blob/main/src/freecad_mcp/freecad_client.py)
- [Addon RPC source](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py)
- [GUI dispatcher](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/gui_dispatch.py)
- [Object factory](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/object_factory.py)
- [Official FreeCAD scripting basics](https://wiki.freecad.org/FreeCAD_Scripting_Basics)
- [Official FreeCAD embedding/headless guidance](https://wiki.freecad.org/Embedding_FreeCAD)
- [Official recompute](https://wiki.freecad.org/Std_Refresh)
- [Official open/save-copy scripting](https://wiki.freecad.org/Std_Open), [save copy](https://wiki.freecad.org/Std_SaveCopy/en)
- [Issue #23](https://github.com/neka-nat/freecad-mcp/issues/23), [#116](https://github.com/neka-nat/freecad-mcp/issues/116), [#140](https://github.com/neka-nat/freecad-mcp/issues/140), [#141](https://github.com/neka-nat/freecad-mcp/issues/141), [#148](https://github.com/neka-nat/freecad-mcp/issues/148)
- [FreeCAD Forum discussion](https://forum.freecad.org/viewtopic.php?style=5&t=106599)
