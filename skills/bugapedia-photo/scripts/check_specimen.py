"""Independently read back a completed GLB, manifest, embedded viewer and ZIP."""
import argparse
import base64
import json
import math
import re
import struct
import zipfile
from pathlib import Path
from build_specimen import require


def check(directory):
    m = json.loads((directory/"anatomy.json").read_text())
    raw = (directory/"specimen.glb").read_bytes()
    require(struct.unpack_from("<4sII",raw)==(b"glTF",2,len(raw)),"Invalid GLB header")
    n,tag = struct.unpack_from("<I4s",raw,12)
    require(tag==b"JSON","Missing GLB JSON")
    g = json.loads(raw[20:20+n])
    size,tag = struct.unpack_from("<I4s",raw,20+n)
    blob = memoryview(raw)[28+n:]
    require(tag==b"BIN\0" and size==len(blob)==g["buffers"][0]["byteLength"],"Bad binary chunk")
    def read(index):
        a = g["accessors"][index]
        b = g["bufferViews"][a["bufferView"]]
        width = {"SCALAR":1,"VEC3":3,"VEC4":4}[a["type"]]
        fmt = {5125:"I",5126:"f"}[a["componentType"]]
        start = b.get("byteOffset",0) + a.get("byteOffset",0)
        end = start+4*width*a["count"]
        require(0<=start<end<=len(blob) and end<=b.get("byteOffset",0)+b["byteLength"],"Accessor outside buffer")
        rows = list(struct.iter_unpack("<"+fmt*width,blob[start:end]))
        require(all(math.isfinite(x) for row in rows for x in row),"Non-finite component")
        return rows
    ids = {p["id"] for p in m["parts"]}
    actual = {p["extras"]["partId"]:p for p in g["nodes"] if "partId" in p.get("extras",{})}
    require(set(actual)==ids and len(ids)==len(m["parts"]),"Part ID mismatch")
    count=0
    for key,node in actual.items():
        require(node["name"]==key and node["children"],"Unselectable part: "+key)
        mesh=g["meshes"][g["nodes"][node["children"][0]]["mesh"]]
        for prim in mesh["primitives"]:
            pts=read(prim["attributes"]["POSITION"])
            normals=read(prim["attributes"]["NORMAL"])
            indices=read(prim["indices"])
            require(len(pts)==len(normals) and len(indices)%3==0 and all(0<=i[0]<len(pts) for i in indices),"Invalid triangles")
            require(all(abs(sum(v*v for v in row)-1)<.001 for row in normals),"Non-unit normal")
            count+=len(indices)//3
    clips={a["name"]:a for a in g["animations"]}
    for name in ("Articulation",m["behavior"]["clip"]):
        require(name in clips,"Missing native animation: "+name)
        moving=set()
        for channel in clips[name]["channels"]:
            sampler=clips[name]["samplers"][channel["sampler"]]
            times=[t[0] for t in read(sampler["input"])]
            values=read(sampler["output"])
            require(len(times)==len(values) and times==sorted(set(times)) and times[0]==0,"Invalid animation sampler")
            expected_end = 1 if name=="Articulation" else m["behavior"]["duration"]
            require(abs(times[-1]-expected_end)<.0001,"Clip duration mismatch")
            if any(row!=values[0] for row in values[1:]):
                moving.add(g["nodes"][channel["target"]["node"]]["name"])
        require(moving,"Empty motion in "+name)
        if name=="Articulation":
            require(moving=={"joint__"+p["id"] for p in m["parts"] if p.get("control",p["id"]) in m["controls"]},"Hinge targets mismatch")
    html=(directory/"explore.html").read_text()
    payload=re.search(r'<script id="bug-data" type="application/json">(.*?)</script>',html,re.S)
    model=re.search(r'<script id="bug-model" type="text/plain">data:model/gltf-binary;base64,([^<]+)</script>',html)
    require(payload and json.loads(payload[1])==m and model and base64.b64decode(model[1],validate=True)==raw,"Explorer uses different assets")
    with zipfile.ZipFile(directory/(m["id"]+"-specimen.zip")) as z:
        require(set(z.namelist())=={"explore.html","field-guide.md","specimen-source.json","anatomy.json","specimen.glb"},"Unexpected files in specimen ZIP")
        for member in z.namelist():
            require(z.read(member)==(directory/member).read_bytes(),"ZIP mismatch: "+member)
    print(f'{len(ids)} selectable parts, {count:,} triangles, {len(m["behavior"]["actions"])} action chapters. Verified GLB, controls, explorer and delivery ZIP.')


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    check(parser.parse_args().directory)
