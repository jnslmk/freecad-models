"""Check the GLED SVG addresses and embedded project stay in sync."""

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from calibrate_stella import packets

ROOT = Path(__file__).parent
SVG = ROOT / "stella-gled2.svg"
PROJECT = ROOT / "gled2/projects/e41136cc-111a-45cd-8d73-1a35169f29af.json"


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
    lower_end_first = {0: True, 1: False, 5: False, 6: True, 9: False, 10: True}
    for edge, path in enumerate(paths):
        settings = json.loads(path.find("s:desc", ns).text)
        assert path.get("id") == f"T{edge // 6 + 1}-E{edge % 6 + 1}"
        assert settings["start"] == edge * 23 and settings["count"] == 23
        assert {"all", f"tetra{edge // 6 + 1}", path.get("id")} <= set(settings["groups"])
        coords = tuple(map(int, re.findall(r"\d+", path.get("d"))))
        assert len(coords) == 4
        endpoints.append(coords)
        if edge in lower_end_first:
            assert (coords[1] > coords[3]) == lower_end_first[edge]
        tetra_edges[edge // 6].append(frozenset((coords[:2], coords[2:])))
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


if __name__ == "__main__":
    test_mapping()
    print("GLED2 mapping: 276 distinct RGB pixels across universes 2–3")
