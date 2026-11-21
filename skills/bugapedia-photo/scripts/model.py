"""Encode a self-contained glTF 2.0 binary with selectable parts and native clips."""
from bisect import bisect_right
import json
import math
import struct
from collections import defaultdict
from geometry import surface, sub


def multiply(a, b):
    x,y,z,w = a
    X,Y,Z,W = b
    return [w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z]


def rotation(angles):
    q = [0,0,0,1]
    for k, angle in enumerate(angles):
        half = math.radians(angle)/2
        axis = [0.,0.,0.,math.cos(half)]
        axis[k] = math.sin(half)
        q = multiply(q, axis)
    return q


def rotate(q, position):
    return multiply(multiply(q, [*position, 0]), [-q[0],-q[1],-q[2],q[3]])[:3]


def sample(keys, t):
    i = bisect_right(keys, t, key=lambda row: row[0])
    if i == 0:
        return keys[0][1:]
    if i == len(keys):
        return keys[-1][1:]
    t0,*a = keys[i-1]
    t1,*b = keys[i]
    f = (t-t0)/(t1-t0)
    return [[x+(y-x)*f for x,y in zip(u,v)] for u,v in zip(a,b)]


class Glb:
    def __init__(self):
        self.binary = bytearray()
        self.data = {
            "asset":{"version":"2.0","generator":"AnyBug photo builder"},
            "scene":0,"scenes":[{"nodes":[0]}],
            "nodes":[{"name":"Specimen","scale":[.001]*3,"children":[]}],
            "accessors":[],"bufferViews":[],"materials":[],"meshes":[],"animations":[]
        }

    def add(self, collection, item):
        items = self.data[collection]
        items.append(item)
        return len(items)-1

    def accessor(self, rows, shape, integers=False, target=None):
        start = len(self.binary)
        fmt = "I" if integers else "f"
        for row in rows:
            self.binary.extend(struct.pack("<" + fmt*len(row), *row))
        view = {"buffer":0,"byteOffset":start,"byteLength":len(self.binary)-start}
        if target:
            view["target"] = target
        return self.add("accessors", {
            "bufferView":self.add("bufferViews",view),"type":shape,
            "componentType":5125 if integers else 5126,"count":len(rows),
            "min":[min(axis) for axis in zip(*rows)],"max":[max(axis) for axis in zip(*rows)]
        })

    def clip(self, name):
        clip = {"name":name,"samplers":[],"channels":[]}
        self.add("animations", clip)
        return clip

    def track(self, clip, node, prop, times, values):
        index = len(clip["samplers"])
        clip["samplers"].append({"input":times,"output":self.accessor(values,"VEC4" if prop=="rotation" else "VEC3"),"interpolation":"LINEAR"})
        clip["channels"].append({"sampler":index,"target":{"node":node,"path":prop}})

    def encode(self):
        self.data["buffers"] = [{"byteLength":len(self.binary)}]
        info = json.dumps(self.data, separators=(",",":"), allow_nan=False).encode()
        info += b" "*((-len(info))%4)
        return (struct.pack("<4sII", b"glTF", 2, 28+len(info)+len(self.binary))
                + struct.pack("<I4s", len(info), b"JSON") + info
                + struct.pack("<I4s", len(self.binary), b"BIN\0") + self.binary)


def build(spec):
    glb = Glb()
    parts = {p["id"]:p for p in spec["parts"]}
    nodes, hinges, materials = {}, {}, {}
    for key, part in parts.items():
        pivot = part["pivot"]
        groups = defaultdict(lambda: ([],[],[]))
        for shape in part["shapes"]:
            color = shape["color"]
            alpha = shape.get("alpha",1)
            v,n,f = surface(shape,pivot)
            points,normals,indices = groups[color,alpha]
            offset = len(points)
            points.extend(v)
            normals.extend(n)
            indices.extend([[i+offset] for face in f for i in face])
        primitives = []
        for (color,alpha),(v,n,i) in groups.items():
            if (color,alpha) not in materials:
                srgb = [int(color[j:j+2],16)/255 for j in (1,3,5)]
                rgb = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in srgb]
                materials[color,alpha] = glb.add("materials",{"name":color,"pbrMetallicRoughness":{
                    "baseColorFactor":[*rgb,alpha],"metallicFactor":0,"roughnessFactor":.51},
                    "doubleSided":True,"alphaMode":"BLEND" if alpha < 1 else "OPAQUE"})
            primitives.append({"attributes":{"POSITION":glb.accessor(v,"VEC3",target=34962),
                                               "NORMAL":glb.accessor(n,"VEC3",target=34962)},
                               "indices":glb.accessor(i,"SCALAR",True,34963),"material":materials[color,alpha]})
        mesh = glb.add("meshes",{"name":key+"_surface","primitives":primitives})
        hinges[key] = glb.add("nodes",{"name":"joint__"+key,"mesh":mesh})
        nodes[key] = glb.add("nodes",{"name":key,"extras":{"partId":key},
                                      "translation":pivot,"children":[hinges[key]]})
        glb.data["nodes"][0]["children"].append(nodes[key])
    if spec["controls"]:
        clip = glb.clip("Articulation")
        steps = [i / 24 for i in range(25)]
        times = glb.accessor([[t] for t in steps],"SCALAR")
        for key, p in parts.items():
            driver = p.get("control",key)
            if driver not in spec["controls"]:
                continue
            angles = spec["controls"][driver]["angles"]
            rotations = [rotation([a*t for a in angles]) for t in steps]
            glb.track(clip,hinges[key],"rotation",times,rotations)
            if key != driver:
                arm = sub(p["pivot"],parts[driver]["pivot"])
                arc = [sub(rotate(q,arm),arm) for q in rotations]
                glb.track(clip,hinges[key],"translation",times,arc)
    behavior = spec["behavior"]
    clip = glb.clip(behavior["clip"])
    duration = behavior["duration"]
    frames = max(2,math.ceil(duration*24))
    # Include the author's exact event times as well as regular parent-pose samples.
    moments = sorted(set([duration*i/frames for i in range(frames+1)]
                         + [k[0] for track in behavior["tracks"].values() for k in track]))
    times = glb.accessor([[t] for t in moments],"SCALAR")
    poses = defaultdict(list)
    for t in moments:
        cache = {}
        def world(key):
            if key in cache:
                return cache[key]
            p = parts[key]
            parent = p.get("parent")
            angles,shift = sample(behavior["tracks"][key],t) if key in behavior["tracks"] else ([0]*3,[0]*3)
            pivot = p["pivot"]
            q = rotation(angles)
            local = [a+b for a,b in zip(pivot,shift)]
            if parent:
                parent_q, parent_pos = world(parent)
                delta = rotate(parent_q, sub(local,parts[parent]["pivot"]))
                local = [a+b for a,b in zip(parent_pos,delta)]
                q = multiply(parent_q,q)
            cache[key] = q,local
            return q,local
        for key in parts:
            poses[key].append(world(key))
    for key, rows in poses.items():
        for prop,values in zip(("rotation","translation"),zip(*rows)):
            if any(any(abs(a-b)>1e-7 for a,b in zip(v,values[0])) for v in values[1:]) or list(values[0]) != ([0,0,0,1] if prop=="rotation" else parts[key]["pivot"]):
                glb.track(clip,nodes[key],prop,times,values)
    if not clip["channels"]:
        raise ValueError("Behavior sequence has no motion")
    return glb.encode()
