"""Build an original animated GLB, its anatomy manifest and an offline explorer."""
import argparse
import json
import math
import re
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from model import build, sample
from portable_viewer import render

SKILL = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z][a-z0-9_]{0,63}")
COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric(x):
    return type(x) in (float,int) and math.isfinite(x)


def vector(x):
    return isinstance(x,list) and len(x)==3 and all(numeric(v) for v in x)


def words(item, fields):
    for k in fields.split():
        require(isinstance(item.get(k),str) and item[k].strip(), "Missing text: "+k)


def validate(s):
    words(s,"id name scientific stage scaleNote title overview focus dragHint gestureGuide")
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,63}",s["id"]), "Invalid specimen slug")
    require(numeric(s["lengthMm"]) and s["lengthMm"]>0, "Model length must be positive")
    view = s["view"]
    require(vector(view["target"]) and vector(view["direction"]) and any(view["direction"]) and numeric(view["radius"]) and view["radius"]>0, "Invalid camera")
    sources = s["sources"]
    for key,(title,url) in sources.items():
        p = urlsplit(url)
        require(title and p.scheme in ("http","https") and p.hostname and not p.username, "Invalid source: "+key)
    require("exterior" in s["systems"], "Missing exterior system")
    for sys in s["systems"].values():
        words(sys,"name")
        require(COLOR.fullmatch(sys["color"]), "Invalid system color")
    parts = {p["id"]:p for p in s["parts"]}
    require(len(parts)==len(s["parts"]) and s["focus"] in parts, "Part IDs must be unique and focus present")
    require(any(p["system"]!="exterior" for p in parts.values()), "Include a documented internal system")
    for key,p in parts.items():
        require(ID.fullmatch(key) and not key.startswith("joint__"), "Invalid part ID: "+key)
        words(p,"name term short detail evidence")
        require(p["system"] in s["systems"] and p["source"] in sources and vector(p["pivot"]) and p["shapes"],"Incomplete part: "+key)
        seen = {key}
        parent = p.get("parent")
        while parent is not None:
            require(parent in parts and parent not in seen,"Invalid attachment for "+key)
            seen.add(parent)
            parent = parts[parent].get("parent")
        if "control" in p:
            require(p["control"] in s["controls"] and p["control"] in seen and key not in s["controls"],
                    "A dependent part must follow a hinged ancestor")
        for shape in p["shapes"]:
            require(COLOR.fullmatch(shape["color"]) and numeric(shape.get("alpha",1)) and 0<shape.get("alpha",1)<=1,"Invalid material on "+key)
    for key,c in s["controls"].items():
        require(key in parts and vector(c["angles"]) and any(c["angles"]), "Invalid hinge: "+key)
        words(c,"open close")
        # Each hinge belongs to one independently selectable part.
        require("requires" not in c,"Use independent hinges")
    require(s["controls"], "Give the specimen a draggable anatomical joint")
    for key in s.get("landmarks",[]):
        require(key in parts,"Unknown landmark "+key)
    for key,v in s.get("spread",{}).items():
        require(key in parts and vector(v),"Invalid spread offset")
    b = s["behavior"]
    words(b,"clip")
    duration = b["duration"]
    require(b["clip"]!="Articulation" and numeric(duration) and 0<duration<=120 and numeric(b["frameScale"]) and b["frameScale"]>0,"Invalid behavior clip")
    starts = [a["start"] for a in b["actions"]]
    require(len(starts)>=2 and all(numeric(x) for x in starts) and starts==sorted(set(starts)) and starts[0]==0 and starts[-1]<duration,"Provide distinct action chapters within clip")
    for a in b["actions"]:
        words(a,"name note")
    require(b["sourceIds"] and all(k in sources for k in b["sourceIds"]), "Missing motion source")
    for key,rows in b["tracks"].items():
        require(key in parts and len(rows)>=2,"Invalid track: "+key)
        require(all(len(row)==3 and numeric(row[0]) and vector(row[1]) and vector(row[2]) for row in rows),"Malformed pose: "+key)
        times = [row[0] for row in rows]
        require(times==sorted(set(times)) and 0<=times[0]<times[-1]<=duration,"Invalid keyframe times: "+key)
    for a,z in zip(starts,starts[1:]+[duration]):
        def moves(track):
            poses = [sample(track,a), *[k[1:] for k in track if a<k[0]<z], sample(track,z)]
            return any(p!=poses[0] for p in poses[1:])
        require(any(moves(track) for track in b["tracks"].values()),"No animated motion in chapter at "+str(a))
    obs = s["observation"]
    words(obs,"identification visible reconstructed unresolved")
    for row in s["fieldNotes"]:
        words(row,"topic text")
        require(row["source"] in sources,"Unknown field-note source")
    require(s["fieldNotes"],"Include natural history")


def anatomy(s):
    fields = "id name scientific stage lengthMm scaleNote title overview focus dragHint gestureGuide view systems sources observation fieldNotes".split()
    m = {k:s[k] for k in fields}
    for k in ("landmarks","spread"):
        if k in s:
            m[k]=s[k]
    m["model"] = "specimen.glb"
    m["parts"] = [{k:v for k,v in p.items() if k not in ("shapes","pivot")} for p in s["parts"]]
    m["controls"] = {k:{a:c[a] for a in ("open","close")} for k,c in s["controls"].items()}
    m["behavior"] = {k:v for k,v in s["behavior"].items() if k not in ("tracks","sourceIds")}
    m["behavior"]["references"] = [s["sources"][k] for k in s["behavior"]["sourceIds"]]
    return m


def field_guide(s):
    obs = s["observation"]
    out = [f'# {s["name"]}',s["scientific"]+" · "+s["stage"],s["overview"],s["scaleNote"],
           "## Identification and evidence",*[obs[k] for k in ("identification","visible","reconstructed","unresolved")],"## Natural history"]
    for item in s["fieldNotes"]:
        title,url = s["sources"][item["source"]]
        out.append(f'**{item["topic"]}.** {item["text"]} [{title}]({url})')
    out.append("## Watch the animal")
    for a in s["behavior"]["actions"]:
        out.append(f'**{a["name"]}** ({a["start"]} s). {a["note"]}')
    out.append("## Anatomy")
    for p in s["parts"]:
        title,url = s["sources"][p["source"]]
        out.append(f'**{p["name"]}** ({p["term"]}). {p["short"]} {p["detail"]} {p["evidence"]}. [{title}]({url})')
    return "\n\n".join(out)+"\n"


def deliver(s, target):
    validate(s)
    m = anatomy(s)
    glb = build(s)
    html = render(m,glb,SKILL)
    target = target.resolve()
    if target.exists():
        raise ValueError("Choose a new output directory")
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        directory = Path(tmp)/"delivery"
        directory.mkdir()
        def dump(name, value):
            (directory/name).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n", encoding="utf-8")
        dump("specimen-source.json",s)
        dump("anatomy.json",m)
        (directory/"specimen.glb").write_bytes(glb)
        (directory/"explore.html").write_text(html,encoding="utf-8")
        (directory/"field-guide.md").write_text(field_guide(s),encoding="utf-8")
        with zipfile.ZipFile(directory/(s["id"]+"-specimen.zip"),"x",zipfile.ZIP_DEFLATED) as z:
            for f in sorted(directory.iterdir()):
                if f.suffix!=".zip":
                    z.write(f,f.name)
        directory.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    a = parser.parse_args()
    try:
        target = deliver(json.loads(a.source.read_text(encoding="utf-8")),a.out)
    except (KeyError,ValueError,TypeError,IndexError,OverflowError) as error:
        parser.exit(1,f"Specimen needs a correction: {error}\n")
    print(f"Built GLB, offline explorer, field guide and editable source in {target}")


if __name__ == "__main__":
    main()
