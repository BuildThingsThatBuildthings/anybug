"""Package the private-installable ChatGPT skill from explicit source inputs."""
import argparse
import gzip
import sys
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/"skills/bugapedia-photo"
sys.dont_write_bytecode=True
sys.path.insert(0,str(SKILL/"scripts"))
from portable_viewer import template

FILES=("SKILL.md","agents/openai.yaml","scripts/build_specimen.py","scripts/check_specimen.py",
       "scripts/model.py","scripts/geometry.py","scripts/portable_viewer.py",
       "references/format.md","references/earwig_example.py")


def package(destination):
    items={name:(SKILL/name).read_bytes() for name in FILES}
    items["LICENSE.txt"]=(ROOT/"LICENSE").read_bytes()
    items["assets/viewer.html.gz"]=gzip.compress(template(ROOT).encode(),mtime=0)
    items["assets/THIRD-PARTY.txt"]=b"\n\n".join(
        p.read_bytes() for p in [ROOT/"vendor/three/LICENSE",*sorted((ROOT/"vendor/fonts").glob("*LICENSE.txt"))])
    destination.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent,delete=False) as tmp:
        path=Path(tmp.name)
    try:
        with zipfile.ZipFile(path,"w") as z:
            for name,data in sorted(items.items()):
                info=zipfile.ZipInfo("bugapedia-photo/"+name,(2026,1,1,0,0,0))
                info.external_attr=0o100644<<16
                z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED)
        path.replace(destination)
    finally:
        path.unlink(missing_ok=True)
    print(destination)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    package(parser.parse_args().output)
