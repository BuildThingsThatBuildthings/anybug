"""Build, reimport and package the locally authored, single-specimen Blender project."""

import base64
import gzip
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent


def main():
    [entry] = json.loads((ROOT / "specimens/catalog.json").read_text())
    slug = entry["id"]
    subprocess.run(
        [sys.executable, str(ROOT / "rebuild.py"), slug], cwd=ROOT, check=True
    )
    species = ROOT / "specimens" / slug
    manifest = json.loads((species / "anatomy.json").read_text())
    if manifest["id"] != slug or not manifest.get("behavior", {}).get("actions"):
        raise ValueError("Inconsistent specimen ID or missing native behavior")
    template = gzip.decompress((ROOT / "viewer.html.gz").read_bytes()).decode()
    model = (
        "data:model/gltf-binary;base64,"
        + base64.b64encode((species / "specimen.glb").read_bytes()).decode()
    )
    html = template.replace("__ANYBUG_MODEL__", model).replace(
        "__ANYBUG_DATA__", json.dumps(manifest).replace("<", "\\u003c")
    )
    with TemporaryDirectory(dir=ROOT) as work:
        result = Path(work) / "explore.html"
        result.write_text(html, encoding="utf-8")
        result.replace(ROOT / "explore.html")
    print("Built and reimported the Blender specimen. Open", ROOT / "explore.html")


if __name__ == "__main__":
    main()
