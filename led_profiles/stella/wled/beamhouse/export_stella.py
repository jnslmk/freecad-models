"""Export saved Stella CAD links to Beamhouse; never rebuild or save CAD.

Run from any directory with FreeCAD's Python modules available. --check is
read-only and checks CAD provenance, mesh bounds, ownership and wiring.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import struct
import tempfile

import FreeCAD as App

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCENE = HERE / 'stella_octangula.bhs'
MANIFEST = HERE / 'mesh_provenance.json'
EDGES = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
# Mapping records connectivity and elevation, not azimuth or CAD vertex labels.
RUNS = {'base': ((1, 0), (0, 2), (2, 1), (1, 3), (3, 2), (0, 3)),
        'offset': ((1, 0), (0, 2), (2, 3), (3, 1), (1, 2), (3, 0))}
SUFFIXES = ('Aluminium', 'Diffuser', 'EndcapNear', 'EndcapFar',
            'GlandNear', 'GlandFar', 'CableNear', 'CableFar')
ROOM = ((1 / math.sqrt(2), -1 / math.sqrt(2), 0),
        (1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3)),
        (-1 / math.sqrt(6), -1 / math.sqrt(6), 2 / math.sqrt(6)))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def room(v):
    return App.Vector(*(sum(row[i] * v[i] for i in range(3)) for row in ROOM))


def write_glb(path, components):
    """One named mesh per native instance; millimetres become Z-up metres."""
    binary = bytearray()
    doc = {'asset': {'version': '2.0', 'generator': 'Stella native CAD tessellation'},
           'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [], 'meshes': [],
           'bufferViews': [], 'accessors': [], 'materials': []}
    colors = {'Aluminium': [0.42, 0.45, 0.49, 1], 'Diffuser': [1, 1, 1, 1],
              'Core': [0.17, 0.20, 0.24, 1], 'Clamp': [0.48, 0.50, 0.54, 1]}
    all_points = []

    def accessor(values, kind, width):
        offset = len(binary)
        binary.extend(struct.pack('<' + 'f' * len(values), *values))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(binary) - offset})
        acc = {'bufferView': view, 'componentType': 5126, 'count': len(values) // width, 'type': kind}
        if kind == 'VEC3':
            acc['min'] = [min(values[i::3]) for i in range(3)]
            acc['max'] = [max(values[i::3]) for i in range(3)]
        doc['accessors'].append(acc)
        return len(doc['accessors']) - 1

    for name, category, points, triangles in components:
        positions, normals = [], []
        for triangle in triangles:
            a, b, c = [points[i] for i in triangle]
            normal = (b - a).cross(c - a)
            if normal.Length < 1e-12:
                continue
            normal.normalize()
            for point in (a, b, c):
                positions.extend(point)
                normals.extend(normal)
                all_points.append(tuple(point))
        position = accessor(positions, 'VEC3', 3)
        normal = accessor(normals, 'VEC3', 3)
        material = len(doc['materials'])
        doc['materials'].append({'name': category, 'pbrMetallicRoughness': {
            'baseColorFactor': colors.get(category, [0.08, 0.08, 0.09, 1]),
            'metallicFactor': 0.7 if category == 'Aluminium' else 0,
            'roughnessFactor': 0.55}})
        mesh = len(doc['meshes'])
        doc['meshes'].append({'name': name, 'primitives': [{'attributes': {
            'POSITION': position, 'NORMAL': normal}, 'material': material}]})
        doc['scenes'][0]['nodes'].append(len(doc['nodes']))
        doc['nodes'].append({'name': name, 'mesh': mesh})
    doc['buffers'] = [{'byteLength': len(binary)}]
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary += b'\0' * (-len(binary) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(binary)) +
                     struct.pack('<II', len(encoded), 0x4e4f534a) + encoded +
                     struct.pack('<II', len(binary), 0x004e4942) + binary)
    return all_points


def export_to(stage):
    cad = ROOT / 'StellaOctangula.FCStd'
    before = {p.name: digest(p) for p in ROOT.glob('*.FCStd')}
    doc = App.openDocument(str(cad))
    if Path(doc.FileName).resolve() != cad.resolve():
        raise RuntimeError('Wrong assembly document')
    doc.recompute()  # Isolated headless state only; no native file is saved.
    visible_links = [o for o in doc.Objects if o.TypeId == 'App::Link' and o.Visibility]
    assert len(visible_links) == 128
    assert all(o.Shape.isValid() and not o.Shape.isNull() for o in visible_links)
    scene = json.loads(SCENE.read_text())
    scene['definitions'], scene['assets'] = {}, {}
    report = {'sourceSha256': before, 'cadToRoomRotation': ROOM,
              'tessellationDeflectionMm': 0.2, 'runs': [],
              'unmeasured': 'Azimuth and correspondence of named base corners to CAD vertices are illustrative. No LED centre spacing/endpoint inset exists in CAD; 23 equal diffuser texture bins cover its 1500 mm length.'}
    used = []
    tessellations = {}
    for tetra, runs in RUNS.items():
        vertices = [doc.getObject(f'Core_{tetra}_{i}').Placement.Base for i in range(4)]
        heights = [room(v).y for v in vertices]
        apex = 0 if tetra == 'base' else 1
        base = [heights[i] for i in range(4) if i != apex]
        assert max(base) - min(base) < 1e-6
        assert (heights[apex] > base[0]) == (tetra == 'base')
        owners = {v: next(i for i, pair in enumerate(runs) if v in pair) for v in range(4)}
        for run, (first, last) in enumerate(runs):
            fixture = run + 1 + (6 if tetra == 'offset' else 0)
            edge = EDGES.index(tuple(sorted((first, last))))
            direction = room(vertices[last] - vertices[first]); direction.normalize()
            yaw = math.atan2(-direction.z, direction.x)
            tilt = math.asin(max(-1, min(1, direction.y)))
            # Three.js XYZ Euler R_y(yaw) R_z(tilt); native roll is baked into vertices.
            cy, sy, cz, sz = math.cos(yaw), math.sin(yaw), math.cos(tilt), math.sin(tilt)
            axes = (App.Vector(cy * cz, sz, -sy * cz),
                    App.Vector(-cy * sz, cz, sy * sz), App.Vector(sy, 0, cy))
            assert (axes[0] - direction).Length < 1e-8
            def local(point):
                world = room(point)
                q = [world.dot(axis) / 1000 for axis in axes]
                # Inverse of the loader's +90 degree X conversion.
                return App.Vector(q[0], q[2], -q[1])
            objects = [(doc.getObject(f'Lamp_{tetra}_{edge}_{s}'), s) for s in SUFFIXES]
            objects += [(doc.getObject(f'Clamp_{tetra}_{edge}_{end}'), 'Clamp') for end in ('near', 'far')]
            objects += [(doc.getObject(f'Core_{tetra}_{v}'), 'Core') for v in range(4) if owners[v] == run]
            components = {'body': [], 'diffuser': []}
            provenance = []
            for obj, category in objects:
                assert obj is not None and obj.Visibility and obj.Shape.isValid()
                source = obj.LinkedObject.Document.Name + '.' + obj.LinkedObject.Name
                if source not in tessellations:
                    points, triangles = obj.Shape.tessellate(0.2)
                    inverse = obj.Placement.inverse()
                    tessellations[source] = ([inverse.multVec(p) for p in points], triangles)
                native_points, triangles = tessellations[source]
                points = [obj.Placement.multVec(p) for p in native_points]
                components['diffuser' if category == 'Diffuser' else 'body'].append(
                    (obj.Name, category, [local(p) for p in points], triangles))
                used.append(obj.Name)
                provenance.append({'instance': obj.Name, 'source': obj.LinkedObject.Document.Name + '.' + obj.LinkedObject.Name,
                                   'solids': len(obj.Shape.Solids)})
            definition = f'bhs:stella-T{1 if tetra == "base" else 2}-E{run + 1}'
            points = []
            assets = {}
            for kind in ('body', 'diffuser'):
                relative = f'meshes/T{1 if tetra == "base" else 2}-E{run + 1}-{kind}.glb'
                path = stage / relative
                path.parent.mkdir(exist_ok=True)
                points.extend(write_glb(path, components[kind]))
                assets[kind] = relative
            # Use float32 mesh bounds, exactly as GLTFLoader does before centering.
            rounded = [struct.unpack('<fff', struct.pack('<fff', *p)) for p in points]
            center = [(min(p[i] for p in rounded) + max(p[i] for p in rounded)) / 2 for i in range(3)]
            converted = App.Vector(center[0], -center[2], center[1])
            position = sum((axes[i] * converted[i] for i in range(3)), App.Vector())
            for collection in ('fixtures',):
                for item in scene[collection]:
                    if item['id'] == fixture: item['definition'] = definition
            for item in scene['patch']['fixtures']:
                if item['id'] == fixture: item['definition'] = definition
            scene['definitions'][definition] = {'kind': 'strip', 'pixels': 23,
                'pitchMm': doc.StellaAssemblyParams.ProfileLength.Value / 23, 'channelsPerPixel': 3, 'primitive': 'Cylinder'}
            scene['assets'][definition] = assets
            scene['overrides'][str(fixture)] = {'pos': list(position), 'rot': [0, math.degrees(yaw), math.degrees(tilt)]}
            report['runs'].append({'fixture': fixture, 'definition': definition, 'cadEdge': f'{tetra}:{edge}',
                'firstVertex': first, 'lastVertex': last, 'firstRoomMm': list(room(vertices[first])),
                'lastRoomMm': list(room(vertices[last])), 'components': provenance,
                'assets': {kind: {'path': path, 'sha256': digest(stage / path)} for kind, path in assets.items()}})
    assert len(used) == len(set(used)) == 128
    visible = {o.Name for o in doc.Objects if o.TypeId == 'App::Link' and o.Visibility}
    assert set(used) == visible, (set(used) - visible, visible - set(used))
    assert before == {p.name: digest(p) for p in ROOT.glob('*.FCStd')}
    report['componentCounts'] = {'profiles': 12, 'diffusers': 12, 'endcaps': 24, 'glands': 24, 'cables': 24, 'cores': 8, 'clamps': 24}
    report['profileLengthMm'] = doc.StellaAssemblyParams.ProfileLength.Value
    report['crossingOffsetMm'] = doc.StellaAssemblyParams.CrossingOffset.Value
    (stage / SCENE.name).write_text(json.dumps(scene, indent=2) + '\n')
    (stage / MANIFEST.name).write_text(json.dumps(report, indent=2) + '\n')
    # ponytail: validation/export failures leave live assets intact; publication is
    # atomic per file, not across the bundle. A transactional bundle is needed only
    # if readers must load scenes concurrently with regeneration.
    (HERE / 'meshes').mkdir(exist_ok=True)
    for path in sorted((stage / 'meshes').iterdir()):
        path.replace(HERE / 'meshes' / path.name)
    (stage / SCENE.name).replace(SCENE)
    (stage / MANIFEST.name).replace(MANIFEST)
    print(json.dumps({'instances': len(used), 'counts': report['componentCounts'], 'CAD_unchanged': True}))


def export():
    with tempfile.TemporaryDirectory(prefix='.stella-export-', dir=HERE) as temporary:
        export_to(Path(temporary))
    sync_svg()


def diffuser_heights(scene):
    """Match GLTFLoader's float32 bounds, joint centering and XYZ placement."""
    heights = []
    for fixture in scene['fixtures']:
        bounds = {}
        for kind, relative in scene['assets'][fixture['definition']].items():
            data = (HERE / relative).read_bytes()
            length = struct.unpack_from('<I', data, 12)[0]
            gltf = json.loads(data[20:20 + length])
            positions = [gltf['accessors'][p['attributes']['POSITION']]
                         for mesh in gltf['meshes'] for p in mesh['primitives']]
            # Extrema are monotonic under float32 rounding, exactly like POSITION.
            bounds[kind] = [[struct.unpack('<f', struct.pack('<f', value))[0] for value in values]
                            for values in ([min(a['min'][i] for a in positions) for i in range(3)],
                                           [max(a['max'][i] for a in positions) for i in range(3)])]
        center = [(min(b[0][i] for b in bounds.values()) + max(b[1][i] for b in bounds.values())) / 2
                  for i in range(3)]
        lower, upper = bounds['diffuser']
        placement = scene['overrides'][str(fixture['id'])]
        rx, ry, rz = map(math.radians, placement['rot'])

        def world_height(t):
            x = lower[0] + t * (upper[0] - lower[0]) - center[0]
            y = -((lower[2] + upper[2]) / 2 - center[2])
            z = (lower[1] + upper[1]) / 2 - center[1]
            x, y = math.cos(rz) * x - math.sin(rz) * y, math.sin(rz) * x + math.cos(rz) * y
            x, z = math.cos(ry) * x + math.sin(ry) * z, -math.sin(ry) * x + math.cos(ry) * z
            y = math.cos(rx) * y - math.sin(rx) * z
            return (placement['pos'][1] + y) * 1000

        heights.append({'fixture': fixture['id'], 'materialEndsMm': [world_height(0), world_height(1)],
                        'pixelCentresMm': [world_height((pixel + 0.5) / 23) for pixel in range(23)]})
    return heights


def sync_svg():
    """Update only elevation coordinates and the native project's embedded SVG."""
    scene = json.loads(SCENE.read_text())
    heights = diffuser_heights(scene)
    samples = [y for run in heights for y in run['pixelCentresMm']]
    minimum, maximum = min(samples), max(samples)
    svg_path = ROOT / 'wled/gled2/stella_octangula.svg'
    project_path = ROOT / 'wled/gled2/projects/e41136cc-111a-45cd-8d73-1a35169f29af.json'
    svg = svg_path.read_text()
    for index, run in enumerate(heights):
        name = f'T{index // 6 + 1}-E{index % 6 + 1}'
        pattern = rf'(<path id="{name}" d=")([^"]+)(")'
        match = re.search(pattern, svg)
        if match is None:
            raise RuntimeError(f'Missing SVG path {name}')
        coords = list(map(float, re.findall(r'-?\d+(?:\.\d+)?', match[2])))
        first, last = run['pixelCentresMm'][0], run['pixelCentresMm'][-1]
        y1, y2 = [22 + (maximum - y) * 356 / (maximum - minimum) for y in (first, last)]
        path = f'M {coords[0]:g},{y1:.9f} L {coords[2]:g},{y2:.9f}'
        svg = re.sub(pattern, lambda m: m[1] + path + m[3], svg)
    project = json.loads(project_path.read_text())
    project['svg']['svg_contents'] = svg
    report = json.loads(MANIFEST.read_text())
    report['gledElevation'] = {'sampleRangeMm': [minimum, maximum], 'svgYRange': [22, 378],
        'sampling': 'GLED samples endpoints with i/(23-1); SVG endpoints are Beamhouse bin centres 0.5/23 and 22.5/23.',
        'runs': heights}
    svg_path.write_text(svg)
    project_path.write_text(json.dumps(project, indent=2) + '\n')
    MANIFEST.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'sampleRangeMm': [minimum, maximum], 'svgYRange': [22, 378],
                      'runs': [{'fixture': run['fixture'], 'materialEndsMm': run['materialEndsMm'],
                                'firstLastPixelCentresMm': [run['pixelCentresMm'][0], run['pixelCentresMm'][-1]]}
                               for run in heights]}, indent=2))


def check():
    report, scene = json.loads(MANIFEST.read_text()), json.loads(SCENE.read_text())
    assert len(report['runs']) == len(scene['fixtures']) == len(scene['assets']) == 12
    asset_paths = [a['path'] for r in report['runs'] for a in r['assets'].values()]
    assert len(asset_paths) == len(set(asset_paths)) == 24
    mesh_names = []
    assert all(digest(ROOT / name) == sha for name, sha in report['sourceSha256'].items())
    names = [c['instance'] for r in report['runs'] for c in r['components']]
    assert len(names) == len(set(names)) == 128
    expected = ((1, 1, 69), (1, 70, 69), (1, 139, 69), (1, 208, 69), (1, 277, 69), (1, 346, 69),
                (1, 415, 69), (1, 484, 27), (2, 43, 69), (2, 112, 69), (2, 181, 69), (2, 250, 69))
    for run, fixture, address in zip(report['runs'], scene['fixtures'], expected):
        assert fixture['id'] == run['fixture'] and fixture['definition'] == run['definition']
        assert scene['definitions'][run['definition']]['pixels'] == 23
        assert fixture['addresses'][0] == {'universe': address[0] + 2, 'address': address[1], 'footprint': address[2]}
        if fixture['id'] == 8:
            assert fixture['addresses'][1] == {'universe': 4, 'address': 1, 'footprint': 42}
        assert scene['assets'][run['definition']] == {k: a['path'] for k, a in run['assets'].items()}
        assert set(run['assets']) == {'body', 'diffuser'}
        for kind, asset in run['assets'].items():
            path = HERE / asset['path']
            assert digest(path) == asset['sha256']
            data = path.read_bytes()
            magic, version, size = struct.unpack_from('<III', data)
            assert (magic, version, size) == (0x46546c67, 2, len(data))
            length = struct.unpack_from('<I', data, 12)[0]
            gltf = json.loads(data[20:20 + length])
            assert gltf['nodes'] and all(a['count'] > 0 for a in gltf['accessors'])
            node_names = [node['name'] for node in gltf['nodes']]
            expected_names = [c['instance'] for c in run['components']
                              if (c['instance'].endswith('_Diffuser')) == (kind == 'diffuser')]
            assert len(node_names) == len(set(node_names)) and set(node_names) == set(expected_names)
            mesh_names.extend(node_names)
            if kind == 'diffuser':
                accessors = [gltf['accessors'][p['attributes']['POSITION']]
                             for mesh in gltf['meshes'] for p in mesh['primitives']]
                span = max(a['max'][0] for a in accessors) - min(a['min'][0] for a in accessors)
                assert abs(span * 1000 - report['profileLengthMm']) < 0.01
        print(f"Fixture {fixture['id']}: {run['cadEdge']} vertex {run['firstVertex']} -> {run['lastVertex']}; height {run['firstRoomMm'][1]:.3f} -> {run['lastRoomMm'][1]:.3f} mm")
    assert scene['patch']['fixtures'] == scene['fixtures']
    assert len(mesh_names) == len(set(mesh_names)) == 128 and set(mesh_names) == set(names)
    print('CAD hashes, 128 unique native components, 24 GLBs, 276 RGB pixels, LED170 universe split OK')
    print(f"Native profile {report['profileLengthMm']} mm; crossing offset {report['crossingOffsetMm']} mm")
    svg = (ROOT / 'wled/gled2/stella_octangula.svg').read_text()
    project = json.loads((ROOT / 'wled/gled2/stella_octangula.json').read_text())
    assert project['svg']['svg_contents'] == svg
    minimum, maximum = report['gledElevation']['sampleRangeMm']
    for index, run in enumerate(diffuser_heights(scene)):
        name = f'T{index // 6 + 1}-E{index % 6 + 1}'
        path = re.search(rf'<path id="{name}" d="([^"]+)"', svg)
        coords = list(map(float, re.findall(r'-?\d+(?:\.\d+)?', path[1])))
        for pixel, height in enumerate(run['pixelCentresMm']):
            y = coords[1] + (coords[3] - coords[1]) * pixel / 22
            assert abs(height - (maximum - (y - 22) * (maximum - minimum) / 356)) < 0.001
    print('GLED endpoint-inclusive samples match all 276 diffuser bin-centre elevations within 0.001 mm')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Read-only provenance, dimensions and mapping check')
    mode.add_argument('--sync-svg', action='store_true', help='Update GLED elevation from existing meshes without CAD export')
    args = parser.parse_args()
    if args.check:
        check()
    elif args.sync_svg:
        sync_svg()
    else:
        export()
