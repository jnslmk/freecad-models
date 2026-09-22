"""Export the authoritative build123d LED-profile parts for FreeCAD assembly use.

Run from ``../build123d-models``'s environment with this repository as the
current working tree.  The generated STEP files are reference geometry only;
the source build123d models remain authoritative for the bought profile,
endcaps, glands, and cable stubs.
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import export_step

SOURCE_ROOT = Path(__file__).resolve().parent
BUILD123D_ROOT = SOURCE_ROOT.parents[2] / "build123d-models"
OUTPUT = SOURCE_ROOT / "stella_profile_sources"

sys.path.insert(0, str(BUILD123D_ROOT))

from models.led_profiles import endcap, gland, profile  # noqa: E402


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    parts = {
        "profile_extrusion.step": profile.create_extrusion(),
        "profile_diffuser.step": profile.create_diffuser(),
        "endcap_near.step": endcap.seated(),
        "endcap_far.step": endcap.seated(at_far_end=True),
        "gland_near.step": gland.seated()[0],
        "cable_near.step": gland.seated()[1],
        "gland_far.step": gland.seated(at_far_end=True)[0],
        "cable_far.step": gland.seated(at_far_end=True)[1],
    }
    for filename, part in parts.items():
        export_step(part, str(OUTPUT / filename))
    print(f"exported {len(parts)} STEP sources to {OUTPUT}")


if __name__ == "__main__":
    main()
