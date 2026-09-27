"""Identify Stella's 12 physical LED runs over Art-Net, without saving WLED state.

Close GLED first. Run ``python calibrate_stella.py`` at the star, then record
which physical vertices the green and magenta ends of each numbered edge touch.
"""

import json
import socket
import sys
import threading
from pathlib import Path
from time import sleep
from urllib.request import urlopen
from xml.etree import ElementTree as ET

HOST = "192.168.8.243"
PORT = 6454
ROOT = Path(__file__).parent


def edges():
    ns = {"s": "http://www.w3.org/2000/svg"}
    for path in ET.parse(ROOT / "stella-gled2.svg").findall(".//s:path", ns):
        settings = json.loads(path.find("s:desc", ns).text)
        yield path.get("id"), settings["start"], settings["count"]


def packets(start, count):
    rgb = bytearray(276 * 3)
    if start in (46, 69, 92):  # T1's three lower base corners
        markers = ((0, (0, 0, 36)), (42, (36, 25, 0)), (134, (0, 28, 28)))
    elif start in (161, 184, 253):  # T2's three upper base corners
        markers = ((157, (0, 0, 36)), (207, (36, 25, 0)), (249, (0, 28, 28)))
    else:
        markers = ()
    for first, color in markers:
        for led in range(first, first + 4):
            rgb[led * 3:led * 3 + 3] = color
    for led in range(start, start + count):
        rgb[led * 3:led * 3 + 3] = (12, 12, 12)
    for led in range(start, start + 3):
        rgb[led * 3:led * 3 + 3] = (0, 36, 0)  # first three: green
    for led in range(start + count - 3, start + count):
        rgb[led * 3:led * 3 + 3] = (36, 0, 20)  # last three: magenta
    for universe in (2, 3):
        offset = (universe - 2) * 170 * 3
        payload = bytes(rgb[offset:offset + 510]).ljust(512, b"\0")
        yield (b"Art-Net\0" + b"\x00\x50\x00\x0e\x00\x00"
               + universe.to_bytes(2, "little") + len(payload).to_bytes(2, "big") + payload)


def main():
    edge_list = list(edges())
    assert len(edge_list) == 12 and all(count == 23 for _, _, count in edge_list)
    cfg = json.load(urlopen(f"http://{HOST}/json/cfg", timeout=5))
    live = cfg["if"]["live"]
    if (live["port"], live["dmx"]["uni"], live["dmx"]["addr"], live["dmx"]["mode"]) != (PORT, 2, 1, 4):
        raise SystemExit("STAR-TENT must use Art-Net, universe 2, DMX address 1, Multi RGB")

    selected = 0
    stop = threading.Event()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    frames = tuple(packets(*edge_list[selected][1:]))

    def stream():
        while not stop.is_set():
            for frame in frames:
                sock.sendto(frame, (HOST, PORT))
            stop.wait(0.1)

    sender = threading.Thread(target=stream, daemon=True)
    sender.start()
    try:
        print("Close GLED during calibration. Green = first 3 LEDs; magenta = last 3; white = run.")
        while True:
            name, start, count = edge_list[selected]
            if start in (46, 69, 92, 161, 184, 253):
                slopes = "E1/E2/E6" if start < 138 else "E1/E4/E5"
                print(f"Base-corner markers on sloping edges {slopes}: blue/yellow/cyan.")
            answer = input(f"{name} LEDs {start}–{start + count - 1}: note green→magenta vertices; Enter=next, p=previous, 1–12=select, q=quit > ").strip().lower()
            if answer == "q":
                break
            selected = (selected - 1) % len(edge_list) if answer == "p" else (
                int(answer) - 1 if answer.isdigit() and 1 <= int(answer) <= 12 else
                (selected + 1) % len(edge_list))
            frames = tuple(packets(*edge_list[selected][1:]))
    finally:
        stop.set()
        sender.join()
        sock.close()
        print("Probe stopped; WLED resumes its saved scene after realtime timeout.")


if __name__ == "__main__":
    main()
