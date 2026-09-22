# FreeCAD variables and parametric expressions beyond spreadsheets

## Recommendation

For FreeCAD 1.0 or newer, replace a spreadsheet used only as a named parameter bag with a native `App::VarSet`, keeping expressions on consuming properties. Create typed properties such as `App::PropertyLength`, `App::PropertyAngle`, `App::PropertyInteger`, `App::PropertyFloat`, `App::PropertyBool`, `App::PropertyString`, or `App::PropertyEnumeration`, then reference them as `StellaParams.PropertyName`.

Keep spreadsheets where tabular inputs, formulas, ranges, aggregates, visible calculation sheets, reports, or FreeCAD 0.21 compatibility are required. `App::FeaturePython` custom properties are a fallback for scripted validation/computation, not the simplest plain-variable store.

## Evidence

- [Std VarSet](https://wiki.freecad.org/Std_VarSet): `App::VarSet` was introduced in FreeCAD 1.0 and is a set of typed properties usable as expression variables. It documents the Python API using `doc.addObject("App::VarSet", ...)` and `addProperty(...)`.
- [Release notes 1.0](https://wiki.freecad.org/Release_notes_1.0#Core_system_and_API): identifies `App::VarSet` as a new core property container, alongside the expression engine.
- [Expressions](https://wiki.freecad.org/Expressions): expressions are unit-aware, may reference any object's properties, custom properties, spreadsheet aliases, and named Sketcher constraints. `setExpression(path, expression)` is the scripting API.
- [FreeCAD source: VarSet.h](https://raw.githubusercontent.com/FreeCAD/FreeCAD/main/src/App/VarSet.h): confirms `App::VarSet` is a `DocumentObject` intended to store variables.
- [Manual: Using spreadsheets](https://wiki.freecad.org/Manual:Using_spreadsheets): documents spreadsheet aliases as the historical “master values” pattern and explains their automatic propagation into model properties.
- [FeaturePython custom properties](https://wiki.freecad.org/FeaturePython_Custom_Properties): documents typed dynamic properties on scripted objects; these properties are also expression-addressable.
- [Sketcher constraints](https://wiki.freecad.org/Sketcher_Workbench#Edit_constraints): named dimensional constraints can be used in expressions and are appropriate for sketch-local design intent.

## Version choice

| Mechanism | Availability | Best use |
|---|---:|---|
| Spreadsheet aliases | Before 0.21 and newer | Compatibility, formulas, tables, reports |
| `App::VarSet` | 1.0+ | Native typed model parameters |
| `App::FeaturePython` properties | Broad | Custom validation/computation or legacy scripted objects |
| Named Sketcher constraints | Broad | Local geometric design dimensions |
| Assembly joints/constraints | 1.0+ | Placement and kinematic relationships, not global scalar storage |

`App::VarSet` is unavailable in FreeCAD 0.21, so models targeting that version must retain spreadsheet aliases or use a version-specific compatibility strategy. FreeCAD 1.1 adds additional expression-language improvements, but does not change the recommendation.

## Migration guidance for Stella

For a 1.0/1.1-only model:

1. Create one `App::VarSet` named `StellaParams`.
2. Move each spreadsheet alias to a typed property, preserving units.
3. Change consumers from `Spreadsheet.Alias` to `StellaParams.PropertyName`.
4. Keep named sketch constraints for dimensions that belong intrinsically to a sketch.
5. Retain a spreadsheet only if it provides calculations, reports, or tabular documentation.
6. Recompute and inspect expression/dependency errors after migration.

Example:

```python
params = doc.addObject("App::VarSet", "StellaParams")
params.addProperty("App::PropertyLength", "CoreHeight", "Dimensions")
params.CoreHeight = 20
feature.setExpression("Length", "StellaParams.CoreHeight")
doc.recompute()
```

### Bottom line

Yes: the modern native replacement is `App::VarSet`, introduced in FreeCAD 1.0. It is cleaner than a spreadsheet when the spreadsheet is only being used as a variable container. It is complementary—not a replacement—for spreadsheet calculations and reporting.
