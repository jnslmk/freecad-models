"""Build the Stella-octangula layout from the authoritative component files.

Scope: creates one new assembly file. The default is ``StellaOctangula.FCStd``;
``STELLA_OUTPUT_PATH`` selects a separate working copy without replacing an
existing file. It links, but never edits, the saved core, arm, and clamp sources.
Run inside FreeCAD after all three component documents are saved.
"""

from __future__ import annotations

import os
from math import cos, radians, sin, sqrt

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.environ.get("STELLA_OUTPUT_PATH", os.path.join(HERE, "StellaOctangula.FCStd"))
CORE_PATH = os.path.join(HERE, "StellaCore.FCStd")
ARM_PATH = os.path.join(HERE, "StellaArm.FCStd")
CLAMP_PATH = os.path.join(HERE, "StellaProfileClamp.FCStd")

PROFILE_LENGTH = 1500.0
PROFILE_WIDTH = 26.1
PROFILE_HEIGHT = 30.5
PROFILE_RIM_Z = 16.8
PROFILE_SOURCE_DIR = os.path.join(HERE, "stella_profile_sources")
CABLE_DIAMETER = 6.7
ARM_SADDLE_START = 72.0
SADDLE_AXIS_Z = 19.25
CROSSING_OFFSET = PROFILE_HEIGHT + 0.25
BASE_SIGNS = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))
OFFSET_SIGNS = tuple((-x, y, z) for x, y, z in BASE_SIGNS)
EDGES = tuple((i, j) for i in range(4) for j in range(i + 1, 4))
SEAT_ANGLES = (90.0, 210.0, 330.0)


def _normalized(vector: App.Vector) -> App.Vector:
    result = App.Vector(vector)
    if result.Length < 1e-9:
        raise RuntimeError("zero-length layout vector")
    result.normalize()
    return result


def _placement_from_axes(
    origin: App.Vector,
    x_axis: App.Vector,
    y_axis: App.Vector,
    z_axis: App.Vector,
) -> App.Placement:
    matrix = App.Matrix()
    matrix.A11, matrix.A12, matrix.A13, matrix.A14 = (
        x_axis.x,
        y_axis.x,
        z_axis.x,
        origin.x,
    )
    matrix.A21, matrix.A22, matrix.A23, matrix.A24 = (
        x_axis.y,
        y_axis.y,
        z_axis.y,
        origin.y,
    )
    matrix.A31, matrix.A32, matrix.A33, matrix.A34 = (
        x_axis.z,
        y_axis.z,
        z_axis.z,
        origin.z,
    )
    matrix.A41, matrix.A42, matrix.A43, matrix.A44 = 0.0, 0.0, 0.0, 1.0
    return App.Placement(matrix)


def _source_to_target(
    source_origin: App.Vector,
    source_x: App.Vector,
    source_y: App.Vector,
    source_z: App.Vector,
    target_origin: App.Vector,
    target_x: App.Vector,
    target_y: App.Vector,
    target_z: App.Vector,
) -> App.Placement:
    def rotate(vector: App.Vector) -> App.Vector:
        return (
            target_x * vector.dot(source_x)
            + target_y * vector.dot(source_y)
            + target_z * vector.dot(source_z)
        )

    x_axis = rotate(App.Vector(1, 0, 0))
    y_axis = rotate(App.Vector(0, 1, 0))
    z_axis = rotate(App.Vector(0, 0, 1))
    placement = _placement_from_axes(
        target_origin - rotate(source_origin), x_axis, y_axis, z_axis
    )
    if (placement.multVec(source_origin) - target_origin).Length > 1e-7:
        raise RuntimeError("arm-root transform does not preserve the mating origin")
    return placement


SOURCE_ROOT = App.Vector(14.0, 0.0, sqrt(2) * 14.0 + 2.0)
SOURCE_X = App.Vector(0.0, 1.0, 0.0)
SOURCE_Z = App.Vector(-sqrt(2 / 3), 0.0, 1 / sqrt(3))
SOURCE_Y = _normalized(SOURCE_Z.cross(SOURCE_X))


def _layout(base_side: float, offset_side: float, core_seat_height: float) -> list[tuple]:
    layout = []
    for tetra_name, signs, offset, side in (
        ("base", BASE_SIGNS, 0.0, base_side),
        ("offset", OFFSET_SIGNS, CROSSING_OFFSET, offset_side),
    ):
        half_cube = side / sqrt(8)
        vertices = [
            App.Vector(x * half_cube, y * half_cube, z * half_cube)
            for x, y, z in signs
        ]
        cores = []
        for index, (vertex, sign) in enumerate(zip(vertices, signs, strict=True)):
            radial = -_normalized(App.Vector(*sign))  # Seat faces point toward the tetrahedron centre.
            x_neighbour = next(
                other
                for other_index, other in enumerate(vertices)
                if other_index != index and abs(vertex.x - other.x) < 1e-7
            )
            edge = _normalized(x_neighbour - vertex)
            face_normal = App.Vector(1.0 if vertex.x > 0 else -1.0, 0.0, 0.0)
            core_x = _normalized(face_normal.cross(edge))
            core_y = _normalized(radial.cross(core_x))
            core_origin = vertex + App.Vector(*sign) * (offset / 3.0)
            cores.append((core_origin, core_x, core_y, radial))

        used_angles = [set() for _ in vertices]
        for edge_index, (near_index, far_index) in enumerate(EDGES):
            near_vertex, far_vertex = vertices[near_index], vertices[far_index]
            direction = _normalized(far_vertex - near_vertex)
            arms = []
            for endpoint, desired_direction, endpoint_name in (
                (near_index, direction, "near"),
                (far_index, -direction, "far"),
            ):
                core_origin, core_x, core_y, core_z = cores[endpoint]
                candidates = []
                for theta in SEAT_ANGLES:
                    tangent = core_x * sin(radians(theta)) - core_y * cos(radians(theta))
                    target_x = tangent
                    target_z = -core_z
                    target_y = _normalized(target_z.cross(target_x))
                    arm_axis = _normalized(
                        target_x * App.Vector(1, 0, 0).dot(SOURCE_X)
                        + target_y * App.Vector(1, 0, 0).dot(SOURCE_Y)
                        + target_z * App.Vector(1, 0, 0).dot(SOURCE_Z)
                    )
                    candidates.append((arm_axis.dot(desired_direction), theta, target_x, target_y, target_z))
                alignment, theta, target_x, target_y, target_z = max(
                    candidates, key=lambda candidate: candidate[0]
                )
                if alignment < 0.999999:
                    raise RuntimeError(
                        f"arm-to-edge alignment failed: {tetra_name} edge {edge_index} "
                        f"{endpoint_name}, {alignment:.9f}"
                    )
                if theta in used_angles[endpoint]:
                    raise RuntimeError(f"core {tetra_name}:{endpoint} reuses seat {theta:g}°")
                used_angles[endpoint].add(theta)
                target_origin = (
                    core_origin
                    + core_x * (50.0 * cos(radians(theta)))
                    + core_y * (50.0 * sin(radians(theta)))
                    + core_z * core_seat_height
                )
                arm_placement = _source_to_target(
                    SOURCE_ROOT,
                    SOURCE_X,
                    SOURCE_Y,
                    SOURCE_Z,
                    target_origin,
                    target_x,
                    target_y,
                    target_z,
                )
                seat_start = arm_placement.multVec(
                    App.Vector(ARM_SADDLE_START, 0.0, SADDLE_AXIS_Z)
                )
                arms.append((endpoint_name, endpoint, theta, arm_placement, seat_start))
            layout.append((tetra_name, edge_index, cores, direction, arms))
        if any(len(angles) != 3 for angles in used_angles):
            raise RuntimeError(f"{tetra_name} core branches were not assigned once each")
    return layout


def _set_view_property(
    object_: App.DocumentObject, property_name: str, value: object
) -> None:
    view = getattr(object_, "ViewObject", None)
    if view is not None and hasattr(view, property_name):
        setattr(view, property_name, value)


def _add_link(
    document: App.Document,
    name: str,
    label: str,
    source: App.DocumentObject,
    placement: App.Placement,
    parent: App.DocumentObject,
    colour: tuple[float, float, float] | None = None,
    transparency: int | None = None,
) -> App.DocumentObject:
    if not document.FileName:
        raise RuntimeError("assembly document must be saved before creating cross-document links")
    source_document = source.Document
    if source_document is not document and not source_document.FileName:
        raise RuntimeError(
            f"linked source document is unsaved: {source_document.Name}; save it before linking"
        )
    if parent.Document is not document:
        raise RuntimeError(f"link parent belongs to another document: {parent.Name}")
    link = document.addObject("App::Link", name)
    link.Label = label
    link.LinkedObject = source
    link.LinkTransform = True
    link.Placement = placement
    if colour is not None:
        _set_view_property(link, "ShapeColor", colour)
    if transparency is not None:
        _set_view_property(link, "Transparency", transparency)
    parent.addObject(link)
    return link


def _open_source_document(documents: dict, name: str, path: str) -> App.Document:
    document = documents.get(name) or App.openDocument(path)
    if not document.FileName:
        raise RuntimeError(f"{name} is unsaved; save the authoritative source before assembling")
    if os.path.realpath(document.FileName) != os.path.realpath(path):
        raise RuntimeError(
            f"{name} is open from an unexpected path: {document.FileName}; expected {path}"
        )
    return document


def _require_source_object(
    document: App.Document, name: str, expected_type: str
) -> App.DocumentObject:
    source = document.getObject(name)
    if source is None:
        raise RuntimeError(f"{document.Name} is missing required object {name}")
    if source.TypeId != expected_type:
        raise RuntimeError(
            f"{document.Name}.{name} has type {source.TypeId}; expected {expected_type}"
        )
    if not hasattr(source, "Shape") or source.Shape.isNull() or not source.Shape.isValid():
        raise RuntimeError(f"{document.Name}.{name} has no valid shape")
    return source

def _import_step_source(
    document: App.Document,
    name: str,
    label: str,
    filename: str,
    parent: App.DocumentObject,
    colour: tuple[float, float, float],
    transparency: int = 0,
) -> App.DocumentObject:
    path = os.path.join(PROFILE_SOURCE_DIR, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"missing generated source {path}; run export_stella_profile_sources.py first"
        )
    shape = Part.read(path)
    if shape.isNull() or not shape.isValid():
        raise RuntimeError(f"invalid STEP source: {path}")
    source = document.addObject("Part::Feature", name)
    source.Label = label
    source.Shape = shape
    source.addProperty("App::PropertyString", "SourcePath", "Reference")
    source.SourcePath = path
    source.addProperty("App::PropertyString", "Purpose", "Reference")
    source.Purpose = "Exact reference geometry exported from ../build123d-models."
    _set_view_property(source, "ShapeColor", colour)
    _set_view_property(source, "Transparency", transparency)
    parent.addObject(source)
    return source


def build() -> App.Document:
    documents = App.listDocuments()
    if os.path.exists(OUTPUT_PATH):
        raise RuntimeError(
            f"refusing to replace existing assembly: {OUTPUT_PATH}; remove it deliberately first"
        )
    if not os.path.isdir(os.path.dirname(os.path.realpath(OUTPUT_PATH))):
        raise RuntimeError(f"assembly output directory does not exist: {OUTPUT_PATH}")

    core_doc = _open_source_document(documents, "StellaCore", CORE_PATH)
    arm_doc = _open_source_document(documents, "StellaArm", ARM_PATH)
    clamp_doc = _open_source_document(documents, "StellaProfileClamp", CLAMP_PATH)
    core_source = _require_source_object(core_doc, "CoreBody", "PartDesign::Body")
    arm_source = _require_source_object(arm_doc, "ArmBody", "PartDesign::Body")
    connector_source = _require_source_object(arm_doc, "ConnectorBody", "PartDesign::Body")
    clamp_source = _require_source_object(clamp_doc, "ProfileClampBody", "PartDesign::Body")
    if not arm_source.ViewObject.Visibility:
        raise RuntimeError("ArmBody must be visible in StellaArm")
    # ConnectorBody is already fused into ArmBody. Link the final arm only;
    # ConnectorBody may be hidden to avoid duplicate printable solids.
    core_params = core_doc.getObject("StellaParams")
    if core_params is None or "CoreHeight" not in core_params.PropertiesList:
        raise RuntimeError("StellaCore.StellaParams.CoreHeight is required")
    core_seat_height = core_params.CoreHeight.Value
    if core_seat_height <= 0:
        raise RuntimeError("core seat height must be positive")

    initial_side = PROFILE_LENGTH + 2 * ARM_SADDLE_START
    initial_layout = _layout(initial_side, initial_side, core_seat_height)
    base_direction, base_arms = initial_layout[0][3:]
    offset_direction, offset_arms = initial_layout[len(EDGES)][3:]
    base_initial_span = (base_arms[1][4] - base_arms[0][4]).dot(base_direction)
    offset_initial_span = (offset_arms[1][4] - offset_arms[0][4]).dot(offset_direction)
    base_side = initial_side + PROFILE_LENGTH - base_initial_span
    offset_side = initial_side + PROFILE_LENGTH - offset_initial_span
    layout_data = _layout(base_side, offset_side, core_seat_height)
    span_error = 0.0
    line_error = 0.0
    for _, _, _, direction, arms in layout_data:
        delta = arms[1][4] - arms[0][4]
        span_error = max(span_error, abs(delta.dot(direction) - PROFILE_LENGTH))
        line_error = max(line_error, (delta - direction * delta.dot(direction)).Length)
    if span_error > 1e-6 or line_error > 1e-6:
        raise RuntimeError(
            f"profile endpoints do not reconcile: span={span_error:.9f}, line={line_error:.9f}"
        )

    document = App.newDocument("StellaOctangula", "Stella octangula — redesigned arm layout")
    document.saveAs(OUTPUT_PATH)  # Cross-document App::Links require a saved owner.
    document.openTransaction("create redesigned Stella octangula layout")
    try:


        params = document.addObject("App::VarSet", "StellaAssemblyParams")
        params.Label = "Stella octangula layout dimensions"
        for name, value in (
            ("ProfileLength", PROFILE_LENGTH),
            ("ProfileWidth", PROFILE_WIDTH),
            ("ProfileHeight", PROFILE_HEIGHT),
            ("ProfileRimHeight", PROFILE_RIM_Z),
            ("ArmSaddleStart", ARM_SADDLE_START),
            ("CoreSeatHeight", core_seat_height),
            ("CableDiameter", CABLE_DIAMETER),
            ("CrossingOffset", CROSSING_OFFSET),
            ("BaseTetrahedronSide", base_side),
            ("OffsetTetrahedronSide", offset_side),
        ):
            params.addProperty("App::PropertyLength", name, "Layout dimensions")
            setattr(params, name, value)
        params.addProperty("App::PropertyString", "CoreSeatDirection", "Layout dimensions")
        params.CoreSeatDirection = "Inward toward the tetrahedron centre"
        params.addProperty("App::PropertyString", "LayoutIntent", "Layout dimensions")
        params.LayoutIntent = (
            "Twelve complete 1.5 m LED profile assemblies on two interpenetrating "
            "tetrahedra, using exact build123d extrusion, diffuser, endcaps, glands, "
            "and cable stubs. Core seats face inward along each closed-frame edge."
        )

        sources = document.addObject("App::Part", "ReferenceSources")
        sources.Label = "Reference-only build123d source geometry"
        profile_source = _import_step_source(
            document,
            "ProfileExtrusionSource",
            "Exact aluminium LED profile — 26.1 × 30.5 × 1500 mm",
            "profile_extrusion.step",
            sources,
            (0.42, 0.45, 0.49),
        )
        diffuser_source = _import_step_source(
            document,
            "ProfileDiffuserSource",
            "Exact snap-in diffuser",
            "profile_diffuser.step",
            sources,
            (0.95, 0.95, 0.80),
            35,
        )
        endcap_near_source = _import_step_source(
            document,
            "EndcapNearSource",
            "Exact near endcap",
            "endcap_near.step",
            sources,
            (0.20, 0.22, 0.25),
        )
        endcap_far_source = _import_step_source(
            document,
            "EndcapFarSource",
            "Exact far endcap",
            "endcap_far.step",
            sources,
            (0.20, 0.22, 0.25),
        )
        gland_near_source = _import_step_source(
            document,
            "GlandNearSource",
            "Exact near cable gland",
            "gland_near.step",
            sources,
            (0.08, 0.08, 0.09),
        )
        cable_near_source = _import_step_source(
            document,
            "CableNearSource",
            "Actual near cable stub — Ø6.7 mm",
            "cable_near.step",
            sources,
            (0.04, 0.04, 0.05),
        )
        gland_far_source = _import_step_source(
            document,
            "GlandFarSource",
            "Exact far cable gland",
            "gland_far.step",
            sources,
            (0.08, 0.08, 0.09),
        )
        cable_far_source = _import_step_source(
            document,
            "CableFarSource",
            "Actual far cable stub — Ø6.7 mm",
            "cable_far.step",
            sources,
            (0.04, 0.04, 0.05),
        )
        _set_view_property(sources, "Visibility", False)

        assembly = document.addObject("App::Part", "StellaOctangula")
        assembly.Label = "Stella octangula — 12 LED profiles, 8 cores, 24 arms and clamps"
        cores_group = document.addObject("App::Part", "VertexCores")
        cores_group.Label = "Vertex cores — 8 linked instances"
        arms_group = document.addObject("App::Part", "ProfileArms")
        arms_group.Label = "Profile arms — 24 linked instances"
        clamps_group = document.addObject("App::Part", "ProfileClamps")
        clamps_group.Label = "Profile clamps — 24 linked native instances"
        lamps_group = document.addObject("App::Part", "LEDProfileAssemblies")
        lamps_group.Label = "Complete LED profile assemblies — 12 lamps"
        for group in (cores_group, arms_group, clamps_group, lamps_group):
            assembly.addObject(group)


        core_links: dict[tuple[str, int], App.DocumentObject] = {}
        arm_links: list[tuple[App.DocumentObject, App.DocumentObject]] = []
        clamp_links: list[tuple[App.DocumentObject, App.DocumentObject]] = []
        clamp_profile_pairs: list[tuple[App.DocumentObject, App.DocumentObject, App.DocumentObject]] = []
        profile_pairs: list[
            tuple[
                App.DocumentObject,
                App.DocumentObject,
                App.DocumentObject,
                App.DocumentObject,
            ]
        ] = []
        cable_links: list[tuple[App.DocumentObject, App.DocumentObject]] = []
        core_counter = arm_counter = clamp_counter = lamp_counter = 0
        for tetra_name, edge_index, cores, direction, arms in layout_data:
            if edge_index == 0:
                for index, (core_origin, core_x, core_y, core_z) in enumerate(cores):
                    core_placement = _placement_from_axes(core_origin, core_x, core_y, core_z)
                    core_links[(tetra_name, index)] = _add_link(
                        document,
                        f"Core_{tetra_name}_{index}",
                        f"Organic vertex core — {tetra_name} {index}",
                        core_source,
                        core_placement,
                        cores_group,
                        (0.17, 0.20, 0.24),
                    )
                    core_counter += 1

            arm_by_endpoint = {}
            clamp_by_endpoint = {}
            for endpoint_name, endpoint, theta, arm_placement, seat_start in arms:
                arm_link = _add_link(
                    document,
                    f"Arm_{tetra_name}_{edge_index}_{endpoint_name}",
                    f"Profile arm — {tetra_name} edge {edge_index} {endpoint_name}, seat {theta:g}°",
                    arm_source,
                    arm_placement,
                    arms_group,
                    (0.24, 0.27, 0.31),
                )
                arm_by_endpoint[endpoint_name] = (arm_placement, seat_start, arm_link)
                arm_links.append((arm_link, core_links[(tetra_name, endpoint)]))
                arm_counter += 1
                clamp_link = _add_link(
                    document,
                    f"Clamp_{tetra_name}_{edge_index}_{endpoint_name}",
                    f"Profile clamp — {tetra_name} edge {edge_index} {endpoint_name}",
                    clamp_source,
                    arm_placement,
                    clamps_group,
                    (0.48, 0.50, 0.54),
                )
                clamp_by_endpoint[endpoint_name] = clamp_link
                clamp_links.append((clamp_link, arm_link))
                clamp_counter += 1

            near_placement, _, near_arm = arm_by_endpoint["near"]
            _, _, far_arm = arm_by_endpoint["far"]
            profile_placement = near_placement.multiply(
                App.Placement(App.Vector(ARM_SADDLE_START, 0.0, 4.0), App.Rotation())
            )
            lamp = document.addObject("App::Part", f"Lamp_{tetra_name}_{edge_index}")
            lamp.Label = f"LED profile assembly — {tetra_name} lamp {edge_index}"
            lamps_group.addObject(lamp)
            lamp.ViewObject.Visibility = True
            component_specs = (
                ("Aluminium", "Aluminium profile", profile_source, (0.42, 0.45, 0.49), None),
                ("Diffuser", "Diffuser", diffuser_source, (0.95, 0.95, 0.80), 35),
                ("EndcapNear", "Near endcap", endcap_near_source, (0.20, 0.22, 0.25), None),
                ("EndcapFar", "Far endcap", endcap_far_source, (0.20, 0.22, 0.25), None),
                ("GlandNear", "Near cable gland", gland_near_source, (0.08, 0.08, 0.09), None),
                ("CableNear", "Near cable stub", cable_near_source, (0.04, 0.04, 0.05), None),
                ("GlandFar", "Far cable gland", gland_far_source, (0.08, 0.08, 0.09), None),
                ("CableFar", "Far cable stub", cable_far_source, (0.04, 0.04, 0.05), None),
            )
            links = []
            for suffix, label, source, colour, transparency in component_specs:
                links.append(
                    _add_link(
                        document,
                        f"Lamp_{tetra_name}_{edge_index}_{suffix}",
                        f"{label} — {tetra_name} lamp {edge_index}",
                        source,
                        profile_placement,
                        lamp,
                        colour,
                        transparency,
                    )
                )
            (
                aluminium_link,
                diffuser_link,
                _endcap_near_link,
                _endcap_far_link,
                _gland_near_link,
                cable_near_link,
                _gland_far_link,
                cable_far_link,
            ) = links
            cable_links.extend(((cable_near_link, near_arm), (cable_far_link, far_arm)))
            profile_pairs.append((aluminium_link, diffuser_link, near_arm, far_arm))
            clamp_profile_pairs.extend(
                (
                    (clamp_by_endpoint["near"], aluminium_link, diffuser_link),
                    (clamp_by_endpoint["far"], aluminium_link, diffuser_link),
                )
            )
            lamp_counter += 1

        document.recompute()
        params.addProperty("App::PropertyInteger", "ClampInstances", "Layout dimensions")
        params.ClampInstances = clamp_counter
        invalid = [
            obj.Name
            for obj in (
                *core_links.values(),
                *(arm for arm, _ in arm_links),
                *(clamp for clamp, _ in clamp_links),
                *(cable for cable, _ in cable_links),
                *(obj for pair in profile_pairs for obj in pair[:2]),
            )
            if not obj.Shape.isValid()
        ]
        if invalid:
            raise RuntimeError(f"invalid linked geometry: {invalid}")
        max_joint_overlap = max(
            (arm.Shape.common(core.Shape).Volume for arm, core in arm_links), default=0.0
        )
        max_joint_gap = max(
            (arm.Shape.distToShape(core.Shape)[0] for arm, core in arm_links), default=0.0
        )
        max_clamp_arm_overlap = max(
            (clamp.Shape.common(arm.Shape).Volume for clamp, arm in clamp_links), default=0.0
        )
        max_clamp_profile_overlap = max(
            max(
                clamp.Shape.common(aluminium.Shape).Volume,
                clamp.Shape.common(diffuser.Shape).Volume,
            )
            for clamp, aluminium, diffuser in clamp_profile_pairs
        )
        max_cable_overlap = max(
            (cable.Shape.common(arm.Shape).Volume for cable, arm in cable_links),
            default=0.0,
        )
        max_profile_overlap = max(
            max(
                aluminium.Shape.common(near.Shape).Volume,
                aluminium.Shape.common(far.Shape).Volume,
                diffuser.Shape.common(near.Shape).Volume,
                diffuser.Shape.common(far.Shape).Volume,
            )
            for aluminium, diffuser, near, far in profile_pairs
        )
        if max_joint_overlap > 0.01:
            raise RuntimeError(f"arm/core material overlap is too large: {max_joint_overlap:.6f} mm^3")
        if max_joint_gap > 1e-4:
            raise RuntimeError(f"arm/core seating gap is too large: {max_joint_gap:.6f} mm")
        if max_clamp_arm_overlap > 0.01 or max_clamp_profile_overlap > 0.01:
            raise RuntimeError(
                "clamp interference: "
                f"arm={max_clamp_arm_overlap:.6f}, profile={max_clamp_profile_overlap:.6f} mm^3"
            )
        if max_profile_overlap > 0.01:
            raise RuntimeError(f"profile or diffuser intersects its saddle: {max_profile_overlap:.6f} mm^3")
        assembly.addProperty("App::PropertyVolume", "MaxCableArmOverlap", "Validation")
        assembly.MaxCableArmOverlap = max_cable_overlap
        assembly.addProperty("App::PropertyBool", "CableRouteClear", "Validation")
        assembly.CableRouteClear = max_cable_overlap <= 1e-6
        assembly.addProperty("App::PropertyString", "CableRouteNote", "Validation")
        assembly.CableRouteNote = (
            "Axial build123d cable stubs are shown deliberately; non-zero overlap "
            "marks the arm-side clearance that still needs a cabling-hole decision."
        )
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        App.closeDocument(document.Name)
        if os.path.exists(OUTPUT_PATH):
            os.remove(OUTPUT_PATH)
        raise

    document.recompute()
    document.saveAs(OUTPUT_PATH)
    print(
        {
            "file": document.FileName,
            "profiles": lamp_counter,
            "cores": core_counter,
            "arms": arm_counter,
            "clamps": clamp_counter,
            "cable_stubs": len(cable_links),
            "endcaps_per_lamp": 2,
            "glands_per_lamp": 2,
            "base_tetrahedron_side": round(base_side, 6),
            "offset_tetrahedron_side": round(offset_side, 6),
            "profile_span_error": span_error,
            "profile_line_error": line_error,
            "max_arm_core_overlap": max_joint_overlap,
            "max_arm_core_gap": max_joint_gap,
            "max_clamp_arm_overlap": max_clamp_arm_overlap,
            "max_clamp_profile_overlap": max_clamp_profile_overlap,
            "max_cable_arm_overlap": max_cable_overlap,
            "max_profile_saddle_overlap": max_profile_overlap,
        }
    )
    return document


if __name__ == "__main__":
    build()
