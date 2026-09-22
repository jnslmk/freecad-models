"""Build the Stella-octangula layout from the authoritative arm and core files.

Scope: creates only ``StellaOctangula.FCStd``. It opens and links the existing
``StellaCore.FCStd`` and ``StellaArm.FCStd`` files; it never edits either source.
Run inside FreeCAD after the arm carries its CableClearanceEnvelope witness.
"""

from __future__ import annotations

import os
from math import cos, radians, sin, sqrt

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(HERE, "StellaOctangula.FCStd")
CORE_PATH = os.path.join(HERE, "StellaCore.FCStd")
ARM_PATH = os.path.join(HERE, "StellaArm.FCStd")

PROFILE_LENGTH = 1500.0
PROFILE_WIDTH = 26.1
PROFILE_HEIGHT = 30.5
PROFILE_RIM_Z = 16.8
PROFILE_RADIUS = PROFILE_WIDTH / 2
ARM_SADDLE_START = 72.0
SADDLE_AXIS_Z = 19.25
CABLE_DIAMETER = 6.7
CABLE_ENVELOPE_DIAMETER = 7.7
CABLE_BEND_RADIUS = 26.8  # LAPP ÖLFLEX CLASSIC 110, 4 × measured 6.7 mm OD.
CABLE_SERVICE_RADIUS = 45.0
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


def _layout(base_side: float, offset_side: float) -> list[tuple]:
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
                    + core_z * 20.0
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
    link = document.addObject("App::Link", name)
    link.Label = label
    link.LinkedObject = source
    link.LinkTransform = True
    link.Placement = placement
    if colour is not None and hasattr(link.ViewObject, "ShapeColor"):
        link.ViewObject.ShapeColor = colour
    if transparency is not None and hasattr(link.ViewObject, "Transparency"):
        link.ViewObject.Transparency = transparency
    parent.addObject(link)
    return link


def build() -> App.Document:
    if os.path.exists(OUTPUT_PATH):
        raise RuntimeError(f"refusing to replace existing assembly: {OUTPUT_PATH}")

    documents = App.listDocuments()
    core_doc = documents.get("StellaCore") or App.openDocument(CORE_PATH)
    arm_doc = documents.get("StellaArm") or App.openDocument(ARM_PATH)
    core_source = core_doc.getObject("CoreBody")
    arm_source = arm_doc.getObject("ArmBody")
    cable_source = arm_doc.getObject("CableClearanceEnvelope")
    if not all((core_source, arm_source, cable_source)):
        raise RuntimeError("Stella source bodies or cable-clearance witness are unavailable")

    initial_side = PROFILE_LENGTH + 2 * ARM_SADDLE_START
    initial_layout = _layout(initial_side, initial_side)
    base_direction, base_arms = initial_layout[0][3:]
    offset_direction, offset_arms = initial_layout[len(EDGES)][3:]
    base_initial_span = (base_arms[1][4] - base_arms[0][4]).dot(base_direction)
    offset_initial_span = (offset_arms[1][4] - offset_arms[0][4]).dot(offset_direction)
    base_side = initial_side + PROFILE_LENGTH - base_initial_span
    offset_side = initial_side + PROFILE_LENGTH - offset_initial_span
    layout_data = _layout(base_side, offset_side)
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
            ("CableDiameter", CABLE_DIAMETER),
            ("CableEnvelopeDiameter", CABLE_ENVELOPE_DIAMETER),
            ("CableBendRadius", CABLE_BEND_RADIUS),
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
            "Twelve 1.5 m LED profile envelopes on two interpenetrating tetrahedra. "
            "Core seats face inward so the existing keyed arms follow each closed-frame edge; "
            "arm-side cable envelopes remain open and reference-only."
        )

        sources = document.addObject("App::Part", "ReferenceSources")
        sources.Label = "Reference-only source geometry"
        profile_outer = document.addObject("Part::Feature", "ProfileEnvelopeSource")
        profile_outer.Label = "Measured LED profile outer envelope — 26.1 × 30.5 × 1500 mm"
        lower = Part.makeCylinder(
            PROFILE_RADIUS,
            PROFILE_LENGTH,
            App.Vector(0, 0, PROFILE_RADIUS),
            App.Vector(1, 0, 0),
        )
        upper = Part.makeCylinder(
            PROFILE_RADIUS,
            PROFILE_LENGTH,
            App.Vector(0, 0, PROFILE_HEIGHT - PROFILE_RADIUS),
            App.Vector(1, 0, 0),
        )
        middle = Part.makeBox(
            PROFILE_LENGTH,
            PROFILE_WIDTH,
            PROFILE_HEIGHT - PROFILE_WIDTH,
            App.Vector(0, -PROFILE_RADIUS, PROFILE_RADIUS),
        )
        outer_shape = lower.fuse(upper).fuse(middle)
        diffuser_cut = Part.makeBox(
            PROFILE_LENGTH,
            PROFILE_WIDTH + 0.02,
            PROFILE_HEIGHT - PROFILE_RIM_Z,
            App.Vector(0, -PROFILE_RADIUS - 0.01, PROFILE_RIM_Z),
        )
        diffuser_shape = outer_shape.common(diffuser_cut)
        profile_outer.Shape = outer_shape.cut(diffuser_shape)
        profile_outer.addProperty("App::PropertyString", "Purpose", "Reference")
        profile_outer.Purpose = "Reference-only measured aluminium profile envelope; not a manufactured extrusion model."
        profile_outer.ViewObject.ShapeColor = (0.42, 0.45, 0.49)
        diffuser = document.addObject("Part::Feature", "DiffuserEnvelopeSource")
        diffuser.Label = "Reference-only diffuser envelope"
        diffuser.Shape = diffuser_shape
        diffuser.addProperty("App::PropertyString", "Purpose", "Reference")
        diffuser.Purpose = "Reference-only diffuser envelope; retained to show the illuminated surface direction."
        diffuser.ViewObject.ShapeColor = (0.95, 0.95, 0.80)
        diffuser.ViewObject.Transparency = 35
        cable_bend = document.addObject("Part::Feature", "CableBendEnvelopeSource")
        cable_bend.Label = "Reference-only flexible cable bend — R26.8 mm, Ø7.7 mm envelope"
        cable_bend.Shape = Part.makeTorus(
            CABLE_BEND_RADIUS,
            CABLE_ENVELOPE_DIAMETER / 2,
            App.Vector(CABLE_SERVICE_RADIUS + CABLE_BEND_RADIUS, 0.0, 20.0),
            App.Vector(0.0, 1.0, 0.0),
            0.0,
            90.0,
            90.0,
        )
        cable_bend.addProperty("App::PropertyLength", "MinimumBendRadius", "Cable service")
        cable_bend.MinimumBendRadius = CABLE_BEND_RADIUS
        cable_bend.addProperty("App::PropertyString", "Purpose", "Cable service")
        cable_bend.Purpose = "Reference-only 90° cable bend envelope outside the core; no sharp turn or closed threading path."
        cable_bend.ViewObject.ShapeColor = (1.0, 0.55, 0.0)
        cable_bend.ViewObject.Transparency = 55
        sources.addObject(profile_outer)
        sources.addObject(diffuser)
        sources.addObject(cable_bend)
        sources.ViewObject.Visibility = False

        assembly = document.addObject("App::Part", "StellaOctangula")
        assembly.Label = "Stella octangula — 12 LED profiles, 8 cores, 24 cable-clearance arms"
        cores_group = document.addObject("App::Part", "VertexCores")
        cores_group.Label = "Vertex cores — 8 linked instances"
        arms_group = document.addObject("App::Part", "ProfileArms")
        arms_group.Label = "Profile arms — 24 linked instances"
        lamps_group = document.addObject("App::Part", "LEDProfileAssemblies")
        lamps_group.Label = "LED profile assemblies — 12 linked pairs"
        cable_group = document.addObject("App::Part", "CableClearanceRoutes")
        cable_group.Label = "Cable service envelopes — 24 open arm routes plus 24 R26.8 bends"
        for group in (cores_group, arms_group, lamps_group, cable_group):
            assembly.addObject(group)

        core_links: dict[tuple[str, int], App.DocumentObject] = {}
        arm_links: list[tuple[App.DocumentObject, App.DocumentObject]] = []
        profile_pairs: list[tuple[App.DocumentObject, App.DocumentObject, App.DocumentObject]] = []
        cable_links: list[tuple[App.DocumentObject, App.DocumentObject]] = []
        bend_links: list[tuple[App.DocumentObject, App.DocumentObject]] = []
        core_counter = arm_counter = lamp_counter = 0
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
                    for angle in (30.0, 150.0, 270.0):
                        bend_placement = core_placement.multiply(
                            App.Placement(App.Vector(), App.Vector(0, 0, 1), angle)
                        )
                        bend_link = _add_link(
                            document,
                            f"CableBend_{tetra_name}_{index}_{int(angle)}",
                            f"Flexible cable bend — {tetra_name} core {index}, R26.8 mm",
                            cable_bend,
                            bend_placement,
                            cable_group,
                            (1.0, 0.55, 0.0),
                            55,
                        )
                        bend_links.append((bend_link, core_links[(tetra_name, index)]))

            arm_by_endpoint = {}
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
                cable_link = _add_link(
                    document,
                    f"CableRoute_{tetra_name}_{edge_index}_{endpoint_name}",
                    f"Open cable envelope — {tetra_name} edge {edge_index} {endpoint_name}",
                    cable_source,
                    arm_placement,
                    cable_group,
                    (1.0, 0.55, 0.0),
                    55,
                )
                arm_links.append((arm_link, core_links[(tetra_name, endpoint)]))
                cable_links.append((cable_link, arm_link))
                arm_by_endpoint[endpoint_name] = (arm_placement, seat_start, arm_link)
                arm_counter += 1

            near_placement, _, near_arm = arm_by_endpoint["near"]
            _, _, far_arm = arm_by_endpoint["far"]
            profile_placement = near_placement.multiply(
                App.Placement(App.Vector(ARM_SADDLE_START, 0.0, 4.0), App.Rotation())
            )
            lamp = document.addObject("App::Part", f"Lamp_{tetra_name}_{edge_index}")
            lamp.Label = f"LED profile assembly — {tetra_name} lamp {edge_index}"
            lamps_group.addObject(lamp)
            aluminium_link = _add_link(
                document,
                f"Lamp_{tetra_name}_{edge_index}_Aluminium",
                f"Aluminium profile — {tetra_name} lamp {edge_index}",
                profile_outer,
                profile_placement,
                lamp,
                (0.42, 0.45, 0.49),
            )
            _add_link(
                document,
                f"Lamp_{tetra_name}_{edge_index}_Diffuser",
                f"Diffuser — {tetra_name} lamp {edge_index}",
                diffuser,
                profile_placement,
                lamp,
                (0.95, 0.95, 0.80),
                35,
            )
            profile_pairs.append((aluminium_link, near_arm, far_arm))
            lamp_counter += 1

        document.recompute()
        invalid = [
            obj.Name
            for obj in (
                *core_links.values(),
                *(arm for arm, _ in arm_links),
                *(cable for cable, _ in cable_links),
                *(bend for bend, _ in bend_links),
                *(profile[0] for profile in profile_pairs),
            )
            if not obj.Shape.isValid()
        ]
        if invalid:
            raise RuntimeError(f"invalid linked geometry: {invalid}")
        max_joint_overlap = max(
            (arm.Shape.common(core.Shape).Volume for arm, core in arm_links), default=0.0
        )
        max_cable_overlap = max(
            (cable.Shape.common(arm.Shape).Volume for cable, arm in cable_links),
            default=0.0,
        )
        max_bend_core_overlap = max(
            (bend.Shape.common(core.Shape).Volume for bend, core in bend_links), default=0.0
        )
        max_profile_overlap = max(
            max(aluminium.Shape.common(near.Shape).Volume, aluminium.Shape.common(far.Shape).Volume)
            for aluminium, near, far in profile_pairs
        )
        if max_joint_overlap > 0.01:
            raise RuntimeError(f"arm/core material overlap is too large: {max_joint_overlap:.6f} mm^3")
        if max_cable_overlap > 1e-6:
            raise RuntimeError(f"cable envelope intersects arm material: {max_cable_overlap:.6f} mm^3")
        if max_bend_core_overlap > 1e-6:
            raise RuntimeError(
                f"minimum-radius cable bend intersects core material: {max_bend_core_overlap:.6f} mm^3"
            )
        if max_profile_overlap > 0.01:
            raise RuntimeError(f"profile envelope intersects its saddle: {max_profile_overlap:.6f} mm^3")
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
            "cable_routes": len(cable_links),
            "cable_bends": len(bend_links),
            "cable_bend_radius": CABLE_BEND_RADIUS,
            "base_tetrahedron_side": round(base_side, 6),
            "offset_tetrahedron_side": round(offset_side, 6),
            "profile_span_error": span_error,
            "profile_line_error": line_error,
            "max_arm_core_overlap": max_joint_overlap,
            "max_cable_arm_overlap": max_cable_overlap,
            "max_profile_saddle_overlap": max_profile_overlap,
            "max_bend_core_overlap": max_bend_core_overlap,
        }
    )
    return document


if __name__ == "__main__":
    build()
