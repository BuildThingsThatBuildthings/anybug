"""Rebuild and round-trip a registered specimen using headless Blender."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specimen", nargs="?", default="seven-spot")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "specimens/catalog.json").read_text())
    if args.specimen not in {s["id"] for s in catalog}:
        parser.error("Choose a specimen from specimens/catalog.json")
    blender = os.environ.get("BLENDER") or shutil.which("blender")
    if not blender:
        mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
        blender = str(mac) if mac.is_file() else None
    if not blender:
        parser.error("Install Blender 5.2 or set BLENDER to its executable.")
    folder = ROOT / "specimens" / args.specimen
    with tempfile.TemporaryDirectory(dir=folder) as name:
        staging = Path(name)
        for source in folder.iterdir():
            if source.is_file() and source.name not in {
                "specimen.glb",
                "specimen.blend",
                "anatomy.json",
            }:
                shutil.copy(source, staging)
        for script in ("build.py", "verify.py"):
            subprocess.run(
                [
                    blender,
                    "-b",
                    "--factory-startup",
                    "--python-exit-code",
                    "1",
                    "--python",
                    str(ROOT / "pipeline" / script),
                    "--",
                    str(staging),
                ],
                check=True,
            )
        for output in ("specimen.blend", "specimen.glb", "anatomy.json"):
            os.replace(staging / output, folder / output)


if __name__ == "__main__":
    main()
