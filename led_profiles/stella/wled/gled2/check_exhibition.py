#!/usr/bin/env python3
"""Check Stella's native tile schedule and RGB on a real GPU (optional wgpu).

python wled/gled2/check_exhibition.py --schedule-only
uv run --with wgpu python wled/gled2/check_exhibition.py --gled-source /path/to/gled2
GPU checks cover shader output, not GLED's raster sampling, Art-Net, or physical LEDs.
"""

import argparse
import json
import math
from pathlib import Path
import struct

from exhibition import ANIMATION_ID, MODES, PROJECT_ID, ROOT, TILES, endpoints, tile_weights


def close(actual, expected, message, tolerance=2e-5):
    assert len(actual) == len(expected), (message, actual, expected)
    assert max(abs(a - b) for a, b in zip(actual, expected)) <= tolerance, (
        message, actual, expected)


def check_schedule():
    assert TILES == (
        "/scene/grid/2/0", "/scene/grid/0/1", "/scene/grid/1/1",
        "/scene/grid/2/1", "/scene/grid/0/2", "/scene/grid/1/2", "/scene/grid/2/2",
    ), "native tiles must follow build, breath, chase, scan, echoes, counterflow, aurora"
    assert MODES == ("loop", "build", "breath", "chase", "scan", "echoes", "counterflow", "aurora")
    samples = 0

    def expect(seconds, hold, transition, expected, mode="loop", tolerance=1e-9):
        nonlocal samples
        weights = tile_weights(seconds, hold, transition, mode)
        assert len(weights) == 7 and all(math.isfinite(w) and 0 <= w <= 1 for w in weights)
        assert abs(sum(weights) - 1) < 1e-9, ("normalized native output", seconds, weights)
        close(weights, expected, ("tile schedule", seconds, hold, transition, mode), tolerance)
        if tolerance == 1e-9:
            assert {i for i, w in enumerate(weights) if w > 0} == {
                i for i, w in enumerate(expected) if w > 0
            }, ("only scheduled tiles active", seconds, weights)
        samples += 1

    for hold, transition in ((40.0, 6.0), (23.5, 4.0)):
        for chapter in range(7):
            outgoing = [float(i == chapter) for i in range(7)]
            incoming = [float(i == (chapter + 1) % 7) for i in range(7)]
            boundary = (chapter + 1) * hold
            expect(chapter * hold, hold, transition, outgoing)
            expect(boundary - transition, hold, transition, outgoing)
            expect(boundary - transition - 0.001, hold, transition, outgoing)
            # Absolute times exercise starting the runner in the middle of any fade.
            for fraction, weight in ((0.25, 0.15625), (0.5, 0.5), (0.75, 0.84375)):
                expected = [0.0] * 7
                expected[chapter] = 1 - weight
                expected[(chapter + 1) % 7] = weight
                seconds = boundary - transition + transition * fraction
                expect(seconds, hold, transition, expected)
                expect(seconds + 7 * hold, hold, transition, expected)
            expect(boundary - 0.001, hold, transition, incoming, tolerance=1e-6)
            expect(boundary, hold, transition, incoming)
            expect(boundary + 0.001, hold, transition, incoming)
        for index, mode in enumerate(MODES[1:]):
            for seconds in (0.0, hold - transition / 2, 3 * hold, 7 * hold + 1):
                expect(seconds, hold, transition,
                       [float(i == index) for i in range(7)], mode)
    print(f"PASS: {samples} scheduler samples; seven boundaries + wrap, smooth fades, fixed modes")


def check(gled_source):
    import wgpu

    project = json.loads((ROOT / "projects" / f"{PROJECT_ID}.json").read_text())
    animation = json.loads((ROOT / "animations" / f"{ANIMATION_ID}.json").read_text())
    effects = sorted(project["scenes_instances_grid"]["2:0"]["scene"]["effects"],
                     key=lambda effect: effect["animation_config"]["u32_0"])
    positions = endpoints(project["svg"]["svg_contents"])
    edges = [positions[project["groups"][str(effect["group_index"])]] for effect in effects]
    assert len(edges) == 12, "show must address all twelve measured runs"
    assert [effect["animation_config"]["u32_0"] for effect in effects] == list(range(12))
    for mode, address in enumerate(TILES):
        x, y = address.rsplit("/", 2)[1:]
        tile = project["scenes_instances_grid"][f"{x}:{y}"]
        mapped = sorted(tile["scene"]["effects"], key=lambda effect: effect["animation_config"]["u32_0"])
        assert len(mapped) == 12, ("twelve mapped runs per native tile", address)
        assert [effect["group_index"] for effect in mapped] == [effect["group_index"] for effect in effects]
        for edge, effect in enumerate(mapped):
            config = effect["animation_config"]
            assert effect["animation"] == ANIMATION_ID and config["u32_0"] == edge
            assert config["u32_1"] == mode, ("fixed native shader mode", address, edge)
            assert "u32_2" not in config and "float_5" not in config, ("no internal chapter timing", address)
    colors = [project["palette"][name]["rgb"] for name in ("primary", "secondary")]
    palette = colors + [entry["rgb"] for entry in project["palette"]["gradient"]]
    points = [coordinate for x1, y1, x2, y2 in edges for pixel in range(23)
              for coordinate in (x1 + (x2 - x1) * pixel / 22,
                                 y1 + (y2 - y1) * pixel / 22)]

    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    device = adapter.request_device_sync()
    # Keep common.wgsl and the animation intact; only add a compute entry point.
    shader = device.create_shader_module(code=(
        (gled_source / "src/shaders/common.wgsl").read_text()
        + "\n" + animation["shader_code"] + "\n" + """
@group(1) @binding(0) var<storage, read> sample_points: array<vec2<f32>>;
@group(1) @binding(1) var<storage, read_write> sample_rgb: array<vec4<f32>>;
@compute @workgroup_size(32)
fn check_rgb(@builtin(global_invocation_id) id: vec3<u32>) {
    if id.x >= 23u { return; }
    let index = uniforms.u32_0 * 23u + id.x;
    sample_rgb[index] = vec4<f32>(animation(sample_points[index], uniforms.beat_progression), 1.0);
}
"""))
    pipeline = device.create_compute_pipeline(
        layout="auto", compute={"module": shader, "entry_point": "check_rgb"})
    # Each binding exposes exactly the native 1376 bytes; padding is ONLY between
    # binding offsets, to meet the GPU's uniform-buffer alignment requirement.
    alignment = device.limits["min-uniform-buffer-offset-alignment"]
    stride = (1376 + alignment - 1) // alignment * alignment
    uniforms = device.create_buffer(size=12 * stride,
                                    usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST)
    coordinates = device.create_buffer_with_data(
        data=struct.pack(f"<{len(points)}f", *points), usage=wgpu.BufferUsage.STORAGE)
    output = device.create_buffer(size=12 * 23 * 16,
                                  usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC)
    uniform_groups = [device.create_bind_group(
        layout=pipeline.get_bind_group_layout(0), entries=[{
            "binding": 0, "resource": {"buffer": uniforms, "offset": edge * stride, "size": 1376},
        }]) for edge in range(12)]
    samples = device.create_bind_group(layout=pipeline.get_bind_group_layout(1), entries=[
        {"binding": 0, "resource": {"buffer": coordinates, "offset": 0, "size": coordinates.size}},
        {"binding": 1, "resource": {"buffer": output, "offset": 0, "size": output.size}},
    ])
    memory = bytearray(12 * stride)
    for edge in range(12):
        offset = edge * stride
        for index, color in enumerate(palette[:18]):
            struct.pack_into("<3f", memory, offset + index * 16, *color)
        # Palette: 288 bytes. State: 64 bytes. Zero-filled FFT: 1024 bytes.
        struct.pack_into("<7f3I6f", memory, offset + 288,
                         0.0, 0.0, 120.0, 30.0, 1.0, 0.0, 1.0,
                         edge, 0, 0,
                         *edges[edge], 0.0, 0.0)
    cache = {}

    def rgb(mode, seconds):
        key = mode, seconds
        if key not in cache:
            for edge in range(12):
                struct.pack_into("<I", memory, edge * stride + 320, mode - 1)
                struct.pack_into("<f", memory, edge * stride + 344, seconds)
            device.queue.write_buffer(uniforms, 0, memory)
            encoder = device.create_command_encoder()
            compute = encoder.begin_compute_pass()
            compute.set_pipeline(pipeline)
            compute.set_bind_group(1, samples)
            for group in uniform_groups:
                compute.set_bind_group(0, group)
                compute.dispatch_workgroups(1)
            compute.end()
            device.queue.submit([encoder.finish()])
            values = struct.unpack("<1104f", device.queue.read_buffer(output))
            result = [[tuple(values[(edge * 23 + pixel) * 4 + channel] for channel in range(3))
                       for pixel in range(23)] for edge in range(12)]
            assert all(math.isfinite(value) and 0 <= value <= 1
                       for run in result for pixel in run for value in pixel), ("RGB bounds", key)
            cache[key] = result
        return cache[key]

    def level(pixel, edge):
        ratios = [value / color for value, color in zip(pixel, colors[edge // 6])]
        close(ratios, [ratios[0]] * 3, "tetra color must remain proportional")
        return sum(ratios) / 3

    # Whole-edge sequencing, including the explicitly required 1-second frame.
    for built in range(12):
        frame = rgb(1, 1.0 + 1.1 * built)
        for edge, run in enumerate(frame):
            for pixel in run:
                close(pixel, run[0], ("build must illuminate a whole edge", built, edge))
            brightness = level(run[0], edge)
            assert brightness > 0.8 if edge <= built else brightness < 2e-5, (
                "sequential edge build", built, edge, brightness)

    # Reciprocal fades across every pixel, normalized for the two different colors.
    breaths = {}
    for seconds in (0.0, 1.75, 3.5, 7.0, 10.5, 14.0):
        frame = rgb(2, seconds)
        levels = [level(frame[edge][0], edge) for edge in (0, 6)]
        for edge, run in enumerate(frame):
            for pixel in run:
                close(pixel, frame[edge // 6 * 6][0], "whole-tetra fade")
        if breaths:
            close([sum(levels)], [sum(breaths[0.0])],
                  "reciprocal fades must have constant normalized sum")
        breaths[seconds] = levels
    assert breaths[3.5][0] > 0.8 and breaths[3.5][1] < 0.05
    assert breaths[10.5][1] > 0.8 and breaths[10.5][0] < 0.05
    assert breaths[0.0][0] < breaths[1.75][0] < breaths[3.5][0]

    # A head at the same fraction must align physically on slopes, and follow the
    # recorded first-to-last direction on level edges, not SVG left-to-right.
    for fraction_pixel in (0, 5, 11, 17, 22):
        frame = rgb(3, (fraction_pixel / 22 + 0.2) / 1.4 * 7.5)
        reference = [level(pixel, 0) for pixel in frame[0]]
        for edge, run in enumerate(frame):
            profile = [level(pixel, edge) for pixel in run]
            reversed_slope = edges[edge][3] < edges[edge][1] - 1e-5
            aligned = profile[::-1] if reversed_slope else profile
            close(aligned, reference, ("same-fraction chase", fraction_pixel, edge))
            peak = max(range(23), key=profile.__getitem__)
            expected = 22 - fraction_pixel if reversed_slope else fraction_pixel
            assert peak == expected and profile[peak] > 0.8, ("chase physical direction", edge, peak, expected)
            far = 22 if expected < 11 else 0
            assert profile[far] < 0.05, ("chase must remain localized", edge)

    # mapping.md's six measured slope/base corner connections, including BOTH
    # incident base endpoints. Pixel indices are first=0, last=22.
    corners = (
        (0, 0, ((2, 22), (3, 0))),
        (1, 22, ((2, 0), (4, 22))),
        (5, 22, ((3, 22), (4, 0))),
        (6, 22, ((7, 0), (11, 22))),
        (9, 0, ((8, 22), (11, 0))),
        (10, 22, ((7, 22), (8, 0))),
    )
    for seconds in (4.5, 4.9, 5.0, 5.1, 5.5):
        frame = rgb(5, seconds)
        for slope, end, connected in corners:
            for base, pixel in connected:
                close(frame[slope][end], frame[base][pixel],
                      ("echo continuity at connected corner", seconds, slope, base, pixel))
    apex = rgb(5, 5 / 3)
    halfway = rgb(5, 10 / 3)
    corner = rgb(5, 5.0)
    base_middle = rgb(5, 20 / 3)
    for slope, end, connected in corners:
        assert sum(apex[slope][22 - end]) > sum(apex[slope][end]) + 0.5
        assert sum(halfway[slope][11]) > sum(halfway[slope][end]) + 0.5
        assert sum(corner[slope][end]) > sum(corner[slope][11]) + 0.5
        for base, pixel in connected:
            assert sum(corner[base][pixel]) > sum(corner[base][11]) + 0.5
            assert sum(base_middle[base][11]) > sum(base_middle[base][pixel]) + 0.5

    for mode in range(1, 8):
        for seconds in (0.0, 1.0, 3.5, 5.0, 7.5, 14.0, 17.8, 31.999, 40.0, 83.0, 279.999, 280.0, 347.0):
            rgb(mode, seconds)

    def scheduled_rgb(seconds):
        weights = tile_weights(seconds, 40.0, 6.0)
        frames = [(weight, rgb(index + 1, seconds))
                  for index, weight in enumerate(weights) if weight > 0]
        return [[[sum(weight * frame[edge][pixel][channel] for weight, frame in frames)
                  for channel in range(3)] for pixel in range(23)] for edge in range(12)]

    for chapter in range(7):
        boundary = (chapter + 1) * 40.0
        incoming = (chapter + 1) % 7 + 1
        for seconds in (boundary - 0.001, boundary, boundary + 0.001):
            mixed = scheduled_rgb(seconds)
            arriving = rgb(incoming, seconds)
            for edge in range(12):
                for pixel in range(23):
                    close(mixed[edge][pixel], arriving[edge][pixel],
                          ("boundary continuous phase", chapter, seconds))
        # Scheduler weights come from the runner; expectations are independent
        # known smoothstep values, applied to actual GPU frames at global time.
        # This is RGB arithmetic, not a test of GLED's native output mixer.
        for fraction, weight in ((0.25, 0.15625), (0.5, 0.5), (0.75, 0.84375)):
            seconds = boundary - 6.0 + 6.0 * fraction
            mixed = scheduled_rgb(seconds)
            outgoing = rgb(chapter + 1, seconds)
            arriving = rgb(incoming, seconds)
            for edge in range(12):
                for pixel in range(23):
                    expected = [a * (1 - weight) + b * weight
                                for a, b in zip(outgoing[edge][pixel], arriving[edge][pixel])]
                    close(mixed[edge][pixel], expected, ("scheduled RGB arithmetic", chapter, fraction))

    print(f"PASS: {adapter.summary}; {len(cache)} GPU frames, 276 samples/frame; "
          "build, reciprocal breath, aligned chase, connected echoes, seven-mode RGB bounds, scheduled RGB arithmetic")
    device.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule-only", action="store_true", help="check scheduler without wgpu or GLED")
    parser.add_argument("--gled-source", type=Path, help="native GLED source checkout (required for GPU checks)")
    args = parser.parse_args()
    if not args.schedule_only:
        if args.gled_source is None:
            parser.error("--gled-source is required for GPU checks; use --schedule-only for scheduler checks")
        if not (args.gled_source / "src/shaders/common.wgsl").is_file():
            parser.error("--gled-source must contain src/shaders/common.wgsl")
    check_schedule()
    if not args.schedule_only:
        check(args.gled_source.resolve())


if __name__ == "__main__":
    main()
