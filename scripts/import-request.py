"""Import an approved Bugapedia request into the ignored private modeling inbox."""

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = re.compile(r"[0-9]{13}-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
SPECIES_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def text_field(data, key, limit, required=True):
    value = data.get(key)
    if not isinstance(value, str) or len(value) > limit or (value and not value.isprintable()):
        raise ValueError(f"Invalid {key}.")
    if required and not value.strip():
        raise ValueError(f"Missing {key}.")
    return value.strip()


def import_request(packet, root):
    if packet.stat().st_size > 5_000_000:
        raise ValueError("The request file is too large.")
    data = json.loads(packet.read_bytes())
    if not isinstance(data, dict) or data.get("format") != "anybug-request-v1":
        raise ValueError("Choose an exported Bugapedia request.")
    decision, observation = data.get("decision"), data.get("observation")
    if not isinstance(decision, dict) or decision.get("status") != "approved" or not isinstance(observation, dict):
        raise ValueError("A curator-approved decision and observation are required.")
    request_id = text_field(data, "id", 50)
    species = text_field(decision, "speciesId", 70)
    if not REQUEST_ID.fullmatch(request_id) or not SPECIES_ID.fullmatch(species):
        raise ValueError("Invalid request or species ID.")
    name = text_field(decision, "name", 100)
    focus = text_field(decision, "focus", 240)
    guess = text_field(observation, "name", 80, False)
    note = text_field(observation, "note", 240, False)
    encoded = data.get("photo")
    if not isinstance(encoded, str):
        raise ValueError("Missing reference photo.")
    image = base64.b64decode(encoded, validate=True)
    if not image.startswith(b"\xff\xd8\xff") or not image.endswith(b"\xff\xd9"):
        raise ValueError("Invalid JPEG reference.")
    # Plain text keeps visitor observations inert when viewed in a browser or editor.
    brief = (f"Approved specimen request {request_id}\n\nSpecies: {name} ({species})\n"
             f"Curator's modeling focus: {focus}\n\nVisitor's tentative identification: {guess or '(none)'}\n"
             f"Visitor's observation: {note or '(none)'}\n\nReference: reference.jpg (private)\n"
             "Check identification and anatomy against published sources before authoring the model.\n")
    inbox = root / "private" / "requests"
    inbox.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = inbox / request_id
    files = {"reference.jpg": image, "brief.txt": brief.encode("utf-8")}
    if not target.exists():
        with tempfile.TemporaryDirectory(dir=inbox) as temporary:
            staging = Path(temporary) / "request"
            staging.mkdir(mode=0o700)
            for filename, contents in files.items():
                with os.fdopen(os.open(staging / filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as stream:
                    stream.write(contents)
            try:
                staging.rename(target)
            except OSError:
                if not target.is_dir():
                    raise
    if any((target / filename).read_bytes() != contents for filename, contents in files.items()):
        raise ValueError("A different request already uses this reference. Existing files were preserved.")
    return target, species


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--rebuild", action="store_true", help="Run the existing local Blender builder for a registered species.")
    args = parser.parse_args()
    try:
        folder, species = import_request(args.packet, ROOT)
    except (OSError, ValueError, binascii.Error) as error:
        parser.exit(1, f"Could not import request: {error}\n")
    print(f"Private reference and brief: {folder}")
    catalog = json.loads((ROOT / "specimens/catalog.json").read_text())
    authored = any(item["id"] == species for item in catalog) and (ROOT / "specimens" / species / "build.py").is_file()
    if authored:
        if args.rebuild:
            subprocess.run([sys.executable, str(ROOT / "rebuild.py"), species], cwd=ROOT, check=True)
        else:
            print(f"To rebuild the authored specimen: python3 rebuild.py {species}")
    else:
        print(f"Follow docs/ADDING-A-SPECIES.md to author and register specimens/{species}.")
        if args.rebuild:
            parser.exit(1, "The brief is ready. A local builder is required before this species can be rebuilt.\n")


if __name__ == "__main__":
    main()
