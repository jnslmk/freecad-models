"""Check the GLED SVG addresses and embedded project stay in sync."""

import json
import math
import re
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

from calibrate_stella import packets

ROOT = Path(__file__).parent
SVG = ROOT / "gled2/stella_octangula.svg"
PROJECT = ROOT / "gled2/stella_octangula.json"


def test_mapping():
    project = json.loads(PROJECT.read_text())
    assert project["svg"]["svg_contents"] == SVG.read_text()
    ns = {"s": "http://www.w3.org/2000/svg"}
    root = ET.parse(SVG).getroot()
    paths = root.findall(".//s:path", ns)
    assert len(paths) == 12
    tetra_edges = [[], []]
    pixels = set()
    endpoints = []
    provenance = json.loads((ROOT / "beamhouse/mesh_provenance.json").read_text())
    lower_end_first = {0: True, 1: False, 5: False, 6: True, 9: False, 10: True}
    for edge, path in enumerate(paths):
        settings = json.loads(path.find("s:desc", ns).text)
        assert path.get("id") == f"T{edge // 6 + 1}-E{edge % 6 + 1}"
        assert settings["start"] == edge * 23 and settings["count"] == 23
        assert {"all", f"tetra{edge // 6 + 1}", path.get("id")} <= set(settings["groups"])
        coords = tuple(map(float, re.findall(r"-?\d+(?:\.\d+)?", path.get("d"))))
        assert len(coords) == 4
        run = provenance["runs"][edge]
        # Connectivity belongs to connector vertices, not inset diffuser samples.
        corners = (coords[0], -run["firstRoomMm"][1], coords[2], -run["lastRoomMm"][1])
        endpoints.append(corners)
        if edge not in lower_end_first:
            assert math.isclose(coords[1], coords[3], abs_tol=1e-7)
        if edge in lower_end_first:
            assert (coords[1] > coords[3]) == lower_end_first[edge]
        tetra_edges[edge // 6].append(frozenset((corners[:2], corners[2:])))
        pixels.update((settings["universe"] + led // 170, led % 170)
                      for led in range(settings["start"], settings["start"] + settings["count"]))
    assert endpoints[2][:2] == endpoints[1][2:]  # T1-E3 green meets E2.
    assert endpoints[2][2:] == endpoints[0][:2]  # T1-E3 magenta meets E1.
    assert endpoints[3][:2] == endpoints[0][:2]  # T1-E4 green meets E1.
    assert endpoints[3][2:] == endpoints[5][2:]  # T1-E4 magenta meets E6.
    assert endpoints[4][:2] == endpoints[5][2:]  # T1-E5 green meets E6.
    assert endpoints[4][2:] == endpoints[1][2:]  # T1-E5 magenta meets E2.
    assert endpoints[7][:2] == endpoints[6][2:]  # T2-E2 green meets E1.
    assert endpoints[7][2:] == endpoints[10][2:]  # T2-E2 magenta meets E5.
    assert endpoints[8][:2] == endpoints[10][2:]  # T2-E3 green meets E5.
    assert endpoints[8][2:] == endpoints[9][:2]  # T2-E3 magenta meets E4.
    assert endpoints[11][:2] == endpoints[9][:2]  # T2-E6 green meets E4.
    assert endpoints[11][2:] == endpoints[6][2:]  # T2-E6 magenta meets E1.
    for tetra_index, tetra in enumerate(tetra_edges):
        vertices = set().union(*tetra)
        assert len(vertices) == 4 and len(set(tetra)) == 6
        assert all(sum(vertex in pair for pair in tetra) == 3 for vertex in vertices)
        apex = (min if tetra_index == 0 else max)(vertices, key=lambda point: point[1])
        sloping = {i + 1 for i, pair in enumerate(tetra) if apex in pair}
        assert sloping == ({1, 2, 6} if tetra_index == 0 else {1, 4, 5})
        base = {vertex for vertex in vertices if vertex != apex}
        assert len({vertex[1] for vertex in base}) == 1  # A level physical triangle scans together.
    assert pixels == {(2 + led // 170, led % 170) for led in range(276)}
    assert set(project["output_routings"]["routings"]) == {"2", "3"}
    first, second = packets(161, 23)  # T2-E2 crosses the universe boundary.
    assert first[18 + 161 * 3:18 + 164 * 3] == bytes((0, 36, 0)) * 3
    assert second[18:21] == bytes((12, 12, 12))  # LED 170
    assert second[18 + 13 * 3:18 + 14 * 3] == bytes((36, 0, 20))  # LED 183
    assert first[18:21] == second[18 + 14 * 3:18 + 15 * 3] == bytes(3)
    assert first[18 + 157 * 3:18 + 161 * 3] == bytes((0, 0, 36)) * 4
    assert second[18 + 37 * 3:18 + 41 * 3] == bytes((36, 25, 0)) * 4
    assert second[18 + 79 * 3:18 + 83 * 3] == bytes((0, 28, 28)) * 4
    first, _ = packets(46, 23)
    assert first[18:30] == bytes((0, 0, 36)) * 4
    assert first[18 + 42 * 3:18 + 46 * 3] == bytes((36, 25, 0)) * 4
    assert first[18 + 134 * 3:18 + 138 * 3] == bytes((0, 28, 28)) * 4


def test_beamhouse_project():
    scene = json.loads((ROOT / "beamhouse/stella_octangula.bhs").read_text())
    fixtures = scene["fixtures"]
    assert len(fixtures) == 12 and scene["patch"]["fixtures"] == fixtures
    provenance = json.loads((ROOT / "beamhouse/mesh_provenance.json").read_text())
    endpoints = []
    owned = []
    paths = ET.parse(SVG).getroot().findall(".//{http://www.w3.org/2000/svg}path")
    minimum, maximum = provenance["gledElevation"]["sampleRangeMm"]
    for index, fixture in enumerate(fixtures):
        assert fixture["id"] == index + 1
        start = index * 23
        first = min(23, max(0, 170 - start))
        expected = []
        if first:
            expected.append({"universe": 3, "address": 3 * start + 1, "footprint": 3 * first})
        if first < 23:
            expected.append({"universe": 4, "address": 3 * max(0, start - 170) + 1,
                             "footprint": 3 * (23 - first)})
        assert fixture["addresses"] == expected
        definition = scene["definitions"][fixture["definition"]]
        assert definition["pixels"] == 23 and definition["channelsPerPixel"] == 3
        run = provenance["runs"][index]
        assert run["fixture"] == fixture["id"]
        owned.extend(component["instance"] for component in run["components"])
        assets = scene["assets"][fixture["definition"]]
        bounds = {}
        for kind in ("body", "diffuser"):
            data = (ROOT / "beamhouse" / assets[kind]).read_bytes()
            json_length = struct.unpack_from("<I", data, 12)[0]
            gltf = json.loads(data[20:20 + json_length])
            positions = [gltf["accessors"][primitive["attributes"]["POSITION"]]
                         for mesh in gltf["meshes"] for primitive in mesh["primitives"]]
            bounds[kind] = (
                [min(accessor["min"][axis] for accessor in positions) for axis in range(3)],
                [max(accessor["max"][axis] for accessor in positions) for axis in range(3)],
            )
        assert math.isclose((bounds["diffuser"][1][0] - bounds["diffuser"][0][0]) * 1000,
                            provenance["profileLengthMm"], abs_tol=0.01)
        position = scene["overrides"][str(index + 1)]["pos"]
        rx, ry, rz = map(math.radians, scene["overrides"][str(index + 1)]["rot"])

        def rotate(point):
            x, y, z = point
            x, y = math.cos(rz) * x - math.sin(rz) * y, math.sin(rz) * x + math.cos(rz) * y
            x, z = math.cos(ry) * x + math.sin(ry) * z, -math.sin(ry) * x + math.cos(ry) * z
            y, z = math.cos(rx) * y - math.sin(rx) * z, math.sin(rx) * y + math.cos(rx) * z
            return x, y, z

        # Diffuser +X is electrical first→last, independent of owned hardware bounds.
        direction = rotate((1, 0, 0))
        first, last = run["firstRoomMm"], run["lastRoomMm"]
        length = math.dist(first, last)
        assert all(math.isclose(direction[axis], (last[axis] - first[axis]) / length,
                                abs_tol=1e-9) for axis in range(3))
        center = [(min(bounds[k][0][a] for k in bounds) +
                   max(bounds[k][1][a] for k in bounds)) / 2 for a in range(3)]
        # Loader converts Z-up→Y-up, then jointly centers both assets.
        restored = rotate((center[0], -center[2], center[1]))
        assert all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(position, restored))
        coords = tuple(map(float, re.findall(r"-?\d+(?:\.\d+)?", paths[index].get("d"))))
        lower, upper = bounds["diffuser"]
        for pixel in range(23):
            t = (pixel + 0.5) / 23
            local = (lower[0] + t * (upper[0] - lower[0]) - center[0],
                     -((lower[2] + upper[2]) / 2 - center[2]),
                     (lower[1] + upper[1]) / 2 - center[1])
            height = (position[1] + rotate(local)[1]) * 1000
            # GLED samples SVG endpoint-inclusive i/22, matching diffuser bin centres.
            svg_y = coords[1] + (coords[3] - coords[1]) * pixel / 22
            mapped_height = maximum - (svg_y - 22) * (maximum - minimum) / 356
            assert math.isclose(height, mapped_height, abs_tol=0.001)
        endpoints.append((tuple(first), tuple(last)))

    assert len(owned) == len(set(owned)) == sum(provenance["componentCounts"].values())

    for edges, names, above in (
        (endpoints[:6], (("B", "A"), ("A", "C"), ("C", "B"),
                         ("B", "D"), ("D", "C"), ("A", "D")), True),
        (endpoints[6:], (("A", "B"), ("B", "D"), ("D", "C"),
                         ("C", "A"), ("A", "D"), ("C", "B")), False),
    ):
        vertices = {}
        for edge, (start, end) in zip(edges, names):
            for point, name in zip(edge, (start, end)):
                if name in vertices:
                    assert all(math.isclose(a, b, abs_tol=1e-9)
                               for a, b in zip(point, vertices[name]))
                vertices[name] = point
            assert math.dist(*edge) > provenance["profileLengthMm"]
        assert len({round(vertices[name][1], 9) for name in ("B", "C", "D")}) == 1
        assert (vertices["A"][1] > vertices["B"][1]) == above

if __name__ == "__main__":
    test_mapping()
    test_beamhouse_project()
    print("GLED2 mapping: 276 distinct RGB pixels across universes 2–3")
