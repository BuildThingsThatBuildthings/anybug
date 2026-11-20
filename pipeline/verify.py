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
# Every visible mesh belongs to exactly one labelled and selectable structure.
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        parents = []
        current = obj
        while current:
            if current.get("partId"):
                parents.append(current["partId"])
            current = current.parent
        assert len(parents) == 1, (obj.name, parents)

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
if brief["id"] == "european-mantis":
    assert set(brief["controls"]) == {"tibia_l", "tibia_r"}

    def center(pid):
        points = [
            obj.matrix_world @ Vector(corner)
            for obj in bpy.data.objects[pid].children_recursive
            if obj.type == "MESH"
            for corner in obj.bound_box
        ]
        return sum(points, Vector()) / len(points)

    for side in ("l", "r"):
        for piece in (
            "coxa",
            "trochanter",
            "femur",
            "tibia",
            "forefoot",
            "tibial_spines",
            "femoral_spines",
            "flexor",
        ):
            part = next(p for p in brief["parts"] if p["id"] == f"{piece}_{side}")
            assert part["control"] == f"tibia_{side}"
        # Verify substantial travel in the imported geometry at the two keyed poses.
        bpy.context.scene.frame_set(1)
        folded = center(f"forefoot_{side}")
        bpy.context.scene.frame_set(49)
        assert (center(f"forefoot_{side}") - folded).length > 0.012
    bpy.context.scene.frame_set(1)
    assert 0.048 < (center("head") - center("cercus_l")).length < 0.066
print(
    f"Verified {len(brief['parts'])} anatomical parts and {len(brief['controls'])} articulated controls."
)
