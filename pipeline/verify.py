"""Validate the packed, exported specimen in a new scene."""

import json
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector

folder = Path(sys.argv[sys.argv.index("--") + 1])
brief = json.loads((folder / "anatomy.json").read_text())
raw = (folder / "specimen.glb").read_bytes()
size = struct.unpack_from("<I", raw, 12)[0]
gltf = json.loads(raw[20 : 20 + size])
assert raw[:4] == b"glTF" and all("uri" not in i for i in gltf.get("images", []))
names = {node["name"] for node in gltf["nodes"] if "name" in node}
assert brief["focus"] in {p["id"] for p in brief["parts"]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(folder / "specimen.glb"))
for p in brief["parts"]:
    assert p["id"] in names and p["short"] and p["detail"], p["id"]
    obj = bpy.data.objects[p["id"]]
    assert obj.get("partId") == p["id"]
    assert any(o.type == "MESH" for o in obj.children_recursive), p["id"]
animated = set()
for clip in gltf.get("animations", []):
    for channel in clip["channels"]:
        target = channel["target"]
        animated.add(gltf["nodes"][target["node"]]["name"])
for pid in brief["controls"]:
    obj = bpy.data.objects[pid]
    assert {pid, *(c.name for c in obj.children_recursive)} & animated, pid
if brief["id"] == "seven-spot":
    ids = {p["id"] for p in brief["parts"]}
    assert sum(i.startswith("leg_") for i in ids) == 6
    assert sum(i.startswith("foot_") for i in ids) == 6
    assert {"cover_l", "cover_r", "wing_l", "wing_r", "ovary_l", "ovary_r"} <= ids
    corners = [
        o.matrix_world @ Vector(v)
        for o in bpy.context.scene.objects
        if o.type == "MESH"
        for v in o.bound_box
    ]
    length = (max(p.y for p in corners) - min(p.y for p in corners)) * 1000
    assert 7 < length < 9, length
print(
    f"Verified {len(brief['parts'])} anatomical parts and {len(brief['controls'])} articulated controls."
)
