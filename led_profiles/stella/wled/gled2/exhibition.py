#!/usr/bin/env python3
"""Run the native Stella show in an isolated GLED profile; never edit personal assets.

GLED's shader beat curve repeats every four beats. This small OSC clock supplies
real elapsed seconds and crossfades seven native scene tiles independently of tempo.
"""

import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import struct
import subprocess
import time
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT_ID = "e41136cc-111a-45cd-8d73-1a35169f29af"
ANIMATION_ID = "80182491-76a5-4ac8-a74f-f7072673d6e8"
TILES = ("/scene/grid/2/0", "/scene/grid/0/1", "/scene/grid/1/1",
         "/scene/grid/2/1", "/scene/grid/0/2", "/scene/grid/1/2", "/scene/grid/2/2")
TILE_NAMES = ("Edge build", "Tetra breath", "Edge chase", "Stellar scan",
              "Vertex echoes", "Counterflow", "Aurora")
MODES = ("loop", "build", "breath", "chase", "scan", "echoes", "counterflow", "aurora")


def tile_weights(seconds, hold, transition, mode="loop"):
    """Return native scene weights, fading into the next tile at each hold's end."""
    weights = [0.0] * len(TILES)
    if mode != "loop":
        weights[MODES.index(mode) - 1] = 1.0
    else:
        chapter, elapsed = divmod(seconds, hold)
        current = int(chapter) % len(TILES)
        progress = max(0.0, min(1.0, (elapsed - hold + transition) / transition))
        incoming = progress * progress * (3.0 - 2.0 * progress)
        weights[current] = 1.0 - incoming
        weights[(current + 1) % len(TILES)] = incoming
    return tuple(weights)


def clock_tiles(sock, destination, seconds, hold, transition, mode="loop", previous=None):
    """Clock only visible tiles before applying opacity and activation changes."""
    weights = tile_weights(seconds, hold, transition, mode)
    # GLED accepts individual messages, not OSC bundles. Prime incoming shaders first.
    for tile, weight in zip(TILES, weights):
        if weight > 0:
            for edge in range(12):
                sock.sendto(message(f"{tile}/effect/{edge}/config/f32/4", seconds), destination)
    for index, (tile, weight) in enumerate(zip(TILES, weights)):
        if previous is None or weight != previous[index]:
            sock.sendto(message(tile + "/opacity", weight), destination)
        if previous is None or (weight > 0) != (previous[index] > 0):
            sock.sendto(message(tile + "/active", weight > 0), destination)
    return weights


def osc_string(value):
    data = value.encode() + b"\0"
    return data + bytes(-len(data) % 4)


def message(address, value=None):
    if value is None:
        return osc_string(address) + osc_string(",")
    if isinstance(value, bool):
        return osc_string(address) + osc_string(",T" if value else ",F")
    kind = "i" if isinstance(value, int) else "f"
    return osc_string(address) + osc_string("," + kind) + struct.pack(">" + kind, value)


def feedback(packet):
    end = packet.index(0)
    address = packet[:end].decode()
    offset = (end + 4) & ~3
    end = packet.index(0, offset)
    tag = packet[offset:end].decode()
    offset = (end + 4) & ~3
    if tag == ",s":
        return address, packet[offset:packet.index(0, offset)].decode()
    if tag in (",i", ",f"):
        return address, struct.unpack_from(">" + tag[1], packet, offset)[0]
    if tag in (",T", ",F"):
        return address, tag == ",T"
    return address, None


def endpoints(svg):
    root = ET.fromstring(svg)
    width, height = float(root.get("width")), float(root.get("height"))
    result = {}
    for path in root.findall(".//{http://www.w3.org/2000/svg}path"):
        coords = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", path.get("d"))]
        if len(coords) != 4 or not path.get("d").startswith("M ") or " L " not in path.get("d"):
            raise ValueError("Stella exhibition requires straight M/L edge paths")
        x1, y1, x2, y2 = coords
        result[path.get("id")] = (x1 / width, 1 - y1 / height, x2 / width, 1 - y2 / height)
    return result


def prepare(profile, installed, args):
    data = profile / "data/gled2"
    data.mkdir(parents=True, exist_ok=True)
    if not (data / ".git").exists():
        # GLED requires its asset directory to be a Git repository, even offline.
        subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(data)], check=True)
    project = json.loads((ROOT / "projects" / f"{PROJECT_ID}.json").read_text())
    positions = endpoints(project["svg"]["svg_contents"])
    weights = tile_weights(args.start_at, args.hold, args.transition, args.mode)
    for scene in project["scenes_instances_grid"].values():
        scene["active"] = False
    for tile, weight in zip(TILES, weights):
        col, row = tile.split("/")[-2:]
        scene = project["scenes_instances_grid"][f"{col}:{row}"]
        scene["active"] = weight > 0
        scene["opacity"] = {"multiplier": weight, "curve": None, "sound_trigger": None}
        for effect in scene["scene"]["effects"]:
            config = effect["animation_config"]
            name = project["groups"][str(effect["group_index"])]
            # Raw F32 slots avoid Percentage widgets rewriting time to multiplier=1.
            for index, value in enumerate((*positions[name], args.start_at)):
                config[f"float_{index}"] = {"F32": value}
    project["osc_config"] = {"active": True, "port": args.port}
    for routing in project["output_routings"]["routings"].values():
        routing.pop("mirror_device", None)
    for directory, ids in (
        ("animations", {effect["animation"] for scene in project["scenes_instances_grid"].values()
                        for effect in scene["scene"]["effects"]}),
        ("curves", {"2e075ccb-90c4-474b-8d16-c670405499a6"}),
        ("output_devices", {"a2078bd5-a076-421b-9b35-a38fe2c1d794"}),
        ("palettes", {asset.stem for directory in (installed / "palettes", ROOT / "palettes")
                      for asset in directory.glob("*.json")}),
    ):
        (data / directory).mkdir(exist_ok=True)
        for asset in ids:
            relative = Path(directory) / f"{asset}.json"
            if directory == "palettes" and (data / relative).exists():
                continue
            source = ROOT / relative
            if not source.exists():
                source = installed / relative
            shutil.copyfile(source, data / relative)
    if not args.live:
        device_path = data / "output_devices/a2078bd5-a076-421b-9b35-a38fe2c1d794.json"
        device = json.loads(device_path.read_text())
        device["Artnet"]["ip"] = "127.0.0.1"
        # BeamHouse listens on 6455 by default (gled2 owns 6454); keep the
        # preview stream addressed at the visualiser, not gled2's own input.
        device["Artnet"]["port"] = 6455
        device_path.write_text(json.dumps(device, indent=2) + "\n")
    (data / "projects").mkdir(exist_ok=True)
    (data / "projects" / f"{PROJECT_ID}.json").write_text(json.dumps(project, indent=2) + "\n")
    shutil.copyfile(installed / "version", data / "version")
    (profile / ".gled").write_text(json.dumps({
        "last_project_id": PROJECT_ID, "fps_limit": 30.0,
        "effects_always_render": False, "ableton_link_read_only": True,
    }) + "\n")
    return data


def wait_ready(sock, destination, process):
    deadline = time.monotonic() + 30
    expected = {tile + "/name": name for tile, name in zip(TILES, TILE_NAMES)}
    expected.update({tile + "/effect/count": 12 for tile in TILES})
    seen = {}
    sock.sendto(message("/osc/state/subscribe"), destination)
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"GLED exited with status {process.returncode}")
        try:
            packet, sender = sock.recvfrom(65535)
        except socket.timeout:
            sock.sendto(message("/osc/state/subscribe"), destination)
            continue
        if sender != destination:
            continue
        address, value = feedback(packet)
        if address in expected:
            seen[address] = value
        if all(seen.get(address) == value for address, value in expected.items()):
            sock.sendto(message("/osc/state/unsubscribe"), destination)
            return
    raise RuntimeError("GLED did not load all seven exhibition tiles with 12 effects or enable OSC within 30 seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="send to STAR-TENT; default is localhost preview only")
    parser.add_argument("--hold", type=float, default=40, help="seconds per chapter, including transition (default: 40)")
    parser.add_argument("--transition", type=int, default=6, help="crossfade seconds (1–15, default: 6)")
    parser.add_argument("--mode", choices=MODES, default="loop", help="loop or preview one animation")
    parser.add_argument("--start-at", type=float, default=0, help="start at this show time in seconds")
    parser.add_argument("--duration", type=float, help="stop after this many seconds; omitted runs indefinitely")
    parser.add_argument("--port", type=int, default=18765, help="local GLED OSC port")
    parser.add_argument("--profile", type=Path, default=Path.home() / ".local/state/stella-exhibition")
    parser.add_argument("--gled", default=shutil.which("gled"), help="GLED executable")
    args = parser.parse_args()
    if (not math.isfinite(args.hold) or args.hold <= args.transition
            or not 1 <= args.transition <= 15 or not 1 <= args.port <= 65535
            or not math.isfinite(args.start_at) or args.start_at < 0
            or args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0)):
        parser.error("require finite hold > transition, transition 1–15, valid port, nonnegative start time, positive duration")
    if not args.gled:
        parser.error("GLED is not installed; provide --gled /path/to/gled")
    profile = args.profile.expanduser().resolve()
    profile.mkdir(parents=True, exist_ok=True)
    with (profile / "runner.lock").open("w") as lock, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Refuse to send a clock to an unrelated GLED instance on an occupied port.
        sock.bind(("127.0.0.1", args.port))
        sock.close()
        installed = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "gled2"
        prepare(profile, installed, args)
        environment = dict(os.environ, HOME=str(profile), XDG_DATA_HOME=str(profile / "data"),
                           XDG_CONFIG_HOME=str(profile / "config"), GLED_FPS_LIMIT="30")
        with (profile / "gled.log").open("w") as log:
            process = subprocess.Popen([args.gled], env=environment, stdout=log, stderr=subprocess.STDOUT)
            destination = ("127.0.0.1", args.port)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as clock:
                    clock.settimeout(0.25)
                    wait_ready(clock, destination, process)
                    weights = clock_tiles(clock, destination, args.start_at,
                                          args.hold, args.transition, args.mode)
                    clock.sendto(message("/project/blackout", False), destination)
                    print(f"Ready: {'STAR-TENT' if args.live else 'localhost preview'}, "
                          f"{args.hold:g}s chapters / {args.transition}s fades, "
                          f"{args.hold * len(TILES):g}s loop; log: {profile / 'gled.log'}", flush=True)
                    started = time.monotonic()
                    chapter = None
                    while process.poll() is None:
                        elapsed = time.monotonic() - started
                        if args.duration is not None and elapsed >= args.duration:
                            break
                        show_time = args.start_at + elapsed
                        # ponytail: a local 30 Hz OSC clock; no scheduler daemon or app fork.
                        weights = clock_tiles(clock, destination, show_time, args.hold,
                                              args.transition, args.mode, weights)
                        current = int(show_time / args.hold) % len(TILES) if args.mode == "loop" else MODES.index(args.mode) - 1
                        if current != chapter:
                            chapter = current
                            print(f"{show_time:8.1f}s  {MODES[current + 1]}", flush=True)
                        time.sleep(1 / 30)
                    if process.poll() not in (None, 0):
                        raise RuntimeError(f"GLED exited with status {process.returncode}; see {profile / 'gled.log'}")
            finally:
                if process.poll() is None:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as stop:
                        stop.sendto(message("/project/blackout", True), destination)
                    time.sleep(0.15)
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    try:
        main()
    except KeyboardInterrupt:
        pass
